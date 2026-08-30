from hubnet.hubnet_schema import (
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
from hubnet.netlist.spectre.writer import write_spectre


def make_port(uid: int, name: str) -> Port:
    return Port(
        uid=uid,
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


class TestSpectreFormat:
    def test_subckt_with_parens(self) -> None:
        mod = Module(
            name="test",
            ports=[make_port(0, "a"), make_port(1, "b")],
        )
        circuit = Circuit(
            name="test", domain="spectre", top_module="test", modules=[mod]
        )
        output = write_spectre(circuit)
        assert "subckt test (a b)" in output
        assert "ends test" in output

    def test_instance_with_parens(self) -> None:
        resistor = ExternalModule(
            name="resistor",
            domain="spectre",
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
                        "r": Parameter(
                            name="r",
                            default_value=make_pv(10.0, SIPrefix.KILO),
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
            domain="spectre",
            top_module="test",
            modules=[mod],
            ext_modules=[resistor],
        )
        output = write_spectre(circuit)
        assert "R1 (a b) resistor r=10k" in output

    def test_x_instance(self) -> None:
        inner = Module(name="inner", ports=[make_port(0, "p"), make_port(1, "q")])
        outer = Module(
            name="outer",
            ports=[make_port(0, "a"), make_port(1, "b")],
            module_references=[ModuleReference(name="X1", module_name="inner")],
            connections=[
                make_conn("a", "", "a", "X1", "p"),
                make_conn("b", "", "b", "X1", "q"),
            ],
        )
        circuit = Circuit(
            name="test",
            domain="spectre",
            top_module="outer",
            modules=[inner, outer],
        )
        output = write_spectre(circuit)
        assert "X1 (a b) inner" in output
