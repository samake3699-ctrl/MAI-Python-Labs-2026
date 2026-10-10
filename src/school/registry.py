
from typing import Callable

from .analysis import Analyzer, AnalysisContext, AnalysisReport
from .models import Submission


class AnalyzerRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], Analyzer]] = {}

    def register(
        self,
        analyzer_id: str,
        factory: Callable[[], Analyzer],
    ) -> None:
        if analyzer_id in self._factories:
            raise ValueError(
                f"Analyzer already registered: {analyzer_id}"
            )

        self._factories[analyzer_id] = factory

    def create(self, analyzer_id: str) -> Analyzer:
        if analyzer_id not in self._factories:
            raise ValueError(
                f"Unknown analyzer: {analyzer_id}"
            )

        return self._factories[analyzer_id]()


class AnalysisService:
    def __init__(self, registry: AnalyzerRegistry) -> None:
        self.registry = registry

    def run(
        self,
        analyzer_id: str,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:

        analyzer = self.registry.create(analyzer_id)

        return analyzer.analyze(submission, context)
