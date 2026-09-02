# Getting Started

## Installation

### From PyPI

```bash
pip install morphnet
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add morphnet
```

### Development Setup

Requires [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just):

```bash
git clone https://github.com/das-dias/morphnet.git
cd morphnet
just dev      # create venv and install all deps
just test     # run the test suite
just lint     # ruff check --fix
just fmt      # ruff format
```

## Your First Parse

Parse a Spectre netlist into MorphNet's intermediate representation:

```python
from morphnet.netlist.spectre.parser import parse_spectre

text = """\
subckt rc_lowpass (in_ out gnd)
R1 (in_ out) resistor value=1k
C1 (out gnd) capacitor value=100p
ends rc_lowpass
"""

circuit = parse_spectre(text)

print(circuit.domain)  # "spectre"
print(circuit.top_module)  # "rc_lowpass"
print(len(circuit.modules))  # 1
```

The `circuit` object is a `Circuit` model — MorphNet's common intermediate representation. Every parser produces the same type, regardless of the input format.

## Your First Conversion

Convert from one format to another by combining a parser with a writer:

```python
from morphnet.netlist.spectre.parser import parse_spectre
from morphnet.netlist.hspice.writer import write_hspice

spectre_text = """\
subckt rc_lowpass (in_ out gnd)
R1 (in_ out) resistor value=1k
C1 (out gnd) capacitor value=100p
ends rc_lowpass
"""

circuit = parse_spectre(spectre_text)
hspice_text = write_hspice(circuit)
print(hspice_text)
```

Output:

```spice
.subckt rc_lowpass in_ out gnd
R1 in_ out 1k
C1 out gnd 100p
.ends rc_lowpass
```

## YAML Roundtrip

Every `Circuit` object can be serialized to and from YAML for portable interchange:

```python
from morphnet.morphnet_schema import Circuit
from morphnet.netlist.hspice.parser import parse_hspice

circuit = parse_hspice("""\
.subckt rc_lowpass in_ out gnd
R1 in_ out 1k
C1 out gnd 100p
.ends rc_lowpass
""")

yaml_str = circuit.to_yaml()
restored = Circuit.from_yaml(yaml_str)

assert restored == circuit
```

## Project Structure

```
src/morphnet/
  morphnet_schema/     # Pydantic + protobuf data models (Circuit, Module, Port, etc.)
  netlist/
    grammars/          # Lark EBNF grammar files for each format
    hspice/            # HSPICE parser, writer, transformer, preprocessor
    spectre/           # Spectre parser, writer, transformer, preprocessor
    spectre_spice/     # Spectre-SPICE parser, writer, preprocessor
    spice/             # Generic SPICE parser, writer, transformer, preprocessor
    vams/              # Verilog-AMS parser, writer, transformer, preprocessor
    xyce/              # Xyce parser, writer, transformer, preprocessor
    net_utils.py       # Connectivity utilities
    value_utils.py     # SI value parsing and formatting
    simulation_data.py # Simulation analysis helpers
```
