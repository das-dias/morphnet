from __future__ import annotations

import re

from hubnet.hubnet_schema import ParameterValue, PrefixedValue, SIPrefix

# ---------------------------------------------------------------------------
# SI suffix ↔ SIPrefix enum — O(1) lookups in both directions
# ---------------------------------------------------------------------------

SI_SUFFIX_TO_PREFIX: dict[str, SIPrefix] = {
    "a": SIPrefix.ATTO,
    "f": SIPrefix.FEMTO,
    "p": SIPrefix.PICO,
    "n": SIPrefix.NANO,
    "u": SIPrefix.MICRO,
    "m": SIPrefix.MILLI,
    "k": SIPrefix.KILO,
    "x": SIPrefix.MEGA,
    "meg": SIPrefix.MEGA,
    "g": SIPrefix.GIGA,
    "t": SIPrefix.TERA,
}

MIL_SCALE: float = 25.4e-6

PREFIX_TO_SI_SUFFIX: dict[SIPrefix, str] = {
    v: k for k, v in SI_SUFFIX_TO_PREFIX.items()
}

# ---------------------------------------------------------------------------
# Device port templates — O(1) lookup per instance line
# ---------------------------------------------------------------------------

DEVICE_PORT_TEMPLATES: dict[str, list[str]] = {
    "R": ["p", "n"],
    "C": ["p", "n"],
    "L": ["p", "n"],
    "D": ["p", "n"],
    "Q": ["c", "b", "e"],
    "M": ["d", "g", "s", "b"],
    "V": ["p", "n"],
    "I": ["p", "n"],
}

DEVICE_PREFIX_TO_MODULE: dict[str, str] = {
    "R": "resistor",
    "C": "capacitor",
    "L": "inductor",
    "D": "diode",
    "Q": "bjt",
    "M": "mosfet",
    "V": "vsource",
    "I": "isource",
}

# Regex: optional sign, digits with optional decimal, optional SI suffix
SI_NUMBER_RE: re.Pattern[str] = re.compile(
    r"^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)(meg|mil|[afpnumkgtxAFPNUMKGTX])?$",
    re.IGNORECASE,
)


def parse_si_number(token: str) -> PrefixedValue:
    """Parse a SPICE-style SI-prefixed number like '10k', '2.2u', '100meg'.

    Returns a PrefixedValue with the numeric part and the SIPrefix enum.
    Raises ValueError if the token is not a valid SI number.
    """
    m = SI_NUMBER_RE.match(token)
    if m is None:
        raise ValueError(f"Not a valid SI number: {token!r}")
    numeric_str, suffix = m.group(1), m.group(2)
    value = float(numeric_str)
    if suffix is None:
        prefix = SIPrefix.UNSPECIFIED
    else:
        suffix_lower = suffix.lower()
        if suffix_lower == "mil":
            return PrefixedValue(double_value=value * MIL_SCALE, prefix=SIPrefix.UNSPECIFIED)
        prefix = SI_SUFFIX_TO_PREFIX.get(suffix_lower)
        if prefix is None:
            raise ValueError(f"Unknown SI suffix: {suffix!r}")
    return PrefixedValue(double_value=value, prefix=prefix)


def parse_parameter_number(token: str) -> ParameterValue:
    """Parse a numeric token into the most appropriate ParameterValue variant.

    Whole integers (no decimal, no SI suffix, no exponent) return int_value.
    Everything else delegates to parse_si_number and returns prefixed_value.
    """
    m = SI_NUMBER_RE.match(token)
    if m is None:
        raise ValueError(f"Not a valid SI number: {token!r}")
    numeric_str, suffix = m.group(1), m.group(2)
    if suffix is None and "." not in numeric_str and "e" not in numeric_str.lower():
        return ParameterValue(int_value=int(numeric_str))
    return ParameterValue(prefixed_value=parse_si_number(token))


def format_si_value(pv: PrefixedValue) -> str:
    """Format a PrefixedValue as a SPICE-style string like '10k', '2.2u'.

    Produces the shortest clean representation (no trailing zeros).
    """
    num = pv.double_value
    if num == int(num):
        num_str = str(int(num))
    else:
        num_str = f"{num:g}"

    if pv.prefix == SIPrefix.UNSPECIFIED:
        return num_str

    suffix = PREFIX_TO_SI_SUFFIX.get(pv.prefix, "")
    return f"{num_str}{suffix}"


def is_si_number(token: str) -> bool:
    """Check whether a token looks like an SI-prefixed number."""
    return SI_NUMBER_RE.match(token) is not None
