"""Generate pydantic-xml model skeletons from attributes.xml.

Reads opgee/etc/attributes.xml (read-only) and prints Python code for:
  - FieldModel (159 Field attrs as elements)
  - Process subclass models
  - AnalysisModel

Usage:
    uv run python scripts/generate_models.py > .claude/tmp/model_skeleton.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
ATTRS_XML = ROOT / "opgee" / "etc" / "attributes.xml"

# Attributes that have smart defaults → default=None, type becomes T | None
SMART_DEFAULT_ATTRS = {
    "WOR", "SOR", "GOR", "WIR", "stabilizer_column", "GFIR", "depth",
    "res_press", "res_temp", "num_prod_wells", "num_water_inj_wells",
    "num_gas_inj_wells", "fraction_elec_onsite", "fraction_remaining_gas_inj",
    "ecosystem_richness", "field_development_intensity",
    "common_gas_process_choice", "prod_water_inlet_temp",
}

# Type mapping from AttrDef type to Python type
TYPE_MAP = {
    "binary": "int",
    "int": "int",
    "float": "float",
    "str": "str",
}


def python_name(attr_name: str) -> str:
    """Ensure attr_name is a valid Python identifier."""
    if attr_name in ("class", "type", "import", "from", "global", "lambda"):
        return f"{attr_name}_"
    return attr_name


def parse_options(class_attrs_elt: etree._Element) -> dict[str, list[str]]:
    """Parse <Options> elements into {name: [option_values]}."""
    result = {}
    for opts in class_attrs_elt.findall("Options"):
        name = opts.get("name")
        values = []
        for opt in opts.findall("Option"):
            val = opt.text
            if val:
                values.append(val)
        result[name] = values
    return result


def generate_field(attr_name: str, attr_def: etree._Element, options_map: dict[str, list[str]]) -> str:
    """Generate a pydantic field definition line."""
    atype = attr_def.get("type", "str")
    py_type = TYPE_MAP.get(atype, "str")
    default_text = attr_def.text
    opts_name = attr_def.get("options")
    pname = python_name(attr_name)

    # Constraints
    constraints = []
    for bound in ("GT", "GE", "LT", "LE"):
        val = attr_def.get(bound)
        if val is not None:
            constraints.append(f"{bound}={val}")

    constraint_comment = f"  # {', '.join(constraints)}" if constraints else ""

    # Options → Literal
    if opts_name and opts_name in options_map:
        opts = options_map[opts_name]
        literal_vals = ", ".join(f'"{v}"' for v in opts)
        py_type = f"Literal[{literal_vals}]"

    # Smart default → None
    if attr_name in SMART_DEFAULT_ATTRS:
        if opts_name:
            return f"    {pname}: {py_type} | None = element(tag='{attr_name}', default=None){constraint_comment}"
        return f"    {pname}: {py_type} | None = element(tag='{attr_name}', default=None){constraint_comment}"

    # Static default
    if default_text is not None:
        default_text = default_text.strip()
        if py_type == "int":
            try:
                default_val = str(int(float(default_text)))
            except ValueError:
                default_val = f"'{default_text}'"
        elif py_type == "float":
            try:
                default_val = str(float(default_text))
            except ValueError:
                default_val = f"'{default_text}'"
        elif py_type == "str" or opts_name:
            default_val = f"'{default_text}'"
        else:
            default_val = f"'{default_text}'"
        return f"    {pname}: {py_type} = element(tag='{attr_name}', default={default_val}){constraint_comment}"

    # No default
    return f"    {pname}: {py_type} | None = element(tag='{attr_name}', default=None){constraint_comment}"


def main() -> None:
    tree = etree.parse(str(ATTRS_XML))
    root = tree.getroot()
    attr_defs = root.find("AttrDefs")

    print("# Auto-generated model skeletons from attributes.xml")
    print("# This is a one-time bootstrap — hand-maintained after generation.")
    print("from __future__ import annotations")
    print()
    print("from typing import Literal, Union")
    print()
    print("from pydantic_xml import BaseXmlModel, attr, element")
    print()

    for class_attrs in attr_defs.findall("ClassAttrs"):
        class_name = class_attrs.get("name")
        options_map = parse_options(class_attrs)

        print(f"\n# === {class_name} ===")
        if class_name == "Field":
            print(f"class FieldModel(BaseXmlModel, tag='Field', search_mode='unordered'):")
        elif class_name == "Analysis":
            print(f"class AnalysisModel(BaseXmlModel, tag='Analysis', search_mode='unordered'):")
        elif class_name == "Model":
            print(f"class ModelModel(BaseXmlModel, tag='Model'):")
        elif class_name == "Stream":
            print(f"class StreamModel(BaseXmlModel, tag='Stream'):")
        else:
            print(f"class {class_name}Model(BaseXmlModel, tag='{class_name}'):")

        print(f"    '''Attributes for {class_name} ({len(class_attrs.findall('AttrDef'))} attrs)'''")

        if class_name in ("Field", "Analysis", "Model"):
            print(f"    name: str = attr()")

        for attr_def in class_attrs.findall("AttrDef"):
            name = attr_def.get("name")
            line = generate_field(name, attr_def, options_map)
            print(line)

        print()


if __name__ == "__main__":
    main()
