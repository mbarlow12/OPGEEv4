import pint

class TemperaturePressure:
    """
    Stores temperature and pressure together for convenience.
    """

    __slots__ = ("T", "P")  # keeps instances small and fast

    def __init__(self, T, P):
        self.T = None
        self.P = None
        self.set(T=T, P=P)

    def __str__(self):
        return f"<T={self.T} P={self.P}>"

    def set(self, T=None, P=None):
        if T is None and P is None:
            # _logger.warning("Tried to set TemperaturePressure with both values None")
            return

        if T is not None:
            self.T = (
                T if isinstance(T, pint.Quantity) else ureg.Quantity(float(T), "degF")
            )

        if P is not None:
            self.P = (
                P if isinstance(P, pint.Quantity) else ureg.Quantity(float(P), "psia")
            )

    def get(self):
        return (self.T, self.P)

    def copy_from(self, tp):
        self.set(T=tp.T, P=tp.P)
