from morphnet.morphnet_schema import DirectiveKind, ExternalModuleKind
from morphnet.netlist.vams.parser import parse_vams


class TestBasicParsing:
    def test_simple_module(self) -> None:
        text = """\
module divider (vin, vout, gnd);
  inout vin, vout, gnd;
  electrical vin, vout, gnd;
  resistor #(.r(10k)) R1 (.p(vin), .n(vout));
  resistor #(.r(10k)) R2 (.p(vout), .n(gnd));
endmodule
"""
        circuit = parse_vams(text)
        assert circuit.domain == "vams"
        assert circuit.top_module == "divider"
        assert len(circuit.modules) == 1
        mod = circuit.modules[0]
        assert mod.name == "divider"
        assert len(mod.ports) == 3
        assert len(mod.module_references) == 2

    def test_port_directions(self) -> None:
        text = """\
module amp (inp, inn, out, vdd, vss);
  input inp, inn;
  output out;
  inout vdd, vss;
  electrical inp, inn, out, vdd, vss;
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        dirs = {p.name: p.direction.name for p in mod.ports}
        assert dirs["inp"] == "INPUT"
        assert dirs["inn"] == "INPUT"
        assert dirs["out"] == "OUTPUT"
        assert dirs["vdd"] == "INOUT"

    def test_port_disciplines(self) -> None:
        text = """\
module test (a, b);
  inout a, b;
  electrical a, b;
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        for port in mod.ports:
            assert port.discipline == "electrical"


class TestParameters:
    def test_typed_real_parameter(self) -> None:
        text = """\
module test (a);
  inout a;
  parameter real r = 50;
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        assert len(mod.parameters) == 1
        p = mod.parameters[0]
        assert p.name == "r"
        assert p.properties.get("type") == "real"
        assert p.default_value is not None
        assert p.default_value.prefixed_value is not None

    def test_typed_integer_parameter(self) -> None:
        text = """\
module test (a);
  inout a;
  parameter integer n = 4;
endmodule
"""
        circuit = parse_vams(text)
        p = circuit.modules[0].parameters[0]
        assert p.name == "n"
        assert p.properties.get("type") == "integer"
        assert p.default_value is not None
        assert p.default_value.int_value == 4

    def test_untyped_parameter(self) -> None:
        text = """\
module test (a);
  inout a;
  parameter x = 100;
endmodule
"""
        circuit = parse_vams(text)
        p = circuit.modules[0].parameters[0]
        assert p.name == "x"
        assert p.properties.get("type", "") == ""

    def test_localparam(self) -> None:
        text = """\
module test (a);
  inout a;
  localparam real pi = 3.14;
endmodule
"""
        circuit = parse_vams(text)
        p = circuit.modules[0].parameters[0]
        assert p.name == "pi"
        assert p.properties.get("localparam") == "true"
        assert p.properties.get("type") == "real"


class TestInstances:
    def test_named_ports_and_params(self) -> None:
        text = """\
module test (a, b);
  inout a, b;
  electrical a, b;
  resistor #(.r(10k)) R1 (.p(a), .n(b));
endmodule
"""
        circuit = parse_vams(text)
        ref = circuit.modules[0].module_references[0]
        assert ref.name == "R1"
        assert ref.module_name == "resistor"
        assert "r" in ref.parameter_overrides
        param = ref.parameter_overrides["r"]
        assert param.default_value.prefixed_value is not None

    def test_positional_ports(self) -> None:
        text = """\
module test (a, b);
  inout a, b;
  electrical a, b;
  resistor #(.r(1k)) R1 (a, b);
endmodule
"""
        circuit = parse_vams(text)
        ref = circuit.modules[0].module_references[0]
        assert ref.name == "R1"
        assert ref.module_name == "resistor"
        assert len(circuit.modules[0].connections) > 0

    def test_no_param_override(self) -> None:
        text = """\
module test (a, b);
  inout a, b;
  electrical a, b;
  mysubckt X1 (.p(a), .n(b));
endmodule
"""
        circuit = parse_vams(text)
        ref = circuit.modules[0].module_references[0]
        assert ref.name == "X1"
        assert ref.module_name == "mysubckt"
        assert len(ref.parameter_overrides) == 0


class TestDirectives:
    def test_include(self) -> None:
        text = """\
`include "constants.vams"
module test (a);
  inout a;
endmodule
"""
        circuit = parse_vams(text)
        includes = [d for d in circuit.directives if d.kind == DirectiveKind.INCLUDE]
        assert len(includes) == 1
        assert includes[0].value == "constants.vams"

    def test_timescale(self) -> None:
        text = """\
`timescale 1ns/1ps
module test (a);
  inout a;
endmodule
"""
        circuit = parse_vams(text)
        ts = [d for d in circuit.directives if d.kind == DirectiveKind.TIMESCALE]
        assert len(ts) == 1
        assert ts[0].value == "1ns/1ps"


class TestNatureAndDiscipline:
    def test_nature(self) -> None:
        text = """\
