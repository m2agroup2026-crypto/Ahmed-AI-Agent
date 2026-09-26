from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


SUPPORTED_SUBJECTS = {"mathematics", "physics", "english"}


class TutorProfileUpdate(BaseModel):
    grade_level: str = Field(min_length=1, max_length=64)
    locale: str = Field(default="ar-EG", min_length=2, max_length=16)
    subject_codes: list[str] = Field(default_factory=list, max_length=3)
    learning_preferences: dict = Field(default_factory=dict)


class TutorProfileResponse(TutorProfileUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class LessonSummary(BaseModel):
    id: str
    subject_code: str
    title_ar: str
    title_en: str
    summary_ar: str
    summary_en: str
    skill_codes: list[str]
    curriculum_version: str


class SessionCreate(BaseModel):
    subject_code: str = Field(min_length=1, max_length=32)
    curriculum_version: str = Field(default="egypt-secondary-2026", min_length=1, max_length=64)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    subject_code: str
    curriculum_version: str
    status: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    lesson_id: str | None = Field(default=None, max_length=128)
    locale: str = Field(default="ar-EG", min_length=2, max_length=16)


class MessageView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    lesson_id: str | None
    created_at: datetime


class TutorAnswer(BaseModel):
    status: str
    content: str
    source_lesson_id: str | None = None
    source_title: str | None = None


class MessageExchange(BaseModel):
    learner_message: MessageView
    tutor_message: MessageView | None
    answer: TutorAnswer
