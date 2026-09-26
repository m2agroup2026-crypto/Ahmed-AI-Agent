import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.products.tutor.content import list_lessons
from app.products.tutor.importer import import_curriculum_bundle
from app.products.tutor.models import AssessmentAttempt, CurriculumLesson
from app.products.tutor.practice import get_next_question, submit_attempt
from app.products.tutor.progress import get_progress
from app.products.tutor.schemas import CurriculumImportPayload
from app.models.user import User


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        session.add(User(id=1, name="Practice Student", email="practice@example.com", password_hash="test"))
        session.commit()
        yield session
    Base.metadata.drop_all(bind=engine)


def _payload(*, license_status="approved", version_status="published", lesson_status="published"):
    return CurriculumImportPayload.model_validate(
        {
            "source": {
                "id": "ministry-eg",
                "name_ar": "وزارة التربية والتعليم",
                "name_en": "Ministry of Education",
                "source_type": "official",
                "base_url": "https://moe.gov.eg",
                "license_status": license_status,
                "is_active": True,
            },
            "version": {
                "code": "egypt-secondary-2026",
                "title_ar": "منهج المرحلة الثانوية 2026",
                "title_en": "Egyptian Secondary Curriculum 2026",
                "stage": "secondary",
                "grade_level": "secondary-1",
                "academic_year": "2025-2026",
                "status": version_status,
            },
            "skills": [
                {
                    "code": "math.linear-equations",
                    "subject_code": "mathematics",
                    "title_ar": "المعادلات الخطية",
                    "title_en": "Linear equations",
                    "description_ar": "حل المعادلات الخطية.",
                    "description_en": "Solve linear equations.",
                }
            ],
            "lessons": [
                {
                    "id": "official-linear-equations",
                    "subject_code": "mathematics",
                    "title_ar": "المعادلات الخطية الرسمية",
                    "title_en": "Official linear equations",
                    "summary_ar": "ملخص رسمي.",
                    "summary_en": "Official summary.",
                    "content_ar": "شرح رسمي موثق من المصدر.",
                    "content_en": "Official source-grounded explanation.",
                    "skill_codes": ["math.linear-equations"],
                    "source_url": "https://moe.gov.eg/books/linear-equations",
                    "source_locator": "page-12",
                    "source_checksum": "checksum-1",
                    "status": lesson_status,
                }
            ],
            "questions": [
                {
                    "id": "official-linear-question-1",
                    "lesson_id": "official-linear-equations",
                    "skill_code": "math.linear-equations",
                    "question_type": "single_choice",
                    "prompt_ar": "ما قيمة س في س + 2 = 5؟",
                    "prompt_en": "What is x in x + 2 = 5?",
                    "choices_ar": ["2", "3", "4"],
                    "choices_en": ["2", "3", "4"],
                    "accepted_answers": ["3"],
                    "explanation_ar": "نطرح 2 من الطرفين.",
                    "explanation_en": "Subtract 2 from both sides.",
                    "source_locator": "page-12-question-1",
                    "source_checksum": "question-checksum-1",
                    "points": 2,
                    "status": lesson_status,
                }
            ],
        }
    )


def test_import_is_idempotent_and_published_content_is_preferred(db):
    payload = _payload()

    first = import_curriculum_bundle(db, payload)
    second = import_curriculum_bundle(db, payload)

    assert first.imported_lessons == second.imported_lessons == 1
    assert db.query(CurriculumLesson).count() == 1
    lessons = list_lessons(db, "mathematics")
    assert lessons[0]["id"] == "official-linear-equations"
    assert lessons[0]["source_status"] == "approved"
    assert lessons[0]["source_locator"] == "page-12"


def test_practice_question_is_source_grounded_and_attempt_is_scored(db):
    import_curriculum_bundle(db, _payload())

    question = get_next_question(
        db,
        user_id=1,
        subject_code="mathematics",
        curriculum_version="egypt-secondary-2026",
    )
    assert question["id"] == "official-linear-question-1"
    assert question["source_locator"] == "page-12-question-1"
    assert "accepted_answers" not in question

    wrong = submit_attempt(db, 1, question["id"], "2", "ar-EG")
    assert wrong.is_correct is False
    assert wrong.score == 0
    assert wrong.next_action == "review"

    correct = submit_attempt(db, 1, question["id"], "3", "ar-EG")
    assert correct.is_correct is True
    assert correct.score == 2
    assert correct.next_action == "continue"
    assert db.query(AssessmentAttempt).count() == 2

    progress = get_progress(db, 1, "egypt-secondary-2026", "mathematics")
    assert progress["attempts"] == 2
    assert progress["correct_answers"] == 1
    assert progress["score"] == 2
    assert progress["max_score"] == 4
    assert progress["accuracy_percent"] == 50.0
    assert progress["next_focus_skill"] == "math.linear-equations"


def test_unapproved_source_cannot_publish_content(db):
    with pytest.raises(HTTPException) as error:
        import_curriculum_bundle(db, _payload(license_status="pending_review"))

    assert error.value.status_code == 422
    assert db.query(CurriculumLesson).count() == 0


def test_draft_content_is_not_exposed_until_published(db):
    import_curriculum_bundle(
        db,
        _payload(version_status="draft", lesson_status="draft"),
    )

    assert list_lessons(db, "mathematics")[0]["id"] == "math-linear-equations"
