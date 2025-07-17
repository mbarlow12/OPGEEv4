import pluggy

from opgee.core.plugin import ENTRYPOINT
from opgee.core.plugin import hookspecs
from opgee.core.process import register_procs


class Manager:
    def __init__(self):
        pm = pluggy.PluginManager(ENTRYPOINT)
        pm.add_hookspecs(hookspecs)
        pm.load_setuptools_entrypoints(ENTRYPOINT)
        pm.register(register_procs)
        self._pm = pm

    def hook(self):
        return self._pm.hook
