"""Generate XML fragment files from opgee.xml for XInclude-based composition.

Reads opgee/etc/opgee.xml (read-only) and produces:
  opgee/input/xml/fragments/
    templates/template.xml       — template Field (processes + streams, no ProcessChoice)
    process_groups/{choice_name}/{group_name}.xml — per-group fragments

Usage:
    uv run python scripts/generate_fragments.py
"""
from __future__ import annotations

import re
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parent.parent
OPGEE_XML = ROOT / "opgee" / "etc" / "opgee.xml"
FRAGMENTS_DIR = ROOT / "opgee" / "input" / "xml" / "fragments"

# Attributes that have smart defaults — omit from template
SMART_DEFAULT_ATTRS = {
    "WOR", "SOR", "GOR", "WIR", "stabilizer_column", "GFIR", "depth",
    "res_press", "res_temp", "num_prod_wells", "num_water_inj_wells",
    "num_gas_inj_wells", "fraction_elec_onsite", "fraction_remaining_gas_inj",
    "ecosystem_richness", "field_development_intensity",
    "common_gas_process_choice", "prod_water_inlet_temp",
}


def slugify(name: str) -> str:
    """Convert a ProcessChoice/ProcessGroup name to a safe filename."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s


def find_stream(field_elt: etree._Element, stream_name: str) -> etree._Element | None:
    """Find a <Stream> element by matching src/dst or name attribute."""
    for stream in field_elt.findall("Stream"):
        # Match by name attribute
        if stream.get("name") == stream_name:
            return stream
        # Match by "src => dst" pattern
        src = stream.get("src", "")
        dst = stream.get("dst", "")
        if f"{src} => {dst}" == stream_name:
            return stream
    return None


def find_process(field_elt: etree._Element, proc_name: str) -> etree._Element | None:
    """Find a <Process> by class or name."""
    for proc in field_elt.findall("Process"):
        if proc.get("class") == proc_name or proc.get("name") == proc_name:
            return proc
    return None


def make_process_tag(proc_elt: etree._Element) -> etree._Element:
    """Convert <Process class="X" ...> to <X ...> (tag = class name).

    Copies relevant attributes (not 'class' or 'name' if name == class).
    """
    class_name = proc_elt.get("class")
    new_elt = etree.Element(class_name)
    for k, v in proc_elt.attrib.items():
        if k == "class":
            continue
        if k == "name" and v == class_name:
            continue
        new_elt.set(k, v)
    # Copy child elements
    for child in proc_elt:
        new_elt.append(child)
    return new_elt


def generate_group_fragment(
    field_elt: etree._Element,
    group_elt: etree._Element,
) -> etree._Element:
    """Generate a <fragment> element for a ProcessGroup."""
    fragment = etree.Element("fragment")

    for proc_ref in group_elt.findall("ProcessRef"):
        proc_name = proc_ref.get("name") or proc_ref.get("class")
        proc = find_process(field_elt, proc_name)
        if proc is not None:
            new_proc = make_process_tag(proc)
            fragment.append(new_proc)
        else:
            # Process not found in template — emit empty tag
            fragment.append(etree.Element(proc_name))

    for stream_ref in group_elt.findall("StreamRef"):
        stream_name = stream_ref.get("name")
        stream = find_stream(field_elt, stream_name)
        if stream is not None:
            from copy import deepcopy
            fragment.append(deepcopy(stream))
        else:
            # Stream not found — emit a comment
            fragment.append(etree.Comment(f" StreamRef '{stream_name}' not found in template "))

    return fragment


def generate_template(field_elt: etree._Element) -> etree._Element:
    """Generate template.xml — Field minus ProcessChoice elements.

    Renames <Process class="X"> to <X/> and omits smart-defaulted attrs.
    """
    fragment = etree.Element("fragment")

    for child in field_elt:
        if child.tag == "ProcessChoice":
            continue
        if child.tag == "Aggregator":
            continue
        if child.tag == "A":
            name = child.get("name")
            if name in SMART_DEFAULT_ATTRS:
                continue
            # Convert <A name="x">value</A> to <x>value</x>
            new_elt = etree.Element(name)
            new_elt.text = child.text
            fragment.append(new_elt)
            continue
        if child.tag == "Process":
            fragment.append(make_process_tag(child))
            continue
        if child.tag == "Stream":
            from copy import deepcopy
            fragment.append(deepcopy(child))
            continue
        # Other elements: copy as-is
        from copy import deepcopy
        fragment.append(deepcopy(child))

    return fragment


def write_fragment(path: Path, fragment: etree._Element) -> None:
    """Write a fragment element to an XML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tree = etree.ElementTree(fragment)
    tree.write(str(path), pretty_print=True, xml_declaration=True, encoding="UTF-8")
    print(f"  wrote {path.relative_to(ROOT)}")


def main() -> None:
    tree = etree.parse(str(OPGEE_XML))
    root = tree.getroot()

    field_elt = root.find("Field")
    if field_elt is None:
        raise RuntimeError("No <Field> element found in opgee.xml")

    print(f"Generating fragments from {OPGEE_XML.relative_to(ROOT)}")
    print(f"Output: {FRAGMENTS_DIR.relative_to(ROOT)}/\n")

    # Generate template
    template = generate_template(field_elt)
    write_fragment(FRAGMENTS_DIR / "templates" / "template.xml", template)

    # Generate process group fragments
    for choice in field_elt.findall("ProcessChoice"):
        choice_name = choice.get("name")
        choice_slug = slugify(choice_name)
        print(f"\nProcessChoice: {choice_name}")

        for group in choice.findall("ProcessGroup"):
            group_name = group.get("name")
            group_slug = slugify(group_name)
            fragment = generate_group_fragment(field_elt, group)
            path = FRAGMENTS_DIR / "process_groups" / choice_slug / f"{group_slug}.xml"
            write_fragment(path, fragment)

    print("\nDone!")


if __name__ == "__main__":
    main()
