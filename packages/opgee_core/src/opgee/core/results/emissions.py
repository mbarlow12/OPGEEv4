from collections.abc import Iterable
from typing import Final, Literal

from pandas import DataFrame, Series

from opgee.core.emissions import GASES, Emissions, GHGEmitter

GHG: Final[str] = "GHG"

GWP = Literal[20, 100]


def compute_ghg(emissions: Emissions, gwp: Series) -> DataFrame:
    """
    Compute and store total CO2-eq GHGs using the given Series of GWP values.

    :param gwp: (pandas.Series) the GWP values to use, expected to have the
        same index as self.data (i.e., Emissions.emissions)
    :return: (pandas.DataFrame) the Emissions data with total ghg
    """
    data = emissions.data.copy(deep=True)
    product = data.T[GASES] * gwp
    data.loc[GHG] = product.sum(axis="columns")
    return data


def compute_emitters_ghg(emitters: Iterable[GHGEmitter], gwp: Literal[20, 100]): ...
