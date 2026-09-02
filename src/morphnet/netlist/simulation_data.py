from __future__ import annotations

from morphnet.morphnet_schema import AnalysisKind, OutputRequestKind


class AnalysisData:
    __slots__ = ("arguments", "kind", "name", "options")

    def __init__(
        self,
        kind: str,
        arguments: list[str],
        options: dict[str, str],
        name: str = "",
    ) -> None:
        self.kind = kind
        self.name = name
        self.arguments = arguments
        self.options = options


class OutputRequestData:
    __slots__ = ("analysis_type", "kind", "variables")

    def __init__(
        self,
        kind: str,
        analysis_type: str,
        variables: list[str],
    ) -> None:
        self.kind = kind
        self.analysis_type = analysis_type
        self.variables = variables


class MeasurementData:
    __slots__ = ("analysis_type", "body", "name")

    def __init__(self, name: str, analysis_type: str, body: str) -> None:
        self.name = name
        self.analysis_type = analysis_type
        self.body = body


class InitialConditionData:
    __slots__ = ("conditions", "kind")

    def __init__(self, kind: str, conditions: dict[str, str]) -> None:
        self.kind = kind
        self.conditions = conditions


class TemperatureData:
    __slots__ = ("temperatures",)

    def __init__(self, temperatures: list[float]) -> None:
        self.temperatures = temperatures


ANALYSIS_KIND_MAP: dict[str, AnalysisKind] = {
    "op": AnalysisKind.OP,
    "dc": AnalysisKind.DC,
    "ac": AnalysisKind.AC,
    "tran": AnalysisKind.TRAN,
    "noise": AnalysisKind.NOISE,
    "tf": AnalysisKind.TF,
    "sens": AnalysisKind.SENS,
    "pz": AnalysisKind.PZ,
    "disto": AnalysisKind.DISTO,
    "four": AnalysisKind.FOUR,
    "fft": AnalysisKind.FFT,
}

OUTPUT_REQUEST_KIND_MAP: dict[str, OutputRequestKind] = {
    "print": OutputRequestKind.PRINT,
    "plot": OutputRequestKind.PLOT,
    "probe": OutputRequestKind.PROBE,
    "save": OutputRequestKind.SAVE,
}
