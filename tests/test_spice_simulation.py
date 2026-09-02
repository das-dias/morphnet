from morphnet.morphnet_schema import AnalysisKind, OutputRequestKind
from morphnet.netlist.spice.parser import parse_spice
from morphnet.netlist.spice.writer import write_spice


class TestSpiceSimulationParsing:
    def test_op_analysis(self) -> None:
        text = """\
.op
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        assert len(circuit.simulation.analyses) == 1
        assert circuit.simulation.analyses[0].kind == AnalysisKind.OP

    def test_tran_analysis(self) -> None:
        text = """\
.tran 1n 10u
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        a = circuit.simulation.analyses[0]
        assert a.kind == AnalysisKind.TRAN
        assert a.arguments == ["1n", "10u"]

    def test_ac_analysis(self) -> None:
        text = """\
.ac DEC 10 1k 100G
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        a = circuit.simulation.analyses[0]
        assert a.kind == AnalysisKind.AC
        assert a.arguments == ["DEC", "10", "1k", "100G"]

    def test_dc_analysis(self) -> None:
        text = """\
.dc VDD 0 1.8 0.01
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        a = circuit.simulation.analyses[0]
        assert a.kind == AnalysisKind.DC
        assert a.arguments == ["VDD", "0", "1.8", "0.01"]

    def test_noise_analysis(self) -> None:
        text = """\
.noise V(out) VIN DEC 10 1 1G
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        a = circuit.simulation.analyses[0]
        assert a.kind == AnalysisKind.NOISE
        assert "V(out)" in a.arguments

    def test_print_statement(self) -> None:
        text = """\
.print TRAN V(out) I(R1)
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        req = circuit.simulation.output_requests[0]
        assert req.kind == OutputRequestKind.PRINT
        assert req.analysis_type == "TRAN"
        assert req.variables == ["V(out)", "I(R1)"]

    def test_plot_statement(self) -> None:
        text = """\
.plot DC V(out)
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        req = circuit.simulation.output_requests[0]
        assert req.kind == OutputRequestKind.PLOT
        assert req.analysis_type == "DC"

    def test_probe_statement(self) -> None:
        text = """\
.probe TRAN V(out) V(in)
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        req = circuit.simulation.output_requests[0]
        assert req.kind == OutputRequestKind.PROBE

    def test_meas_statement(self) -> None:
        text = """\
.meas TRAN delay MAX V(out)
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        m = circuit.simulation.measurements[0]
        assert m.analysis_type == "TRAN"
        assert m.name == "delay"

    def test_ic_statement(self) -> None:
        text = """\
.ic V(out)=0 V(in)=1.8
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        ic = circuit.simulation.initial_conditions
        assert ic is not None
        assert ic.conditions["V(out)"] == "0"
        assert ic.conditions["V(in)"] == "1.8"

    def test_nodeset_statement(self) -> None:
        text = """\
.nodeset V(net1)=0.9
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        ns = circuit.simulation.node_sets
        assert ns is not None
        assert ns.conditions["V(net1)"] == "0.9"

    def test_temp_statement(self) -> None:
        text = """\
.temp 27 -40 125
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        assert circuit.simulation.temperatures == [27.0, -40.0, 125.0]

    def test_multiple_analyses(self) -> None:
        text = """\
.op
.tran 1n 10u
.ac DEC 10 1k 1G
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        assert len(circuit.simulation.analyses) == 3
        kinds = [a.kind for a in circuit.simulation.analyses]
        assert kinds == [AnalysisKind.OP, AnalysisKind.TRAN, AnalysisKind.AC]

    def test_no_simulation(self) -> None:
        text = """\
.subckt test a b
R1 a b 1k
.ends test
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is None

    def test_full_netlist_with_simulation(self) -> None:
        text = """\
.subckt inverter vin vout vdd gnd
M1 vout vin vdd vdd pmos w=1u l=100n
M2 vout vin gnd gnd nmos w=500n l=100n
.ends inverter
X1 vin vout vdd 0 inverter
.tran 1n 20n
.print TRAN V(vin) V(vout)
.end
"""
        circuit = parse_spice(text)
        assert circuit.simulation is not None
        assert len(circuit.simulation.analyses) == 1
        assert circuit.simulation.analyses[0].kind == AnalysisKind.TRAN
        assert len(circuit.simulation.output_requests) == 1


class TestSpiceSimulationWriter:
    def test_write_tran(self) -> None:
        text = """\
.tran 1n 10u
.end
"""
        circuit = parse_spice(text)
        output = write_spice(circuit)
        assert ".tran 1n 10u" in output

    def test_write_ac(self) -> None:
        text = """\
.ac DEC 10 1k 100G
.end
"""
        circuit = parse_spice(text)
        output = write_spice(circuit)
        assert ".ac DEC 10 1k 100G" in output

    def test_write_op(self) -> None:
        text = """\
.op
.end
"""
        circuit = parse_spice(text)
        output = write_spice(circuit)
        assert ".op" in output

    def test_write_print(self) -> None:
        text = """\
.print TRAN V(out) I(R1)
.end
"""
        circuit = parse_spice(text)
        output = write_spice(circuit)
        assert ".print TRAN V(out) I(R1)" in output

    def test_write_ic(self) -> None:
        text = """\
.ic V(out)=0
.end
"""
        circuit = parse_spice(text)
        output = write_spice(circuit)
        assert ".ic V(out)=0" in output

    def test_write_temp(self) -> None:
        text = """\
.temp 27 -40 125
.end
"""
        circuit = parse_spice(text)
        output = write_spice(circuit)
        assert ".temp 27.0 -40.0 125.0" in output
