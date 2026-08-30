from enum import IntEnum

import pytest
from pydantic import ValidationError

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

# ======================================================================
# Enum tests
# ======================================================================


class TestEnums:
    def test_port_direction_is_intenum(self):
        assert issubclass(PortDirection, IntEnum)

    def test_signal_domain_is_intenum(self):
        assert issubclass(SignalDomain, IntEnum)

    def test_si_prefix_is_intenum(self):
        assert issubclass(SIPrefix, IntEnum)

    def test_port_direction_values(self):
        assert PortDirection.INOUT == 0
        assert PortDirection.INPUT == 1
        assert PortDirection.OUTPUT == 2

    def test_signal_domain_values(self):
        assert SignalDomain.UNSPECIFIED == 0
        assert SignalDomain.ELECTRICAL == 1
        assert SignalDomain.WAVEGUIDE == 2

    def test_si_prefix_values(self):
        assert SIPrefix.UNSPECIFIED == 0
        assert SIPrefix.QUECTO == 1
        assert SIPrefix.NANO == 8
        assert SIPrefix.MICRO == 9
        assert SIPrefix.MILLI == 10
        assert SIPrefix.KILO == 15
        assert SIPrefix.MEGA == 16
        assert SIPrefix.GIGA == 17
        assert SIPrefix.QUETTA == 24
        assert len(SIPrefix) == 25


# ======================================================================
# Default construction tests
# ======================================================================


class TestDefaults:
    @pytest.mark.parametrize(
        "model_cls",
        [
            PrefixedValue,
            ModelReference,
            ParameterValue,
            Parameter,
            ModelInterface,
            PortReference,
            Port,
            Connection,
            Bus,
            ModuleReference,
            Module,
            ExternalModule,
            Circuit,
        ],
    )
    def test_default_construction(self, model_cls):
        instance = model_cls()
        assert instance is not None


class TestFrozen:
    def test_immutability(self, prefixed_value):
        with pytest.raises(ValidationError):
            prefixed_value.double_value = 99.0


# ======================================================================
# ParameterValue oneof tests
# ======================================================================


class TestParameterValueOneof:
    def test_allows_empty(self):
        pv = ParameterValue()
        assert pv.prefixed_value is None
        assert pv.model_ref is None

    def test_allows_prefixed_value_only(self, prefixed_value):
        pv = ParameterValue(prefixed_value=prefixed_value)
        assert pv.prefixed_value is not None
        assert pv.model_ref is None

    def test_allows_model_ref_only(self, model_reference):
        pv = ParameterValue(model_ref=model_reference)
        assert pv.prefixed_value is None
        assert pv.model_ref is not None

    def test_rejects_both_set(self, prefixed_value, model_reference):
        with pytest.raises(ValueError, match="oneof"):
            ParameterValue(
                prefixed_value=prefixed_value,
                model_ref=model_reference,
            )


# ======================================================================
# Per-model round-trip tests
# ======================================================================


class TestPrefixedValue:
    def test_roundtrip_proto_binary(self, prefixed_value):
        data = prefixed_value.to_proto_bytes()
        restored = PrefixedValue.from_proto_bytes(data)
        assert restored == prefixed_value

    def test_roundtrip_json(self, prefixed_value):
        json_str = prefixed_value.to_json()
        restored = PrefixedValue.from_json(json_str)
        assert restored == prefixed_value

    def test_roundtrip_yaml(self, prefixed_value):
        yaml_str = prefixed_value.to_yaml()
        restored = PrefixedValue.from_yaml(yaml_str)
        assert restored == prefixed_value


class TestModelReference:
    def test_roundtrip_proto_binary(self, model_reference):
        data = model_reference.to_proto_bytes()
        restored = ModelReference.from_proto_bytes(data)
        assert restored == model_reference

    def test_roundtrip_json(self, model_reference):
        json_str = model_reference.to_json()
        restored = ModelReference.from_json(json_str)
        assert restored == model_reference

    def test_roundtrip_yaml(self, model_reference):
        yaml_str = model_reference.to_yaml()
        restored = ModelReference.from_yaml(yaml_str)
        assert restored == model_reference


