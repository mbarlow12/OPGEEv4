
from lxml.etree import _Element as Element

from opgee.field import Field
from opgee.process import Aggregator
from opgee.xml.adapters.process import process_from_xml


def aggregator_from_xml(elt: Element, field: Field | Aggregator) -> Aggregator:
    name = elt.attrib.get("name")
    attr_dict = Aggregator.instantiate_attrs(elt)
    obj = Aggregator(name, attr_dict=attr_dict, parent=field)

    aggs = [aggregator_from_xml(elt=sub_elt, field=obj) for sub_elt in elt.findall("Aggregator")]
    procs = [process_from_xml(elt=sub_elt, parent=obj) for sub_elt in elt.findall("Process")]

    obj.add_children(aggs=aggs, procs=procs)

    # Aggregators are disabled if they are empty or contain only disabled aggs & procs
    enabled = not all([not child.is_enabled() for child in aggs + procs])
    obj.set_enabled(enabled)

    return obj
