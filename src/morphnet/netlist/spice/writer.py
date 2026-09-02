from __future__ import annotations

from morphnet.morphnet_schema import (
    Analysis,
    AnalysisKind,
    Circuit,
    Directive,
    DirectiveKind,
    ExternalModule,
    Measurement,
    Module,
    ModuleReference,
    OutputRequest,
    OutputRequestKind,
    ParameterValue,
    Simulation,
)
from morphnet.netlist.net_utils import connections_to_instance_nets
from morphnet.netlist.value_utils import (
    DEVICE_PREFIX_TO_MODULE,
    format_si_value,
)

# Reverse lookup: module name → SPICE device prefix letter — O(1) per instance
MODULE_TO_PREFIX: dict[str, str] = {v: k for k, v in DEVICE_PREFIX_TO_MODULE.items()}


class SpiceWriter:
    """Convert a Circuit model to SPICE netlist text.

    All lookups use dict-based O(1) access.
    """

    def format_param_value(self, pval: ParameterValue) -> str:
        """Format any ParameterValue variant as a SPICE-compatible string."""
        if pval.prefixed_value is not None:
            return format_si_value(pval.prefixed_value)
        if pval.int_value is not None:
            return str(pval.int_value)
        if pval.expression is not None:
            return f"'{pval.expression}'"
        if pval.string_value is not None:
            return pval.string_value
        return "0"

    def write(self, circuit: Circuit) -> str:
        lines: list[str] = []

        # Title line
        title = circuit.name or "untitled"
        lines.append(f"* {title}")

        # Build lookups — O(e + m)
        ext_by_name: dict[str, ExternalModule] = {
            e.name: e for e in circuit.ext_modules
        }
        mod_by_name: dict[str, Module] = {m.name: m for m in circuit.modules}

        self.write_directives(circuit.directives, lines)

        for ext in circuit.ext_modules:
            model_type = ext.properties.get("model_type", "")
            if model_type:
                self.write_model(ext, model_type, lines)

        # Emit subcircuit definitions
        for module in circuit.modules:
            if module.name == "__top__":
                self.write_top_instances(module, ext_by_name, mod_by_name, lines)
            else:
                self.write_subckt(module, ext_by_name, mod_by_name, lines)

        if circuit.simulation:
            self.write_simulation(circuit.simulation, lines)

        lines.append(".end")
        lines.append("")
        return "\n".join(lines)

    def write_directives(
        self, directives: list[Directive], lines: list[str]
    ) -> None:
        for d in directives:
            if d.kind == DirectiveKind.INCLUDE:
                lines.append(f'.include "{d.value}"')
            elif d.kind == DirectiveKind.LIB:
                lines.append(f".lib {d.value}")
            elif d.kind == DirectiveKind.GLOBAL:
                lines.append(f".global {d.value}")
            elif d.kind == DirectiveKind.OPTION:
                lines.append(f".option {d.name}={d.value}")
            elif d.kind == DirectiveKind.PARAM:
                lines.append(f".param {d.name}={d.value}")

    def write_model(
        self,
        ext: ExternalModule,
        model_type: str,
        lines: list[str],
    ) -> None:
        """Emit a .model statement."""
        param_strs: list[str] = []
        for p in ext.parameters:
            if p.default_value:
                param_strs.append(
                    f"{p.name}={self.format_param_value(p.default_value)}"
                )
        params_text = " ".join(param_strs)
        if params_text:
            lines.append(f".model {ext.name} {model_type} {params_text}")
        else:
            lines.append(f".model {ext.name} {model_type}")

    def write_subckt(
        self,
        module: Module,
        ext_by_name: dict[str, ExternalModule],
        mod_by_name: dict[str, Module],
        lines: list[str],
    ) -> None:
        """Emit a .subckt / .ends block."""
        port_names = " ".join(p.name for p in module.ports)
        lines.append(f".subckt {module.name} {port_names}")

        # Emit .param for module parameters
        for param in module.parameters:
            if param.default_value:
                val = self.format_param_value(param.default_value)
                lines.append(f".param {param.name}={val}")

        # Build (instance_name, port_name) → net_name — O(c)
        inst_nets = connections_to_instance_nets(module.connections)

        # Emit instances
        for ref in module.module_references:
            lines.append(self.write_instance(ref, inst_nets, ext_by_name, mod_by_name))

        lines.append(f".ends {module.name}")

    def write_top_instances(
        self,
        module: Module,
        ext_by_name: dict[str, ExternalModule],
        mod_by_name: dict[str, Module],
        lines: list[str],
    ) -> None:
        """Emit top-level instances (outside any subcircuit)."""
        inst_nets = connections_to_instance_nets(module.connections)
        for ref in module.module_references:
            lines.append(self.write_instance(ref, inst_nets, ext_by_name, mod_by_name))

    def write_instance(
        self,
        ref: ModuleReference,
        inst_nets: dict[tuple[str, str], str],
        ext_by_name: dict[str, ExternalModule],
        mod_by_name: dict[str, Module],
    ) -> str:
        """Emit a single instance line.

        Device prefix and port order determined by O(1) dict lookups.
        """
        prefix = MODULE_TO_PREFIX.get(ref.module_name)
        ext_mod = ext_by_name.get(ref.module_name)

        if prefix:
            # Primitive device: R1 net1 net2 value param=val ...
            inst_name = ref.name
            if ext_mod:
                port_order = [p.name for p in ext_mod.ports]
            else:
                port_order = ["p", "n"]

            nets = [inst_nets.get((inst_name, pn), "?") for pn in port_order]
            nets_str = " ".join(nets)

            model_name = ref.model_name

            # Device value (for R, C, L)
            value_str = ""
            value_param = ref.parameter_overrides.get("value")
            if value_param and value_param.default_value:
                value_str = self.format_param_value(value_param.default_value)

            # Other params
            other_params: list[str] = []
            for pname, param in ref.parameter_overrides.items():
                if pname == "value":
                    continue
                if param.default_value:
                    other_params.append(
                        f"{pname}={self.format_param_value(param.default_value)}"
                    )

            parts = [inst_name, nets_str]
            if model_name:
                parts.append(model_name)
            if value_str:
                parts.append(value_str)
            if other_params:
                parts.extend(other_params)

            return " ".join(parts)

        # Subcircuit instance: X1 net1 net2 ... subckt_name param=val
        inst_name = ref.name
        subckt_name = ref.module_name

        # Resolve port order: module defs first, then ext_modules, then infer
        ref_mod = mod_by_name.get(subckt_name)
        if ref_mod is not None:
            port_order = [p.name for p in ref_mod.ports]
        elif ext_mod is not None:
            port_order = [p.name for p in ext_mod.ports]
        else:
            port_order = self.infer_port_order(ref, inst_nets)

        nets = [inst_nets.get((inst_name, pn), "?") for pn in port_order]
        nets_str = " ".join(nets)

        params_parts: list[str] = []
        for pname, param in ref.parameter_overrides.items():
            if param.default_value:
                params_parts.append(
                    f"{pname}={self.format_param_value(param.default_value)}"
                )

        parts = [inst_name, nets_str, subckt_name]
        if params_parts:
            parts.extend(params_parts)
        return " ".join(parts)

    def infer_port_order(
        self,
        ref: ModuleReference,
        inst_nets: dict[tuple[str, str], str],
    ) -> list[str]:
        """Infer port order from the instance-net map when no module def is available."""
        port_names: list[str] = []
        for iname, pname in inst_nets:
            if iname == ref.name and pname not in port_names:
                port_names.append(pname)
        return port_names

    # ── Simulation writing ──────────────────────────────────────────────

    def write_simulation(
        self, simulation: Simulation, lines: list[str]
    ) -> None:
        for analysis in simulation.analyses:
            lines.append(self.format_analysis(analysis))
        for req in simulation.output_requests:
            lines.append(self.format_output_request(req))
        for meas in simulation.measurements:
            lines.append(self.format_measurement(meas))
        if simulation.initial_conditions:
            assigns = " ".join(
                f"{k}={v}"
                for k, v in simulation.initial_conditions.conditions.items()
            )
            lines.append(f".ic {assigns}")
        if simulation.node_sets:
            assigns = " ".join(
                f"{k}={v}"
                for k, v in simulation.node_sets.conditions.items()
            )
            lines.append(f".nodeset {assigns}")
        if simulation.temperatures:
            temps = " ".join(str(t) for t in simulation.temperatures)
            lines.append(f".temp {temps}")

    def format_analysis(self, analysis: Analysis) -> str:
        keyword = _ANALYSIS_KIND_TO_KW.get(analysis.kind, ".op")
        parts = [keyword]
        parts.extend(analysis.arguments)
        for k, v in analysis.options.items():
            parts.append(f"{k}={v}")
        return " ".join(parts)

    def format_output_request(self, req: OutputRequest) -> str:
        keyword = _OUTPUT_REQUEST_KIND_TO_KW.get(req.kind, ".print")
        parts = [keyword]
        if req.analysis_type:
            parts.append(req.analysis_type)
        parts.extend(req.variables)
        return " ".join(parts)

    def format_measurement(self, meas: Measurement) -> str:
        parts = [".meas"]
        if meas.analysis_type:
            parts.append(meas.analysis_type)
        if meas.name:
            parts.append(meas.name)
        if meas.body:
            parts.append(meas.body)
        return " ".join(parts)


_ANALYSIS_KIND_TO_KW: dict[AnalysisKind, str] = {
    AnalysisKind.OP: ".op",
    AnalysisKind.DC: ".dc",
    AnalysisKind.AC: ".ac",
    AnalysisKind.TRAN: ".tran",
    AnalysisKind.NOISE: ".noise",
    AnalysisKind.TF: ".tf",
    AnalysisKind.SENS: ".sens",
    AnalysisKind.PZ: ".pz",
    AnalysisKind.DISTO: ".disto",
    AnalysisKind.FOUR: ".four",
    AnalysisKind.FFT: ".fft",
}

_OUTPUT_REQUEST_KIND_TO_KW: dict[OutputRequestKind, str] = {
    OutputRequestKind.PRINT: ".print",
    OutputRequestKind.PLOT: ".plot",
    OutputRequestKind.PROBE: ".probe",
    OutputRequestKind.SAVE: "save",
}


def write_spice(circuit: Circuit) -> str:
    """Convert a Circuit model to SPICE netlist text."""
    return SpiceWriter().write(circuit)
