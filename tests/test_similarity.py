import unittest

from src.school.similarity import (
    make_ngrams,
    jaccard_similarity,
    compare_python_code,
)


class TestSimilarity(unittest.TestCase):

    def test_make_ngrams(self):
        values = ["a", "b", "c", "d"]

        result = make_ngrams(values, n=3)

        self.assertEqual(
            result,
            {("a", "b", "c"), ("b", "c", "d")},
        )

    def test_identical_sets(self):
        grams = {("a", "b", "c")}

        self.assertEqual(
            jaccard_similarity(grams, grams),
            1.0,
        )

    def test_disjoint_sets(self):
        left = {("a", "b", "c")}
        right = {("x", "y", "z")}

        self.assertEqual(
            jaccard_similarity(left, right),
            0.0,
        )

    def test_empty_sets(self):
        self.assertEqual(
            jaccard_similarity(set(), set()),
            0.0,
        )

    def test_same_code_with_different_formatting(self):
        code_a = "x = 10\nprint(x)"

        code_b = (
            "# commentaire\n"
            "x=10\n"
            "\n"
            "print(x)  # affichage\n"
        )

        score = compare_python_code(code_a, code_b)

        self.assertEqual(score, 1.0)


if __name__ == "__main__":
    unittest.main()