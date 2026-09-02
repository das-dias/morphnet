# ruff: noqa: RUF012
from __future__ import annotations

from enum import IntEnum
from typing import ClassVar

from pydantic import model_validator

from morphnet.morphnet_schema import circuit_pb2 as pb
from morphnet.morphnet_schema._base import ProtoModel
from morphnet.morphnet_schema._simulation import Simulation

__all__ = [
    "Bus",
    "Circuit",
    "Connection",
    "Directive",
    "DirectiveKind",
    "ExternalModule",
    "ExternalModuleKind",
    "ModelInterface",
    "ModelReference",
    "Module",
    "ModuleReference",
    "Parameter",
    "ParameterValue",
    "Port",
    "PortDirection",
    "PortReference",
    "PrefixedValue",
    "SIPrefix",
    "SignalDomain",
]


# ======================================================================
# Enums
# ======================================================================


class PortDirection(IntEnum):
    INOUT = 0
    INPUT = 1
    OUTPUT = 2


class SignalDomain(IntEnum):
    UNSPECIFIED = 0
    ELECTRICAL = 1
    WAVEGUIDE = 2


class SIPrefix(IntEnum):
    UNSPECIFIED = 0
    QUECTO = 1
    RONTO = 2
    YOCTO = 3
    ZEPTO = 4
    ATTO = 5
    FEMTO = 6
    PICO = 7
    NANO = 8
    MICRO = 9
    MILLI = 10
    CENTI = 11
    DECI = 12
    DECA = 13
    HECTO = 14
    KILO = 15
    MEGA = 16
    GIGA = 17
    TERA = 18
    PETA = 19
    EXA = 20
    ZETTA = 21
    YOTTA = 22
    RONNA = 23
    QUETTA = 24


class ExternalModuleKind(IntEnum):
    UNSPECIFIED = 0
    DEVICE = 1
    MODEL = 2
    NATURE = 3
    DISCIPLINE = 4


class DirectiveKind(IntEnum):
    UNSPECIFIED = 0
    INCLUDE = 1
    LIB = 2
    GLOBAL = 3
    OPTION = 4
    PARAM = 5
    DEFINE = 6
    TIMESCALE = 7


# ======================================================================
# Parameter models
# ======================================================================


class PrefixedValue(ProtoModel):
    _proto_type: ClassVar[type] = pb.PrefixedValue

    double_value: float = 0.0
    prefix: SIPrefix = SIPrefix.UNSPECIFIED


class ModelReference(ProtoModel):
    _proto_type: ClassVar[type] = pb.ModelReference

    model_interface_name: str = ""
    arguments: dict[str, ParameterValue] = {}


class ParameterValue(ProtoModel):
    _proto_type: ClassVar[type] = pb.ParameterValue

    prefixed_value: PrefixedValue | None = None
    model_ref: ModelReference | None = None
    string_value: str | None = None
    expression: str | None = None
    int_value: int | None = None

    @model_validator(mode="after")
    def _check_oneof(self) -> ParameterValue:
        set_count = sum(
            v is not None
            for v in (
                self.prefixed_value,
                self.model_ref,
                self.string_value,
                self.expression,
                self.int_value,
            )
        )
        if set_count > 1:
            raise ValueError(
                "ParameterValue is a oneof: set exactly one of "
                "'prefixed_value', 'model_ref', 'string_value', "
                "'expression', 'int_value'"
            )
        return self


class Parameter(ProtoModel):
    _proto_type: ClassVar[type] = pb.Parameter

    uid: int = 0
    name: str = ""
    default_value: ParameterValue | None = None
    description: str = ""
    properties: dict[str, str] = {}


# ======================================================================
# Directives
# ======================================================================


class Directive(ProtoModel):
    _proto_type: ClassVar[type] = pb.Directive

    kind: DirectiveKind = DirectiveKind.UNSPECIFIED
    name: str = ""
    value: str = ""


# ======================================================================
# Model interfaces
# ======================================================================


class ModelInterface(ProtoModel):
    _proto_type: ClassVar[type] = pb.ModelInterface

    name: str = ""
    function_name: str = ""
    parameters: list[Parameter] = []
    properties: dict[str, str] = {}


# ======================================================================
# Ports and connections
# ======================================================================


class PortReference(ProtoModel):
    _proto_type: ClassVar[type] = pb.PortReference

    instance_name: str = ""
    port_name: str = ""


class Port(ProtoModel):
    _proto_type: ClassVar[type] = pb.Port

    uid: int = 0
    name: str = ""
    direction: PortDirection = PortDirection.INOUT
    domain: SignalDomain = SignalDomain.UNSPECIFIED
    width: int = 0
    cross_section: str = ""
    properties: dict[str, str] = {}
    discipline: str = ""


class Connection(ProtoModel):
    _proto_type: ClassVar[type] = pb.Connection

    name: str = ""
    source: PortReference | None = None
    target: PortReference | None = None
    domain: SignalDomain = SignalDomain.UNSPECIFIED
    weight: int = 0
    properties: dict[str, str] = {}


class Bus(ProtoModel):
    _proto_type: ClassVar[type] = pb.Bus

    name: str = ""
    width: int = 0
    domain: SignalDomain = SignalDomain.UNSPECIFIED
    connections: list[Connection] = []
    properties: dict[str, str] = {}


# ======================================================================
# Module hierarchy
# ======================================================================


class ModuleReference(ProtoModel):
    _proto_type: ClassVar[type] = pb.ModuleReference

    name: str = ""
    module_name: str = ""
    class_name: str = ""
    parameters: list[Parameter] = []
    parameter_overrides: dict[str, Parameter] = {}
    properties: dict[str, str] = {}
    model_name: str = ""


class Module(ProtoModel):
    _proto_type: ClassVar[type] = pb.Module

    uid: int = 0
    name: str = ""
    class_name: str = ""
    ports: list[Port] = []
    parameters: list[Parameter] = []
    model_interfaces: list[ModelInterface] = []
    module_references: list[ModuleReference] = []
    connections: list[Connection] = []
    buses: list[Bus] = []
    properties: dict[str, str] = {}
    directives: list[Directive] = []


class ExternalModule(ProtoModel):
    _proto_type: ClassVar[type] = pb.ExternalModule

    name: str = ""
    domain: str = ""
    ports: list[Port] = []
    parameters: list[Parameter] = []
    properties: dict[str, str] = {}
    kind: ExternalModuleKind = ExternalModuleKind.UNSPECIFIED


# ======================================================================
# Circuit (top-level container)
# ======================================================================


class Circuit(ProtoModel):
    _proto_type: ClassVar[type] = pb.Circuit

    name: str = ""
    domain: str = ""
    top_module: str = ""
    modules: list[Module] = []
    ext_modules: list[ExternalModule] = []
    properties: dict[str, str] = {}
    directives: list[Directive] = []
    simulation: Simulation | None = None


# Resolve forward references for the ParameterValue <-> ModelReference cycle
ModelReference.model_rebuild()
ParameterValue.model_rebuild()
