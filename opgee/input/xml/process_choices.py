"""Stage 3: Resolve ProcessChoice elements — remove disabled processes and streams."""

from copy import deepcopy

from lxml import etree

from opgee.error import OpgeeException
from opgee.log import getLogger

_logger = getLogger(__name__)


def resolve_process_choices(root: etree.Element) -> etree.Element:
    """
    Resolve all ProcessChoice elements in the Field, keeping only active
    processes and streams. Removes ProcessChoice, ProcessGroup, Aggregator
    elements from the output.

    :param root: <Model> lxml Element
    :return: a new Element with choices resolved (input is not modified)
    """
    root = deepcopy(root)
    field_elt = root.find("Field")
    if field_elt is None:
        return root

    # Build dicts of all processes and streams by name
    enabled_procs = _collect_processes(field_elt)
    enabled_streams = _collect_streams(field_elt)
    disabled_procs: dict[str, etree.Element] = {}
    disabled_streams: dict[str, etree.Element] = {}

    # Process all top-level ProcessChoice elements
    for choice_elt in field_elt.findall("ProcessChoice"):
        _resolve_choice(
            choice_elt, field_elt,
            enabled_procs, enabled_streams,
            disabled_procs, disabled_streams,
        )

    # Validate: enabled streams must reference enabled processes
    for stream_name, stream_elt in enabled_streams.items():
        src = stream_elt.get("src")
        dst = stream_elt.get("dst")

        if src in disabled_procs:
            raise OpgeeException(
                f"Enabled stream '{stream_name}' references disabled src process '{src}'"
            )
        if dst in disabled_procs:
            raise OpgeeException(
                f"Enabled stream '{stream_name}' references disabled dst process '{dst}'"
            )

    # Remove ProcessChoice elements
    for choice_elt in field_elt.findall("ProcessChoice"):
        field_elt.remove(choice_elt)

    # Remove disabled Process elements
    for proc_elt in disabled_procs.values():
        if proc_elt.getparent() is not None:
            proc_elt.getparent().remove(proc_elt)

    # Remove disabled Stream elements
    for stream_elt in disabled_streams.values():
        if stream_elt.getparent() is not None:
            stream_elt.getparent().remove(stream_elt)

    # Remove Aggregator elements
    for agg_elt in field_elt.findall("Aggregator"):
        field_elt.remove(agg_elt)

    return root


def _collect_processes(field_elt: etree.Element) -> dict[str, etree.Element]:
    """Collect all <Process> elements keyed by resolved name."""
    procs: dict[str, etree.Element] = {}
    for proc_elt in field_elt.findall("Process"):
        name = _process_name(proc_elt)
        procs[name] = proc_elt
    return procs


def _collect_streams(field_elt: etree.Element) -> dict[str, etree.Element]:
    """Collect all <Stream> elements keyed by resolved name."""
    streams: dict[str, etree.Element] = {}
    for stream_elt in field_elt.findall("Stream"):
        name = _stream_name(stream_elt)
        streams[name] = stream_elt
    return streams


def _process_name(proc_elt: etree.Element) -> str:
    """Get the resolved name for a Process element.

    Uses `name` attribute if present, else `class` attribute.
    """
    return proc_elt.get("name") or proc_elt.get("class")


def _stream_name(stream_elt: etree.Element) -> str:
    """Get the resolved name for a Stream element.

    Uses `name` attribute if present, else "{src} => {dst}".
    """
    name = stream_elt.get("name")
    if name:
        return name
    return f"{stream_elt.get('src')} => {stream_elt.get('dst')}"


def _resolve_choice(choice_elt: etree.Element, field_elt: etree.Element,
                    enabled_procs: dict[str, etree.Element],
                    enabled_streams: dict[str, etree.Element],
                    disabled_procs: dict[str, etree.Element],
                    disabled_streams: dict[str, etree.Element]) -> None:
    """
    Resolve a single ProcessChoice: disable all referenced procs/streams,
    then re-enable those in the selected group.
    """
    choice_name = choice_elt.get("name")

    # Collect ALL refs from ALL groups (including nested choices)
    all_proc_refs: set[str] = set()
    all_stream_refs: set[str] = set()
    _collect_all_refs(choice_elt, all_proc_refs, all_stream_refs)

    # Move all referenced items from enabled to disabled
    for ref in all_proc_refs:
        if ref in enabled_procs:
            disabled_procs[ref] = enabled_procs.pop(ref)

    for ref in all_stream_refs:
        if ref in enabled_streams:
            disabled_streams[ref] = enabled_streams.pop(ref)

    # Look up the selected group name from Field attributes
    selected_name = _read_choice_attr(field_elt, choice_name)
    if selected_name is None:
        _logger.debug(f"No attribute value for ProcessChoice '{choice_name}'")
        return

    selected_name_lower = selected_name.lower()

    # Find the selected group
    selected_group = None
    for group_elt in choice_elt.findall("ProcessGroup"):
        if group_elt.get("name", "").lower() == selected_name_lower:
            selected_group = group_elt
            break

    if selected_group is None:
        # Missing group: all stay disabled (silent, as per plan)
        _logger.debug(
            f"ProcessChoice '{choice_name}': group '{selected_name}' not found, "
            f"all referenced procs/streams stay disabled"
        )
        return

    # Re-enable refs from the selected group
    for proc_ref in selected_group.findall("ProcessRef"):
        ref_name = proc_ref.get("name")
        if ref_name and ref_name in disabled_procs:
            enabled_procs[ref_name] = disabled_procs.pop(ref_name)

    for stream_ref in selected_group.findall("StreamRef"):
        ref_name = stream_ref.get("name")
        if ref_name and ref_name in disabled_streams:
            enabled_streams[ref_name] = disabled_streams.pop(ref_name)

    # Recurse into nested ProcessChoice elements within the selected group
    for nested_choice in selected_group.findall("ProcessChoice"):
        _resolve_choice(
            nested_choice, field_elt,
            enabled_procs, enabled_streams,
            disabled_procs, disabled_streams,
        )


def _collect_all_refs(choice_elt: etree.Element,
                      proc_refs: set[str], stream_refs: set[str]) -> None:
    """Recursively collect all ProcessRef and StreamRef names from all groups."""
    for group_elt in choice_elt.findall("ProcessGroup"):
        for proc_ref in group_elt.findall("ProcessRef"):
            name = proc_ref.get("name")
            if name:
                proc_refs.add(name)

        for stream_ref in group_elt.findall("StreamRef"):
            name = stream_ref.get("name")
            if name:
                stream_refs.add(name)

        # Recurse into nested ProcessChoice
        for nested in group_elt.findall("ProcessChoice"):
            _collect_all_refs(nested, proc_refs, stream_refs)


def _read_choice_attr(field_elt: etree.Element, attr_name: str) -> str | None:
    """Read the value of an <A> element from the Field for a ProcessChoice."""
    for a_elt in field_elt.findall("A"):
        if a_elt.get("name") == attr_name:
            return a_elt.text
    return None
