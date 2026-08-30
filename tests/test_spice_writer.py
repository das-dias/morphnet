from hubnet.hubnet_schema import (
    Circuit,
    Connection,
    Directive,
    DirectiveKind,
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
from hubnet.netlist.spice.writer import write_spice


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


class TestResistorOutput:
    def test_basic_resistor(self) -> None:
        resistor = ExternalModule(
            name="resistor",
            domain="spice",
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
            name="test_circuit",
            domain="spice",
            top_module="test",
            modules=[mod],
            ext_modules=[resistor],
        )
        output = write_spice(circuit)
        assert ".subckt test a b" in output
        assert "R1 a b 10k" in output
        assert ".ends test" in output
        assert ".end" in output


class TestMosfetOutput:
    def test_mosfet_with_model(self) -> None:
        mosfet = ExternalModule(
            name="mosfet",
            domain="spice",
            ports=[
                make_port(0, "d"),
                make_port(1, "g"),
                make_port(2, "s"),
                make_port(3, "b"),
            ],
            properties={"spice_prefix": "M"},
        )
        mod = Module(
            name="inv",
            ports=[
                make_port(0, "in_"),
                make_port(1, "out"),
                make_port(2, "vdd"),
                make_port(3, "vss"),
            ],
            module_references=[
                ModuleReference(
                    name="M1",
                    module_name="mosfet",
                    model_name="pch",
                    parameter_overrides={
                        "W": Parameter(
                            name="W",
                            default_value=make_pv(1.0, SIPrefix.MICRO),
                        ),
                        "L": Parameter(
                            name="L",
                            default_value=make_pv(0.18, SIPrefix.MICRO),
                        ),
                    },
                ),
            ],
            connections=[
                make_conn("out", "", "out", "M1", "d"),
                make_conn("in_", "", "in_", "M1", "g"),
                make_conn("vdd", "", "vdd", "M1", "s"),
                make_conn("vdd", "", "vdd", "M1", "b"),
            ],
        )
        circuit = Circuit(
            name="test",
            domain="spice",
            top_module="inv",
            modules=[mod],
            ext_modules=[mosfet],
        )
        output = write_spice(circuit)
        assert "M1 out in_ vdd vdd pch W=1u L=0.18u" in output


class TestSubcircuitInstance:
    def test_x_instance(self) -> None:
        inner = Module(
            name="inner",
            ports=[make_port(0, "p"), make_port(1, "q")],
        )
        outer = Module(
            name="outer",
            ports=[make_port(0, "a"), make_port(1, "b")],
            module_references=[
                ModuleReference(name="X1", module_name="inner"),
            ],
            connections=[
                make_conn("a", "", "a", "X1", "p"),
                make_conn("b", "", "b", "X1", "q"),
            ],
        )
        circuit = Circuit(
            name="test",
            domain="spice",
            top_module="outer",
            modules=[inner, outer],
        )
        output = write_spice(circuit)
        assert "X1 a b inner" in output


class TestDirectiveOutput:
    def test_include(self) -> None:
        circuit = Circuit(
            name="test",
            domain="spice",
            directives=[Directive(kind=DirectiveKind.INCLUDE, value="models.lib")],
        )
        output = write_spice(circuit)
        assert '.include "models.lib"' in output

    def test_global(self) -> None:
        circuit = Circuit(
            name="test",
            domain="spice",
            directives=[Directive(kind=DirectiveKind.GLOBAL, value="VDD VSS")],
        )
        output = write_spice(circuit)
        assert ".global VDD VSS" in output

    def test_model(self) -> None:
        from hubnet.hubnet_schema import Parameter

        nch = ExternalModule(
            name="nch",
            domain="spice",
            parameters=[
                Parameter(name="level", default_value=make_pv(49.0)),
                Parameter(name="vth0", default_value=make_pv(0.4)),
            ],
            properties={"model_type": "nmos"},
        )
        circuit = Circuit(
            name="test",
            domain="spice",
            ext_modules=[nch],
        )
        output = write_spice(circuit)
        assert ".model nch nmos" in output
        assert "level=49" in output
        assert "vth0=0.4" in output


class TestAllValueTypes:
    def test_int_value_param(self) -> None:
        nch = ExternalModule(
            name="nch",
            domain="spice",
            parameters=[
                Parameter(name="level", default_value=ParameterValue(int_value=49)),
            ],
            properties={"model_type": "nmos"},
        )
        circuit = Circuit(name="test", domain="spice", ext_modules=[nch])
        output = write_spice(circuit)
        assert "level=49" in output

    def test_string_value_param(self) -> None:
        nch = ExternalModule(
            name="nch",
            domain="spice",
            parameters=[
                Parameter(
                    name="version",
                    default_value=ParameterValue(string_value="4.7"),
                ),
            ],
            properties={"model_type": "nmos"},
        )
        circuit = Circuit(name="test", domain="spice", ext_modules=[nch])
        output = write_spice(circuit)
        assert "version=4.7" in output

    def test_expression_param(self) -> None:
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
            name="test", domain="spice", top_module="test", modules=[mod]
        )
        output = write_spice(circuit)
        assert ".param r='1k+2k'" in output
