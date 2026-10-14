"""
Top-level factory functions for building circuit netlists.

API mirrors gdstk: Circuit ↔ Library, Module ↔ Cell, ModuleReference ↔ Reference.
"""
from __future__ import annotations

from morphnet.morphnet_schema._circuit import (
    Circuit,
    Connection,
    ExternalLibrary,
    ExternalModule,
    ModelInterface,
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

__all__ = [
    "circuit",
    "connection",
    "ext_module",
    "external_library",
    "model_interface",
    "module",
    "module_reference",
    "parameter",
    "port",
]

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

_ParamSpec = Parameter | tuple[str, float] | str


def _make_params(specs: list[_ParamSpec] | None, kwargs: dict[str, float]) -> list[Parameter]:
    """Convert mixed param specs and float kwargs into Parameter objects."""
    result: list[Parameter] = []
    for spec in specs or []:
        if isinstance(spec, Parameter):
            result.append(spec)
        elif isinstance(spec, tuple):
            name, val = spec
            result.append(
                Parameter(
                    name=name,
                    default_value=ParameterValue(
                        prefixed_value=PrefixedValue(double_value=val)
                    ),
                )
            )
        else:
            result.append(Parameter(name=spec))
    for name, val in kwargs.items():
        result.append(
            Parameter(
                name=name,
                default_value=ParameterValue(
                    prefixed_value=PrefixedValue(double_value=val)
                ),
            )
        )
    return result


# --------------------------------------------------------------------------
# Factory functions
# --------------------------------------------------------------------------


def circuit(
    name: str,
    *,
    top_module: str = "",
    properties: dict[str, str] | None = None,
) -> Circuit:
    return Circuit(name=name, top_module=top_module, properties=properties or {})


def module(
    name: str,
    *,
    class_name: str = "",
    parameters: list[_ParamSpec] | None = None,
    properties: dict[str, str] | None = None,
) -> Module:
    return Module(
        name=name,
        class_name=class_name,
        parameters=_make_params(parameters, {}),
        properties=properties or {},
    )


def module_reference(
    name: str,
    module_name: str,
    *,
    class_name: str = "",
    parameters: list[_ParamSpec] | None = None,
    properties: dict[str, str] | None = None,
    **param_kwargs: float,
) -> ModuleReference:
    return ModuleReference(
        name=name,
        module_name=module_name,
        class_name=class_name,
        parameters=_make_params(parameters, param_kwargs),
        properties=properties or {},
    )


def ext_module(
    name: str,
    *,
    class_name: str = "",
    library_name: str = "",
    group_name: str = "",
    ports: list[Port] | None = None,
    parameters: list[_ParamSpec] | None = None,
    properties: dict[str, str] | None = None,
) -> ExternalModule:
    return ExternalModule(
        name=name,
        class_name=class_name,
        library_name=library_name,
        group_name=group_name,
        ports=ports or [],
        parameters=_make_params(parameters, {}),
        properties=properties or {},
    )


def port(
    name: str,
    *,
    direction: PortDirection = PortDirection.INOUT,
    domain: SignalDomain = SignalDomain.UNSPECIFIED,
    width: int = 0,
    discipline: str = "",
    properties: dict[str, str] | None = None,
) -> Port:
    return Port(
        name=name,
        direction=direction,
        domain=domain,
        width=width,
        discipline=discipline,
        properties=properties or {},
    )


def connection(
    name: str,
    src: tuple[str, str],
    tgt: tuple[str, str],
    *,
    domain: SignalDomain = SignalDomain.UNSPECIFIED,
    properties: dict[str, str] | None = None,
) -> Connection:
    return Connection(
        name=name,
        source=PortReference(instance_name=src[0], port_name=src[1]),
        target=PortReference(instance_name=tgt[0], port_name=tgt[1]),
        domain=domain,
        properties=properties or {},
    )


def parameter(
    name: str,
    *,
    default_value: ParameterValue | None = None,
    description: str = "",
    properties: dict[str, str] | None = None,
) -> Parameter:
    return Parameter(
        name=name,
        default_value=default_value,
        description=description,
        properties=properties or {},
    )


def external_library(
    path: str,
    *,
    model_type: str = "",
    external_model_names: list[str] | None = None,
) -> ExternalLibrary:
    return ExternalLibrary(
        path=path,
        model_type=model_type,
        external_model_names=external_model_names or [],
    )


def model_interface(
    name: str,
    *,
    function_name: str = "",
    parameters: list[_ParamSpec] | None = None,
    properties: dict[str, str] | None = None,
) -> ModelInterface:
    return ModelInterface(
        name=name,
        function_name=function_name,
        parameters=_make_params(parameters, {}),
        properties=properties or {},
    )
