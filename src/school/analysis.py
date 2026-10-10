
from dataclasses import dataclass, field
from typing import Any, Protocol

from .models import Submission


@dataclass(frozen=True)
class AnalysisReport:
    analyzer_id: str
    analyzer_version: str
    submission_id: str
    rubric_feedback: list[dict[str, Any]] = field(
        default_factory=list
    )
    similarity: float | None = None
    evidence: list[dict[str, Any]] = field(
        default_factory=list
    )


@dataclass(frozen=True)
class AnalysisContext:
    assignment: dict[str, Any]
    templates: dict[str, str] = field(
        default_factory=dict
    )


class Analyzer(Protocol):
    analyzer_id: str
    analyzer_version: str

    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:
        ...
