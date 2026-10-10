
from .models import Submission
from .analysis import AnalysisReport, AnalysisContext


class LengthAnalyzer:
    analyzer_id = "length"
    analyzer_version = "1.0"

    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:

        text_lines = sum(
            1 for line in submission.text.splitlines()
            if line.strip()
        )

        code_lines = sum(
            1 for line in submission.code.splitlines()
            if line.strip()
        )

        return AnalysisReport(
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            submission_id=submission.submission_id,
            rubric_feedback=[
                {
                    "criterion": "length",
                    "score": None,
                    "message": (
                        f"Text: {text_lines} non-empty lines; "
                        f"Code: {code_lines} non-empty lines."
                    ),
                }
            ],
        )


class TemplateAnalyzer:
    analyzer_id = "template"
    analyzer_version = "1.0"

    def analyze(
        self,
        submission: Submission,
        context: AnalysisContext,
    ) -> AnalysisReport:

        template = context.templates.get(
            submission.template_id or ""
        )

        if not template:
            return AnalysisReport(
                analyzer_id=self.analyzer_id,
                analyzer_version=self.analyzer_version,
                submission_id=submission.submission_id,
                similarity=0.0,
                rubric_feedback=[
                    {
                        "criterion": "template_similarity",
                        "score": None,
                        "message": "No authorized template available.",
                    }
                ],
            )

        template_lines = {
            line for line in template.splitlines()
            if line.strip()
        }

        code_lines = submission.code.splitlines()

        evidence = [
            {
                "field": "code",
                "start_line": number,
                "end_line": number,
                "text": line,
            }
            for number, line in enumerate(code_lines, start=1)
            if line.strip() and line in template_lines
        ]

        nonempty_count = sum(
            1 for line in code_lines if line.strip()
        )

        similarity = (
            len(evidence) / nonempty_count
            if nonempty_count else 0.0
        )

        return AnalysisReport(
            analyzer_id=self.analyzer_id,
            analyzer_version=self.analyzer_version,
            submission_id=submission.submission_id,
            similarity=similarity,
            evidence=evidence,
            rubric_feedback=[
                {
                    "criterion": "template_similarity",
                    "score": None,
                    "message": (
                        "Exact matches with an authorized template "
                        "are permitted and are not evidence of misconduct."
                    ),
                }
            ],
        )
