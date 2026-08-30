from __future__ import annotations

import re
from dataclasses import dataclass, field

BLOCK_COMMENT_RE: re.Pattern[str] = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE: re.Pattern[str] = re.compile(r"//[^\n]*")
DIRECTIVE_RE: re.Pattern[str] = re.compile(r"^\s*`(\w+)\s*(.*)", re.MULTILINE)


@dataclass
class VamsPreprocessResult:
    text: str
    directives: list[tuple[str, str]] = field(default_factory=list)
    analog_blocks: list[str] = field(default_factory=list)


def preprocess_vams(text: str) -> VamsPreprocessResult:
    """Prepare Verilog-AMS text for Lark parsing.

    1. Strip block comments and line comments.
    2. Extract backtick directives (`include, `define, `timescale, etc.).
    3. Replace analog blocks with __analog_placeholder__ N ; markers.
    """
    text = BLOCK_COMMENT_RE.sub("", text)
    text = LINE_COMMENT_RE.sub("", text)

    directives: list[tuple[str, str]] = []
    for m in DIRECTIVE_RE.finditer(text):
        directives.append((m.group(1), m.group(2).strip()))
    text = DIRECTIVE_RE.sub("", text)

    text, analog_blocks = replace_analog_blocks(text)

    text = re.sub(r"\n{2,}", "\n", text)
    text = text.strip()
    if text and not text.endswith("\n"):
        text += "\n"

    return VamsPreprocessResult(
        text=text,
        directives=directives,
        analog_blocks=analog_blocks,
    )


ANALOG_SINGLE_RE = re.compile(
    r"\banalog\b\s+(?!begin\b)([^;]+;)", re.DOTALL
)


def replace_analog_blocks(text: str) -> tuple[str, list[str]]:
    """Replace analog blocks with numbered placeholder tokens."""
    blocks: list[str] = []

    text = _replace_analog_begin_end(text, blocks)
    text = _replace_analog_single(text, blocks)

    return text, blocks


def _replace_analog_begin_end(text: str, blocks: list[str]) -> str:
    """Replace `analog begin ... end` blocks."""
    result: list[str] = []
    i = 0
    while i < len(text):
        m = re.search(r"\banalog\s+begin\b", text[i:])
        if m is None:
            result.append(text[i:])
            break
        start = i + m.start()
        result.append(text[i:start])
        body_start = i + m.end()
        depth = 1
        j = body_start
        while j < len(text) and depth > 0:
            bm = re.search(r"\b(begin|end)\b", text[j:])
            if bm is None:
                j = len(text)
                break
            keyword = bm.group(1)
            j = j + bm.end()
            if keyword == "begin":
                depth += 1
            else:
                depth -= 1
        block_text = text[start:j].strip()
        idx = len(blocks)
        blocks.append(block_text)
        result.append(f"__analog_placeholder__ {idx} ;")
        i = j
    return "".join(result)


def _replace_analog_single(text: str, blocks: list[str]) -> str:
    """Replace single-statement `analog <stmt>;` (not `analog begin`)."""

    def repl(m: re.Match[str]) -> str:
        idx = len(blocks)
        blocks.append(f"analog {m.group(1)}")
        return f"__analog_placeholder__ {idx} ;"

    return ANALOG_SINGLE_RE.sub(repl, text)
