import json
import tempfile
import unittest
from pathlib import Path

from src.school.candidates import (
    common_token_evidence,
    iter_candidates,
    top_candidates,
    without_authorized_template,
)
from src.school.corpus import generate_corpus
from src.school.models import AIDeclaration, Submission
from src.school.streaming import iter_validated_submissions
from datetime import datetime, timezone


TEMPLATE = "print('Hello')\nprint('Example')\n"
TEMPLATES = {"template-001": TEMPLATE}


def example(sid, student, code, assignment="assignment-001", template_id=None):
    return Submission(
        schema_version=1,
        submission_id=sid,
        student_id=student,
        assignment_id=assignment,
        submitted_at=datetime(2026, 10, 15, tzinfo=timezone.utc),
        ai_declaration=AIDeclaration(used=False, verified_by_student=True),
        text="exemple de test",
        code=code,
        template_id=template_id,
    )


class TestCandidates(unittest.TestCase):
    def test_exclude_self_same_student_and_other_assignment(self):
        source = example("a", "s1", "x = 1\nprint(x)")
        candidates = [
            source,
            example("a2", "s1", "x = 1\nprint(x)"),
            example("other-task", "s2", "x = 1\nprint(x)", "assignment-002"),
            example("valid", "s2", "x = 1\nprint(x)"),
        ]
        result = list(iter_candidates(source, candidates, {}))
        self.assertEqual([item.candidate_id for item in result], ["valid"])

    def test_other_students_versions_remain_distinct(self):
        source = example("a", "s1", "x = 1\nprint(x)")
        records = [example("b1", "s2", "x=1\nprint(x)"),
                   example("b2", "s2", "x=2\nprint(x)")]
        found = list(iter_candidates(source, records, {}))
        self.assertEqual([r.candidate_id for r in found], ["b1", "b2"])

    def test_template_only_is_insufficient_not_accusation(self):
        source = example("a", "s1", TEMPLATE, template_id="template-001")
        other = example("b", "s2", TEMPLATE, template_id="template-001")
        candidate = next(iter(iter_candidates(source, [other], TEMPLATES)))
        self.assertIsNone(candidate.token_score)
        self.assertIsNone(candidate.ast_score)
        self.assertIsNone(candidate.evidence)
        self.assertEqual(candidate.authorized_template_lines_source, (1, 2))
        self.assertEqual(candidate.authorized_template_lines_candidate, (1, 2))

    def test_evidence_points_to_real_lines(self):
        evidence = common_token_evidence("x=3\nprint(x)\n", "# note\nx = 3\nprint(x)\n")
        self.assertIsNotNone(evidence)
        self.assertEqual(evidence.left_start, 1)
        self.assertEqual(evidence.right_start, 2)
        self.assertGreaterEqual(evidence.left_end, evidence.left_start)
        self.assertLessEqual(evidence.right_end, 3)

    def test_template_removal_preserves_line_numbers(self):
        submission = example("a", "s1", TEMPLATE + "x=3\nprint(x)", template_id="template-001")
        cleaned, removed = without_authorized_template(submission, TEMPLATES)
        self.assertEqual(removed, (1, 2))
        token = common_token_evidence(cleaned, cleaned)
        self.assertIsNotNone(token)
        self.assertEqual(token.left_start, 3)

    def test_ast_syntax_error_is_reported_without_crash(self):
        source = example("a", "s1", "x=1\n")
        other = example("b", "s2", "x = 1+\n")
        candidate = next(iter(iter_candidates(source, [other], {})))
        self.assertIsNone(candidate.ast_score)
        self.assertIn("AST impossible", candidate.warning)

    def test_top_candidates_limits_and_validates_limit(self):
        source = example("a", "s1", "x=1\nprint(x)")
        records = [example("b", "s2", "x=1\nprint(x)"),
                   example("c", "s3", "a=[1,2]\nprint(a)")]
        result = top_candidates(source, records, {}, limit=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].candidate_id, "b")
        with self.assertRaises(ValueError):
            top_candidates(source, records, {}, limit=-1)

    def test_generated_corpus_integrates_with_streaming(self):
        with tempfile.TemporaryDirectory() as directory:
            generate_corpus(directory)
            path = Path(directory) / "submissions.jsonl"
            results = list(iter_validated_submissions(path))
            self.assertEqual(len(results), 30)
            self.assertTrue(all(error is None for _, _, error in results))
            records = [submission for _, submission, _ in results]
            source = records[0]
            candidates = list(iter_candidates(source, records, TEMPLATES))
            self.assertEqual(len(candidates), 29)
            self.assertTrue(all(r.candidate_id != source.submission_id for r in candidates))
            self.assertTrue(all(r.source_id == source.submission_id for r in candidates))


if __name__ == "__main__":
    unittest.main()
