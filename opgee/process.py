#
# OPGEE process support
#
# Author: Richard Plevin and Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging
from typing import Union

import pandas as pd
import pint

from .combine_streams import combine_streams
from .context import FieldContext
from .emissions import EM_COMBUSTION, Emissions
from .energy import EN_ELECTRICITY, Energy
from .error import (
    AbstractMethodError,
    ModelValidationError,
    OpgeeException,
    OpgeeIterationConverged,
)
from .import_export import ImportExport
from .stream import Stream
from .units import magnitude

_logger = logging.getLogger(__name__)


# Module-level list of iterating processes.
# TODO(phase 6.1): Move ownership of iterating-process tracking to Field. This
# is module-global during the deep-clean transition, preserving pre-refactor
# behavior (which used a Process class variable) without adding a circular
# Process↔Field dependency.
_iterating_processes: list["Process"] = []


# DOCUMENT this feature
class IntermediateValues:
    """
    Stores "interesting" intermediate values from processes for display.
    """

    def __init__(self):
        self.data = pd.DataFrame(columns=("value", "unit", "desc"))

    def store(self, name, value, unit=None, desc=None):
        # Strip magnitude and unit from Quantity objects
        if isinstance(value, pint.Quantity):
            unit = str(value.u)
            value = value.m

        self.data.loc[name, ("value", "unit", "desc")] = (value, unit or "", desc or "")

    def get(self, name):
        """
        Return the record associated with `name`.

        :param name: (str) the name of an intermediate value
        :return: (pd.Series) the row in the DataFrame of intermediate values for this process.
        """
        try:
            return self.data.loc[name]
        except KeyError:
            raise OpgeeException(f"An intermediate value for '{name}' was not found")


def run_corr_eqns(x1, x2, x3, x4, x5, coef_df):
    """
    Generalized function to run a quadratic correlation equation of 5 coefficients.

    :param x1-x5: (float) the coefficients
    :param coef_df: (pandas.DataFrame) data values
    :return: pandas.Series
    """

    x = pd.Series(
        data=[1, x1, x2, x3, x4, x5, x1 * x2, x1 * x3, x1 * x4, x1 * x5, x2 * x3, x2 * x4, x2 * x5, x3 * x4,
              x3 * x5, x4 * x5, x1 ** 2, x2 ** 2, x3 ** 2, x4 ** 2, x5 ** 2], index=coef_df.index)
    df = coef_df.mul(x, axis=0)
    result = df.sum(axis="rows")
    return result


