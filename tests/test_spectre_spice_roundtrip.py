from morphnet.netlist.spectre_spice.parser import parse_spectre_spice
from morphnet.netlist.spectre_spice.writer import write_spectre_spice


class TestSpectreSpiceRoundTrip:
    def test_pure_spice_roundtrip(self) -> None:
        text = """\
.subckt test a b
R1 a b 10k
.ends test
.end
"""
        circuit1 = parse_spectre_spice(text)
        written = write_spectre_spice(circuit1)
        circuit2 = parse_spectre_spice(written)

        assert circuit1.top_module == circuit2.top_module
        assert len(circuit1.modules) == len(circuit2.modules)

        m1 = circuit1.modules[0]
        m2 = circuit2.modules[0]
        assert m1.name == m2.name
        assert [p.name for p in m1.ports] == [p.name for p in m2.ports]
        assert len(m1.module_references) == len(m2.module_references)

    def test_write_parse_write_stable(self) -> None:
        text = """\
.subckt test a b c
R1 a b 10k
C1 b c 100p
.ends test
.end
"""
        circuit1 = parse_spectre_spice(text)
        written1 = write_spectre_spice(circuit1)
        circuit2 = parse_spectre_spice(written1)
        written2 = write_spectre_spice(circuit2)
        assert written1 == written2
