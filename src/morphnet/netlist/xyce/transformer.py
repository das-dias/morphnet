from __future__ import annotations

from typing import Any

from lark import Token

from morphnet.morphnet_schema import ParameterValue
from morphnet.netlist.simulation_data import OutputRequestData
from morphnet.netlist.spice.transformer import SpiceTransformer


class XyceTransformer(SpiceTransformer):
    """Extend the SPICE transformer with Xyce-specific handling.

    Additions:
    - {expression} blocks in parameter values and tokens.
    - PARAMS: keyword in .SUBCKT (consumed by grammar, no transformer change needed).
    """

    def token_expr(self, items: list[Token]) -> Token:
        return items[0]

    def pvalue_expr(self, items: list[Token]) -> ParameterValue:
        return ParameterValue(expression=str(items[0]))

    def params_kw(self, items: list[Any]) -> None:
        return None

    def print_stmt(self, items: list[Any]) -> OutputRequestData:
        tokens = [
            str(t) for t in items if isinstance(t, Token) and not str(t).startswith(".")
        ]
        analysis_type = tokens[0] if tokens else ""
        variables = tokens[1:]
        return OutputRequestData(
            kind="print", analysis_type=analysis_type, variables=variables
        )
