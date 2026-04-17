#
# GasReinjectionCompressor class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..emissions import EM_FUGITIVES
from ..energy import EN_ELECTRICITY
from ..process import Process
from ..thermodynamics import Gas
from ..units import ureg
from .compressor import Compressor
from .shared import get_energy_carrier

_logger = logging.getLogger(__name__)


class GasReinjectionCompressor(Process):
    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        gas: Gas,
        res_press: Quantity[float],
        prime_mover_type: str,
        eta_compressor: Quantity[float],
        loss_rate: Quantity[float],
        air_separation_energy_intensity: Quantity[float],
    ):
        super().__init__(name, ctx)

        self.gas = gas
        self.res_press = res_press
        self.prime_mover_type = prime_mover_type
        self.eta_compressor = eta_compressor
        self.loss_rate = loss_rate
        self.air_separation_energy_intensity = air_separation_energy_intensity

        self._required_inputs = [
            "gas"
        ]

        self._required_outputs = [
            "gas"
        ]

    def run(self):
        self.print_running_msg()

        # TODO: unclear how this can work if the input stream doesn't exist
        input = self.find_input_stream("gas", raiseError=False)

        if input is None or input.is_uninitialized():
            return

        gas_fugitives = self.set_gas_fugitives(input, self.loss_rate)

        gas_to_well = self.find_output_stream("gas")
        gas_to_well.copy_flow_rates_from(input)
        gas_to_well.subtract_rates_from(gas_fugitives)

        discharge_press = self.res_press + ureg.Quantity(500., "psi")
        overall_compression_ratio = discharge_press / input.tp.P
        energy_consumption, output_temp, _ = Compressor.get_compressor_energy_consumption(
            self.gas,
            self.prime_mover_type,
            self.eta_compressor,
            overall_compression_ratio,
            input)

        gas_to_well.tp.set(T=output_temp, P=discharge_press)

        self.set_iteration_value(gas_to_well.total_flow_rate())

        # energy-use
        energy_use = self.energy
        energy_carrier = get_energy_carrier(self.prime_mover_type)
        energy_use.set_rate(energy_carrier, energy_consumption)

        if self.ctx.process_data.get("N2_reinjection_volume_rate"):
            N2_volume_rate = self.ctx.process_data["N2_reinjection_volume_rate"]
            energy_consump_air_separation = N2_volume_rate * self.air_separation_energy_intensity
            energy_use.set_rate(EN_ELECTRICITY, energy_consump_air_separation)

        # import/export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
