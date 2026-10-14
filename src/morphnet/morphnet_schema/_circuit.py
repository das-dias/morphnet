# ruff: noqa: RUF012
from __future__ import annotations

from enum import IntEnum
from typing import ClassVar

from pydantic import Field, model_validator

from morphnet.morphnet_schema import circuit_pb2 as pb
from morphnet.morphnet_schema._base import ProtoModel
from morphnet.morphnet_schema._simulation import Simulation

__all__ = [
    "Bus",
    "Circuit",
    "Connection",
    "Directive",
    "DirectiveKind",
    "ExternalLibrary",
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

    @model_validator(mode="after")
    def _check_oneof(self) -> ParameterValue:
        set_count = sum(v is not None for v in (self.prefixed_value, self.model_ref))
        if set_count > 1:
            raise ValueError(
                "ParameterValue is a oneof: set exactly one of 'prefixed_value', 'model_ref'"
            )
        return self


class Parameter(ProtoModel):
    _proto_type: ClassVar[type] = pb.Parameter

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
    _proto_type: ClassVar[type] = pb.TerminalReference

    instance_name: str = ""
    port_name: str = Field(default="", alias="terminal_name")


class Port(ProtoModel):
    _proto_type: ClassVar[type] = pb.Terminal

    name: str = ""
    direction: PortDirection = PortDirection.INOUT
    domain: SignalDomain = SignalDomain.UNSPECIFIED
    width: int = 0
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
    properties: dict[str, str] = {}


class Module(ProtoModel):
    _proto_type: ClassVar[type] = pb.Module

    name: str = ""
    class_name: str = ""
    ports: list[Port] = Field(default=[], alias="terminals")
    parameters: list[Parameter] = []
    model_interfaces: list[ModelInterface] = []
    module_references: list[ModuleReference] = []
    connections: list[Connection] = []
    buses: list[Bus] = []
    properties: dict[str, str] = {}
    directives: list[Directive] = []

    def add_terminal(
        self,
        name: str,
        *,
        direction: PortDirection = PortDirection.INOUT,
        domain: SignalDomain = SignalDomain.UNSPECIFIED,
        width: int = 0,
        discipline: str = "",
        properties: dict[str, str] | None = None,
    ) -> "Module":
        self.ports.append(
            Port(
                name=name,
                direction=direction,
                domain=domain,
                width=width,
                discipline=discipline,
                properties=properties or {},
            )
        )
        return self

    def add(self, *refs: ModuleReference) -> "Module":
        self.module_references.extend(refs)
        return self

    def connect(
        self,
        net_name: str,
        *endpoints: tuple[str, str],
        domain: SignalDomain = SignalDomain.UNSPECIFIED,
        properties: dict[str, str] | None = None,
    ) -> "Module":
        """
        Create chained point-to-point connections on a named net.

        Each endpoint is (instance_name, terminal_name).
        instance_name='' refers to this module's own terminal (parent level).
        endpoints [A, B, C] → Connection(A→B), Connection(B→C).
        """
        if len(endpoints) < 2:
            raise ValueError(f"connect({net_name!r}): need ≥ 2 endpoints, got {len(endpoints)}")
        props = properties or {}
        for (si, sp), (ti, tp) in zip(endpoints, endpoints[1:]):
            self.connections.append(
                Connection(
                    name=net_name,
                    source=PortReference(instance_name=si, port_name=sp),
                    target=PortReference(instance_name=ti, port_name=tp),
                    domain=domain,
                    properties=props,
                )
            )
        return self


class ExternalModule(ProtoModel):
    _proto_type: ClassVar[type] = pb.ExternalModule

    name: str = ""
    class_name: str = ""
    library_name: str = ""
    group_name: str = ""
    ports: list[Port] = Field(default=[], alias="terminals")
    parameters: list[Parameter] = []
    properties: dict[str, str] = {}
    kind: ExternalModuleKind = ExternalModuleKind.UNSPECIFIED


# ======================================================================
# External libraries
# ======================================================================


class ExternalLibrary(ProtoModel):
    _proto_type: ClassVar[type] = pb.ExternalLibrary

    path: str = ""
    model_type: str = ""
    external_model_names: list[str] = []


# ======================================================================
# Circuit (top-level container)
# ======================================================================


class Circuit(ProtoModel):
    _proto_type: ClassVar[type] = pb.Circuit

    name: str = ""
    top_module: str = ""
    modules: list[Module] = []
    ext_modules: list[ExternalModule] = []
    properties: dict[str, str] = {}
    directives: list[Directive] = []
    simulation: Simulation | None = None
    libraries: dict[str, ExternalLibrary] = {}

    def add(self, *modules: Module) -> "Circuit":
        self.modules.extend(modules)
        if not self.top_module and modules:
            self.top_module = modules[0].name
        return self

    def add_ext(self, *ext: ExternalModule) -> "Circuit":
        self.ext_modules.extend(ext)
        return self

    def add_library(self, name: str, lib: ExternalLibrary) -> "Circuit":
        self.libraries[name] = lib
        return self


# Resolve forward references for the ParameterValue <-> ModelReference cycle
ModelReference.model_rebuild()
ParameterValue.model_rebuild()
