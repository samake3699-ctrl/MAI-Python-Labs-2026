
"""Audit de conformité des données du laboratoire 2."""

from __future__ import annotations

import json
from pathlib import Path

from .evaluation import load_scored_pairs
from .streaming import iter_validated_submissions


def check_evidence(
    evidence: dict | None,
    left_code: str,
    right_code: str,
) -> None:
    """Vérifier les numéros de ligne des preuves."""

    if evidence is None:
        return

    for side, code in (
        ("left", left_code),
        ("right", right_code),
    ):
        start = evidence.get(f"{side}_start")
        end = evidence.get(f"{side}_end")
        line_count = len(code.splitlines())

        if (
            type(start) is not int
            or type(end) is not int
            or start < 1
            or end < start
            or end > line_count
        ):
            raise ValueError(
                f"Preuve invalide : lignes "
                f"{side} {start}-{end}"
            )


def audit_corpus(directory: str | Path) -> dict:
    """Contrôler le corpus et ses preuves de comparaison."""

    directory = Path(directory)
    submissions = {}

    for number, submission, error in (
        iter_validated_submissions(
            directory / "submissions.jsonl"
        )
    ):
        if error or submission is None:
            raise ValueError(
                f"Soumission invalide ligne {number}: {error}"
            )

        if submission.submission_id in submissions:
            raise ValueError(
                f"Soumission dupliquée : "
                f"{submission.submission_id}"
            )

        submissions[submission.submission_id] = submission

    # Réutilise les vérifications déjà réalisées
    # dans notre module evaluation.py.
    pairs = load_scored_pairs(directory)

    evidence_count = 0

    for pair in pairs:
        check_evidence(
            pair.evidence,
            submissions[pair.left_id].code,
            submissions[pair.right_id].code,
        )

        if pair.evidence is not None:
            evidence_count += 1

    return {
        "n_submissions": len(submissions),
        "n_pairs": len(pairs),
        "n_tuning": sum(
            pair.split == "tuning" for pair in pairs
        ),
        "n_evaluation": sum(
            pair.split == "evaluation" for pair in pairs
        ),
        "n_template_only": sum(
            pair.template_only for pair in pairs
        ),
        "n_valid_evidence": evidence_count,
        "family_leakage_checked": True,
        "self_match_checked": True,
        "evidence_ranges_checked": True,
        "warning": (
            "Corpus pédagogique synthétique : "
            "ne pas inférer un plagiat."
        ),
    }


def main() -> None:
    directory = Path("data/lab2")

    report = audit_corpus(directory)

    output = directory / "audit_report.json"

    output.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(
        f"Audit OK : {report['n_submissions']} "
        f"soumissions, {report['n_pairs']} paires"
    )

    print(
        f"Tuning : {report['n_tuning']} ; "
        f"évaluation : {report['n_evaluation']}"
    )

    print(
        "Paires modèle autorisé :",
        report["n_template_only"],
    )

    print(
        "Preuves valides :",
        report["n_valid_evidence"],
    )

    print(f"Rapport enregistré : {output}")


if __name__ == "__main__":
    main()
