from __future__ import annotations

from typing import Any

from lark import Token, Transformer

from morphnet.morphnet_schema import (
    Analysis,
    Circuit,
    Directive,
    DirectiveKind,
    ExternalModule,
    ExternalModuleKind,
    Module,
    ModuleReference,
    OutputRequest,
    Parameter,
    ParameterValue,
    Port,
    PortDirection,
    SignalDomain,
    Simulation,
)
from morphnet.netlist.net_utils import NetMap, add_port_to_net, net_map_to_connections
from morphnet.netlist.simulation_data import (
    ANALYSIS_KIND_MAP,
    OUTPUT_REQUEST_KIND_MAP,
    AnalysisData,
    OutputRequestData,
)
from morphnet.netlist.value_utils import (
    DEVICE_PORT_TEMPLATES,
    DEVICE_PREFIX_TO_MODULE,
    format_si_value,
    parse_parameter_number,
)

SPECTRE_ANALYSIS_TYPES: set[str] = {
    "tran", "dc", "ac", "noise", "sp", "stb", "pss", "pnoise", "xf", "psp",
    "op",
}


def _param_value_to_str(pval: ParameterValue) -> str:
    """Convert a ParameterValue to a plain string for directive storage."""
    if pval.prefixed_value is not None:
        return format_si_value(pval.prefixed_value)
    if pval.int_value is not None:
        return str(pval.int_value)
    if pval.expression is not None:
        return pval.expression
    if pval.string_value is not None:
        return pval.string_value
    return ""


class InstanceData:
    __slots__ = ("cell_name", "device_prefix", "name", "net_names", "params")

    def __init__(
        self,
        name: str,
        net_names: list[str],
        cell_name: str,
        params: dict[str, ParameterValue],
        device_prefix: str,
    ) -> None:
        self.name = name
        self.net_names = net_names
        self.cell_name = cell_name
        self.params = params
        self.device_prefix = device_prefix


class ModelData:
    __slots__ = ("name", "params", "type_name")

    def __init__(
        self, name: str, type_name: str, params: dict[str, ParameterValue]
    ) -> None:
        self.name = name
        self.type_name = type_name
        self.params = params


class SubcktData:
    __slots__ = ("ext_modules", "module")

    def __init__(self, module: Module, ext_modules: dict[str, ExternalModule]) -> None:
        self.module = module
        self.ext_modules = ext_modules


class IncludeData:
    __slots__ = ("path",)

    def __init__(self, path: str) -> None:
        self.path = path


class ParamData:
    __slots__ = ("params",)

    def __init__(self, params: dict[str, ParameterValue]) -> None:
        self.params = params


