from hubnet.hubnet_schema import (
    Circuit,
    Connection,
    Directive,
    DirectiveKind,
    ExternalModule,
    ExternalModuleKind,
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
from hubnet.netlist.vams.writer import write_vams


def make_pv(val: float, prefix: SIPrefix = SIPrefix.UNSPECIFIED) -> ParameterValue:
    return ParameterValue(prefixed_value=PrefixedValue(double_value=val, prefix=prefix))


def make_port(
    uid: int, name: str, direction: PortDirection = PortDirection.INOUT, discipline: str = "electrical"
) -> Port:
    return Port(uid=uid, name=name, direction=direction, domain=SignalDomain.ELECTRICAL, discipline=discipline)


def make_conn(net: str, src_inst: str, src_port: str, tgt_inst: str, tgt_port: str) -> Connection:
    return Connection(
        name=net,
        source=PortReference(instance_name=src_inst, port_name=src_port),
        target=PortReference(instance_name=tgt_inst, port_name=tgt_port),
    )


class TestModuleOutput:
    def test_simple_module(self) -> None:
        mod = Module(
            name="divider",
            ports=[make_port(0, "vin"), make_port(1, "vout"), make_port(2, "gnd")],
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
                make_conn("vin", "", "vin", "R1", "p"),
                make_conn("vout", "", "vout", "R1", "n"),
            ],
        )
        circuit = Circuit(
            name="",
            domain="vams",
            top_module="divider",
            modules=[mod],
        )
        output = write_vams(circuit)
        assert "module divider" in output
        assert "endmodule" in output
        assert "inout vin, vout, gnd;" in output
        assert "electrical vin, vout, gnd;" in output
        assert "resistor" in output
        assert "R1" in output


class TestDirectiveOutput:
    def test_include(self) -> None:
        circuit = Circuit(
            name="",
            domain="vams",
            directives=[Directive(kind=DirectiveKind.INCLUDE, value="models.vams")],
        )
        output = write_vams(circuit)
        assert '`include "models.vams"' in output

    def test_timescale(self) -> None:
        circuit = Circuit(
            name="",
            domain="vams",
            directives=[Directive(kind=DirectiveKind.TIMESCALE, value="1ns/1ps")],
        )
        output = write_vams(circuit)
        assert "`timescale 1ns/1ps" in output


class TestParameterOutput:
    def test_typed_parameter(self) -> None:
        mod = Module(
            name="test",
            ports=[make_port(0, "a")],
            parameters=[
                Parameter(
                    name="r",
                    default_value=make_pv(50.0),
                    properties={"type": "real"},
                ),
            ],
        )
        circuit = Circuit(name="", domain="vams", top_module="test", modules=[mod])
        output = write_vams(circuit)
        assert "parameter real r = 50" in output

    def test_integer_parameter(self) -> None:
        mod = Module(
            name="test",
            ports=[make_port(0, "a")],
            parameters=[
                Parameter(
                    name="n",
                    default_value=ParameterValue(int_value=4),
                    properties={"type": "integer"},
                ),
            ],
        )
        circuit = Circuit(name="", domain="vams", top_module="test", modules=[mod])
        output = write_vams(circuit)
        assert "parameter integer n = 4" in output


class TestNatureAndDisciplineOutput:
    def test_nature(self) -> None:
        ext = ExternalModule(
            name="Voltage",
            domain="vams",
            kind=ExternalModuleKind.NATURE,
            properties={"nature_units": "V", "nature_access": "V"},
        )
        circuit = Circuit(name="", domain="vams", ext_modules=[ext])
        output = write_vams(circuit)
        assert "nature Voltage;" in output
        assert "endnature" in output
        assert "units = V;" in output

    def test_discipline(self) -> None:
        ext = ExternalModule(
            name="electrical",
            domain="vams",
            kind=ExternalModuleKind.DISCIPLINE,
            properties={
                "discipline_potential": "Voltage",
                "discipline_flow": "Current",
                "discipline_domain": "continuous",
            },
        )
        circuit = Circuit(name="", domain="vams", ext_modules=[ext])
        output = write_vams(circuit)
        assert "discipline electrical;" in output
        assert "enddiscipline" in output
        assert "domain continuous;" in output
        assert "potential Voltage;" in output
