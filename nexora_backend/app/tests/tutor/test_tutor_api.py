import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth.dependencies import get_current_user_id
from app.database.base import Base
from app.database.dependencies import get_db
from app.main import app
from app.models.user import User
from app.products.tutor.models import (
    CurriculumLesson,
    CurriculumQuestion,
    CurriculumSource,
    CurriculumVersion,
)


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    user = User(name="Tutor Student", email="student@example.com", password_hash="test")
    other_user = User(name="Other Student", email="other@example.com", password_hash="test")
    db.add(user)
    db.add(other_user)
    db.commit()
    db.refresh(user)

    def override_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user_id] = lambda: user.id

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def practice_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    user = User(id=7, name="Practice Student", email="practice-api@example.com", password_hash="test")
    db.add(user)
    source = CurriculumSource(
        id="ministry-eg",
        name_ar="وزارة التربية والتعليم",
        name_en="Ministry of Education",
        source_type="official",
        base_url="https://moe.gov.eg",
        license_status="approved",
        is_active=True,
    )
    version = CurriculumVersion(
        code="egypt-secondary-2026",
        source_id=source.id,
        title_ar="منهج المرحلة الثانوية 2026",
        title_en="Egyptian Secondary Curriculum 2026",
        stage="secondary",
        grade_level="secondary-1",
        academic_year="2025-2026",
        status="published",
    )
    lesson = CurriculumLesson(
        id="api-lesson",
        curriculum_version=version.code,
        subject_code="mathematics",
        title_ar="درس الرياضيات",
        title_en="Mathematics lesson",
        summary_ar="ملخص",
        summary_en="Summary",
        content_ar="شرح",
        content_en="Explanation",
        skill_codes=[],
        source_url="https://moe.gov.eg/books/api-lesson",
        source_locator="page-1",
        source_checksum="lesson-checksum",
        status="published",
    )
    question = CurriculumQuestion(
        id="api-question",
        lesson_id=lesson.id,
        question_type="single_choice",
        prompt_ar="كم يساوي 1 + 1؟",
        prompt_en="What is 1 + 1?",
        choices_ar=["1", "2"],
        choices_en=["1", "2"],
        accepted_answers=["2"],
        explanation_ar="الناتج 2.",
        explanation_en="The result is 2.",
        source_locator="page-1-question-1",
        source_checksum="question-checksum",
        points=1,
        status="published",
    )
    db.add_all([source, version, lesson, question])
    db.commit()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user_id] = lambda: user.id
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_lessons_are_curriculum_scoped(client):
    response = client.get("/api/v1/tutor/lessons")

    assert response.status_code == 200
    lessons = response.json()
    assert {lesson["subject_code"] for lesson in lessons} == {
        "mathematics",
        "physics",
        "english",
    }
    assert all(lesson["curriculum_version"] == "egypt-secondary-2026" for lesson in lessons)


def test_student_can_create_profile_session_and_curriculum_message(client):
    profile = client.put(
        "/api/v1/tutor/profile",
        json={
            "grade_level": "secondary-1",
            "locale": "ar-EG",
            "subject_codes": ["mathematics", "physics", "english"],
            "learning_preferences": {"voice_enabled": True},
        },
    )
    assert profile.status_code == 200
    assert profile.json()["grade_level"] == "secondary-1"

    session = client.post(
        "/api/v1/tutor/sessions",
        json={"subject_code": "mathematics"},
    )
    assert session.status_code == 201
    session_id = session.json()["id"]

    exchange = client.post(
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={
            "content": "اشرح لي الدرس",
            "lesson_id": "math-linear-equations",
            "locale": "ar-EG",
        },
    )
    assert exchange.status_code == 200
    body = exchange.json()
    assert body["answer"]["status"] == "curriculum_context"
    assert body["answer"]["source_lesson_id"] == "math-linear-equations"
    assert body["answer"]["adaptation_mode"] == "standard"
    assert body["answer"]["next_action"] == "practice"
    assert body["tutor_message"]["role"] == "tutor"


def test_unknown_subject_is_rejected(client):
    response = client.post(
        "/api/v1/tutor/sessions",
        json={"subject_code": "biology"},
    )

    assert response.status_code == 422


def test_session_is_not_visible_to_another_authenticated_user(client):
    session = client.post(
        "/api/v1/tutor/sessions",
        json={"subject_code": "physics"},
    )
    session_id = session.json()["id"]

    app.dependency_overrides[get_current_user_id] = lambda: 2
    response = client.get(f"/api/v1/tutor/sessions/{session_id}")

    assert response.status_code == 404


def test_curriculum_import_requires_platform_permission(client):
    response = client.post(
        "/api/v1/tutor/curriculum/import",
        json={
            "source": {
                "id": "ministry-eg",
                "name_ar": "وزارة التربية والتعليم",
                "name_en": "Ministry of Education",
                "source_type": "official",
                "base_url": "https://moe.gov.eg",
                "license_status": "approved",
            },
            "version": {
                "code": "egypt-secondary-2026",
                "title_ar": "منهج المرحلة الثانوية 2026",
                "title_en": "Egyptian Secondary Curriculum 2026",
                "stage": "secondary",
                "grade_level": "secondary-1",
                "academic_year": "2025-2026",
                "status": "published",
            },
            "lessons": [
                {
                    "id": "official-lesson",
                    "subject_code": "mathematics",
                    "title_ar": "درس رسمي",
                    "title_en": "Official lesson",
                    "summary_ar": "ملخص",
                    "summary_en": "Summary",
                    "content_ar": "شرح",
                    "content_en": "Explanation",
                    "source_url": "https://moe.gov.eg/books/lesson",
                    "source_locator": "page-1",
                    "source_checksum": "checksum",
                    "status": "published",
                }
            ],
        },
    )

    assert response.status_code == 403


def test_practice_api_returns_question_and_persists_attempt(practice_client):
    question_response = practice_client.get(
        "/api/v1/tutor/practice/next?subject_code=mathematics"
    )
    assert question_response.status_code == 200
    question = question_response.json()
    assert question["id"] == "api-question"
    assert "accepted_answers" not in question

    attempt_response = practice_client.post(
        "/api/v1/tutor/practice/attempts",
        json={
            "question_id": question["id"],
            "submitted_answer": "2",
            "locale": "en-US",
        },
    )
    assert attempt_response.status_code == 201
    body = attempt_response.json()
    assert body["is_correct"] is True
    assert body["score"] == 1
    assert body["next_action"] == "continue"

    progress_response = practice_client.get("/api/v1/tutor/progress")
    assert progress_response.status_code == 200
    progress = progress_response.json()
    assert progress["attempts"] == 1
    assert progress["correct_answers"] == 1
    assert progress["accuracy_percent"] == 100.0
