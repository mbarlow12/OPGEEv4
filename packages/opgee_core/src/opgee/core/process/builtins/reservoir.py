from opgee.core.process.base import Process


class Reservoir(Process):
    """
    Reservoir represents natural resources such as oil and gas reservoirs, and water sources
    in the subsurface. Each Field object holds a single Reservoir instance.
    """

    def __init__(self, parent=None):
        super().__init__("Reservoir", parent=parent, desc="The Reservoir")

    def run(self, analysis):
        self.print_running_msg()
