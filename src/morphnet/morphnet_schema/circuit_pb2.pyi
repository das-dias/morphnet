import simulation_pb2 as _simulation_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PortDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PORT_DIRECTION_INOUT: _ClassVar[PortDirection]
    PORT_DIRECTION_INPUT: _ClassVar[PortDirection]
    PORT_DIRECTION_OUTPUT: _ClassVar[PortDirection]

class SignalDomain(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SIGNAL_DOMAIN_UNSPECIFIED: _ClassVar[SignalDomain]
    SIGNAL_DOMAIN_ELECTRICAL: _ClassVar[SignalDomain]
    SIGNAL_DOMAIN_WAVEGUIDE: _ClassVar[SignalDomain]

class SIPrefix(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    SI_PREFIX_UNSPECIFIED: _ClassVar[SIPrefix]
    SI_PREFIX_QUECTO: _ClassVar[SIPrefix]
    SI_PREFIX_RONTO: _ClassVar[SIPrefix]
    SI_PREFIX_YOCTO: _ClassVar[SIPrefix]
    SI_PREFIX_ZEPTO: _ClassVar[SIPrefix]
    SI_PREFIX_ATTO: _ClassVar[SIPrefix]
    SI_PREFIX_FEMTO: _ClassVar[SIPrefix]
    SI_PREFIX_PICO: _ClassVar[SIPrefix]
    SI_PREFIX_NANO: _ClassVar[SIPrefix]
    SI_PREFIX_MICRO: _ClassVar[SIPrefix]
    SI_PREFIX_MILLI: _ClassVar[SIPrefix]
    SI_PREFIX_CENTI: _ClassVar[SIPrefix]
    SI_PREFIX_DECI: _ClassVar[SIPrefix]
    SI_PREFIX_DECA: _ClassVar[SIPrefix]
    SI_PREFIX_HECTO: _ClassVar[SIPrefix]
    SI_PREFIX_KILO: _ClassVar[SIPrefix]
    SI_PREFIX_MEGA: _ClassVar[SIPrefix]
    SI_PREFIX_GIGA: _ClassVar[SIPrefix]
    SI_PREFIX_TERA: _ClassVar[SIPrefix]
    SI_PREFIX_PETA: _ClassVar[SIPrefix]
    SI_PREFIX_EXA: _ClassVar[SIPrefix]
    SI_PREFIX_ZETTA: _ClassVar[SIPrefix]
    SI_PREFIX_YOTTA: _ClassVar[SIPrefix]
    SI_PREFIX_RONNA: _ClassVar[SIPrefix]
    SI_PREFIX_QUETTA: _ClassVar[SIPrefix]

class ExternalModuleKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EXTERNAL_MODULE_KIND_UNSPECIFIED: _ClassVar[ExternalModuleKind]
    EXTERNAL_MODULE_KIND_DEVICE: _ClassVar[ExternalModuleKind]
    EXTERNAL_MODULE_KIND_MODEL: _ClassVar[ExternalModuleKind]
    EXTERNAL_MODULE_KIND_NATURE: _ClassVar[ExternalModuleKind]
    EXTERNAL_MODULE_KIND_DISCIPLINE: _ClassVar[ExternalModuleKind]

class DirectiveKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DIRECTIVE_KIND_UNSPECIFIED: _ClassVar[DirectiveKind]
    DIRECTIVE_KIND_INCLUDE: _ClassVar[DirectiveKind]
    DIRECTIVE_KIND_LIB: _ClassVar[DirectiveKind]
    DIRECTIVE_KIND_GLOBAL: _ClassVar[DirectiveKind]
    DIRECTIVE_KIND_OPTION: _ClassVar[DirectiveKind]
    DIRECTIVE_KIND_PARAM: _ClassVar[DirectiveKind]
    DIRECTIVE_KIND_DEFINE: _ClassVar[DirectiveKind]
    DIRECTIVE_KIND_TIMESCALE: _ClassVar[DirectiveKind]
PORT_DIRECTION_INOUT: PortDirection
PORT_DIRECTION_INPUT: PortDirection
PORT_DIRECTION_OUTPUT: PortDirection
SIGNAL_DOMAIN_UNSPECIFIED: SignalDomain
SIGNAL_DOMAIN_ELECTRICAL: SignalDomain
SIGNAL_DOMAIN_WAVEGUIDE: SignalDomain
SI_PREFIX_UNSPECIFIED: SIPrefix
SI_PREFIX_QUECTO: SIPrefix
SI_PREFIX_RONTO: SIPrefix
SI_PREFIX_YOCTO: SIPrefix
SI_PREFIX_ZEPTO: SIPrefix
SI_PREFIX_ATTO: SIPrefix
SI_PREFIX_FEMTO: SIPrefix
SI_PREFIX_PICO: SIPrefix
SI_PREFIX_NANO: SIPrefix
SI_PREFIX_MICRO: SIPrefix
SI_PREFIX_MILLI: SIPrefix
SI_PREFIX_CENTI: SIPrefix
SI_PREFIX_DECI: SIPrefix
SI_PREFIX_DECA: SIPrefix
SI_PREFIX_HECTO: SIPrefix
SI_PREFIX_KILO: SIPrefix
SI_PREFIX_MEGA: SIPrefix
SI_PREFIX_GIGA: SIPrefix
SI_PREFIX_TERA: SIPrefix
SI_PREFIX_PETA: SIPrefix
SI_PREFIX_EXA: SIPrefix
SI_PREFIX_ZETTA: SIPrefix
SI_PREFIX_YOTTA: SIPrefix
SI_PREFIX_RONNA: SIPrefix
SI_PREFIX_QUETTA: SIPrefix
EXTERNAL_MODULE_KIND_UNSPECIFIED: ExternalModuleKind
EXTERNAL_MODULE_KIND_DEVICE: ExternalModuleKind
EXTERNAL_MODULE_KIND_MODEL: ExternalModuleKind
EXTERNAL_MODULE_KIND_NATURE: ExternalModuleKind
EXTERNAL_MODULE_KIND_DISCIPLINE: ExternalModuleKind
DIRECTIVE_KIND_UNSPECIFIED: DirectiveKind
DIRECTIVE_KIND_INCLUDE: DirectiveKind
DIRECTIVE_KIND_LIB: DirectiveKind
DIRECTIVE_KIND_GLOBAL: DirectiveKind
DIRECTIVE_KIND_OPTION: DirectiveKind
DIRECTIVE_KIND_PARAM: DirectiveKind
DIRECTIVE_KIND_DEFINE: DirectiveKind
DIRECTIVE_KIND_TIMESCALE: DirectiveKind

class PrefixedValue(_message.Message):
    __slots__ = ("double_value", "prefix")
    DOUBLE_VALUE_FIELD_NUMBER: _ClassVar[int]
    PREFIX_FIELD_NUMBER: _ClassVar[int]
    double_value: float
    prefix: SIPrefix
    def __init__(self, double_value: _Optional[float] = ..., prefix: _Optional[_Union[SIPrefix, str]] = ...) -> None: ...

class ParameterValue(_message.Message):
    __slots__ = ("prefixed_value", "model_ref", "string_value", "expression", "int_value")
    PREFIXED_VALUE_FIELD_NUMBER: _ClassVar[int]
    MODEL_REF_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    EXPRESSION_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    prefixed_value: PrefixedValue
    model_ref: ModelReference
    string_value: str
    expression: str
    int_value: int
    def __init__(self, prefixed_value: _Optional[_Union[PrefixedValue, _Mapping]] = ..., model_ref: _Optional[_Union[ModelReference, _Mapping]] = ..., string_value: _Optional[str] = ..., expression: _Optional[str] = ..., int_value: _Optional[int] = ...) -> None: ...

class Parameter(_message.Message):
    __slots__ = ("uid", "name", "default_value", "description", "properties")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    UID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_VALUE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    uid: int
    name: str
    default_value: ParameterValue
    description: str
    properties: _containers.ScalarMap[str, str]
    def __init__(self, uid: _Optional[int] = ..., name: _Optional[str] = ..., default_value: _Optional[_Union[ParameterValue, _Mapping]] = ..., description: _Optional[str] = ..., properties: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Directive(_message.Message):
    __slots__ = ("kind", "name", "value")
    KIND_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    kind: DirectiveKind
    name: str
    value: str
    def __init__(self, kind: _Optional[_Union[DirectiveKind, str]] = ..., name: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class ModelInterface(_message.Message):
    __slots__ = ("name", "function_name", "parameters", "properties")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    name: str
    function_name: str
    parameters: _containers.RepeatedCompositeFieldContainer[Parameter]
    properties: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., function_name: _Optional[str] = ..., parameters: _Optional[_Iterable[_Union[Parameter, _Mapping]]] = ..., properties: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ModelReference(_message.Message):
    __slots__ = ("model_interface_name", "arguments")
    class ArgumentsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: ParameterValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[ParameterValue, _Mapping]] = ...) -> None: ...
    MODEL_INTERFACE_NAME_FIELD_NUMBER: _ClassVar[int]
    ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    model_interface_name: str
    arguments: _containers.MessageMap[str, ParameterValue]
    def __init__(self, model_interface_name: _Optional[str] = ..., arguments: _Optional[_Mapping[str, ParameterValue]] = ...) -> None: ...

class Port(_message.Message):
    __slots__ = ("uid", "name", "direction", "domain", "width", "cross_section", "properties", "discipline")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    UID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DIRECTION_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    CROSS_SECTION_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    DISCIPLINE_FIELD_NUMBER: _ClassVar[int]
    uid: int
    name: str
    direction: PortDirection
    domain: SignalDomain
    width: int
    cross_section: str
    properties: _containers.ScalarMap[str, str]
    discipline: str
    def __init__(self, uid: _Optional[int] = ..., name: _Optional[str] = ..., direction: _Optional[_Union[PortDirection, str]] = ..., domain: _Optional[_Union[SignalDomain, str]] = ..., width: _Optional[int] = ..., cross_section: _Optional[str] = ..., properties: _Optional[_Mapping[str, str]] = ..., discipline: _Optional[str] = ...) -> None: ...

class PortReference(_message.Message):
    __slots__ = ("instance_name", "port_name")
    INSTANCE_NAME_FIELD_NUMBER: _ClassVar[int]
    PORT_NAME_FIELD_NUMBER: _ClassVar[int]
    instance_name: str
    port_name: str
    def __init__(self, instance_name: _Optional[str] = ..., port_name: _Optional[str] = ...) -> None: ...

class Connection(_message.Message):
    __slots__ = ("name", "source", "target", "domain", "weight", "properties")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    name: str
    source: PortReference
    target: PortReference
    domain: SignalDomain
    weight: int
    properties: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., source: _Optional[_Union[PortReference, _Mapping]] = ..., target: _Optional[_Union[PortReference, _Mapping]] = ..., domain: _Optional[_Union[SignalDomain, str]] = ..., weight: _Optional[int] = ..., properties: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Bus(_message.Message):
    __slots__ = ("name", "width", "domain", "connections", "properties")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    name: str
    width: int
    domain: SignalDomain
    connections: _containers.RepeatedCompositeFieldContainer[Connection]
    properties: _containers.ScalarMap[str, str]
    def __init__(self, name: _Optional[str] = ..., width: _Optional[int] = ..., domain: _Optional[_Union[SignalDomain, str]] = ..., connections: _Optional[_Iterable[_Union[Connection, _Mapping]]] = ..., properties: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ModuleReference(_message.Message):
    __slots__ = ("name", "module_name", "class_name", "parameters", "parameter_overrides", "properties", "model_name")
    class ParameterOverridesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Parameter
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Parameter, _Mapping]] = ...) -> None: ...
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    MODULE_NAME_FIELD_NUMBER: _ClassVar[int]
    CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    PARAMETER_OVERRIDES_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    module_name: str
    class_name: str
    parameters: _containers.RepeatedCompositeFieldContainer[Parameter]
    parameter_overrides: _containers.MessageMap[str, Parameter]
    properties: _containers.ScalarMap[str, str]
    model_name: str
    def __init__(self, name: _Optional[str] = ..., module_name: _Optional[str] = ..., class_name: _Optional[str] = ..., parameters: _Optional[_Iterable[_Union[Parameter, _Mapping]]] = ..., parameter_overrides: _Optional[_Mapping[str, Parameter]] = ..., properties: _Optional[_Mapping[str, str]] = ..., model_name: _Optional[str] = ...) -> None: ...