class Process:
    """
    The "leaf" node in the process hierarchy. ``Process`` is an abstract superclass:
    actual runnable Process instances must be of subclasses of ``Process`` defined in
    `opgee/processes/*.py`.

    Each Process subclass must implement the ``run`` method.

    If a model contains process loops (cycles), one or more of the processes can call
    the method ``set_iteration_value()`` to store the value(s) of a designated
    variable(s) to be checked on each call to see if the change from the prior
    iteration is <= ``ctx.simulation.maximum_change``. If so, an
    ``OpgeeIterationConverged`` exception is raised to terminate the run.

    In addition to testing for convergence, a "visit" counter in each ``Process`` is
    incremented each time the process is run (or bypassed) and if the count reaches
    ``ctx.simulation.maximum_iterations``, ``OpgeeMaxIterationsReached`` is likewise
    raised. Whichever limit is reached first will cause iterations to stop.
    """

    # Constants to support stream "finding" methods
    INPUT = "input"
    OUTPUT = "output"

    # Support for stream validation. Subclasses can set these ivars
    # or redefine the methods required_inputs() / required_outputs()
    _required_inputs: list = []
    _required_outputs: list = []

    def __init__(self, name: str, ctx: FieldContext):
        self.name = name
        self.ctx = ctx
        self.desc = ""
        self.run_after = False
        self.extend = False

        # Stream instances, set in Field.connect_processes()
        self.inputs: list[Stream] = []
        self.outputs: list[Stream] = []

        self.energy = Energy()
        self.emissions = Emissions()
        self.import_export = ImportExport()

        # Per-process emission-factor series; set by subclass constructors that
        # use `set_combustion_emissions` / `compute_emission_combustion`. Left
        # None here because the old lookup path (`self.model.process_EF_df`) has
        # been removed in the deep-clean refactor.
        self.process_EF = None

        self.intermediate_results: dict | None = None

        # Support for cycles
        self.visit_count = 0  # increment when the Process has been run
        self.iteration_count = 0
        self.iteration_value = None
        self.iteration_converged = False
        self.iteration_registered = False
        self.in_cycle = False

    def __str__(self):
        return f"<{self.__class__.__name__} '{self.name}'>"

    def required_inputs(self):
        """
        Return the names of required input stream contents
        """
        return self._required_inputs

    def required_outputs(self):
        """
        Return the names of required output stream contents
        """
        return self._required_outputs

    def reset(self):
        self.energy.reset()
        self.emissions.reset()
        self.reset_iteration()

    #
    # Pass-through convenience methods for energy and emissions
    #
    def add_emission_rate(self, category, gas, rate):
        """
        Add to the stored rate of emissions for a single gas.

        :param category: (str) one of the defined emissions categories
        :param gas: (str) one of the defined emissions (values of Emissions.emissions)
        :param rate: (float) the increment in rate in the Process' flow units (e.g., mmbtu/day
            (LHV) of fuel burned) except for electricity, which is in mmbtu/day as well but
            without LHV (no combustion to thermal energy), assuming 100% mechanical to thermal
            energy conversion.
        :return: none
        """
        self.emissions.add_rate(category, gas, rate)

    def add_emission_rates(self, category, **kwargs):
        """
        Add emissions to those already stored, for of one or more gases, given as
        keyword arguments, e.g., add_emission_rates(CO2=100, CH4=30, N2O=6).

        :param category: (str) one of the defined emissions categories
        :param kwargs: (dict) the keyword arguments
        :return: none
        """
        self.emissions.add_rates(category, **kwargs)

    def get_emission_rates(self, gwp):
        """
        Return the emission rates and the calculated GHG value.

        :param gwp: (pandas.Series) global warming potentials, typically from
            ``self.ctx.gwp.values``.
        :return: ((pandas.Series, float)) a tuple containing the emissions Series
            and the GHG value computed using the supplied GWP.
        """
        return self.emissions.rates(gwp=gwp)

    def compute_emission_combustion(self) -> pint.Quantity:
        """
        Compute the total emissions from the combustion of all energy carriers,
        excluding electricity.

        :return: (float) the total combustion emissions calculated by multiplying
                the energy used (excluding electricity) by the process emission
                factor and summing the result.
        """
        if self.process_EF is None:
            raise ModelValidationError(
                f"{self}: process_EF must be set by the subclass before calling "
                f"compute_emission_combustion()"
            )
        energy_for_combustion = self.energy.data.drop(EN_ELECTRICITY)
        combustion_emission = (energy_for_combustion * self.process_EF).sum()
        return combustion_emission

    def set_combustion_emissions(self):
        emissions = self.compute_emission_combustion()
        self.emissions.set_rate(EM_COMBUSTION, "CO2", emissions)

    def add_energy_rate(self, carrier, rate):
        """
        Set the rate of energy use for a single carrier.

        :param carrier: (str) one of the defined energy carriers (values of Energy.carriers)
        :param rate: (float)  the rate of use for all energy sources in mmbtu/day (LHV), except
            for electricity, which is in mmbtu/day as well but without LHV (no combustion to
            thermal energy), assuming 100% mechanical to thermal energy conversion.
        :return: none
        """
        self.energy.add_rate(carrier, rate)

    def add_energy_rates(self, dictionary):
        """
        Add to the energy use rate for one or more carriers.

        :param dictionary: (dict) the carriers and rates
        :return: none
        """
        self.energy.add_rates(dictionary)

    def get_energy_rates(self):
        """
        Return the energy consumption rates.
        """
        return self.energy.rates()

    def get_net_imported_product(self):
        """
        Return the net imported product energy rate (water is mass rate)
        :return:
        """
        imp_exp = self.import_export.imports_exports()
        return imp_exp[ImportExport.NET_IMPORTS]

    def set_import_from_energy(self, energy_use):
        self.import_export.set_import_from_energy(self.name, energy_use)

    #
    # end of pass through energy and emissions methods
    #

    def set_gas_fugitives(self, stream, loss_rate) -> Stream:
        """
        Initialize the gas fugitives stream, get loss rate, copy rates.

        :param stream: input Stream
        :param loss_rate: fraction of the stream's gas flow that leaks
        :return: (Stream) the newly constructed fugitives Stream
        """
        gas_fugitives = Stream("gas fugitives", tp=self.ctx.stp)
        gas_fugitives.copy_gas_rates_from(stream)
        gas_fugitives.multiply_flow_rates(loss_rate)

        return gas_fugitives

    def get_compressor_and_well_loss_rate(self, inlet_stream):
        """Compute fugitive loss rate through compressors and injection wells.

        TODO(phase 5): re-wire via explicit constructor params — subclasses
        need access to `num_gas_inj_wells`, `loss_mat_gas_ave_df`, and the
        `gas` thermo object. Currently only called by sour_gas_injection,
        gas_lifting_compressor, gas_reinjection_well, CO2_injection_well
        subclasses, all of which will be migrated in Phase 5.
        """
        raise NotImplementedError(
            "get_compressor_and_well_loss_rate: wiring deferred to Phase 5 "
            "subclass migration"
        )

    def visit(self):
        self.visit_count += 1
        return self.visit_count

    def visited(self):
        return self.visit_count

    def _find_streams_by_type(self, direction, stream_type,
                              combine=False,
                              as_list=False,
                              regex=False,
                              raiseError=True) -> Union[
        Stream, list, dict]:
        """
        Find the input or output streams (indicated by `direction`) that contain the indicated
        `stream_type`, e.g., 'oil', 'water' and so on.

        :param direction: (str) 'input' or 'output'
        :param stream_type: (str) the generic type of stream a process can handle.
        :param combine: (bool) whether to (thermodynamically) combine multiple Streams into a single one
        :param as_list: (bool) return results as a list rather than as a dict
        :param regex (bool) whether to interpret `stream_type` as a regular expression
        :param raiseError: (bool) whether to raise an error if no handlers of `stream_type` are found.
        :return: (Stream, list or dict of Streams) depends on various keyword args
        :raises: OpgeeException if no processes handling `stream_type` are found and `raiseError` is True
        """
        if combine and as_list:
            raise OpgeeException("_find_streams_by_type: both 'combine' and 'as_list' cannot be True")

        assert direction in {self.INPUT, self.OUTPUT}
        stream_list = self.inputs if direction == self.INPUT else self.outputs
        streams = [stream for stream in stream_list if stream.contains(stream_type, regex=regex)]

        if not streams and raiseError:
            raise OpgeeException(f"{self}: no {direction} streams contain '{stream_type}'")

        return combine_streams(streams) if combine else (
            streams if as_list else {s.name: s for s in streams})

    def find_input_streams(self, stream_type,
                           combine=False,
                           as_list=False,
                           regex=False,
                           raiseError=True) -> Union[
        Stream, list, dict]:
        """
        Convenience method to call `_find_streams_by_type` with direction "input"
        """
        return self._find_streams_by_type(self.INPUT, stream_type, combine=combine,
                                          as_list=as_list, regex=regex, raiseError=raiseError)

    def find_output_streams(self, stream_type,
                            combine=False,
                            as_list=False,
                            regex=False,
                            raiseError=True) -> Union[
        Stream, list, dict]:
        """
        Convenience method to call `_find_streams_by_type` with direction "output"
        """
        return self._find_streams_by_type(self.OUTPUT, stream_type, regex=regex, combine=combine, as_list=as_list,
                                          raiseError=raiseError)

    def find_input_stream(self, stream_type, regex=False, raiseError=True) -> Union[Stream, None]:
        """
        Find exactly one input stream connected to a downstream Process that produces the indicated
        `stream_type`, e.g., 'oil', 'water' and so on.
        """
        streams = self.find_input_streams(stream_type, as_list=True, regex=regex, raiseError=raiseError)
        if len(streams) != 1:
            if raiseError:
                raise OpgeeException(f"Expected one input stream with '{stream_type}'; found {len(streams)}")
            return None

        return streams[0]

    def find_output_stream(self, stream_type, regex=False, raiseError=True) -> Union[Stream, None]:
        """
        Find exactly one output stream connected to a downstream Process that consumes the indicated
        `stream_type`, e.g., 'oil', 'water' and so on.
        """
        streams = self.find_output_streams(stream_type, as_list=True, regex=regex, raiseError=raiseError)
        if len(streams) != 1:
            if raiseError:
                raise OpgeeException(f"{self}: Expected one output stream with '{stream_type}'; found {len(streams)}")
            return None

        return streams[0]

    def add_output_stream(self, stream):
        self.outputs.append(stream)

    def add_input_stream(self, stream):
        self.inputs.append(stream)

    def predecessors(self) -> set:
        """
        Return a Process's immediate precedent Processes.

        :return: (set of Process) the Processes that are the sources of
           Streams connected to `process`.
        """
        return {stream.src_proc for stream in self.inputs}

    def successors(self) -> set:
        """
        Return a Process's immediately following Processes.

        :return: (set of Process) the Processes that are the destinations
           of Streams connected to `process`.
        """
        return {stream.dst_proc for stream in self.outputs}

    def set_iteration_value(self, value):
        """
        Store the value of one or more variables used to determine when an
        iteration loop has stabilized. When set, if the absolute value of the
        change in each value is less than ``self.ctx.simulation.maximum_change``,
        the run loop is terminated by throwing an OpgeeStopIteration exception.
        """
        _logger.debug(f"{self.name}:count = {self.visit_count}")
        if not self.in_cycle or self.iteration_converged:
            return  # nothing left to do

        maximum_change = self.ctx.simulation.maximum_change

        # register the process and remember its registration so we don't do it again
        if not self.iteration_registered:
            self.register_iterating_process(self)

        prior_value = self.iteration_value

        # helper function to check for convergence of each element of a tuple
        def converged(prior_value, value):
            delta = magnitude(abs(value - prior_value))
            is_converged = delta <= maximum_change
            if not is_converged:
                _logger.debug(f"process: {self.name}")
                _logger.debug(f"current value is {value}")
                _logger.debug(f"prior value is {prior_value}")
            return is_converged

        if prior_value is not None:
            if type(prior_value) is not type(value):
                raise OpgeeException(f"Type of iterator value changed; was: {type(prior_value)} is: {type(value)}")

            # TODO: we expect the series to have no units
            if isinstance(value, pd.Series):
                diff = abs(value - prior_value)  # type: pd.Series
                if all(diff <= maximum_change):
                    self.iteration_converged = True
                    self.check_iterator_convergence()
                else:
                    _logger.debug(f"process: {self.name}")
                    _logger.debug(f"current value is {value}")
                    _logger.debug(f"prior value is {prior_value}")
            else:
                pairs = zip(prior_value, value) if isinstance(value, (tuple, list)) \
                    else [(prior_value, value)]  # make a list of the one pair

                if all([converged(old, new) for old, new in pairs]):
                    self.iteration_converged = True
                    # Raise OpgeeStopIteration exception if all process's
                    # iterator values have converged.
                    self.check_iterator_convergence()

        self.iteration_value = value

    @staticmethod
    def register_iterating_process(process):
        process.iteration_registered = True
        _iterating_processes.append(process)

    @staticmethod
    def check_iterator_convergence():
        """
        Check whether the current process is the last of all process iterator values to converge.
        stop when one converges but others have yet to do so.

        :return: none.
        :raises OpgeeIterationConverged: if all processes have converged.
        """
        if all([proc.iteration_converged for proc in _iterating_processes]):
            raise OpgeeIterationConverged("Change <= maximum_change in all iterating processes")

    @staticmethod
    def reset_all_iteration():
        """
        Reset the iteration value and counter in all iterating processes,
        then clear the list to prevent duplicate registration on re-entry.

        :return: none
        """
        for proc in _iterating_processes:
            proc.reset_iteration()
        _iterating_processes.clear()

    def reset_iteration(self):
        self.visit_count = self.iteration_count = 0
        self.iteration_converged = self.iteration_registered = False
        self.iteration_value = None
        self._reset_before_iteration()

    def _reset_before_iteration(self):
        """
        Optional method to allow iterating Process subclasses to reset state before
        a new iteration cycle begins.

        :return: none
        """
        pass

    def run(self):
        """
        This method implements the behavior required of the Process subclass.
        **Subclasses of Process must implement this method.**

        :return: None
        """
        raise AbstractMethodError(self.__class__, "Process.run")

    def print_running_msg(self):
        _logger.debug(f"Running {type(self)} name='{self.name}'")

    def init_intermediate_results(self, names):
        """
        Initialize the `intermediate_results` dict with (Energy, Emissions) pairs
        keyed by the supplied names.
        """
        self.intermediate_results = {name: (Energy(), Emissions()) for name in names}

    def get_intermediate_results(self):
        """
        :return: the dict of (Energy, Emissions) pairs, or None.
        """
        return self.intermediate_results

    def sum_intermediate_results(self):
        """
        Sum intermediate energy and emission results into the Process-level
        energy/emissions objects.
        """

        if self.intermediate_results is None:
            return

        self.energy.reset()
        self.emissions.reset()

        for _, (energy, emission) in self.intermediate_results.items():
            self.energy.add_rates_from(energy)
            self.emissions.add_rates_from(emission)

    def all_streams_ready(self, input_stream_contents):
        """
        Check if all the streams to ``self`` containing ``input_stream_contents``
        are initialized.

        :param input_stream_contents: (str) name of input stream contents
        :return: (bool) whether all indicated streams are initialized
        """
        input_streams = self.find_input_streams(input_stream_contents)
        for stream in input_streams.values():
            if stream.is_uninitialized():
                return False

        return True


class Reservoir(Process):
    """
    Reservoir represents natural resources such as oil and gas reservoirs, and water sources
    in the subsurface. Each Field object holds a single Reservoir instance. Its ``run()`` is
    a no-op; it exists structurally as a source node in the process graph.
    """

    def __init__(self, name: str, ctx: FieldContext):
        super().__init__(name, ctx)
        self.desc = "The Reservoir"

    def run(self):
        self.print_running_msg()
