from contextlib import contextmanager
from pathlib import Path

from opgee.process import Process


@contextmanager
def tempdir():
    import shutil
    import tempfile

    d = tempfile.mkdtemp()
    try:
        yield d
    finally:
        shutil.rmtree(d)


class ProcA(Process):
    def run(self, analysis):
        pass


class ProcB(Process):
    def run(self, analysis):
        pass


class Before(Process):
    def run(self, analysis):
        pass

    def impute(self):
        pass


# Required to load opgee.xml and some test XML files
class After(Process):
    def run(self, analysis):
        pass


def path_to_test_file(filename):
    return str(Path(__file__).parent / "files" / filename)
