import hashlib
import json
from dataclasses import asdict

from .models import Submission

def submission_hash(submission: Submission) -> str:
    data = asdict(submission)

    data["submitted_at"] = submission.submitted_at.isoformat()

    serialized = json.dumps(
        data,
        sort_keys=True,
        separators=(",",":"),
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
