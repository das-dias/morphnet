from hubnet.netlist.spectre.parser import parse_spectre


class TestBasicParsing:
    def test_resistor_subcircuit(self) -> None:
        text = """\
subckt divider (vin vout gnd)
R1 (vin vout) resistor r=10k
R2 (vout gnd) resistor r=10k
ends divider
"""
        circuit = parse_spectre(text)
        assert circuit.domain == "spectre"
        assert circuit.top_module == "divider"
        assert len(circuit.modules) == 1

    def test_port_names(self) -> None:
        text = """\
subckt mymod (a b c)
R1 (a b) resistor r=1k
ends mymod
"""
        circuit = parse_spectre(text)
        assert [p.name for p in circuit.modules[0].ports] == ["a", "b", "c"]

    def test_instance_params(self) -> None:
        text = """\
subckt test (a b)
R1 (a b) resistor r=10k
ends test
"""
        circuit = parse_spectre(text)
        ref = circuit.modules[0].module_references[0]
        assert "r" in ref.parameter_overrides


class TestDeviceTypes:
    def test_mosfet(self) -> None:
        text = """\
subckt inv (in out vdd vss)
M1 (out in vdd vdd) pch w=1u l=0.18u
M2 (out in vss vss) nch w=0.5u l=0.18u
ends inv
"""
        circuit = parse_spectre(text)
        refs = circuit.modules[0].module_references
        assert refs[0].module_name == "mosfet"
        assert refs[0].model_name == "pch"
        assert refs[1].model_name == "nch"

    def test_subcircuit_instance(self) -> None:
        text = """\
subckt inner (a b)
R1 (a b) resistor r=1k
ends inner

subckt outer (x y)
X1 (x y) inner
ends outer
"""
        circuit = parse_spectre(text)
        outer = next(m for m in circuit.modules if m.name == "outer")
        assert outer.module_references[0].module_name == "inner"


class TestDirectives:
    def test_include(self) -> None:
        text = """\
include "models.scs"
subckt test (a b)
R1 (a b) resistor r=1k
ends test
"""
        circuit = parse_spectre(text)
        includes = [d for d in circuit.directives if d.kind.name == "INCLUDE"]
        assert len(includes) >= 1
        assert includes[0].value == "models.scs"

    def test_model_statement(self) -> None:
        text = """\
model nch nmos (level=49 vth0=0.4)
subckt test (d g s b)
M1 (d g s b) nch w=1u l=0.18u
ends test
"""
        circuit = parse_spectre(text)
        ext_names = {e.name for e in circuit.ext_modules}
        assert "nch" in ext_names


class TestConnectivity:
    def test_hierarchy_port_resolution(self) -> None:
        text = """\
subckt child (p q)
R1 (p q) resistor r=1k
ends child

subckt parent (a b)
X1 (a b) child
ends parent
"""
        circuit = parse_spectre(text)
        parent = next(m for m in circuit.modules if m.name == "parent")
        x1_ports: set[str] = set()
        for c in parent.connections:
            if c.target and c.target.instance_name == "X1":
                x1_ports.add(c.target.port_name)
            if c.source and c.source.instance_name == "X1":
                x1_ports.add(c.source.port_name)
        assert "p" in x1_ports
        assert "q" in x1_ports
