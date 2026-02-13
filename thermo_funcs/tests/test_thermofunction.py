"""
Tests ported from tests/test_thermofunction.py.

Every test uses the purely-functional API from thermo_funcs instead of the
original OOP methods on Oil/Gas/Water instances.  Expected values are kept
identical to the original test suite.
"""
import pandas as pd
import pytest

from thermo_funcs.units import ureg, Q_
from thermo_funcs.types import StreamInfo, TemperaturePressure
from thermo_funcs.constants import PHASE_GAS

from .conftest import TEST_API, TEST_GOR, TEST_TP, TEST_RES_TP, TEST_GAS_COMP, TEST_TDS

# ===================================================================
# Oil tests
# ===================================================================

class TestOil:

    def test_gas_specific_gravity(self, gas_SG):
        assert gas_SG == Q_(pytest.approx(0.620513719), "frac")

    def test_bubble_point_solution_GOR(self):
        from thermo_funcs.oil import bubble_point_solution_GOR
        gor_bubble = bubble_point_solution_GOR(TEST_GOR)
        assert gor_bubble == Q_(pytest.approx(2822.361), "scf/bbl_oil")

    def test_oil_specific_gravity(self, oil_SG):
        from thermo_funcs.oil import specific_gravity_from_API
        computed = specific_gravity_from_API(TEST_API)
        assert computed == Q_(pytest.approx(oil_SG.magnitude), "frac")

    def test_oil_API_from_SG(self, oil_SG):
        from thermo_funcs.oil import API_from_specific_gravity
        api = API_from_specific_gravity(oil_SG)
        assert api == Q_(pytest.approx(TEST_API.magnitude), "degAPI")

    def test_reservoir_solution_GOR(self, oil_SG, gas_SG):
        from thermo_funcs.oil import reservoir_solution_GOR
        res_gor = reservoir_solution_GOR(oil_SG, gas_SG, TEST_GOR, TEST_RES_TP)
        assert res_gor == Q_(pytest.approx(291.03397), "scf/bbl_oil")

    def test_bubble_point_pressure(self, oil_SG, gas_SG):
        from thermo_funcs.oil import bubble_point_pressure
        p = bubble_point_pressure(oil_SG, gas_SG, TEST_GOR, TEST_RES_TP.T.to("rankine"))
        assert p == Q_(pytest.approx(9235.176121), "psia")

    def test_solution_gas_oil_ratio(self, oil_SG, gas_SG):
        from thermo_funcs.oil import solution_gas_oil_ratio_at
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={},
        )
        sol_gor = solution_gas_oil_ratio_at(stream, oil_SG, gas_SG, TEST_GOR)
        assert sol_gor == Q_(pytest.approx(290.890838), "scf/bbl_oil")

    def test_saturated_formation_volume_factor(self, oil_SG, gas_SG):
        from thermo_funcs.oil import saturated_formation_volume_factor
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={},
        )
        sat_fvf = saturated_formation_volume_factor(stream, oil_SG, gas_SG, TEST_GOR)
        assert sat_fvf == Q_(pytest.approx(1.19867887), "frac")

    def test_unsat_formation_volume_factor(self, oil_SG, gas_SG):
        from thermo_funcs.oil import unsat_formation_volume_factor
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={},
        )
        unsat_fvf = unsat_formation_volume_factor(stream, oil_SG, gas_SG, TEST_GOR, TEST_RES_TP)
        assert unsat_fvf == Q_(pytest.approx(1.22717505), "frac")

    def test_isothermal_compressibility(self, oil_SG):
        from thermo_funcs.oil import isothermal_compressibility
        co = isothermal_compressibility(oil_SG)
        assert co == Q_(pytest.approx(3.0528295800365155e-6), "pa**-1")

    def test_isothermal_compressibility_extended(self, oil_SG, gas_SG):
        from thermo_funcs.oil import isothermal_compressibility_extended
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={},
        )
        co_x = isothermal_compressibility_extended(stream, oil_SG, gas_SG, TEST_GOR)
        assert co_x == Q_(0.0, "pa**-1")

    def test_formation_volume_factor(self, oil_SG, gas_SG):
        from thermo_funcs.oil import formation_volume_factor
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={},
        )
        fvf = formation_volume_factor(stream, oil_SG, gas_SG, TEST_GOR, TEST_RES_TP)
        assert fvf == Q_(pytest.approx(1.19867887), "frac")

    def test_oil_density(self, oil_SG, gas_SG, dry_air):
        from thermo_funcs.oil import density
        from thermo_funcs.water import water_density
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={},
        )
        water_rho_stp = water_density(TEST_TDS)
        rho = density(stream, oil_SG, gas_SG, TEST_GOR, TEST_RES_TP, water_rho_stp, dry_air)
        assert rho == Q_(pytest.approx(47.0100087, rel=10e-5), "lb/ft**3")

    def test_oil_mass_energy_density(self, oil_LHV_mass):
        assert oil_LHV_mass == Q_(pytest.approx(18279.816), "btu/lb")

    def test_oil_volume_flow_rate(self, oil_SG, gas_SG, dry_air):
        from thermo_funcs.oil import volume_flow_rate
        from thermo_funcs.water import water_density
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={"oil": Q_(276.534764, "tonne/day")},
        )
        water_rho_stp = water_density(TEST_TDS)
        vfr = volume_flow_rate(stream, oil_SG, gas_SG, TEST_GOR, TEST_RES_TP, water_rho_stp, dry_air)
        assert vfr == Q_(pytest.approx(2309.80926, rel=10e-5), "bbl_oil/day")

    def test_oil_volume_energy_density(self, oil_SG, gas_SG, dry_air):
        from thermo_funcs.oil import volume_energy_density
        from thermo_funcs.water import water_density
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={},
            API=TEST_API,
        )
        water_rho_stp = water_density(TEST_TDS)
        ved = volume_energy_density(stream, oil_SG, gas_SG, TEST_GOR, TEST_RES_TP, water_rho_stp, dry_air)
        assert ved == Q_(pytest.approx(4.82480434, rel=10e-5), "mmBtu/bbl_oil")

    def test_oil_energy_flow_rate(self):
        from thermo_funcs.oil import energy_flow_rate
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={
                "oil": Q_(273.831958, "tonne/day"),
                "PC": Q_(0.0, "tonne/day"),
            },
            API=TEST_API,
        )
        efr = energy_flow_rate(stream, TEST_API)
        assert efr == Q_(pytest.approx(11035.4544), "mmbtu/day")

    def test_oil_specific_heat(self):
        from thermo_funcs.oil import specific_heat
        cp = specific_heat(TEST_API, Q_(127.5, "degF"))
        assert cp == Q_(pytest.approx(0.48734862), "btu/lb/degF")

    def test_liquid_fuel_composition(self):
        from thermo_funcs.oil import liquid_fuel_composition
        comp = liquid_fuel_composition(Q_(10, "degAPI"))
        assert comp["C"] == Q_(pytest.approx(71.432), "mol/kg")


