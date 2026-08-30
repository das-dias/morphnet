from __future__ import annotations

from typing import Any

from lark import Token, Transformer

from hubnet.hubnet_schema import (
    Analysis,
    Circuit,
    Connection,
    Directive,
    DirectiveKind,
    ExternalModule,
    ExternalModuleKind,
    InitialCondition,
    Measurement,
    Module,
    ModuleReference,
    OutputRequest,
    Parameter,
    ParameterValue,
    Port,
    PortDirection,
    PrefixedValue,
    SignalDomain,
    Simulation,
)
from hubnet.netlist.net_utils import NetMap, add_port_to_net, net_map_to_connections
from hubnet.netlist.simulation_data import (
    ANALYSIS_KIND_MAP,
    OUTPUT_REQUEST_KIND_MAP,
    AnalysisData,
    InitialConditionData,
    MeasurementData,
    OutputRequestData,
    TemperatureData,
)
from hubnet.netlist.value_utils import (
    DEVICE_PORT_TEMPLATES,
    DEVICE_PREFIX_TO_MODULE,
    is_si_number,
    parse_parameter_number,
    parse_si_number,
)


def _param_value_to_str(pval: ParameterValue) -> str:
    """Convert a ParameterValue to a plain string for directive storage."""
    if pval.prefixed_value is not None:
        from hubnet.netlist.value_utils import format_si_value

        return format_si_value(pval.prefixed_value)
    if pval.int_value is not None:
        return str(pval.int_value)
    if pval.expression is not None:
        return pval.expression
    if pval.string_value is not None:
        return pval.string_value
    return ""


class InstanceData:
    """Intermediate representation of a parsed device/subcircuit instance."""

    __slots__ = (
        "device_prefix",
        "model_or_subckt",
        "name",
        "net_names",
        "params",
        "value",
    )

    def __init__(
        self,
        name: str,
        net_names: list[str],
        model_or_subckt: str,
        value: PrefixedValue | None,
        params: dict[str, ParameterValue],
        device_prefix: str,
    ) -> None:
        self.name = name
        self.net_names = net_names
        self.model_or_subckt = model_or_subckt
        self.value = value
        self.params = params
        self.device_prefix = device_prefix


class ModelData:
    """Intermediate representation of a .model statement."""

    __slots__ = ("name", "params", "type_name")

    def __init__(
        self,
        name: str,
        type_name: str,
        params: dict[str, ParameterValue],
    ) -> None:
        self.name = name
        self.type_name = type_name
        self.params = params


class SubcktData:
    """Intermediate representation of a fully parsed subcircuit."""

    __slots__ = ("ext_modules", "module")

    def __init__(
        self,
        module: Module,
        ext_modules: dict[str, ExternalModule],
    ) -> None:
        self.module = module
        self.ext_modules = ext_modules


class IncludeData:
    """Intermediate representation of a .include directive."""

    __slots__ = ("path",)

    def __init__(self, path: str) -> None:
        self.path = path


class LibData:
    """Intermediate representation of a .lib directive."""

    __slots__ = ("path", "section")

    def __init__(self, path: str, section: str) -> None:
        self.path = path
        self.section = section


class GlobalData:
    """Intermediate representation of a .global directive."""

    __slots__ = ("nets",)

    def __init__(self, nets: list[str]) -> None:
        self.nets = nets


class OptionData:
    """Intermediate representation of a .option directive."""

    __slots__ = ("options",)

    def __init__(self, options: dict[str, str]) -> None:
        self.options = options


class ParamData:
    """Intermediate representation of a .param directive."""

    __slots__ = ("params",)

    def __init__(self, params: dict[str, ParameterValue]) -> None:
        self.params = params


