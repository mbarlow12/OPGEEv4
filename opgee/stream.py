#
# OPGEE stream support
#
# Author: Richard Plevin and Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging
import re
from copy import copy

import pandas as pd
import pint

from .chemistry import (
    CARBON_NUMBER,
    COMPONENT_NAMES,
    GASES,
    HYDROCARBONS,
    LIQUIDS,
    PHASE_GAS,
    PHASE_LIQUID,
    PHASE_SOLID,
    VOCS,
)
from .context import FieldContext
from .core import TemperaturePressure
from .error import OpgeeException
from .units import magnitude, ureg

_logger = logging.getLogger(__name__)

# Carbon-number series used by ``add_combustion_CO2_from``. Built once at
# module load from the canonical ``CARBON_NUMBER`` dict in ``opgee.chemistry``.
_carbon_number_series = pd.Series(CARBON_NUMBER, dtype="pint[dimensionless]")

# Components assumed to combust completely to CO2 (used by
# ``add_combustion_CO2_from``).
_combustible_components = HYDROCARBONS + GASES


#
# Can streams have emissions (e.g., leakage) or is that attributed to a process?
#
class Stream:
    """
    The `Stream` class represents the flow rates of single substances or mingled
    combinations of co-flowing substances in any of the three states of matter
    (solid, liquid, or gas). Streams and stream components are specified in mass
    flow rates (e.g., Mg per day). The default set of substances is defined by
    ``opgee.chemistry.COMPONENT_NAMES``.
    """

    _phases = [PHASE_SOLID, PHASE_LIQUID, PHASE_GAS]

    _units = ureg.Unit("tonne/day")

    tp: TemperaturePressure

    def __init__(
        self,
        name: str,
        tp: TemperaturePressure | None,
        ctx: FieldContext | None = None,
        *,
        API=None,
        comp_matrix=None,
        src_name: str | None = None,
        dst_name: str | None = None,
        contents: list[str] | None = None,
        impute: bool = True,
    ):
        self.name = name
        self.ctx = ctx

        # TBD: rename this self.comp_matrix for clarity
        self.components = (
            self.create_component_matrix() if comp_matrix is None else comp_matrix
        )

        self.tp = copy(tp)

        # These values are used by self.reset() to restore the stream to its
        # initial state.
        self.initial_tp = copy(self.tp)
        self.initial_data = comp_matrix

        self.src_name = src_name
        self.dst_name = dst_name

        self.src_proc = None  # set in Field.connect_processes()
        self.dst_proc = None
        self.API = API

        self.contents = contents or []  # generic description of what the stream carries

        self.impute = impute

        # Tracks whether any data have been written to the stream yet. Note
        # that it is False if only temperature and pressure are set, though
        # setting T & P makes no sense on an empty stream.
        self.initialized = comp_matrix is not None

    def __str__(self):
        return f"<Stream '{self.name}'>"

    def to_dataframe(self):
        """
        Converts the data for the stream, including stream name, temperature, pressure,
        and API to a long-format DataFrame for writing CSV files.

        :return: (pd.DataFrame) data series
        """
        df = self.components.reset_index().melt(
            id_vars=["index"], var_name="phase", value_name="value"
        )
        df.rename(columns={"index": "component"}, inplace=True)

        df["units"] = "metric_ton / day"
        df.value = df.value.apply(lambda v: v.m)  # strip off units

        df = df[df.value != 0]  # eliminate *many* zero rows

        # TBD: Drop non-solid petcoke, non-liquid oil, non-gaseous O2, N2, CO2, CO? Or just leave it.

        # Add extra bits that don't fit the original matrix format
        no_phase = ""

        columns = ["phase", "component", "value", "units"]

        items = [('T', self.tp.T),
                 ('P', self.tp.P),
                 ('API', self.API)]

        tuples = [(no_phase, name, value.m, str(value.units))
                    for name, value in items if value is not None and value.m != 0]

        extras = pd.DataFrame(data=tuples, columns=columns)
        result = pd.concat([df, extras], axis='rows')

        result['stream'] = self.name
        result['source'] = self.src_name
        result['destination'] = self.dst_name

        col_order = ["stream", "source", "destination"] + columns
        return result[col_order]

    def reset(self):
        """
        Reset an existing `Stream` to a state suitable for re-running the model.
        If the stream was initialized with an explicit component matrix, this
        will have been stored in ``self.initial_data`` and is used to reset the
        stream. Otherwise, a new component matrix is created.

        :return: none
        """
        self.initialized = has_initial_data = self.initial_data is not None
        self.components = (
            self.initial_data if has_initial_data else self.create_component_matrix()
        )

        self.tp.copy_from(self.initial_tp)

    @classmethod
    def units(cls):
        return cls._units

    @classmethod
    def create_component_matrix(cls):
        """
        Create a pandas DataFrame to hold the 3 phases of the known Components.

        :return: (pandas.DataFrame) Zero-filled stream DataFrame
        """
        return pd.DataFrame(
            data=0.0,
            index=COMPONENT_NAMES,
            columns=cls._phases,
            dtype="pint[tonne/day]",
        )

    def is_initialized(self):
        return self.initialized

    def is_uninitialized(self):
        return not self.initialized

    def has_zero_flow(self):
        return self.total_flow_rate().m == 0

    def component_phases(self, name):
        """
        Return the flow rates for all phases of stream component `name`.

        :param name: (str) The name of a stream component
        :return: (pandas.Series) the flow rates for the three phases of component `name`
        """
        return self.components.loc[name]

    def flow_rate(self, name, phase):
        """
        Get the value of the stream component `name` for `phase`.

        :param name: (str) the name of a stream component
        :param phase: (str) the name of a phase of matter ('gas', 'liquid' or 'solid')
        :return: (float) the flow rate for the given stream component
        """
        rate = self.components.loc[name, phase]
        return rate

    def total_flow_rate(self):
        """
        total mass flow rate

        :return:
        """
        return self.components.sum(axis="columns").sum()

    def hydrocarbons_rates(self, phase):
        """
        Set rates for each hydrocarbons

        :param phase: (str) the name of a phase of matter ('gas', 'liquid' or 'solid')
        :return: (float) the flow rates for all the hydrocarbons
        """
        return self.flow_rate(HYDROCARBONS + LIQUIDS, phase)

    def hydrocarbon_rate(self, phase):
        """
        Summarize rates for each hydrocarbon

        :param phase: (str) the name of a phase of matter ('gas', 'liquid' or 'solid')
        :return: (float) the summation of flow rates of all hydrocarbons
        """
        return self.hydrocarbons_rates(phase).sum()

    def total_gases_rates(self):
        """

        :return:
        """
        return self.gas_flow_rate(HYDROCARBONS + GASES)

    def total_gas_rate(self):
        """

        :return:
        """
        return self.total_gases_rates().sum()

    def set_flow_rate(self, name, phase, rate):
        """
        Set the value of the stream component ``name`` for ``phase` to ``rate``.

        :param name: (str) the name of a stream component
        :param phase: (str) the name of a phase of matter ('gas', 'liquid' or 'solid')
        :param rate: (float) the flow rate for the given stream component
        :return: none
        """
        rate = rate.to("tonne/day") if isinstance(rate, pint.Quantity) else rate
        # TBD: Check that this comment remains true with updates to pint. (If not, update the code)
        # It's currently not possible to assign a Quantity to a DataFrame even if
        # the units match. It's magnitude must be extracted. We check the units first...
        self.components.loc[name, phase] = magnitude(rate, units="tonne/day")
        self.initialized = True

    def set_API(self, API):
        if not isinstance(API, ureg.Quantity):
            API = ureg.Quantity(API, "degAPI")
        self.API = API

    #
    # Convenience functions
    #
    def gas_flow_rates(self, index=None):
        """
        Return all positive gas flows

        :return: (pandas.Series) all flow rates
        """
        gas = self.components.gas
        if index is not None:
            return gas[index]
        return gas[gas > 0]

    def gas_flow_rate(self, name):
        """
        Convenience method to get the flow rate of a gas.

        :param name: (str) the name of the component
        :return: (pint.Quantity) the flow rate of the component
        """
        return self.flow_rate(name, PHASE_GAS)

    def liquid_flow_rate(self, name):
        """
        Convenience method to get the flow rate of a liquid.

        :param name: (str) the name of the component
        :return: (pint.Quantity) the flow rate of the component
        """
        return self.flow_rate(name, PHASE_LIQUID)

    def solid_flow_rate(self, name):
        """
        Convenience method to get the flow rate of a solid.

        :param name: (str) the name of the component
        :return: (pint.Quantity) the flow rate of the component
        """
        return self.flow_rate(name, PHASE_SOLID)

    def voc_flow_rates(self):
        return self.components.gas[VOCS]

    def non_zero_flow_rates(self):
        zero = ureg.Quantity(0.0, "tonne/day")
        c = self.components
        return c[(c.solid > zero) | (c.liquid > zero) | (c.gas > zero)]

    def set_gas_flow_rate(self, name, rate):
        """
        Convenience method to set the flow rate for a gas.
        """
        return self.set_flow_rate(name, PHASE_GAS, rate)

    def set_liquid_flow_rate(self, name, rate, tp=None):
        """
        Sets the flow rate of a liquid substance
        """
        if tp:
            self.tp.copy_from(tp)

        self.initialized = True
        return self.set_flow_rate(name, PHASE_LIQUID, rate)

    def set_solid_flow_rate(self, name, rate, tp=None):
        """
        Sets the flow rate of a solid substance
        """
        if tp:
            self.tp.copy_from(tp)

        self.initialized = True
        return self.set_flow_rate(name, PHASE_SOLID, rate)

    def set_rates_from_series(self, series, phase, upper_bound_stream=None):
        """
        set rates from pandas series given phase given the upper bound stream

        :param series:
        :param phase:
        :param upper_bound_stream: (Stream) the result stream's component rate cannot exceed the component rate from this stream
        :return:
        """
        self.initialized = True
        self.components.loc[series.index, phase] = series.clip(lower=0)
        if upper_bound_stream is not None:
            self.components.loc[series.index, phase] = self.components.loc[
                series.index, phase
            ].clip(upper=upper_bound_stream.components.loc[series.index, phase])

    def multiply_factor_from_series(self, series, phase):
        """
        Multiply the flow rates for the given ``phase`` by the values in ``series``

        :param series: (pandas.Series) index must refer to components of `Stream`
        :param phase: (str) one of {'gas', 'liquid', or 'solid'}
        :return:
        """
        self.initialized = True
        self.components.loc[series.index, phase] = (
            series * self.components.loc[series.index, phase]
        )

    def set_tp(self, tp):
        """
        Set the stream's temperature and pressure, unless the pressure is zero,
        in which case nothing is done.

        :param tp: (TemperaturePressure) temperature and pressure
        :return: none
        """
        if tp is None:
            raise OpgeeException("Called Stream.set_tp() with None")

        if tp.P.m == 0:
            _logger.warning("Called Stream.set_tp() with zero pressure")
            return

        self.tp = copy(tp)
        self.initialized = True

    def copy_flow_rates_from(self, stream, phase=None, tp=None, API=None):
        """
        Copy all mass flow rates from ``stream`` to ``self``

        :param phase: (str) one of {'gas', 'liquid', or 'solid'}
        :param tp: (TemperaturePressure) temperature and pressure to set
        :param API: (Quantity) the API to assign to this stream. If None,
            the source stream's API is copied.
        :param stream: (Stream) to copy

        :return: none
        """
        if stream.is_uninitialized():
            raise OpgeeException(f"Can't copy from uninitialized stream: {stream}")

        if phase:
            self.components[phase] = stream.components[phase]
        else:
            self.components[self.components.columns] = stream.components

        self.API = API or stream.API
        self.tp.copy_from(tp or stream.tp)

        self.initialized = True

    def copy_gas_rates_from(self, stream, tp=None, API=None):
        """
        Copy gas mass flow rates from ``stream`` to ``self``

        :param stream: (Stream) to copy
        :param tp: (TemperaturePressure) temperature and pressure to set
        :param API: (Quantity) the API to assign to this stream. If None,
            the source stream's API is copied.
        :return: none
        """

        if stream.is_uninitialized():
            raise OpgeeException(f"Can't copy from uninitialized stream: {stream}")

        self.API = API or stream.API

        self.initialized = True
        self.components[PHASE_GAS] = stream.components[PHASE_GAS]

        if tp:
            self.set_tp(tp)

    def copy_liquid_rates_from(self, stream):
        """
        Copy liquid mass flow rates from ``stream`` to ``self``

        :param stream: (Stream) to copy
        :return: none
        """
        if stream.is_uninitialized():
            return OpgeeException(f"copy NULL stream from {stream.name}")

        self.initialized = True
        self.components[PHASE_LIQUID] = stream.components[PHASE_LIQUID]

    def multiply_flow_rates(self, factor):
        """
        Multiply all our mass flow rates by `factor`.

        :param factor: (float) the value to multiply by
        :return: none
        """
        factor = factor.to("fraction") if isinstance(factor, pint.Quantity) else factor
        self.initialized = True

        multiplier = magnitude(factor, "fraction")
        self.components *= multiplier

    def add_flow_rate(self, name, phase, rate):
        """
        Add the mass flow ``rate`` to our own.

        :param name: (str) the name of the component
        :param phase: (str) one of {'gas', 'liquid', or 'solid'}
        :param rate: (pint.Quantity) in units of mass/time
        :return: none
        """
        self.set_flow_rate(name, phase, self.flow_rate(name, phase) + rate)

    def add_flow_rates_from(self, stream):
        """
        Add the mass flow rates from `stream` to our own.

        :param stream: (Stream) the source of the rates to add
        :return: none
        """
        if stream.is_uninitialized():
            return

        self.initialized = True
        self.components += stream.components

    def subtract_rates_from(self, stream, phase=PHASE_GAS):
        """
        Subtract the gas mass flow rates of ``stream`` from our own.

        :param phase: solid, liquid, gas phase
        :param stream: (Stream) the source of the rates to subtract
        :return: none
        """
        if stream.is_uninitialized():
            return

        self.initialized = True
        self.components[phase] -= stream.components[phase]
        self.components[phase] = self.components[phase].clip(0)

    def add_combustion_CO2_from(self, stream):
        """
        Compute the amount of CO2 from the combustible components in `stream`
        and add these to ``self`` as CO2, assuming complete combustion.

        :param stream: (Stream) a Stream with combustible components
        :return: (pint.Quantity(unit="tonne/day")) the mass rate of CO2 from combustion.
        """
        from .thermodynamics import (
            ChemicalInfo,
        )  # avoids circular imports (stream <-> thermodynamics)

        component_MW = ChemicalInfo.mol_weights()

        rate = (
            stream.components.loc[_combustible_components, PHASE_GAS]
            / component_MW[_combustible_components]
            * _carbon_number_series
            * component_MW["CO2"]
        ).sum()

        self.set_flow_rate("CO2", PHASE_GAS, rate)  # sets initialized flag
        return rate

    def contains(self, stream_type, regex=False):
        """
        Return whether ``stream_type`` is one of named contents of ``self``.

        :param stream_type: (str) a symbolic name for contents of `stream`
        :param regex (bool) whether to interpret `stream_type` as a regular expression
        :return: (bool) True if `stream_type` is among the contents of `stream`
        """
        if regex:
            return any(re.fullmatch(stream_type, name) for name in self.contents)
        else:
            return stream_type in self.contents

    @property
    def hydrocarbons(self):
        return HYDROCARBONS
