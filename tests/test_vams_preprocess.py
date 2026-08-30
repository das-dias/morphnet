from hubnet.netlist.vams.preprocess import preprocess_vams


class TestCommentStripping:
    def test_block_comment(self) -> None:
        text = "/* comment */\nmodule test (a); endmodule\n"
        result = preprocess_vams(text)
        assert "comment" not in result.text
        assert "module test" in result.text

    def test_line_comment(self) -> None:
        text = "module test (a); // inline\nendmodule\n"
        result = preprocess_vams(text)
        assert "inline" not in result.text
        assert "module test" in result.text

    def test_multiline_block_comment(self) -> None:
        text = "module test (a);\n/* multi\nline\ncomment */\nendmodule\n"
        result = preprocess_vams(text)
        assert "multi" not in result.text


class TestDirectiveExtraction:
    def test_include(self) -> None:
        text = '`include "models.vams"\nmodule test (a); endmodule\n'
        result = preprocess_vams(text)
        assert ("include", '"models.vams"') in result.directives
        assert "`include" not in result.text

    def test_define(self) -> None:
        text = "`define PI 3.14159\nmodule test (a); endmodule\n"
        result = preprocess_vams(text)
        assert ("define", "PI 3.14159") in result.directives

    def test_timescale(self) -> None:
        text = "`timescale 1ns/1ps\nmodule test (a); endmodule\n"
        result = preprocess_vams(text)
        assert ("timescale", "1ns/1ps") in result.directives


class TestAnalogBlockReplacement:
    def test_analog_begin_end(self) -> None:
        text = "module test (a);\nanalog begin\n  V(a) <+ 1.0;\nend\nendmodule\n"
        result = preprocess_vams(text)
        assert "__analog_placeholder__" in result.text
        assert len(result.analog_blocks) == 1
        assert "V(a)" in result.analog_blocks[0]

    def test_analog_single_statement(self) -> None:
        text = "module test (a);\nanalog V(a) <+ 1.0;\nendmodule\n"
        result = preprocess_vams(text)
        assert "__analog_placeholder__" in result.text
        assert len(result.analog_blocks) == 1

    def test_nested_begin_end(self) -> None:
        text = "module test (a);\nanalog begin\n  begin\n    V(a) <+ 1.0;\n  end\nend\nendmodule\n"
        result = preprocess_vams(text)
        assert len(result.analog_blocks) == 1
        assert "begin" in result.analog_blocks[0]
