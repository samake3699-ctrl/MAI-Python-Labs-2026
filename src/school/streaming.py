import json
from collections.abc import Iterator
from pathlib import Path

from .models import Submission
from .parser import SubmissionSchemaError, parse_submission
from .validation import validate_submission


def iter_jsonl_lines(path: str | Path) -> Iterator[tuple[int, str]]:
    """Lire progressivement les lignes non vides d'un fichier JSONL."""

    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if line.strip():
                yield line_number, line


def iter_jsonl_records(path: str | Path) -> Iterator[tuple[int, object]]:
    """Convertir progressivement les lignes JSONL en données Python."""

    for line_number, line in iter_jsonl_lines(path):
        data = json.loads(line)
        yield line_number, data

def iter_jsonl_results(
    path: str | Path,
) -> Iterator[tuple[int, dict[str, object] | None, str | None]]:
    """Lire les objets JSONL et signaler les erreurs sans interrompre la lecture."""

    for line_number, line in iter_jsonl_lines(path):
        try:
            data = json.loads(line)

        except json.JSONDecodeError as error:
            yield line_number, None, f"JSON invalide : {error.msg}"
            continue

        if not isinstance(data, dict):
            yield line_number, None, "La ligne doit contenir un objet JSON."
            continue

        yield line_number, data, None

def iter_jsonl_results(
    path: str | Path,
) -> Iterator[tuple[int, dict[str, object] | None, str | None]]:
    """Lire un fichier JSONL sans s'arrêter sur les lignes invalides."""

    for line_number, line in iter_jsonl_lines(path):
        try:
            data = json.loads(line)

        except json.JSONDecodeError as error:
            yield line_number, None, f"JSON invalide : {error.msg}"
            continue

        if not isinstance(data, dict):
            yield line_number, None, "La ligne doit contenir un objet JSON."
            continue

        yield line_number, data, None

def iter_validated_submissions(
    path: str | Path,
) -> Iterator[tuple[int, Submission | None, str | None]]:
    """Lire et valider les soumissions une par une."""

    for line_number, data, json_error in iter_jsonl_results(path):

        if json_error is not None:
            yield line_number, None, json_error
            continue

        try:
            submission = parse_submission(data)

            errors = validate_submission(submission)

            if errors:
                message = "; ".join(
                    f"{error.field}: {error.message}"
                    for error in errors
                )
                yield line_number, None, message
                continue

            yield line_number, submission, None

        except SubmissionSchemaError as error:
            yield line_number, None, (
                f"{error.field}: {error}"
            )

        except (TypeError, ValueError, AttributeError) as error:
            yield line_number, None, str(error)