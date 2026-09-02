from __future__ import annotations

from morphnet.netlist.spectre.preprocess import join_continuations_backslash
from morphnet.netlist.spice.preprocess import join_continuations, strip_inline_comment


def preprocess_hspice(text: str) -> str:
    """Prepare HSPICE text for Lark parsing.

    1. Strip comment lines (* at column 0) and inline comments ($ or ;).
    2. Join backslash continuations (\\ at end of line).
    3. Join + continuations (+ at start of next line).
    4. Ensure trailing newline.
    """
    lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("*"):
            continue
        cleaned = strip_inline_comment(stripped)
        if not cleaned:
            continue
        lines.append(cleaned)

    joined_lines = join_continuations_backslash(lines).splitlines()
    joined = join_continuations(joined_lines)
    if joined and not joined.endswith("\n"):
        joined += "\n"
    return joined
