import pytest

from hubnet.hubnet_schema import SIPrefix
from hubnet.netlist.hspice.parser import parse_hspice


class TestBasicParsing:
    def test_standard_subckt(self) -> None:
        text = """\
.subckt divider vin vout gnd
R1 vin vout 10k
R2 vout gnd 10k
.ends divider
.end
"""
        circuit = parse_hspice(text)
        assert circuit.domain == "hspice"
        assert circuit.top_module == "divider"
        assert len(circuit.modules) == 1

    def test_macro_eom(self) -> None:
        text = """\
.macro mymod a b
R1 a b 10k
.eom mymod
.end
"""
        circuit = parse_hspice(text)
        assert circuit.top_module == "mymod"
        m = circuit.modules[0]
        assert m.name == "mymod"
        assert len(m.module_references) == 1

    def test_macro_ports(self) -> None:
        text = """\
.macro amp inp inn out vdd vss
R1 inp out 1k
.eom amp
.end
"""
        circuit = parse_hspice(text)
        m = circuit.modules[0]
        assert [p.name for p in m.ports] == ["inp", "inn", "out", "vdd", "vss"]

    def test_macro_with_params(self) -> None:
        text = """\
.macro myres a b r=1k
R1 a b 1k
.eom myres
.end
"""
        circuit = parse_hspice(text)
        m = circuit.modules[0]
        assert any(p.name == "r" for p in m.parameters)


class TestExpressionParams:
    def test_quoted_expression(self) -> None:
        text = """\
.subckt test a b
.param r='1k+2k'
R1 a b 10k
.ends test
.end
"""
        circuit = parse_hspice(text)
        m = circuit.modules[0]
        rparam = next(p for p in m.parameters if p.name == "r")
        assert rparam.default_value is not None
        assert rparam.default_value.expression == "1k+2k"

    def test_quoted_string_no_operators(self) -> None:
        text = """\
.subckt test a b
.param name='mystring'
R1 a b 10k
.ends test
.end
"""
        circuit = parse_hspice(text)
        m = circuit.modules[0]
        nparam = next(p for p in m.parameters if p.name == "name")
        assert nparam.default_value is not None
        assert nparam.default_value.string_value == "mystring"

    def test_complex_expression(self) -> None:
        text = """\
.subckt test a b
.param gain='(vdd/2)*ratio'
R1 a b 10k
.ends test
.end
"""
        circuit = parse_hspice(text)
        m = circuit.modules[0]
        gparam = next(p for p in m.parameters if p.name == "gain")
        assert gparam.default_value is not None
        assert gparam.default_value.expression == "(vdd/2)*ratio"


class TestSuffixes:
    def test_mil_suffix(self) -> None:
        text = """\
.subckt test a b
R1 a b 25mil
.ends test
.end
"""
        circuit = parse_hspice(text)
        ref = circuit.modules[0].module_references[0]
        pv = ref.parameter_overrides["value"].default_value
        assert pv.prefixed_value is not None
        assert pv.prefixed_value.double_value == pytest.approx(25 * 25.4e-6)

    def test_x_suffix_as_mega(self) -> None:
        text = """\
.subckt test a b
R1 a b 1x
.ends test
.end
"""
        circuit = parse_hspice(text)
        ref = circuit.modules[0].module_references[0]
        pv = ref.parameter_overrides["value"].default_value
        assert pv.prefixed_value is not None
        assert pv.prefixed_value.prefix == SIPrefix.MEGA


class TestDeviceTypes:
    def test_mosfet(self) -> None:
        text = """\
.subckt test d g s b
M1 d g s b nch W=1u L=0.18u
.ends test
.end
"""
        circuit = parse_hspice(text)
        ref = circuit.modules[0].module_references[0]
        assert ref.module_name == "mosfet"
        assert ref.model_name == "nch"


class TestDirectives:
    def test_include(self) -> None:
        text = """\
.include "models.lib"
.subckt test a b
R1 a b 1k
.ends test
.end
"""
        circuit = parse_hspice(text)
        includes = [d for d in circuit.directives if d.kind.name == "INCLUDE"]
        assert len(includes) >= 1
        assert includes[0].value == "models.lib"

    def test_model_statement(self) -> None:
        text = """\
.model nch nmos level=49 vth0=0.4
.subckt test d g s b
M1 d g s b nch W=1u L=0.18u
.ends test
.end
"""
        circuit = parse_hspice(text)
        nch = next(e for e in circuit.ext_modules if e.name == "nch")
        level = next(p for p in nch.parameters if p.name == "level")
        assert level.default_value is not None
        assert level.default_value.int_value == 49


class TestConnectivity:
    def test_net_connections(self) -> None:
        text = """\
.subckt test a b gnd
R1 a b 10k
R2 b gnd 10k
.ends test
.end
"""
        circuit = parse_hspice(text)
        m = circuit.modules[0]
        net_names = {c.name for c in m.connections}
        assert "a" in net_names
        assert "b" in net_names
        assert "gnd" in net_names
