import pandas as pd
from thermosteam import Chemical
from opgee.core.substances import HYDROCARBONS, NON_HYDROCARBON_GASES, PUBCHEM_CIDS

class ChemicalInfo:
    instance = None

    _chemical_dict: dict[str, Chemical]
    _mol_weights: pd.Series
    def __init__(self):
        dict_non_hydrocarbon = {name: Chemical(name) for name in NON_HYDROCARBON_GASES}
        self._chemical_dict = chemical_dict = {name : Chemical(f"PubChem={num}") for name, num in PUBCHEM_CIDS}
        chemical_dict.update(dict_non_hydrocarbon)
        self._mol_weights = pd.Series({name: chemical.MW for name, chemical in chemical_dict.items()},
                                      dtype="pint[g/mole]")

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = cls()

        return cls.instance

    @classmethod
    def chemical(cls, component_name):
        obj = cls.get_instance()
        return obj._chemical_dict[component_name]

    @classmethod
    def mol_weight(cls, component, with_units=True):
        obj = cls.get_instance()
        mw = obj._mol_weights.get(component)
        return mw if with_units else mw.m

    @classmethod
    def mol_weights(cls):
        obj = cls.get_instance()
        return obj._mol_weights

    @classmethod
    def names(cls):
        obj = cls.get_instance()
        return list(obj._mol_weights.keys())

