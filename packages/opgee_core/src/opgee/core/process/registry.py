from __future__ import annotations


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Process


class ProcessRegistry(object):
    _instance = None

    def __new__(cls, hook):
        if cls._instance is None:
            cls._self = super().__new__(cls)
        return cls._self

    def __init__(self, hook):
        self._classes: set[type[Process]] = set()
        self.hook = hook

    def register(self, proc: type[Process]):
        self._classes.add(proc)

    def register_procs(self):
        self.procs = self.hook.opgee_register_process_classes(registry=self)
