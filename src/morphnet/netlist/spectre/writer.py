from __future__ import annotations

from morphnet.morphnet_schema import (
    Analysis,
    AnalysisKind,
    Circuit,
    Directive,
    DirectiveKind,
    ExternalModule,
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

MODULE_TO_PREFIX: dict[str, str] = {v: k for k, v in DEVICE_PREFIX_TO_MODULE.items()}


class SpectreWriter:
    """Convert a Circuit model to Spectre netlist text."""

    def format_param_value(self, pval: ParameterValue) -> str:
        """Format any ParameterValue variant as a Spectre-compatible string."""
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

        ext_by_name: dict[str, ExternalModule] = {
            e.name: e for e in circuit.ext_modules
        }
        mod_by_name: dict[str, Module] = {m.name: m for m in circuit.modules}

        self.write_directives(circuit.directives, lines)

        for ext in circuit.ext_modules:
            model_type = ext.properties.get("model_type")
            if model_type:
                self.write_model(ext, model_type, lines)

        for module in circuit.modules:
            if module.name == "__top__":
                self.write_top_instances(module, ext_by_name, mod_by_name, lines)
            else:
                self.write_subckt(module, ext_by_name, mod_by_name, lines)

        if circuit.simulation:
            self.write_simulation(circuit.simulation, lines)

        lines.append("")
        return "\n".join(lines)

    def write_directives(
        self, directives: list[Directive], lines: list[str]
    ) -> None:
        params: dict[str, str] = {}
        for d in directives:
            if d.kind == DirectiveKind.INCLUDE:
                lines.append(f'include "{d.value}"')
            elif d.kind == DirectiveKind.PARAM:
                params[d.name] = d.value
        if params:
            assigns = " ".join(f"{k}={v}" for k, v in params.items())
            lines.append(f"parameters {assigns}")

    def write_model(
        self, ext: ExternalModule, model_type: str, lines: list[str]
    ) -> None:
        param_strs: list[str] = []
        for p in ext.parameters:
            if p.default_value:
                param_strs.append(
                    f"{p.name}={self.format_param_value(p.default_value)}"
                )
        params_text = " ".join(param_strs)
        lines.append(f"model {ext.name} {model_type} ({params_text})")

    def write_subckt(
        self,
        module: Module,
        ext_by_name: dict[str, ExternalModule],
        mod_by_name: dict[str, Module],
        lines: list[str],
    ) -> None:
        port_names = " ".join(p.name for p in module.ports)

        param_strs: list[str] = []
        for param in module.parameters:
            if param.default_value:
                param_strs.append(
                    f"{param.name}={self.format_param_value(param.default_value)}"
                )
        params_suffix = " " + " ".join(param_strs) if param_strs else ""

        lines.append(f"subckt {module.name} ({port_names}){params_suffix}")

        inst_nets = connections_to_instance_nets(module.connections)

        for ref in module.module_references:
            lines.append(self.write_instance(ref, inst_nets, ext_by_name, mod_by_name))

        lines.append(f"ends {module.name}")

    def write_top_instances(
        self,
        module: Module,
        ext_by_name: dict[str, ExternalModule],
        mod_by_name: dict[str, Module],
        lines: list[str],
    ) -> None:
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
        ext_mod = ext_by_name.get(ref.module_name)
        prefix = MODULE_TO_PREFIX.get(ref.module_name)

        # Determine port order
        if prefix and ext_mod:
            port_order = [p.name for p in ext_mod.ports]
        else:
            ref_mod = mod_by_name.get(ref.module_name)
            if ref_mod:
                port_order = [p.name for p in ref_mod.ports]
            elif ext_mod:
                port_order = [p.name for p in ext_mod.ports]
            else:
                port_order = self.infer_port_order(ref, inst_nets)

        nets = [inst_nets.get((ref.name, pn), "?") for pn in port_order]
        nets_str = " ".join(nets)

        cell_name = ref.model_name if ref.model_name else ref.module_name

        # Params
        param_strs: list[str] = []
        for pname, param in ref.parameter_overrides.items():
            if param.default_value:
                param_strs.append(
                    f"{pname}={self.format_param_value(param.default_value)}"
                )

        params_text = " " + " ".join(param_strs) if param_strs else ""
        return f"{ref.name} ({nets_str}) {cell_name}{params_text}"

    def infer_port_order(
        self,
        ref: ModuleReference,
        inst_nets: dict[tuple[str, str], str],
    ) -> list[str]:
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

    def format_analysis(self, analysis: Analysis) -> str:
        keyword = _ANALYSIS_KIND_TO_SPECTRE.get(analysis.kind, "dc")
        parts = [analysis.name or keyword, keyword]
        for k, v in analysis.options.items():
            parts.append(f"{k}={v}")
        return " ".join(parts)

    def format_output_request(self, req: OutputRequest) -> str:
        if req.kind == OutputRequestKind.SAVE:
            return "save " + " ".join(req.variables)
        return "save " + " ".join(req.variables)


_ANALYSIS_KIND_TO_SPECTRE: dict[AnalysisKind, str] = {
    AnalysisKind.OP: "op",
    AnalysisKind.DC: "dc",
    AnalysisKind.AC: "ac",
    AnalysisKind.TRAN: "tran",
    AnalysisKind.NOISE: "noise",
}


def write_spectre(circuit: Circuit) -> str:
    """Convert a Circuit model to Spectre netlist text."""
    return SpectreWriter().write(circuit)
