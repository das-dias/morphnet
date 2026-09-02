from __future__ import annotations

from morphnet.netlist.spice.preprocess import preprocess_spice


def preprocess_xyce(text: str) -> str:
    """Prepare Xyce text for Lark parsing.

    Same as SPICE preprocessing — Xyce uses the same comment and
    continuation conventions.  {expression} blocks are preserved
    since they don't contain comment or continuation characters.
    """
    return preprocess_spice(text)