nature Voltage;
  units = "V";
  access = V;
  abstol = 1u;
endnature
module test (a);
  inout a;
endmodule
"""
        circuit = parse_vams(text)
        ext_names = {e.name for e in circuit.ext_modules}
        assert "Voltage" in ext_names
        voltage = next(e for e in circuit.ext_modules if e.name == "Voltage")
        assert voltage.kind == ExternalModuleKind.NATURE
        assert "nature_units" in voltage.properties

    def test_discipline(self) -> None:
        text = """\
discipline electrical;
  potential Voltage;
  flow Current;
  domain continuous;
enddiscipline
module test (a);
  inout a;
endmodule
"""
        circuit = parse_vams(text)
        ext_names = {e.name for e in circuit.ext_modules}
        assert "electrical" in ext_names
        elec = next(e for e in circuit.ext_modules if e.name == "electrical")
        assert elec.kind == ExternalModuleKind.DISCIPLINE
        assert elec.properties.get("discipline_potential") == "Voltage"
        assert elec.properties.get("discipline_flow") == "Current"
        assert elec.properties.get("discipline_domain") == "continuous"


class TestGroundAndAnalog:
    def test_ground(self) -> None:
        text = """\
module test (a);
  inout a;
  electrical a;
  ground gnd;
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        assert mod.properties.get("ground_net") == "gnd"

    def test_analog_block(self) -> None:
        text = """\
module test (a);
  inout a;
  electrical a;
  analog begin
    V(a) <+ 1.0;
  end
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        assert "analog_block" in mod.properties
        assert "V(a)" in mod.properties["analog_block"]


class TestConnectivity:
    def test_named_port_connections(self) -> None:
        text = """\
module test (a, b, gnd);
  inout a, b, gnd;
  electrical a, b, gnd;
  resistor #(.r(10k)) R1 (.p(a), .n(b));
  resistor #(.r(10k)) R2 (.p(b), .n(gnd));
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        assert len(mod.connections) > 0
        conn_nets = {c.name for c in mod.connections}
        assert "a" in conn_nets
        assert "b" in conn_nets
        assert "gnd" in conn_nets


class TestMultipleModules:
    def test_two_modules(self) -> None:
        text = """\
module inner (p, n);
  inout p, n;
  electrical p, n;
endmodule

module outer (a, b);
  inout a, b;
  electrical a, b;
  inner X1 (.p(a), .n(b));
endmodule
"""
        circuit = parse_vams(text)
        assert len(circuit.modules) == 2
        assert circuit.top_module == "outer"


class TestAnalogBlockDirectives:
    def test_analog_begin_end_stored(self) -> None:
        text = """\
module vsrc (p, n);
  inout p, n;
  electrical p, n;
  parameter real vdc = 1.0;
  analog begin
    V(p, n) <+ vdc;
  end
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        assert "analog_block" in mod.properties
        block = mod.properties["analog_block"]
        assert "V(p, n)" in block
        assert "vdc" in block

    def test_analog_single_statement(self) -> None:
        text = """\
module vsrc (p, n);
  inout p, n;
  electrical p, n;
  analog V(p, n) <+ 1.0;
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        assert "analog_block" in mod.properties
        assert "V(p, n)" in mod.properties["analog_block"]

    def test_analog_with_nested_begin_end(self) -> None:
        text = """\
module ctrl (out);
  output out;
  electrical out;
  analog begin
    if (V(out) > 0.5) begin
      I(out) <+ 1m;
    end
  end
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        assert "analog_block" in mod.properties
        block = mod.properties["analog_block"]
        assert "if" in block
        assert "I(out)" in block

    def test_module_with_analog_and_instances(self) -> None:
        text = """\
module amp (inp, out, vdd, gnd);
  inout inp, out, vdd, gnd;
  electrical inp, out, vdd, gnd;
  parameter real gain = 10;
  resistor #(.r(1k)) R1 (.p(inp), .n(out));
  analog begin
    V(out) <+ gain * V(inp);
  end
endmodule
"""
        circuit = parse_vams(text)
        mod = circuit.modules[0]
        assert len(mod.module_references) == 1
        assert mod.module_references[0].name == "R1"
        assert "analog_block" in mod.properties
        assert "gain" in mod.properties["analog_block"]


class TestParamset:
    def test_paramset(self) -> None:
        text = """\
paramset myres resistor;
  parameter real r = 100;
endparamset
module test (a, b);
  inout a, b;
  electrical a, b;
endmodule
"""
        circuit = parse_vams(text)
        ext_names = {e.name for e in circuit.ext_modules}
        assert "myres" in ext_names
        myres = next(e for e in circuit.ext_modules if e.name == "myres")
        assert myres.kind == ExternalModuleKind.MODEL
        assert myres.properties.get("model_type") == "resistor"
