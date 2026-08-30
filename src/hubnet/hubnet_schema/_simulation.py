# ruff: noqa: RUF012
from __future__ import annotations

from enum import IntEnum
from typing import ClassVar

from hubnet.hubnet_schema import simulation_pb2 as pb
from hubnet.hubnet_schema._base import ProtoModel

__all__ = [
    "Analysis",
    "AnalysisKind",
    "InitialCondition",
    "Measurement",
    "OutputRequest",
    "OutputRequestKind",
    "Simulation",
]


# ======================================================================
# Enums
# ======================================================================


class AnalysisKind(IntEnum):
    UNSPECIFIED = 0
    OP = 1
    DC = 2
    AC = 3
    TRAN = 4
    NOISE = 5
    TF = 6
    SENS = 7
    PZ = 8
    DISTO = 9
    FOUR = 10
    FFT = 11


class OutputRequestKind(IntEnum):
    UNSPECIFIED = 0
    PRINT = 1
    PLOT = 2
    PROBE = 3
    SAVE = 4


# ======================================================================
# Simulation models
# ======================================================================


class Analysis(ProtoModel):
    _proto_type: ClassVar[type] = pb.Analysis

    kind: AnalysisKind = AnalysisKind.UNSPECIFIED
    name: str = ""
    arguments: list[str] = []
    options: dict[str, str] = {}


class OutputRequest(ProtoModel):
    _proto_type: ClassVar[type] = pb.OutputRequest

    kind: OutputRequestKind = OutputRequestKind.UNSPECIFIED
    analysis_type: str = ""
    variables: list[str] = []


class Measurement(ProtoModel):
    _proto_type: ClassVar[type] = pb.Measurement

    name: str = ""
    analysis_type: str = ""
    body: str = ""


class InitialCondition(ProtoModel):
    _proto_type: ClassVar[type] = pb.InitialCondition

    conditions: dict[str, str] = {}


class Simulation(ProtoModel):
    _proto_type: ClassVar[type] = pb.Simulation

    analyses: list[Analysis] = []
    output_requests: list[OutputRequest] = []
    measurements: list[Measurement] = []
    initial_conditions: InitialCondition | None = None
    node_sets: InitialCondition | None = None
    temperatures: list[float] = []
    options: dict[str, str] = {}
