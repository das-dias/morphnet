from __future__ import annotations

from hubnet.hubnet_schema import (
    Circuit,
    Directive,
    DirectiveKind,
    ExternalModule,
    ExternalModuleKind,
    Module,
    ModuleReference,
)
from hubnet.netlist.net_utils import connections_to_instance_nets
from hubnet.netlist.value_utils import format_si_value


class VamsWriter:
    """Convert a Circuit model to Verilog-AMS netlist text."""

    def write(self, circuit: Circuit) -> str:
        lines: list[str] = []

        ext_by_name: dict[str, ExternalModule] = {
            e.name: e for e in circuit.ext_modules
        }
        mod_by_name: dict[str, Module] = {m.name: m for m in circuit.modules}

        self.write_directives(circuit.directives, lines)

        for ext in circuit.ext_modules:
            if ext.kind == ExternalModuleKind.NATURE:
                self.write_nature(ext, lines)
            elif ext.kind == ExternalModuleKind.DISCIPLINE:
                self.write_discipline(ext, lines)

        for module in circuit.modules:
            self.write_module(module, ext_by_name, mod_by_name, lines)

        if lines and lines[-1] != "":
            lines.append("")
        return "\n".join(lines)

    def write_directives(
        self, directives: list[Directive], lines: list[str]
    ) -> None:
        for d in directives:
            if d.kind == DirectiveKind.INCLUDE:
                lines.append(f'`include "{d.value}"')
            elif d.kind == DirectiveKind.DEFINE:
                lines.append(f"`define {d.value}")
            elif d.kind == DirectiveKind.TIMESCALE:
                lines.append(f"`timescale {d.value}")

    def write_nature(self, ext: ExternalModule, lines: list[str]) -> None:
        lines.append(f"nature {ext.name};")
        for key, val in ext.properties.items():
            if key.startswith("nature_"):
                attr = key.removeprefix("nature_")
                lines.append(f"  {attr} = {val};")
        lines.append("endnature")

    def write_discipline(self, ext: ExternalModule, lines: list[str]) -> None:
        lines.append(f"discipline {ext.name};")
        domain = ext.properties.get("discipline_domain")
        if domain:
            lines.append(f"  domain {domain};")
        for key, val in ext.properties.items():
            if key.startswith("discipline_") and key != "discipline_domain":
                role = key.removeprefix("discipline_")
                lines.append(f"  {role} {val};")
        lines.append("enddiscipline")

    def write_module(
        self,
        module: Module,
        ext_by_name: dict[str, ExternalModule],
        mod_by_name: dict[str, Module],
        lines: list[str],
    ) -> None:
        port_names = [p.name for p in module.ports]
        ports_str = ", ".join(port_names)
        lines.append(f"module {module.name} ({ports_str});")

        dirs_by_dir: dict[str, list[str]] = {}
        for port in module.ports:
            d = port.direction.name.lower()
            dirs_by_dir.setdefault(d, []).append(port.name)
        for d, names in dirs_by_dir.items():
            lines.append(f"  {d} {', '.join(names)};")

        disc_by_disc: dict[str, list[str]] = {}
        for port in module.ports:
            if port.discipline:
                disc_by_disc.setdefault(port.discipline, []).append(port.name)
        for disc, names in disc_by_disc.items():
            lines.append(f"  {disc} {', '.join(names)};")

        for param in module.parameters:
            is_local = param.properties.get("localparam") == "true"
            kw = "localparam" if is_local else "parameter"
            ptype = param.properties.get("type", "")
            val = self.format_param_value(param.default_value)
            type_str = f" {ptype}" if ptype else ""
            lines.append(f"  {kw}{type_str} {param.name} = {val};")

        ground_net = module.properties.get("ground_net")
        if ground_net:
            lines.append(f"  ground {ground_net};")

        inst_nets = connections_to_instance_nets(module.connections)

        for ref in module.module_references:
            lines.append(
                self.write_instance(ref, inst_nets, ext_by_name, mod_by_name)
            )

        analog_block = module.properties.get("analog_block")
        if analog_block:
            lines.append(f"  {analog_block}")

        lines.append("endmodule")

    def write_instance(
        self,
        ref: ModuleReference,
        inst_nets: dict[tuple[str, str], str],
        ext_by_name: dict[str, ExternalModule],
        mod_by_name: dict[str, Module],
    ) -> str:
        params_str = ""
        if ref.parameter_overrides:
            param_parts: list[str] = []
            for pname, param in ref.parameter_overrides.items():
                if param.default_value:
                    val = self.format_param_value(param.default_value)
                    param_parts.append(f".{pname}({val})")
            params_str = f" #({', '.join(param_parts)})"

        ref_mod = mod_by_name.get(ref.module_name)
        ext_mod = ext_by_name.get(ref.module_name)
        if ref_mod is not None:
            port_order = [p.name for p in ref_mod.ports]
        elif ext_mod is not None:
            port_order = [p.name for p in ext_mod.ports]
        else:
            port_order = self.infer_port_order(ref, inst_nets)

        port_parts: list[str] = []
        for pn in port_order:
            net = inst_nets.get((ref.name, pn), "?")
            port_parts.append(f".{pn}({net})")
        ports_str = ", ".join(port_parts)

        return f"  {ref.module_name}{params_str} {ref.name} ({ports_str});"

    def format_param_value(self, pval: object) -> str:
        from hubnet.hubnet_schema import ParameterValue

        if pval is None:
            return "0"
        if not isinstance(pval, ParameterValue):
            return str(pval)
        if pval.prefixed_value is not None:
            return format_si_value(pval.prefixed_value)
        if pval.string_value is not None:
            return pval.string_value
        if pval.expression is not None:
            return pval.expression
        if pval.int_value is not None:
            return str(pval.int_value)
        return "0"

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


def write_vams(circuit: Circuit) -> str:
    """Convert a Circuit model to Verilog-AMS netlist text."""
    return VamsWriter().write(circuit)
