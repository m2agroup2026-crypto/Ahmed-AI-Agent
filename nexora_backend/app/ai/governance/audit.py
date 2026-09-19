from dataclasses import dataclass
from datetime import datetime


@dataclass
class AuditRecord:

    user_id: int

    action: str

    decision: str

    reason: str

    created_at: datetime = datetime.utcnow()


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
