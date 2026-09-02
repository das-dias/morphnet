from __future__ import annotations

from morphnet.morphnet_schema import Circuit
from morphnet.netlist.spice.writer import SpiceWriter


class HspiceWriter(SpiceWriter):
    """Convert a Circuit model to HSPICE netlist text.

    HSPICE output is structurally identical to generic SPICE.
    Expressions are output in single quotes by the base format_param_value.
    """


def write_hspice(circuit: Circuit) -> str:
    """Convert a Circuit model to HSPICE netlist text."""
    return HspiceWriter().write(circuit)
