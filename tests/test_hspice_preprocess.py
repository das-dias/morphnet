from morphnet.netlist.hspice.preprocess import preprocess_hspice


class TestCommentStripping:
    def test_star_comment(self) -> None:
        text = "* comment\nR1 a b 1k\n"
        result = preprocess_hspice(text)
        assert "R1 a b 1k" in result
        assert "comment" not in result

    def test_dollar_inline_comment(self) -> None:
        text = "R1 a b 1k $ feedback resistor\n"
        result = preprocess_hspice(text)
        assert "R1 a b 1k" in result
        assert "feedback" not in result

    def test_semicolon_inline_comment(self) -> None:
        text = "R1 a b 1k ; comment\n"
        result = preprocess_hspice(text)
        assert "R1 a b 1k" in result
        assert "comment" not in result


class TestContinuations:
    def test_plus_continuation(self) -> None:
        text = "R1 a b\n+ 1k\n"
        result = preprocess_hspice(text)
        assert "R1 a b 1k" in result

    def test_backslash_continuation(self) -> None:
        text = "R1 a b \\\n1k\n"
        result = preprocess_hspice(text)
        assert "R1 a b" in result
        assert "1k" in result

    def test_combined_continuations(self) -> None:
        text = ".subckt test a b \\\nc d\n+ e f\n.ends test\n"
        result = preprocess_hspice(text)
        lines = [l for l in result.splitlines() if l.strip()]
        assert any("test" in l and "a" in l and "c" in l for l in lines)
