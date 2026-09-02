# API Reference

## morphnet.netlist — Parse and Write Functions

All functions are importable directly from `morphnet.netlist`:

```python
from morphnet.netlist import parse_spectre, write_spectre
```

Or from their format-specific modules:

```python
from morphnet.netlist.spectre.parser import parse_spectre
from morphnet.netlist.spectre.writer import write_spectre
```

### HSPICE

#### `parse_hspice(text: str) -> Circuit`

Parse HSPICE netlist text. Handles `.subckt`/`.ends`, `.macro`/`.eom`, device instances, `.model` statements, simulation directives (`.tran`, `.ac`, `.dc`, `.op`, `.fft`, etc.), `.include`, `.lib`, `.param`.

#### `write_hspice(circuit: Circuit) -> str`

Write a `Circuit` to HSPICE format.

### SPICE

#### `parse_spice(text: str) -> Circuit`

Parse generic SPICE netlist text. Supports the common SPICE3 subset shared across simulators.

#### `write_spice(circuit: Circuit) -> str`

Write a `Circuit` to generic SPICE format.

### Xyce

#### `parse_xyce(text: str) -> Circuit`

Parse Xyce netlist text. Supports Xyce-specific syntax extensions.

#### `write_xyce(circuit: Circuit) -> str`

Write a `Circuit` to Xyce format.

### Spectre

#### `parse_spectre(text: str) -> Circuit`

Parse Spectre netlist text. Handles `subckt`/`ends`, instances with `(port list) module_name param=value` syntax, model statements, and simulation analyses.

#### `write_spectre(circuit: Circuit) -> str`

Write a `Circuit` to Spectre format.

### Spectre-SPICE

#### `parse_spectre_spice(text: str) -> Circuit`

Parse Spectre-SPICE mixed-mode netlists. Handles both Spectre and SPICE syntax blocks.

#### `write_spectre_spice(circuit: Circuit) -> str`

Write a `Circuit` to Spectre-SPICE format (SPICE-style output).

### Verilog-AMS

#### `parse_vams(text: str) -> Circuit`

Parse Verilog-AMS netlist text. Handles `module`/`endmodule`, named port connections (`.port(net)`), parameter overrides (`#(.param(value))`), natures, and disciplines.

#### `write_vams(circuit: Circuit) -> str`

Write a `Circuit` to Verilog-AMS format.

---

## morphnet.morphnet_schema — Data Models

All models are importable from `morphnet.morphnet_schema`:

```python
from morphnet.morphnet_schema import Circuit, Module, Port, SIPrefix
```

### Base Class

#### `ProtoModel`

Base class for all MorphNet data models. Extends `pydantic.BaseModel` with `frozen=True` (immutable) and protobuf serialization.

**Methods:**

| Method | Description |
|---|---|
| `to_proto() -> ProtoMessage` | Convert to a protobuf Message |
| `to_proto_bytes() -> bytes` | Serialize to binary protobuf |
| `from_proto_bytes(data: bytes) -> Self` | Deserialize from binary protobuf (classmethod) |
| `from_proto(msg: ProtoMessage) -> Self` | Convert from a protobuf Message (classmethod) |
| `to_json(**kwargs) -> str` | Serialize to JSON string |
| `from_json(json_str: str) -> Self` | Deserialize from JSON string (classmethod) |
| `to_yaml(**kwargs) -> str` | Serialize to YAML string |
| `from_yaml(yaml_str: str) -> Self` | Deserialize from YAML string (classmethod) |
| `model_copy(update={...})` | Create a modified copy (inherited from Pydantic) |

### Core Models

#### `Circuit`

Top-level container for a parsed netlist.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Circuit name |
| `domain` | `str` | Source format (e.g., `"spectre"`, `"hspice"`) |
| `top_module` | `str` | Name of the top-level module |
| `modules` | `list[Module]` | Subcircuit/module definitions |
| `ext_modules` | `list[ExternalModule]` | Primitive device declarations |
| `properties` | `dict[str, str]` | Arbitrary key-value properties |
| `directives` | `list[Directive]` | Include, lib, param directives |
| `simulation` | `Simulation \| None` | Simulation configuration |

#### `Module`

A subcircuit or module definition.

| Field | Type | Description |
|---|---|---|
| `uid` | `int` | Unique identifier |
| `name` | `str` | Module name |
| `class_name` | `str` | Class/type name |
| `ports` | `list[Port]` | Port declarations |
| `parameters` | `list[Parameter]` | Parameter declarations |
| `model_interfaces` | `list[ModelInterface]` | Model function definitions |
| `module_references` | `list[ModuleReference]` | Instances of other modules |
| `connections` | `list[Connection]` | Point-to-point connections |
| `buses` | `list[Bus]` | Bus definitions |
| `properties` | `dict[str, str]` | Arbitrary properties |
| `directives` | `list[Directive]` | Module-level directives |

