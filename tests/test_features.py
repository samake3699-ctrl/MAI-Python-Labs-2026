import unittest

from src.school.features import extract_code_tokens


class TestCodeFeatures(unittest.TestCase):

    def test_extract_tokens(self):
        code = "x = 10\nprint(x)"

        tokens = extract_code_tokens(code)

        values = [token.value for token in tokens]

        self.assertEqual(
            values,
            ["x", "=", "10", "print", "(", "x", ")"]
        )

    def test_ignore_comments(self):
        code_a = "x = 10\nprint(x)"

        code_b = (
            "# Mon commentaire\n"
            "x=10\n"
            "\n"
            "print(x)  # Affichage\n"
        )

        values_a = [
            token.value
            for token in extract_code_tokens(code_a)
        ]

        values_b = [
            token.value
            for token in extract_code_tokens(code_b)
        ]

        self.assertEqual(values_a, values_b)

    def test_empty_code(self):
        tokens = extract_code_tokens("")

        self.assertEqual(tokens, [])

    def test_line_numbers(self):
        code = "x = 10\n\nprint(x)"

        tokens = extract_code_tokens(code)

        print_token = next(
            token for token in tokens
            if token.value == "print"
        )

        self.assertEqual(print_token.line, 3)


if __name__ == "__main__":
    unittest.main()