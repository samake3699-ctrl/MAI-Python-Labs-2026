from collections.abc import Sequence

from .features import extract_code_tokens


def make_ngrams(
    values: Sequence[str],
    n: int = 3,
) -> set[tuple[str, ...]]:
    """Construire des groupes de n tokens consécutifs."""

    if n < 1:
        raise ValueError("n doit être supérieur ou égal à 1")

    return {
        tuple(values[i:i + n])
        for i in range(len(values) - n + 1)
    }


def jaccard_similarity(
    left: set[tuple[str, ...]],
    right: set[tuple[str, ...]],
) -> float:
    """Calculer le recouvrement entre deux ensembles."""

    if not left or not right:
        return 0.0

    intersection = len(left & right)
    union = len(left | right)

    return intersection / union


def compare_python_code(
    code_a: str,
    code_b: str,
) -> float | None:
    """Comparer deux codes Python avec des 3-grammes."""

    tokens_a = [
        token.value
        for token in extract_code_tokens(code_a)
    ]

    tokens_b = [
        token.value
        for token in extract_code_tokens(code_b)
    ]

    ngrams_a = make_ngrams(tokens_a, n=3)
    ngrams_b = make_ngrams(tokens_b, n=3)

    if not ngrams_a or not ngrams_b:
        return None

    return jaccard_similarity(ngrams_a, ngrams_b)