# ===================================================================
# Gas tests
# ===================================================================

class TestGas:

    def test_total_molar_flow_rate(self, gas_stream, props):
        from thermo_funcs.gas import total_molar_flow_rate
        result = total_molar_flow_rate(gas_stream, props)
        assert result == Q_(pytest.approx(6122349.16), "mol/day")

    def test_molar_flow_rate(self, gas_stream, props):
        from thermo_funcs.gas import molar_flow_rate
        result = molar_flow_rate(gas_stream, "C1", props)
        assert result == Q_(pytest.approx(5459905.78), "mol/day")

    def test_component_molar_fraction_N2(self, gas_stream, props):
        from thermo_funcs.gas import component_molar_fraction
        result = component_molar_fraction("N2", gas_stream, props)
        assert result == Q_(pytest.approx(0.0285991048), "frac")

    def test_component_molar_fraction_C1(self, gas_stream, props):
        from thermo_funcs.gas import component_molar_fraction
        result = component_molar_fraction("C1", gas_stream, props)
        assert result == Q_(pytest.approx(0.891799149), "frac")

    def test_component_mass_fraction(self, props):
        from thermo_funcs.gas import component_mass_fractions
        molar_fracs = pd.Series(
            [0.004, 0.9666, 0.02, 0.01],
            index=["N2", "C1", "C2", "C3"],
            dtype="pint[mol/mol]",
        )
        result = component_mass_fractions(molar_fracs, props)
        assert result["C1"] == Q_(pytest.approx(0.9307131413113588))

    def test_specific_gravity(self, gas_stream, props, dry_air):
        from thermo_funcs.gas import specific_gravity
        result = specific_gravity(gas_stream, props, dry_air)
        assert result == Q_(pytest.approx(0.620514541), "frac")

    def test_ratio_of_specific_heat(self, gas_stream, props):
        from thermo_funcs.gas import ratio_of_specific_heat
        result = ratio_of_specific_heat(gas_stream, props)
        assert result == Q_(pytest.approx(1.28972962, rel=10e-4), "frac")

    def test_gas_heat_capacity(self, gas_stream):
        from thermo_funcs.gas import heat_capacity
        result = heat_capacity(gas_stream)
        assert result == Q_(pytest.approx(132557.175, rel=10e-3), "btu/degF/day")

    def test_uncorrected_pseudocritical_temperature(self, gas_stream, props):
        from thermo_funcs.gas import uncorrected_pseudocritical_temperature_and_pressure
        T_pc, _ = uncorrected_pseudocritical_temperature_and_pressure(gas_stream, props)
        assert T_pc == Q_(pytest.approx(361.164867, rel=10e-5), "rankine")

    def test_uncorrected_pseudocritical_pressure(self, gas_stream, props):
        from thermo_funcs.gas import uncorrected_pseudocritical_temperature_and_pressure
        _, P_pc = uncorrected_pseudocritical_temperature_and_pressure(gas_stream, props)
        assert P_pc == Q_(pytest.approx(669.895774, rel=10e-5), "psia")

    def test_corrected_pseudocritical_temperature(self, gas_stream, props):
        from thermo_funcs.gas import corrected_pseudocritical_temperature
        result = corrected_pseudocritical_temperature(gas_stream, props)
        assert result == Q_(pytest.approx(361.164867, rel=10e-5), "rankine")

    def test_corrected_pseudocritical_pressure(self, gas_stream, props):
        from thermo_funcs.gas import corrected_pseudocritical_pressure
        result = corrected_pseudocritical_pressure(gas_stream, props)
        assert result == Q_(pytest.approx(669.895774, rel=10e-5), "psia")

    def test_reduced_temperature(self, gas_stream, props):
        from thermo_funcs.gas import reduced_temperature
        result = reduced_temperature(gas_stream, props)
        assert result == Q_(pytest.approx(1.82650656, rel=10e-5), "frac")

    def test_reduced_pressure(self, gas_stream, props):
        from thermo_funcs.gas import reduced_pressure
        result = reduced_pressure(gas_stream, props)
        assert result == Q_(pytest.approx(2.32274939, rel=10e-5), "frac")

    def test_Z_factor(self, gas_stream, props):
        from thermo_funcs.gas import reduced_temperature, reduced_pressure, Z_factor
        Tr = reduced_temperature(gas_stream, props)
        Pr = reduced_pressure(gas_stream, props)
        result = Z_factor(Tr, Pr)
        assert result == Q_(pytest.approx(0.922374916, rel=10e-5), "frac")

    def test_volume_factor(self, gas_stream, props):
        from thermo_funcs.gas import volume_factor
        result = volume_factor(gas_stream, props)
        assert result == Q_(pytest.approx(0.0109559824, abs=0.0005), "frac")

    def test_gas_density(self, gas_stream, props, dry_air):
        from thermo_funcs.gas import gas_density
        result = gas_density(gas_stream, props, dry_air)
        assert result == Q_(pytest.approx(0.0686303423, rel=10e-4), "tonne/m**3")

    def test_gas_viscosity(self, gas_stream, props, dry_air):
        from thermo_funcs.gas import viscosity
        result = viscosity(gas_stream, props, dry_air)
        assert result == Q_(pytest.approx(0.0171786183, rel=10e-5), "centipoise")

    def test_molar_weight(self, gas_stream, props):
        from thermo_funcs.gas import molar_weight
        result = molar_weight(gas_stream, props)
        assert result == Q_(pytest.approx(17.97378), "g/mol")

    def test_molar_weight_from_molar_fracs(self, props):
        from thermo_funcs.gas import molar_weight_from_molar_fracs
        molar_fracs = pd.Series(
            [0.004, 0.9666, 0.02, 0.01],
            index=["N2", "C1", "C2", "C3"],
            dtype="pint[mol/mol]",
        )
        result = molar_weight_from_molar_fracs(molar_fracs, props)
        assert result == Q_(pytest.approx(16.6610324), "g/mol")

    def test_gas_volume_flow_rate(self, gas_stream, props, dry_air):
        from thermo_funcs.gas import gas_volume_flow_rate
        result = gas_volume_flow_rate(gas_stream, props, dry_air)
        assert result == Q_(pytest.approx(1603.39805, rel=10e-4), "m**3/day")

    def test_gas_volume_flow_rate_STP(self, props):
        from thermo_funcs.gas import gas_volume_flow_rate_STP
        gas_rates = pd.Series(
            {"N2": 1.0638, "C1": 147.1241, "C2": 5.7095, "C3": 4.1863},
            dtype="pint[tonne/day]",
        )
        s = StreamInfo(tp=TEST_TP, gas_flow_rates=gas_rates, liquid_flow_rates={})
        result = gas_volume_flow_rate_STP(s, props).to("mmscf/day")
        assert result == Q_(pytest.approx(7.94253339, rel=1e-2), "mmscf/day")

    def test_gas_volume_flow_rates_STP(self, props):
        from thermo_funcs.gas import gas_volume_flow_rates_STP
        gas_rates = pd.Series(
            {"N2": 1.0638, "C1": 147.1241, "C2": 5.7095, "C3": 4.1863},
            dtype="pint[tonne/day]",
        )
        s = StreamInfo(tp=TEST_TP, gas_flow_rates=gas_rates, liquid_flow_rates={})
        result = gas_volume_flow_rates_STP(s, props)
        assert result["C1"].to("mmscf/day") == Q_(pytest.approx(7.66776813, rel=10e-3), "mmscf/day")

    def test_gas_mass_energy_density(self, gas_stream, props):
        from thermo_funcs.gas import mass_energy_density
        result = mass_energy_density(gas_stream, props)
        assert result == Q_(pytest.approx(46.9246768), "MJ/kg")

    def test_gas_mass_energy_density_from_molar_fracs(self, props):
        from thermo_funcs.gas import mass_energy_density_from_molar_fracs
        molar_fracs = pd.Series(
            [0.004, 0.9666, 0.02, 0.01],
            index=["N2", "C1", "C2", "C3"],
            dtype="pint[mol/mol]",
        )
        result = mass_energy_density_from_molar_fracs(molar_fracs, props)
        assert result == Q_(pytest.approx(49.7703477), "MJ/kg")

    def test_combustion_enthalpy(self):
        from thermo_funcs.gas import combustion_enthalpy
        molar_fracs = pd.Series(
            [9.2878, 2.4624, 0.0035, 0.2399],
            index=["N2", "O2", "CO2", "H2O"],
            dtype="pint[mol/mol]",
        )
        temperature = Q_(80.33, "degF")
        result = combustion_enthalpy(molar_fracs, temperature, PHASE_GAS)
        assert result["H2O"] == Q_(pytest.approx(2162.8143928135105), "joule/mole")

    def test_volume_energy_density(self, gas_stream, props):
        from thermo_funcs.gas import volume_energy_density
        result = volume_energy_density(gas_stream, props)
        assert result == Q_(pytest.approx(957.960214, rel=10e-3), "btu/ft**3")

    def test_energy_flow_rate(self, gas_stream, props):
        from thermo_funcs.gas import energy_flow_rate
        result = energy_flow_rate(gas_stream, props)
        assert result == Q_(pytest.approx(4894.21783), "mmBtu/day")


