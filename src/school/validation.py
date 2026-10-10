from dataclasses import dataclass

from .models import Submission


FORMAT_ERROR = "FORMAT_ERROR"
SCHEMA_ERROR = "SCHEMA_ERROR"
CONFLICT_ERROR = "CONFLICT"


@dataclass(frozen=True)
class ValidationError:
    code: str
    field: str
    message: str


def validate_submission(submission: Submission) -> list[ValidationError]:
    errors: list[ValidationError] = []

    if type(submission.schema_version) is not int or submission.schema_version != 1:
        errors.append(
            ValidationError(
                code="INVALID_SCHEMA_VERSION",
                field="schema_version",
                message="schema_version must be 1",
            )
        )

    if not isinstance(submission.student_id, str):
        errors.append(
            ValidationError(
                code="INVALID_STUDENT_ID_TYPE",
                field="student_id",
                message="student_id must be a string",
            )
        )
    elif not submission.student_id.strip():
        errors.append(
            ValidationError(
                code="EMPTY_STUDENT_ID",
                field="student_id",
                message="student_id must not be empty",
            )
        )

    if not isinstance(submission.submission_id, str):
        errors.append(
            ValidationError(
                code="INVALID_SUBMISSION_ID_TYPE",
                field="submission_id",
                message="submission_id must be a string",
            )
        )
    elif not submission.submission_id.strip():
        errors.append(
            ValidationError(
                code="EMPTY_SUBMISSION_ID",
                field="submission_id",
                message="submission_id must not be empty",
            )
        )

    if not isinstance(submission.assignment_id, str):
        errors.append(
            ValidationError(
                code="INVALID_ASSIGNMENT_ID_TYPE",
                field="assignment_id",
                message="assignment_id must be a string",
            )
        )
    elif not submission.assignment_id.strip():
        errors.append(
            ValidationError(
                code="EMPTY_ASSIGNMENT_ID",
                field="assignment_id",
                message="assignment_id must not be empty",
            )
        )

    if submission.submitted_at.tzinfo is None:
        errors.append(
            ValidationError(
                code="MISSING_TIMEZONE",
                field="submitted_at",
                message="submitted_at must include a timezone",
            )
        )

    if not isinstance(submission.text, str):
        errors.append(
            ValidationError(
                code="INVALID_TEXT_TYPE",
                field="text",
                message="text must be a string",
            )
        )

    if not isinstance(submission.code, str):
        errors.append(
            ValidationError(
                code="INVALID_CODE_TYPE",
                field="code",
                message="code must be a string",
            )
        )

    if isinstance(submission.text, str) and isinstance(submission.code, str):
        if not submission.text.strip() and not submission.code.strip():
            errors.append(
                ValidationError(
                    code="EMPTY_CONTENT",
                    field="text/code",
                    message="at least one of text or code must be non-empty",
                )
            )

    if submission.template_id is not None:
        if not isinstance(submission.template_id, str):
            errors.append(
                ValidationError(
                    code="INVALID_TEMPLATE_ID_TYPE",
                    field="template_id",
                    message="template_id must be a string or null",
                )
            )
        elif not submission.template_id.strip():
            errors.append(
                ValidationError(
                    code="EMPTY_TEMPLATE_ID",
                    field="template_id",
                    message="template_id must not be empty when provided",
                )
            )

    if submission.ai_declaration.used:
        if (
            submission.ai_declaration.tool is None
            or not submission.ai_declaration.tool.strip()
        ):
            errors.append(
                ValidationError(
                    code="EMPTY_AI_TOOL",
                    field="ai_declaration.tool",
                    message="tool must be non-empty when AI is used",
                )
            )

        if (
            submission.ai_declaration.purpose is None
            or not submission.ai_declaration.purpose.strip()
        ):
            errors.append(
                ValidationError(
                    code="EMPTY_AI_PURPOSE",
                    field="ai_declaration.purpose",
                    message="purpose must be non-empty when AI is used",
                )
            )

    return errors