#
# GasPartition class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

import pandas as pd
from pint.facets.plain import PlainQuantity as Quantity

from ..combine_streams import combine_streams
from ..context import FieldContext
from ..core import STP, TemperaturePressure
from ..energy import EN_NATURAL_GAS
from ..error import OpgeeException
from ..import_export import N2, CO2_Flooding, NATURAL_GAS
from ..process import Process
from ..stream import PHASE_GAS, Stream
from ..thermodynamics import Gas
from ..units import ureg

from .shared import get_init_lifting_stream

_logger = logging.getLogger(__name__)


class GasPartition(Process):
    """
    Gas partition is to check the reasonable amount of gas goes to gas lifting and gas reinjection
    """
    iteration_tolerance = 0.000001

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas: Gas,
        imported_NG_comp: pd.Series,
        natural_gas_reinjection: bool,
        gas_lifting: bool,
        gas_flooding: bool,
        flood_gas_type: str,
        fraction_remaining_gas_inj: Quantity[float],
        oil_volume_rate: Quantity[float],
        WOR: Quantity[float],
        GLIR: Quantity[float],
        GFIR: Quantity[float],
        CO2_source: str,
        impurity_CH4_in_CO2: Quantity[float],
        impurity_N2_in_CO2: Quantity[float],
        N2_flooding_temp: Quantity[float],
        N2_flooding_press: Quantity[float],
        C1_flooding_temp: Quantity[float],
        C1_flooding_press: Quantity[float],
        CO2_flooding_temp: Quantity[float],
        CO2_flooding_press: Quantity[float],
        mol_per_scf: Quantity[float],
    ):
        super().__init__(name, ctx)

        # TODO: avoid process names in contents.
        self._required_inputs = [
            "gas for gas partition"
        ]

        self._required_outputs = [
            "exported gas",
            # also two possible output streams below: "lifting gas" and "gas"
        ]

        if natural_gas_reinjection:
            self._required_outputs.append("gas")

        if gas_lifting:
            self._required_outputs.append("lifting gas")

        self.gas = gas
        self.imported_NG_comp = imported_NG_comp
        self.imported_NG_mass_frac = gas.component_mass_fractions(imported_NG_comp)

        self.natural_gas_reinjection = natural_gas_reinjection
        self.gas_lifting = gas_lifting
        self.gas_flooding = gas_flooding
        self.flood_gas_type = flood_gas_type
        self.fraction_remaining_gas_inj = fraction_remaining_gas_inj
        self.oil_volume_rate = oil_volume_rate
        self.WOR = WOR
        self.GLIR = GLIR
        self.GFIR = GFIR
        self.CO2_source = CO2_source
        self.impurity_CH4_in_CO2 = impurity_CH4_in_CO2
        self.impurity_N2_in_CO2 = impurity_N2_in_CO2

        self.N2_flooding_tp = TemperaturePressure(N2_flooding_temp, N2_flooding_press)
        self.C1_flooding_tp = TemperaturePressure(C1_flooding_temp, C1_flooding_press)
        self.CO2_flooding_tp = TemperaturePressure(CO2_flooding_temp, CO2_flooding_press)

        self.gas_flooding_vol_rate = oil_volume_rate * GFIR
        self.mol_per_scf = mol_per_scf

        self.is_first_loop = True
        self.is_gas_flooding_visited = False
        self.reset_flag = False

    def run(self):
        self.print_running_msg()
        gas_lifting_vol_rate = self.oil_volume_rate * (1 + self.WOR) * self.GLIR

        exported_gas_stream = Stream("exported_gas_stream", tp=self.ctx.stp)

        if not self.all_streams_ready("gas for gas partition"):
            return

        input = self.find_input_streams("gas for gas partition", combine=True)
        if input.is_uninitialized():
            return
        exported_gas_stream.copy_flow_rates_from(input)

        if self.gas_lifting:
            lifting_gas_to_compressor = self.find_output_stream("lifting gas")
            if self.is_first_loop:
                init_stream = get_init_lifting_stream(
                    self.gas, input, gas_lifting_vol_rate
                )
                lifting_gas_to_compressor.copy_flow_rates_from(init_stream)
                self.is_first_loop = False

            iteration_series = (
                lifting_gas_to_compressor.components.gas - input.components.gas
            ).astype(float)
            iteration_series[iteration_series < 0] = 0

            if sum(iteration_series) >= self.iteration_tolerance:
                self.set_iteration_value(iteration_series)
                lifting_gas_to_compressor.copy_flow_rates_from(input)
                return

            exported_gas_stream.subtract_rates_from(
                lifting_gas_to_compressor, PHASE_GAS
            )

        if self.gas_flooding and not self.is_gas_flooding_visited:
            reinjected_gas_stream = Stream("reinjected_gas_stream", tp=self.ctx.stp)
            self.gas_flooding_setup(reinjected_gas_stream, exported_gas_stream)
            self.ctx.process_data["gas_flooding_stream"] = reinjected_gas_stream
            self.is_gas_flooding_visited = True

        if self.natural_gas_reinjection:
            reinjected_HC_stream = Stream("reinjected_HC_stream", tp=self.ctx.stp)
            NG_energy_flow_rate_needed = self.import_export.import_df[
                EN_NATURAL_GAS
            ].sum()
            reinjected_gas_energy_flow_rate = self.gas.energy_flow_rate(
                exported_gas_stream
            )
            if reinjected_gas_energy_flow_rate <= NG_energy_flow_rate_needed:
                reinjected_HC_stream.set_tp(exported_gas_stream.tp)
                exported_gas_stream.reset()
                exported_gas_stream.set_tp(reinjected_HC_stream.tp)
            else:
                fuel_stream = Stream("fuel_stream", tp=exported_gas_stream.tp)
                fuel_stream.copy_flow_rates_from(exported_gas_stream)
                fuel_fraction = (
                    NG_energy_flow_rate_needed / reinjected_gas_energy_flow_rate
                )
                fuel_stream.multiply_flow_rates(fuel_fraction)

                reinjected_HC_stream.copy_flow_rates_from(exported_gas_stream)
                reinjected_HC_stream.subtract_rates_from(fuel_stream)
                reinjected_HC_stream.multiply_flow_rates(
                    self.fraction_remaining_gas_inj
                )

                exported_gas_stream.subtract_rates_from(reinjected_HC_stream)
                exported_gas_stream.subtract_rates_from(fuel_stream)

            gas_to_reinjection = self.find_output_stream("gas")
            combined_gas_stream = reinjected_HC_stream
            if self.ctx.process_data.get("gas_flooding_stream") is not None:
                gas_flooding_stream = self.ctx.process_data.get("gas_flooding_stream")
                combined_gas_stream = combine_streams(
                    [gas_flooding_stream, reinjected_HC_stream]
                )

            gas_to_reinjection.copy_flow_rates_from(combined_gas_stream)
            self.ctx.process_data["NG_energy_rate_consumption"] = min(
                NG_energy_flow_rate_needed, reinjected_gas_energy_flow_rate
            )

        exported_gas = self.find_output_stream("exported gas")
        if self.ctx.process_data.get("is_input_from_well") is None:
            exported_gas.copy_flow_rates_from(exported_gas_stream)

        self.ctx.process_data["exported_gas"] = exported_gas
        if self.gas_lifting and not self.reset_flag:
            self.reset_iteration()
            self.reset_flag = True
        self.set_iteration_value(exported_gas.total_flow_rate())

    def gas_flooding_setup(self, reinjected_gas_stream, exported_gas_stream):
        """
        Set up the gas flooding system for this field.

        The method first checks the type of flooding gas used (either "N2", "NG", or "CO2").
        If the type is not recognized, an exception is raised.

        For each type of gas, the method calculates the mass flow rate, adjusts the reinjected
        gas stream, and updates process data for the field. It also takes care of different
        scenarios for each type of gas flooding (like source of CO2, required imported natural
        gas etc.).

        If the reinjected gas stream has a non-zero total flow rate, the flow rates are copied
        to the gas for the reinjection compressor.

        :param reinjected_gas_stream: (Stream) gas stream being reinjected into the reservoir
        :param exported_gas_stream: (Stream) gas stream being exported from the field
        :raises: OpgeeException if flood_gas_type is not in known gas types ("N2", "NG", "CO2")
        :return: None
        """

        known_types = ["N2", "NG", "CO2"]
        if self.flood_gas_type not in known_types:
            raise OpgeeException(
                f"{self.flood_gas_type} is not in the known gas type: {known_types}"
            )

        if self.flood_gas_type == "N2":
            N2_mass_rate = (
                self.gas_flooding_vol_rate * self.gas.component_gas_rho_STP["N2"]
            )
            reinjected_gas_stream.set_gas_flow_rate("N2", N2_mass_rate)
            reinjected_gas_stream.set_tp(self.N2_flooding_tp)
            self.ctx.process_data["N2_reinjection_volume_rate"] = self.gas_flooding_vol_rate

            self.import_export.set_import(self.name, N2, N2_mass_rate)
        elif self.flood_gas_type == "CO2":
            CO2_mass_rate = (
                self.gas_flooding_vol_rate * self.gas.component_gas_rho_STP["CO2"]
            )
            if self.ctx.process_data.get("CO2_flooding_rate_init") is None:
                self.ctx.process_data["CO2_flooding_rate_init"] = CO2_mass_rate
            prod_CO2_mass_rate = exported_gas_stream.gas_flow_rate("CO2")
            CO2_mass_rate = max(
                ureg.Quantity(0, "tonne/day"), CO2_mass_rate - prod_CO2_mass_rate
            )

            impurity_type = (
                "C1" if self.CO2_source == "Natural subsurface reservoir" else "N2"
            )
            impurity_rate = (
                self.impurity_CH4_in_CO2
                if impurity_type == "C1"
                else self.impurity_N2_in_CO2
            )
            impurity_mass_rate = CO2_mass_rate * impurity_rate
            reinjected_gas_stream.set_gas_flow_rate(impurity_type, impurity_mass_rate)

            reinjected_gas_stream.set_gas_flow_rate("CO2", CO2_mass_rate)
            reinjected_gas_stream.set_tp(self.CO2_flooding_tp)

            self.import_export.set_import(
                self.name, CO2_Flooding, CO2_mass_rate + impurity_mass_rate
            )
            self.ctx.process_data["CO2_mass_rate"] = CO2_mass_rate
        else:
            input_STP = Stream("input_stream_at_STP", tp=STP)
            if exported_gas_stream is None:
                exported_gas_mass_rate = ureg.Quantity(0, "tonne/day")
            else:
                exported_gas_mass_rate = exported_gas_stream.total_gas_rate()
                input_STP.copy_flow_rates_from(exported_gas_stream, tp=STP)

            exported_gas_volume_rate = exported_gas_mass_rate / self.gas.density(
                input_STP
            )

            NG_flooding_volume_rate = self.gas_flooding_vol_rate

            # The mass of produced processed NG is enough for NG flooding
            if NG_flooding_volume_rate < exported_gas_volume_rate:
                NG_flooding_mass_rate = NG_flooding_volume_rate * self.gas.density(
                    input_STP
                )
                reinjected_gas_series = (
                    NG_flooding_mass_rate
                    * self.gas.component_mass_fractions(
                        self.gas.component_molar_fractions(exported_gas_stream)
                    )
                )
                reinjected_gas_stream.set_rates_from_series(
                    reinjected_gas_series, PHASE_GAS
                )
                reinjected_gas_stream.set_tp(exported_gas_stream.tp)
                exported_gas_stream.subtract_rates_from(
                    reinjected_gas_stream, PHASE_GAS
                )

            # The imported NG is need for NG flooding
            else:
                imported_NG_series = (
                    (NG_flooding_volume_rate - exported_gas_volume_rate)
                    * self.imported_NG_comp
                    * self.mol_per_scf
                )
                imported_NG_series *= self.gas.component_MW[imported_NG_series.index]
                imported_NG_stream = Stream(
                    "imported_NG_stream", tp=self.C1_flooding_tp
                )
                imported_NG_stream.set_rates_from_series(imported_NG_series, PHASE_GAS)
                imported_NG_energy_rate = self.gas.energy_flow_rate(imported_NG_stream)

                reinjected_gas_stream = imported_NG_stream
                if exported_gas_stream is not None:
                    reinjected_gas_stream.add_flow_rates_from(exported_gas_stream)
                exported_gas_stream.reset()
                exported_gas_stream.set_tp(tp=STP)
                self.import_export.set_import(
                    self.name, NATURAL_GAS, imported_NG_energy_rate
                )

        gas_to_reinjection = self.find_output_stream("gas")
        if reinjected_gas_stream.total_flow_rate().m != 0:
            gas_to_reinjection.copy_flow_rates_from(reinjected_gas_stream)
