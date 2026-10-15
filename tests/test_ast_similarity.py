import unittest

from src.school.ast_similarity import (
    extract_ast_features,
    compare_ast_code,
)


class TestASTSimilarity(unittest.TestCase):

    def test_identical_code(self):
        code = "x = 10\nprint(x)"

        score = compare_ast_code(code, code)

        self.assertEqual(score, 1.0)

    def test_renamed_variables(self):
        code_a = "x = 10\nprint(x)"
        code_b = "nombre = 10\nprint(nombre)"

        score = compare_ast_code(code_a, code_b)

        self.assertEqual(score, 1.0)

    def test_different_structures(self):
        code_a = "x = 10"
        code_b = "print(10)"

        score = compare_ast_code(code_a, code_b)

        self.assertIsNotNone(score)
        self.assertLess(score, 1.0)

    def test_empty_code(self):
        score = compare_ast_code("", "x = 10")

        self.assertIsNone(score)

    def test_invalid_python(self):
        with self.assertRaisesRegex(
            ValueError,
            "Code Python invalide",
        ):
            extract_ast_features("def test(:")

    def test_symmetry(self):
        code_a = "x = 10"
        code_b = "print(10)"

        score_ab = compare_ast_code(code_a, code_b)
        score_ba = compare_ast_code(code_b, code_a)

        self.assertEqual(score_ab, score_ba)


if __name__ == "__main__":
    unittest.main()