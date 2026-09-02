from morphnet.netlist.spectre_spice.preprocess import preprocess_spectre_spice


class TestDefaultMode:
    def test_pure_spice(self) -> None:
        sections = preprocess_spectre_spice("R1 a b 1k\n")
        assert len(sections) == 1
        assert sections[0].language == "spice"
        assert "R1 a b 1k" in sections[0].text


class TestLanguageSwitching:
    def test_switch_to_spectre(self) -> None:
        text = "R1 a b 1k\nsimulator lang=spectre\nR0 (a b) resistor r=1k\n"
        sections = preprocess_spectre_spice(text)
        assert len(sections) == 2
        assert sections[0].language == "spice"
        assert sections[1].language == "spectre"

    def test_switch_back_to_spice(self) -> None:
        text = """\
.subckt s1 a b
R1 a b 1k
.ends s1
simulator lang=spectre
subckt s2 (a b)
R0 (a b) resistor r=1k
ends s2
simulator lang=spice
.subckt s3 a b
R2 a b 2k
.ends s3
"""
        sections = preprocess_spectre_spice(text)
        assert len(sections) == 3
        assert sections[0].language == "spice"
        assert sections[1].language == "spectre"
        assert sections[2].language == "spice"

    def test_case_insensitive(self) -> None:
        text = "SIMULATOR LANG=SPECTRE\nR0 (a b) resistor r=1k\n"
        sections = preprocess_spectre_spice(text)
        assert len(sections) == 1
        assert sections[0].language == "spectre"

    def test_empty_section_skipped(self) -> None:
        text = "simulator lang=spectre\nsimulator lang=spice\nR1 a b 1k\n"
        sections = preprocess_spectre_spice(text)
        non_empty = [s for s in sections if s.text.strip()]
        assert len(non_empty) == 1
        assert non_empty[0].language == "spice"
