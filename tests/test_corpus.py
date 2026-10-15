import json
import tempfile
import unittest
from pathlib import Path

from src.school.corpus import generate_corpus
from src.school.parser import parse_submission
from src.school.validation import validate_submission


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class TestCorpus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        generate_corpus(self.directory)
        self.submissions = load_jsonl(self.directory / "submissions.jsonl")
        self.provenance = load_jsonl(self.directory / "provenance.jsonl")
        self.pairs = load_jsonl(self.directory / "pairs.jsonl")

    def test_counts(self):
        self.assertEqual(len(self.submissions), 30)
        self.assertEqual(len(self.provenance), 30)
        self.assertEqual(len(self.pairs), 40)

    def test_all_submissions_validate(self):
        for raw in self.submissions:
            self.assertEqual(validate_submission(parse_submission(raw)), [])

    def test_pair_labels_and_student_separation(self):
        records = {s["submission_id"]: s for s in self.submissions}
        for pair in self.pairs:
            a, b = records[pair["left_id"]], records[pair["right_id"]]
            self.assertNotEqual(a["student_id"], b["student_id"])
            self.assertEqual(a["assignment_id"], b["assignment_id"])
            self.assertEqual(pair["derivation_relation"],
                             pair["left_family_id"] == pair["right_family_id"])
        self.assertGreaterEqual(sum(p["template_only"] for p in self.pairs), 5)

    def test_no_family_leakage(self):
        families = {"tuning": set(), "evaluation": set()}
        for item in self.provenance:
            families[item["split"]].add(item["family_id"])
        self.assertTrue(families["tuning"].isdisjoint(families["evaluation"]))
        for pair in self.pairs:
            prov = {r["submission_id"]: r for r in self.provenance}
            self.assertEqual(prov[pair["left_id"]]["split"], pair["split"])
            self.assertEqual(prov[pair["right_id"]]["split"], pair["split"])

    def test_deterministic(self):
        before = (self.directory / "pairs.jsonl").read_bytes()
        generate_corpus(self.directory)
        self.assertEqual(before, (self.directory / "pairs.jsonl").read_bytes())


if __name__ == "__main__":
    unittest.main()
