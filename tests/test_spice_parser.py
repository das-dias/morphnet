
from hubnet.hubnet_schema import SIPrefix
from hubnet.netlist.spice.parser import parse_spice


class TestBasicParsing:
    def test_resistor_divider(self) -> None:
        text = """\
.subckt divider vin vout gnd
R1 vin vout 10k
R2 vout gnd 10k
.ends divider
.end
"""
        circuit = parse_spice(text)
        assert circuit.domain == "spice"
        assert circuit.top_module == "divider"
        assert len(circuit.modules) == 1
        assert len(circuit.ext_modules) == 1
        assert circuit.ext_modules[0].name == "resistor"

    def test_subcircuit_ports(self) -> None:
        text = """\
.subckt mymod a b c
R1 a b 1k
.ends mymod
.end
"""
        circuit = parse_spice(text)
        m = circuit.modules[0]
        assert [p.name for p in m.ports] == ["a", "b", "c"]

    def test_instance_names_preserved(self) -> None:
        text = """\
.subckt test a b
R1 a b 1k
R2 a b 2k
.ends test
.end
"""
        circuit = parse_spice(text)
        m = circuit.modules[0]
        names = [r.name for r in m.module_references]
        assert names == ["R1", "R2"]

    def test_parameter_values(self) -> None:
        text = """\
.subckt test a b
R1 a b 10k
.ends test
.end
"""
        circuit = parse_spice(text)
        ref = circuit.modules[0].module_references[0]
        param = ref.parameter_overrides["value"]
        pv = param.default_value
        assert pv.prefixed_value is not None
        assert pv.prefixed_value.double_value == 10.0
        assert pv.prefixed_value.prefix == SIPrefix.KILO


class TestDeviceTypes:
    def test_capacitor(self) -> None:
        text = """\
.subckt test a b
C1 a b 100p
.ends test
.end
"""
        circuit = parse_spice(text)
        ref = circuit.modules[0].module_references[0]
        assert ref.module_name == "capacitor"
        pv = ref.parameter_overrides["value"].default_value
        assert pv.prefixed_value.prefix == SIPrefix.PICO

    def test_inductor(self) -> None:
        text = """\
.subckt test a b
L1 a b 10n
.ends test
.end
"""
        circuit = parse_spice(text)
        ref = circuit.modules[0].module_references[0]
        assert ref.module_name == "inductor"

    def test_mosfet(self) -> None:
        text = """\
.subckt test d g s b
M1 d g s b nch W=1u L=0.18u
.ends test
.end
"""
        circuit = parse_spice(text)
        ref = circuit.modules[0].module_references[0]
        assert ref.module_name == "mosfet"
        assert ref.model_name == "nch"
        assert "W" in ref.parameter_overrides
        assert "L" in ref.parameter_overrides

    def test_subcircuit_instance(self) -> None:
        text = """\
.subckt inner a b
R1 a b 1k
.ends inner

.subckt outer x y
X1 x y inner
.ends outer
.end
"""
        circuit = parse_spice(text)
        outer = next(m for m in circuit.modules if m.name == "outer")
        ref = outer.module_references[0]
        assert ref.name == "X1"
        assert ref.module_name == "inner"


class TestDirectives:
    def test_include(self) -> None:
        text = """\
.include "models.lib"
.subckt test a b
R1 a b 1k
.ends test
.end
"""
        circuit = parse_spice(text)
        includes = [d for d in circuit.directives if d.kind.name == "INCLUDE"]
        assert len(includes) >= 1
        assert includes[0].value == "models.lib"

    def test_global(self) -> None:
        text = """\
.global VDD VSS
.subckt test a b
R1 a b 1k
.ends test
.end
"""
        circuit = parse_spice(text)
        globals_ = [d for d in circuit.directives if d.kind.name == "GLOBAL"]
        assert len(globals_) >= 1
        assert globals_[0].value == "VDD VSS"

    def test_model_statement(self) -> None:
        text = """\
.model nch nmos level=49 vth0=0.4
.subckt test d g s b
M1 d g s b nch W=1u L=0.18u
.ends test
.end
"""
        circuit = parse_spice(text)
        ext_names = {e.name for e in circuit.ext_modules}
        assert "nch" in ext_names
        nch = next(e for e in circuit.ext_modules if e.name == "nch")
        assert nch.properties.get("model_type") == "nmos"

    def test_model_integer_param(self) -> None:
        text = """\
.model nch nmos level=49
.subckt test d g s b
M1 d g s b nch
.ends test
.end
"""
        circuit = parse_spice(text)
        nch = next(e for e in circuit.ext_modules if e.name == "nch")
        level_param = next(p for p in nch.parameters if p.name == "level")
        assert level_param.default_value is not None
        assert level_param.default_value.int_value == 49

    def test_param_statement(self) -> None:
        text = """\
.param vdd=1.8
.subckt test a b
R1 a b 1k
.ends test
.end
"""
        circuit = parse_spice(text)
        params = [d for d in circuit.directives if d.kind.name == "PARAM"]
        param_names = {d.name for d in params}
        assert "vdd" in param_names


class TestConnectivity:
    def test_net_connections(self) -> None:
        text = """\
.subckt test a b gnd
R1 a b 10k
R2 b gnd 10k
.ends test
.end
"""
        circuit = parse_spice(text)
        m = circuit.modules[0]
        # Should have connections for nets: a, b, gnd
        net_names = {c.name for c in m.connections}
        assert "a" in net_names
        assert "b" in net_names
        assert "gnd" in net_names

    def test_shared_net(self) -> None:
        """When two instances share a net, multiple connections reference it."""
        text = """\
.subckt test a b c
R1 a b 1k
R2 b c 2k
.ends test
.end
"""
        circuit = parse_spice(text)
        m = circuit.modules[0]
        b_conns = [c for c in m.connections if c.name == "b"]
        # b connects: module port b, R1.n, R2.p — should be 2 connections
        assert len(b_conns) >= 2

    def test_hierarchy_port_resolution(self) -> None:
        """X-instance port names should resolve from referenced subcircuit."""
        text = """\
.subckt child p q
R1 p q 1k
.ends child

.subckt parent a b
X1 a b child
.ends parent
.end
"""
        circuit = parse_spice(text)
        parent = next(m for m in circuit.modules if m.name == "parent")
        conns = parent.connections
        # X1 should have ports named 'p' and 'q' from child definition
        x1_ports = set()
        for c in conns:
            if c.source and c.source.instance_name == "X1":
                x1_ports.add(c.source.port_name)
            if c.target and c.target.instance_name == "X1":
                x1_ports.add(c.target.port_name)
        assert "p" in x1_ports
        assert "q" in x1_ports


class TestEdgeCases:
    def test_empty_subcircuit(self) -> None:
        text = """\
.subckt empty a b
.ends empty
.end
"""
        circuit = parse_spice(text)
        m = circuit.modules[0]
        assert m.name == "empty"
        assert len(m.module_references) == 0

    def test_no_end_statement(self) -> None:
        text = """\
.subckt test a b
R1 a b 1k
.ends test
"""
        circuit = parse_spice(text)
        assert len(circuit.modules) == 1

    def test_case_insensitive_keywords(self) -> None:
        text = """\
.SUBCKT Test A B
R1 A B 1k
.ENDS Test
.END
"""
        circuit = parse_spice(text)
        assert circuit.modules[0].name == "Test"
