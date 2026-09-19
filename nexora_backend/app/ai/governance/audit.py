from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class AuditRecord:

    user_id: int

    action: str

    decision: str

    reason: str

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AuditLogger:


    def __init__(self):

        self.records = []


    def record(
        self,
        audit_record: AuditRecord
    ):

        self.records.append(
            audit_record
        )

        return audit_record


    def all(self):

        return self.records
