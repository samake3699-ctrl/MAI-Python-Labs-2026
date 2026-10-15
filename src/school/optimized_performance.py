
"""Optimisation du pipeline : référence Token/AST pré-calculée."""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
import tracemalloc
from pathlib import Path

from .ast_similarity import extract_ast_features
from .features import extract_code_tokens
from .performance import prepare_load
from .similarity import jaccard_similarity, make_ngrams
from .streaming import iter_validated_submissions


def token_features(code: str) -> set[tuple[str, ...]]:
    """Extraire les 3-grammes d'un programme."""
    return make_ngrams([
        token.value for token in extract_code_tokens(code)
    ])


def optimized_scores(
    code: str,
    reference_tokens: set[tuple[str, ...]],
    reference_ast: set[str],
) -> tuple[float | None, float | None]:
    """Comparer avec une référence déjà analysée."""

    tokens = token_features(code)
    ast_nodes = extract_ast_features(code)

    token_score = (
        jaccard_similarity(tokens, reference_tokens)
        if tokens and reference_tokens
        else None
    )

    ast_score = (
        len(ast_nodes & reference_ast)
        / len(ast_nodes | reference_ast)
        if ast_nodes and reference_ast
        else None
    )

    return token_score, ast_score


def measure_once_optimized(
    path: Path,
    reference_code: str,
) -> dict[str, float | int]:
    """Mesurer le pipeline avec la référence en cache."""

    processed = 0
    undefined = 0
    score_total = 0.0

    tracemalloc.start()
    started = time.perf_counter()

    try:
        # Calcul effectué une seule fois par exécution.
        reference_tokens = token_features(reference_code)
        reference_ast = extract_ast_features(reference_code)

        for line_number, submission, error in (
            iter_validated_submissions(path)
        ):
            if error or submission is None:
                raise ValueError(
                    f"Ligne {line_number} invalide : {error}"
                )

            scores = optimized_scores(
                submission.code,
                reference_tokens,
                reference_ast,
            )

            processed += 1

            for score in scores:
                if score is None:
                    undefined += 1
                else:
                    score_total += score

        elapsed = time.perf_counter() - started
        _, peak_bytes = tracemalloc.get_traced_memory()

    finally:
        tracemalloc.stop()

    return {
        "processed": processed,
        "wall_seconds": elapsed,
        "peak_mib": peak_bytes / (1024 * 1024),
        "undefined_scores": undefined,
        "score_checksum": round(score_total, 6),
    }


def benchmark_optimized(
    source: str | Path,
    sizes: tuple[int, ...] = (100, 1000, 5000),
    repeats: int = 3,
    seed: int = 42,
) -> dict:
    """Mesurer les performances après optimisation."""

    if repeats < 1 or not sizes or any(
        size < 1 for size in sizes
    ):
        raise ValueError(
            "Tailles et répétitions doivent être positives"
        )

    rows = []

    with tempfile.TemporaryDirectory() as directory:
        for size in sizes:
            path = Path(directory) / f"load-{size}.jsonl"

            reference_code = prepare_load(
                Path(source), path, size, seed
            )

            trials = []

            for repeat in range(1, repeats + 1):
                trial = measure_once_optimized(
                    path, reference_code
                )

                if trial["processed"] != size:
                    raise AssertionError(
                        "Nombre de soumissions incohérent"
                    )

                trials.append(trial)

                print(
                    f"{size} entrées | essai {repeat}/{repeats} | "
                    f"{trial['wall_seconds']:.3f} s | "
                    f"{trial['peak_mib']:.2f} MiB",
                    flush=True,
                )

            rows.append({
                "size": size,
                "trials": trials,
                "wall_mean_seconds": statistics.mean(
                    t["wall_seconds"] for t in trials
                ),
                "wall_median_seconds": statistics.median(
                    t["wall_seconds"] for t in trials
                ),
                "peak_mean_mib": statistics.mean(
                    t["peak_mib"] for t in trials
                ),
                "peak_median_mib": statistics.median(
                    t["peak_mib"] for t in trials
                ),
            })

    return {
        "experiment": (
            "Même charge que la baseline, "
            "référence Token/AST pré-calculée"
        ),
        "seed": seed,
        "repeats": repeats,
        "sizes": list(sizes),
        "generation_included_in_timing": False,
        "memory_profiler": (
            "tracemalloc : allocations Python seulement"
        ),
        "results": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/lab2/submissions.jsonl"),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/lab2/performance_optimized.json"),
    )

    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=[100, 1000, 5000],
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    report = benchmark_optimized(
        args.source,
        tuple(args.sizes),
        args.repeats,
    )

    args.output.parent.mkdir(
        parents=True, exist_ok=True
    )

    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"Rapport enregistré : {args.output}")


if __name__ == "__main__":
    main()
