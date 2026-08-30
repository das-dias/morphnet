import pytest

from hubnet.hubnet_schema import (
    Bus,
    Circuit,
    Connection,
    ExternalModule,
    ModelInterface,
    ModelReference,
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


@pytest.fixture
def prefixed_value():
    return PrefixedValue(double_value=3.14159, prefix=SIPrefix.NANO)


@pytest.fixture
def model_reference(parameter_value_with_prefixed):
    return ModelReference(
        model_interface_name="s_params_model",
        arguments={"width": parameter_value_with_prefixed},
    )


@pytest.fixture
def parameter_value_with_prefixed(prefixed_value):
    return ParameterValue(prefixed_value=prefixed_value)


@pytest.fixture
def parameter_value_with_model_ref():
    pv = ParameterValue(
        prefixed_value=PrefixedValue(double_value=1.55, prefix=SIPrefix.MICRO)
    )
    ref = ModelReference(
        model_interface_name="neff_model",
        arguments={"wavelength": pv},
    )
    return ParameterValue(model_ref=ref)


@pytest.fixture
def parameter(parameter_value_with_prefixed):
    return Parameter(
        uid=42,
        name="width",
        default_value=parameter_value_with_prefixed,
        description="Waveguide width",
        properties={"unit": "m", "category": "geometry"},
    )


@pytest.fixture
def model_interface(parameter):
    return ModelInterface(
        name="sparams",
        function_name="compute_sparams",
        parameters=[parameter],
        properties={"engine": "meep"},
    )


@pytest.fixture
def port_reference():
    return PortReference(instance_name="mmi_1", port_name="o1")


@pytest.fixture
def port():
    return Port(
        uid=7,
        name="o1",
        direction=PortDirection.OUTPUT,
        domain=SignalDomain.WAVEGUIDE,
        width=1,
        cross_section="strip",
        properties={"layer": "1/0"},
    )


@pytest.fixture
def connection(port_reference):
    return Connection(
        name="net0",
        source=port_reference,
        target=PortReference(instance_name="mmi_2", port_name="i1"),
        domain=SignalDomain.WAVEGUIDE,
        weight=1,
        properties={"routing": "auto"},
    )


@pytest.fixture
def bus(connection):
    return Bus(
        name="data_bus",
        width=4,
        domain=SignalDomain.ELECTRICAL,
        connections=[connection],
        properties={"protocol": "spi"},
    )


@pytest.fixture
def module_reference(parameter_value_with_prefixed):
    return ModuleReference(
        name="mmi_1",
        module_name="mmi1x2",
        class_name="MMI1x2",
        parameter_values=[parameter_value_with_prefixed],
        parameter_overrides={
            "length": Parameter(
                name="length",
                default_value=ParameterValue(
                    prefixed_value=PrefixedValue(
                        double_value=5.5, prefix=SIPrefix.MICRO
                    )
                ),
            )
        },
        properties={"technology": "siph"},
    )


@pytest.fixture
def module(port, parameter, model_interface, module_reference, connection, bus):
    return Module(
        uid=1,
        name="top",
        class_name="TopLevel",
        ports=[port],
        parameters=[parameter],
        model_interfaces=[model_interface],
        module_references=[module_reference],
        connections=[connection],
        buses=[bus],
        properties={"foundry": "GlobalFoundries"},
    )


@pytest.fixture
def external_module(port, parameter):
    return ExternalModule(
        name="pd_model",
        domain="electrical",
        ports=[port],
        parameters=[parameter],
        properties={"vendor": "Lumerical"},
    )


@pytest.fixture
def circuit(module, external_module):
    return Circuit(
        name="mzi_circuit",
        domain="photonics",
        top_module="top",
        modules=[module],
        ext_modules=[external_module],
        properties={"pdk": "gf45spclo"},
    )
