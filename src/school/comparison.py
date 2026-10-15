from dataclasses import dataclass

from .similarity import compare_python_code
from .ast_similarity import compare_ast_code


@dataclass(frozen=True)
class MethodComparison:
    token_score: float | None
    ast_score: float | None
    difference: float | None


def compare_methods(
    code_a: str,
    code_b: str,
) -> MethodComparison:
    """Comparer deux programmes avec Token et AST."""

    token_score = compare_python_code(code_a, code_b)
    ast_score = compare_ast_code(code_a, code_b)

    if token_score is None or ast_score is None:
        difference = None
    else:
        difference = abs(token_score - ast_score)

    return MethodComparison(
        token_score=token_score,
        ast_score=ast_score,
        difference=difference,
    )