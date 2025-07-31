from enum import Enum
from typing import Final

import pandas as pd

class Phase(Enum):
    SOLID = "solid"
    LIQUID = "liquid"
    GAS = "gas"


PUBCHEM_CIDS: Final[tuple[tuple[str, int], ...]] = (
    ("C1", 297),
    ("C2", 6324),
    ("C3", 6334),
    ("C4", 7843),
    ("C5", 8003),
    ("C6", 8058),
    ("C7", 8900),
    ("C8", 356),
    ("C9", 8141),
    ("C10", 15600),
    ("C11", 14257),
    ("C12", 8182),
    ("C13", 12388),
    ("C14", 12389),
    ("C15", 12391),
    ("C16", 11006),
    ("C17", 12398),
    ("C18", 11635),
    ("C19", 12401),
    ("C20", 8222),
    ("C21", 12403),
    ("C22", 12405),
    ("C23", 12534),
    ("C24", 12592),
    ("C25", 12406),
    ("C26", 12407),
    ("C27", 11636),
    ("C28", 12408),
    ("C29", 12409),
    ("C30", 12535),
)
HYDROCARBONS: Final[tuple[str, ...]] = tuple(cnum for cnum, _ in PUBCHEM_CIDS)
NON_HYDROCARBON_GASES: Final[tuple[str, ...]] = (
    "N2",
    "O2",
    "CO2",
    "H2O",
    "H2",
    "H2S",
    "SO2",
    "CO",
    "Argon",
    "Neon",
    "Helium",
    "Krypton",
    "Xenon",
)
_carbon_nums, _cids = tuple(zip(*PUBCHEM_CIDS))
PUBCHEM_CID_SERIES: Final[pd.Series] = pd.Series(
    data=_cids,
    index=pd.Index(_carbon_nums),
)
