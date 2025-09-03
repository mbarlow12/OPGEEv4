from lxml.etree import _Element as Element

from opgee.field import Field
from opgee.process import Aggregator, Process, _get_subclass
from opgee.utils import getBooleanXML


def process_from_xml(elt: Element, parent: Field | Aggregator) -> Process:
    """
    Instantiate an instance from an XML element

    :param elt: (etree.Element) representing a <Process> element
    :param parent: (opgee.Analysis) the Analysis containing the new Process
    :return: (Process) instance populated from XML
    """
    elem_attrib = elt.attrib
    name = elem_attrib.get("name")

    if name == "test_proc":
        pass

    desc = elem_attrib.get("desc")
    impute_start = elem_attrib.get("impute-start")
    cycle_start = elem_attrib.get("cycle-start")
    boundary = elem_attrib.get("boundary")  # optional

    classname = elem_attrib["class"]  # required by XML schema
    subclass = _get_subclass(Process, classname)
    attr_dict = subclass.instantiate_attrs(elt, is_process=True)

    proc = subclass(
        name,
        attr_dict=attr_dict,
        parent=parent,
        desc=desc,
        cycle_start=cycle_start,
        impute_start=impute_start,
        boundary=boundary,
    )

    proc.set_enabled(elem_attrib.get("enabled", "1"))
    proc.set_extend(elem_attrib.get("extend", "0"))
    proc.set_run_after(getBooleanXML(elem_attrib.get("after", "0")))

    return proc
