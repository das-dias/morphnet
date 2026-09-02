from __future__ import annotations

from typing import Any

from lark import Token, Transformer

from morphnet.morphnet_schema import (
    Circuit,
    ExternalModule,
    ExternalModuleKind,
    Module,
    ModuleReference,
    Parameter,
    ParameterValue,
    Port,
    PortDirection,
    PrefixedValue,
    SignalDomain,
)
from morphnet.netlist.net_utils import NetMap, add_port_to_net, net_map_to_connections
from morphnet.netlist.value_utils import parse_parameter_number


class InstanceData:
    __slots__ = ("module_type", "name", "named_params", "named_ports",
                 "positional_params", "positional_ports")

    def __init__(
        self,
        module_type: str,
        name: str,
        named_ports: dict[str, str],
        positional_ports: list[str],
        named_params: dict[str, ParameterValue],
        positional_params: list[ParameterValue],
    ) -> None:
        self.module_type = module_type
        self.name = name
        self.named_ports = named_ports
        self.positional_ports = positional_ports
        self.named_params = named_params
        self.positional_params = positional_params


class NatureData:
    __slots__ = ("attrs", "name")

    def __init__(self, name: str, attrs: dict[str, ParameterValue]) -> None:
        self.name = name
        self.attrs = attrs


class DisciplineData:
    __slots__ = ("domain", "name", "natures")

    def __init__(
        self, name: str, natures: dict[str, str], domain: str
    ) -> None:
        self.name = name
        self.natures = natures
        self.domain = domain


class ParamsetData:
    __slots__ = ("base_type", "name", "params")

    def __init__(
        self, name: str, base_type: str, params: dict[str, ParameterValue]
    ) -> None:
        self.name = name
        self.base_type = base_type
        self.params = params


class PortDirData:
    __slots__ = ("direction", "names")

    def __init__(self, direction: PortDirection, names: list[str]) -> None:
        self.direction = direction
        self.names = names


class DisciplineDeclData:
    __slots__ = ("discipline", "names")

    def __init__(self, discipline: str, names: list[str]) -> None:
        self.discipline = discipline
        self.names = names


class GroundData:
    __slots__ = ("net",)

    def __init__(self, net: str) -> None:
        self.net = net


class AnalogData:
    __slots__ = ("index",)

    def __init__(self, index: int) -> None:
        self.index = index


DIR_MAP = {
    "input": PortDirection.INPUT,
    "output": PortDirection.OUTPUT,
    "inout": PortDirection.INOUT,
}


