# Advanced Usage

## Working with the Circuit Model

### Circuit Structure

A `Circuit` is the top-level container. Here is how it is organized:

```
Circuit
├── name: str                    # circuit name
├── domain: str                  # source format ("spectre", "hspice", etc.)
├── top_module: str              # name of the top-level module
├── modules: list[Module]        # subcircuit/module definitions
│   ├── ports: list[Port]
│   ├── parameters: list[Parameter]
│   ├── module_references: list[ModuleReference]  # instances
│   ├── connections: list[Connection]
│   └── buses: list[Bus]
├── ext_modules: list[ExternalModule]  # primitive devices (resistor, mosfet, etc.)
├── directives: list[Directive]        # .include, .lib, .param, etc.
└── simulation: Simulation | None      # analyses, output requests, measurements
```

### Inspecting Modules

```python
from morphnet.netlist.spectre.parser import parse_spectre

circuit = parse_spectre("""\
subckt rc_lowpass (in_ out gnd)
R1 (in_ out) resistor value=1k
C1 (out gnd) capacitor value=100p
ends rc_lowpass
""")

module = circuit.modules[0]
print(module.name)  # "rc_lowpass"

# List port names
for port in module.ports:
    print(f"  {port.name} ({port.direction.name})")

# List instances
for ref in module.module_references:
    print(f"  {ref.name} -> {ref.module_name}")
    for pname, param in ref.parameter_overrides.items():
        print(f"    {pname} = {param.default_value}")
```

### Inspecting Connections

Connections are point-to-point links between port references:

```python
for conn in module.connections:
    src = conn.source
    tgt = conn.target
    print(
        f"  net {conn.name}: {src.instance_name}.{src.port_name} -> "
        f"{tgt.instance_name}.{tgt.port_name}"
    )
```

### Modifying Circuits

All MorphNet models are **frozen** (immutable Pydantic models). To create a modified version, use `model_copy`:

```python
modified = circuit.model_copy(update={"name": "my_modified_circuit"})

modified_module = module.model_copy(
    update={
        "name": "rc_lowpass_v2",
        "ports": module.ports + [Port(name="extra", direction=PortDirection.INPUT)],
    }
)
```

## Protobuf Serialization

### Binary Serialization

Compact binary format for storage or cross-language interop (C++, Java, Go, etc.):

```python
from morphnet.netlist.spectre.parser import parse_spectre
from morphnet.morphnet_schema import Circuit

circuit = parse_spectre("""\
subckt rc_lowpass (in_ out gnd)
R1 (in_ out) resistor value=1k
C1 (out gnd) capacitor value=100p
ends rc_lowpass
""")

# Serialize to bytes
data = circuit.to_proto_bytes()
print(f"Binary size: {len(data)} bytes")

# Deserialize
restored = Circuit.from_proto_bytes(data)
assert restored == circuit
```

### JSON Serialization

```python
json_str = circuit.to_json()
restored = Circuit.from_json(json_str)
assert restored == circuit
```

## Simulation Data

MorphNet parses simulation directives (analyses, output requests, measurements) into structured models.

### Parsing Simulation Statements

```python
from morphnet.netlist.hspice.parser import parse_hspice
from morphnet.morphnet_schema import AnalysisKind

circuit = parse_hspice("""\
.macro inv vin vout vdd gnd
M1 vout vin vdd vdd pmos w=1u l=100n
M2 vout vin gnd gnd nmos w=500n l=100n
.eom inv
.tran 1n 10u
.print TRAN V(vout)
.end
""")

sim = circuit.simulation
print(f"Analyses: {len(sim.analyses)}")
print(f"Output requests: {len(sim.output_requests)}")

analysis = sim.analyses[0]
print(f"Kind: {analysis.kind.name}")  # TRAN
print(f"Arguments: {analysis.arguments}")  # ["1n", "10u"]

output = sim.output_requests[0]
print(f"Variables: {output.variables}")  # ["V(vout)"]
```

### Analysis Kinds

The `AnalysisKind` enum supports:

| Kind | Description |
|------|-------------|
| `OP` | Operating point |
| `DC` | DC sweep |
| `AC` | AC frequency sweep |
| `TRAN` | Transient analysis |
| `NOISE` | Noise analysis |
| `TF` | Transfer function |
| `SENS` | Sensitivity |
| `PZ` | Pole-zero |
| `DISTO` | Distortion |
| `FOUR` | Fourier |
| `FFT` | Fast Fourier Transform |

### FFT Example

```python
from morphnet.netlist.hspice.parser import parse_hspice
from morphnet.morphnet_schema import AnalysisKind

circuit = parse_hspice("""\
.fft V(out) NP=1024 START=0 STOP=10u
.end
""")

fft = circuit.simulation.analyses[0]
assert fft.kind == AnalysisKind.FFT
print(fft.options)  # {"NP": "1024", "START": "0", "STOP": "10u"}
```

## Preprocessing Raw Text

Each format has a preprocessor that normalizes raw input before parsing (strips comments, joins line continuations, normalizes whitespace). You can call them directly:

```python
from morphnet.netlist.hspice.preprocess import preprocess_hspice
from morphnet.netlist.spectre.preprocess import preprocess_spectre
from morphnet.netlist.vams.preprocess import preprocess_vams

cleaned = preprocess_hspice(raw_text)
cleaned = preprocess_spectre(raw_text)
cleaned = preprocess_vams(raw_text)
```

This is useful when you need to inspect the cleaned text before parsing, or when building a custom pipeline.

## Value Utilities

The `value_utils` module provides functions for working with SPICE-style SI-prefixed numbers.

### Parsing SI Numbers

```python
from morphnet.netlist.value_utils import parse_si_number
from morphnet.morphnet_schema import SIPrefix

pv = parse_si_number("10k")
print(pv.double_value)  # 10.0
print(pv.prefix)  # SIPrefix.KILO

pv = parse_si_number("2.2u")
print(pv.double_value)  # 2.2
print(pv.prefix)  # SIPrefix.MICRO

pv = parse_si_number("100meg")
print(pv.double_value)  # 100.0
print(pv.prefix)  # SIPrefix.MEGA
```

### Formatting SI Values

```python
from morphnet.netlist.value_utils import format_si_value
from morphnet.morphnet_schema import PrefixedValue, SIPrefix

pv = PrefixedValue(double_value=100.0, prefix=SIPrefix.PICO)
print(format_si_value(pv))  # "100p"

pv = PrefixedValue(double_value=4.7, prefix=SIPrefix.KILO)
print(format_si_value(pv))  # "4.7k"
```

### Parsing Parameter Numbers

```python
from morphnet.netlist.value_utils import parse_parameter_number

# Whole integers -> int_value
pv = parse_parameter_number("42")
print(pv.int_value)  # 42

# SI-prefixed -> prefixed_value
pv = parse_parameter_number("10k")
print(pv.prefixed_value.double_value)  # 10.0
print(pv.prefixed_value.prefix.name)  # "KILO"
```

### Device Port Templates

The module provides lookup dictionaries for standard SPICE device types:

```python
from morphnet.netlist.value_utils import DEVICE_PORT_TEMPLATES, DEVICE_PREFIX_TO_MODULE

print(DEVICE_PORT_TEMPLATES["M"])  # ["d", "g", "s", "b"]
print(DEVICE_PORT_TEMPLATES["R"])  # ["p", "n"]

print(DEVICE_PREFIX_TO_MODULE["M"])  # "mosfet"
print(DEVICE_PREFIX_TO_MODULE["R"])  # "resistor"
```
