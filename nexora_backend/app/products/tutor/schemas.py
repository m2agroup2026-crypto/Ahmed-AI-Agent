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
    source_id: str | None = None
    source_name_ar: str | None = None
    source_name_en: str | None = None
    source_url: str | None = None
    source_locator: str | None = None
    source_status: str | None = None


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
    name_ar: str = Field(min_length=1, max_length=255)
    name_en: str = Field(min_length=1, max_length=255)
    source_type: str = Field(min_length=1, max_length=32)
    base_url: str = Field(min_length=1, max_length=512)
    license_status: str = Field(default="pending_review", min_length=1, max_length=32)
    is_active: bool = True


class CurriculumVersionInput(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    title_ar: str = Field(min_length=1, max_length=255)
    title_en: str = Field(min_length=1, max_length=255)
    stage: str = Field(min_length=1, max_length=64)
    grade_level: str = Field(min_length=1, max_length=64)
    academic_year: str = Field(min_length=1, max_length=32)
    status: str = Field(default="draft", min_length=1, max_length=32)


class CurriculumSkillInput(BaseModel):
    code: str = Field(min_length=1, max_length=128)
    subject_code: str = Field(min_length=1, max_length=32)
    title_ar: str = Field(min_length=1, max_length=255)
    title_en: str = Field(min_length=1, max_length=255)
    description_ar: str = Field(min_length=1)
    description_en: str = Field(min_length=1)


class CurriculumLessonInput(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    subject_code: str = Field(min_length=1, max_length=32)
    title_ar: str = Field(min_length=1, max_length=255)
    title_en: str = Field(min_length=1, max_length=255)
    summary_ar: str = Field(min_length=1)
    summary_en: str = Field(min_length=1)
    content_ar: str = Field(min_length=1)
    content_en: str = Field(min_length=1)
    skill_codes: list[str] = Field(default_factory=list)
    source_url: str = Field(min_length=1, max_length=512)
    source_locator: str = Field(min_length=1, max_length=255)
    source_checksum: str = Field(min_length=1, max_length=128)
    status: str = Field(default="draft", min_length=1, max_length=32)


class CurriculumQuestionInput(BaseModel):
    id: str = Field(min_length=1, max_length=128)
    lesson_id: str = Field(min_length=1, max_length=128)
    skill_code: str | None = Field(default=None, max_length=128)
    question_type: str = Field(default="single_choice", min_length=1, max_length=32)
    prompt_ar: str = Field(min_length=1)
    prompt_en: str = Field(min_length=1)
    choices_ar: list[str] = Field(default_factory=list)
    choices_en: list[str] = Field(default_factory=list)
    accepted_answers: list[str] = Field(min_length=1)
    explanation_ar: str = Field(min_length=1)
    explanation_en: str = Field(min_length=1)
    source_locator: str = Field(min_length=1, max_length=255)
    source_checksum: str = Field(min_length=1, max_length=128)
    points: int = Field(default=1, ge=1, le=100)
    status: str = Field(default="draft", min_length=1, max_length=32)


class CurriculumImportPayload(BaseModel):
    source: CurriculumSourceInput
    version: CurriculumVersionInput
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
