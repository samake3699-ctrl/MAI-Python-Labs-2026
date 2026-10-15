
import json
import tempfile
import unittest
from pathlib import Path

from src.school.audit import audit_corpus, check_evidence
from src.school.corpus import generate_corpus


class TestLab2Audit(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.directory = Path(self.temp.name)
        generate_corpus(self.directory)

    def test_valid_corpus(self):
        report = audit_corpus(self.directory)

        self.assertEqual(report["n_submissions"], 30)
        self.assertEqual(report["n_pairs"], 40)
        self.assertEqual(report["n_tuning"], 20)
        self.assertEqual(report["n_evaluation"], 20)

        self.assertGreaterEqual(
            report["n_template_only"], 5
        )

    def test_valid_line_range(self):
        check_evidence(
            {
                "left_start": 1,
                "left_end": 2,
                "right_start": 2,
                "right_end": 3,
            },
            "x=1\nprint(x)\n",
            "# note\nx=1\nprint(x)\n",
        )

    def test_out_of_bounds_line_range_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError, "Preuve invalide"
        ):
            check_evidence(
                {
                    "left_start": 1,
                    "left_end": 90,
                    "right_start": 1,
                    "right_end": 1,
                },
                "x=1\n",
                "y=2\n",
            )

    def test_family_leakage_is_rejected(self):
        path = self.directory / "provenance.jsonl"

        records = [
            json.loads(row)
            for row in path.read_text(
                encoding="utf-8"
            ).splitlines()
        ]

        records[-1]["family_id"] = "family-00"

        path.write_text(
            "\n".join(json.dumps(row) for row in records)
            + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError, "Fuite de familles"
        ):
            audit_corpus(self.directory)

    def test_self_match_is_rejected(self):
        path = self.directory / "pairs.jsonl"

        records = [
            json.loads(row)
            for row in path.read_text(
                encoding="utf-8"
            ).splitlines()
        ]

        records[0]["right_id"] = records[0]["left_id"]

        path.write_text(
            "\n".join(json.dumps(row) for row in records)
            + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError, "Self-match"
        ):
            audit_corpus(self.directory)


if __name__ == "__main__":
    unittest.main()
