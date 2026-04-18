from typing import override


class OpgeeException(Exception):
    pass


class OpgeeStopIteration(OpgeeException):
    reason: str

    def __init__(self, reason: str):
        super().__init__()
        self.reason = reason


class OpgeeMaxIterationsReached(OpgeeStopIteration):
    """Thrown when iterations have reached maximum_iterations."""

    pass


class OpgeeIterationConverged(OpgeeStopIteration):
    """Thrown when change variables have converged within tolerance."""

    pass


class ModelValidationError(OpgeeException):
    msg: str

    def __init__(self, msg: str):
        super().__init__()
        self.msg = msg

    @override
    def __str__(self):
        return f'<{self.__class__.__name__} "{self.msg}">'


class BalanceError(OpgeeException):
    proc_name: str
    mass_or_energy: str
    message: str | None

    def __init__(self, proc_name: str, mass_or_energy: str, message: str | None = None):
        super().__init__()
        self.proc_name = proc_name
        self.mass_or_energy = mass_or_energy
        self.message = message

    @override
    def __str__(self):
        return f"{self.mass_or_energy} is not balanced in {self.proc_name}" + (
            f": {self.message}" if self.message else ""
        )
