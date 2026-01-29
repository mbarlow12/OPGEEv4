#
# OPGEE Container class
#
# Author: Richard Plevin
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#
from __future__ import annotations

from typing import TYPE_CHECKING

from .attributes import AttrDefs, AttributeMixin
from .core import XmlInstantiable
from .emissions import Emissions
from .energy import Energy
from .import_export import ImportExport
from .log import getLogger
from .units import ureg

if TYPE_CHECKING:
    from .analysis import Analysis
    from .process import Process

_logger = getLogger(__name__)


class Container(AttributeMixin, XmlInstantiable):
    """
    Generic hierarchical node element that contains Processes.

    Note: Aggregators are no longer part of the Container hierarchy.
    They are handled separately in the results module for grouping purposes.
    """

    def __init__(self, name: str, attr_dict: dict | None = None, parent=None):
        AttributeMixin.__init__(self, attr_dict=attr_dict)
        XmlInstantiable.__init__(self, name, parent=parent)

        self.attr_defs = AttrDefs.get_instance()

        self.emissions = Emissions()
        self.energy = Energy()
        self.import_export = ImportExport()

        # Process instances directly inside this Container
        self.procs: list[Process] | None = None

    def add_children(self, procs: list[Process] | None = None, **kwargs):
        """
        Add child processes to this container.

        :param procs: List of Process instances to add as children
        """
        self.procs = self.adopt(procs)

    def _children(self) -> list[Process]:
        """
        Return a list of all children. External callers should use children() instead,
        as it respects the self.is_enabled() setting.
        """
        return self.procs if self.procs else []

    def children(self, include_disabled: bool = False) -> list[Process]:
        """
        Return all directly contained Process objects below this Container.

        :param include_disabled: (bool) whether to include disabled nodes.
        :return: (list of Processes)
        """
        objs = self._children()
        return [obj for obj in objs if (include_disabled or obj.is_enabled())]

    def validate(self):
        for child in self.children():
            child.validate()

    def descendant_procs(self, include_disabled: bool = False) -> list[Process]:
        """
        Return all Processes contained in the current Container.

        :param include_disabled: (bool) whether to include disabled nodes.
        :return: (list of Processes)
        """
        procs = []

        for obj in self.children():
            if include_disabled or obj.is_enabled():
                procs.append(obj)

        return procs

    def print_running_msg(self):
        _logger.debug(f"Running {type(self)} name='{self.name}'")

    def get_energy_rates(self):
        """
        Return the energy consumption rates by summing those of our children nodes,
        recursively working our way down the Container hierarchy, and storing each
        result at each container level.
        """
        self.energy.reset()
        data = self.energy.data

        for child in self.children():
            child_data = child.get_energy_rates()
            data += child_data

        return data

    def get_emission_rates(self, analysis: Analysis, procs_to_exclude=None):
        """
        Return the emission rates (Series) including the calculated GHG values
        based on the current choice of GWP values in the enclosing Model.

        :return: (pandas.Series) the emissions Series.
        """
        data = self.emissions.data
        data[data.columns] = ureg.Quantity(0.0, 't/d')

        for child in self.children():
            if not procs_to_exclude or child not in procs_to_exclude:
                child_data = child.get_emission_rates(analysis, procs_to_exclude=procs_to_exclude)
                data += child_data

        # compute CO2eq using chosen GWP values
        data = self.emissions.rates(analysis.gwp)
        return data

    def get_net_imported_product(self):
        """
        Return a energy rate (water is mass rate) of net imported product.
        The positive value means the amount needs imported, while the negative value mean the amount needs exported

        """
        imp_exp = self.import_export.imports_exports()
        data = imp_exp[ImportExport.NET_IMPORTS]

        for child in self.children():
            child_data = child.get_net_imported_product()
            data += child_data

        return data