class TestParameterValuePrefixed:
    def test_roundtrip_proto_binary(self, parameter_value_with_prefixed):
        data = parameter_value_with_prefixed.to_proto_bytes()
        restored = ParameterValue.from_proto_bytes(data)
        assert restored == parameter_value_with_prefixed

    def test_roundtrip_json(self, parameter_value_with_prefixed):
        json_str = parameter_value_with_prefixed.to_json()
        restored = ParameterValue.from_json(json_str)
        assert restored == parameter_value_with_prefixed

    def test_roundtrip_yaml(self, parameter_value_with_prefixed):
        yaml_str = parameter_value_with_prefixed.to_yaml()
        restored = ParameterValue.from_yaml(yaml_str)
        assert restored == parameter_value_with_prefixed


class TestParameterValueModelRef:
    def test_roundtrip_proto_binary(self, parameter_value_with_model_ref):
        data = parameter_value_with_model_ref.to_proto_bytes()
        restored = ParameterValue.from_proto_bytes(data)
        assert restored == parameter_value_with_model_ref

    def test_roundtrip_json(self, parameter_value_with_model_ref):
        json_str = parameter_value_with_model_ref.to_json()
        restored = ParameterValue.from_json(json_str)
        assert restored == parameter_value_with_model_ref

    def test_roundtrip_yaml(self, parameter_value_with_model_ref):
        yaml_str = parameter_value_with_model_ref.to_yaml()
        restored = ParameterValue.from_yaml(yaml_str)
        assert restored == parameter_value_with_model_ref


class TestParameter:
    def test_roundtrip_proto_binary(self, parameter):
        data = parameter.to_proto_bytes()
        restored = Parameter.from_proto_bytes(data)
        assert restored == parameter

    def test_roundtrip_json(self, parameter):
        json_str = parameter.to_json()
        restored = Parameter.from_json(json_str)
        assert restored == parameter

    def test_roundtrip_yaml(self, parameter):
        yaml_str = parameter.to_yaml()
        restored = Parameter.from_yaml(yaml_str)
        assert restored == parameter


class TestModelInterface:
    def test_roundtrip_proto_binary(self, model_interface):
        data = model_interface.to_proto_bytes()
        restored = ModelInterface.from_proto_bytes(data)
        assert restored == model_interface

    def test_roundtrip_json(self, model_interface):
        json_str = model_interface.to_json()
        restored = ModelInterface.from_json(json_str)
        assert restored == model_interface

    def test_roundtrip_yaml(self, model_interface):
        yaml_str = model_interface.to_yaml()
        restored = ModelInterface.from_yaml(yaml_str)
        assert restored == model_interface


class TestPortReference:
    def test_roundtrip_proto_binary(self, port_reference):
        data = port_reference.to_proto_bytes()
        restored = PortReference.from_proto_bytes(data)
        assert restored == port_reference

    def test_roundtrip_json(self, port_reference):
        json_str = port_reference.to_json()
        restored = PortReference.from_json(json_str)
        assert restored == port_reference

    def test_roundtrip_yaml(self, port_reference):
        yaml_str = port_reference.to_yaml()
        restored = PortReference.from_yaml(yaml_str)
        assert restored == port_reference


class TestPort:
    def test_roundtrip_proto_binary(self, port):
        data = port.to_proto_bytes()
        restored = Port.from_proto_bytes(data)
        assert restored == port

    def test_roundtrip_json(self, port):
        json_str = port.to_json()
        restored = Port.from_json(json_str)
        assert restored == port

    def test_roundtrip_yaml(self, port):
        yaml_str = port.to_yaml()
        restored = Port.from_yaml(yaml_str)
        assert restored == port


