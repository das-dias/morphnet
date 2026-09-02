from morphnet.netlist.spectre_spice.parser import parse_spectre_spice


class TestPureSpiceMode:
    def test_pure_spice(self) -> None:
        text = """\
.subckt test a b
R1 a b 1k
.ends test
.end
"""
        circuit = parse_spectre_spice(text)
        assert circuit.domain == "spectre_spice"
        assert circuit.top_module == "test"
        assert len(circuit.modules) == 1

    def test_spice_devices(self) -> None:
        text = """\
.subckt test d g s b
M1 d g s b nch W=1u L=0.18u
.ends test
.end
"""
        circuit = parse_spectre_spice(text)
        ref = circuit.modules[0].module_references[0]
        assert ref.module_name == "mosfet"
        assert ref.model_name == "nch"


class TestMixedMode:
    def test_spice_then_spectre(self) -> None:
        text = """\
.subckt spice_mod a b
R1 a b 1k
.ends spice_mod

simulator lang=spectre

subckt spectre_mod (a b)
R0 (a b) resistor r=1k
ends spectre_mod
"""
        circuit = parse_spectre_spice(text)
        mod_names = {m.name for m in circuit.modules}
        assert "spice_mod" in mod_names
        assert "spectre_mod" in mod_names
        assert len(circuit.modules) == 2

    def test_three_sections(self) -> None:
        text = """\
.subckt s1 a b
R1 a b 1k
.ends s1

simulator lang=spectre

subckt s2 (a b)
R0 (a b) resistor r=2k
ends s2

simulator lang=spice

.subckt s3 a b
R2 a b 3k
.ends s3
"""
        circuit = parse_spectre_spice(text)
        mod_names = [m.name for m in circuit.modules]
        assert "s1" in mod_names
        assert "s2" in mod_names
        assert "s3" in mod_names
        assert circuit.top_module == "s3"

    def test_directives_from_both_sections(self) -> None:
        text = """\
.include "spice_models.lib"

simulator lang=spectre

include "spectre_models.scs"

subckt test (a b)
R0 (a b) resistor r=1k
ends test
"""
        circuit = parse_spectre_spice(text)
        include_values = {d.value for d in circuit.directives if d.kind.name == "INCLUDE"}
        assert "spice_models.lib" in include_values
        assert "spectre_models.scs" in include_values
