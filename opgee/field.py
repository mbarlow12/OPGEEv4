"""Field class — top-level simulation object for a single oil/gas field.

After the v5 deep-clean, Field is constructed directly from Python objects
(no XML), owns a FieldContext that it injects into its Processes and Streams,
and uses networkx for graph scheduling.

Boundary, ProcessChoice/ProcessGroup, SmartDefault, enabled-state, and the
Model/Analysis hierarchy have all been removed. CI computation is deferred.
"""
from __future__ import annotations

import logging

import networkx as nx
import pandas as pd
import pint
from pint.facets.plain import PlainQuantity as Quantity

from .context import FieldContext, GWPData, SimulationParams
from .core import STP
from .emissions import Emissions
from .energy import Energy
from .error import (
    ModelValidationError,
    OpgeeException,
    OpgeeIterationConverged,
    OpgeeMaxIterationsReached,
    OpgeeStopIteration,
)
from .import_export import ImportExport
from .process import Process, Reservoir
from .stream import Stream
from .table_manager import TableManager
from .thermodynamics import Gas, Oil, Water
from .units import ureg

_logger = logging.getLogger(__name__)


class Field:
    """A `Field` contains all Processes and Streams for one oil/gas field.

    Field is the top-level simulation object. It owns a ``FieldContext`` that
    is injected into every Process and Stream. Physical parameters used only
    by Processes are passed to those Processes directly at construction time
    and are not stored on Field. Only Field-internal physical state lives
    here.

    Graph scheduling metadata (``cycle_starts``, ``impute_starts``,
    ``run_after``) is owned by Field and populated during graph construction.
    """

    def __init__(
        self,
        name: str,
        simulation: SimulationParams,
        gwp: GWPData,
        tables: TableManager,
        processes: list[Process],
        streams: list[Stream],
        oil: Oil,
        gas: Gas,
        water: Water,
        *,
        num_prod_wells: int = 0,
        oil_sands_mine: str = "None",
        field_production_lifetime: Quantity[float] | None = None,
        res_press: Quantity[float] | None = None,
        res_temp: Quantity[float] | None = None,
        has_grid_mix: bool = False,
        reservoir: Reservoir | None = None,
        cycle_start: Process | None = None,
        impute_start: Process | None = None,
    ) -> None:
        """Construct a Field from already-built Processes and Streams.

        :param name: field identifier.
        :param simulation: iteration/convergence settings.
        :param gwp: global-warming-potential values.
        :param tables: loaded CSV lookup tables (TableManager).
        :param processes: list of Process instances. Each must already have
            its own ``ctx`` attribute assigned (typically the same
            FieldContext this Field constructs). Duplicate names are
            rejected.
        :param streams: list of Stream instances. Streams with ``ctx=None``
            will be bound to this Field's context. ``src_name`` / ``dst_name``
            must reference names in ``processes`` (or ``reservoir``).
        :param oil: Oil helper (thermodynamic properties).
        :param gas: Gas helper.
        :param water: Water helper.
        :param num_prod_wells: number of producing wells (integer count).
        :param oil_sands_mine: mine type string; ``"None"`` when not a mine.
        :param field_production_lifetime: years of field production (for
            completion/workover C1 rate amortisation).
        :param res_press: reservoir pressure (psia).
        :param res_temp: reservoir temperature (degF).
        :param has_grid_mix: if True, imported-electricity CI comes from the
            grid-mix tables rather than the default upstream-CI row.
        :param reservoir: optional Reservoir process. If supplied, it is
            added to the process list; if None, a default
            ``Reservoir("Reservoir", ctx)`` is created.
        :param cycle_start: optional Process to prefer as the entry point
            when iterating cyclic subgraphs. Defaults to any Reservoir in
            the cycle, else an arbitrary cycle member.
        :param impute_start: optional Process to prefer as the start point
            for upstream imputation. If None, the source process of the
            first stream with ``has_exogenous_data`` is used. (Currently
            ``has_exogenous_data`` is not set anywhere in live code, so
            impute is skipped when no ``impute_start`` is given.)
        """
        self.name = name
        self.oil = oil
        self.gas = gas
        self.water = water

        # Field-internal physical state (read by methods defined on Field
        # itself; NOT a dumping ground for process-facing attributes).
        self.num_prod_wells = num_prod_wells
        self.oil_sands_mine = oil_sands_mine
        self.field_production_lifetime = field_production_lifetime
        self.res_press = res_press
        self.res_temp = res_temp
        self.has_grid_mix = has_grid_mix
        self.stp = STP

        # Build the FieldContext that every Process and Stream shares.
        self.ctx = FieldContext(
            stp=STP,
            tables=tables,
            gwp=gwp,
            simulation=simulation,
        )

        # Build the Reservoir (source node) if the caller did not supply one.
        if reservoir is None:
            reservoir = Reservoir("Reservoir", self.ctx)
        self.reservoir = reservoir

        # Assemble the full process list, Reservoir first.
        all_procs: list[Process] = [reservoir] + [
            p for p in processes if p is not reservoir
        ]

        # Populate process_dict and stream_dict. Duplicate names raise.
        self.process_dict: dict[str, Process] = {}
        for proc in all_procs:
            if proc.name in self.process_dict:
                raise OpgeeException(
                    f"Duplicate process name '{proc.name}' in field '{name}'"
                )
            self.process_dict[proc.name] = proc

        self.stream_dict: dict[str, Stream] = {}
        for stream in streams:
            if stream.name in self.stream_dict:
                raise OpgeeException(
                    f"Duplicate stream name '{stream.name}' in field '{name}'"
                )
            # Inject our ctx into streams that don't already have one.
            if stream.ctx is None:
                stream.ctx = self.ctx
            self.stream_dict[stream.name] = stream

        # Aggregated results objects (summed across processes in run()).
        self.emissions = Emissions()
        self.energy = Energy()
        self.import_export = ImportExport()

        # Wellhead TP is written by DownholePump.run() and read by Separation.
        # Left None at construction; processes that rely on it do so inside
        # the graph run, after DownholePump has set it.
        self.wellhead_tp = None

        # Build the directed graph and cycle list.
        self.graph: nx.DiGraph = self._connect_processes()
        self.cycles: list[list[Process]] = list(nx.simple_cycles(self.graph))

        # Graph scheduling metadata (moved from Process in Phase 6.1).
        self.impute_starts: set[Process] = set()
        if impute_start is not None:
            self.impute_starts.add(impute_start)

        self.cycle_starts: set[Process] = set()
        if cycle_start is not None:
            self.cycle_starts.add(cycle_start)

        self.run_after: set[Process] = {
            p for p in self.process_dict.values() if getattr(p, "run_after", False)
        }

        # Validate run_after-tagged processes — they may only feed other
        # run_after procs.
        self._check_run_after_procs()

    # ---- string / repr ----

    def __str__(self) -> str:
        return f"<Field '{self.name}'>"

    # ---- graph construction & scheduling ------------------------------

    def _connect_processes(self) -> nx.DiGraph:
        """Build a DiGraph from processes and streams.

        Each stream contributes one edge ``(src_proc, dst_proc)`` with the
        Stream object attached as ``edge[stream]``. No enabled-state
        filtering — every registered process and stream participates.
        """
        g: nx.DiGraph = nx.MultiDiGraph()

        # Add every process as a node and clear stale input/output lists.
        for p in self.process_dict.values():
            g.add_node(p)
            p.inputs.clear()
            p.outputs.clear()

        # Wire up streams.
        for s in self.stream_dict.values():
            src = self.find_process(s.src_name)
            dst = self.find_process(s.dst_name)
            s.src_proc = src
            s.dst_proc = dst

            src.add_output_stream(s)
            dst.add_input_stream(s)

            g.add_edge(src, dst, stream=s)

        return g

    def _check_run_after_procs(self) -> None:
        """Procs tagged ``run_after=True`` may feed only other run_after procs."""

        def _ok(proc: Process) -> bool:
            return all(dst.run_after for dst in proc.successors())

        bad = [p for p in self.process_dict.values() if p.run_after and not _ok(p)]
        if bad:
            raise OpgeeException(
                f"Processes {bad} are tagged run_after=True but feed non-run_after processes"
            )

    def _is_cycle_member(self, process: Process) -> bool:
        return any(process in cycle for cycle in self.cycles)

    def _depends_on_cycle(
        self, process: Process, visited: set[Process] | None = None
    ) -> bool:
        """True if ``process`` reaches a cycle by walking upstream."""
        visited = visited or set()
        for predecessor in process.predecessors():
            if predecessor in visited:
                return True
            visited.add(predecessor)
            if self._depends_on_cycle(predecessor, visited=visited):
                return True
        return False

    def _compute_graph_sections(
        self,
    ) -> tuple[set[Process], set[Process], set[Process], set[Process]]:
        """Partition processes into (cycle_independent, in_cycle, cycle_dependent, run_afters)."""
        processes = list(self.process_dict.values())

        procs_in_cycles: set[Process] = set()
        for cycle in self.cycles:
            for proc in cycle:
                procs_in_cycles.add(proc)

        cycle_dependent: set[Process] = set()
        if procs_in_cycles:
            for process in processes:
                if process not in procs_in_cycles and self._depends_on_cycle(process):
                    cycle_dependent.add(process)

        run_afters = {p for p in processes if p.run_after}

        cycle_independent = (
            set(processes) - procs_in_cycles - cycle_dependent - run_afters
        )
        return cycle_independent, procs_in_cycles, cycle_dependent, run_afters

    # ---- stream / process lookup --------------------------------------

    def streams(self) -> list[Stream]:
        """Return all Streams in this Field."""
        return list(self.stream_dict.values())

    def processes(self) -> list[Process]:
        """Return all Processes in this Field (Reservoir included)."""
        return list(self.process_dict.values())

    # Kept for API compatibility; identical to processes() now that
    # enabled-state is gone.
    all_processes = processes

    def find_stream(self, name: str, raiseError: bool = True) -> Stream | None:
        stream = self.stream_dict.get(name)
        if stream is None and raiseError:
            raise OpgeeException(
                f"Stream named '{name}' was not found in field '{self.name}'"
            )
        return stream

    def find_process(self, name: str, raiseError: bool = True) -> Process | None:
        proc = self.process_dict.get(name)
        if proc is None and raiseError:
            raise OpgeeException(
                f"Process '{name}' was not found in field '{self.name}'"
            )
        return proc

    def find_start_streams(self) -> list[Stream]:
        """Streams flagged as carrying exogenous start data."""
        return [
            s
            for s in self.stream_dict.values()
            if getattr(s, "has_exogenous_data", False)
        ]

    # ---- inter-process data bulletin board ----------------------------

    def save_process_data(self, **kwargs) -> None:
        """Store arbitrary key/value pairs in ``ctx.process_data``."""
        self.ctx.process_data.update(kwargs)

    def get_process_data(self, name: str, raiseError: bool = False):
        """Retrieve a previously-saved value from ``ctx.process_data``."""
        try:
            return self.ctx.process_data[name]
        except KeyError:
            if raiseError:
                raise OpgeeException(
                    f"Process data dictionary does not include {name}"
                )
            return None

    # ---- run lifecycle -------------------------------------------------

    def run(self) -> None:
        """Run all Processes for this Field.

        No ``analysis`` argument and no ``trial_num`` — Field owns its GWP
        via ``self.ctx.gwp`` and MCS has been removed. CI calculation is
        deferred.
        """
        _logger.info(f"Running '{self.name}'")
        self.reset()
        self._impute()
        self.reset_iteration()
        self.run_processes()
        self.check_balances()
        self.get_energy_rates()
        self.get_emission_rates()

    def reset(self) -> None:
        self.reset_streams()
        self.reset_processes()

    def reset_iteration(self) -> None:
        Process.reset_all_iteration()
        for proc in self.process_dict.values():
            proc.reset_iteration()

    def reset_processes(self) -> None:
        for proc in self.process_dict.values():
            proc.reset()

    def reset_streams(self) -> None:
        for stream in self.stream_dict.values():
            stream.reset()

    def check_balances(self) -> None:
        """Hook: per-process mass/energy balance checks.

        Base ``Process`` does not define ``check_balances``; we invoke it
        on processes that implement it.
        """
        for p in self.process_dict.values():
            check = getattr(p, "check_balances", None)
            if callable(check):
                check()

    # ---- imputation ---------------------------------------------------

    def _impute(self) -> None:
        """Populate upstream stream data by walking ancestors of a start process."""

        if self.impute_starts:
            start_procs = set(self.impute_starts)
        else:
            start_streams = self.find_start_streams()
            for stream in start_streams:
                if not stream.impute:
                    raise OpgeeException(
                        f"A start stream {stream} cannot have its 'impute' flag set to '0'."
                    )
            start_procs = {s.src_proc for s in start_streams if s.src_proc is not None}

        if not start_procs:
            return

        if len(start_procs) != 1:
            raise OpgeeException(
                f"Expected exactly one impute start process; got {len(start_procs)}: {start_procs}"
            )

        start_proc = next(iter(start_procs))
        _logger.debug(f"Running impute() for {start_proc}")

        # Walk upstream via nx.ancestors but honour stream 'impute' flags by
        # traversing input streams manually.
        visited: set[Process] = set()

        def _impute_upstream(proc: Process) -> None:
            if proc is None or proc in visited:
                return
            visited.add(proc)
            impute_method = getattr(proc, "impute", None)
            if callable(impute_method):
                impute_method()
            for stream in proc.inputs:
                if stream.impute and stream.src_proc is not None:
                    _impute_upstream(stream.src_proc)

        try:
            _impute_upstream(start_proc)
        except OpgeeStopIteration:
            raise OpgeeException(
                "Impute failed due to a process loop. Use Stream impute=False to break cycle."
            )

    # ---- process scheduling -------------------------------------------

    def run_processes(self) -> None:
        """Run processes in topological order, iterating cyclic subgraphs."""
        (
            cycle_independent,
            procs_in_cycles,
            cycle_dependent,
            run_afters,
        ) = self._compute_graph_sections()

        for proc in procs_in_cycles:
            proc.in_cycle = True

        def run_procs_in_order(subset: set[Process]) -> None:
            if not subset:
                return
            sg = self.graph.subgraph(subset)
            for proc in nx.topological_sort(sg):
                proc.run()

        # 1. cycle-independent nodes in topological order
        run_procs_in_order(cycle_independent)

        # 2. cyclic subgraph iteration
        if procs_in_cycles:
            max_iter = self.ctx.simulation.maximum_iterations

            # Prefer a user-designated cycle start, else any Reservoir in
            # the cycle, else an arbitrary member.
            start_proc: Process | None = None
            for p in self.cycle_starts:
                if p in procs_in_cycles:
                    start_proc = p
                    break
            if start_proc is None:
                for p in procs_in_cycles:
                    if isinstance(p, Reservoir):
                        start_proc = p
                        break
            if start_proc is None:
                start_proc = next(iter(procs_in_cycles))

            # Build an ordering by BFS from start_proc within procs_in_cycles.
            ordered_cycle: list[Process] = []
            seen: set[Process] = set()
            queue: list[Process] = [start_proc]
            while queue:
                p = queue.pop(0)
                if p in seen or p not in procs_in_cycles:
                    continue
                seen.add(p)
                ordered_cycle.append(p)
                for succ in self.graph.successors(p):
                    if succ in procs_in_cycles and succ not in seen:
                        queue.append(succ)

            # Include any cycle members not reachable from start_proc.
            for p in procs_in_cycles:
                if p not in seen:
                    ordered_cycle.append(p)

            iter_count = 0
            while True:
                iter_count += 1
                if iter_count > max_iter:
                    raise OpgeeMaxIterationsReached(
                        f"Maximum iterations ({max_iter}) reached without convergence"
                    )
                try:
                    for proc in ordered_cycle:
                        proc.run()
                except OpgeeIterationConverged as e:
                    _logger.debug(e)
                    break

        # 3. cycle-dependent nodes
        run_procs_in_order(cycle_dependent)

        # 4. run_after-tagged procs
        run_procs_in_order(run_afters)

    # ---- aggregated results -------------------------------------------

    def get_energy_rates(self) -> pd.Series:
        """Sum energy-rate Series from every process."""
        self.energy.reset()
        data = self.energy.data
        for proc in self.process_dict.values():
            data += proc.get_energy_rates()
        return data

    def get_emission_rates(self) -> pd.DataFrame:
        """Sum emission rates from every process, using our GWP."""
        gwp_series = self.ctx.gwp.values
        data = self.emissions.data
        data[data.columns] = ureg.Quantity(0.0, "t/d")
        for proc in self.process_dict.values():
            data += proc.get_emission_rates(gwp_series)
        # Recompute CO2-equivalent GHG totals.
        return self.emissions.rates(gwp_series)

    def get_net_imported_product(self) -> pd.Series:
        """Net imported product (energy or mass) across all processes."""
        imp_exp = self.import_export.imports_exports()
        data = imp_exp[ImportExport.NET_IMPORTS]
        for proc in self.process_dict.values():
            data += proc.get_net_imported_product()
        return data

    def get_imported_emissions(self, net_import: pd.Series) -> Quantity[float]:
        """Emissions from imported products, sourced from upstream-CI and grid-mix tables.

        Uses ``self.ctx.tables`` (TableManager) for the lookups instead of
        the former ``self.model`` references.
        """
        from .import_export import CO2_Flooding, ELECTRICITY, N2, WATER

        imported_emissions = ureg.Quantity(0.0, "tonne/day")
        upstream_CI = self.ctx.tables.get_table("upstream-CI")

        if self.has_grid_mix:
            grid_mix_EF = self.ctx.tables.get_table("grid_mix_EF")
            grid_mix_feed = self.ctx.tables.get_table("grid_mix_feed")
            upstream_CI = upstream_CI.copy()
            upstream_CI.loc[ELECTRICITY] = grid_mix_EF.T.dot(grid_mix_feed).iloc[0, 0]

        for product, energy_rate in net_import.items():
            if product in (WATER, N2, CO2_Flooding):
                continue
            if not isinstance(energy_rate, pint.Quantity):
                energy_rate = ureg.Quantity(energy_rate, "mmbtu/day")
            if energy_rate.m > 0:
                imported_emissions += energy_rate * upstream_CI.loc[product, "EF"]

        return imported_emissions

    # ---- fugitive emissions (component fugitive model) ----------------

    @staticmethod
    def comp_fugitive_productivity(prod_mat_gas: pd.DataFrame, mean: float) -> int:
        """Bin a productivity mean to the matching productivity-table row."""
        result = prod_mat_gas[
            (prod_mat_gas["Bin low"] < mean) & (prod_mat_gas["Bin high"] >= mean)
        ].index.values.astype(int)[0]
        return result

    @staticmethod
    def comp_fugitive_loss(loss_mat_ave: pd.DataFrame, assignment: int) -> pd.Series:
        """Look up the loss-rate row for a productivity-bin assignment."""
        return loss_mat_ave.iloc[assignment - 1, :]

    def get_component_fugitive(
        self,
        *,
        GOR: Quantity[float],
        GOR_cutoff: Quantity[float],
        oil_rate: Quantity[float],
        gas_lifting: bool,
        GLIR: Quantity[float],
        gas_flooding: bool,
        flood_gas_type: str,
        GFIR: Quantity[float],
        frac_CO2_breakthrough: Quantity[float],
        frac_wells_with_plunger: float,
        frac_wells_with_non_plunger: float,
    ) -> tuple[pd.Series, pd.DataFrame]:
        """Compute per-process fugitive loss rates using Jeff's component model.

        All physical inputs are passed explicitly. Table lookups use
        ``self.ctx.tables``.

        :return: (process_loss_rate Series indexed by process name,
                 loss_mat_gas_ave DataFrame)
        """
        productivity = oil_rate * (GOR + (gas_lifting * GLIR))

        if gas_flooding and flood_gas_type == "CO2":
            productivity += oil_rate * GFIR * frac_CO2_breakthrough

        num_prod_wells = self.num_prod_wells
        separation_loss_rate = ureg.Quantity(0.0, "frac")
        tank_loss_rate = ureg.Quantity(0.0, "frac")
        pump_loss_rate = ureg.Quantity(0.0, "frac")
        loss_mat_gas_ave_df = pd.DataFrame()

        if num_prod_wells > 0:
            productivity = (productivity / num_prod_wells).to("kscf/day").m

            tables = self.ctx.tables
            loss_mat_gas = tables.get_table("loss-matrix-gas")
            loss_mat_oil = tables.get_table("loss-matrix-oil")
            prod_mat_gas = tables.get_table("productivity-gas")
            prod_mat_oil = tables.get_table("productivity-oil")

            field_productivity = pd.DataFrame(
                columns=[
                    "Assignment",
                    "col_shift",
                    "Mean gas rate (Mscf/well/day)",
                    "Frac total gas",
                ],
                index=prod_mat_gas.index,
            )

            field_productivity["Mean gas rate (Mscf/well/day)"] = (
                prod_mat_gas["Normalized rate"]
                if GOR > GOR_cutoff
                else prod_mat_oil["Normalized rate"]
            )
            field_productivity["Mean gas rate (Mscf/well/day)"] *= productivity

            field_productivity["Frac total gas"] = (
                prod_mat_gas["Frac total gas"]
                if GOR > GOR_cutoff
                else prod_mat_oil["Frac total gas"]
            )

            field_productivity["Assignment"] = field_productivity.apply(
                lambda row: self.comp_fugitive_productivity(
                    prod_mat_gas, row["Mean gas rate (Mscf/well/day)"]
                ),
                axis=1,
            )

            common_cols = [
                "Well",
                "Header",
                "Heater",
                "Separator",
                "Meter",
                "Tanks-leaks",
                "Tank-thief hatch",
                "Recip Comp",
                "Dehydrator",
                "Chem Inj Pump",
                "Pneum Controllers",
                "Flash factor",
            ]
            cols_gas = common_cols + ["LU-plunger", "LU-no plunger"]
            cols_oil = common_cols
            tranch = range(10)
            flash_factor = 0.51  # kg CH4/bbl total flashing gas

            loss_mat_gas_ave = loss_mat_gas.mean(axis=0).values
            loss_mat_gas_ave = loss_mat_gas_ave.reshape(len(tranch), len(cols_gas))
            loss_mat_gas_ave_df = pd.DataFrame(
                data=loss_mat_gas_ave,
                index=prod_mat_gas["Bin low"],
                columns=cols_gas,
            )

            cols = cols_gas if GOR > GOR_cutoff else cols_oil
            loss_mat = loss_mat_gas if GOR > GOR_cutoff else loss_mat_oil
            loss_mat_ave = loss_mat.mean(axis=0).values
            loss_mat_ave = loss_mat_ave.reshape(len(tranch), len(cols))
            df = pd.DataFrame(loss_mat_ave, columns=cols, index=range(len(tranch)))

            df = field_productivity.apply(
                lambda row: self.comp_fugitive_loss(df, row["Assignment"]), axis=1
            )
            comp_fugitive = df.T.dot(field_productivity["Frac total gas"])
            comp_fugitive["Flash factor"] /= flash_factor

            separation_loss_rate = comp_fugitive["Separator"]
            tank_loss_rate = comp_fugitive["Flash factor"]
            pump_loss_rate = comp_fugitive
            pump_loss_rate.drop("Separator", inplace=True)
            pump_loss_rate.drop("Flash factor", inplace=True)

            if GOR > GOR_cutoff:
                pump_loss_rate["LU-plunger-norm"] = (
                    pump_loss_rate["LU-plunger"] * frac_wells_with_plunger
                    + pump_loss_rate["LU-no plunger"] * frac_wells_with_non_plunger
                )
                pump_loss_rate.drop("LU-plunger", inplace=True)
                pump_loss_rate.drop("LU-no plunger", inplace=True)
            pump_loss_rate = pump_loss_rate.sum()

        process_loss_rate = pd.Series(
            data={
                "Separation": separation_loss_rate,
                "CrudeOilStorage": tank_loss_rate,
                "DownholePump": pump_loss_rate,
            },
            dtype="pint[frac]",
        )
        return process_loss_rate, loss_mat_gas_ave_df

    def get_completion_and_workover_C1_rate(
        self,
        *,
        workovers_per_well: Quantity[float],
        is_flaring: str,
        is_REC: str,
        frac_well_fractured: Quantity[float],
    ) -> Quantity[float]:
        """Compute the annualised C1 rate for well completion + workover events.

        Uses ``self.ctx.tables.get_table('well-completion-and-workover-C1-rate')``
        plus Field's own ``num_prod_wells``, ``oil_sands_mine``, and
        ``field_production_lifetime``.
        """
        completion_event = (
            self.num_prod_wells
            if self.oil_sands_mine == "None"
            else ureg.Quantity(0, "frac")
        )
        workover_event = completion_event * workovers_per_well

        df = self.ctx.tables.get_table("well-completion-and-workover-C1-rate")

        def find_value(
            df: pd.DataFrame,
            is_hydraulic_fracture: str,
            well_type: str,
            is_flaring_: str,
            is_REC_: str,
        ) -> Quantity[float]:
            result = df.loc[
                (df["is_hydraulic_fracture"] == is_hydraulic_fracture)
                & (df["type"] == well_type)
                & (df["is_flaring"] == is_flaring_)
                & (df["is_REC"] == is_REC_)
            ]
            return (
                result["value"].values[0]
                if not result.empty
                else ureg.Quantity(0, "tonne")
            )

        def calculate_C1_rate(event, well_type: str) -> Quantity[float]:
            fracture_rate = find_value(df, "Yes", well_type, is_flaring, is_REC)
            no_fracture_rate = find_value(df, "No", well_type, is_flaring, "No")
            C1_rate = fracture_rate * frac_well_fractured + no_fracture_rate * (
                1 - frac_well_fractured
            )
            return C1_rate * event

        completion_C1_rate = calculate_C1_rate(completion_event, "Completion")
        workover_C1_rate = calculate_C1_rate(workover_event, "Workover")

        if self.field_production_lifetime is None:
            raise OpgeeException(
                f"{self}: field_production_lifetime must be set to compute "
                "completion+workover C1 rate"
            )
        return (completion_C1_rate + workover_C1_rate) / self.field_production_lifetime

    # ---- validation ----------------------------------------------------

    def validate(self) -> None:
        """Lightweight consistency checks.

        Drops the old Model/Analysis ``skip_validation`` switch and the
        boundary-cycle check (Boundary is deferred). Still performs the
        per-process validate() hook and the SOR/steam_flooding consistency
        check if the relevant values are available on Field.
        """
        msgs: list[str] = []

        for proc in self.process_dict.values():
            validate = getattr(proc, "validate", None)
            if callable(validate):
                try:
                    validate()
                except OpgeeException as exc:
                    msgs.append(str(exc))

        try:
            self._check_run_after_procs()
        except OpgeeException as exc:
            msgs.append(str(exc))

        if msgs:
            raise ModelValidationError("Field validation failed: " + "\n - ".join(msgs))

    # ---- debug / reporting --------------------------------------------

    def report(self, include_streams: bool = False) -> None:
        if include_streams:
            _logger.debug(f"\n*** Streams for field '{self.name}'")
            for stream in self.stream_dict.values():
                _logger.debug(f"{stream}")
        _logger.debug(f"{self}\nEnergy consumption:\n{self.energy.data}")
        _logger.debug(f"Emissions (tonne/day):\n{self.emissions.data}")

    def dump(self) -> None:
        """Print a representation of the field's processes and streams."""
        visited: dict[Process, bool] = {}

        def visit(process: Process) -> None:
            visited[process] = True
            next_procs: list[Process] = []
            print(f"\n> {process} outputs:")
            for stream in process.outputs:
                print(f"  * {stream}")
                dst = stream.dst_proc
                if dst is not None and dst not in visited:
                    next_procs.append(dst)
            for proc in next_procs:
                visit(proc)

        print(f"\n{self}:")
        visit(self.reservoir)

    def print_process_list(self) -> None:
        """Debugging tool — list every process with its connected streams."""
        for name in sorted(self.process_dict.keys()):
            proc = self.process_dict[name]
            print(f"\n{proc}")
            print("  Inputs:")
            for s in proc.inputs:
                print(f"    {s} contains '{s.contents}'")
            print("  Outputs:")
            for s in proc.outputs:
                print(f"    {s} contains '{s.contents}'")
