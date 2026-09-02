from __future__ import annotations

from morphnet.morphnet_schema import Circuit
from morphnet.netlist.spice.writer import SpiceWriter


class SpectreSpiceWriter(SpiceWriter):
    """Convert a Circuit model to Spectre-SPICE netlist text.

    Outputs everything in SPICE syntax. HSPICE and Spectre-SPICE both
    accept standard .SUBCKT/.ENDS syntax.
    """


def write_spectre_spice(circuit: Circuit) -> str:
    """Convert a Circuit model to Spectre-SPICE netlist text."""
    return SpectreSpiceWriter().write(circuit)
