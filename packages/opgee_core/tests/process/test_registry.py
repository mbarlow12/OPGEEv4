from opgee.core.process.registry import ProcessRegistry
import pytest


def test_registry_is_singleton():
    r1 = ProcessRegistry(hook={})
