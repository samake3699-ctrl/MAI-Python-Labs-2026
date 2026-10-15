
"""Mesurer les performances du pipeline du Lab 2."""

from __future__ import annotations

import argparse
import json
import platform
import random
import statistics
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

from .ast_similarity import compare_ast_code
from .similarity import compare_python_code
from .streaming import (
    iter_jsonl_results,
    iter_validated_submissions,
)


def prepare_load(
    source: Path,
    target: Path,
    size: int,
    seed: int,
) -> str:
    """Créer des données synthétiques de charge reproductibles."""

    if size <= 0:
        raise ValueError("La taille doit être positive")

    examples = []

    for number, data, error in iter_jsonl_results(source):
        if error or data is None:
            raise ValueError(
                f"Corpus invalide, ligne {number}: {error}"
            )

        examples.append(data)

    if not examples:
        raise ValueError("Le corpus est vide")

    rng = random.Random(seed)

    with target.open("w", encoding="utf-8") as stream:
        for index in range(size):
            original = examples[
                rng.randrange(len(examples))
            ]

            record = dict(original)

            record["submission_id"] = (
                f"load-{index:06d}"
            )

            record["student_id"] = (
                f"load-student-{index:06d}"
            )

            stream.write(
                json.dumps(record, ensure_ascii=False)
                + "\n"
            )

    return examples[0]["code"]


def measure_once(
    path: Path,
    reference_code: str,
) -> dict[str, float | int]:
    """Mesurer une exécution du pipeline."""

    count = 0
    undefined = 0
    score_total = 0.0

    tracemalloc.start()
    started = time.perf_counter()

    try:
        for line_number, submission, error in (
            iter_validated_submissions(path)
        ):
            if error or submission is None:
                raise ValueError(
                    f"Ligne {line_number} invalide: {error}"
                )

            token_score = compare_python_code(
                submission.code,
                reference_code,
            )

            ast_score = compare_ast_code(
                submission.code,
                reference_code,
            )

            count += 1

            for score in (token_score, ast_score):
                if score is None:
                    undefined += 1
                else:
                    score_total += score

        wall_seconds = time.perf_counter() - started

        _, peak_bytes = tracemalloc.get_traced_memory()

    finally:
        tracemalloc.stop()

    return {
        "processed": count,
        "wall_seconds": wall_seconds,
        "peak_mib": peak_bytes / (1024 * 1024),
        "undefined_scores": undefined,
        "score_checksum": round(score_total, 6),
    }


def benchmark(
    source: str | Path,
    sizes: tuple[int, ...] = (100, 1000, 5000),
    repeats: int = 3,
    seed: int = 42,
) -> dict:
    """Répéter les mesures sur les mêmes jeux de données."""

    if (
        repeats < 1
        or not sizes
        or any(size < 1 for size in sizes)
    ):
        raise ValueError(
            "Tailles et répétitions doivent être positives"
        )

    source = Path(source)
    results = []

    with tempfile.TemporaryDirectory() as directory:

        for size in sizes:

            path = (
                Path(directory)
                / f"load-{size}.jsonl"
            )

            reference_code = prepare_load(
                source,
                path,
                size,
                seed,
            )

            trials = []

            for repeat in range(1, repeats + 1):

                result = measure_once(
                    path,
                    reference_code,
                )

                if result["processed"] != size:
                    raise AssertionError(
                        "Nombre de soumissions incohérent"
                    )

                trials.append(result)

                print(
                    f"{size} entrées | "
                    f"essai {repeat}/{repeats} | "
                    f"{result['wall_seconds']:.3f} s | "
                    f"{result['peak_mib']:.2f} MiB",
                    flush=True,
                )

            times = [
                trial["wall_seconds"]
                for trial in trials
            ]

            memories = [
                trial["peak_mib"]
                for trial in trials
            ]

            results.append({
                "size": size,
                "trials": trials,
                "wall_mean_seconds": statistics.mean(
                    times
                ),
                "wall_median_seconds": statistics.median(
                    times
                ),
                "peak_mean_mib": statistics.mean(
                    memories
                ),
                "peak_median_mib": statistics.median(
                    memories
                ),
            })

    return {
        "experiment": (
            "streaming + validation + Token/AST "
            "vs fixed reference"
        ),
        "note": (
            "N comparaisons contre une référence fixe, "
            "pas toutes les paires possibles"
        ),
        "seed": seed,
        "repeats": repeats,
        "sizes": list(sizes),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "memory_profiler": (
            "tracemalloc : allocations Python, "
            "pas RAM totale du processus"
        ),
        "generation_included_in_timing": False,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "data/lab2/submissions.jsonl"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/lab2/performance_baseline.json"
        ),
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

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    report = benchmark(
        args.source,
        tuple(args.sizes),
        args.repeats,
        args.seed,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        f"Rapport enregistré : {args.output}"
    )


if __name__ == "__main__":
    main()
