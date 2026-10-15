
import tempfile
import unittest
from pathlib import Path

from src.school.ast_similarity import (
    compare_ast_code,
    extract_ast_features,
)
from src.school.corpus import generate_corpus
from src.school.optimized_performance import (
    benchmark_optimized,
    measure_once_optimized,
    optimized_scores,
    token_features,
)
from src.school.performance import measure_once, prepare_load
from src.school.similarity import compare_python_code


class TestOptimizedPerformance(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.directory = Path(self.temp.name)
        generate_corpus(self.directory)

        self.source = self.directory / "submissions.jsonl"

    def test_scores_unchanged(self):
        reference = "x = 10\nprint(x)"

        ref_tokens = token_features(reference)
        ref_ast = extract_ast_features(reference)

        examples = (
            reference,
            "nombre = 10\nprint(nombre)",
            "print(20)",
            "",
        )

        for code in examples:
            with self.subTest(code=code):
                scores = optimized_scores(
                    code, ref_tokens, ref_ast
                )

                self.assertEqual(
                    scores[0],
                    compare_python_code(code, reference),
                )

                self.assertEqual(
                    scores[1],
                    compare_ast_code(code, reference),
                )

    def test_same_outputs_as_baseline(self):
        path = self.directory / "load.jsonl"

        reference = prepare_load(
            self.source, path, 12, seed=42
        )

        before = measure_once(path, reference)
        after = measure_once_optimized(path, reference)

        self.assertEqual(
            before["processed"],
            after["processed"],
        )

        self.assertEqual(
            before["undefined_scores"],
            after["undefined_scores"],
        )

        self.assertEqual(
            before["score_checksum"],
            after["score_checksum"],
        )

    def test_benchmark_structure(self):
        report = benchmark_optimized(
            self.source,
            sizes=(3, 7),
            repeats=2,
        )

        self.assertEqual(report["sizes"], [3, 7])

        self.assertEqual(
            len(report["results"]), 2
        )

        self.assertEqual(
            len(report["results"][1]["trials"]), 2
        )

        self.assertEqual(
            report["results"][1]["trials"][0]["processed"],
            7,
        )

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            benchmark_optimized(
                self.source, sizes=(0,)
            )

        with self.assertRaises(ValueError):
            benchmark_optimized(
                self.source, repeats=0
            )

    def test_short_codes_return_none_for_tokens(self):
        reference = "x"

        scores = optimized_scores(
            "y",
            token_features(reference),
            extract_ast_features(reference),
        )

        self.assertIsNone(scores[0])


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from src.school.ast_similarity import (
    compare_ast_code,
    extract_ast_features,
)
from src.school.corpus import generate_corpus
from src.school.optimized_performance import (
    benchmark_optimized,
    measure_once_optimized,
    optimized_scores,
    token_features,
)
from src.school.performance import measure_once, prepare_load
from src.school.similarity import compare_python_code


class TestOptimizedPerformance(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.directory = Path(self.temp.name)
        generate_corpus(self.directory)

        self.source = self.directory / "submissions.jsonl"

    def test_scores_unchanged(self):
        reference = "x = 10\nprint(x)"

        ref_tokens = token_features(reference)
        ref_ast = extract_ast_features(reference)

        examples = (
            reference,
            "nombre = 10\nprint(nombre)",
            "print(20)",
            "",
        )

        for code in examples:
            with self.subTest(code=code):
                scores = optimized_scores(
                    code, ref_tokens, ref_ast
                )

                self.assertEqual(
                    scores[0],
                    compare_python_code(code, reference),
                )

                self.assertEqual(
                    scores[1],
                    compare_ast_code(code, reference),
                )

    def test_same_outputs_as_baseline(self):
        path = self.directory / "load.jsonl"

        reference = prepare_load(
            self.source, path, 12, seed=42
        )

        before = measure_once(path, reference)
        after = measure_once_optimized(path, reference)

        self.assertEqual(
            before["processed"],
            after["processed"],
        )

        self.assertEqual(
            before["undefined_scores"],
            after["undefined_scores"],
        )

        self.assertEqual(
            before["score_checksum"],
            after["score_checksum"],
        )

    def test_benchmark_structure(self):
        report = benchmark_optimized(
            self.source,
            sizes=(3, 7),
            repeats=2,
        )

        self.assertEqual(report["sizes"], [3, 7])

        self.assertEqual(
            len(report["results"]), 2
        )

        self.assertEqual(
            len(report["results"][1]["trials"]), 2
        )

        self.assertEqual(
            report["results"][1]["trials"][0]["processed"],
            7,
        )

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            benchmark_optimized(
                self.source, sizes=(0,)
            )

        with self.assertRaises(ValueError):
            benchmark_optimized(
                self.source, repeats=0
            )

    def test_short_codes_return_none_for_tokens(self):
        reference = "x"

        scores = optimized_scores(
            "y",
            token_features(reference),
            extract_ast_features(reference),
        )

        self.assertIsNone(scores[0])


if __name__ == "__main__":
    unittest.main()