class Module(_message.Message):
    __slots__ = ("uid", "name", "class_name", "ports", "parameters", "model_interfaces", "module_references", "connections", "buses", "properties", "directives")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    UID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CLASS_NAME_FIELD_NUMBER: _ClassVar[int]
    PORTS_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    MODEL_INTERFACES_FIELD_NUMBER: _ClassVar[int]
    MODULE_REFERENCES_FIELD_NUMBER: _ClassVar[int]
    CONNECTIONS_FIELD_NUMBER: _ClassVar[int]
    BUSES_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    DIRECTIVES_FIELD_NUMBER: _ClassVar[int]
    uid: int
    name: str
    class_name: str
    ports: _containers.RepeatedCompositeFieldContainer[Port]
    parameters: _containers.RepeatedCompositeFieldContainer[Parameter]
    model_interfaces: _containers.RepeatedCompositeFieldContainer[ModelInterface]
    module_references: _containers.RepeatedCompositeFieldContainer[ModuleReference]
    connections: _containers.RepeatedCompositeFieldContainer[Connection]
    buses: _containers.RepeatedCompositeFieldContainer[Bus]
    properties: _containers.ScalarMap[str, str]
    directives: _containers.RepeatedCompositeFieldContainer[Directive]
    def __init__(self, uid: _Optional[int] = ..., name: _Optional[str] = ..., class_name: _Optional[str] = ..., ports: _Optional[_Iterable[_Union[Port, _Mapping]]] = ..., parameters: _Optional[_Iterable[_Union[Parameter, _Mapping]]] = ..., model_interfaces: _Optional[_Iterable[_Union[ModelInterface, _Mapping]]] = ..., module_references: _Optional[_Iterable[_Union[ModuleReference, _Mapping]]] = ..., connections: _Optional[_Iterable[_Union[Connection, _Mapping]]] = ..., buses: _Optional[_Iterable[_Union[Bus, _Mapping]]] = ..., properties: _Optional[_Mapping[str, str]] = ..., directives: _Optional[_Iterable[_Union[Directive, _Mapping]]] = ...) -> None: ...

