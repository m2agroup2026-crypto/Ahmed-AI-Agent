from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    content_language: Literal["ar", "en"] | None = None
    unit_id: str | None = None
    position: int = 0
    source_id: str | None = None
    source_name_ar: str | None = None
    source_name_en: str | None = None
    source_url: str | None = None
    source_locator: str | None = None
    source_status: str | None = None


class LessonDetail(LessonSummary):
    content_ar: str
    content_en: str


class CurriculumUnitInput(BaseModel):
    content_language: Literal["ar", "en"] | None = None
    id: str = Field(min_length=1, max_length=128)
    subject_code: str = Field(min_length=1, max_length=32)
    title_ar: str = Field(default="", max_length=255)
    title_en: str = Field(default="", max_length=255)
    position: int = Field(default=0, ge=0)


class CurriculumCatalogVersion(BaseModel):
    code: str
    title_ar: str
    title_en: str
    grade_level: str
    academic_year: str
    content_language: Literal["ar", "en"] | None = None
    source_id: str
    units: list[CurriculumUnitInput]


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
    source_url: str | None = None
    source_locator: str | None = None
    adaptation_mode: str = "standard"
    next_action: str | None = None


class MessageExchange(BaseModel):
    learner_message: MessageView
    tutor_message: MessageView | None
    answer: TutorAnswer


