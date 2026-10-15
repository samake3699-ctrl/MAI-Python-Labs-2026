"""Tests du réglage des seuils et des métriques du Lab 2."""
import json
import tempfile
import unittest
from pathlib import Path

from src.school.corpus import generate_corpus
from src.school.evaluation import (
    ScoredPair,
    build_report,
    choose_threshold,
    confusion_metrics,
    load_scored_pairs,
)


def pair(sid, label, token, ast_score=None):
    return ScoredPair(
        pair_id=sid, left_id=sid + "-a", right_id=sid + "-b",
        split="tuning", derivation_relation=label, template_only=False,
        token_score=token, ast_score=ast_score,
        evidence=None, warning=None,
    )


class TestMetrics(unittest.TestCase):
    def test_confusion_matrix_precision_recall_f1(self):
        pairs = [
            pair("p1", True, .9),    # TP
            pair("p2", True, .7),    # TP
            pair("p3", True, .1),    # FN
            pair("p4", False, .8),   # FP
            pair("p5", False, .2),   # TN
        ]
        report = confusion_metrics(pairs, "token", .5)
        self.assertEqual(report["confusion_matrix"], [[1, 1], [1, 2]])
        self.assertAlmostEqual(report["precision"], 2 / 3)
        self.assertAlmostEqual(report["recall"], 2 / 3)
        self.assertAlmostEqual(report["f1"], 2 / 3)

    def test_undefined_scores_are_reported_separately(self):
        pairs = [pair("a", True, None), pair("b", False, .1)]
        result = confusion_metrics(pairs, "token", .5)
        self.assertEqual(result["undefined"], 1)
        self.assertEqual(result["scored_pairs"], 1)
        self.assertAlmostEqual(result["undefined_fraction"], .5)
        self.assertEqual(result["confusion_matrix"], [[1, 0], [0, 0]])

    def test_empty_pairs_safe(self):
        result = confusion_metrics([], "token", .5)
        self.assertEqual(result["f1"], 0)
        self.assertEqual(result["undefined_fraction"], 0)

    def test_threshold_bounds_and_invalid_method(self):
        with self.assertRaises(ValueError):
            confusion_metrics([], "token", 1.1)
        with self.assertRaises(ValueError):
            confusion_metrics([pair("a", True, .8)], "unknown", .5)

    def test_select_threshold_from_tuning_only(self):
        tuning = [
            pair("t1", True, .9),
            pair("t2", True, .8),
            pair("t3", False, .5),
        ]
        self.assertEqual(choose_threshold(tuning, "token"), .8)
        # Les scores d'une future évaluation ne sont jamais passés à choose_threshold.

    def test_select_threshold_requires_defined_scores(self):
        with self.assertRaises(ValueError):
            choose_threshold([pair("t1", True, None)], "token")


class TestEndToEndEvaluation(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name)
        generate_corpus(self.path)

    def test_fixed_splits_counts_and_methods(self):
        report = build_report(self.path)
        self.assertEqual((report["n_pairs"], report["n_tuning"], report["n_evaluation"]), (40, 20, 20))
        self.assertEqual(set(report["methods"]), {"token", "ast"})
        for method in ("token", "ast"):
            self.assertEqual(report["methods"][method]["evaluation"]["total_pairs"], 20)
            self.assertGreaterEqual(report["methods"][method]["evaluation"]["f1"], 0)
            self.assertLessEqual(report["methods"][method]["evaluation"]["f1"], 1)

    def test_reports_are_reproducible(self):
        self.assertEqual(build_report(self.path), build_report(self.path))

    def test_template_only_cases_visible_in_report(self):
        report = build_report(self.path)
        self.assertGreaterEqual(sum(p["template_only"] for p in report["evaluated_pairs"]), 3)
        self.assertTrue(all("review_required" in p for p in report["evaluated_pairs"]))

    def test_family_leakage_detected(self):
        path = self.path / "provenance.jsonl"
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        records[-1]["family_id"] = "family-00"
        path.write_text("\n".join(json.dumps(x) for x in records) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Fuite de familles"):
            load_scored_pairs(self.path)

    def test_missing_submission_rejected(self):
        path = self.path / "pairs.jsonl"
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        records[0]["right_id"] = "unknown-submission"
        path.write_text("\n".join(json.dumps(x) for x in records) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Soumission inconnue"):
            load_scored_pairs(self.path)


if __name__ == "__main__":
    unittest.main()
