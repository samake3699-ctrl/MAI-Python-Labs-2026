"""Ã‰valuation reproductible des mÃ©thodes Token et AST (Lab 2, Ã©tape B).

Les scores dÃ©clenchent une Ã©ventuelle revue humaine : ils ne prouvent jamais
qu'un Ã©tudiant a commis une fraude. Aucun code soumis n'est exÃ©cutÃ© ici.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from .candidates import iter_candidates
from .corpus import TEMPLATE
from .streaming import iter_jsonl_results, iter_validated_submissions

Method = Literal["token", "ast"]
TEMPLATES = {"template-001": TEMPLATE}


@dataclass(frozen=True)
class ScoredPair:
    pair_id: str
    left_id: str
    right_id: str
    split: str
    derivation_relation: bool
    template_only: bool
    token_score: float | None
    ast_score: float | None
    evidence: dict[str, object] | None
    warning: str | None


def _jsonl_objects(path: Path) -> list[dict[str, object]]:
    """Lire les mÃ©tadonnÃ©es JSONL et refuser les lignes malformÃ©es."""
    records: list[dict[str, object]] = []
    for line_number, record, error in iter_jsonl_results(path):
        if error is not None or record is None:
            raise ValueError(f"{path.name}, ligne {line_number} : {error}")
        records.append(record)
    return records


def load_scored_pairs(
    directory: str | Path,
    templates: dict[str, str] | None = None,
) -> list[ScoredPair]:
    directory = Path(directory)
    active_templates = TEMPLATES if templates is None else templates
    submissions = {}
    for line_number, submission, error in iter_validated_submissions(
        directory / "submissions.jsonl"
    ):
        if error is not None or submission is None:
            raise ValueError(f"submissions.jsonl, ligne {line_number} : {error}")
        if submission.submission_id in submissions:
            raise ValueError(f"Soumission rÃ©pÃ©tÃ©e : {submission.submission_id}")
        submissions[submission.submission_id] = submission

    provenance: dict[str, dict[str, object]] = {}
    split_families: dict[str, set[str]] = {"tuning": set(), "evaluation": set()}
    for record in _jsonl_objects(directory / "provenance.jsonl"):
        submission_id = record.get("submission_id")
        split = record.get("split")
        family = record.get("family_id")
        if not isinstance(submission_id, str) or submission_id not in submissions:
            raise ValueError(f"Provenance inconnue : {submission_id}")
        if submission_id in provenance:
            raise ValueError(f"Provenance rÃ©pÃ©tÃ©e : {submission_id}")
        if split not in split_families or not isinstance(family, str) or not family:
            raise ValueError(f"Provenance incorrecte pour {submission_id}")
        provenance[submission_id] = record
        split_families[split].add(family)

    if len(provenance) != len(submissions):
        raise ValueError("Certaines soumissions n'ont pas de provenance")
    if split_families["tuning"] & split_families["evaluation"]:
        raise ValueError("Fuite de familles entre tuning et evaluation")

    pairs: list[ScoredPair] = []
    seen_pairs: set[str] = set()
    for record in _jsonl_objects(directory / "pairs.jsonl"):
        pair_id = record.get("pair_id")
        left_id = record.get("left_id")
        right_id = record.get("right_id")
        split = record.get("split")
        label = record.get("derivation_relation")
        template_only = record.get("template_only")
        if not isinstance(pair_id, str) or pair_id in seen_pairs:
            raise ValueError(f"Identifiant de paire absent ou rÃ©pÃ©tÃ© : {pair_id}")
        seen_pairs.add(pair_id)
        if left_id not in submissions or right_id not in submissions:
            raise ValueError(f"Soumission inconnue dans {pair_id}")
        if split not in split_families:
            raise ValueError(f"Split inconnu dans {pair_id}")
        if type(label) is not bool or type(template_only) is not bool:
            raise ValueError(f"Annotations invalides pour {pair_id}")
        left = submissions[left_id]
        right = submissions[right_id]
        if left.submission_id == right.submission_id or left.student_id == right.student_id:
            raise ValueError(f"Self-match ou mÃªme Ã©tudiant : {pair_id}")
        if left.assignment_id != right.assignment_id:
            raise ValueError(f"Devoirs diffÃ©rents : {pair_id}")
        if provenance[left_id]["split"] != split or provenance[right_id]["split"] != split:
            raise ValueError(f"Paire traversant les splits : {pair_id}")
        if (
            provenance[left_id]["family_id"] != record.get("left_family_id")
            or provenance[right_id]["family_id"] != record.get("right_family_id")
        ):
            raise ValueError(f"Famille incohÃ©rente : {pair_id}")

        candidate = next(iter(iter_candidates(left, [right], active_templates)))
        pairs.append(
            ScoredPair(
                pair_id=pair_id,
                left_id=left_id,
                right_id=right_id,
                split=split,
                derivation_relation=label,
                template_only=template_only,
                token_score=candidate.token_score,
                ast_score=candidate.ast_score,
                evidence=asdict(candidate.evidence) if candidate.evidence else None,
                warning=candidate.warning,
            )
        )
    return pairs


def get_score(pair: ScoredPair, method: Method) -> float | None:
    """Choisir le score d'une mÃ©thode sans mÃ©langer les deux comparateurs."""
    if method == "token":
        return pair.token_score
    if method == "ast":
        return pair.ast_score
    raise ValueError(f"MÃ©thode inconnue : {method}")


