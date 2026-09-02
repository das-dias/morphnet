from __future__ import annotations

from morphnet.morphnet_schema import Circuit, ParameterValue
from morphnet.netlist.spice.writer import SpiceWriter


class XyceWriter(SpiceWriter):
    """Convert a Circuit model to Xyce netlist text.

    Xyce output is structurally identical to SPICE — the only difference
    is that .SUBCKT lines may include a PARAMS: keyword, which is optional
    and we omit for simplicity (Xyce accepts both forms).
    """

    def format_param_value(self, pval: ParameterValue) -> str:
        if pval.expression is not None:
            expr = pval.expression
            if not expr.startswith("{"):
                expr = "{" + expr + "}"
            return expr
        return super().format_param_value(pval)


def write_xyce(circuit: Circuit) -> str:
    """Convert a Circuit model to Xyce netlist text."""
    return XyceWriter().write(circuit)
