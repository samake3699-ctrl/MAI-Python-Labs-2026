
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .models import Submission, AIDeclaration
from .validation import validate_submission
from .repository import InMemorySubmissionRepository


@dataclass(frozen=True)
class JSONLParseError:
    line_number: int
    code: str
    message: str


@dataclass(frozen=True)
class ImportResult:
    accepted: int
    duplicates: int
    conflicts: int
    errors: list


class SubmissionSchemaError(ValueError):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message)


SUBMISSION_FIELDS = {
    "schema_version",
    "submission_id",
    "student_id",
    "assignment_id",
    "submitted_at",
    "text",
    "code",
    "template_id",
    "ai_declaration",
}

AI_FIELDS = {
    "used",
    "verified_by_student",
    "tool",
    "purpose",
}


def read_jsonl(path: str):
    records = []
    errors = []

    with open(path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            try:
                data = json.loads(line)
                records.append((line_number, data))

            except json.JSONDecodeError as error:
                errors.append(
                    JSONLParseError(
                        line_number=line_number,
                        code="FORMAT_ERROR",
                        message=str(error),
                    )
                )

    return records, errors


def parse_submission(data: dict) -> Submission:
    if not isinstance(data, dict):
        raise SubmissionSchemaError(
            "submission",
            "Submission must be a JSON object",
        )

    unknown_fields = set(data) - SUBMISSION_FIELDS

    if unknown_fields:
        raise SubmissionSchemaError(
            "submission",
            f"Unknown fields: {sorted(unknown_fields)}",
        )

    required_fields = SUBMISSION_FIELDS
    missing_fields = required_fields - set(data)

    if missing_fields:
        raise SubmissionSchemaError(
            "submission",
            f"Missing fields: {sorted(missing_fields)}",
        )

    ai_data = data["ai_declaration"]

    if not isinstance(ai_data, dict):
        raise SubmissionSchemaError(
            "ai_declaration",
            "ai_declaration must be an object",
        )

    unknown_ai_fields = set(ai_data) - AI_FIELDS

    if unknown_ai_fields:
        raise SubmissionSchemaError(
            "ai_declaration",
            f"Unknown AI fields: {sorted(unknown_ai_fields)}",
        )

    missing_ai_fields = AI_FIELDS - set(ai_data)

    if missing_ai_fields:
        raise SubmissionSchemaError(
            "ai_declaration",
            f"Missing AI fields: {sorted(missing_ai_fields)}",
        )

    if type(ai_data["used"]) is not bool:
        raise SubmissionSchemaError(
            "ai_declaration.used",
            "used must be a boolean",
        )

    if type(ai_data["verified_by_student"]) is not bool:
        raise SubmissionSchemaError(
            "ai_declaration.verified_by_student",
            "verified_by_student must be a boolean",
        )

    for field in ("tool", "purpose"):
        value = ai_data[field]
        if value is not None and not isinstance(value, str):
            raise SubmissionSchemaError(
                f"ai_declaration.{field}",
                f"{field} must be a string or null",
            )

    ai = AIDeclaration(
        used=ai_data["used"],
        verified_by_student=ai_data["verified_by_student"],
        tool=ai_data["tool"],
        purpose=ai_data["purpose"],
    )

    date_value = data["submitted_at"]

    if not isinstance(date_value, str):
        raise SubmissionSchemaError(
            "submitted_at",
            "submitted_at must be an ISO 8601 string",
        )

    try:
        submitted_at = datetime.fromisoformat(date_value)
    except ValueError as error:
        raise SubmissionSchemaError(
            "submitted_at",
            f"Invalid ISO 8601 date: {date_value}",
        ) from error

    return Submission(
        schema_version=data["schema_version"],
        submission_id=data["submission_id"],
        student_id=data["student_id"],
        assignment_id=data["assignment_id"],
        submitted_at=submitted_at,
        ai_declaration=ai,
        text=data["text"],
        code=data["code"],
        template_id=data["template_id"],
    )


def import_jsonl(
    path: str,
    repository: InMemorySubmissionRepository,
) -> ImportResult:

    records, parse_errors = read_jsonl(path)

    accepted = 0
    duplicates = 0
    conflicts = 0
    errors = list(parse_errors)

    for line_number, data in records:

        try:
            submission = parse_submission(data)

            validation_errors = validate_submission(submission)

            if validation_errors:
                for error in validation_errors:
                    errors.append(
                        {
                            "line_number": line_number,
                            "code": error.code,
                            "field": error.field,
                            "message": error.message,
                        }
                    )
                continue

            status = repository.add(submission)

            if status == "accepted":
                accepted += 1

            elif status == "duplicate":
                duplicates += 1

            elif status == "conflict":
                conflicts += 1
                errors.append(
                    {
                        "line_number": line_number,
                        "code": "CONFLICT",
                        "field": "submission_id",
                        "message": (
                            "Submission ID already exists "
                            "with different content"
                        ),
                    }
                )

        except SubmissionSchemaError as error:
            errors.append(
                {
                    "line_number": line_number,
                    "code": "SCHEMA_ERROR",
                    "field": error.field,
                    "message": str(error),
                }
            )

        except (TypeError, ValueError, AttributeError) as error:
            errors.append(
                {
                    "line_number": line_number,
                    "code": "SCHEMA_ERROR",
                    "field": "submission",
                    "message": str(error),
                }
            )

    return ImportResult(
        accepted=accepted,
        duplicates=duplicates,
        conflicts=conflicts,
        errors=errors,
    )
