from morphnet.netlist.spectre.preprocess import preprocess_spectre
from morphnet.netlist.spice.preprocess import preprocess_spice
from morphnet.netlist.xyce.preprocess import preprocess_xyce


class TestSpicePreprocess:
    def test_strips_comment_lines(self) -> None:
        text = "* This is a comment\nR1 a b 1k\n"
        result = preprocess_spice(text)
        assert "comment" not in result
        assert "R1 a b 1k" in result

    def test_joins_continuation_lines(self) -> None:
        text = "R1 a b\n+ 1k\n"
        result = preprocess_spice(text)
        assert "R1 a b 1k" in result
        assert "+" not in result

    def test_strips_inline_dollar_comment(self) -> None:
        text = "R1 a b 1k $ inline comment\n"
        result = preprocess_spice(text)
        assert "R1 a b 1k" in result
        assert "inline" not in result

    def test_strips_inline_semicolon_comment(self) -> None:
        text = "R1 a b 1k ; inline comment\n"
        result = preprocess_spice(text)
        assert "R1 a b 1k" in result
        assert "inline" not in result

    def test_preserves_quoted_dollar(self) -> None:
        text = "R1 a b '1k$val'\n"
        result = preprocess_spice(text)
        assert "'1k$val'" in result

    def test_ensures_trailing_newline(self) -> None:
        text = "R1 a b 1k"
        result = preprocess_spice(text)
        assert result.endswith("\n")

    def test_empty_input(self) -> None:
        assert preprocess_spice("") == ""
        assert preprocess_spice("\n\n") == ""

    def test_multiple_continuations(self) -> None:
        text = "M1 d g\n+ s b nch\n+ W=1u L=0.18u\n"
        result = preprocess_spice(text)
        assert "M1 d g s b nch W=1u L=0.18u" in result


class TestSpectrePreprocess:
    def test_strips_line_comments(self) -> None:
        text = "// comment\nR0 (a b) resistor r=1k\n"
        result = preprocess_spectre(text)
        assert "comment" not in result
        assert "R0" in result

    def test_strips_block_comments(self) -> None:
        text = "R0 /* inline block */ (a b) resistor\n"
        result = preprocess_spectre(text)
        assert "inline block" not in result
        assert "R0" in result

    def test_joins_backslash_continuations(self) -> None:
        text = "R0 (a \\\nb) resistor\n"
        result = preprocess_spectre(text)
        assert "R0 (a b) resistor" in result

    def test_ensures_trailing_newline(self) -> None:
        text = "R0 (a b) resistor"
        result = preprocess_spectre(text)
        assert result.endswith("\n")


class TestXycePreprocess:
    def test_same_as_spice(self) -> None:
        text = "* comment\nR1 a b 1k\n+ extra\n"
        assert preprocess_xyce(text) == preprocess_spice(text)
