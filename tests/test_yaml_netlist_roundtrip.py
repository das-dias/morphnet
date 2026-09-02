from __future__ import annotations

from pathlib import Path

import pytest

from morphnet.morphnet_schema import Circuit
from morphnet.netlist.hspice.parser import parse_hspice
from morphnet.netlist.hspice.writer import write_hspice
from morphnet.netlist.spectre.parser import parse_spectre
from morphnet.netlist.spectre.writer import write_spectre
from morphnet.netlist.vams.parser import parse_vams
from morphnet.netlist.vams.writer import write_vams

NETLISTS_DIR = Path(__file__).parent / "netlists"

YAML_STEMS = [
    "rc_lowpass",
    "resistor_divider",
    "hierarchical_subckt",
    "inverter_with_models",
]


def load_yaml_circuit(stem: str) -> Circuit:
    return Circuit.from_yaml((NETLISTS_DIR / f"{stem}.yaml").read_text())


def assert_modules_match(c1: Circuit, c2: Circuit) -> None:
    assert len(c1.modules) == len(c2.modules)
    for m1, m2 in zip(c1.modules, c2.modules):
        assert m1.name == m2.name
        assert [p.name for p in m1.ports] == [p.name for p in m2.ports]
        assert len(m1.module_references) == len(m2.module_references)
        for r1, r2 in zip(m1.module_references, m2.module_references):
            assert r1.name == r2.name
            assert r1.module_name == r2.module_name


class TestYamlToHspice:
    @pytest.mark.parametrize("stem", YAML_STEMS)
    def test_yaml_to_hspice_roundtrip(self, stem: str) -> None:
        circuit = load_yaml_circuit(stem)
        hspice_text = write_hspice(circuit)
        parsed = parse_hspice(hspice_text)
        assert_modules_match(circuit, parsed)

    @pytest.mark.parametrize("stem", YAML_STEMS)
    def test_hspice_write_parse_write_stable(self, stem: str) -> None:
        circuit = load_yaml_circuit(stem)
        text1 = write_hspice(circuit)
        text2 = write_hspice(parse_hspice(text1))
        assert text1 == text2

    @pytest.mark.parametrize("stem", YAML_STEMS)
    def test_hspice_matches_golden(self, stem: str) -> None:
        circuit = load_yaml_circuit(stem)
        actual = write_hspice(circuit)
        golden = (NETLISTS_DIR / "hspice" / f"{stem}.sp").read_text()
        assert actual == golden


class TestYamlToSpectre:
    @pytest.mark.parametrize("stem", YAML_STEMS)
    def test_yaml_to_spectre_roundtrip(self, stem: str) -> None:
        circuit = load_yaml_circuit(stem)
        spectre_text = write_spectre(circuit)
        parsed = parse_spectre(spectre_text)
        assert_modules_match(circuit, parsed)

    @pytest.mark.parametrize("stem", YAML_STEMS)
    def test_spectre_write_parse_write_stable(self, stem: str) -> None:
        circuit = load_yaml_circuit(stem)
        text1 = write_spectre(circuit)
        text2 = write_spectre(parse_spectre(text1))
        assert text1 == text2

    @pytest.mark.parametrize("stem", YAML_STEMS)
    def test_spectre_matches_golden(self, stem: str) -> None:
        circuit = load_yaml_circuit(stem)
        actual = write_spectre(circuit)
        golden = (NETLISTS_DIR / "spectre" / f"{stem}.scs").read_text()
        assert actual == golden


class TestYamlToVams:
    @pytest.mark.parametrize("stem", YAML_STEMS)
    def test_yaml_to_vams_roundtrip(self, stem: str) -> None:
        circuit = load_yaml_circuit(stem)
        vams_text = write_vams(circuit)
        parsed = parse_vams(vams_text)
        assert_modules_match(circuit, parsed)

    @pytest.mark.parametrize("stem", YAML_STEMS)
    def test_vams_write_parse_write_stable(self, stem: str) -> None:
        circuit = load_yaml_circuit(stem)
        text1 = write_vams(circuit)
        c2 = parse_vams(text1)
        text2 = write_vams(c2)
        c3 = parse_vams(text2)
        text3 = write_vams(c3)
        # parse→write may reorder ports on the first cycle, but must be
        # stable from the second cycle onward
        assert text2 == text3

    @pytest.mark.parametrize("stem", YAML_STEMS)
    def test_vams_matches_golden(self, stem: str) -> None:
        circuit = load_yaml_circuit(stem)
        actual = write_vams(circuit)
        golden = (NETLISTS_DIR / "vams" / f"{stem}.vams").read_text()
        assert actual == golden
