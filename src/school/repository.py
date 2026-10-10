from .models import Submission
from .hashing import submission_hash


class InMemorySubmissionRepository:
    def __init__(self):
        self._submissions: dict[str, Submission] = {}

    def add(self, submission: Submission) -> str:
        existing = self._submissions.get(submission.submission_id)

        if existing is None:
            self._submissions[submission.submission_id] = submission
            return "accepted"

        if submission_hash(existing) == submission_hash(submission):
            return "duplicate"

        return "conflict"

    def get(self, submission_id: str) -> Submission | None:
        return self._submissions.get(submission_id)

    def count(self) -> int:
        return len(self._submissions)