#### `ExternalModule`

A primitive or externally-defined device (resistor, mosfet, etc.).

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Device name |
| `domain` | `str` | Signal domain |
| `ports` | `list[Port]` | Port declarations |
| `parameters` | `list[Parameter]` | Parameter declarations |
| `properties` | `dict[str, str]` | Arbitrary properties |
| `kind` | `ExternalModuleKind` | Device kind (DEVICE, MODEL, etc.) |

#### `ModuleReference`

An instance of a module or device within a parent module.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Instance name |
| `module_name` | `str` | Referenced module name |
| `class_name` | `str` | Class/type name |
| `parameters` | `list[Parameter]` | Formal parameters |
| `parameter_overrides` | `dict[str, Parameter]` | Overridden parameter values |
| `properties` | `dict[str, str]` | Arbitrary properties |
| `model_name` | `str` | Model name (for model-based instances) |

#### `Connection`

A point-to-point connection between two port references on a net.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Net name |
| `source` | `PortReference \| None` | Source port reference |
| `target` | `PortReference \| None` | Target port reference |
| `domain` | `SignalDomain` | Signal domain |
| `weight` | `int` | Connection weight |
| `properties` | `dict[str, str]` | Arbitrary properties |

### Port Models

#### `Port`

| Field | Type | Description |
|---|---|---|
| `uid` | `int` | Unique identifier |
| `name` | `str` | Port name |
| `direction` | `PortDirection` | INOUT, INPUT, or OUTPUT |
| `domain` | `SignalDomain` | Signal domain |
| `width` | `int` | Bus width |
| `cross_section` | `str` | Cross section type |
| `properties` | `dict[str, str]` | Arbitrary properties |
| `discipline` | `str` | Verilog-AMS discipline |

#### `PortReference`

A reference to a specific port on a specific instance.

| Field | Type | Description |
|---|---|---|
| `instance_name` | `str` | Name of the instance |
| `port_name` | `str` | Name of the port |

#### `Bus`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Bus name |
| `width` | `int` | Bus width |
| `domain` | `SignalDomain` | Signal domain |
| `connections` | `list[Connection]` | Bus connections |
| `properties` | `dict[str, str]` | Arbitrary properties |

### Parameter Models

#### `Parameter`

| Field | Type | Description |
|---|---|---|
| `uid` | `int` | Unique identifier |
| `name` | `str` | Parameter name |
| `default_value` | `ParameterValue \| None` | Default value |
| `description` | `str` | Description |
| `properties` | `dict[str, str]` | Arbitrary properties |

#### `ParameterValue`

A oneof value — exactly one field should be set:

| Field | Type | Description |
|---|---|---|
| `prefixed_value` | `PrefixedValue \| None` | SI-prefixed numeric value |
| `model_ref` | `ModelReference \| None` | Reference to a model |
| `string_value` | `str \| None` | String value |
| `expression` | `str \| None` | Expression string |
| `int_value` | `int \| None` | Integer value |

#### `PrefixedValue`

| Field | Type | Description |
|---|---|---|
| `double_value` | `float` | Numeric value |
| `prefix` | `SIPrefix` | SI prefix (KILO, MEGA, PICO, etc.) |

#### `ModelReference`

| Field | Type | Description |
|---|---|---|
| `model_interface_name` | `str` | Model interface name |
| `arguments` | `dict[str, ParameterValue]` | Model arguments |

#### `ModelInterface`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Interface name |
| `function_name` | `str` | Function name |
| `parameters` | `list[Parameter]` | Parameters |
| `properties` | `dict[str, str]` | Arbitrary properties |

### Directive Models

#### `Directive`

| Field | Type | Description |
|---|---|---|
| `kind` | `DirectiveKind` | Directive type |
| `name` | `str` | Directive name/key |
| `value` | `str` | Directive value |

### Simulation Models

#### `Simulation`

| Field | Type | Description |
|---|---|---|
| `analyses` | `list[Analysis]` | Simulation analyses |
| `output_requests` | `list[OutputRequest]` | Print/plot/probe/save requests |
| `measurements` | `list[Measurement]` | .meas statements |
| `initial_conditions` | `InitialCondition \| None` | Initial conditions |
| `node_sets` | `InitialCondition \| None` | Node sets |
| `temperatures` | `list[float]` | Temperature list |
| `options` | `dict[str, str]` | Simulation options |

#### `Analysis`

| Field | Type | Description |
|---|---|---|
| `kind` | `AnalysisKind` | Analysis type (OP, DC, AC, TRAN, etc.) |
| `name` | `str` | Analysis name |
| `arguments` | `list[str]` | Positional arguments |
| `options` | `dict[str, str]` | Named options |

#### `OutputRequest`

