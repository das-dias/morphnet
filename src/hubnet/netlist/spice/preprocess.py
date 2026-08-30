from __future__ import annotations


def preprocess_spice(text: str) -> str:
    """Prepare SPICE/HSPICE text for Lark parsing.

    1. Strip comment lines (* at column 0) and inline comments ($ or ;).
    2. Join continuation lines (+ at start of next line appends to previous).
    3. Collapse runs of whitespace to single spaces, strip trailing whitespace.
    4. Ensure a trailing newline.
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

    joined = join_continuations(lines)
    if joined and not joined.endswith("\n"):
        joined += "\n"
    return joined


def strip_inline_comment(line: str) -> str:
    """Remove inline SPICE comments ($ or ;) outside of quoted strings."""
    in_quote = False
    for i, ch in enumerate(line):
        if ch == "'":
            in_quote = not in_quote
        elif not in_quote and ch in ("$", ";"):
            return line[:i].rstrip()
    return line


def join_continuations(lines: list[str]) -> str:
    """Join SPICE continuation lines (+ at column 0 of the next line)."""
    if not lines:
        return ""
    merged: list[str] = [lines[0]]
    for line in lines[1:]:
        if line.startswith("+"):
            merged[-1] += " " + line[1:].lstrip()
        else:
            merged.append(line)
    return "\n".join(merged)
