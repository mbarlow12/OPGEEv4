import pluggy

from . import ENTRYPOINT
from opgee.core.process.registry import ProcessRegistry

hookspec = pluggy.HookspecMarker(ENTRYPOINT)


@hookspec
def opgee_register_process(registry: ProcessRegistry) -> None:
    """Allow plugins to register new Process subclasses.

    Parameters
    ----------
    registry : ProcessRegistry
    """
