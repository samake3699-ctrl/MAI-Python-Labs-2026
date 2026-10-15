"""Corpus synthétique reproductible du laboratoire 2."""
import ast
import json
from itertools import combinations
from pathlib import Path

ASSIGNMENT_ID = "assignment-001"
TEMPLATE = "print('Hello')\nprint('Example')\n"
TEMPLATE_FAMILIES = {0, 1, 2, 5, 6, 7}

BASE_CODES = (
    "value = 5\nresult = value + 1\nprint(result)\n",
    "value = 5\nresult = value * 2\nprint(result)\n",
    "value = [1, 2, 3]\nresult = sum(value)\nprint(result)\n",
    'value = "Mali"\nresult = value.upper()\nprint(result)\n',
    "value = 9\nresult = value % 2\nprint(result)\n",
    "value = 1\nresult = value == 1\nprint(result)\n",
    "value = [2, 4]\nresult = len(value)\nprint(result)\n",
    'value = "python"\nresult = value[::-1]\nprint(result)\n',
    "value = [3, 1, 2]\nresult = sorted(value)\nprint(result)\n",
    "value = 4\nresult = value ** 2\nprint(result)\n",
)

NEGATIVE_FAMILIES = (
    (0, 1), (0, 2), (1, 2), (3, 4), (2, 3),
    (5, 6), (5, 7), (6, 7), (8, 9), (7, 8),
)


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def generate_corpus(directory: str | Path) -> None:
    """Créer 30 soumissions, 30 provenances et 40 paires annotées."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    submissions = []
    provenance = []
    pairs = []

    for family, original in enumerate(BASE_CODES):
        split = "tuning" if family < 5 else "evaluation"
        has_template = family in TEMPLATE_FAMILIES
        family_id = f"family-{family:02d}"

        variations = (
            ("original", original),
            ("renamed", original.replace("value", "item").replace("result", "answer")),
            ("formatted", "# Mise en forme differente\n" + original.replace(" = ", "=")),
        )

        for variant, (kind, solution) in enumerate(variations):
            submission_id = f"lab2-{family:02d}-{variant}"
            code = (TEMPLATE + "\n" if has_template else "") + solution
            ast.parse(code)  # Vérifie la syntaxe sans exécuter le code.
            submissions.append({
                "schema_version": 1,
                "submission_id": submission_id,
                "student_id": f"student-lab2-{family:02d}-{variant}",
                "assignment_id": ASSIGNMENT_ID,
                "submitted_at": "2026-10-15T12:00:00+03:00",
                "text": f"Solution fictive {family}-{variant}",
                "code": code,
                "template_id": "template-001" if has_template else None,
                "ai_declaration": {
                    "used": False, "verified_by_student": True,
                    "tool": None, "purpose": None,
                },
            })
            provenance.append({
                "submission_id": submission_id,
                "family_id": family_id,
                "split": split,
                "variant": kind,
                "origin_submission_id": f"lab2-{family:02d}-0" if variant else None,
                "synthetic": True,
                "template_authorized": has_template,
            })

        for left, right in combinations(range(3), 2):
            pairs.append({
                "pair_id": f"pair-{len(pairs) + 1:03d}",
                "left_id": f"lab2-{family:02d}-{left}",
                "right_id": f"lab2-{family:02d}-{right}",
                "assignment_id": ASSIGNMENT_ID,
                "left_family_id": family_id,
                "right_family_id": family_id,
                "split": split,
                "derivation_relation": True,
                "template_only": False,
            })

    for left, right in NEGATIVE_FAMILIES:
        pairs.append({
            "pair_id": f"pair-{len(pairs) + 1:03d}",
            "left_id": f"lab2-{left:02d}-0",
            "right_id": f"lab2-{right:02d}-0",
            "assignment_id": ASSIGNMENT_ID,
            "left_family_id": f"family-{left:02d}",
            "right_family_id": f"family-{right:02d}",
            "split": "tuning" if left < 5 else "evaluation",
            "derivation_relation": False,
            "template_only": left in TEMPLATE_FAMILIES and right in TEMPLATE_FAMILIES,
        })

    write_jsonl(directory / "submissions.jsonl", submissions)
    write_jsonl(directory / "provenance.jsonl", provenance)
    write_jsonl(directory / "pairs.jsonl", pairs)


if __name__ == "__main__":
    generate_corpus(Path("data") / "lab2")
    print("Corpus généré : 30 soumissions, 30 provenances, 40 paires.")
