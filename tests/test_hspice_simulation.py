from hubnet.hubnet_schema import AnalysisKind
from hubnet.netlist.hspice.parser import parse_hspice


class TestHspiceSimulationParsing:
    def test_fft_analysis(self) -> None:
        text = """\
.fft V(out) NP=1024 START=0 STOP=10u
.end
"""
        circuit = parse_hspice(text)
        assert circuit.simulation is not None
        a = circuit.simulation.analyses[0]
        assert a.kind == AnalysisKind.FFT
        assert "V(out)" in a.arguments
        assert a.options.get("NP") == "1024"

    def test_tran_analysis(self) -> None:
        text = """\
.tran 1n 10u
.end
"""
        circuit = parse_hspice(text)
        assert circuit.simulation is not None
        a = circuit.simulation.analyses[0]
        assert a.kind == AnalysisKind.TRAN
        assert a.arguments == ["1n", "10u"]

    def test_inherited_op(self) -> None:
        text = """\
.op
.end
"""
        circuit = parse_hspice(text)
        assert circuit.simulation is not None
        assert circuit.simulation.analyses[0].kind == AnalysisKind.OP

    def test_hspice_macro_with_simulation(self) -> None:
        text = """\
.macro inv vin vout vdd gnd
M1 vout vin vdd vdd pmos w=1u l=100n
M2 vout vin gnd gnd nmos w=500n l=100n
.eom inv
.tran 1n 10u
.print TRAN V(vout)
.end
"""
        circuit = parse_hspice(text)
        assert circuit.simulation is not None
        assert len(circuit.simulation.analyses) == 1
        assert len(circuit.simulation.output_requests) == 1
