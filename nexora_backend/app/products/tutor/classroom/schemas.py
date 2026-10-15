from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Text120 = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Answer = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]


def numeric(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation:
        raise ValueError("A finite numeric answer is required")
    if not result.is_finite() or result.copy_abs() > Decimal("1e100"):
        raise ValueError("Answer is outside the supported numeric range")
    return result


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClassCreate(Input):
    name: Text120


class ClassUpdate(ClassCreate):
    archived: bool


class Join(Input):
    invite: Annotated[str, StringConstraints(min_length=32, max_length=128)]


class Question(Input):
    prompt: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    answer: Answer

    @field_validator("answer")
    @classmethod
    def validate_answer(cls, value):
        numeric(value)
        return value


class AssignmentCreate(Input):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    lesson: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)]
    questions: list[Question] = Field(min_length=1, max_length=30)
    duration_minutes: int = Field(strict=True, ge=1, le=180)
    original_content_confirmed: Literal[True]


class Submission(Input):
    answers: dict[str, Answer] = Field(min_length=1, max_length=30)

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, value):
        for answer in value.values():
            numeric(answer)
        return value


class ProfileUpdate(Input):
    bio: Annotated[str, StringConstraints(max_length=2000)] = ""


class BookCreate(Input):
    publisher: Text120
    book: Text120
    edition: Text120
    grade: Text120
    subject: Literal["mathematics"] = "mathematics"
    language: Text120
    academic_year: Text120
    license: Literal["unknown", "permission_required", "permission_documented", "open_license"]
    provenance: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    rights_reference: Annotated[str, StringConstraints(max_length=2000)] = ""

    @field_validator("rights_reference")
    @classmethod
    def rights_length(cls, value):
        return value.strip()