class SpectreTransformer(Transformer[Token, Circuit]):
    """Transform a Spectre parse tree into a Circuit model."""

    def __init__(self) -> None:
        super().__init__()
        self.all_subckts: dict[str, Module] = {}

    # ── Leaf transformers ───────────────────────────────────────────────

    def net_ref(self, items: list[Token]) -> str:
        return str(items[0])

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

    def port_decl(self, items: list[Token]) -> tuple[str, str]:
        return ("__port__", str(items[0]))

    # ── Instance statement ──────────────────────────────────────────────

    def instance_stmt(self, items: list[Any]) -> InstanceData | AnalysisData:
        inst_name = str(items[0])
        device_prefix = inst_name[0].upper()

        net_names: list[str] = []
        cell_name = ""
        params: dict[str, ParameterValue] = {}

        for item in items[1:]:
            if isinstance(item, Token):
                cell_name = str(item)
            elif isinstance(item, tuple):
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    params[pname] = pval
            elif isinstance(item, str):
                net_names.append(item)

        if cell_name in SPECTRE_ANALYSIS_TYPES:
            opts: dict[str, str] = {}
            for pname, pval in params.items():
                opts[pname] = _param_value_to_str(pval)
            return AnalysisData(
                kind=cell_name, name=inst_name, arguments=[], options=opts
            )

        return InstanceData(
            name=inst_name,
            net_names=net_names,
            cell_name=cell_name,
            params=params,
            device_prefix=device_prefix,
        )

    # ── model statement ─────────────────────────────────────────────────

    def model_stmt(self, items: list[Any]) -> ModelData:
        name = str(items[0])
        type_name = str(items[1])
        params: dict[str, ParameterValue] = {}
        for item in items[2:]:
            if isinstance(item, tuple):
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    params[pname] = pval
        return ModelData(name=name, type_name=type_name, params=params)

    # ── parameters statement ────────────────────────────────────────────

    def parameters_stmt(self, items: list[Any]) -> ParamData:
        params: dict[str, ParameterValue] = {}
        for item in items:
            if isinstance(item, tuple):
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    params[pname] = pval
        return ParamData(params=params)

    # ── include ─────────────────────────────────────────────────────────

    def include_stmt(self, items: list[Any]) -> IncludeData:
        path = str(items[0]).strip("\"'")
        return IncludeData(path=path)

    # ── save statement ───────────────────────────────────────────────────

    def save_stmt(self, items: list[Any]) -> OutputRequestData:
        variables = [str(item) for item in items if isinstance(item, str)]
        return OutputRequestData(kind="save", analysis_type="", variables=variables)

    # ── section (pass through body) ─────────────────────────────────────

    def section_body(self, items: list[Any]) -> list[Any]:
        return [i for i in items if i is not None]

    def section_def(self, items: list[Any]) -> list[Any]:
        # Return body items to be merged into parent
        for item in items:
            if isinstance(item, list):
                return item
        return []

    # ── Subcircuit ──────────────────────────────────────────────────────

    def subckt_body(self, items: list[Any]) -> list[Any]:
        return [i for i in items if i is not None]

    def subckt_def(self, items: list[Any]) -> SubcktData:
        subckt_name = str(items[0])

        port_names: list[str] = []
        subckt_params: dict[str, ParameterValue] = {}
        body_items: list[Any] = []

        for item in items[1:]:
            if isinstance(item, tuple) and len(item) == 2 and item[0] == "__port__":
                port_names.append(item[1])
            elif isinstance(item, tuple) and len(item) == 2 and item[0] != "__port__":
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    subckt_params[pname] = pval
            elif isinstance(item, list):
                body_items = item

        result = self.build_subckt(subckt_name, port_names, subckt_params, body_items)
        self.all_subckts[subckt_name] = result.module
        return result

    def build_subckt(
        self,
        name: str,
        port_names: list[str],
        subckt_params: dict[str, ParameterValue],
        body_items: list[Any],
    ) -> SubcktData:
        instances: list[InstanceData] = []
        nested_subckts: dict[str, Module] = {}
        ext_modules: dict[str, ExternalModule] = {}
        model_defs: dict[str, ModelData] = {}
        circuit_params: list[Parameter] = []
        directives: list[Directive] = []

        for item in body_items:
            if isinstance(item, InstanceData):
                instances.append(item)
            elif isinstance(item, SubcktData):
                nested_subckts[item.module.name] = item.module
                ext_modules.update(item.ext_modules)
            elif isinstance(item, ModelData):
                model_defs[item.name] = item
            elif isinstance(item, ParamData):
                for pname, pval in item.params.items():
                    circuit_params.append(Parameter(name=pname, default_value=pval))
            elif isinstance(item, IncludeData):
                directives.append(
                    Directive(kind=DirectiveKind.INCLUDE, value=item.path)
                )
            elif isinstance(item, list):
                for sub_item in item:
                    if isinstance(sub_item, InstanceData):
                        instances.append(sub_item)

        for pname, pval in subckt_params.items():
            circuit_params.append(Parameter(name=pname, default_value=pval))

        ports: list[Port] = [
            Port(
                uid=i,
                name=pn,
                direction=PortDirection.INOUT,
                domain=SignalDomain.ELECTRICAL,
            )
            for i, pn in enumerate(port_names)
        ]

        net_map: NetMap = {}
        module_references: list[ModuleReference] = []

        for port in ports:
            add_port_to_net(net_map, port.name, "", port.name)

        for inst in instances:
            device_prefix = inst.device_prefix
            port_template = DEVICE_PORT_TEMPLATES.get(device_prefix)

            # In Spectre, nets and cell name are already separated by grammar
            if device_prefix == "X" or port_template is None:
                # Subcircuit or unknown: resolve ports from definition
                subckt_mod = nested_subckts.get(inst.cell_name) or self.all_subckts.get(
                    inst.cell_name
                )
                if subckt_mod is not None:
                    inst_port_names = [p.name for p in subckt_mod.ports]
                else:
                    inst_port_names = [f"p{i}" for i in range(len(inst.net_names))]

                for net_name, port_name in zip(inst.net_names, inst_port_names):
                    add_port_to_net(net_map, net_name, inst.name, port_name)

                module_references.append(
                    ModuleReference(
                        name=inst.name,
                        module_name=inst.cell_name,
                        parameter_overrides={
                            pname: Parameter(name=pname, default_value=pval)
                            for pname, pval in inst.params.items()
                        },
                    )
                )
            else:
                # Known primitive device
                module_name = DEVICE_PREFIX_TO_MODULE.get(
                    device_prefix, device_prefix.lower()
                )

                for net_name, port_name in zip(inst.net_names, port_template):
                    add_port_to_net(net_map, net_name, inst.name, port_name)

                if module_name not in ext_modules:
                    ext_ports = [
                        Port(
                            uid=j,
                            name=pn,
                            direction=PortDirection.INOUT,
                            domain=SignalDomain.ELECTRICAL,
                        )
                        for j, pn in enumerate(port_template)
                    ]
                    ext_modules[module_name] = ExternalModule(
                        name=module_name,
                        domain="spectre",
                        ports=ext_ports,
                        kind=ExternalModuleKind.DEVICE,
                        properties={"spice_prefix": device_prefix},
                    )

                param_overrides: dict[str, Parameter] = {
                    pname: Parameter(name=pname, default_value=pval)
                    for pname, pval in inst.params.items()
                }

                model_name = ""
                if inst.cell_name and inst.cell_name != module_name:
                    model_name = inst.cell_name

                module_references.append(
                    ModuleReference(
                        name=inst.name,
                        module_name=module_name,
                        parameter_overrides=param_overrides,
                        model_name=model_name,
                    )
                )

        for mdata in model_defs.values():
            if mdata.name not in ext_modules:
                ext_modules[mdata.name] = ExternalModule(
                    name=mdata.name,
                    domain="spectre",
                    parameters=[
                        Parameter(name=pn, default_value=pv)
                        for pn, pv in mdata.params.items()
                    ],
                    kind=ExternalModuleKind.MODEL,
                    properties={"model_type": mdata.type_name},
                )

        connections = net_map_to_connections(net_map)

        module = Module(
            name=name,
            ports=ports,
            parameters=circuit_params,
            module_references=module_references,
            connections=connections,
            directives=directives,
        )
        return SubcktData(module=module, ext_modules=ext_modules)

    # ── Top-level ───────────────────────────────────────────────────────

    def start(self, items: list[Any]) -> Circuit:
        subckt_datas: list[SubcktData] = []
        model_defs: dict[str, ModelData] = {}
        top_instances: list[InstanceData] = []
        directives: list[Directive] = []
        analyses: list[AnalysisData] = []
        output_requests: list[OutputRequestData] = []

        for item in items:
            if item is None:
                continue
            if isinstance(item, SubcktData):
                subckt_datas.append(item)
            elif isinstance(item, ModelData):
                model_defs[item.name] = item
            elif isinstance(item, InstanceData):
                top_instances.append(item)
            elif isinstance(item, AnalysisData):
                analyses.append(item)
            elif isinstance(item, OutputRequestData):
                output_requests.append(item)
            elif isinstance(item, IncludeData):
                directives.append(
                    Directive(kind=DirectiveKind.INCLUDE, value=item.path)
                )
            elif isinstance(item, ParamData):
                for pname, pval in item.params.items():
                    val = _param_value_to_str(pval)
                    directives.append(
                        Directive(kind=DirectiveKind.PARAM, name=pname, value=val)
                    )
            elif isinstance(item, list):
                for sub_item in item:
                    if isinstance(sub_item, SubcktData):
                        subckt_datas.append(sub_item)
                    elif isinstance(sub_item, AnalysisData):
                        analyses.append(sub_item)
                    elif isinstance(sub_item, OutputRequestData):
                        output_requests.append(sub_item)

        modules: list[Module] = []
        all_ext_modules: dict[str, ExternalModule] = {}

        for sd in subckt_datas:
            modules.append(sd.module)
            all_ext_modules.update(sd.ext_modules)

        if top_instances:
            top_data = self.build_subckt("__top__", [], {}, top_instances)
            modules.insert(0, top_data.module)
            all_ext_modules.update(top_data.ext_modules)

        for mdata in model_defs.values():
            if mdata.name not in all_ext_modules:
                all_ext_modules[mdata.name] = ExternalModule(
                    name=mdata.name,
                    domain="spectre",
                    parameters=[
                        Parameter(name=pn, default_value=pv)
                        for pn, pv in mdata.params.items()
                    ],
                    kind=ExternalModuleKind.MODEL,
                    properties={"model_type": mdata.type_name},
                )

        top_module = modules[-1].name if modules else ""

        simulation: Simulation | None = None
        if analyses or output_requests:
            simulation = Simulation(
                analyses=[
                    Analysis(
                        kind=ANALYSIS_KIND_MAP.get(a.kind),
                        name=a.name,
                        arguments=a.arguments,
                        options=a.options,
                    )
                    for a in analyses
                ],
                output_requests=[
                    OutputRequest(
                        kind=OUTPUT_REQUEST_KIND_MAP.get(o.kind),
                        analysis_type=o.analysis_type,
                        variables=o.variables,
                    )
                    for o in output_requests
                ],
            )

        return Circuit(
            name="",
            domain="spectre",
            top_module=top_module,
            modules=modules,
            ext_modules=list(all_ext_modules.values()),
            directives=directives,
            simulation=simulation,
        )
