from __future__ import annotations

from opgee.common import elt_name, instantiate_subelts
from opgee.xml.container import _Container

try:
    from typing import TYPE_CHECKING
except ImportError:
    from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from opgee.core.field import Field


#
# This class is defined here rather than in container.py to avoid import loops and to
# allow the reference to Aggregator above.
#
class Aggregator(_Container):
    parent: Field

    def __init__(self, name, attr_dict=None, parent: Field | None = None):
        super().__init__(name, attr_dict=attr_dict)
        self.parent = parent
        self.enabled = False

    def add_children(self, aggs=None, procs=None):
        super().add_children(aggs=aggs, procs=procs)

    def set_enabled(self, enabled: bool = True):
        self.enabled = enabled

    @classmethod
    def from_xml(cls, elt, parent=None):
        """
        Instantiate an instance from an XML element

        :param elt: (etree.Element) representing a <Aggregator> element
        :param parent: (XmlInstantiable) the parent in the Model object
            hierarchy for the object created here
        :return: (Aggregator) instance populated from XML
        """
        from opgee.core.process import Process

        name = elt_name(elt)
        attr_dict = cls.instantiate_attrs(elt)
        obj = cls(name, attr_dict=attr_dict, parent=parent)

        aggs = instantiate_subelts(elt, Aggregator, parent=obj)
        procs = instantiate_subelts(elt, Process, parent=obj)

        obj.add_children(aggs=aggs, procs=procs)

        # Aggregators are disabled if they are empty or contain only disabled aggs & procs
        enabled = not all([not child.enabled for child in aggs + procs])
        obj.set_enabled(enabled)

        return obj
