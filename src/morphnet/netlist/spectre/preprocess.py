from __future__ import annotations

import re

BLOCK_COMMENT_RE: re.Pattern[str] = re.compile(r"/\*.*?\*/", re.DOTALL)


def preprocess_spectre(text: str) -> str:
    """Prepare Spectre text for Lark parsing.

    1. Strip block comments (/* ... */) and line comments (//).
    2. Join backslash-continuation lines.
    3. Collapse whitespace, ensure trailing newline.
    """
    text = BLOCK_COMMENT_RE.sub("", text)

    lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        idx = stripped.find("//")
        if idx >= 0:
            stripped = stripped[:idx].rstrip()
        if not stripped:
            continue
        lines.append(stripped)

    joined = join_continuations_backslash(lines)
    result = add_semicolons(joined)
    if result and not result.endswith("\n"):
        result += "\n"
    return result


def join_continuations_backslash(lines: list[str]) -> str:
    """Join backslash-continuation lines (trailing \\ merges with next line)."""
    if not lines:
        return ""
    merged: list[str] = []
    buf = ""
    for line in lines:
        if line.endswith("\\"):
            buf += line[:-1].rstrip() + " "
        else:
            buf += line
            merged.append(buf)
            buf = ""
    if buf:
        merged.append(buf)
    return "\n".join(merged)


BLOCK_KEYWORDS = {"subckt", "section"}
END_KEYWORDS = {"ends", "endsection"}


def add_semicolons(text: str) -> str:
    """Append semicolons to lines that are not block openers/closers.

    Spectre uses newlines as statement terminators. For LALR parsing we
    inject explicit semicolons so the grammar can ignore all whitespace.
    Block-opening lines (subckt, section) and block-closing lines (ends,
    endsection) get their own markers handled by the grammar directly.
    """
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        first_word = stripped.split()[0] if stripped.split() else ""
        if first_word in BLOCK_KEYWORDS or first_word in END_KEYWORDS:
            out.append(stripped)
        else:
            out.append(stripped + " ;")
    return "\n".join(out)
