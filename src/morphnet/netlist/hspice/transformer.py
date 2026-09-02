from __future__ import annotations

import re
from typing import Any

from lark import Token

from morphnet.morphnet_schema import ParameterValue
from morphnet.netlist.simulation_data import AnalysisData
from morphnet.netlist.spice.transformer import SpiceTransformer

EXPR_OPERATORS_RE: re.Pattern[str] = re.compile(r"[+\-*/()]")


class HspiceTransformer(SpiceTransformer):
    """Extend the SPICE transformer with HSPICE-specific handling.

    Additions:
    - .MACRO/.EOM treated as synonyms for .SUBCKT/.ENDS
    - Quoted strings containing arithmetic operators route to expression
    - .FFT analysis statement
    """

    def macro_def(self, items: list[Any]) -> Any:
        return self.subckt_def(items)

    def pvalue_qstring(self, items: list[Token]) -> ParameterValue:
        raw = str(items[0]).strip("\"'")
        if EXPR_OPERATORS_RE.search(raw):
            return ParameterValue(expression=raw)
        return ParameterValue(string_value=raw)

    def fft_stmt(self, items: list[Any]) -> AnalysisData:
        args, opts = self._extract_sim_args(items)
        return AnalysisData(kind="fft", arguments=args, options=opts)
