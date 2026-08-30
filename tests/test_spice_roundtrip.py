from hubnet.netlist.spice.parser import parse_spice
from hubnet.netlist.spice.writer import write_spice


class TestSpiceTextRoundTrip:
    """Parse SPICE text → write → parse again → assert structural equality."""

    def test_resistor_divider(self) -> None:
        text = """\
.subckt divider vin vout gnd
R1 vin vout 10k
R2 vout gnd 10k
.ends divider
.end
"""
        self.assert_roundtrip(text)

    def test_rc_filter(self) -> None:
        text = """\
.subckt rc_lowpass in_ out gnd
R1 in_ out 1k
C1 out gnd 100p
.ends rc_lowpass
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

    def test_with_directives(self) -> None:
        text = """\
.include "models.lib"
.global VDD VSS
.model nch nmos level=49 vth0=0.4

.subckt test a b
R1 a b 10k
.ends test
.end
"""
        self.assert_roundtrip(text)

    def test_write_parse_write_stable(self) -> None:
        """Second write produces identical text to first write."""
        text = """\
.subckt test a b c
R1 a b 10k
C1 b c 100p
.ends test
.end
"""
        circuit1 = parse_spice(text)
        written1 = write_spice(circuit1)
        circuit2 = parse_spice(written1)
        written2 = write_spice(circuit2)
        assert written1 == written2

    def assert_roundtrip(self, text: str) -> None:
        """Parse → write → parse → assert circuits are structurally equal."""
        circuit1 = parse_spice(text)
        written = write_spice(circuit1)
        circuit2 = parse_spice(written)

        assert circuit1.top_module == circuit2.top_module
        assert len(circuit1.modules) == len(circuit2.modules)
        assert len(circuit1.ext_modules) == len(circuit2.ext_modules)

        for m1, m2 in zip(circuit1.modules, circuit2.modules):
            assert m1.name == m2.name
            assert [p.name for p in m1.ports] == [p.name for p in m2.ports]
            assert len(m1.module_references) == len(m2.module_references)
            assert len(m1.connections) == len(m2.connections)

            for r1, r2 in zip(m1.module_references, m2.module_references):
                assert r1.name == r2.name
                assert r1.module_name == r2.module_name
                assert r1.parameter_overrides == r2.parameter_overrides
                assert r1.properties == r2.properties
