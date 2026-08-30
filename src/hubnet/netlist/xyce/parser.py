from __future__ import annotations

from importlib.resources import files as resource_files
from typing import ClassVar

from lark import Lark

from hubnet.hubnet_schema import Circuit
from hubnet.netlist.xyce.preprocess import preprocess_xyce
from hubnet.netlist.xyce.transformer import XyceTransformer


class XyceParser:
    """Parse Xyce netlist text into a Circuit model."""

    lark_instance: ClassVar[Lark | None] = None

    @classmethod
    def get_lark(cls) -> Lark:
        if cls.lark_instance is None:
            grammar_text = (
                resource_files("hubnet.netlist.grammars")
                .joinpath("xyce.lark")
                .read_text(encoding="utf-8")
            )
            cls.lark_instance = Lark(grammar_text, parser="earley", ambiguity="resolve")
        return cls.lark_instance

    @classmethod
    def parse(cls, text: str) -> Circuit:
        cleaned = preprocess_xyce(text)
        lark = cls.get_lark()
        tree = lark.parse(cleaned)
        transformer = XyceTransformer()
        return transformer.transform(tree)


def parse_xyce(text: str) -> Circuit:
    """Parse Xyce netlist text into a Circuit model."""
    return XyceParser.parse(text)