class ExternalModule(_message.Message):
    __slots__ = ("name", "domain", "ports", "parameters", "properties", "kind")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    PORTS_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    name: str
    domain: str
    ports: _containers.RepeatedCompositeFieldContainer[Port]
    parameters: _containers.RepeatedCompositeFieldContainer[Parameter]
    properties: _containers.ScalarMap[str, str]
    kind: ExternalModuleKind
    def __init__(self, name: _Optional[str] = ..., domain: _Optional[str] = ..., ports: _Optional[_Iterable[_Union[Port, _Mapping]]] = ..., parameters: _Optional[_Iterable[_Union[Parameter, _Mapping]]] = ..., properties: _Optional[_Mapping[str, str]] = ..., kind: _Optional[_Union[ExternalModuleKind, str]] = ...) -> None: ...

class Circuit(_message.Message):
    __slots__ = ("name", "domain", "top_module", "modules", "ext_modules", "properties", "directives", "simulation")
    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOMAIN_FIELD_NUMBER: _ClassVar[int]
    TOP_MODULE_FIELD_NUMBER: _ClassVar[int]
    MODULES_FIELD_NUMBER: _ClassVar[int]
    EXT_MODULES_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    DIRECTIVES_FIELD_NUMBER: _ClassVar[int]
    SIMULATION_FIELD_NUMBER: _ClassVar[int]
    name: str
    domain: str
    top_module: str
    modules: _containers.RepeatedCompositeFieldContainer[Module]
    ext_modules: _containers.RepeatedCompositeFieldContainer[ExternalModule]
    properties: _containers.ScalarMap[str, str]
    directives: _containers.RepeatedCompositeFieldContainer[Directive]
    simulation: _simulation_pb2.Simulation
    def __init__(self, name: _Optional[str] = ..., domain: _Optional[str] = ..., top_module: _Optional[str] = ..., modules: _Optional[_Iterable[_Union[Module, _Mapping]]] = ..., ext_modules: _Optional[_Iterable[_Union[ExternalModule, _Mapping]]] = ..., properties: _Optional[_Mapping[str, str]] = ..., directives: _Optional[_Iterable[_Union[Directive, _Mapping]]] = ..., simulation: _Optional[_Union[_simulation_pb2.Simulation, _Mapping]] = ...) -> None: ...
