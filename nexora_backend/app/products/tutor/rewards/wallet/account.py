from dataclasses import dataclass


@dataclass
class StudentWallet:

    student_id: int

    xp: int = 0

    creator_tokens: int = 0
