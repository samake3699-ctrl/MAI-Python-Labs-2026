
"""Démonstration du changement de modèle autorisé - Lab 2."""

import hashlib
import json
from pathlib import Path
from shutil import copyfile

from .corpus import TEMPLATE
from .evaluation import build_report, load_scored_pairs


def ensure_config(directory: Path) -> Path:
    """Créer une configuration v2 modifiable."""

    path = directory / "template_config_v2.json"

    if not path.exists():
        config = {
            "config_version": "v2",
            "templates": {
                "template-001": TEMPLATE,
                "template-002": TEMPLATE + "print(result)\n",
            },
            "replace_template_id": {
                "from": "template-001",
                "to": "template-002",
            },
        }

        path.write_text(
            json.dumps(config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return path


def run_demo(directory: str | Path) -> dict:
    """Comparer la version initiale et la nouvelle configuration."""

    directory = Path(directory)
    config_path = ensure_config(directory)

    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)

    version = config["config_version"]
    templates = config["templates"]

    old_id = config["replace_template_id"]["from"]
    new_id = config["replace_template_id"]["to"]

    if (
        not isinstance(version, str)
        or not version.startswith("v")
        or not version[1:].isdigit()
    ):
        raise ValueError("Version de configuration invalide")

    if (
        not isinstance(templates, dict)
        or any(
            not isinstance(key, str)
            or not isinstance(value, str)
            for key, value in templates.items()
        )
    ):
        raise ValueError("Modèles invalides")

    if (
        old_id not in templates
        or new_id not in templates
        or old_id == new_id
    ):
        raise ValueError("Identifiants de modèles invalides")

    target = directory / f"demo_{version}"
    target.mkdir(parents=True, exist_ok=True)

    # Préserver les annotations et les provenances.
    for name in ("provenance.jsonl", "pairs.jsonl"):
        copyfile(directory / name, target / name)

    changed = 0
    records = []

    for line in (
        directory / "submissions.jsonl"
    ).read_text(encoding="utf-8").splitlines():

        record = json.loads(line)

        if record.get("template_id") == old_id:
            record["template_id"] = new_id
            changed += 1

        records.append(record)

    if changed == 0:
        raise ValueError("Aucune soumission concernée par le modèle")

    (target / "submissions.jsonl").write_text(
        "".join(
            json.dumps(row, ensure_ascii=False) + "\n"
            for row in records
        ),
        encoding="utf-8",
    )

    # Comparer les mêmes paires avec les deux configurations.
    original_pairs = load_scored_pairs(directory)

    updated_pairs = load_scored_pairs(
        target,
        templates=templates,
    )

    affected = [
        original.pair_id
        for original, updated in zip(
            original_pairs, updated_pairs
        )
        if (
            original.token_score != updated.token_score
            or original.ast_score != updated.ast_score
        )
    ]

    original_report = build_report(directory)

    updated_report = build_report(
        target,
        templates=templates,
    )

    updated_report["report_version"] = version
    updated_report["config_sha256"] = hashlib.sha256(
        config_bytes
    ).hexdigest()

    updated_report["changed_submissions"] = changed
    updated_report["changed_pairs"] = len(affected)
    updated_report["changed_pair_ids"] = affected

    updated_report["note"] = (
        "Simulation pédagogique du changement de modèle. "
        "Il ne s'agit pas d'une nouvelle évaluation indépendante."
    )

    report_path = (
        target / f"evaluation_report_{version}.json"
    )

    report_path.write_text(
        json.dumps(
            updated_report,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    differences = {
        "from": "v1",
        "to": version,
        "config_sha256": updated_report["config_sha256"],
        "changed_submissions": changed,
        "changed_pairs": len(affected),
        "methods": {},
    }

    for method in ("token", "ast"):
        before = original_report["methods"][method]
        after = updated_report["methods"][method]

        differences["methods"][method] = {
            "f1_before": before["evaluation"]["f1"],
            "f1_after": after["evaluation"]["f1"],
            "threshold_before": before["threshold_from_tuning"],
            "threshold_after": after["threshold_from_tuning"],
        }

    (target / "changes_v1_v2.json").write_text(
        json.dumps(
            differences,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    return differences


def main() -> None:
    directory = Path("data/lab2")
    result = run_demo(directory)

    print(
        f"Version {result['to']} : "
        f"{result['changed_submissions']} soumissions concernées"
    )

    print(
        "Paires dont le score change :",
        result["changed_pairs"],
    )

    for method, scores in result["methods"].items():
        print(
            f"{method.upper()} : "
            f"F1 {scores['f1_before']:.3f} "
            f"-> {scores['f1_after']:.3f}"
        )

    print(
        "Fichiers créés dans :",
        directory / f"demo_{result['to']}",
    )


if __name__ == "__main__":
    main()
