#
# Results handling for OPGEE
#
# This module separates results collection from core simulation logic.
# Aggregators here are lightweight groupings for results purposes only,
# not part of the process hierarchy.
#
# Author: Richard Plevin and Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pint

from .constants import DETAILED_RESULT
from .log import getLogger
from .units import ureg

if TYPE_CHECKING:
    from .analysis import Analysis
    from .field import Field
    from lxml import etree

_logger = getLogger(__name__)


class FieldResult:
    """
    Container for results from running a Field simulation.
    """
    def __init__(
            self,
            analysis_name: str,
            field_name: str,
            result_type: str,
            energy_data=None,
            ghg_data=None,  # CO2e
            gas_data=None,  # individual gases
            streams_data=None,
            ci_results: list[tuple[str, pint.Quantity]] | None = None,
            energy_output: pint.Quantity | None = None,
            trial_num: int | None = None,
            audit_data=None,
            error: str | None = None,
    ):
        self.analysis_name = analysis_name
        self.field_name = field_name
        self.result_type = result_type
        self.ci_results = ci_results  # list of tuples of (node_name, CI)
        self.energy_output = energy_output
        self.energy = energy_data   # energy consumption data
        self.emissions = ghg_data   # TBD: change self.emissions to self.ghgs
        self.gases = gas_data
        self.streams = streams_data
        self.trial_num = trial_num
        self.audit_data = audit_data
        self.error = error

    def __str__(self):
        trl = "" if self.trial_num is None else f"trl:{self.trial_num} "
        return f"<{self.__class__.__name__} ana:{self.analysis_name} fld:{self.field_name} {trl}err:{self.error} res:{self.result_type}>"


class Aggregator:
    """
    Lightweight grouping of processes for results reporting purposes.

    This is not part of the Field/Process hierarchy - it simply holds references to process names
    that should be grouped together when calculating and reporting carbon intensity.
    """
    def __init__(self, name: str, process_refs: list[str]):
        """
        :param name: The name of this aggregator group
        :param process_refs: List of process class names that belong to this group
        """
        self.name = name
        self.process_refs = process_refs

    @classmethod
    def from_xml(cls, elt: etree.Element) -> Aggregator:
        """
        Instantiate an Aggregator from an XML element.

        Expected XML format:
        <Aggregator name="GroupName">
            <ProcessRef class="ProcessClass1"/>
            <ProcessRef class="ProcessClass2"/>
        </Aggregator>

        :param elt: (etree.Element) representing an <Aggregator> element
        :return: (Aggregator) instance populated from XML
        """
        name = elt.attrib['name']
        process_refs = [p.attrib['class'] for p in elt.findall('ProcessRef')]
        return cls(name, process_refs)

    def get_emission_rates(self, field: Field, analysis: Analysis):
        """
        Calculate total emission rates for all processes in this aggregator.

        :param field: The Field containing the processes
        :param analysis: The Analysis for GWP values
        :return: Emission rates DataFrame
        """
        from .emissions import Emissions

        total_emissions = Emissions()
        data = total_emissions.data
        data[data.columns] = ureg.Quantity(0.0, 't/d')

        for proc_name in self.process_refs:
            proc = field.process_dict.get(proc_name)
            if proc and proc.is_enabled():
                proc_data = proc.get_emission_rates(analysis)
                data += proc_data

        return total_emissions.rates(analysis.gwp)

    def __str__(self):
        return f"<Aggregator name='{self.name}' processes={self.process_refs}>"


def parse_aggregators(field_elt: etree.Element) -> dict[str, Aggregator]:
    """
    Parse Aggregator elements from a Field XML element.

    :param field_elt: (etree.Element) the <Field> element
    :return: dict mapping aggregator names to Aggregator instances
    """
    aggregators = {}
    for agg_elt in field_elt.findall('Aggregator'):
        agg = Aggregator.from_xml(agg_elt)
        aggregators[agg.name] = agg
    return aggregators


def _compute_partial_ci(emissions_data, energy: pint.Quantity) -> pint.Quantity:
    """
    Compute partial carbon intensity from emissions data and energy flow.

    :param emissions_data: Emissions DataFrame with GHG row
    :param energy: Energy flow rate at boundary
    :return: Carbon intensity in g/MJ
    """
    ghgs = emissions_data.sum(axis="columns")["GHG"]
    if not isinstance(ghgs, pint.Quantity):
        ghgs = ureg.Quantity(ghgs, "tonne/day")

    ci = ghgs / energy
    return ci.to("grams/MJ")


def get_field_result(
        field: Field,
        analysis: Analysis,
        result_type: str,
        aggregators: dict[str, Aggregator] | None = None,
        trial_num: int | None = None
) -> FieldResult:
    """
    Collect results from a Field run.

    This function is separate from the Field class to decouple results handling
    from the core simulation logic.

    :param field: (Field) the field that was run
    :param analysis: (Analysis) the analysis this field is part of
    :param result_type: (str) whether to return detailed or simple results.
        Legal values are DETAILED_RESULT or SIMPLE_RESULT.
    :param aggregators: (dict) optional dict of Aggregator objects for grouping results.
        If None, only process-level results are included.
    :param trial_num: (int) trial number, if running in MCS mode
    :return: (FieldResult) results
    """
    from .error import ZeroEnergyFlowError
    from .process import Boundary

    energy_data, ghg_data, gas_data = field.energy_and_emissions(analysis) \
        if result_type == DETAILED_RESULT else (None, None, None)

    # Get boundary energy for CI calculation
    try:
        energy = field.boundary_energy_flow_rate(analysis)
    except ZeroEnergyFlowError:
        _logger.error(
            f"Can't compute CI: zero energy flow at system boundary for {field}"
        )
        energy = None

    # Compute CI for each process
    ci_tuples = []
    if energy is not None:
        for proc in field.process_dict.values():
            if isinstance(proc, Boundary):
                continue
            if not proc.is_enabled():
                continue
            ci = _compute_partial_ci(proc.emissions.data, energy)
            ci_tuples.append((proc.name, ci))

        # Add aggregator CIs if provided
        if aggregators:
            for agg in aggregators.values():
                agg_emissions = agg.get_emission_rates(field, analysis)
                ci = _compute_partial_ci(agg_emissions, energy)
                ci_tuples.append((agg.name, ci))

    ci_results = (
        None if not ci_tuples
        else [("TOTAL", field.carbon_intensity)] + ci_tuples
    )

    dfs = [s.to_dataframe() for s in field.streams()]
    streams_data = pd.concat(dfs)

    result = FieldResult(
        analysis.name,
        field.name,
        result_type,
        trial_num=trial_num,
        ci_results=ci_results,
        energy_output=field.energy_output,
        energy_data=energy_data,
        ghg_data=ghg_data,
        gas_data=gas_data,
        streams_data=streams_data,
    )

    # Note: PostProcessor.run_post_processors() should be called by the caller
    # after this function returns, to keep post-processing separate from result collection.

    return result