class VamsTransformer(Transformer[Token, Circuit]):
    """Transform a Verilog-AMS parse tree into a Circuit model."""

    def __init__(self, analog_blocks: list[str] | None = None) -> None:
        super().__init__()
        self.analog_blocks = analog_blocks or []

    # ── Leaf transformers ───────────────────────────────────────────────

    def pvalue_number(self, items: list[Token]) -> ParameterValue:
        return parse_parameter_number(str(items[0]))

    def pvalue_ident(self, items: list[Token]) -> ParameterValue:
        return ParameterValue(string_value=str(items[0]))

    def pvalue_string(self, items: list[Token]) -> ParameterValue:
        raw = str(items[0]).strip("\"'")
        return ParameterValue(string_value=raw)

    def param_assign(self, items: list[Any]) -> tuple[str, ParameterValue]:
        name = str(items[0])
        value = items[1]
        if not isinstance(value, ParameterValue):
            value = ParameterValue(string_value=str(value))
        return (name, value)

    def param_assign_list(self, items: list[Any]) -> list[tuple[str, ParameterValue]]:
        return [item for item in items if isinstance(item, tuple)]

    def param_type(self, items: list[Token]) -> str:
        return str(items[0])

    # ── Port list ──────────────────────────────────────────────────────

    def port_list(self, items: list[Any]) -> list[str]:
        return [str(item) for item in items if isinstance(item, Token)]

    def port_item(self, items: list[Token]) -> Token:
        return items[0]

    def port_name_list(self, items: list[Token]) -> list[str]:
        return [str(t) for t in items]

    # ── Port direction declarations ────────────────────────────────────

    def port_dir_decl(self, items: list[Any]) -> PortDirData:
        direction = DIR_MAP.get(str(items[0]), PortDirection.INOUT)
        names = items[1] if isinstance(items[1], list) else [str(items[1])]
        return PortDirData(direction=direction, names=names)

    # ── Discipline declaration ─────────────────────────────────────────

    def discipline_decl(self, items: list[Any]) -> DisciplineDeclData:
        discipline = str(items[0])
        names = items[1] if isinstance(items[1], list) else [str(items[1])]
        return DisciplineDeclData(discipline=discipline, names=names)

    # ── Parameter / localparam ─────────────────────────────────────────

    def _coerce_value(self, ptype: str, pval: ParameterValue) -> ParameterValue:
        """Coerce a ParameterValue to match the declared Verilog-AMS type."""
        match ptype:
            case "integer":
                if pval.int_value is not None:
                    return pval
                if pval.prefixed_value is not None:
                    return ParameterValue(int_value=int(pval.prefixed_value.double_value))
                if pval.string_value is not None:
                    try:
                        return ParameterValue(int_value=int(pval.string_value))
                    except ValueError:
                        return pval
            case "string":
                if pval.string_value is not None:
                    return pval
                if pval.prefixed_value is not None:
                    return ParameterValue(
                        string_value=str(pval.prefixed_value.double_value)
                    )
            case "real":
                if pval.int_value is not None:
                    return ParameterValue(
                        prefixed_value=PrefixedValue(
                            double_value=float(pval.int_value)
                        )
                    )
                return pval
        return pval

    def typed_parameter_decl(
        self, items: list[Any]
    ) -> list[tuple[str, ParameterValue, str]]:
        ptype = str(items[0])
        assigns: list[tuple[str, ParameterValue]] = []
        for item in items:
            if isinstance(item, list):
                assigns = item
                break
        return [(n, self._coerce_value(ptype, v), ptype) for n, v in assigns]

    def untyped_parameter_decl(
        self, items: list[Any]
    ) -> list[tuple[str, ParameterValue, str]]:
        assigns: list[tuple[str, ParameterValue]] = []
        for item in items:
            if isinstance(item, list):
                assigns = item
                break
        return [(n, v, "") for n, v in assigns]

    def typed_localparam_decl(
        self, items: list[Any]
    ) -> list[tuple[str, ParameterValue, str]]:
        ptype = str(items[0])
        assigns: list[tuple[str, ParameterValue]] = []
        for item in items:
            if isinstance(item, list):
                assigns = item
                break
        return [(n, self._coerce_value(ptype, v), f"localparam:{ptype}") for n, v in assigns]

    def untyped_localparam_decl(
        self, items: list[Any]
    ) -> list[tuple[str, ParameterValue, str]]:
        assigns: list[tuple[str, ParameterValue]] = []
        for item in items:
            if isinstance(item, list):
                assigns = item
                break
        return [(n, v, "localparam") for n, v in assigns]

    # ── Ground statement ───────────────────────────────────────────────

    def ground_stmt(self, items: list[Token]) -> GroundData:
        return GroundData(net=str(items[0]))

    # ── Instance statement ─────────────────────────────────────────────

    def named_override(self, items: list[Any]) -> tuple[str, ParameterValue]:
        name = str(items[0])
        value = items[1]
        if not isinstance(value, ParameterValue):
            value = ParameterValue(string_value=str(value))
        return (name, value)

    def positional_override(self, items: list[Any]) -> ParameterValue:
        v = items[0]
        if not isinstance(v, ParameterValue):
            v = ParameterValue(string_value=str(v))
        return v

    def param_override(self, items: list[Any]) -> dict[str, ParameterValue] | list[ParameterValue]:
        named: dict[str, ParameterValue] = {}
        positional: list[ParameterValue] = []
        for item in items:
            if isinstance(item, tuple):
                named[item[0]] = item[1]
            elif isinstance(item, ParameterValue):
                positional.append(item)
        return named if named else positional

    def named_conn(self, items: list[Token]) -> tuple[str, str]:
        return (str(items[0]), str(items[1]))

    def positional_conn(self, items: list[Token]) -> str:
        return str(items[0])

    def port_conn(self, items: list[Any]) -> dict[str, str] | list[str]:
        named: dict[str, str] = {}
        positional: list[str] = []
        for item in items:
            if isinstance(item, tuple):
                named[item[0]] = item[1]
            elif isinstance(item, str):
                positional.append(item)
        return named if named else positional

    def instance_stmt(self, items: list[Any]) -> InstanceData:
        module_type = str(items[0])

        params: dict[str, ParameterValue] | list[ParameterValue] = {}
        inst_name = ""
        ports: dict[str, str] | list[str] = []

        idx = 1
        if idx < len(items) and isinstance(items[idx], (dict, list)) and not isinstance(items[idx], (str, Token)):
            p = items[idx]
            if isinstance(p, dict) or (isinstance(p, list) and p and isinstance(p[0], ParameterValue)):
                params = p
            idx += 1

        if idx < len(items) and isinstance(items[idx], Token):
            inst_name = str(items[idx])
            idx += 1

        if idx < len(items):
            ports = items[idx]

        named_params: dict[str, ParameterValue] = {}
        positional_params: list[ParameterValue] = []
        if isinstance(params, dict):
            named_params = params
        elif isinstance(params, list):
            positional_params = params

        named_ports: dict[str, str] = {}
        positional_ports: list[str] = []
        if isinstance(ports, dict):
            named_ports = ports
        elif isinstance(ports, list):
            positional_ports = ports

        return InstanceData(
            module_type=module_type,
            name=inst_name,
            named_ports=named_ports,
            positional_ports=positional_ports,
            named_params=named_params,
            positional_params=positional_params,
        )

    # ── Analog placeholder ─────────────────────────────────────────────

    def analog_placeholder(self, items: list[Token]) -> AnalogData:
        return AnalogData(index=int(float(str(items[0]))))

    # ── Nature definition ──────────────────────────────────────────────

    def nature_body(self, items: list[Any]) -> dict[str, ParameterValue]:
        attrs: dict[str, ParameterValue] = {}
        for item in items:
            if isinstance(item, tuple):
                attrs[item[0]] = item[1]
        return attrs

    def nature_attr(self, items: list[Any]) -> tuple[str, ParameterValue]:
        name = str(items[0])
        value = items[1]
        if not isinstance(value, ParameterValue):
            value = ParameterValue(string_value=str(value))
        return (name, value)

    def nature_def(self, items: list[Any]) -> NatureData:
        name = str(items[0])
        attrs = items[1] if isinstance(items[1], dict) else {}
        return NatureData(name=name, attrs=attrs)

    # ── Discipline definition ──────────────────────────────────────────

    def discipline_body(self, items: list[Any]) -> tuple[dict[str, str], str]:
        natures: dict[str, str] = {}
        domain = ""
        for item in items:
            if isinstance(item, tuple) and len(item) == 2:
                natures[item[0]] = item[1]
            elif isinstance(item, str):
                domain = item
        return natures, domain

    def discipline_nature_attr(self, items: list[Token]) -> tuple[str, str]:
        return (str(items[0]), str(items[1]))

    def discipline_domain_attr(self, items: list[Token]) -> str:
        return str(items[0])

    def discipline_def(self, items: list[Any]) -> DisciplineData:
        name = str(items[0])
        body = items[1] if isinstance(items[1], tuple) else ({}, "")
        natures, domain = body
        return DisciplineData(name=name, natures=natures, domain=domain)

    # ── Paramset definition ────────────────────────────────────────────

    def paramset_body(self, items: list[Any]) -> dict[str, ParameterValue]:
        params: dict[str, ParameterValue] = {}
        for item in items:
            if isinstance(item, tuple) and len(item) == 2:
                params[item[0]] = item[1]
        return params

    def paramset_param(self, items: list[Any]) -> tuple[str, ParameterValue] | None:
        for item in items:
            if isinstance(item, tuple) and len(item) == 2:
                name, val = item
                if isinstance(val, ParameterValue):
                    return (name, val)
        return None

    def paramset_constraint(self, items: list[Any]) -> None:
        return None

    def paramset_def(self, items: list[Any]) -> ParamsetData:
        name = str(items[0])
        base_type = str(items[1])
        params = items[2] if isinstance(items[2], dict) else {}
        return ParamsetData(name=name, base_type=base_type, params=params)

    # ── Module body ────────────────────────────────────────────────────

    def module_body(self, items: list[Any]) -> list[Any]:
        return [i for i in items if i is not None]

    # ── Module definition ──────────────────────────────────────────────

    def module_def(self, items: list[Any]) -> tuple[str, Module, dict[str, ExternalModule]]:
        module_name = str(items[0])

        port_names: list[str] = []
        body_items: list[Any] = []

        for item in items[1:]:
            if isinstance(item, list) and item and isinstance(item[0], str) and not isinstance(item[0], Token):
                port_names = item
            elif isinstance(item, list):
                body_items = item

        port_dirs: dict[str, PortDirection] = {}
        port_disciplines: dict[str, str] = {}
        parameters: list[Parameter] = []
        instances: list[InstanceData] = []
        ground_net = ""
        analog_block = ""
        properties: dict[str, str] = {}

        for item in body_items:
            if isinstance(item, PortDirData):
                for n in item.names:
                    port_dirs[n] = item.direction
            elif isinstance(item, DisciplineDeclData):
                for n in item.names:
                    port_disciplines[n] = item.discipline
            elif isinstance(item, list) and item and isinstance(item[0], tuple):
                for entry in item:
                    if len(entry) == 3:
                        pname, pval, ptype_tag = entry
                        props: dict[str, str] = {}
                        if ptype_tag.startswith("localparam"):
                            props["localparam"] = "true"
                            ptype = ptype_tag.removeprefix("localparam:") if ":" in ptype_tag else ""
                        else:
                            ptype = ptype_tag
                        if ptype:
                            props["type"] = ptype
                        parameters.append(
                            Parameter(name=pname, default_value=pval, properties=props)
                        )
                    elif len(entry) == 2:
                        pname, pval = entry
                        parameters.append(Parameter(name=pname, default_value=pval))
            elif isinstance(item, InstanceData):
                instances.append(item)
            elif isinstance(item, GroundData):
                ground_net = item.net
            elif isinstance(item, AnalogData) and item.index < len(self.analog_blocks):
                analog_block = self.analog_blocks[item.index]

        ports: list[Port] = []
        for i, pn in enumerate(port_names):
            ports.append(Port(
                uid=i,
                name=pn,
                direction=port_dirs.get(pn, PortDirection.INOUT),
                domain=SignalDomain.ELECTRICAL,
                discipline=port_disciplines.get(pn, ""),
            ))

        if ground_net:
            properties["ground_net"] = ground_net
        if analog_block:
            properties["analog_block"] = analog_block

        net_map: NetMap = {}
        module_references: list[ModuleReference] = []
        ext_modules: dict[str, ExternalModule] = {}

        for port in ports:
            add_port_to_net(net_map, port.name, "", port.name)

        for inst in instances:
            param_overrides: dict[str, Parameter] = {}
            if inst.named_params:
                param_overrides = {
                    pname: Parameter(name=pname, default_value=pval)
                    for pname, pval in inst.named_params.items()
                }
            elif inst.positional_params:
                for pi, pv in enumerate(inst.positional_params):
                    pname = f"p{pi}"
                    param_overrides[pname] = Parameter(
                        name=pname, default_value=pv
                    )

            if inst.named_ports:
                for port_name, net_name in inst.named_ports.items():
                    add_port_to_net(net_map, net_name, inst.name, port_name)
            elif inst.positional_ports:
                for pi, net_name in enumerate(inst.positional_ports):
                    add_port_to_net(net_map, net_name, inst.name, f"p{pi}")

            module_references.append(
                ModuleReference(
                    name=inst.name,
                    module_name=inst.module_type,
                    parameter_overrides=param_overrides,
                )
            )

        connections = net_map_to_connections(net_map)

        module = Module(
            name=module_name,
            ports=ports,
            parameters=parameters,
            module_references=module_references,
            connections=connections,
            properties=properties,
        )

        return (module_name, module, ext_modules)

    # ── Top-level ──────────────────────────────────────────────────────

    def start(self, items: list[Any]) -> Circuit:
        modules: list[Module] = []
        ext_modules: dict[str, ExternalModule] = {}

        for item in items:
            if item is None:
                continue
            if isinstance(item, tuple) and len(item) == 3:
                _, mod, ext = item
                if isinstance(mod, Module):
                    modules.append(mod)
                    ext_modules.update(ext)
            elif isinstance(item, NatureData):
                props: dict[str, str] = {}
                for k, v in item.attrs.items():
                    if v.string_value is not None:
                        props[f"nature_{k}"] = v.string_value
                    elif v.prefixed_value is not None:
                        from morphnet.netlist.value_utils import format_si_value
                        props[f"nature_{k}"] = format_si_value(v.prefixed_value)
                ext_modules[item.name] = ExternalModule(
                    name=item.name,
                    domain="vams",
                    kind=ExternalModuleKind.NATURE,
                    properties=props,
                )
            elif isinstance(item, DisciplineData):
                props = {}
                for role, nature_name in item.natures.items():
                    props[f"discipline_{role}"] = nature_name
                if item.domain:
                    props["discipline_domain"] = item.domain
                ext_modules[item.name] = ExternalModule(
                    name=item.name,
                    domain="vams",
                    kind=ExternalModuleKind.DISCIPLINE,
                    properties=props,
                )
            elif isinstance(item, ParamsetData):
                params = [
                    Parameter(name=pn, default_value=pv)
                    for pn, pv in item.params.items()
                ]
                ext_modules[item.name] = ExternalModule(
                    name=item.name,
                    domain="vams",
                    parameters=params,
                    kind=ExternalModuleKind.MODEL,
                    properties={"model_type": item.base_type},
                )

        top_module = modules[-1].name if modules else ""

        return Circuit(
            name="",
            domain="vams",
            top_module=top_module,
            modules=modules,
            ext_modules=list(ext_modules.values()),
        )
