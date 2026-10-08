from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

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
from app.config.settings import settings
from app.products.tutor.api import get_tutor_gateway
from app.security.jwt import create_access_token
from jose import jwt
from app.products.tutor.models import (
    CurriculumLesson,
    CurriculumQuestion,
    CurriculumSource,
    CurriculumVersion,
    LearningMessage,
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
    gateway = Mock()
    gateway.generate.return_value = "شرح تعليمي مولد للاختبار"
    app.dependency_overrides[get_tutor_gateway] = lambda: gateway

    try:
        with TestClient(app) as test_client:
            test_client.tutor_gateway = gateway
            test_client.tutor_db = db
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
    assert body["answer"]["content"] == body["tutor_message"]["content"] == client.tutor_gateway.generate.return_value
    client.tutor_gateway.generate.assert_called_once()
    messages = client.get(f"/api/v1/tutor/sessions/{session_id}/messages").json()
    assert [message["role"] for message in messages] == ["learner", "tutor"]
    assert messages[1]["content"] == body["answer"]["content"]


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


def _message_session(client):
    return client.post("/api/v1/tutor/sessions", json={"subject_code": "mathematics"}).json()["id"]


def _use_jwt(client, user_id=1):
    app.dependency_overrides.pop(get_current_user_id, None)
    client.headers["Authorization"] = "Bearer " + create_access_token({"user_id": user_id})


def test_message_uses_jwt_identity_and_ignores_client_user_id(client):
    session_id = _message_session(client)
    _use_jwt(client)
    response = client.post(
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"content": "How do I solve x + 2 = 5?", "user_id": 2, "locale": "en-US"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"]["content"] == body["tutor_message"]["content"]
    assert body["learner_message"]["content"] == "How do I solve x + 2 = 5?"
    client.tutor_gateway.generate.assert_called_once()
    prompt = client.tutor_gateway.generate.call_args.args[0]
    assert "How do I solve x + 2 = 5?" in prompt
    assert "mathematics" in prompt and "egypt-secondary-2026" in prompt
    assert "Respond in English" in prompt
    assert client.tutor_db.query(LearningMessage).count() == 2


@pytest.mark.parametrize("token_kind", ["missing", "invalid", "expired"])
def test_message_rejects_bad_jwt_without_inference(client, token_kind):
    session_id = _message_session(client)
    app.dependency_overrides.pop(get_current_user_id, None)
    if token_kind == "invalid":
        client.headers["Authorization"] = "Bearer invalid-token"
    elif token_kind == "expired":
        token = jwt.encode(
            {"user_id": 1, "exp": datetime.now(UTC) - timedelta(minutes=1)},
            settings.SECRET_KEY, algorithm=settings.ALGORITHM,
        )
        client.headers["Authorization"] = "Bearer " + token
    response = client.post(f"/api/v1/tutor/sessions/{session_id}/messages", json={"content": "Explain"})
    assert response.status_code == 401
    client.tutor_gateway.generate.assert_not_called()
    assert client.tutor_db.query(LearningMessage).count() == 0


@pytest.mark.parametrize("case", ["foreign", "missing", "inactive", "missing_user"])
def test_message_checks_user_and_session_before_inference(client, case):
    session_id = _message_session(client)
    if case == "inactive":
        client.tutor_db.get(User, 1).is_active = False
        client.tutor_db.commit()
    _use_jwt(client, 2 if case == "foreign" else 999 if case == "missing_user" else 1)
    if case == "missing":
        session_id = "nonexistent-session"
    response = client.post(
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"content": "Explain", "user_id": 1},
    )
    assert response.status_code == (401 if case in {"inactive", "missing_user"} else 404)
    client.tutor_gateway.generate.assert_not_called()
    assert client.tutor_db.query(LearningMessage).count() == 0


@pytest.mark.parametrize("failure, expected", [(RuntimeError("private provider detail"), 502), (TimeoutError(), 504), ("", 502), ("   ", 502)])
def test_message_upstream_failures_are_controlled_and_not_persisted(client, failure, expected):
    session_id = _message_session(client)
    if isinstance(failure, Exception):
        client.tutor_gateway.generate.side_effect = failure
    else:
        client.tutor_gateway.generate.return_value = failure
    response = client.post(f"/api/v1/tutor/sessions/{session_id}/messages", json={"content": "Explain"})
    assert response.status_code == expected
    assert "private provider detail" not in response.text
    client.tutor_gateway.generate.assert_called_once()
    assert client.tutor_db.query(LearningMessage).count() == 0


def test_message_rejects_cross_subject_lesson(client):
    session_id = _message_session(client)
    from app.products.tutor.curriculum import get_subject_lesson
    lesson = get_subject_lesson("physics")
    response = client.post(
        f"/api/v1/tutor/sessions/{session_id}/messages",
        json={"content": "Explain", "lesson_id": lesson.id},
    )
    assert response.status_code == 422
    client.tutor_gateway.generate.assert_not_called()
    assert client.tutor_db.query(LearningMessage).count() == 0


def test_message_without_context_keeps_learner_only(client):
    session = client.post(
        "/api/v1/tutor/sessions", json={"subject_code": "mathematics", "curriculum_version": "unavailable"}
    ).json()
    response = client.post(f"/api/v1/tutor/sessions/{session['id']}/messages", json={"content": "Explain"})
    assert response.status_code == 200
    assert response.json()["answer"]["status"] == "needs_context"
    assert response.json()["tutor_message"] is None
    client.tutor_gateway.generate.assert_not_called()
    assert client.tutor_db.query(LearningMessage).count() == 1


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
    recommendation_response = practice_client.get("/api/v1/tutor/recommendation")
    assert recommendation_response.status_code == 200
    recommendation = recommendation_response.json()
    assert recommendation["reason_code"] == "start_learning"
    assert recommendation["question"]["id"] == "api-question"

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
