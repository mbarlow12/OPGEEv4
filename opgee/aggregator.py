from opgee.common import elt_name, instantiate_subelts
from opgee.core.process import Process
from opgee.xml.container import Container


#
# This class is defined here rather than in container.py to avoid import loops and to
# allow the reference to Aggregator above.
#
class Aggregator(Container):
    def __init__(self, name, attr_dict=None, parent=None):
        super().__init__(name, attr_dict=attr_dict, parent=parent)

    def add_children(self, aggs=None, procs=None):
        super().add_children(aggs=aggs, procs=procs)

    @classmethod
    def from_xml(cls, elt, parent=None):
        """
        Instantiate an instance from an XML element

        :param elt: (etree.Element) representing a <Aggregator> element
        :param parent: (XmlInstantiable) the parent in the Model object
            hierarchy for the object created here
        :return: (Aggregator) instance populated from XML
        """
        name = elt_name(elt)
        attr_dict = cls.instantiate_attrs(elt)
        obj = cls(name, attr_dict=attr_dict, parent=parent)

        aggs = instantiate_subelts(elt, Aggregator, parent=obj)
        procs = instantiate_subelts(elt, Process, parent=obj)

        obj.add_children(aggs=aggs, procs=procs)

        # Aggregators are disabled if they are empty or contain only disabled aggs & procs
        enabled = not all([not child.is_enabled() for child in aggs + procs])
        obj.set_enabled(enabled)

        return obj
