from hubnet.hubnet_schema import (
    Circuit,
    Connection,
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
from hubnet.netlist.hspice.writer import write_hspice


def make_port(uid: int, name: str) -> Port:
    return Port(
        uid=uid,
        name=name,
        direction=PortDirection.INOUT,
        domain=SignalDomain.ELECTRICAL,
    )


def make_conn(
    net: str, src_inst: str, src_port: str, tgt_inst: str, tgt_port: str
) -> Connection:
    return Connection(
        name=net,
        source=PortReference(instance_name=src_inst, port_name=src_port),
        target=PortReference(instance_name=tgt_inst, port_name=tgt_port),
    )


class TestBasicOutput:
    def test_simple_circuit(self) -> None:
        from hubnet.hubnet_schema import ExternalModule

        resistor = ExternalModule(
            name="resistor",
            domain="hspice",
            ports=[make_port(0, "p"), make_port(1, "n")],
            properties={"spice_prefix": "R"},
        )
        mod = Module(
            name="test",
            ports=[make_port(0, "a"), make_port(1, "b")],
            module_references=[
                ModuleReference(
                    name="R1",
                    module_name="resistor",
                    parameter_overrides={
                        "value": Parameter(
                            name="value",
                            default_value=ParameterValue(
                                prefixed_value=PrefixedValue(
                                    double_value=10.0, prefix=SIPrefix.KILO
                                )
                            ),
                        )
                    },
                ),
            ],
            connections=[
                make_conn("a", "", "a", "R1", "p"),
                make_conn("b", "", "b", "R1", "n"),
            ],
        )
        circuit = Circuit(
            name="test",
            domain="hspice",
            top_module="test",
            modules=[mod],
            ext_modules=[resistor],
        )
        output = write_hspice(circuit)
        assert "R1 a b 10k" in output
        assert ".subckt test a b" in output
        assert ".ends test" in output
        assert ".end" in output


class TestExpressionOutput:
    def test_expression_in_quotes(self) -> None:
        mod = Module(
            name="test",
            ports=[make_port(0, "a"), make_port(1, "b")],
            parameters=[
                Parameter(
                    name="r",
                    default_value=ParameterValue(expression="1k+2k"),
                ),
            ],
        )
        circuit = Circuit(
            name="test", domain="hspice", top_module="test", modules=[mod]
        )
        output = write_hspice(circuit)
        assert ".param r='1k+2k'" in output
