
import unittest

from src.school.performance_report import (
    calculate_gain,
    build_markdown,
)


class TestPerformanceReport(unittest.TestCase):

    def setUp(self):
        self.before = {
            "results": [
                {
                    "size": 100,
                    "wall_mean_seconds": 0.5,
                },
                {
                    "size": 1000,
                    "wall_mean_seconds": 4.0,
                },
            ]
        }

        self.after = {
            "results": [
                {
                    "size": 100,
                    "wall_mean_seconds": 0.25,
                },
                {
                    "size": 1000,
                    "wall_mean_seconds": 2.0,
                },
            ]
        }

    def test_gain(self):
        self.assertEqual(
            calculate_gain(10, 5),
            50.0,
        )

    def test_slower_version(self):
        self.assertEqual(
            calculate_gain(10, 12),
            -20.0,
        )

    def test_invalid_duration(self):
        with self.assertRaises(ValueError):
            calculate_gain(0, 5)

    def test_markdown(self):
        report = build_markdown(
            self.before,
            self.after,
        )

        self.assertIn("50.0", report)
        self.assertIn("1000", report)
        self.assertIn("cProfile", report)

    def test_incompatible_sizes(self):
        self.after["results"].pop()

        with self.assertRaises(ValueError):
            build_markdown(
                self.before,
                self.after,
            )


if __name__ == "__main__":
    unittest.main()
