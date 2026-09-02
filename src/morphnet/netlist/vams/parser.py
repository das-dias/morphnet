from __future__ import annotations

from importlib.resources import files as resource_files
from typing import ClassVar

from lark import Lark

from morphnet.morphnet_schema import Circuit, Directive, DirectiveKind
from morphnet.netlist.vams.preprocess import preprocess_vams
from morphnet.netlist.vams.transformer import VamsTransformer

DIRECTIVE_KIND_MAP: dict[str, DirectiveKind] = {
    "include": DirectiveKind.INCLUDE,
    "define": DirectiveKind.DEFINE,
    "timescale": DirectiveKind.TIMESCALE,
}


class VamsParser:
    """Parse Verilog-AMS netlist text into a Circuit model."""

    lark_instance: ClassVar[Lark | None] = None

    @classmethod
    def get_lark(cls) -> Lark:
        if cls.lark_instance is None:
            grammar_text = (
                resource_files("morphnet.netlist.grammars")
                .joinpath("vams.lark")
                .read_text(encoding="utf-8")
            )
            cls.lark_instance = Lark(grammar_text, parser="lalr")
        return cls.lark_instance

    @classmethod
    def parse(cls, text: str) -> Circuit:
        result = preprocess_vams(text)
        lark = cls.get_lark()
        tree = lark.parse(result.text)
        transformer = VamsTransformer(analog_blocks=result.analog_blocks)
        circuit = transformer.transform(tree)

        directives: list[Directive] = []
        for kind_str, value in result.directives:
            dk = DIRECTIVE_KIND_MAP.get(kind_str, DirectiveKind.UNSPECIFIED)
            if dk == DirectiveKind.INCLUDE:
                value = value.strip("\"'")
            directives.append(Directive(kind=dk, value=value))

        if directives:
            circuit = Circuit(
                name=circuit.name,
                domain=circuit.domain,
                top_module=circuit.top_module,
                modules=circuit.modules,
                ext_modules=circuit.ext_modules,
                properties=circuit.properties,
                directives=directives,
            )

        return circuit


def parse_vams(text: str) -> Circuit:
    """Parse Verilog-AMS netlist text into a Circuit model."""
    return VamsParser.parse(text)
