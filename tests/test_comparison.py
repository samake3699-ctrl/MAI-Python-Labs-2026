import unittest

from src.school.comparison import compare_methods


class TestMethodComparison(unittest.TestCase):

    def test_identical_code(self):
        code = "x = 10\nprint(x)"

        result = compare_methods(code, code)

        self.assertEqual(result.token_score, 1.0)
        self.assertEqual(result.ast_score, 1.0)
        self.assertEqual(result.difference, 0.0)

    def test_renamed_variables(self):
        code_a = "x = 10\nprint(x)"
        code_b = "nombre = 10\nprint(nombre)"

        result = compare_methods(code_a, code_b)

        self.assertIsNotNone(result.token_score)
        self.assertEqual(result.ast_score, 1.0)
        self.assertLess(result.token_score, result.ast_score)

    def test_empty_code(self):
        result = compare_methods("", "x = 10")

        self.assertIsNone(result.token_score)
        self.assertIsNone(result.ast_score)
        self.assertIsNone(result.difference)

    def test_different_codes(self):
        code_a = "x = 10"
        code_b = "print(10)"

        result = compare_methods(code_a, code_b)

        self.assertIsNotNone(result.token_score)
        self.assertIsNotNone(result.ast_score)
        self.assertGreaterEqual(result.difference, 0.0)

    def test_symmetry(self):
        code_a = "x = 10\nprint(x)"
        code_b = "nombre = 10\nprint(nombre)"

        result_ab = compare_methods(code_a, code_b)
        result_ba = compare_methods(code_b, code_a)

        self.assertEqual(
            result_ab.token_score,
            result_ba.token_score,
        )
        self.assertEqual(
            result_ab.ast_score,
            result_ba.ast_score,
        )


if __name__ == "__main__":
    unittest.main()