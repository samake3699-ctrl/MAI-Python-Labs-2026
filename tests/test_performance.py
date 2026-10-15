
import tempfile
import unittest
from pathlib import Path

from src.school.corpus import generate_corpus
from src.school.performance import (
    benchmark,
    measure_once,
    prepare_load,
)
from src.school.streaming import iter_jsonl_results


class TestPerformance(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.root = Path(self.temp.name)

        generate_corpus(self.root)

        self.source = (
            self.root / "submissions.jsonl"
        )

    def test_load_size_and_unique_identifiers(self):
        target = self.root / "load.jsonl"

        reference = prepare_load(
            self.source,
            target,
            7,
            seed=42,
        )

        records = [
            record
            for _, record, error
            in iter_jsonl_results(target)
            if error is None
        ]

        self.assertEqual(len(records), 7)

        self.assertEqual(
            len({
                record["submission_id"]
                for record in records
            }),
            7,
        )

        self.assertTrue(reference)

    def test_same_seed_produces_identical_data(self):
        first = self.root / "a.jsonl"
        second = self.root / "b.jsonl"

        prepare_load(
            self.source, first, 8, seed=42
        )

        prepare_load(
            self.source, second, 8, seed=42
        )

        self.assertEqual(
            first.read_bytes(),
            second.read_bytes(),
        )

    def test_measurement_counts_all_records(self):
        target = self.root / "load.jsonl"

        reference = prepare_load(
            self.source, target, 4, seed=5
        )

        outcome = measure_once(target, reference)

        self.assertEqual(
            outcome["processed"],
            4,
        )

        self.assertGreaterEqual(
            outcome["wall_seconds"],
            0,
        )

        self.assertGreaterEqual(
            outcome["peak_mib"],
            0,
        )

    def test_benchmark_repetitions_and_summary(self):
        report = benchmark(
            self.source,
            sizes=(3, 6),
            repeats=2,
            seed=4,
        )

        self.assertEqual(report["seed"], 4)

        self.assertEqual(
            len(report["results"]),
            2,
        )

        self.assertEqual(
            len(report["results"][0]["trials"]),
            2,
        )

        self.assertEqual(
            report["results"][1]["trials"][0][
                "processed"
            ],
            6,
        )

        self.assertGreaterEqual(
            report["results"][0][
                "wall_median_seconds"
            ],
            0,
        )

    def test_reject_invalid_arguments(self):
        with self.assertRaises(ValueError):
            benchmark(
                self.source,
                sizes=(0,),
                repeats=3,
            )

        with self.assertRaises(ValueError):
            benchmark(
                self.source,
                sizes=(3,),
                repeats=0,
            )


if __name__ == "__main__":
    unittest.main()
