from opgee.core.error import OpgeeException
from .base import Process


class Boundary(Process):
    """
    Used to define system boundaries in XML, e.g., <Process class="Boundary" name="Production">
    """

    def __init__(self, *args, **kwargs):
        boundary = kwargs.get("boundary")
        if not boundary:
            raise OpgeeException(
                f"XML elements of class 'Boundary' must define a 'boundary' attribute"
            )

        name = f"{boundary}Boundary"  # e.g., "ProductionBoundary"
        super().__init__(name, **kwargs)

    def is_chosen_boundary(self, analysis):
        proc = self.field.boundary_process(analysis)
        return proc == self

    def set_enabled(self, value):
        super().set_enabled(value)

        if not value:
            for s in self.inputs:
                s.set_enabled(False)

            for s in self.outputs:
                s.set_enabled(False)

    def run(self, analysis):
        is_chosen_boundary = self.is_chosen_boundary(analysis)
        # TODO:
        # There's a bug in the handling of the streams at boundaries. Basically, if we select the Distribution Boundary, there's no stream
        # containing PC or oil connected (those are only inputs to the ProductionBoundry). Thus the exports are off
        # and can lead to divide by 0 errors.
        #
        # How would we allow for accurate analysis at the various boundaries?
        # Option 1: remove "Boundary" processes from the graph. The idea of a boundary would instead be a partition of the underlying
        # graph. This might present better accuracy and a simpler interface/xml structure.
        #
        # Option 2: ensure that all output from intermediate boundaries is carried to the selected boundary. I don't know how we would
        # achieve this without double counting a lot of stream contents. Perhaps we could add a "remaining" output stream to all boundaries.
        # If an input stream doesn't have a commensurate output, we'd add its flow rates to the "remaining" stream. All boundaries would be
        # connected to each other by the "remaining" stream, ensuring that material flows are represented at any/all boundaries.

        # Process boundary if only if the chosen boundary has not been processed
        if self.field.get_process_data("is_chosen_boundary_processed") is None:
            # If we're an intermediate boundary, copy all inputs to outputs based on contents
            if not is_chosen_boundary:
                for in_stream in self.inputs:
                    if in_stream.is_uninitialized():
                        break
                    contents = in_stream.contents
                    if len(contents) != 1:
                        raise ModelValidationError(
                            f"Streams to and from boundaries must have only a "
                            f"single Content declaration; {self} inputs are {contents}"
                        )

                    # If not exactly one stream that declares the same contents, raises error
                    out_stream = self.find_output_stream(contents[0], raiseError=False)

                    # TODO: Fix this test
                    # if out_stream is None:
                    #     raise ModelValidationError(f"Missing output stream for '{contents[0]}' in {self} boundary")

                    if out_stream:
                        out_stream.copy_flow_rates_from(in_stream)

            # Hit the user choose boundary
            else:
                combined_streams = combine_streams(self.inputs)

                # calculate gas + LPG energy flow rate
                exported_gas_LPG_LHV = self.field.gas.energy_flow_rate(combined_streams)

                # calculate oil energy flow rate (TODO: this can be replaced by composite oil)
                exported_oil_LHV = (
                    combined_streams.liquid_flow_rate("oil")
                    * self.field.oil.mass_energy_density()
                )

                # calculate PC energy flow rate
                exported_PC_LHV = combined_streams.liquid_flow_rate(
                    "PC"
                ) * self.model.const("petrocoke-heating-value")

                exported_prod_LHV = (
                    exported_gas_LPG_LHV + exported_oil_LHV + exported_PC_LHV
                )

                self.field.save_process_data(exported_prod_LHV=exported_prod_LHV)
                self.field.save_process_data(boundary_API=combined_streams.API)

                if exported_prod_LHV.m != 0:
                    self.field.save_process_data(is_chosen_boundary_processed=True)
