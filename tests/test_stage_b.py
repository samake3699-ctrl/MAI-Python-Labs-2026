
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from src.school.analysis import AnalysisContext
from src.school.analyzers import LengthAnalyzer, TemplateAnalyzer
from src.school.parser import parse_submission
from src.school.registry import AnalyzerRegistry, AnalysisService
from src.school.sources import (
    InMemoryTemplateSource,
    JSONLTemplateSource,
)


def make_submission():
    return parse_submission({
        "schema_version": 1,
        "submission_id": "test-001",
        "student_id": "student-001",
        "assignment_id": "assignment-001",
        "submitted_at": "2026-10-10T12:00:00+03:00",
        "text": "First line\n\nSecond line",
        "code": "print('Hello')\n\nprint('Python')",
        "template_id": "template-001",
        "ai_declaration": {
            "used": False,
            "verified_by_student": True,
            "tool": None,
            "purpose": None,
        },
    })


class TestStageB(unittest.TestCase):

    def setUp(self):
        self.submission = make_submission()
        self.templates = {
            "template-001": "print('Hello')\nprint('Example')"
        }
        self.context = AnalysisContext(
            assignment={"assignment_id": "assignment-001"},
            templates=self.templates,
        )

    def test_length_analyzer(self):
        report = LengthAnalyzer().analyze(
            self.submission, self.context
        )

        self.assertEqual(report.analyzer_id, "length")
        self.assertEqual(report.analyzer_version, "1.0")
        self.assertIsNone(report.similarity)
        self.assertIsNone(report.rubric_feedback[0]["score"])
        self.assertIn(
            "Text: 2 non-empty lines; Code: 2 non-empty lines.",
            report.rubric_feedback[0]["message"],
        )

    def test_template_analyzer(self):
        report = TemplateAnalyzer().analyze(
            self.submission, self.context
        )

        self.assertEqual(report.similarity, 0.5)
        self.assertEqual(len(report.evidence), 1)
        self.assertEqual(report.evidence[0]["start_line"], 1)
        self.assertEqual(report.evidence[0]["end_line"], 1)
        self.assertIn(
            "permitted",
            report.rubric_feedback[0]["message"],
        )

    def test_evidence_line_numbers(self):
        report = TemplateAnalyzer().analyze(
            self.submission, self.context
        )

        lines = self.submission.code.splitlines()

        for evidence in report.evidence:
            start = evidence["start_line"]
            end = evidence["end_line"]

            self.assertGreaterEqual(start, 1)
            self.assertLessEqual(start, end)
            self.assertLessEqual(end, len(lines))
            self.assertEqual(
                evidence["text"],
                lines[start - 1],
            )

    def test_missing_template(self):
        context = AnalysisContext(
            assignment={},
            templates={},
        )

        report = TemplateAnalyzer().analyze(
            self.submission, context
        )

        self.assertEqual(report.similarity, 0.0)
        self.assertEqual(report.evidence, [])

    def test_submission_immutability(self):
        original_text = self.submission.text
        original_code = self.submission.code

        LengthAnalyzer().analyze(
            self.submission, self.context
        )
        TemplateAnalyzer().analyze(
            self.submission, self.context
        )

        self.assertEqual(self.submission.text, original_text)
        self.assertEqual(self.submission.code, original_code)

        with self.assertRaises(FrozenInstanceError):
            self.submission.text = "Modified"

    def test_registry_and_service(self):
        registry = AnalyzerRegistry()
        registry.register("length", LengthAnalyzer)
        registry.register("template", TemplateAnalyzer)

        service = AnalysisService(registry)

        self.assertEqual(
            service.run(
                "length", self.submission, self.context
            ).analyzer_id,
            "length",
        )

        self.assertEqual(
            service.run(
                "template", self.submission, self.context
            ).analyzer_id,
            "template",
        )

    def test_unknown_analyzer(self):
        registry = AnalyzerRegistry()
        service = AnalysisService(registry)

        with self.assertRaises(ValueError):
            service.run(
                "unknown", self.submission, self.context
            )

    def test_analyzer_exception(self):
        class FailingAnalyzer:
            analyzer_id = "failing"
            analyzer_version = "1.0"

            def analyze(self, submission, context):
                raise RuntimeError("Analysis failed")

        registry = AnalyzerRegistry()
        registry.register("failing", FailingAnalyzer)

        service = AnalysisService(registry)

        with self.assertRaisesRegex(
            RuntimeError, "Analysis failed"
        ):
            service.run(
                "failing", self.submission, self.context
            )

    def test_in_memory_source(self):
        source = InMemoryTemplateSource(self.templates)

        self.assertEqual(
            source.get_templates(),
            self.templates,
        )

        # The returned dictionary must be independent.
        result = source.get_templates()
        result.clear()

        self.assertEqual(
            source.get_templates(),
            self.templates,
        )

    def test_jsonl_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "templates.jsonl"

            with path.open("w", encoding="utf-8") as file:
                for template_id, content in self.templates.items():
                    file.write(json.dumps({
                        "template_id": template_id,
                        "content": content,
                    }) + "\n")

            source = JSONLTemplateSource(path)

            with source as opened:
                self.assertEqual(
                    opened.get_templates(),
                    self.templates,
                )

            self.assertIsNone(source._file)

    def test_jsonl_source_closes_on_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.jsonl"
            path.write_text(
                "{invalid json}\n",
                encoding="utf-8",
            )

            source = JSONLTemplateSource(path)

            with self.assertRaises(ValueError):
                with source as opened:
                    opened.get_templates()

            self.assertIsNone(source._file)

    def test_jsonl_source_closes_on_early_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "templates.jsonl"
            path.write_text(
                json.dumps({
                    "template_id": "t1",
                    "content": "print(1)",
                }) + "\n",
                encoding="utf-8",
            )

            source = JSONLTemplateSource(path)

            with source as opened:
                self.assertIn(
                    "t1",
                    opened.get_templates(),
                )
                # Leave the with block before any further work.

            self.assertIsNone(source._file)

    def test_both_sources_same_analyzer_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "templates.jsonl"
            path.write_text(
                json.dumps({
                    "template_id": "template-001",
                    "content": self.templates["template-001"],
                }) + "\n",
                encoding="utf-8",
            )

            memory_source = InMemoryTemplateSource(
                self.templates
            )

            with JSONLTemplateSource(path) as file_source:
                for source in (memory_source, file_source):
                    with self.subTest(source=type(source).__name__):
                        context = AnalysisContext(
                            assignment={},
                            templates=source.get_templates(),
                        )

                        report = TemplateAnalyzer().analyze(
                            self.submission,
                            context,
                        )

                        self.assertEqual(report.similarity, 0.5)
                        self.assertEqual(len(report.evidence), 1)


if __name__ == "__main__":
    unittest.main()