class TestConnection:
    def test_roundtrip_proto_binary(self, connection):
        data = connection.to_proto_bytes()
        restored = Connection.from_proto_bytes(data)
        assert restored == connection

    def test_roundtrip_json(self, connection):
        json_str = connection.to_json()
        restored = Connection.from_json(json_str)
        assert restored == connection

    def test_roundtrip_yaml(self, connection):
        yaml_str = connection.to_yaml()
        restored = Connection.from_yaml(yaml_str)
        assert restored == connection


class TestBus:
    def test_roundtrip_proto_binary(self, bus):
        data = bus.to_proto_bytes()
        restored = Bus.from_proto_bytes(data)
        assert restored == bus

    def test_roundtrip_json(self, bus):
        json_str = bus.to_json()
        restored = Bus.from_json(json_str)
        assert restored == bus

    def test_roundtrip_yaml(self, bus):
        yaml_str = bus.to_yaml()
        restored = Bus.from_yaml(yaml_str)
        assert restored == bus


class TestModuleReference:
    def test_roundtrip_proto_binary(self, module_reference):
        data = module_reference.to_proto_bytes()
        restored = ModuleReference.from_proto_bytes(data)
        assert restored == module_reference

    def test_roundtrip_json(self, module_reference):
        json_str = module_reference.to_json()
        restored = ModuleReference.from_json(json_str)
        assert restored == module_reference

    def test_roundtrip_yaml(self, module_reference):
        yaml_str = module_reference.to_yaml()
        restored = ModuleReference.from_yaml(yaml_str)
        assert restored == module_reference


class TestModule:
    def test_roundtrip_proto_binary(self, module):
        data = module.to_proto_bytes()
        restored = Module.from_proto_bytes(data)
        assert restored == module

    def test_roundtrip_json(self, module):
        json_str = module.to_json()
        restored = Module.from_json(json_str)
        assert restored == module

    def test_roundtrip_yaml(self, module):
        yaml_str = module.to_yaml()
        restored = Module.from_yaml(yaml_str)
        assert restored == module


class TestExternalModule:
    def test_roundtrip_proto_binary(self, external_module):
        data = external_module.to_proto_bytes()
        restored = ExternalModule.from_proto_bytes(data)
        assert restored == external_module

    def test_roundtrip_json(self, external_module):
        json_str = external_module.to_json()
        restored = ExternalModule.from_json(json_str)
        assert restored == external_module

    def test_roundtrip_yaml(self, external_module):
        yaml_str = external_module.to_yaml()
        restored = ExternalModule.from_yaml(yaml_str)
        assert restored == external_module


# ======================================================================
# Full circuit integration tests
# ======================================================================


class TestCircuitIntegration:
    def test_roundtrip_proto_binary(self, circuit):
        data = circuit.to_proto_bytes()
        restored = Circuit.from_proto_bytes(data)
        assert restored == circuit

    def test_roundtrip_json(self, circuit):
        json_str = circuit.to_json()
        restored = Circuit.from_json(json_str)
        assert restored == circuit

    def test_roundtrip_yaml(self, circuit):
        yaml_str = circuit.to_yaml()
        restored = Circuit.from_yaml(yaml_str)
        assert restored == circuit

    def test_proto_interop(self, circuit):
        proto_msg = circuit.to_proto()
        assert proto_msg.name == "mzi_circuit"
        assert proto_msg.domain == "photonics"
        assert proto_msg.top_module == "top"
        assert len(proto_msg.modules) == 1
        assert len(proto_msg.ext_modules) == 1
        assert proto_msg.modules[0].name == "top"
        assert proto_msg.modules[0].ports[0].name == "o1"

        restored = Circuit.from_proto(proto_msg)
        assert restored == circuit

    def test_cross_format_equivalence(self, circuit):
        from_proto = Circuit.from_proto_bytes(circuit.to_proto_bytes())
        from_json = Circuit.from_json(circuit.to_json())
        from_yaml = Circuit.from_yaml(circuit.to_yaml())
        assert from_proto == from_json == from_yaml == circuit
