import json
import tempfile
import unittest
from pathlib import Path

from src.school.streaming import iter_jsonl_results


class TestStreaming(unittest.TestCase):

    def test_continue_after_invalid_json(self):
        """Une ligne incorrecte ne doit pas arrêter la lecture."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.jsonl"

            lines = [
                json.dumps({"submission_id": "sub-001"}),
                '{"submission_id":',
                json.dumps({"submission_id": "sub-003"}),
            ]

            path.write_text("\n".join(lines), encoding="utf-8")

            results = list(iter_jsonl_results(path))

            self.assertEqual(len(results), 3)

            self.assertEqual(results[0][1]["submission_id"], "sub-001")
            self.assertIsNone(results[0][2])

            self.assertIsNone(results[1][1])
            self.assertIn("JSON invalide", results[1][2])

            self.assertEqual(results[2][1]["submission_id"], "sub-003")
            self.assertIsNone(results[2][2])

    def test_reject_non_object_json(self):
        """Un tableau JSON ne doit pas être accepté comme objet."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.jsonl"

            path.write_text("[1, 2, 3]\n", encoding="utf-8")

            results = list(iter_jsonl_results(path))

            self.assertEqual(len(results), 1)
            self.assertIsNone(results[0][1])
            self.assertIn("objet JSON", results[0][2])

    def test_skip_empty_lines(self):
        """Les lignes vides sont ignorées, sans fausser les numéros."""

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.jsonl"

            path.write_text(
                '\n{"submission_id": "sub-001"}\n\n',
                encoding="utf-8",
            )

            results = list(iter_jsonl_results(path))

            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][0], 2)


if __name__ == "__main__":
    unittest.main()