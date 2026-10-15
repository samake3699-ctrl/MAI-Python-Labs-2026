
"""Analyser les erreurs des méthodes Token et AST."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluation import (
    ScoredPair,
    build_report,
    get_score,
    load_scored_pairs,
)


def categorize(
    pair: ScoredPair,
    method: str,
    threshold: float,
) -> str:
    """Identifier VP, VN, FP, FN ou indéterminé."""

    if not 0 <= threshold <= 1:
        raise ValueError("Seuil invalide")

    score = get_score(pair, method)

    if score is None:
        return "indetermine"

    alerte = score >= threshold

    if alerte and pair.derivation_relation:
        return "vrai_positif"

    if alerte and not pair.derivation_relation:
        return "faux_positif"

    if not alerte and pair.derivation_relation:
        return "faux_negatif"

    return "vrai_negatif"


def explain_case(category: str, template_only: bool) -> str:
    """Expliquer une erreur sans conclure à un plagiat."""

    if category == "faux_positif" and template_only:
        return (
            "Les deux solutions partagent un modèle autorisé. "
            "Cette ressemblance ne prouve pas un plagiat."
        )

    if category == "faux_positif":
        return (
            "Deux solutions indépendantes peuvent avoir "
            "des structures communes."
        )

    if category == "faux_negatif":
        return (
            "La similarité n'a pas été détectée. "
            "Vérifier les transformations et le seuil."
        )

    return "Examiner les informations disponibles."


def analyze_errors(directory: str | Path) -> dict:
    """Analyser les erreurs sur le corpus du Lab 2."""

    report = build_report(directory)
    pairs = load_scored_pairs(directory)

    results = []
    summary = {}

    for method in ("token", "ast"):

        threshold = report["methods"][method][
            "threshold_from_tuning"
        ]

        summary[method] = {}

        for split in ("tuning", "evaluation"):

            counters = {
                "vrai_positif": 0,
                "vrai_negatif": 0,
                "faux_positif": 0,
                "faux_negatif": 0,
                "indetermine": 0,
            }

            for pair in pairs:

                if pair.split != split:
                    continue

                category = categorize(
                    pair, method, threshold
                )

                counters[category] += 1

                if category not in (
                    "faux_positif",
                    "faux_negatif",
                ):
                    continue

                results.append({
                    "pair_id": pair.pair_id,
                    "method": method,
                    "split": split,
                    "category": category,
                    "score": get_score(pair, method),
                    "threshold": threshold,
                    "template_only": pair.template_only,
                    "left_id": pair.left_id,
                    "right_id": pair.right_id,
                    "evidence": pair.evidence,
                    "explanation": explain_case(
                        category,
                        pair.template_only,
                    ),
                })

            summary[method][split] = counters

    # Priorité aux erreurs du jeu d'évaluation.
    results.sort(
        key=lambda item: (
            item["split"] != "evaluation",
            not item["template_only"],
            item["pair_id"],
        )
    )

    return {
        "schema_version": 1,
        "summary": summary,
        "errors": results,
        "case_studies": results[:4],
        "warning": (
            "Les seuils ont été choisis sur tuning. "
            "Seul le groupe evaluation fournit "
            "une mesure indépendante. "
            "Les alertes ne prouvent pas un plagiat."
        ),
    }


def render_markdown(analysis: dict) -> str:
    """Créer un rapport Markdown lisible."""

    lines = [
        "# Lab 2 - Analyse des erreurs",
        "",
        analysis["warning"],
        "",
        "## Résumé des classifications",
        "",
        "| Méthode | Groupe | FP | FN |",
        "|---|---|---:|---:|",
    ]

    for method, splits in analysis["summary"].items():
        for split, counts in splits.items():
            lines.append(
                f"| {method} | {split} | "
                f"{counts['faux_positif']} | "
                f"{counts['faux_negatif']} |"
            )

    lines.extend(["", "## Études de cas", ""])

    if not analysis["case_studies"]:
        lines.append("Aucune erreur observée.")

    for index, case in enumerate(
        analysis["case_studies"], start=1
    ):

        lines.extend([
            f"### Cas {index}: {case['pair_id']}",
            "",
            f"- Méthode : {case['method']}",
            f"- Groupe : {case['split']}",
            f"- Erreur : {case['category']}",
            f"- Score : {case['score']:.4f}",
            f"- Seuil : {case['threshold']:.4f}",
            f"- Explication : {case['explanation']}",
        ])

        evidence = case["evidence"]

        if evidence:
            lines.append(
                "- Lignes concernées : "
                f"{evidence['left_start']}-"
                f"{evidence['left_end']} et "
                f"{evidence['right_start']}-"
                f"{evidence['right_end']}"
            )

        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Générer les rapports JSON et Markdown."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("data/lab2"),
    )

    args = parser.parse_args()

    analysis = analyze_errors(args.data)

    json_path = args.data / "error_analysis.json"
    md_path = args.data / "error_analysis.md"

    json_path.write_text(
        json.dumps(
            analysis,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    md_path.write_text(
        render_markdown(analysis),
        encoding="utf-8",
    )

    print("Rapports enregistrés :")
    print(json_path)
    print(md_path)

    for method, splits in analysis["summary"].items():
        for split, counts in splits.items():
            print(
                f"{method.upper()} / {split} : "
                f"FP={counts['faux_positif']} "
                f"FN={counts['faux_negatif']}"
            )

    print(
        "Études de cas :",
        len(analysis["case_studies"]),
    )


if __name__ == "__main__":
    main()
