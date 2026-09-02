from morphnet.netlist.xyce.parser import parse_xyce
from morphnet.netlist.xyce.writer import write_xyce


class TestXyceTextRoundTrip:
    def test_resistor_divider(self) -> None:
        text = """\
.SUBCKT divider vin vout gnd
R1 vin vout 10k
R2 vout gnd 10k
.ENDS divider
.END
"""
        self.assert_roundtrip(text)

    def test_mosfet_inverter(self) -> None:
        text = """\
.SUBCKT inverter in out vdd vss
M1 out in vdd vdd pch W=1u L=0.18u
M2 out in vss vss nch W=0.5u L=0.18u
.ENDS inverter
.END
"""
        self.assert_roundtrip(text)

    def test_hierarchical(self) -> None:
        text = """\
.SUBCKT inverter in out vdd vss
R1 in out 1k
R2 out vss 1k
.ENDS inverter

.SUBCKT buffer a b vdd vss
X1 a mid vdd vss inverter
X2 mid b vdd vss inverter
.ENDS buffer
.END
"""
        self.assert_roundtrip(text)

    def test_write_parse_write_stable(self) -> None:
        text = """\
.SUBCKT test a b c
R1 a b 10k
C1 b c 100p
.ENDS test
.END
"""
        circuit1 = parse_xyce(text)
        written1 = write_xyce(circuit1)
        circuit2 = parse_xyce(written1)
        written2 = write_xyce(circuit2)
        assert written1 == written2

    def assert_roundtrip(self, text: str) -> None:
        circuit1 = parse_xyce(text)
        written = write_xyce(circuit1)
        circuit2 = parse_xyce(written)

        assert circuit1.top_module == circuit2.top_module
        assert len(circuit1.modules) == len(circuit2.modules)

        for m1, m2 in zip(circuit1.modules, circuit2.modules):
            assert m1.name == m2.name
            assert [p.name for p in m1.ports] == [p.name for p in m2.ports]
            assert len(m1.module_references) == len(m2.module_references)
            assert len(m1.connections) == len(m2.connections)
