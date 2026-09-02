from __future__ import annotations

from importlib.resources import files as resource_files
from typing import ClassVar

from lark import Lark

from morphnet.morphnet_schema import Circuit
from morphnet.netlist.spectre.preprocess import preprocess_spectre
from morphnet.netlist.spectre.transformer import SpectreTransformer


class SpectreParser:
    """Parse Spectre netlist text into a Circuit model."""

    lark_instance: ClassVar[Lark | None] = None

    @classmethod
    def get_lark(cls) -> Lark:
        if cls.lark_instance is None:
            grammar_text = (
                resource_files("morphnet.netlist.grammars")
                .joinpath("spectre.lark")
                .read_text(encoding="utf-8")
            )
            cls.lark_instance = Lark(grammar_text, parser="lalr")
        return cls.lark_instance

    @classmethod
    def parse(cls, text: str) -> Circuit:
        cleaned = preprocess_spectre(text)
        lark = cls.get_lark()
        tree = lark.parse(cleaned)
        transformer = SpectreTransformer()
        return transformer.transform(tree)


def parse_spectre(text: str) -> Circuit:
    """Parse Spectre netlist text into a Circuit model."""
    return SpectreParser.parse(text)
