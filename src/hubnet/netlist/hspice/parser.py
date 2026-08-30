from __future__ import annotations

from importlib.resources import files as resource_files
from typing import ClassVar

from lark import Lark

from hubnet.hubnet_schema import Circuit
from hubnet.netlist.hspice.preprocess import preprocess_hspice
from hubnet.netlist.hspice.transformer import HspiceTransformer


class HspiceParser:
    """Parse HSPICE netlist text into a Circuit model.

    Extends SpiceParser with HSPICE grammar and preprocessor.
    """

    lark_instance: ClassVar[Lark | None] = None

    @classmethod
    def get_lark(cls) -> Lark:
        if cls.lark_instance is None:
            grammar_text = (
                resource_files("hubnet.netlist.grammars")
                .joinpath("hspice.lark")
                .read_text(encoding="utf-8")
            )
            cls.lark_instance = Lark(grammar_text, parser="earley", ambiguity="resolve")
        return cls.lark_instance

    @classmethod
    def parse(cls, text: str) -> Circuit:
        cleaned = preprocess_hspice(text)
        lark = cls.get_lark()
        tree = lark.parse(cleaned)
        transformer = HspiceTransformer()
        circuit = transformer.transform(tree)
        return Circuit(
            name=circuit.name,
            domain="hspice",
            top_module=circuit.top_module,
            modules=circuit.modules,
            ext_modules=circuit.ext_modules,
            directives=circuit.directives,
            simulation=circuit.simulation,
        )


def parse_hspice(text: str) -> Circuit:
    """Parse HSPICE netlist text into a Circuit model."""
    return HspiceParser.parse(text)