class CurriculumSourceInput(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    name_ar: str = Field(default="", max_length=255)
    name_en: str = Field(default="", max_length=255)
    source_type: str = Field(min_length=1, max_length=32)
    base_url: str = Field(min_length=1, max_length=512)
    license_status: str = Field(default="pending_review", min_length=1, max_length=32)
    is_active: bool = True


class CurriculumVersionInput(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    title_ar: str = Field(default="", max_length=255)
    title_en: str = Field(default="", max_length=255)
    stage: str = Field(min_length=1, max_length=64)
    grade_level: str = Field(min_length=1, max_length=64)
    academic_year: str = Field(min_length=1, max_length=32)
    content_language: Literal["ar", "en"] | None = None
    status: str = Field(default="draft", min_length=1, max_length=32)


class CurriculumSkillInput(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    subject_code: str = Field(min_length=1, max_length=32)
    title_ar: str = Field(default="", max_length=255)
    title_en: str = Field(default="", max_length=255)
    description_ar: str = ""
    description_en: str = ""


class CurriculumLessonInput(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    content_language: Literal["ar", "en"] | None = None
    subject_code: str = Field(min_length=1, max_length=32)
    unit_id: str | None = Field(default=None, max_length=128)
    position: int = Field(default=0, ge=0)
    title_ar: str = Field(default="", max_length=255)
    title_en: str = Field(default="", max_length=255)
    summary_ar: str = ""
    summary_en: str = ""
    content_ar: str = ""
    content_en: str = ""
    skill_codes: list[str] = Field(default_factory=list)
    source_url: str = Field(min_length=1, max_length=512)
    source_locator: str = Field(min_length=1, max_length=255)
    source_checksum: str = Field(min_length=1, max_length=128)
    status: str = Field(default="draft", min_length=1, max_length=32)

    @field_validator("unit_id", mode="before")
    @classmethod
    def empty_unit_is_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value


class ChoiceOption(BaseModel):
    """An opaque, source-defined identity shared by translated option labels."""

    id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
    label: str = Field(min_length=1)


class CurriculumQuestionInput(BaseModel):
    # Optional assertion; questions inherit their lesson's effective language.
    content_language: Literal["ar", "en"] | None = None
    id: str = Field(min_length=1, max_length=128)
    lesson_id: str = Field(min_length=1, max_length=128)
    skill_code: str | None = Field(default=None, max_length=128)
    question_type: str = Field(default="single_choice", min_length=1, max_length=32)
    prompt_ar: str = ""
    prompt_en: str = ""
    choices_ar: list[str | ChoiceOption] = Field(default_factory=list)
    choices_en: list[str | ChoiceOption] = Field(default_factory=list)
    accepted_answers: list[str] = Field(min_length=1)
    explanation_ar: str = ""
    explanation_en: str = ""
    source_locator: str = Field(min_length=1, max_length=255)
    source_checksum: str = Field(min_length=1, max_length=128)
    points: int = Field(default=1, ge=1, le=100)
    status: str = Field(default="draft", min_length=1, max_length=32)

    @model_validator(mode="after")
    def validate_choice_identity(self):
        if not {"choices_ar", "choices_en"} <= self.model_fields_set:
            # An update may retain omitted stored choices. Validate identities
            # once the importer has assembled the complete final question.
            return self
        if self.question_type != "single_choice":
            if any(isinstance(choice, ChoiceOption) for choice in self.choices_ar + self.choices_en):
                raise ValueError("Option identifiers require a single_choice question")
            return self
        choices = self.choices_ar + self.choices_en
        if any(isinstance(choice, ChoiceOption) for choice in choices):
            if not all(isinstance(choice, ChoiceOption) for choice in choices):
                raise ValueError("Do not mix text choices and identified choices")
            ar_ids = [choice.id for choice in self.choices_ar]
            en_ids = [choice.id for choice in self.choices_en]
            if not choices or len(set(ar_ids)) != len(ar_ids) or len(set(en_ids)) != len(en_ids):
                raise ValueError("Choice identifiers must be nonempty and unique in each language")
            if ar_ids and en_ids and set(ar_ids) != set(en_ids):
                raise ValueError("Arabic and English choices must share the same identifiers")
            if not set(self.accepted_answers) <= set(ar_ids or en_ids):
                raise ValueError("Accepted answers must reference choice identifiers")
        elif (not choices or (self.choices_ar and self.choices_en and set(self.choices_ar) != set(self.choices_en))
              or len(set(self.choices_ar)) != len(self.choices_ar)
              or len(set(self.choices_en)) != len(self.choices_en)):
            raise ValueError("Legacy choices require unique labels; when both languages are supplied their labels must match, otherwise import identified choices")
        return self


class CurriculumImportPayload(BaseModel):
    source: CurriculumSourceInput
    version: CurriculumVersionInput
    units: list[CurriculumUnitInput] = Field(default_factory=list)
    skills: list[CurriculumSkillInput] = Field(default_factory=list)
    lessons: list[CurriculumLessonInput] = Field(min_length=1)
    questions: list[CurriculumQuestionInput] = Field(default_factory=list)


class CurriculumImportResult(BaseModel):
    source_id: str
    curriculum_version: str
    imported_lessons: int
    imported_skills: int
    published_lessons: int
    imported_questions: int = 0
    published_questions: int = 0
    imported_units: int = 0


class PracticeQuestionResponse(BaseModel):
    id: str
    lesson_id: str
    subject_code: str
    skill_code: str | None = None
    question_type: str
    prompt_ar: str
    prompt_en: str
    choices_ar: list[str]
    choices_en: list[str]
    options_ar: list[ChoiceOption] = Field(default_factory=list)
    options_en: list[ChoiceOption] = Field(default_factory=list)
    content_language: Literal["ar", "en"] | None = None
    curriculum_version: str
    source_url: str
    source_locator: str
    source_status: str


class PracticeAttemptCreate(BaseModel):
    question_id: str = Field(min_length=1, max_length=128)
    submitted_answer: str = Field(min_length=1, max_length=4000)
    locale: str = Field(default="ar-EG", min_length=2, max_length=16)
    session_id: str | None = Field(default=None, max_length=36)


class PracticeAttemptResponse(BaseModel):
    content_language: Literal["ar", "en"] | None = None
    attempt_id: str
    question_id: str
    is_correct: bool
    score: int
    max_score: int
    explanation_ar: str
    explanation_en: str
    source_url: str
    source_locator: str
    next_action: str


class ProgressSkill(BaseModel):
    skill_code: str
    attempts: int
    correct_answers: int
    score: int
    max_score: int
    accuracy_percent: float


class LessonProgress(BaseModel):
    lesson_id: str
    attempts: int
    correct_answers: int


class ProgressResponse(BaseModel):
    curriculum_version: str | None = None
    subject_code: str | None = None
    attempts: int
    correct_answers: int
    score: int
    max_score: int
    accuracy_percent: float
    skills: list[ProgressSkill]
    next_focus_skill: str | None = None
    last_activity_at: datetime | None = None
    last_lesson_id: str | None = None
    last_curriculum_version: str | None = None
    lessons: list[LessonProgress] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    status: str
    reason_code: str
    message_ar: str
    message_en: str
    subject_code: str
    curriculum_version: str
    skill_code: str | None = None
    skill_accuracy_percent: float | None = None
    question: PracticeQuestionResponse
