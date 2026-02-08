import copy
import os
import pytest
from opgee.config import getConfig
from opgee.log import setLogLevels, configureLogs
from opgee.model_file import ModelFile
from opgee.tool import Opgee
from .utils_for_tests import load_test_model, path_to_test_file


def pytest_addoption(parser):
    parser.addoption("--run-slow", action="store_true", default=False, help="run slow tests")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


@pytest.fixture(scope="session")
def configure_logging_for_tests():
    # Don't display routine diagnostic messages during tests
    getConfig()
    setLogLevels('ERROR')
    configureLogs(force=True)
    return None


@pytest.fixture(scope="session")
def _cached_test_model(configure_logging_for_tests):
    return load_test_model('test_model.xml')


@pytest.fixture(scope="session")
def _cached_test_model2(configure_logging_for_tests):
    return load_test_model('test_model2.xml', class_path=path_to_test_file('user_processes.py'))


@pytest.fixture(scope="module")
def test_model(_cached_test_model):
    return copy.deepcopy(_cached_test_model)


@pytest.fixture(scope="function")
def test_model_with_change(_cached_test_model):
    """
    The same as test_model, only with "function" scope, for use on
    tests that alter the model, to avoid creating state changes that
    confuse tests.
    """
    return copy.deepcopy(_cached_test_model)


@pytest.fixture(scope="function")
def test_model2(_cached_test_model2):
    return copy.deepcopy(_cached_test_model2)


@pytest.fixture(scope='function')
def opgee_main():
    return Opgee()
