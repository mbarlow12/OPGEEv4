"""Stage 0: Load attribute definitions from an <AttrDefs> lxml Element."""

from lxml import etree

from opgee.attributes import AttrDefs


def load_attr_defs(attr_defs_elt: etree.Element) -> None:
    """
    Initialize the AttrDefs singleton from an <AttrDefs> lxml Element.

    This must be called before any other pipeline stage, as Stages 1–4
    rely on AttrDefs.get_instance() to look up attribute metadata.

    :param attr_defs_elt: lxml Element representing <AttrDefs>
    """
    AttrDefs.load_attr_defs(attr_defs_elt)
