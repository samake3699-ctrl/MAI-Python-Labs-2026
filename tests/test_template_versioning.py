
import json
import tempfile
import unittest
from pathlib import Path

from src.school.corpus import generate_corpus
from src.school.template_versioning import (
    ensure_config,
    run_demo,
)


class TestTemplateVersioning(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.directory = Path(self.temp.name)
        generate_corpus(self.directory)

    def test_new_template_changes_scores(self):
        result = run_demo(self.directory)

        self.assertGreater(
            result["changed_pairs"],
            0,
        )

        self.assertEqual(
            result["changed_submissions"],
            18,
        )

        self.assertEqual(result["to"], "v2")

    def test_original_corpus_not_modified(self):
        source = self.directory / "submissions.jsonl"
        before = source.read_bytes()

        run_demo(self.directory)

        self.assertEqual(
            source.read_bytes(),
            before,
        )

    def test_report_is_versioned(self):
        run_demo(self.directory)

        path = (
            self.directory
            / "demo_v2"
            / "evaluation_report_v2.json"
        )

        report = json.loads(
            path.read_text(encoding="utf-8")
        )

        self.assertEqual(
            report["report_version"],
            "v2",
        )

        self.assertEqual(
            len(report["config_sha256"]),
            64,
        )

        self.assertEqual(report["n_pairs"], 40)

    def test_invalid_configuration_rejected(self):
        path = ensure_config(self.directory)

        config = json.loads(
            path.read_text(encoding="utf-8")
        )

        config["replace_template_id"]["to"] = "unknown"

        path.write_text(
            json.dumps(config),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Identifiants",
        ):
            run_demo(self.directory)


if __name__ == "__main__":
    unittest.main()
