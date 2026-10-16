"""Real login, SQL persistence and authorization; no identity dependency bypass."""
from datetime import timedelta
import importlib.util
from pathlib import Path
import secrets

from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.auth.router import router as auth_router
from app.database.base import Base
from app.database.dependencies import get_db
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import User
from app.products.tutor.classroom import api
from app.products.tutor.classroom.models import Classroom, Enrollment, ExamAttempt, ExternalBook
from app.security.password import hash_password

ROOT = "/api/v1/classroom"
TASK = {"title": "Original addition practice", "lesson": "Addition combines quantities.",
        "questions": [{"prompt": "What is 17 + 26?", "answer": "43"},
                      {"prompt": "What is 12 + 8?", "answer": "20"}],
        "duration_minutes": 5, "original_content_confirmed": True}


def classroom_migration():
    path = Path(__file__).parents[2] / "alembic/versions/d1e2f3a4b567_add_human_classrooms.py"
    spec = importlib.util.spec_from_file_location("classroom_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


@pytest.fixture
def journey():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    # Existing tables use their known metadata; every new classroom table is
    # created through the real migration so the journey also checks schema parity.
    classroom_tables = {"tutor_classrooms", "tutor_classroom_enrollments", "tutor_classroom_assignments",
                        "tutor_classroom_exam_attempts", "tutor_external_books"}
    Base.metadata.create_all(engine, tables=[table for table in Base.metadata.sorted_tables
                                            if table.name not in classroom_tables])
    with engine.begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            classroom_migration().upgrade()
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(api.router)
    with Session(engine) as db:
        roles = {name: Role(name=name) for name in ("TEACHER", "STUDENT", "SUPER_ADMIN")}
        db.add_all(roles.values())
        db.flush()
        permission = Permission(name="users.manage")
        db.add(permission)
        db.flush()
        db.add(RolePermission(role_id=roles["SUPER_ADMIN"].id, permission_id=permission.id))
        password = secrets.token_urlsafe(24)
        password_hash = hash_password(password)
        users = {}
        for name, role in (("teacher", "TEACHER"), ("other_teacher", "TEACHER"),
                           ("student", "STUDENT"), ("other_student", "STUDENT"),
                           ("admin", "SUPER_ADMIN"), ("unassigned", None)):
            users[name] = User(name=name, email=f"{name}@classroom.example.com",
                               password_hash=password_hash, role_id=roles[role].id if role else None)
        db.add_all(users.values())
        db.commit()
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as client:
            headers = {}
            for name, user in users.items():
                response = client.post("/auth/login", json={"email": user.email, "password": password})
                assert response.status_code == 200, response.text
                headers[name] = {"Authorization": "Bearer " + response.json()["access_token"]}
            yield client, db, headers, users
    engine.dispose()


def setup_task(journey):
    client, _, h, _ = journey
    response = client.post(ROOT + "/classes", json={"name": "Mathematics"}, headers=h["teacher"])
    assert response.status_code == 201, response.text
    classroom = response.json()
    joined = client.post(ROOT + "/join", json={"invite": classroom["invite"]}, headers=h["student"])
    assert joined.status_code == 200, joined.text
    response = client.post(ROOT + f"/classes/{classroom['id']}/assignments", json=TASK, headers=h["teacher"])
    assert response.status_code == 201, response.text
    assignment = response.json()
    response = client.post(ROOT + f"/assignments/{assignment['id']}/start", headers=h["student"])
    assert response.status_code == 200, response.text
    return classroom, assignment, response.json()


def test_full_journey_login_profile_class_lesson_exam_results_and_progress(journey):
    client, db, h, users = journey
    assert client.get(ROOT + "/me", headers=h["teacher"]).json()["role"] == "TEACHER"
    profile = client.put(ROOT + "/teacher-profile", json={"bio": "Mathematics teacher"}, headers=h["teacher"])
    assert profile.status_code == 200 and profile.json()["verification_status"] == "pending"
    classroom, assignment, attempt = setup_task(journey)
    assert "answer" not in str(assignment)
    stored_class = db.get(Classroom, classroom["id"])
    assert stored_class.invite_hash != classroom["invite"] and len(stored_class.invite_hash) == 64
    assert client.get(ROOT + "/classes", headers=h["student"]).json()[0]["id"] == classroom["id"]
    roster = client.get(ROOT + f"/classes/{classroom['id']}/students", headers=h["teacher"]).json()
    assert roster == [{"id": users["student"].id, "name": "student"}]
    student_assignment = client.get(ROOT + f"/classes/{classroom['id']}/assignments", headers=h["student"]).json()
    assert student_assignment == [{**assignment, "questions": []}]
    assert attempt["questions"] == assignment["questions"]
    assert attempt["deadline"].endswith(("Z", "+00:00"))
    retry_start = client.post(ROOT + f"/assignments/{assignment['id']}/start", headers=h["student"])
    assert retry_start.json() == attempt
    url = ROOT + f"/attempts/{attempt['id']}/submit"
    submission = {"answers": {"1": "43.0", "2": "19"}}
    result = client.post(url, json=submission, headers=h["student"])
    assert result.status_code == 200, result.text
    assert result.json()["score"] == 1 and result.json()["total"] == 2
    assert client.post(url, json=submission, headers=h["student"]).json() == result.json()
    assert client.post(url, json={"answers": {"1": "43", "2": "20"}}, headers=h["student"]).status_code == 409
    db.expire_all()
    assert db.query(ExamAttempt).count() == 1
    assert db.get(ExamAttempt, attempt["id"]).score == 1
    results = client.get(ROOT + f"/classes/{classroom['id']}/results", headers=h["teacher"])
    assert results.json() == [{**result.json(), "student_name": "student"}]
    progress = client.get(ROOT + "/progress", headers=h["student"]).json()
    assert (progress["completed"], progress["earned"], progress["possible"]) == (1, 1, 2)
    assert progress["attempts"] == [result.json()]
    assert client.get(ROOT + "/progress", headers=h["other_student"]).json()["attempts"] == []


@pytest.mark.parametrize("name", ["student", "other_student", "unassigned", "admin"])
def test_only_teacher_role_can_create_or_self_profile(journey, name):
    client, _, h, _ = journey
    assert client.post(ROOT + "/classes", json={"name": "No"}, headers=h[name]).status_code == 403
    assert client.put(ROOT + "/teacher-profile", json={"bio": "No"}, headers=h[name]).status_code == 403


@pytest.mark.parametrize("name", ["other_teacher", "other_student", "admin"])
def test_ownership_and_student_privacy(journey, name):
    client, _, h, _ = journey
    classroom, assignment, attempt = setup_task(journey)
    base = ROOT + f"/classes/{classroom['id']}"
    assert client.get(base + "/assignments", headers=h[name]).status_code == 404
    expected = 404 if name == "other_teacher" else 403
    for path in ("/students", "/results"):
        assert client.get(base + path, headers=h[name]).status_code == expected
    assert client.patch(base, json={"name": "Stolen", "archived": False}, headers=h[name]).status_code == expected
    assert client.post(base + "/assignments", json=TASK, headers=h[name]).status_code == expected
    assert client.post(base + "/invite", headers=h[name]).status_code == expected
    assert client.delete(base + "/students/1", headers=h[name]).status_code == expected
    student_expected = 404 if name == "other_student" else 403
    assert client.post(ROOT + f"/assignments/{assignment['id']}/start", headers=h[name]).status_code == student_expected
    assert client.post(ROOT + f"/attempts/{attempt['id']}/submit", json={"answers": {"1": "43", "2": "20"}},
                       headers=h[name]).status_code == student_expected


def test_authentication_role_revocation_and_disabled_accounts(journey):
    client, db, h, users = journey
    assert client.get(ROOT + "/classes").status_code == 401
    assert client.post(ROOT + "/classes", json={"name": "No"}).status_code == 401
    users["teacher"].role_id = users["student"].role_id
    db.commit()
    db.expire_all()
    assert client.post(ROOT + "/classes", json={"name": "No"}, headers=h["teacher"]).status_code == 403
    users["student"].is_active = False
    db.commit()
    assert client.get(ROOT + "/classes", headers=h["student"]).status_code == 403


def test_only_authorized_identity_admin_can_provision_teacher(journey):
    client, db, h, users = journey
    url = ROOT + f"/teachers/{users['unassigned'].id}"
    assert client.put(url).status_code == 401
    for name in ("student", "teacher", "unassigned", "other_teacher"):
        assert client.put(url, headers=h[name]).status_code == 403
    assert client.put(url, headers=h["admin"]).status_code == 200
    assert client.put(url, headers=h["admin"]).status_code == 200
    db.expire_all()
    assert client.get(ROOT + "/me", headers=h["unassigned"]).json()["role"] == "TEACHER"
    assert client.post(ROOT + "/classes", json={"name": "Provisioned teacher class"}, headers=h["unassigned"]).status_code == 201
    assert client.put(ROOT + f"/teachers/{users['admin'].id}", headers=h["admin"]).status_code == 409
    assert client.put(ROOT + "/teachers/999999", headers=h["admin"]).status_code == 404


def test_public_signup_cannot_self_assign_teacher_role(journey):
    client, db, _, users = journey
    password = secrets.token_urlsafe(24)
    response = client.post("/auth/register", json={"name": "New learner", "email": "new@classroom.example.com",
        "password": password, "role_id": users["teacher"].role_id, "role": "TEACHER"})
    assert response.status_code == 200
    user = db.get(User, response.json()["id"])
    assert user.role_id is None
    token = client.post("/auth/login", json={"email": user.email, "password": password}).json()["access_token"]
    assert client.post(ROOT + "/classes", json={"name": "No"}, headers={"Authorization": "Bearer " + token}).status_code == 403


def test_routes_are_mounted_in_real_application(journey):
    from app.main import app
    _, db, h, _ = journey
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            assert client.get(ROOT + "/me", headers=h["teacher"]).json()["role"] == "TEACHER"
            assert client.post(ROOT + "/classes", json={"name": "Real application"}, headers=h["teacher"]).status_code == 201
            assert client.get(ROOT + "/classes").status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_invite_rotation_archiving_and_enrollment_revocation(journey):
    client, db, h, users = journey
    classroom, assignment, attempt = setup_task(journey)
    base = ROOT + f"/classes/{classroom['id']}"
    assert client.post(ROOT + "/join", json={"invite": classroom["invite"]}, headers=h["student"]).status_code == 200
    assert db.query(Enrollment).count() == 1
    new = client.post(base + "/invite", headers=h["teacher"]).json()["invite"]
    assert new != classroom["invite"]
    assert client.post(ROOT + "/join", json={"invite": classroom["invite"]}, headers=h["other_student"]).status_code == 404
    assert client.post(ROOT + "/join", json={"invite": new}, headers=h["teacher"]).status_code == 403
    assert client.post(ROOT + "/join", json={"invite": new}, headers=h["other_student"]).status_code == 200
    assert client.delete(base + f"/students/{users['student'].id}", headers=h["teacher"]).status_code == 200
    assert client.get(base + "/assignments", headers=h["student"]).status_code == 404
    assert client.post(ROOT + f"/attempts/{attempt['id']}/submit", json={"answers": {"1": "43", "2": "20"}}, headers=h["student"]).status_code == 404
    assert client.patch(base, json={"name": "Archived", "archived": True}, headers=h["teacher"]).status_code == 200
    assert client.post(ROOT + "/join", json={"invite": new}, headers=h["unassigned"]).status_code == 404
    assert client.post(base + "/assignments", json=TASK, headers=h["teacher"]).status_code == 409
    assert client.post(ROOT + f"/assignments/{assignment['id']}/start", headers=h["other_student"]).status_code == 409


def test_deadline_is_server_enforced_and_start_does_not_reset_it(journey, monkeypatch):
    client, db, h, _ = journey
    _, assignment, attempt = setup_task(journey)
    deadline = db.get(ExamAttempt, attempt["id"]).deadline
    monkeypatch.setattr(api, "now", lambda: deadline + timedelta(seconds=1))
    assert client.post(ROOT + f"/assignments/{assignment['id']}/start", headers=h["student"]).json() == attempt
    response = client.post(ROOT + f"/attempts/{attempt['id']}/submit", json={"answers": {"1": "43", "2": "20"}}, headers=h["student"])
    assert response.status_code == 409
    assert db.get(ExamAttempt, attempt["id"]).submitted_at is None


@pytest.mark.parametrize("answers", [{"1": "43"}, {"1": "43", "2": "20", "3": "0"},
    {"1": "NaN", "2": "20"}, {"1": "Infinity", "2": "20"},
    {"1": "__import__('os')", "2": "20"}, {"1": "1e99999999", "2": "20"},
    {"1": True, "2": "20"}, {"1": "9" * 65, "2": "20"}])
def test_invalid_answers_do_not_mutate_attempt(journey, answers):
    client, db, h, _ = journey
    _, _, attempt = setup_task(journey)
    assert client.post(ROOT + f"/attempts/{attempt['id']}/submit", json={"answers": answers}, headers=h["student"]).status_code == 422
    assert db.get(ExamAttempt, attempt["id"]).submitted_at is None


def test_book_catalog_is_rights_aware_metadata_only_and_private(journey):
    client, db, h, _ = journey
    metadata = {"publisher": "Test publisher", "book": "Metadata fixture", "edition": "1",
                "grade": "7", "language": "en", "academic_year": "2026-2027",
                "license": "unknown", "provenance": "Teacher supplied bibliographic record"}
    response = client.post(ROOT + "/books", json=metadata, headers=h["teacher"])
    assert response.status_code == 201 and response.json()["content_import_enabled"] is False
    assert db.query(ExternalBook).count() == 1
    assert client.get(ROOT + "/books", headers=h["other_teacher"]).json() == []
    assert client.get(ROOT + "/books", headers=h["student"]).status_code == 403
    assert client.post(ROOT + "/books", json={**metadata, "license": "open_license"}, headers=h["teacher"]).status_code == 422
    assert client.post(ROOT + "/books", json={**metadata, "content": "Not accepted"}, headers=h["teacher"]).status_code == 422


def test_original_declaration_and_assignment_validation(journey):
    client, _, h, _ = journey
    classroom, _, _ = setup_task(journey)
    url = ROOT + f"/classes/{classroom['id']}/assignments"
    for patch in ({"original_content_confirmed": False}, {"questions": []}, {"duration_minutes": 0},
                  {"questions": [{"prompt": "Bad", "answer": "NaN"}]}, {"teacher_id": 2}):
        assert client.post(url, json={**TASK, **patch}, headers=h["teacher"]).status_code == 422


def test_migration_upgrade_and_downgrade_only_in_memory():
    migration = classroom_migration()
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        User.__table__.create(connection)
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            assert "tutor_classroom_exam_attempts" in inspect(connection).get_table_names()
            assert {"assignment_id", "student_id"} == set(inspect(connection).get_unique_constraints(
                "tutor_classroom_exam_attempts")[0]["column_names"])
            migration.downgrade()
            assert inspect(connection).get_table_names() == ["users"]
    engine.dispose()