| Field | Type | Description |
|---|---|---|
| `kind` | `OutputRequestKind` | PRINT, PLOT, PROBE, or SAVE |
| `analysis_type` | `str` | Associated analysis type |
| `variables` | `list[str]` | Variable expressions |

#### `Measurement`

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Measurement name |
| `analysis_type` | `str` | Associated analysis type |
| `body` | `str` | Measurement body |

#### `InitialCondition`

| Field | Type | Description |
|---|---|---|
| `conditions` | `dict[str, str]` | Node/value pairs |

### Enums

#### `PortDirection`

`INOUT` (0), `INPUT` (1), `OUTPUT` (2)

#### `SignalDomain`

`UNSPECIFIED` (0), `ELECTRICAL` (1), `WAVEGUIDE` (2)

#### `SIPrefix`

`UNSPECIFIED` (0), `QUECTO` (1), `RONTO` (2), `YOCTO` (3), `ZEPTO` (4), `ATTO` (5), `FEMTO` (6), `PICO` (7), `NANO` (8), `MICRO` (9), `MILLI` (10), `CENTI` (11), `DECI` (12), `DECA` (13), `HECTO` (14), `KILO` (15), `MEGA` (16), `GIGA` (17), `TERA` (18), `PETA` (19), `EXA` (20), `ZETTA` (21), `YOTTA` (22), `RONNA` (23), `QUETTA` (24)

#### `ExternalModuleKind`

`UNSPECIFIED` (0), `DEVICE` (1), `MODEL` (2), `NATURE` (3), `DISCIPLINE` (4)

#### `DirectiveKind`

`UNSPECIFIED` (0), `INCLUDE` (1), `LIB` (2), `GLOBAL` (3), `OPTION` (4), `PARAM` (5), `DEFINE` (6), `TIMESCALE` (7)

#### `AnalysisKind`

`UNSPECIFIED` (0), `OP` (1), `DC` (2), `AC` (3), `TRAN` (4), `NOISE` (5), `TF` (6), `SENS` (7), `PZ` (8), `DISTO` (9), `FOUR` (10), `FFT` (11)

#### `OutputRequestKind`

`UNSPECIFIED` (0), `PRINT` (1), `PLOT` (2), `PROBE` (3), `SAVE` (4)

---

## morphnet.netlist.value_utils — Value Utilities

```python
from morphnet.netlist.value_utils import parse_si_number, format_si_value
```

#### `parse_si_number(token: str) -> PrefixedValue`

Parse a SPICE-style SI-prefixed number (e.g., `"10k"`, `"2.2u"`, `"100meg"`) into a `PrefixedValue`. Raises `ValueError` if the token is not valid.

#### `format_si_value(pv: PrefixedValue) -> str`

Format a `PrefixedValue` as a SPICE-style string (e.g., `"10k"`, `"2.2u"`).

#### `parse_parameter_number(token: str) -> ParameterValue`

Parse a numeric token into the most appropriate `ParameterValue` variant. Whole integers return `int_value`; everything else returns `prefixed_value`.

#### `is_si_number(token: str) -> bool`

Check whether a token looks like an SI-prefixed number.

#### Constants

| Constant | Type | Description |
|---|---|---|
| `SI_SUFFIX_TO_PREFIX` | `dict[str, SIPrefix]` | Maps suffix strings (`"k"`, `"u"`, `"meg"`, etc.) to `SIPrefix` enum values |
| `PREFIX_TO_SI_SUFFIX` | `dict[SIPrefix, str]` | Reverse mapping from `SIPrefix` to suffix strings |
| `DEVICE_PORT_TEMPLATES` | `dict[str, list[str]]` | Maps device prefix letters to port name lists (e.g., `"M"` -> `["d", "g", "s", "b"]`) |
| `DEVICE_PREFIX_TO_MODULE` | `dict[str, str]` | Maps device prefix letters to module names (e.g., `"M"` -> `"mosfet"`) |

---

## morphnet.netlist.net_utils — Network Utilities

```python
from morphnet.netlist.net_utils import (
    net_map_to_connections,
    connections_to_instance_nets,
)
```

#### `net_map_to_connections(net_map: NetMap) -> list[Connection]`

Convert a net-based connectivity map (`dict[str, list[PortReference]]`) to point-to-point `Connection` objects. For each net with N port references, produces N-1 connections.

#### `connections_to_instance_nets(connections: list[Connection]) -> dict[tuple[str, str], str]`

Build an `(instance_name, port_name) -> net_name` lookup from a list of `Connection` objects. Used by writers to reconstruct instance lines with correct net names.

#### `add_port_to_net(net_map: NetMap, net_name: str, instance_name: str, port_name: str) -> None`

Register a port reference on a net in the net map.

#### Type Aliases

| Alias | Definition | Description |
|---|---|---|
| `NetMap` | `dict[str, list[PortReference]]` | Maps net names to port references |
