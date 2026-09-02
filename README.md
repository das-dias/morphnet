# MorphNet

A bidirectional netlist parser built on [Lark](https://github.com/lark-parser/lark), enabling translation between SPICE-family circuit netlist formats (HSPICE, Xyce, Spectre, Spectre-SPICE) and Verilog-AMS.

All formats share a common intermediate representation defined in [Protocol Buffers](protos/circuit.proto) and wrapped with [Pydantic v2](src/morphnet/morphnet_schema/_circuit.py) models, making it straightforward to parse, transform, and serialize netlists programmatically.

## Installation

```bash
pip install morphnet
```

**Development setup** (requires [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just)):

```bash
just dev      # create venv and install all deps
just test     # run the test suite
just lint     # ruff check --fix
just fmt      # ruff format
```

## Quick Start

### Parse a Spectre netlist and convert to Verilog-AMS

```python
from morphnet.netlist.spectre.parser import parse_spectre
from morphnet.netlist.vams.writer import write_vams

spectre_netlist = """\
subckt rc_lowpass (in_ out gnd)
R1 (in_ out) resistor value=1k
C1 (out gnd) capacitor value=100p
ends rc_lowpass
"""

circuit = parse_spectre(spectre_netlist)
print(write_vams(circuit))
```

Output:

```verilog
module rc_lowpass (in_, out, gnd);
  inout in_, out, gnd;
  resistor #(.value(1k)) R1 (.p(in_), .n(out));
  capacitor #(.value(100p)) C1 (.p(out), .n(gnd));
endmodule
```

### Parse a Verilog-AMS netlist and convert to Spectre

```python
from morphnet.netlist.vams.parser import parse_vams
from morphnet.netlist.spectre.writer import write_spectre

vams_netlist = """\
module cmos_inverter (in_, out, vdd, vss);
  inout in_, out, vdd, vss;
  mosfet #(.L(0.18u), .W(1u)) M1 (.d(out), .g(in_), .s(vdd), .b(vdd));
  mosfet #(.L(0.18u), .W(0.5u)) M2 (.d(out), .g(in_), .s(vss), .b(vss));
endmodule
"""

circuit = parse_vams(vams_netlist)
print(write_spectre(circuit))
```

Output:

```spectre
subckt cmos_inverter (in_ out vdd vss)
M1 (out in_ vdd vdd) mosfet L=0.18u W=1u
M2 (out in_ vss vss) mosfet L=0.18u W=0.5u
ends cmos_inverter
```

### YAML as a portable interchange format

Every `Circuit` object serializes to and from YAML:

```python
from morphnet.morphnet_schema import Circuit
from morphnet.netlist.hspice.parser import parse_hspice

circuit = parse_hspice(".subckt rc_lowpass in_ out gnd\nR1 in_ out 1k\nC1 out gnd 100p\n.ends rc_lowpass\n")

yaml_str = circuit.to_yaml()
restored = Circuit.from_yaml(yaml_str)

assert restored == circuit
```

### Supported formats

| Format | Parser | Writer |
|---|---|---|
| HSPICE | `morphnet.netlist.hspice.parser.parse_hspice` | `morphnet.netlist.hspice.writer.write_hspice` |
| SPICE | `morphnet.netlist.spice.parser.parse_spice` | `morphnet.netlist.spice.writer.write_spice` |
| Xyce | `morphnet.netlist.xyce.parser.parse_xyce` | `morphnet.netlist.xyce.writer.write_xyce` |
| Spectre | `morphnet.netlist.spectre.parser.parse_spectre` | `morphnet.netlist.spectre.writer.write_spectre` |
| Spectre-SPICE | `morphnet.netlist.spectre_spice.parser.parse_spectre_spice` | `morphnet.netlist.spectre_spice.writer.write_spectre_spice` |
| Verilog-AMS | `morphnet.netlist.vams.parser.parse_vams` | `morphnet.netlist.vams.writer.write_vams` |

## Architecture

```
spectre.scs ──┐                          ┌── spectre.scs
hspice.sp  ───┤  parse_*()   write_*()   ├── hspice.sp
xyce.cir   ───┼──────────► Circuit ──────►├── xyce.cir
spice.sp   ───┤          (protobuf +      ├── spice.sp
vams.vams  ───┘           pydantic)       └── vams.vams
                             │
                        to_yaml / from_yaml
                             │
                          circuit.yaml
```

Each format follows the same internal pipeline:

```
raw text → preprocess → Lark grammar → parse tree → Transformer → Circuit
Circuit → Writer → formatted text
```

## Contributing

### Adding support for a new netlist grammar

MorphNet follows a consistent pattern for every netlist format. To add a new one (e.g., `myformat`), create the following modules under `src/morphnet/netlist/myformat/`:

#### 1. Write the Lark grammar

Create a `.lark` file in `src/morphnet/netlist/grammars/myformat.lark`.

MorphNet grammars use the [Lark EBNF syntax](https://lark-parser.readthedocs.io/en/stable/grammar.html). The LALR parser is preferred for performance; use Earley only if the grammar is inherently ambiguous.

Start from the existing grammars as a reference -- for example, `spectre.lark` (71 lines) covers subcircuits, instances, models, parameters, and simulation statements. Every grammar must define a `start` rule that produces the top-level netlist structure.

```lark
// myformat.lark
start: toplevel_item*

?toplevel_item: subckt_def
              | instance_stmt

subckt_def: "SUBCKT" IDENT port_decl+ body "END"
// ... define terminals and rules for your format
```

Shared terminals (identifiers, SI numbers) can be imported from `common.lark` if applicable.

#### 2. Create the preprocessor

Create `preprocess.py` to normalize raw input before parsing. Most formats need comment stripping, line continuation joining, or whitespace normalization:

```python
# src/morphnet/netlist/myformat/preprocess.py
def preprocess_myformat(text: str) -> str:
    # Strip comments, join continuations, normalize whitespace
    ...
    return cleaned
```

#### 3. Implement the Transformer

Create `transformer.py` with a Lark `Transformer` subclass that converts the parse tree into a `Circuit` model:

```python
# src/morphnet/netlist/myformat/transformer.py
from lark import Transformer
from morphnet.morphnet_schema import Circuit, Module, Port, ...

class MyFormatTransformer(Transformer):
    def subckt_def(self, items):
        # Build a Module from the parsed subcircuit
        ...

    def instance_stmt(self, items):
        # Build a ModuleReference from a parsed instance
        ...

    def start(self, items):
        # Assemble the final Circuit
        return Circuit(modules=..., ext_modules=...)
```

The transformer must produce a valid `Circuit` object -- the same protobuf-backed Pydantic model that all other formats use.

#### 4. Implement the Parser

Create `parser.py` following the established pattern: a class with a cached `Lark` instance and a `parse()` class method, plus a module-level convenience function:

```python
# src/morphnet/netlist/myformat/parser.py
from importlib.resources import files as resource_files
from lark import Lark
from morphnet.morphnet_schema import Circuit

class MyFormatParser:
    lark_instance = None

    @classmethod
    def get_lark(cls) -> Lark:
        if cls.lark_instance is None:
            grammar_text = (
                resource_files("morphnet.netlist.grammars")
                .joinpath("myformat.lark")
                .read_text(encoding="utf-8")
            )
            cls.lark_instance = Lark(grammar_text, parser="lalr")
        return cls.lark_instance

    @classmethod
    def parse(cls, text: str) -> Circuit:
        cleaned = preprocess_myformat(text)
        tree = cls.get_lark().parse(cleaned)
        return MyFormatTransformer().transform(tree)

def parse_myformat(text: str) -> Circuit:
    return MyFormatParser.parse(text)
```

#### 5. Implement the Writer

Create `writer.py` that takes a `Circuit` and produces formatted netlist text:

```python
# src/morphnet/netlist/myformat/writer.py
from morphnet.morphnet_schema import Circuit

class MyFormatWriter:
    def write(self, circuit: Circuit) -> str:
        lines = []
        for module in circuit.modules:
            # Emit subcircuit/module header, instances, parameters
            ...
        return "\n".join(lines)

def write_myformat(circuit: Circuit) -> str:
    return MyFormatWriter().write(circuit)
```

#### 6. Add tests

Create three test files in `tests/`:

- **`test_myformat_parser.py`** -- unit tests for parsing individual constructs (subcircuits, instances, parameters, models).
- **`test_myformat_writer.py`** -- unit tests for writer output on known `Circuit` objects.
- **`test_myformat_roundtrip.py`** -- roundtrip stability tests: `parse → write → parse → assert` and `write → parse → write → assert text equal`.

Add golden netlist files under `tests/netlists/myformat/` for the four standard circuits (`rc_lowpass`, `resistor_divider`, `hierarchical_subckt`, `inverter_with_models`) and wire them into `test_yaml_netlist_roundtrip.py`.

### Running tests

```bash
just test                          # full suite
uv run pytest tests/ -x -q        # stop on first failure
uv run pytest -k "myformat" -v    # run only your format's tests
```

### Protobuf schema changes

If you need to modify the circuit or simulation protobuf schemas:

1. Edit the `.proto` files in `protos/`
2. Run `just proto` to regenerate Python bindings
3. Update the corresponding Pydantic models in `src/morphnet/morphnet_schema/`
4. Run the full test suite to verify nothing broke

## Coding Standards

This project follows [PEP 8](https://peps.python.org/pep-0008/) enforced by [Ruff](https://docs.astral.sh/ruff/). Key conventions:

**Style**
- Line length: 88 characters (Ruff default)
- Formatting: `just fmt` (runs `ruff format`)
- Linting: `just lint` (runs `ruff check --fix`)
- Import order: managed by Ruff's isort rules

**Naming**
- `snake_case` for functions, methods, variables, and modules
- `PascalCase` for classes (e.g., `SpectreParser`, `VamsWriter`)
- `UPPER_SNAKE_CASE` for module-level constants
- Prefix private helpers with underscore (`_resolve_proto_model_type`)

**Type annotations**
- Required on all public function signatures
- Use `from __future__ import annotations` for modern syntax (`list[str]` over `List[str]`)
- Pydantic models use `ClassVar` for class-level attributes

**Code organization**
- One parser/writer/transformer per format under `src/morphnet/netlist/<format>/`
- Shared utilities in `src/morphnet/netlist/net_utils.py` and `value_utils.py`
- Schema models in `src/morphnet/morphnet_schema/`
- No inline comments unless explaining a non-obvious constraint
- Prefer flat code over deep nesting

**Testing**
- Use `pytest` with parametrized tests for multi-format coverage
- Each format needs parser, writer, and roundtrip test files
- Golden files in `tests/netlists/<format>/` for regression testing

## License

See [LICENSE](LICENSE) for details.
