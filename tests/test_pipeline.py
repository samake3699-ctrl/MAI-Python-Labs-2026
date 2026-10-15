import json
import tempfile
import unittest
from pathlib import Path

from src.school.models import Submission
from src.school.streaming import iter_validated_submissions


ROOT = Path(__file__).resolve().parents[1]


class TestValidationPipeline(unittest.TestCase):

    def setUp(self):
        path = ROOT / "valid_submission.jsonl"
        self.valid = json.loads(
            path.read_text(encoding="utf-8").splitlines()[0]
        )

    def run_pipeline(self, lines):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.jsonl"
            path.write_text("\n".join(lines), encoding="utf-8")
            return list(iter_validated_submissions(path))

    def test_valid_submission(self):
        results = self.run_pipeline([
            json.dumps(self.valid)
        ])

        self.assertEqual(len(results), 1)

        line_number, submission, error = results[0]

        self.assertEqual(line_number, 1)
        self.assertIsInstance(submission, Submission)
        self.assertIsNone(error)

    def test_invalid_student_id(self):
        invalid = {
            **self.valid,
            "student_id": "",
        }

        results = self.run_pipeline([
            json.dumps(invalid)
        ])

        self.assertIsNone(results[0][1])
        self.assertIn("student_id", results[0][2])

    def test_continue_after_errors(self):
        another_valid = {
            **self.valid,
            "submission_id": "sub-002",
        }

        results = self.run_pipeline([
            json.dumps(self.valid),
            '{"broken":',
            json.dumps(another_valid),
        ])

        self.assertEqual(len(results), 3)

        self.assertIsInstance(results[0][1], Submission)
        self.assertIsNotNone(results[1][2])
        self.assertIsInstance(results[2][1], Submission)

        self.assertEqual(
            results[2][1].submission_id,
            "sub-002",
        )


if __name__ == "__main__":
    unittest.main()