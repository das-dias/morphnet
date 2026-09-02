# Extending MorphNet with New Formats

MorphNet follows a consistent 5-module pattern for every netlist format. To add support for a new format (e.g., `myformat`), create the following modules under `src/morphnet/netlist/myformat/`.

## Overview

```
src/morphnet/netlist/myformat/
  __init__.py          # empty
  preprocess.py        # text normalization
  transformer.py       # parse tree -> Circuit
  parser.py            # grammar + orchestration
  writer.py            # Circuit -> text
```

Plus a grammar file:

```
src/morphnet/netlist/grammars/myformat.lark
```

## Step 1: Write the Lark Grammar

Create `src/morphnet/netlist/grammars/myformat.lark`.

MorphNet grammars use [Lark EBNF syntax](https://lark-parser.readthedocs.io/en/stable/grammar.html). The LALR parser is preferred for performance; use Earley only if the grammar is inherently ambiguous.

```lark
// myformat.lark
start: toplevel_item*

?toplevel_item: subckt_def
              | instance_stmt

subckt_def: "SUBCKT" IDENT port_decl+ body "END"
// ... define terminals and rules for your format
```

Every grammar must define a `start` rule that produces the top-level netlist structure.

Shared terminals (identifiers, SI numbers) can be imported from `common.lark`:

```lark
%import .common.IDENT
%import .common.SI_NUMBER
```

!!! tip
    Start from an existing grammar as a reference. `spectre.lark` and `spice.lark` in `src/morphnet/netlist/grammars/` are good starting points.

## Step 2: Create the Preprocessor

Create `src/morphnet/netlist/myformat/preprocess.py` to normalize raw input before parsing. Most formats need comment stripping, line continuation joining, or whitespace normalization:

```python
# src/morphnet/netlist/myformat/preprocess.py


def preprocess_myformat(text: str) -> str:
    # Strip comments, join continuations, normalize whitespace
    ...
    return cleaned
```

## Step 3: Implement the Transformer

Create `src/morphnet/netlist/myformat/transformer.py` with a Lark `Transformer` subclass that converts the parse tree into a `Circuit` model:

```python
# src/morphnet/netlist/myformat/transformer.py
from __future__ import annotations

from lark import Transformer

from morphnet.morphnet_schema import Circuit, Module, Port, ModuleReference, Connection
from morphnet.netlist.net_utils import NetMap, add_port_to_net, net_map_to_connections
from morphnet.netlist.value_utils import parse_si_number


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

The transformer must produce a valid `Circuit` object — the same protobuf-backed Pydantic model that all other formats use.

!!! tip "Reuse utilities"
    Use `net_map_to_connections` from `morphnet.netlist.net_utils` to convert net-based connectivity (common in SPICE) to point-to-point `Connection` objects. Use `parse_si_number` from `morphnet.netlist.value_utils` to parse SI-prefixed parameter values.

## Step 4: Implement the Parser

Create `src/morphnet/netlist/myformat/parser.py` following the established pattern: a class with a cached `Lark` instance, a `parse()` classmethod, and a module-level convenience function:

```python
# src/morphnet/netlist/myformat/parser.py
from __future__ import annotations

from importlib.resources import files as resource_files
from typing import ClassVar

from lark import Lark

from morphnet.morphnet_schema import Circuit
from morphnet.netlist.myformat.preprocess import preprocess_myformat
from morphnet.netlist.myformat.transformer import MyFormatTransformer


class MyFormatParser:
    lark_instance: ClassVar[Lark | None] = None

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

## Step 5: Implement the Writer

Create `src/morphnet/netlist/myformat/writer.py` that takes a `Circuit` and produces formatted netlist text:

```python
# src/morphnet/netlist/myformat/writer.py
from __future__ import annotations

from morphnet.morphnet_schema import Circuit
from morphnet.netlist.net_utils import connections_to_instance_nets
from morphnet.netlist.value_utils import format_si_value


class MyFormatWriter:
    def write(self, circuit: Circuit) -> str:
        lines = []
        for module in circuit.modules:
            # Emit subcircuit/module header
            # Emit instances with port connections and parameters
            # Emit footer
            ...
        return "\n".join(lines)


def write_myformat(circuit: Circuit) -> str:
    return MyFormatWriter().write(circuit)
```

!!! tip "Reuse utilities"
    Use `connections_to_instance_nets` to build a `(instance_name, port_name) -> net_name` lookup from the module's connections. Use `format_si_value` to emit SI-prefixed parameter values.

## Step 6: Add Tests

Create three test files in `tests/`:

### Parser tests

`tests/test_myformat_parser.py` — unit tests for parsing individual constructs:

```python
from morphnet.netlist.myformat.parser import parse_myformat


class TestBasicParsing:
    def test_resistor_subcircuit(self) -> None:
        circuit = parse_myformat("...")
        assert len(circuit.modules) == 1
        assert circuit.modules[0].name == "divider"


class TestDeviceTypes:
    def test_mosfet_instance(self) -> None:
        circuit = parse_myformat("...")
        refs = circuit.modules[0].module_references
        assert refs[0].module_name == "mosfet"
```

### Writer tests

`tests/test_myformat_writer.py` — unit tests for writer output on known `Circuit` objects.

### Roundtrip tests

`tests/test_myformat_roundtrip.py` — roundtrip stability:

```python
def test_parse_write_parse(self) -> None:
    circuit1 = parse_myformat(text)
    written = write_myformat(circuit1)
    circuit2 = parse_myformat(written)
    assert circuit1 == circuit2
```

Add golden netlist files under `tests/netlists/myformat/` for the four standard circuits (`rc_lowpass`, `resistor_divider`, `hierarchical_subckt`, `inverter_with_models`).

## Step 7: Register Exports

Add the new parse and write functions to `src/morphnet/netlist/__init__.py`:

```python
from morphnet.netlist.myformat.parser import parse_myformat
from morphnet.netlist.myformat.writer import write_myformat
```

## Protobuf Schema Changes

If you need to modify the circuit or simulation protobuf schemas:

1. Edit the `.proto` files in `protos/`
2. Run `just proto` to regenerate Python bindings
3. Update the corresponding Pydantic models in `src/morphnet/morphnet_schema/`
4. Run the full test suite to verify nothing broke

## Coding Standards

This project follows [PEP 8](https://peps.python.org/pep-0008/) enforced by [Ruff](https://docs.astral.sh/ruff/):

- **Line length**: 88 characters (Ruff default)
- **Formatting**: `just fmt` (runs `ruff format`)
- **Linting**: `just lint` (runs `ruff check --fix`)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants
- **Type annotations**: Required on all public function signatures
- **Testing**: `pytest` with parametrized tests for multi-format coverage
- **No inline comments** unless explaining a non-obvious constraint
