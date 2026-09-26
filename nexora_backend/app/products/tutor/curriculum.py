"""Small, versioned curriculum catalog used by the first Tutor foundation slice.

The catalog is intentionally explicit and finite. It is not a generated answer
source and it contains no learner metrics. A later content service can replace
this module without changing the API response shape.
"""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Lesson:
    id: str
    subject_code: str
    title_ar: str
    title_en: str
    summary_ar: str
    summary_en: str
    skill_codes: tuple[str, ...]
    curriculum_version: str = "egypt-secondary-2026"


LESSONS: tuple[Lesson, ...] = (
    Lesson(
        id="math-linear-equations",
        subject_code="mathematics",
        title_ar="المعادلات الخطية",
        title_en="Linear equations",
        summary_ar="تعرّف على نقل الحدود وتجميع الحدود المتشابهة وحل المعادلة خطوة بخطوة.",
        summary_en="Learn to isolate the unknown, combine like terms, and solve a linear equation step by step.",
        skill_codes=("algebra", "equations"),
    ),
    Lesson(
        id="physics-motion-basics",
        subject_code="physics",
        title_ar="أساسيات الحركة",
        title_en="Motion basics",
        summary_ar="راجع المسافة والسرعة والزمن والعلاقة بينها في مسائل الحركة الأساسية.",
        summary_en="Review distance, speed, time, and their relationship in introductory motion problems.",
        skill_codes=("kinematics", "units"),
    ),
    Lesson(
        id="english-reading-context",
        subject_code="english",
        title_ar="فهم المقروء من السياق",
        title_en="Reading from context",
        summary_ar="استخدم الكلمات المحيطة وعلامات الربط لاستنتاج معنى المفردة داخل النص.",
        summary_en="Use surrounding words and connectors to infer the meaning of a word in context.",
        skill_codes=("reading", "vocabulary"),
    ),
)


def list_lessons(subject_code: str | None = None) -> list[dict]:
    lessons = (
        lesson for lesson in LESSONS if subject_code is None or lesson.subject_code == subject_code
    )
    return [asdict(lesson) for lesson in lessons]


def get_lesson(lesson_id: str | None) -> Lesson | None:
    if not lesson_id:
        return None
    return next((lesson for lesson in LESSONS if lesson.id == lesson_id), None)


def get_subject_lesson(subject_code: str) -> Lesson | None:
    return next((lesson for lesson in LESSONS if lesson.subject_code == subject_code), None)
