class OpgeeException(Exception):
    pass


class OpgeeStopIteration(OpgeeException):
    def __init__(self, reason):
        self.reason = reason

class OpgeeMaxIterationsReached(OpgeeStopIteration):
    """Thrown when iterations have reached maximum_iterations."""
    pass

class OpgeeIterationConverged(OpgeeStopIteration):
    """Thrown when change variables have converged within tolerance."""
    pass

class AbstractMethodError(OpgeeException):
    def __init__(self, cls, method):
        self.cls = cls
        self.method = method

    def __str__(self):
        return f"Abstract method {self.method} was called. Subclass {self.cls.__name__} must implement this method."


class ModelValidationError(OpgeeException):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f'<{self.__class__.__name__} "{self.msg}">'


class BalanceError(OpgeeException):
    def __init__(self, proc_name, mass_or_energy, message=None):
        self.proc_name = proc_name
        self.mass_or_energy = mass_or_energy
        self.message = message

    def __str__(self):
        return f"{self.mass_or_energy} is not balanced in {self.proc_name}" + \
               (f": {self.message}" if self.message else "")


class ZeroEnergyFlowError(OpgeeException):
    def __init__(self, stream, message=None):
        self.stream = stream
        self.message = message

    def __str__(self):
        return (f"Zero energy flow rate for {self.stream} boundary stream" +
                (f": {self.message}" if self.message else ""))
