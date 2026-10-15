
"""Rapport des performances du Lab 2."""

import json
import pstats
from pathlib import Path


def calculate_gain(before: float, after: float) -> float:
    """Calculer le pourcentage de temps économisé."""

    if before <= 0 or after < 0:
        raise ValueError("Durées invalides")

    return (before - after) / before * 100


def build_markdown(
    baseline: dict,
    optimized: dict,
    profile_path: Path | None = None,
) -> str:
    """Construire un rapport Markdown à partir des mesures."""

    before_rows = {
        row["size"]: row
        for row in baseline["results"]
    }

    after_rows = {
        row["size"]: row
        for row in optimized["results"]
    }

    if before_rows.keys() != after_rows.keys():
        raise ValueError(
            "Les tailles des expériences ne correspondent pas"
        )

    lines = [
        "# Lab 2 - Rapport de performances",
        "",
        "## Comparaison avant / après optimisation",
        "",
        "| Entrées | Avant (s) | Après (s) | Gain (%) |",
        "|---:|---:|---:|---:|",
    ]

    for size in sorted(before_rows):
        before = before_rows[size]["wall_mean_seconds"]
        after = after_rows[size]["wall_mean_seconds"]

        gain = calculate_gain(before, after)

        lines.append(
            f"| {size} | {before:.3f} | "
            f"{after:.3f} | {gain:.1f} |"
        )

    lines.extend([
        "",
        "## Méthodologie",
        "",
        "- Trois répétitions par taille.",
        "- Mesures réalisées sur 100, 1000 et 5000 entrées.",
        "- Données synthétiques reproductibles.",
        "- Comparaison avec une référence fixe.",
        "- Lecture JSONL progressive.",
        "- Temps mesuré avec time.perf_counter().",
        "- Allocations Python suivies avec tracemalloc.",
        "- Génération des données exclue du chronométrage.",
        "",
        "## Optimisation",
        "",
        "Les caractéristiques Token et AST de la référence "
        "sont calculées une seule fois par exécution.",
        "",
        "## Analyse cProfile",
        "",
    ])

    if profile_path is not None and profile_path.exists():
        stats = pstats.Stats(str(profile_path)).stats

        targets = (
            "extract_ast_features",
            "dump",
            "extract_code_tokens",
        )

        for target in targets:
            matches = [
                (key, values)
                for key, values in stats.items()
                if key[2] == target
            ]

            if not matches:
                continue

            key, values = max(
                matches,
                key=lambda item: item[1][3],
            )

            calls = values[1]
            cumulative = values[3]

            lines.append(
                f"- `{key[2]}` : {calls} appels, "
                f"{cumulative:.3f} s cumulées."
            )

    else:
        lines.append(
            "Aucun fichier de profilage disponible."
        )

    lines.extend([
        "",
        "## Limites",
        "",
        "- Le jeu de données est synthétique.",
        "- Les mesures ne couvrent pas toutes les paires.",
        "- tracemalloc ne mesure pas toute la RAM Windows.",
        "- Les temps cumulés cProfile se chevauchent.",
        "- Une similarité élevée ne prouve pas un plagiat.",
        "",
    ])

    return "\n".join(lines)


def main() -> None:
    directory = Path("data/lab2")

    baseline = json.loads(
        (directory / "performance_baseline.json")
        .read_text(encoding="utf-8")
    )

    optimized = json.loads(
        (directory / "performance_optimized.json")
        .read_text(encoding="utf-8")
    )

    markdown = build_markdown(
        baseline,
        optimized,
        directory / "profile_optimized_1000.prof",
    )

    output = directory / "performance_report.md"

    output.write_text(markdown, encoding="utf-8")

    print(f"Rapport enregistré : {output}")
    print(markdown)


if __name__ == "__main__":
    main()