class SpiceTransformer(Transformer[Token, Circuit]):
    """Transform a SPICE parse tree into a Circuit model.

    Architecture:
    - Bottom-up: subcircuit bodies resolve before enclosing scope.
    - Dict-based lookups everywhere for O(n) overall complexity.
    - Per-subcircuit NetMap built in single pass over instances.
    - Stateful: _all_subckts accumulates all resolved subcircuit Modules
      so later subcircuits can resolve X-instance port names from earlier ones.
    """

    def __init__(self) -> None:
        super().__init__()
        self.all_subckts: dict[str, Module] = {}

    # ── Leaf transformers ───────────────────────────────────────────────

    def token_number(self, items: list[Token]) -> Token:
        return items[0]

    def token_ident(self, items: list[Token]) -> Token:
        return items[0]

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

    # ── Instance statement ──────────────────────────────────────────────

    def instance_stmt(self, items: list[Any]) -> InstanceData:
        inst_name = str(items[0])
        device_prefix = inst_name[0].upper()

        tokens: list[Token] = []
        params: dict[str, ParameterValue] = {}
        for item in items[1:]:
            if isinstance(item, tuple):
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    params[pname] = pval
                else:
                    params[pname] = ParameterValue(string_value=str(pval))
            elif isinstance(item, Token):
                tokens.append(item)

        port_template = DEVICE_PORT_TEMPLATES.get(device_prefix)

        if device_prefix == "X":
            # Subcircuit instance: last token is subcircuit name, rest are nets
            model_or_subckt = str(tokens[-1]) if tokens else ""
            net_names = [str(t) for t in tokens[:-1]]
            return InstanceData(
                name=inst_name,
                net_names=net_names,
                model_or_subckt=model_or_subckt,
                value=None,
                params=params,
                device_prefix=device_prefix,
            )

        if port_template is not None:
            n_ports = len(port_template)
            token_strs = [str(t) for t in tokens]

            # Devices like R, C, L: after ports, next token is value or model name
            net_names = token_strs[:n_ports]
            remaining = token_strs[n_ports:]

            value: PrefixedValue | None = None
            model_name = ""
            for tok in remaining:
                if is_si_number(tok):
                    value = parse_si_number(tok)
                else:
                    model_name = tok

            return InstanceData(
                name=inst_name,
                net_names=net_names,
                model_or_subckt=model_name,
                value=value,
                params=params,
                device_prefix=device_prefix,
            )

        # Unknown device prefix — treat like subcircuit instance
        model_or_subckt = str(tokens[-1]) if tokens else ""
        net_names = [str(t) for t in tokens[:-1]]
        return InstanceData(
            name=inst_name,
            net_names=net_names,
            model_or_subckt=model_or_subckt,
            value=None,
            params=params,
            device_prefix=device_prefix,
        )

    # ── .model ──────────────────────────────────────────────────────────

    def model_stmt(self, items: list[Any]) -> ModelData:
        # items[0] = MODEL_KW, items[1] = model name, items[2] = type, rest = params
        name = str(items[1])
        type_name = str(items[2])
        params: dict[str, ParameterValue] = {}
        for item in items[3:]:
            if isinstance(item, tuple):
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    params[pname] = pval
        return ModelData(name=name, type_name=type_name, params=params)

    # ── .param ──────────────────────────────────────────────────────────

    def param_stmt(self, items: list[Any]) -> ParamData:
        params: dict[str, ParameterValue] = {}
        for item in items:
            if isinstance(item, tuple):
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    params[pname] = pval
        return ParamData(params=params)

    # ── .include / .lib ─────────────────────────────────────────────────

    def include_stmt(self, items: list[Any]) -> IncludeData:
        path = str(items[1]).strip("\"'")
        return IncludeData(path=path)

    def lib_stmt(self, items: list[Any]) -> LibData:
        path = str(items[1]).strip("\"'")
        section = (
            str(items[2]) if len(items) > 2 and not isinstance(items[2], Token) else ""
        )
        if len(items) > 2 and isinstance(items[2], Token):
            section = str(items[2])
        return LibData(path=path, section=section)

    # ── .global ─────────────────────────────────────────────────────────

    def global_stmt(self, items: list[Any]) -> GlobalData:
        nets = [
            str(t) for t in items if isinstance(t, Token) and not str(t).startswith(".")
        ]
        return GlobalData(nets=nets)

    # ── .option ─────────────────────────────────────────────────────────

    def option_stmt(self, items: list[Any]) -> OptionData:
        options: dict[str, str] = {}
        for item in items:
            if isinstance(item, tuple):
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    options[pname] = _param_value_to_str(pval)
                else:
                    options[pname] = str(pval)
        return OptionData(options=options)

    # ── .end ────────────────────────────────────────────────────────────

    def end_stmt(self, items: list[Any]) -> None:
        return None

    # ── Simulation: analysis statements ─────────────────────────────────

    def _extract_sim_args(
        self, items: list[Any]
    ) -> tuple[list[str], dict[str, str]]:
        args: list[str] = []
        opts: dict[str, str] = {}
        for item in items:
            if isinstance(item, tuple):
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    opts[pname] = _param_value_to_str(pval)
                else:
                    opts[pname] = str(pval)
            elif isinstance(item, Token):
                val = str(item)
                if not val.startswith("."):
                    args.append(val)
        return args, opts

    def token_output_var(self, items: list[Token]) -> Token:
        return items[0]

    def op_stmt(self, items: list[Any]) -> AnalysisData:
        return AnalysisData(kind="op", arguments=[], options={})

    def tran_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="tran", arguments=args, options=opts)

    def ac_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="ac", arguments=args, options=opts)

    def dc_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="dc", arguments=args, options=opts)

    def noise_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="noise", arguments=args, options=opts)

    def tf_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="tf", arguments=args, options=opts)

    def sens_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="sens", arguments=args, options=opts)

    def pz_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="pz", arguments=args, options=opts)

    def disto_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="disto", arguments=args, options=opts)

    def four_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="four", arguments=args, options=opts)

    # ── Simulation: output requests ─────────────────────────────────────

    def print_stmt(self, items: list[Any]) -> OutputRequestData:
        tokens = [str(t) for t in items if isinstance(t, Token) and not str(t).startswith(".")]
        analysis_type = tokens[0] if tokens else ""
        variables = tokens[1:]
        return OutputRequestData(
            kind="print", analysis_type=analysis_type, variables=variables
        )

    def plot_stmt(self, items: list[Any]) -> OutputRequestData:
        tokens = [str(t) for t in items if isinstance(t, Token) and not str(t).startswith(".")]
        analysis_type = tokens[0] if tokens else ""
        variables = tokens[1:]
        return OutputRequestData(
            kind="plot", analysis_type=analysis_type, variables=variables
        )

    def probe_stmt(self, items: list[Any]) -> OutputRequestData:
        tokens = [str(t) for t in items if isinstance(t, Token) and not str(t).startswith(".")]
        analysis_type = tokens[0] if tokens else ""
        variables = tokens[1:]
        return OutputRequestData(
            kind="probe", analysis_type=analysis_type, variables=variables
        )

    # ── Simulation: measurements ────────────────────────────────────────

    def meas_stmt(self, items: list[Any]) -> MeasurementData:
        tokens = [str(t) for t in items if isinstance(t, Token) and not str(t).startswith(".")]
        opts: list[str] = []
        for item in items:
            if isinstance(item, tuple):
                pname, pval = item
                if isinstance(pval, ParameterValue):
                    opts.append(f"{pname}={_param_value_to_str(pval)}")
                else:
                    opts.append(f"{pname}={pval}")
        analysis_type = tokens[0] if tokens else ""
        name = tokens[1] if len(tokens) > 1 else ""
        body_parts = tokens[2:] + opts
        return MeasurementData(
            name=name,
            analysis_type=analysis_type,
            body=" ".join(body_parts),
        )

    # ── Simulation: initial conditions ──────────────────────────────────

    def ic_assign(self, items: list[Any]) -> tuple[str, str]:
        var_name = str(items[0])
        value = items[1]
        if isinstance(value, ParameterValue):
            return (var_name, _param_value_to_str(value))
        return (var_name, str(value))

    def ic_stmt(self, items: list[Any]) -> InitialConditionData:
        conditions = {k: v for item in items if isinstance(item, tuple) for k, v in [item]}
        return InitialConditionData(kind="ic", conditions=conditions)

    def nodeset_stmt(self, items: list[Any]) -> InitialConditionData:
        conditions = {k: v for item in items if isinstance(item, tuple) for k, v in [item]}
        return InitialConditionData(kind="nodeset", conditions=conditions)

    # ── Simulation: temperature ─────────────────────────────────────────

    def temp_stmt(self, items: list[Any]) -> TemperatureData:
        temps: list[float] = []
        for item in items:
            if isinstance(item, Token):
                val = str(item)
                if val.startswith("."):
                    continue
                try:
                    temps.append(float(val))
                except ValueError:
                    pass
        return TemperatureData(temperatures=temps)

    # ── Subcircuit body & definition ────────────────────────────────────

    def subckt_body(self, items: list[Any]) -> list[Any]:
        return [i for i in items if i is not None]

    def port_decl(self, items: list[Token]) -> tuple[str, str]:
        """Tag port declarations so they are distinguishable from raw tokens."""
        return ("__port__", str(items[0]))

    def subckt_def(self, items: list[Any]) -> SubcktData:
        # After transform, items are:
        #   Token(SUBCKT_KW), Token(IDENT=name),
        #   ("__port__", name)*, (param_name, param_val)*,
        #   body_list,
        #   Token(ENDS_KW), Token(IDENT=end_name)?
        subckt_name = str(items[1])

        port_names: list[str] = []
        subckt_params: dict[str, ParameterValue] = {}
        body_items: list[Any] = []

        for item in items[2:]:
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
        """Assemble a Module from parsed subcircuit contents.

        O(n) overall: single pass over body items to collect instances,
        single pass to build NetMap, single pass to generate Connections.
        """
        instances: list[InstanceData] = []
        nested_subckts: dict[str, Module] = {}
        ext_modules: dict[str, ExternalModule] = {}
        model_defs: dict[str, ModelData] = {}
        circuit_params: list[Parameter] = []
        directives: list[Directive] = []

        # Single pass: classify body items by type — O(n)
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
            elif isinstance(item, GlobalData):
                directives.append(
                    Directive(kind=DirectiveKind.GLOBAL, value=" ".join(item.nets))
                )
            elif isinstance(item, OptionData):
                for k, v in item.options.items():
                    directives.append(
                        Directive(kind=DirectiveKind.OPTION, name=k, value=v)
                    )

        # Add subckt-level params
        for pname, pval in subckt_params.items():
            circuit_params.append(Parameter(name=pname, default_value=pval))

        # Build ports — O(p)
        ports: list[Port] = []
        for i, pname in enumerate(port_names):
            ports.append(
                Port(
                    uid=i,
                    name=pname,
                    direction=PortDirection.INOUT,
                    domain=SignalDomain.ELECTRICAL,
                )
            )

        # Build module_references and NetMap from instances — O(n * avg_ports)
        net_map: NetMap = {}
        module_references: list[ModuleReference] = []

        # Register module's own ports on their nets (port name = net name)
        for port in ports:
            add_port_to_net(net_map, port.name, "", port.name)

        for inst in instances:
            device_prefix = inst.device_prefix
            port_template = DEVICE_PORT_TEMPLATES.get(device_prefix)

            if device_prefix == "X":
                # Subcircuit instance: resolve port names from local or global registry
                subckt_mod = nested_subckts.get(
                    inst.model_or_subckt
                ) or self.all_subckts.get(inst.model_or_subckt)
                if subckt_mod is not None:
                    inst_port_names = [p.name for p in subckt_mod.ports]
                else:
                    inst_port_names = [f"p{i}" for i in range(len(inst.net_names))]

                for net_name, port_name in zip(inst.net_names, inst_port_names):
                    add_port_to_net(net_map, net_name, inst.name, port_name)

                param_overrides: dict[str, Parameter] = {
                    pname: Parameter(name=pname, default_value=pval)
                    for pname, pval in inst.params.items()
                }

                module_references.append(
                    ModuleReference(
                        name=inst.name,
                        module_name=inst.model_or_subckt,
                        parameter_overrides=param_overrides,
                    )
                )
            elif port_template is not None:
                # Primitive device instance
                module_name = DEVICE_PREFIX_TO_MODULE.get(
                    device_prefix, device_prefix.lower()
                )

                for net_name, port_name in zip(inst.net_names, port_template):
                    add_port_to_net(net_map, net_name, inst.name, port_name)

                # Build ExternalModule if not yet seen — O(1) amortized
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
                        domain="spice",
                        ports=ext_ports,
                        kind=ExternalModuleKind.DEVICE,
                        properties={"spice_prefix": device_prefix},
                    )

                param_overrides: dict[str, Parameter] = {}
                if inst.value is not None:
                    param_overrides["value"] = Parameter(
                        name="value",
                        default_value=ParameterValue(prefixed_value=inst.value),
                    )
                for pname, pval in inst.params.items():
                    param_overrides[pname] = Parameter(
                        name=pname, default_value=pval
                    )

                module_references.append(
                    ModuleReference(
                        name=inst.name,
                        module_name=module_name,
                        parameter_overrides=param_overrides,
                        model_name=inst.model_or_subckt,
                    )
                )
            else:
                # Unknown prefix — treat as subcircuit
                for i, net_name in enumerate(inst.net_names):
                    add_port_to_net(net_map, net_name, inst.name, f"p{i}")
                module_references.append(
                    ModuleReference(
                        name=inst.name,
                        module_name=inst.model_or_subckt,
                        parameter_overrides={
                            pname: Parameter(name=pname, default_value=pval)
                            for pname, pval in inst.params.items()
                        },
                    )
                )

        # Convert model definitions to ExternalModules
        for mdata in model_defs.values():
            if mdata.name not in ext_modules:
                ext_params = [
                    Parameter(name=pn, default_value=pv)
                    for pn, pv in mdata.params.items()
                ]
                ext_modules[mdata.name] = ExternalModule(
                    name=mdata.name,
                    domain="spice",
                    parameters=ext_params,
                    kind=ExternalModuleKind.MODEL,
                    properties={"model_type": mdata.type_name},
                )

        # Convert NetMap to Connections — O(n)
        connections: list[Connection] = net_map_to_connections(net_map)

        module = Module(
            name=name,
            ports=ports,
            parameters=circuit_params,
            module_references=module_references,
            connections=connections,
            directives=directives,
        )

        return SubcktData(module=module, ext_modules=ext_modules)

    # ── Top-level: start ────────────────────────────────────────────────

    def start(self, items: list[Any]) -> Circuit:
        subckt_datas: list[SubcktData] = []
        model_defs: dict[str, ModelData] = {}
        top_instances: list[InstanceData] = []
        circuit_params: list[Parameter] = []
        directives: list[Directive] = []
        analyses: list[AnalysisData] = []
        output_requests: list[OutputRequestData] = []
        measurements: list[MeasurementData] = []
        ic_data: InitialConditionData | None = None
        nodeset_data: InitialConditionData | None = None
        temperatures: list[float] = []

        # Single pass over top-level items — O(n)
        for item in items:
            if item is None:
                continue
            if isinstance(item, SubcktData):
                subckt_datas.append(item)
            elif isinstance(item, ModelData):
                model_defs[item.name] = item
            elif isinstance(item, InstanceData):
                top_instances.append(item)
            elif isinstance(item, ParamData):
                for pname, pval in item.params.items():
                    circuit_params.append(Parameter(name=pname, default_value=pval))
            elif isinstance(item, IncludeData):
                directives.append(
                    Directive(kind=DirectiveKind.INCLUDE, value=item.path)
                )
            elif isinstance(item, LibData):
                val = item.path
                if item.section:
                    val += f" {item.section}"
                directives.append(Directive(kind=DirectiveKind.LIB, value=val))
            elif isinstance(item, GlobalData):
                directives.append(
                    Directive(kind=DirectiveKind.GLOBAL, value=" ".join(item.nets))
                )
            elif isinstance(item, OptionData):
                for k, v in item.options.items():
                    directives.append(
                        Directive(kind=DirectiveKind.OPTION, name=k, value=v)
                    )
            elif isinstance(item, AnalysisData):
                analyses.append(item)
            elif isinstance(item, OutputRequestData):
                output_requests.append(item)
            elif isinstance(item, MeasurementData):
                measurements.append(item)
            elif isinstance(item, InitialConditionData):
                if item.kind == "ic":
                    if ic_data is None:
                        ic_data = item
                    else:
                        ic_data.conditions.update(item.conditions)
                else:
                    if nodeset_data is None:
                        nodeset_data = item
                    else:
                        nodeset_data.conditions.update(item.conditions)
            elif isinstance(item, TemperatureData):
                temperatures.extend(item.temperatures)

        # Collect all modules and ext_modules from subcircuit definitions
        modules: list[Module] = []
        all_ext_modules: dict[str, ExternalModule] = {}
        subckt_by_name: dict[str, Module] = {}

        for sd in subckt_datas:
            modules.append(sd.module)
            subckt_by_name[sd.module.name] = sd.module
            all_ext_modules.update(sd.ext_modules)

        # If there are top-level instances, create a synthetic top module
        if top_instances:
            top_data = self.build_subckt(
                name="__top__",
                port_names=[],
                subckt_params={},
                body_items=top_instances,
            )
            modules.insert(0, top_data.module)
            all_ext_modules.update(top_data.ext_modules)

        # Convert model definitions to ExternalModules
        for mdata in model_defs.values():
            if mdata.name not in all_ext_modules:
                ext_params = [
                    Parameter(name=pn, default_value=pv)
                    for pn, pv in mdata.params.items()
                ]
                all_ext_modules[mdata.name] = ExternalModule(
                    name=mdata.name,
                    domain="spice",
                    parameters=ext_params,
                    properties={"model_type": mdata.type_name},
                )

        # Determine top module: last defined subcircuit is conventionally the top
        top_module = ""
        if modules:
            top_module = modules[-1].name

        for p in circuit_params:
            val = _param_value_to_str(p.default_value) if p.default_value else ""
            directives.append(
                Directive(kind=DirectiveKind.PARAM, name=p.name, value=val)
            )

        # Build Simulation object if any simulation data was found
        simulation: Simulation | None = None
        if analyses or output_requests or measurements or ic_data or nodeset_data or temperatures:
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
                measurements=[
                    Measurement(
                        name=m.name,
                        analysis_type=m.analysis_type,
                        body=m.body,
                    )
                    for m in measurements
                ],
                initial_conditions=(
                    InitialCondition(conditions=ic_data.conditions)
                    if ic_data
                    else None
                ),
                node_sets=(
                    InitialCondition(conditions=nodeset_data.conditions)
                    if nodeset_data
                    else None
                ),
                temperatures=temperatures,
            )

        return Circuit(
            name="",
            domain="spice",
            top_module=top_module,
            modules=modules,
            ext_modules=list(all_ext_modules.values()),
            directives=directives,
            simulation=simulation,
        )
