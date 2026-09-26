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
