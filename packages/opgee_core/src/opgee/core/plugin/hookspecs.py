import pluggy

from . import ENTRYPOINT
from opgee.core.process.base import Process

hookspec = pluggy.HookspecMarker(ENTRYPOINT)


@hookspec
def opgee_register_process(process: Process): ...
