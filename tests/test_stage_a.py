
import json
import tempfile
import unittest
from pathlib import Path

from src.school.parser import import_jsonl
from src.school.repository import InMemorySubmissionRepository


VALID = {
    "schema_version": 1,
    "submission_id": "sub-001",
    "student_id": "student-001",
    "assignment_id": "assignment-001",
    "submitted_at": "2026-10-07T12:00:00+00:00",
    "text": "Hello",
    "code": "",
    "template_id": None,
    "ai_declaration": {
        "used": False,
        "verified_by_student": True,
        "tool": None,
        "purpose": None,
    },
}


class TestStageA(unittest.TestCase):

    def import_records(self, records):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.jsonl"
            path.write_text(
                "\n".join(
                    json.dumps(record) if isinstance(record, dict)
                    else record
                    for record in records
                ) + "\n",
                encoding="utf-8",
            )
            repo = InMemorySubmissionRepository()
            result = import_jsonl(str(path), repo)
            return result, repo

    def test_valid_submission(self):
        result, repo = self.import_records([VALID])
        self.assertEqual(result.accepted, 1)
        self.assertEqual(repo.count(), 1)

    def test_invalid_date(self):
        record = {**VALID, "submitted_at": "bonjour"}
        result, _ = self.import_records([record])
        self.assertEqual(result.accepted, 0)
        self.assertEqual(result.errors[0]["field"], "submitted_at")

    def test_empty_student_id(self):
        record = {**VALID, "student_id": ""}
        result, _ = self.import_records([record])
        self.assertEqual(result.accepted, 0)
        self.assertTrue(result.errors)

    def test_unknown_field(self):
        record = {**VALID, "age": 25}
        result, _ = self.import_records([record])
        self.assertEqual(result.accepted, 0)
        self.assertEqual(result.errors[0]["code"], "SCHEMA_ERROR")

    def test_duplicate(self):
        result, repo = self.import_records([VALID, VALID])
        self.assertEqual(result.accepted, 1)
        self.assertEqual(result.duplicates, 1)
        self.assertEqual(repo.count(), 1)

    def test_conflict(self):
        changed = {**VALID, "text": "Different content"}
        result, repo = self.import_records([VALID, changed])
        self.assertEqual(result.accepted, 1)
        self.assertEqual(result.conflicts, 1)
        self.assertEqual(repo.count(), 1)

    def test_invalid_json_continues(self):
        result, repo = self.import_records([
            VALID,
            "{invalid json",
            {**VALID, "submission_id": "sub-002"},
        ])
        self.assertEqual(result.accepted, 2)
        self.assertEqual(repo.count(), 2)
        self.assertTrue(
            any(
                getattr(error, "line_number", None) == 2
                for error in result.errors
            )
        )


if __name__ == "__main__":
    unittest.main()
