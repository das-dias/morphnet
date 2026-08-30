from __future__ import annotations

from importlib.resources import files as resource_files
from typing import ClassVar

from lark import Lark

from hubnet.hubnet_schema import Circuit
from hubnet.netlist.spice.preprocess import preprocess_spice
from hubnet.netlist.spice.transformer import SpiceTransformer


class SpiceParser:
    """Parse SPICE/HSPICE netlist text into a Circuit model.

    The Lark parser instance is built once and cached at class level.
    """

    lark_instance: ClassVar[Lark | None] = None

    @classmethod
    def get_lark(cls) -> Lark:
        if cls.lark_instance is None:
            grammar_text = (
                resource_files("hubnet.netlist.grammars")
                .joinpath("spice.lark")
                .read_text(encoding="utf-8")
            )
            cls.lark_instance = Lark(grammar_text, parser="earley", ambiguity="resolve")
        return cls.lark_instance

    @classmethod
    def parse(cls, text: str) -> Circuit:
        """Parse SPICE netlist text into a Circuit model.

        Steps:
        1. Pre-process: strip comments, join continuations — O(lines)
        2. Lark parse: build parse tree — O(n) with Earley
        3. Transform: convert tree to Circuit models — O(n) with dict lookups
        """
        cleaned = preprocess_spice(text)
        lark = cls.get_lark()
        tree = lark.parse(cleaned)
        transformer = SpiceTransformer()
        return transformer.transform(tree)


def parse_spice(text: str) -> Circuit:
    """Parse SPICE netlist text into a Circuit model."""
    return SpiceParser.parse(text)
