
import tempfile
import unittest
from pathlib import Path

from src.school.corpus import generate_corpus
from src.school.evaluation import ScoredPair
from src.school.error_analysis import (
    categorize,
    explain_case,
    analyze_errors,
    render_markdown,
)


def sample_pair(label, score, template_only=False):
    """Construire une paire fictive pour les tests."""

    return ScoredPair(
        pair_id="test-pair",
        left_id="sub-a",
        right_id="sub-b",
        split="evaluation",
        derivation_relation=label,
        template_only=template_only,
        token_score=score,
        ast_score=score,
        evidence=None,
        warning=None,
    )


class TestErrorCategories(unittest.TestCase):

    def test_true_positive(self):
        pair = sample_pair(True, 0.9)
        self.assertEqual(
            categorize(pair, "token", 0.5),
            "vrai_positif",
        )

    def test_false_positive(self):
        pair = sample_pair(False, 0.9)
        self.assertEqual(
            categorize(pair, "token", 0.5),
            "faux_positif",
        )

    def test_false_negative(self):
        pair = sample_pair(True, 0.1)
        self.assertEqual(
            categorize(pair, "token", 0.5),
            "faux_negatif",
        )

    def test_true_negative(self):
        pair = sample_pair(False, 0.1)
        self.assertEqual(
            categorize(pair, "token", 0.5),
            "vrai_negatif",
        )

    def test_undefined_score(self):
        pair = sample_pair(True, None)
        self.assertEqual(
            categorize(pair, "ast", 0.5),
            "indetermine",
        )

    def test_invalid_threshold(self):
        pair = sample_pair(True, 0.8)
        with self.assertRaises(ValueError):
            categorize(pair, "token", 1.5)

    def test_authorized_template_explanation(self):
        message = explain_case(
            "faux_positif",
            template_only=True,
        )
        self.assertIn("modèle autorisé", message)


class TestCorpusAnalysis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temp.name)

        generate_corpus(cls.directory)

        cls.analysis = analyze_errors(cls.directory)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_methods_present(self):
        self.assertIn("token", self.analysis["summary"])
        self.assertIn("ast", self.analysis["summary"])

    def test_evaluation_false_positive(self):
        result = self.analysis["summary"]["token"][
            "evaluation"
        ]

        self.assertEqual(
            result["faux_positif"],
            1,
        )

    def test_ast_no_observed_errors(self):
        for split in ("tuning", "evaluation"):
            result = self.analysis["summary"]["ast"][split]

            self.assertEqual(
                result["faux_positif"]
                + result["faux_negatif"],
                0,
            )

    def test_three_or_more_cases(self):
        self.assertGreaterEqual(
            len(self.analysis["errors"]),
            3,
        )

    def test_markdown_report(self):
        markdown = render_markdown(self.analysis)

        self.assertIn("Études de cas", markdown)
        self.assertIn("evaluation", markdown)
        self.assertIn("tuning", markdown)

    def test_template_false_positive(self):
        cases = [
            case
            for case in self.analysis["errors"]
            if case["template_only"]
        ]

        self.assertTrue(cases)


if __name__ == "__main__":
    unittest.main()
