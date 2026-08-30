from hubnet.netlist.hspice.parser import parse_hspice
from hubnet.netlist.hspice.writer import write_hspice


class TestHspiceRoundTrip:
    def test_resistor_divider(self) -> None:
        text = """\
.subckt divider vin vout gnd
R1 vin vout 10k
R2 vout gnd 10k
.ends divider
.end
"""
        self.assert_roundtrip(text)

    def test_mosfet_inverter(self) -> None:
        text = """\
.subckt inverter in_ out vdd vss
M1 out in_ vdd vdd pch W=1u L=0.18u
M2 out in_ vss vss nch W=0.5u L=0.18u
.ends inverter
.end
"""
        self.assert_roundtrip(text)

    def test_hierarchical(self) -> None:
        text = """\
.subckt inverter in_ out vdd vss
R1 in_ out 1k
R2 out vss 1k
.ends inverter

.subckt buffer a b vdd vss
X1 a mid vdd vss inverter
X2 mid b vdd vss inverter
.ends buffer
.end
"""
        self.assert_roundtrip(text)

    def test_write_parse_write_stable(self) -> None:
        text = """\
.subckt test a b c
R1 a b 10k
C1 b c 100p
.ends test
.end
"""
        circuit1 = parse_hspice(text)
        written1 = write_hspice(circuit1)
        circuit2 = parse_hspice(written1)
        written2 = write_hspice(circuit2)
        assert written1 == written2

    def assert_roundtrip(self, text: str) -> None:
        circuit1 = parse_hspice(text)
        written = write_hspice(circuit1)
        circuit2 = parse_hspice(written)

        assert circuit1.top_module == circuit2.top_module
        assert len(circuit1.modules) == len(circuit2.modules)

        for m1, m2 in zip(circuit1.modules, circuit2.modules):
            assert m1.name == m2.name
            assert [p.name for p in m1.ports] == [p.name for p in m2.ports]
            assert len(m1.module_references) == len(m2.module_references)
