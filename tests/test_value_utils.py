import pytest

from morphnet.morphnet_schema import PrefixedValue, SIPrefix
from morphnet.netlist.value_utils import (
    format_si_value,
    is_si_number,
    parse_parameter_number,
    parse_si_number,
)


class TestParseSiNumber:
    def test_integer(self) -> None:
        pv = parse_si_number("100")
        assert pv.double_value == 100.0
        assert pv.prefix == SIPrefix.UNSPECIFIED

    def test_float(self) -> None:
        pv = parse_si_number("3.14")
        assert pv.double_value == pytest.approx(3.14)
        assert pv.prefix == SIPrefix.UNSPECIFIED

    def test_kilo(self) -> None:
        pv = parse_si_number("10k")
        assert pv.double_value == 10.0
        assert pv.prefix == SIPrefix.KILO

    def test_micro(self) -> None:
        pv = parse_si_number("1u")
        assert pv.double_value == 1.0
        assert pv.prefix == SIPrefix.MICRO

    def test_nano(self) -> None:
        pv = parse_si_number("9n")
        assert pv.double_value == 9.0
        assert pv.prefix == SIPrefix.NANO

    def test_pico(self) -> None:
        pv = parse_si_number("100p")
        assert pv.double_value == 100.0
        assert pv.prefix == SIPrefix.PICO

    def test_mega(self) -> None:
        pv = parse_si_number("1meg")
        assert pv.double_value == 1.0
        assert pv.prefix == SIPrefix.MEGA

    def test_negative(self) -> None:
        pv = parse_si_number("-0.4")
        assert pv.double_value == pytest.approx(-0.4)
        assert pv.prefix == SIPrefix.UNSPECIFIED

    def test_scientific_notation(self) -> None:
        pv = parse_si_number("1e-6")
        assert pv.double_value == pytest.approx(1e-6)
        assert pv.prefix == SIPrefix.UNSPECIFIED

    def test_decimal_with_suffix(self) -> None:
        pv = parse_si_number("0.18u")
        assert pv.double_value == pytest.approx(0.18)
        assert pv.prefix == SIPrefix.MICRO

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="Not a valid SI number"):
            parse_si_number("abc")


class TestParseSiNumberExtended:
    def test_mil_suffix(self) -> None:
        pv = parse_si_number("25mil")
        assert pv.double_value == pytest.approx(25 * 25.4e-6)
        assert pv.prefix == SIPrefix.UNSPECIFIED

    def test_x_suffix_as_mega(self) -> None:
        pv = parse_si_number("1x")
        assert pv.double_value == 1.0
        assert pv.prefix == SIPrefix.MEGA


class TestParseParameterNumber:
    def test_integer_returns_int_value(self) -> None:
        pv = parse_parameter_number("49")
        assert pv.int_value == 49
        assert pv.prefixed_value is None

    def test_negative_integer_returns_int_value(self) -> None:
        pv = parse_parameter_number("-3")
        assert pv.int_value == -3

    def test_zero_returns_int_value(self) -> None:
        pv = parse_parameter_number("0")
        assert pv.int_value == 0

    def test_float_returns_prefixed_value(self) -> None:
        pv = parse_parameter_number("3.14")
        assert pv.prefixed_value is not None
        assert pv.prefixed_value.double_value == pytest.approx(3.14)
        assert pv.int_value is None

    def test_suffixed_returns_prefixed_value(self) -> None:
        pv = parse_parameter_number("10k")
        assert pv.prefixed_value is not None
        assert pv.prefixed_value.prefix == SIPrefix.KILO

    def test_scientific_returns_prefixed_value(self) -> None:
        pv = parse_parameter_number("1e-6")
        assert pv.prefixed_value is not None
        assert pv.int_value is None

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="Not a valid SI number"):
            parse_parameter_number("abc")


class TestFormatSiValue:
    def test_integer_kilo(self) -> None:
        pv = PrefixedValue(double_value=10.0, prefix=SIPrefix.KILO)
        assert format_si_value(pv) == "10k"

    def test_float_micro(self) -> None:
        pv = PrefixedValue(double_value=0.18, prefix=SIPrefix.MICRO)
        assert format_si_value(pv) == "0.18u"

    def test_no_prefix(self) -> None:
        pv = PrefixedValue(double_value=3.14, prefix=SIPrefix.UNSPECIFIED)
        assert format_si_value(pv) == "3.14"

    def test_integer_no_prefix(self) -> None:
        pv = PrefixedValue(double_value=49.0, prefix=SIPrefix.UNSPECIFIED)
        assert format_si_value(pv) == "49"


class TestIsSiNumber:
    def test_valid(self) -> None:
        assert is_si_number("10k")
        assert is_si_number("3.14")
        assert is_si_number("100p")
        assert is_si_number("-0.4")
        assert is_si_number("1e-6")
        assert is_si_number("1meg")

    def test_invalid(self) -> None:
        assert not is_si_number("abc")
        assert not is_si_number("nch")
        assert not is_si_number("VDD")