def confusion_metrics(
    pairs: list[ScoredPair], method: Method, threshold: float
) -> dict[str, int | float | list[list[int]]]:
    """Ã‰valuer review_required sur les paires ayant un score dÃ©fini.

    Matrice : lignes = rÃ©alitÃ© [nÃ©gatif, positif] ;
              colonnes = signal [non, review_required].
    Les scores None sont comptÃ©s sÃ©parÃ©ment comme indÃ©terminÃ©s.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Le seuil doit Ãªtre compris entre 0 et 1")
    tp = fp = tn = fn = undefined = 0
    for pair in pairs:
        score = get_score(pair, method)
        if score is None:
            undefined += 1
            continue
        review_required = score >= threshold
        if review_required and pair.derivation_relation:
            tp += 1
        elif review_required and not pair.derivation_relation:
            fp += 1
        elif not review_required and pair.derivation_relation:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "total_pairs": len(pairs),
        "scored_pairs": len(pairs) - undefined,
        "undefined": undefined,
        "undefined_fraction": undefined / len(pairs) if pairs else 0.0,
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "confusion_matrix": [[tn, fp], [fn, tp]],
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def choose_threshold(tuning_pairs: list[ScoredPair], method: Method) -> float:
    """Choisir le meilleur seuil F1 uniquement sur le jeu tuning.

    En cas d'Ã©galitÃ©, prÃ©fÃ©rer le plus grand seuil : signal plus prudent.
    """
    values = [get_score(pair, method) for pair in tuning_pairs]
    scores = [score for score in values if score is not None]
    if not scores:
        raise ValueError(f"Aucun score pour le rÃ©glage de la mÃ©thode {method}")
    candidates = sorted(set(scores) | {0.0, 1.0})
    return max(
        candidates,
        key=lambda threshold: (
            confusion_metrics(tuning_pairs, method, threshold)["f1"],
            threshold,
        ),
    )


def build_report(
    directory: str | Path,
    templates: dict[str, str] | None = None,
) -> dict[str, object]:
    pairs = load_scored_pairs(directory, templates=templates)
    tuning = [pair for pair in pairs if pair.split == "tuning"]
    evaluation = [pair for pair in pairs if pair.split == "evaluation"]
    if not tuning or not evaluation:
        raise ValueError("Les splits tuning et evaluation doivent Ãªtre non vides")

    methods: dict[str, dict[str, object]] = {}
    for method in ("token", "ast"):
        threshold = choose_threshold(tuning, method)
        methods[method] = {
            "threshold_from_tuning": threshold,
            "tuning": confusion_metrics(tuning, method, threshold),
            "evaluation": confusion_metrics(evaluation, method, threshold),
        }

    evaluated_pairs = []
    for pair in evaluation:
        record = asdict(pair)
        record["review_required"] = {
            method: (
                None if get_score(pair, method) is None
                else get_score(pair, method) >= methods[method]["threshold_from_tuning"]
            )
            for method in ("token", "ast")
        }
        evaluated_pairs.append(record)

    return {
        "schema_version": 1,
        "corpus": "synthÃ©tique pÃ©dagogique : rÃ©sultats non gÃ©nÃ©ralisables aux Ã©tudiants rÃ©els",
        "task": "signaler une relation de dÃ©rivation pour revue humaine, pas prouver une fraude",
        "threshold_rule": "maximiser F1 sur tuning ; Ã©galitÃ© -> seuil le plus Ã©levÃ©",
        "evaluation_rule": "seuil fixÃ© avant l'Ã©valuation ; mÃ©triques sur scores dÃ©finis",
        "n_pairs": len(pairs),
        "n_tuning": len(tuning),
        "n_evaluation": len(evaluation),
        "methods": methods,
        "evaluated_pairs": evaluated_pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ã‰valuation de la similaritÃ© du Lab 2")
    parser.add_argument("--data", type=Path, default=Path("data/lab2"))
    parser.add_argument("--output", type=Path, default=Path("data/lab2/evaluation_report.json"))
    args = parser.parse_args()
    report = build_report(args.data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Rapport enregistrÃ© : {args.output}")
    print(f"Paires : {report['n_pairs']} ; tuning : {report['n_tuning']} ; Ã©valuation : {report['n_evaluation']}")
    for method, result in report["methods"].items():
        summary = result["evaluation"]
        print(
            f"{method.upper()} | seuil={result['threshold_from_tuning']:.4f} "
            f"| precision={summary['precision']:.3f} "
            f"| recall={summary['recall']:.3f} "
            f"| F1={summary['f1']:.3f} "
            f"| indÃ©terminÃ©s={summary['undefined']}/{summary['total_pairs']}"
        )


if __name__ == "__main__":
    main()
