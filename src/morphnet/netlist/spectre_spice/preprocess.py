from __future__ import annotations

import re
from dataclasses import dataclass

SIMULATOR_LANG_RE: re.Pattern[str] = re.compile(
    r"^\s*simulator\s+lang\s*=\s*(\w+)", re.IGNORECASE
)


@dataclass
class SpectreSpiceSection:
    """A section of a Spectre-SPICE file with its language mode."""

    language: str
    text: str


def preprocess_spectre_spice(text: str) -> list[SpectreSpiceSection]:
    """Split a Spectre-SPICE file into sections by language mode.

    Default mode is 'spice'. Lines matching 'simulator lang=spectre'
    or 'simulator lang=spice' switch the mode.
    """
    sections: list[SpectreSpiceSection] = []
    current_lang = "spice"
    current_lines: list[str] = []

    for line in text.splitlines():
        m = SIMULATOR_LANG_RE.match(line)
        if m:
            if current_lines:
                sections.append(
                    SpectreSpiceSection(
                        language=current_lang,
                        text="\n".join(current_lines) + "\n",
                    )
                )
                current_lines = []
            current_lang = m.group(1).lower()
        else:
            current_lines.append(line)

    if current_lines:
        sections.append(
            SpectreSpiceSection(
                language=current_lang,
                text="\n".join(current_lines) + "\n",
            )
        )

    return sections