# ===================================================================
# Water tests
# ===================================================================

class TestWater:

    def test_water_density(self):
        from thermo_funcs.water import water_density
        result = water_density(TEST_TDS)
        assert result == Q_(pytest.approx(1002.4871, rel=1e-5), "kg/m**3")

    def test_water_volume_rate(self):
        from thermo_funcs.water import water_volume_flow_rate
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={"H2O": Q_(1962.61672, "tonne/day")},
        )
        result = water_volume_flow_rate(stream, TEST_TDS)
        assert result == Q_(pytest.approx(12313.8616, rel=1e-5), "bbl_water/day")

    def test_water_specific_heat(self):
        from thermo_funcs.water import water_specific_heat
        result = water_specific_heat(Q_(200, "degF"))
        assert result == Q_(pytest.approx(0.450496339, rel=10e-4), "btu/lb/degF")

    def test_water_heat_capacity(self):
        from thermo_funcs.water import water_heat_capacity
        stream = StreamInfo(
            tp=TEST_TP,
            gas_flow_rates=pd.Series(dtype="pint[tonne/day]"),
            liquid_flow_rates={"H2O": Q_(1962.61672, "tonne/day")},
        )
        result = water_heat_capacity(stream)
        assert result == Q_(pytest.approx(1949220.72, rel=10e-4), "btu/degF/day")

    def test_water_saturated_temperature(self):
        from thermo_funcs.water import saturated_temperature
        result = saturated_temperature(Q_(1122.00, "psia"))
        assert result.to("degC") == Q_(pytest.approx(292.660571, abs=0.025), "degC")

    def test_water_enthalpy_PT(self):
        from thermo_funcs.water import enthalpy_PT
        result = enthalpy_PT(
            Q_(13.7895, "bar"),
            Q_(60.0, "degC"),
            Q_(3.94e7, "kg/day"),
        )
        assert result == Q_(pytest.approx(9940445.92), "MJ/day")

    def test_steam_enthalpy(self):
        from thermo_funcs.water import steam_enthalpy
        result = steam_enthalpy(
            Q_(77.359177, "bar"),
            Q_(0.7, "frac"),
            Q_(5.52e7, "kg/day"),
        )
        assert result == Q_(pytest.approx(1.28341315e8), "MJ/day")
