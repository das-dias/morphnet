from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AnalysisKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ANALYSIS_KIND_UNSPECIFIED: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_OP: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_DC: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_AC: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_TRAN: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_NOISE: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_TF: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_SENS: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_PZ: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_DISTO: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_FOUR: _ClassVar[AnalysisKind]
    ANALYSIS_KIND_FFT: _ClassVar[AnalysisKind]

class OutputRequestKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OUTPUT_REQUEST_KIND_UNSPECIFIED: _ClassVar[OutputRequestKind]
    OUTPUT_REQUEST_KIND_PRINT: _ClassVar[OutputRequestKind]
    OUTPUT_REQUEST_KIND_PLOT: _ClassVar[OutputRequestKind]
    OUTPUT_REQUEST_KIND_PROBE: _ClassVar[OutputRequestKind]
    OUTPUT_REQUEST_KIND_SAVE: _ClassVar[OutputRequestKind]
ANALYSIS_KIND_UNSPECIFIED: AnalysisKind
ANALYSIS_KIND_OP: AnalysisKind
ANALYSIS_KIND_DC: AnalysisKind
ANALYSIS_KIND_AC: AnalysisKind
ANALYSIS_KIND_TRAN: AnalysisKind
ANALYSIS_KIND_NOISE: AnalysisKind
ANALYSIS_KIND_TF: AnalysisKind
ANALYSIS_KIND_SENS: AnalysisKind
ANALYSIS_KIND_PZ: AnalysisKind
ANALYSIS_KIND_DISTO: AnalysisKind
ANALYSIS_KIND_FOUR: AnalysisKind
ANALYSIS_KIND_FFT: AnalysisKind
OUTPUT_REQUEST_KIND_UNSPECIFIED: OutputRequestKind
OUTPUT_REQUEST_KIND_PRINT: OutputRequestKind
OUTPUT_REQUEST_KIND_PLOT: OutputRequestKind
OUTPUT_REQUEST_KIND_PROBE: OutputRequestKind
OUTPUT_REQUEST_KIND_SAVE: OutputRequestKind

class Analysis(_message.Message):
    __slots__ = ("kind", "name", "arguments", "options")
    class OptionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    KIND_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ARGUMENTS_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    kind: AnalysisKind
    name: str
    arguments: _containers.RepeatedScalarFieldContainer[str]
    options: _containers.ScalarMap[str, str]
    def __init__(self, kind: _Optional[_Union[AnalysisKind, str]] = ..., name: _Optional[str] = ..., arguments: _Optional[_Iterable[str]] = ..., options: _Optional[_Mapping[str, str]] = ...) -> None: ...

class OutputRequest(_message.Message):
    __slots__ = ("kind", "analysis_type", "variables")
    KIND_FIELD_NUMBER: _ClassVar[int]
    ANALYSIS_TYPE_FIELD_NUMBER: _ClassVar[int]
    VARIABLES_FIELD_NUMBER: _ClassVar[int]
    kind: OutputRequestKind
    analysis_type: str
    variables: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, kind: _Optional[_Union[OutputRequestKind, str]] = ..., analysis_type: _Optional[str] = ..., variables: _Optional[_Iterable[str]] = ...) -> None: ...

class Measurement(_message.Message):
    __slots__ = ("name", "analysis_type", "body")
    NAME_FIELD_NUMBER: _ClassVar[int]
    ANALYSIS_TYPE_FIELD_NUMBER: _ClassVar[int]
    BODY_FIELD_NUMBER: _ClassVar[int]
    name: str
    analysis_type: str
    body: str
    def __init__(self, name: _Optional[str] = ..., analysis_type: _Optional[str] = ..., body: _Optional[str] = ...) -> None: ...

class InitialCondition(_message.Message):
    __slots__ = ("conditions",)
    class ConditionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    conditions: _containers.ScalarMap[str, str]
    def __init__(self, conditions: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Simulation(_message.Message):
    __slots__ = ("analyses", "output_requests", "measurements", "initial_conditions", "node_sets", "temperatures", "options")
    class OptionsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ANALYSES_FIELD_NUMBER: _ClassVar[int]
    OUTPUT_REQUESTS_FIELD_NUMBER: _ClassVar[int]
    MEASUREMENTS_FIELD_NUMBER: _ClassVar[int]
    INITIAL_CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    NODE_SETS_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURES_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    analyses: _containers.RepeatedCompositeFieldContainer[Analysis]
    output_requests: _containers.RepeatedCompositeFieldContainer[OutputRequest]
    measurements: _containers.RepeatedCompositeFieldContainer[Measurement]
    initial_conditions: InitialCondition
    node_sets: InitialCondition
    temperatures: _containers.RepeatedScalarFieldContainer[float]
    options: _containers.ScalarMap[str, str]
    def __init__(self, analyses: _Optional[_Iterable[_Union[Analysis, _Mapping]]] = ..., output_requests: _Optional[_Iterable[_Union[OutputRequest, _Mapping]]] = ..., measurements: _Optional[_Iterable[_Union[Measurement, _Mapping]]] = ..., initial_conditions: _Optional[_Union[InitialCondition, _Mapping]] = ..., node_sets: _Optional[_Union[InitialCondition, _Mapping]] = ..., temperatures: _Optional[_Iterable[float]] = ..., options: _Optional[_Mapping[str, str]] = ...) -> None: ...
