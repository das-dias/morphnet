from morphnet.morphnet_schema import (
    Circuit,
    Connection,
    ExternalModule,
    Module,
    ModuleReference,
    Parameter,
    ParameterValue,
    Port,
    PortDirection,
    PortReference,
    PrefixedValue,
    SignalDomain,
    SIPrefix,
)
from morphnet.netlist.xyce.writer import write_xyce


def make_port(name: str) -> Port:
    return Port(
        name=name,
        direction=PortDirection.INOUT,
        domain=SignalDomain.ELECTRICAL,
    )


def make_pv(value: float, prefix: SIPrefix = SIPrefix.UNSPECIFIED) -> ParameterValue:
    return ParameterValue(
        prefixed_value=PrefixedValue(double_value=value, prefix=prefix)
    )


def make_conn(
    net: str, src_inst: str, src_port: str, tgt_inst: str, tgt_port: str
) -> Connection:
    return Connection(
        name=net,
        source=PortReference(instance_name=src_inst, port_name=src_port),
        target=PortReference(instance_name=tgt_inst, port_name=tgt_port),
    )


class TestXyceFormat:
    def test_basic_output(self) -> None:
        """Xyce output matches SPICE format."""
        resistor = ExternalModule(
            name="resistor",
            ports=[make_port("p"), make_port("n")],
            properties={"spice_prefix": "R"},
        )
        mod = Module(
            name="test",
            ports=[make_port("a"), make_port("b")],
            module_references=[
                ModuleReference(
                    name="R1",
                    module_name="resistor",
                    parameters=[
                        Parameter(
                            name="value",
                            default_value=make_pv(10.0, SIPrefix.KILO),
                        )
                    ],
                ),
            ],
            connections=[
                make_conn("a", "", "a", "R1", "p"),
                make_conn("b", "", "b", "R1", "n"),
            ],
        )
        circuit = Circuit(
            name="test",
            top_module="test",
            modules=[mod],
            ext_modules=[resistor],
        )
        output = write_xyce(circuit)
        assert ".subckt test a b" in output
        assert "R1 a b 10k" in output
        assert ".ends test" in output
