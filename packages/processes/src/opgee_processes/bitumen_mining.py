#
# BitumenMining class
#
# Author: Wennan Long
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
import logging

import pandas as pd
from pint.facets.plain import PlainQuantity as Quantity

from ..context import FieldContext
from ..core import TemperaturePressure
from ..emissions import EM_FUGITIVES
from ..energy import EN_NATURAL_GAS, EN_ELECTRICITY, EN_DIESEL
from ..error import OpgeeException
from ..process import Process
from ..stream import Stream
from ..thermodynamics import Gas, Oil, Water
from ..units import ureg

_logger = logging.getLogger(__name__)


class BitumenMining(Process):
    # TODO: documentation below describes input streams that do not appear in the code.
    """
        This process takes input streams and produces output streams as part of an
        oil sands mining operation.

        Inputs:
            - Streams from bitumen path dictionary

        Outputs:
            - Bitumen stream for upgrading or dilution
            - Gas stream for partition

        Attributes:
            - oil_sands_mine: Name of the oil sands mine
            - API_bitumen: API gravity of the bitumen
            - bitumen_SG: Specific gravity of the bitumen
            - mined_bitumen_tp: Temperature and pressure of the mined bitumen
            - oil_prod_rate: Oil production rate
            - upgrader_type: Type of upgrader used
            - gas_comp: Gas composition
            - FOR: Flaring oil ratio
            - VOR: Venting oil ratio
            - bitumen_path_dict: Dictionary of possible paths for the bitumen stream
            - water_density: Density of water
            - CH4_loss_rate: Methane loss rate
    """

    def __init__(
        self,
        name: str,
        ctx: FieldContext,
        oil_sands_mine: str,
        API: Quantity[float],
        mined_bitumen_t: Quantity[float],
        mined_bitumen_p: Quantity[float],
        downhole_pump: bool,
        oil_volume_rate: Quantity[float],
        upgrader_type: str,
        gas_comp: pd.Series,
        FOR: Quantity[float],
        CH4_loss_rate: Quantity[float],
        mining_energy_intensity_df: pd.DataFrame,
        NG_heating_value: Quantity[float],
        diesel_LHV: Quantity[float],
        oil: Oil,
        water: Water,
        gas: Gas,
    ):
        super().__init__(name, ctx)

        self._required_outputs = [
            # TODO: If the process names were avoided, we might have just one output stream
            #  with, say, "heavy oil". Should describe the contents, not the destination.
            ("oil for upgrading",     # TODO: avoid process names in contents.
             "oil for dilution"),     # TODO: avoid process names in contents.

            "gas for partition",
        ]

        self.oil_sands_mine = oil_sands_mine
        self.API = API
        self.mined_bitumen_t = mined_bitumen_t
        self.mined_bitumen_p = mined_bitumen_p
        self.mined_bitumen_tp = TemperaturePressure(mined_bitumen_t, mined_bitumen_p)
        self.downhole_pump = downhole_pump
        self.oil_volume_rate = oil_volume_rate
        self.upgrader_type = upgrader_type
        self.gas_comp = gas_comp
        self.FOR = FOR
        self.CH4_loss_rate = CH4_loss_rate
        self.mining_energy_intensity_df = mining_energy_intensity_df
        self.NG_heating_value = NG_heating_value
        self.diesel_LHV = diesel_LHV
        self.oil = oil
        self.water = water
        self.gas = gas

        self.bitumen_path_dict = {"Integrated with upgrader": "oil for upgrading",
                                  "Integrated with diluent": "oil for dilution",
                                  "Integrated with both": "oil for dilution"}

        self.bitumen_SG = oil.specific_gravity(API)
        self.water_density = water.density()

    def run(self):
        self.print_running_msg()

        bitumen_mass_rate = self.oil_volume_rate * self.bitumen_SG * self.water_density
        try:
            output = self.bitumen_path_dict[self.oil_sands_mine]
        except KeyError:
            raise OpgeeException(f"{self.name} bitumen is not recognized:{self.oil_sands_mine}."
                                 f"Must be one of {list(self.bitumen_path_dict.keys())}")
        output_bitumen = self.find_output_stream(output)

        output_tp = self.mined_bitumen_tp
        output_bitumen.\
            set_liquid_flow_rate("oil", bitumen_mass_rate, tp=output_tp)
        output_bitumen.set_API(self.API)
        self.set_iteration_value(output_bitumen.total_flow_rate())

        d = self.mining_energy_intensity_df
        mining_intensity_table = d[self.oil_sands_mine]
        unit_col = d["Units"]

        temp = self.oil_volume_rate * self.gas.component_gas_rho_STP["C1"]
        mine_flaring_rate = self.FOR * temp
        mine_CH4_rate = self.CH4_loss_rate * temp

        gas_fugitives = Stream("gas_fugitives", tp=self.ctx.stp)
        gas_fugitives.set_gas_flow_rate("C1", mine_CH4_rate)

        gas_flaring = self.find_output_stream("gas for partition")
        gas_flaring.set_gas_flow_rate("C1", mine_flaring_rate)
        gas_flaring.set_tp(self.ctx.stp)

        # energy-use
        energy_use = self.energy
        NG_consumption = \
            self.oil_volume_rate * ureg.Quantity(mining_intensity_table["Natural gas use"],
                                                 unit_col["Natural gas use"]) * self.NG_heating_value
        diesel_consumption = \
            self.oil_volume_rate * ureg.Quantity(mining_intensity_table["Diesel fuel use"],
                                                 unit_col["Diesel fuel use"]) * self.diesel_LHV
        electricity_consumption = \
            self.oil_volume_rate * ureg.Quantity(mining_intensity_table["Electricity use"], unit_col["Electricity use"])
        energy_use.set_rate(EN_NATURAL_GAS, NG_consumption.to("mmBtu/day"))
        energy_use.set_rate(EN_DIESEL, diesel_consumption.to("mmBtu/day"))
        energy_use.set_rate(EN_ELECTRICITY, electricity_consumption.to("mmBtu/day"))

        # import and export
        self.set_import_from_energy(energy_use)

        # emissions
        self.set_combustion_emissions()
        self.emissions.set_from_stream(EM_FUGITIVES, gas_fugitives)
