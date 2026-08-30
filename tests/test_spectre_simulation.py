from hubnet.hubnet_schema import AnalysisKind, OutputRequestKind
from hubnet.netlist.spectre.parser import parse_spectre
from hubnet.netlist.spectre.writer import write_spectre


class TestSpectreSimulationParsing:
    def test_tran_analysis(self) -> None:
        text = "tran1 (0) tran stop=10u\n"
        circuit = parse_spectre(text)
        assert circuit.simulation is not None
        a = circuit.simulation.analyses[0]
        assert a.kind == AnalysisKind.TRAN
        assert a.name == "tran1"
        assert a.options.get("stop") == "10u"

    def test_dc_analysis(self) -> None:
        text = "dc1 (0) dc\n"
        circuit = parse_spectre(text)
        assert circuit.simulation is not None
        a = circuit.simulation.analyses[0]
        assert a.kind == AnalysisKind.DC
        assert a.name == "dc1"

    def test_ac_analysis(self) -> None:
        text = "ac1 (0) ac start=1 stop=1G dec=10\n"
        circuit = parse_spectre(text)
        assert circuit.simulation is not None
        a = circuit.simulation.analyses[0]
        assert a.kind == AnalysisKind.AC
        assert a.name == "ac1"

    def test_save_statement(self) -> None:
        text = "save out in\n"
        circuit = parse_spectre(text)
        assert circuit.simulation is not None
        req = circuit.simulation.output_requests[0]
        assert req.kind == OutputRequestKind.SAVE
        assert "out" in req.variables
        assert "in" in req.variables

    def test_multiple_analyses(self) -> None:
        text = "dc1 (0) dc\ntran1 (0) tran stop=10u\n"
        circuit = parse_spectre(text)
        assert circuit.simulation is not None
        assert len(circuit.simulation.analyses) == 2

    def test_no_simulation(self) -> None:
        text = """\
subckt inv (in out vdd gnd)
M0 (out in vdd vdd) pmos w=1u l=100n
M1 (out in gnd gnd) nmos w=500n l=100n
ends inv
"""
        circuit = parse_spectre(text)
        assert circuit.simulation is None

    def test_analysis_with_subcircuit(self) -> None:
        text = """\
subckt inv (in out vdd gnd)
M0 (out in vdd vdd) pmos w=1u l=100n
M1 (out in gnd gnd) nmos w=500n l=100n
ends inv
tran1 (0) tran stop=10u
save out
"""
        circuit = parse_spectre(text)
        assert circuit.simulation is not None
        assert len(circuit.simulation.analyses) == 1
        assert len(circuit.simulation.output_requests) == 1


class TestSpectreSimulationWriter:
    def test_write_tran(self) -> None:
        text = "tran1 (0) tran stop=10u\n"
        circuit = parse_spectre(text)
        output = write_spectre(circuit)
        assert "tran1 tran stop=10u" in output

    def test_write_save(self) -> None:
        text = "save out in\n"
        circuit = parse_spectre(text)
        output = write_spectre(circuit)
        assert "save out in" in output
