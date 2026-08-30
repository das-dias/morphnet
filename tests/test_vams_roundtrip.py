from hubnet.netlist.vams.parser import parse_vams
from hubnet.netlist.vams.writer import write_vams


class TestRoundtrip:
    def test_simple_resistor_divider(self) -> None:
        text = """\
module divider (vin, vout, gnd);
  inout vin, vout, gnd;
  electrical vin, vout, gnd;
  resistor #(.r(10k)) R1 (.p(vin), .n(vout));
  resistor #(.r(10k)) R2 (.p(vout), .n(gnd));
endmodule
"""
        circuit1 = parse_vams(text)
        output = write_vams(circuit1)
        circuit2 = parse_vams(output)

        assert circuit1.top_module == circuit2.top_module
        assert len(circuit1.modules) == len(circuit2.modules)

        m1, m2 = circuit1.modules[0], circuit2.modules[0]
        assert m1.name == m2.name
        assert [p.name for p in m1.ports] == [p.name for p in m2.ports]
        assert len(m1.module_references) == len(m2.module_references)

    def test_with_parameters(self) -> None:
        text = """\
module test (a, b);
  inout a, b;
  electrical a, b;
  parameter real r = 1k;
  resistor #(.r(r)) R1 (.p(a), .n(b));
endmodule
"""
        circuit1 = parse_vams(text)
        output = write_vams(circuit1)
        circuit2 = parse_vams(output)

        p1 = circuit1.modules[0].parameters[0]
        p2 = circuit2.modules[0].parameters[0]
        assert p1.name == p2.name
        assert p1.properties.get("type") == p2.properties.get("type")

    def test_include_directive(self) -> None:
        text = """\
`include "constants.vams"
module test (a);
  inout a;
  electrical a;
endmodule
"""
        circuit1 = parse_vams(text)
        output = write_vams(circuit1)
        circuit2 = parse_vams(output)

        inc1 = [d for d in circuit1.directives if d.kind.name == "INCLUDE"]
        inc2 = [d for d in circuit2.directives if d.kind.name == "INCLUDE"]
        assert len(inc1) == len(inc2)
        assert inc1[0].value == inc2[0].value

    def test_port_directions_preserved(self) -> None:
        text = """\
module amp (inp, out, vdd);
  input inp;
  output out;
  inout vdd;
  electrical inp, out, vdd;
endmodule
"""
        circuit1 = parse_vams(text)
        output = write_vams(circuit1)
        circuit2 = parse_vams(output)

        dirs1 = {p.name: p.direction for p in circuit1.modules[0].ports}
        dirs2 = {p.name: p.direction for p in circuit2.modules[0].ports}
        assert dirs1 == dirs2

    def test_disciplines_preserved(self) -> None:
        text = """\
module test (a, b);
  inout a, b;
  electrical a, b;
endmodule
"""
        circuit1 = parse_vams(text)
        output = write_vams(circuit1)
        circuit2 = parse_vams(output)

        discs1 = {p.name: p.discipline for p in circuit1.modules[0].ports}
        discs2 = {p.name: p.discipline for p in circuit2.modules[0].ports}
        assert discs1 == discs2
