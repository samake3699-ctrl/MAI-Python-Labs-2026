from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class AIDeclaration:
    used: bool
    verified_by_student: bool
    tool: str | None = None
    purpose: str | None = None



@dataclass(frozen=True)
class Submission:
    schema_version: int
    submission_id: str
    student_id: str
    assignment_id: str
    submitted_at: datetime
    ai_declaration: AIDeclaration
    text: str = ""
    code: str = ""
    template_id: str | None = None
    

     
