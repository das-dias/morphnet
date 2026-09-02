from __future__ import annotations

from morphnet.morphnet_schema import (
    Analysis,
    Circuit,
    ExternalModule,
    InitialCondition,
    Measurement,
    Module,
    OutputRequest,
    Simulation,
)
from morphnet.netlist.spectre.parser import parse_spectre
from morphnet.netlist.spectre_spice.preprocess import preprocess_spectre_spice
from morphnet.netlist.spice.parser import parse_spice


class SpectreSpiceParser:
    """Parse Spectre-SPICE netlist text into a Circuit model.

    Splits input on `simulator lang=` directives and delegates each
    section to the appropriate sub-parser.
    """

    @classmethod
    def parse(cls, text: str) -> Circuit:
        sections = preprocess_spectre_spice(text)

        all_modules: list[Module] = []
        all_ext_modules: dict[str, ExternalModule] = {}
        all_directives = []
        all_analyses: list[Analysis] = []
        all_output_requests: list[OutputRequest] = []
        all_measurements: list[Measurement] = []
        all_temperatures: list[float] = []
        ic_conditions: dict[str, str] = {}
        ns_conditions: dict[str, str] = {}

        for section in sections:
            if not section.text.strip():
                continue
            if section.language == "spectre":
                circuit = parse_spectre(section.text)
            else:
                circuit = parse_spice(section.text)

            all_modules.extend(circuit.modules)
            for ext in circuit.ext_modules:
                all_ext_modules[ext.name] = ext
            all_directives.extend(circuit.directives)

            if circuit.simulation:
                all_analyses.extend(circuit.simulation.analyses)
                all_output_requests.extend(circuit.simulation.output_requests)
                all_measurements.extend(circuit.simulation.measurements)
                all_temperatures.extend(circuit.simulation.temperatures)
                if circuit.simulation.initial_conditions:
                    ic_conditions.update(
                        circuit.simulation.initial_conditions.conditions
                    )
                if circuit.simulation.node_sets:
                    ns_conditions.update(circuit.simulation.node_sets.conditions)

        top_module = all_modules[-1].name if all_modules else ""

        has_sim = (
            all_analyses
            or all_output_requests
            or all_measurements
            or ic_conditions
            or ns_conditions
            or all_temperatures
        )
        simulation: Simulation | None = None
        if has_sim:
            simulation = Simulation(
                analyses=all_analyses,
                output_requests=all_output_requests,
                measurements=all_measurements,
                initial_conditions=(
                    InitialCondition(conditions=ic_conditions)
                    if ic_conditions
                    else None
                ),
                node_sets=(
                    InitialCondition(conditions=ns_conditions)
                    if ns_conditions
                    else None
                ),
                temperatures=all_temperatures,
            )

        return Circuit(
            name="",
            domain="spectre_spice",
            top_module=top_module,
            modules=all_modules,
            ext_modules=list(all_ext_modules.values()),
            directives=all_directives,
            simulation=simulation,
        )


def parse_spectre_spice(text: str) -> Circuit:
    """Parse Spectre-SPICE netlist text into a Circuit model."""
    return SpectreSpiceParser.parse(text)
