"""Source-aware curriculum -> lesson -> attempt -> durable resume contracts."""

from copy import deepcopy
from unittest.mock import Mock
import importlib.util
from pathlib import Path
import json
import subprocess

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from alembic.migration import MigrationContext
from alembic.operations import Operations
from pydantic import ValidationError

from app.api.auth.dependencies import get_current_user_id
from app.database.base import Base
from app.database.dependencies import get_db
from app.models.user import User
from app.products.tutor.api import router, get_tutor_gateway
from app.products.tutor.content import list_curriculum
from app.products.tutor.importer import import_curriculum_bundle
from app.products.tutor.models import AssessmentAttempt, CurriculumLesson, CurriculumUnit, CurriculumVersion
from app.products.tutor.schemas import CurriculumImportPayload
from app.tests.tutor.test_tutor_content import _payload


@pytest.fixture
def journey():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    db = Session(engine, autoflush=False)
    db.add_all([User(id=1, name="Learner", email="journey@example.test", password_hash="test"),
                User(id=2, name="Other", email="other@example.test", password_hash="test")])
    db.commit()
    bundle = _payload().model_dump()
    bundle["units"] = [{"id": "math-unit", "subject_code": "mathematics",
                        "title_ar": "وحدة اختبار", "title_en": "Test unit", "position": 1}]
    bundle["lessons"][0].update(unit_id="math-unit", position=2)
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[get_db] = lambda: db
    application.dependency_overrides[get_current_user_id] = lambda: 1
    with TestClient(application) as client:
        yield client, db, bundle, application
    db.close()
    engine.dispose()


def test_math_journey_persists_and_resumes_without_answer_leak(journey):
    client, db, bundle, _ = journey
    catalog = client.get("/api/v1/tutor/curriculum?subject_code=mathematics").json()
    assert catalog[0]["grade_level"] == "secondary-1"  # Never relabel as Grade 12.
    assert catalog[0]["units"][0]["id"] == "math-unit"
    version = catalog[0]["code"]
    lessons = client.get(f"/api/v1/tutor/lessons?subject_code=mathematics&curriculum_version={version}").json()
    assert lessons[0]["unit_id"] == "math-unit"
    lesson_id = lessons[0]["id"]
    detail = client.get(f"/api/v1/tutor/lessons/{lesson_id}?curriculum_version={version}")
    assert detail.status_code == 200
    assert detail.json()["content_en"] == bundle["lessons"][0]["content_en"]
    question = client.get(f"/api/v1/tutor/practice/next?subject_code=mathematics&curriculum_version={version}&lesson_id={lesson_id}").json()
    assert not {"accepted_answers", "explanation_ar", "explanation_en"} & question.keys()
    result = client.post("/api/v1/tutor/practice/attempts", json={"question_id": question["id"], "submitted_answer": "3", "locale": "en-US"})
    assert result.status_code == 201 and result.json()["is_correct"]
    assert result.json()["explanation_en"]
    db.expire_all()  # Read persisted state, not client memory.
    assert db.query(AssessmentAttempt).count() == 1
    progress = client.get(f"/api/v1/tutor/progress?subject_code=mathematics&curriculum_version={version}").json()
    assert progress["last_lesson_id"] == lesson_id
    assert progress["last_curriculum_version"] == version
    assert progress["lessons"] == [{"lesson_id": lesson_id, "attempts": 1, "correct_answers": 1}]


def test_resume_is_private_and_published_content_only(journey):
    client, db, bundle, application = journey
    question_id = bundle["questions"][0]["id"]
    client.post("/api/v1/tutor/practice/attempts", json={"question_id": question_id, "submitted_answer": "2"})
    application.dependency_overrides[get_current_user_id] = lambda: 2
    progress = client.get("/api/v1/tutor/progress?subject_code=mathematics").json()
    assert progress["attempts"] == 0 and progress["last_lesson_id"] is None
    application.dependency_overrides[get_current_user_id] = lambda: 1
    db.get(CurriculumLesson, bundle["lessons"][0]["id"]).status = "draft"
    db.commit()
    assert client.get("/api/v1/tutor/curriculum?subject_code=mathematics").json() == []
    assert client.get("/api/v1/tutor/progress?subject_code=mathematics").json()["last_lesson_id"] is None
    assert client.get(f"/api/v1/tutor/lessons/{bundle['lessons'][0]['id']}?curriculum_version=egypt-secondary-2026").status_code == 404
    assert db.query(AssessmentAttempt).count() == 1


def test_old_import_keeps_existing_unit_link_and_is_idempotent(journey):
    _, db, bundle, _ = journey
    original = _payload()
    import_curriculum_bundle(db, original)
    import_curriculum_bundle(db, original)
    assert db.query(CurriculumUnit).count() == 1
    assert db.get(CurriculumLesson, bundle["lessons"][0]["id"]).unit_id == "math-unit"
    assert list_curriculum(db, "physics") == []


@pytest.mark.parametrize("kind", ["unknown", "subject", "version", "duplicate"])
def test_invalid_unit_links_rejected_without_changing_saved_content(journey, kind):
    _, db, bundle, _ = journey
    bad = deepcopy(bundle)
    if kind == "unknown": bad["lessons"][0]["unit_id"] = "missing"
    if kind == "subject": bad["lessons"][0]["subject_code"] = "physics"
    if kind == "version": bad["version"]["code"] = "different-version"
    if kind == "duplicate": bad["units"].append(deepcopy(bad["units"][0]))
    with pytest.raises(HTTPException) as error:
        import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bad))
    assert error.value.status_code == 422
    assert db.get(CurriculumLesson, bundle["lessons"][0]["id"]).subject_code == "mathematics"


def test_existing_admin_import_permission_is_still_required(journey):
    client, db, bundle, application = journey
    assert client.post("/api/v1/tutor/curriculum/import", json=bundle).status_code == 403
    route = next(route for route in router.routes if getattr(route, "path", None) == "/api/v1/tutor/curriculum/import")
    permission = next(dep.call for dep in route.dependant.dependencies if dep.call.__name__ == "permission_checker")
    def denied():
        raise HTTPException(status_code=403, detail="Permission denied")
    application.dependency_overrides[permission] = denied
    assert client.post("/api/v1/tutor/curriculum/import", json=bundle).status_code == 403
    assert db.query(CurriculumUnit).count() == 1
    application.dependency_overrides[permission] = lambda: True
    assert client.post("/api/v1/tutor/curriculum/import", json=bundle).status_code == 201


def test_math_scope_does_not_include_other_subjects_and_skips_attempted_questions(journey):
    client, db, bundle, _ = journey
    other = deepcopy(bundle)
    other["units"] = []
    other["skills"] = []
    other["lessons"][0].update(id="physics-lesson", subject_code="physics", unit_id=None, skill_codes=[])
    other["questions"][0].update(id="physics-question", lesson_id="physics-lesson", skill_code=None)
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(other))
    client.post("/api/v1/tutor/practice/attempts", json={"question_id": "physics-question", "submitted_answer": "3"})
    progress = client.get("/api/v1/tutor/progress?subject_code=mathematics").json()
    assert progress["attempts"] == 0 and progress["last_lesson_id"] is None
    items = client.get("/api/v1/tutor/lessons?subject_code=mathematics&curriculum_version=egypt-secondary-2026").json()
    assert all(item["subject_code"] == "mathematics" for item in items)
    second = deepcopy(bundle)
    second["questions"][0]["id"] = "official-linear-question-2"
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(second))
    client.post("/api/v1/tutor/practice/attempts", json={"question_id": bundle["questions"][0]["id"], "submitted_answer": "3"})
    question = client.get("/api/v1/tutor/practice/next?subject_code=mathematics&lesson_id=official-linear-equations").json()
    assert question["id"] == "official-linear-question-2"


def test_missing_curriculum_does_not_create_or_relabel_content(journey):
    client, db, _, _ = journey
    assert client.get("/api/v1/tutor/lessons/api-missing?curriculum_version=grade-12").status_code == 404
    assert client.get("/api/v1/tutor/practice/next?subject_code=mathematics&curriculum_version=grade-12").status_code == 404
    assert db.query(AssessmentAttempt).count() == 0


def test_unit_migration_preserves_legacy_rows_and_downgrades():
    path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "b8c9d0e1f234_add_curriculum_unit_linkage.py"
    spec = importlib.util.spec_from_file_location("unit_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE tutor_curriculum_versions (code VARCHAR(64) PRIMARY KEY)")
        connection.exec_driver_sql("CREATE TABLE tutor_curriculum_lessons (id VARCHAR(128) PRIMARY KEY, title_en VARCHAR(255))")
        connection.exec_driver_sql("INSERT INTO tutor_curriculum_lessons VALUES ('legacy', 'Unchanged')")
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        assert connection.exec_driver_sql("SELECT title_en, unit_id, position FROM tutor_curriculum_lessons").one() == ("Unchanged", None, 0)
        migration.downgrade()
        assert connection.exec_driver_sql("SELECT * FROM tutor_curriculum_lessons").one() == ("legacy", "Unchanged")
    engine.dispose()


@pytest.mark.parametrize("locale", ["ar-EG", "en-US"])
def test_identified_choices_are_correct_after_translation_reordering(journey, locale):
    client, db, bundle, _ = journey
    question = bundle["questions"][0]
    question["choices_ar"] = [{"id": "two", "label": "\u0627\u062b\u0646\u0627\u0646"}, {"id": "three", "label": "\u062b\u0644\u0627\u062b\u0629"}]
    question["choices_en"] = [{"id": "three", "label": "Three"}, {"id": "two", "label": "Two"}]
    question["accepted_answers"] = ["three"]
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    view = client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()
    assert not {"accepted_answers", "explanation_ar", "explanation_en"} & view.keys()
    assert view["options_ar"][1]["id"] == view["options_en"][0]["id"] == "three"
    options = view["options_ar"] if locale == "ar-EG" else view["options_en"]
    for option in options:
        response = client.post("/api/v1/tutor/practice/attempts", json={
            "question_id": view["id"], "submitted_answer": option["id"], "locale": locale,
        })
        assert response.status_code == 201
        assert response.json()["is_correct"] == (option["id"] == "three")
    before = db.query(AssessmentAttempt).count()
    for answer in ["Three", "unknown"]:
        assert client.post("/api/v1/tutor/practice/attempts", json={
            "question_id": view["id"], "submitted_answer": answer, "locale": locale,
        }).status_code == 422
    assert db.query(AssessmentAttempt).count() == before


def test_legacy_choice_ids_follow_labels_instead_of_positions(journey):
    client, _, bundle, _ = journey
    bundle["questions"][0]["choices_en"] = ["4", "2", "3"]
    import_curriculum_bundle(journey[1], CurriculumImportPayload.model_validate(bundle))
    view = client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()
    ar = next(option for option in view["options_ar"] if option["label"] == "3")
    en = next(option for option in view["options_en"] if option["label"] == "3")
    assert ar["id"] == en["id"]
    response = client.post("/api/v1/tutor/practice/attempts", json={
        "question_id": view["id"], "submitted_answer": en["id"], "locale": "en-US",
    })
    assert response.status_code == 201 and response.json()["is_correct"]


@pytest.mark.parametrize("case", ["duplicate", "different_ids", "answer_label", "mixed", "ambiguous_legacy"])
def test_import_rejects_ambiguous_choice_identity(journey, case):
    _, db, bundle, _ = journey
    question = bundle["questions"][0]
    question.update(choices_ar=[{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],
                    choices_en=[{"id": "b", "label": "Bee"}, {"id": "a", "label": "Ay"}],
                    accepted_answers=["b"])
    if case == "duplicate": question["choices_en"][0]["id"] = "a"
    if case == "different_ids": question["choices_en"][0]["id"] = "c"
    if case == "answer_label": question["accepted_answers"] = ["Bee"]
    if case == "mixed": question["choices_ar"][0] = "A"
    if case == "ambiguous_legacy":
        question.update(choices_ar=["A", "B"], choices_en=["Bee", "Ay"])
    with pytest.raises(ValidationError):
        CurriculumImportPayload.model_validate(bundle)
    assert db.query(AssessmentAttempt).count() == 0


@pytest.mark.parametrize("value", ["", "   ", None])
def test_explicit_empty_unit_is_unlinked_before_database_write(journey, value):
    _, db, bundle, _ = journey
    bundle["lessons"][0]["unit_id"] = value
    payload = CurriculumImportPayload.model_validate(bundle)
    assert payload.lessons[0].unit_id is None
    import_curriculum_bundle(db, payload)
    db.expire_all()
    assert db.get(CurriculumLesson, bundle["lessons"][0]["id"]).unit_id is None
    assert db.query(CurriculumUnit).count() == 1


@pytest.mark.parametrize("language", ["ar", "en"])
def test_interface_language_switch_keeps_official_question_and_choices(journey, language):
    client, db, bundle, _ = journey
    previous_question = client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()
    previous_lesson = client.get("/api/v1/tutor/lessons/official-linear-equations?curriculum_version=egypt-secondary-2026").json()
    bundle["version"]["content_language"] = language
    # A source-language-only bundle must reach the existing mobile helpers
    # without inventing a translation in the other fields.
    other = "en" if language == "ar" else "ar"
    for item in [bundle["source"], bundle["version"], *bundle["units"],
                 *bundle["skills"], *bundle["lessons"], *bundle["questions"]]:
        for key in list(item):
            if key.endswith("_" + other):
                del item[key]
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    view = client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()
    assert view["content_language"] == language
    lesson = client.get("/api/v1/tutor/lessons/official-linear-equations?curriculum_version=egypt-secondary-2026").json()
    assert lesson["content_language"] == language
    assert lesson["content_" + language] == bundle["lessons"][0]["content_" + language]
    assert view["prompt_" + language] == bundle["questions"][0]["prompt_" + language]
    assert view["choices_" + language] == bundle["questions"][0]["choices_" + language]
    assert lesson["content_" + other] == previous_lesson["content_" + other]
    assert view["prompt_" + other] == previous_question["prompt_" + other]
    assert view["options_" + other] == previous_question["options_" + other]
    assert client.get("/api/v1/tutor/curriculum?subject_code=mathematics").json()[0]["content_language"] == language
    module = Path(__file__).resolve().parents[4] / "apps/tutor-mobile/src/learning.ts"
    # Execute the same presentation selector used by the mobile screen.
    script = """
        import assert from 'node:assert/strict';
        const {copy, readingStyle, officialQuestion, officialText} = await import(process.argv[2]);
        const {question, lesson} = JSON.parse(process.argv[1]);
        const render = uiLocale => ({
            button: copy(uiLocale, 'AR', 'EN'),
            direction: readingStyle(uiLocale).writingDirection,
            question: officialQuestion(question),
            lesson: officialText(lesson.content_language, lesson.content_ar, lesson.content_en),
        });
        const arUI = render('ar-EG'), enUI = render('en-US');
        assert.notEqual(arUI.button, enUI.button);
        assert.notEqual(arUI.direction, enUI.direction);
        assert.deepEqual(arUI.question, enUI.question);
        assert.equal(arUI.lesson, enUI.lesson);
        const language = question.content_language;
        assert.equal(arUI.question.prompt, question['prompt_' + language]);
        assert.deepEqual(arUI.question.choices, question['options_' + language]);
        assert.equal(officialQuestion({...question, content_language: null}), null);
        assert.equal(officialText(null, lesson.content_ar, lesson.content_en), null);
    """
    result = subprocess.run(
        ["node", "--experimental-strip-types", "--input-type=module", "-e", script,
         json.dumps({"question": view, "lesson": lesson}), module.as_uri()],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    response = client.post("/api/v1/tutor/practice/attempts", json={
        "question_id": view["id"], "submitted_answer": view["options_" + language][1]["id"],
        "locale": "ar-EG" if language == "ar" else "en-US",
    })
    assert response.status_code == 201
    assert response.json()["content_language"] == language


@pytest.mark.parametrize("language", ["ar", "en"])
def test_monolingual_identified_choices_are_saved_and_scored_in_source_language(journey, language):
    client, db, bundle, _ = journey
    bundle["version"]["content_language"] = language
    question = bundle["questions"][0]
    question["content_language"] = language
    question["choices_" + language] = [{"id": "two", "label": "2"}, {"id": "three", "label": "3"}]
    question["accepted_answers"] = ["three"]
    other = "en" if language == "ar" else "ar"
    question["choices_" + other] = [{"id": "two", "label": "2"}, {"id": "three", "label": "3"}]
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    previous_question = client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()
    for item in [bundle["source"], bundle["version"], *bundle["units"],
                 *bundle["skills"], *bundle["lessons"], *bundle["questions"]]:
        for key in list(item):
            if key.endswith("_" + other):
                del item[key]
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    view = client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()
    assert view["options_" + language] == question["choices_" + language]
    assert view["options_" + other] == previous_question["options_" + other]
    assert "accepted_answers" not in view and "explanation_" + language not in view
    for ui_locale in ["ar-EG", "en-US"]:
        response = client.post("/api/v1/tutor/practice/attempts", json={
            "question_id": question["id"], "submitted_answer": "three", "locale": ui_locale,
        })
        assert response.status_code == 201
        result = response.json()
        assert result["is_correct"] and result["content_language"] == language
        assert result["explanation_" + language] == question["explanation_" + language]
        assert result["explanation_" + other] == _payload().questions[0].model_dump()["explanation_" + other]
        assert db.get(AssessmentAttempt, result["attempt_id"]).locale == (
            "ar-EG" if language == "ar" else "en-US")


@pytest.mark.parametrize("case", ["missing_language", "empty_text", "blank_text", "empty_prompt",
                                 "missing_choices", "question_conflict", "unit_language"])
def test_invalid_source_language_bundle_is_rejected_before_any_mutation(journey, case):
    _, db, bundle, _ = journey
    before = db.get(CurriculumLesson, bundle["lessons"][0]["id"]).content_ar
    if case == "missing_language":
        bundle["version"]["content_language"] = None
    elif case == "empty_text":
        bundle["lessons"][0]["content_ar"] = ""
    elif case == "empty_prompt":
        bundle["questions"][0]["prompt_ar"] = ""
    elif case == "blank_text":
        bundle["lessons"][0]["summary_ar"] = "   "
    elif case == "missing_choices":
        bundle["questions"][0]["choices_ar"] = []
    elif case == "question_conflict":
        bundle["questions"][0]["content_language"] = "en"
    else:
        bundle["version"]["content_language"] = None
        bundle["lessons"][0]["content_language"] = "ar"
    bundle["source"]["id"] = "must-not-be-written"
    with pytest.raises(HTTPException) as error:
        import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert error.value.status_code == 422
    assert "language" in error.value.detail or "choices_ar" in error.value.detail
    assert not db.new and not db.dirty
    assert db.get(CurriculumLesson, bundle["lessons"][0]["id"]).content_ar == before
    from app.products.tutor.models import CurriculumSource
    assert db.get(CurriculumSource, "must-not-be-written") is None


def test_monolingual_reimport_preserves_saved_lesson_language_when_omitted(journey):
    client, db, bundle, _ = journey
    bundle["lessons"][0]["content_language"] = "ar"
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    previous_question = client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()
    del bundle["lessons"][0]["content_language"]
    bundle["version"]["content_language"] = "en"
    for item in [*bundle["lessons"], *bundle["questions"], *bundle["skills"]]:
        for key in list(item):
            if key.endswith("_en"):
                del item[key]
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    question = client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()
    assert question["content_language"] == "ar"
    assert question["options_en"] == previous_question["options_en"]
    assert question["prompt_en"] == previous_question["prompt_en"]
    assert db.get(CurriculumLesson, bundle["lessons"][0]["id"]).content_language == "ar"


def _database_rows(db, *, ignore_source_sync=False):
    """Include all persisted tables, including metadata and timestamps."""
    result = {}
    for table in Base.metadata.sorted_tables:
        columns = [column for column in table.columns if not (
            ignore_source_sync and table.name == "tutor_curriculum_sources"
            and column.name in {"last_synced_at", "updated_at"})]
        result[table.name] = sorted(repr(tuple(row)) for row in
                                  db.execute(table.select().with_only_columns(*columns)).all())
    return result


def test_omitted_language_fields_preserve_every_saved_record(journey):
    _, db, bundle, _ = journey
    before = _database_rows(db, ignore_source_sync=True)
    for item in [bundle["source"], bundle["version"], *bundle["units"],
                 *bundle["skills"], *bundle["lessons"], *bundle["questions"]]:
        for field in list(item):
            if field.endswith("_en"):
                del item[field]
    # Omitted source-language fields also retain their stored values.
    for field in ["prompt_ar", "explanation_ar", "choices_ar"]:
        del bundle["questions"][0][field]
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    after = _database_rows(db, ignore_source_sync=True)
    # Only the importer sync timestamp changes on an otherwise identical import.
    assert after == before
    from app.products.tutor.models import CurriculumSource
    assert db.get(CurriculumSource, bundle["source"]["id"]).name_en == _payload().source.name_en


@pytest.mark.parametrize("change", ["lesson", "version_fallback"])
@pytest.mark.parametrize("missing", ["prompt_en", "explanation_en", "choices_en"])
def test_language_change_rejects_incompatible_saved_questions_without_partial_update(journey, change, missing):
    _, db, bundle, _ = journey
    # Existing source-language-only questions, with an otherwise bilingual lesson.
    question = bundle["questions"][0]
    question[missing] = [] if missing == "choices_en" else ""
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    before = _database_rows(db)
    if change == "lesson":
        bundle["lessons"][0]["content_language"] = "en"
    else:
        bundle["version"]["content_language"] = "en"
    bundle["questions"] = []
    bundle["source"]["id"] = "must-not-be-written"
    with pytest.raises(HTTPException) as error:
        import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert error.value.status_code == 422
    assert question["id"] in error.value.detail and missing in error.value.detail
    assert not db.new and not db.dirty
    db.commit()  # Even a caller committing after rejection must save no partial change.
    db.expire_all()
    assert _database_rows(db) == before


def test_merged_choice_identifiers_are_validated_before_any_write(journey):
    _, db, bundle, _ = journey
    question = bundle["questions"][0]
    question.update(choices_ar=[{"id": "two", "label": "2"}, {"id": "three", "label": "3"}],
                    choices_en=[{"id": "three", "label": "3"}, {"id": "two", "label": "2"}],
                    accepted_answers=["three"])
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    before = _database_rows(db)
    del question["choices_en"]
    question["choices_ar"][0]["id"] = "different"
    with pytest.raises(HTTPException) as error:
        import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert error.value.status_code == 422 and "Merged curriculum" in error.value.detail
    assert not db.new and not db.dirty
    db.commit()
    assert _database_rows(db) == before


@pytest.mark.parametrize("field", ["prompt_ar", "explanation_ar", "choices_ar"])
def test_explicit_empty_required_question_content_is_rejected_atomically(journey, field):
    _, db, bundle, _ = journey
    before = _database_rows(db)
    bundle["questions"][0][field] = [] if field == "choices_ar" else ""
    bundle["source"]["id"] = "must-not-be-written"
    with pytest.raises(HTTPException) as error:
        import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert error.value.status_code == 422
    assert not db.new and not db.dirty
    db.commit()
    assert _database_rows(db) == before


@pytest.mark.parametrize("failure_stage", ["flush", "commit"])
def test_database_save_failure_rolls_back_all_rows_and_session_is_reusable(journey, failure_stage):
    _, db, bundle, _ = journey
    # Real SQLite errors after earlier import updates have reached the database.
    # Change metadata only; keep all fixture source texts and choices intact.
    bundle["version"]["status"] = "draft"
    bundle["units"][0]["position"] += 1
    bundle["lessons"][0].update(status="draft", position=bundle["lessons"][0]["position"] + 1)
    bundle["questions"][0]["status"] = "draft"
    connection = db.connection()
    if failure_stage == "flush":
        connection.exec_driver_sql("""
            CREATE TRIGGER import_save_failure BEFORE UPDATE ON tutor_curriculum_units
            BEGIN SELECT RAISE(ABORT, 'isolated import flush failure'); END
        """)
        expected_error = "isolated import flush failure"
    else:
        connection.exec_driver_sql("""
            CREATE TABLE isolated_import_constraint (
                version_code TEXT REFERENCES tutor_curriculum_versions(code)
                DEFERRABLE INITIALLY DEFERRED
            )
        """)
        connection.exec_driver_sql("""
            CREATE TRIGGER import_save_failure AFTER UPDATE ON tutor_curriculum_questions
            BEGIN INSERT INTO isolated_import_constraint VALUES ('missing-test-version'); END
        """)
        expected_error = "FOREIGN KEY constraint failed"
    db.commit()
    before = _database_rows(db)
    written_tables = []
    commit_calls = []

    def record_update(conn, cursor, statement, parameters, context, executemany):
        if statement.upper().startswith("UPDATE "):
            written_tables.append(statement.split()[1])

    def record_commit(session):
        commit_calls.append(True)

    engine = db.get_bind()
    event.listen(engine, "after_cursor_execute", record_update)
    event.listen(db, "before_commit", record_commit)
    try:
        with pytest.raises(IntegrityError, match=expected_error):
            import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    finally:
        event.remove(engine, "after_cursor_execute", record_update)
        event.remove(db, "before_commit", record_commit)

    assert "tutor_curriculum_versions" in written_tables
    assert len(commit_calls) == (1 if failure_stage == "commit" else 0)
    assert db.is_active and not db.new and not db.dirty
    # No caller rollback or close: reads work immediately on the same session.
    assert _database_rows(db) == before
    if failure_stage == "commit":
        assert db.connection().exec_driver_sql("SELECT count(*) FROM isolated_import_constraint").scalar_one() == 0
        assert "tutor_curriculum_questions" in written_tables
    assert db.connection().exec_driver_sql("PRAGMA foreign_key_check").all() == []

    # Remove only the test guard, then prove this session can save a new import.
    db.connection().exec_driver_sql("DROP TRIGGER import_save_failure")
    db.commit()
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert db.get(CurriculumVersion, bundle["version"]["code"]).status == "draft"
    assert db.get(CurriculumUnit, bundle["units"][0]["id"]).position == bundle["units"][0]["position"]


def test_content_language_is_declared_not_inferred_and_legacy_import_preserves_it(journey):
    client, db, bundle, _ = journey
    url = "/api/v1/tutor/curriculum?subject_code=mathematics"
    bundle["version"]["content_language"] = None
    with pytest.raises(HTTPException) as error:
        import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert error.value.status_code == 422
    assert client.get(url).json()[0]["content_language"] == "ar"
    bundle["version"]["content_language"] = "ar"
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    del bundle["version"]["content_language"]
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert client.get(url).json()[0]["content_language"] == "ar"
    bundle["version"]["content_language"] = "fr"
    with pytest.raises(ValidationError):
        CurriculumImportPayload.model_validate(bundle)
    assert client.get(url).json()[0]["content_language"] == "ar"


def test_content_language_migration_does_not_guess_legacy_language():
    path = Path(__file__).resolve().parents[3] / "alembic/versions/c9d0e1f234a5_add_curriculum_content_language.py"
    spec = importlib.util.spec_from_file_location("content_language_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE tutor_curriculum_versions (code VARCHAR(64) PRIMARY KEY)")
        connection.exec_driver_sql("INSERT INTO tutor_curriculum_versions VALUES ('legacy')")
        connection.exec_driver_sql("CREATE TABLE tutor_curriculum_units (id VARCHAR(128) PRIMARY KEY)")
        connection.exec_driver_sql("INSERT INTO tutor_curriculum_units VALUES ('legacy-unit')")
        connection.exec_driver_sql("CREATE TABLE tutor_curriculum_lessons (id VARCHAR(128) PRIMARY KEY)")
        connection.exec_driver_sql("INSERT INTO tutor_curriculum_lessons VALUES ('legacy-lesson')")
        migration.op = Operations(MigrationContext.configure(connection))
        migration.upgrade()
        assert connection.exec_driver_sql("SELECT * FROM tutor_curriculum_versions").one() == ("legacy", None)
        assert connection.exec_driver_sql("SELECT * FROM tutor_curriculum_lessons").one() == ("legacy-lesson", None)
        assert connection.exec_driver_sql("SELECT * FROM tutor_curriculum_units").one() == ("legacy-unit", None)
        migration.downgrade()
        assert connection.exec_driver_sql("SELECT * FROM tutor_curriculum_versions").one() == ("legacy",)
        assert connection.exec_driver_sql("SELECT * FROM tutor_curriculum_lessons").one() == ("legacy-lesson",)
        assert connection.exec_driver_sql("SELECT * FROM tutor_curriculum_units").one() == ("legacy-unit",)
    engine.dispose()


def test_mixed_subject_languages_use_lesson_metadata_independently_of_ui(journey):
    client, db, bundle, _ = journey
    # Reuse existing test texts only. This fixture does not create production content.
    bundle["version"]["content_language"] = None
    bundle["units"][0]["content_language"] = "ar"
    bundle["lessons"][0]["content_language"] = "ar"
    english_lesson = deepcopy(bundle["lessons"][0])
    english_lesson.update(id="english-language-contract", subject_code="english",
                          content_language="en", unit_id=None, skill_codes=[])
    english_question = deepcopy(bundle["questions"][0])
    english_question.update(id="english-question-contract", lesson_id=english_lesson["id"],
                            skill_code=None, choices_en=["4", "2", "3"])
    bundle["lessons"].append(english_lesson)
    bundle["questions"].append(english_question)
    # One mixed-language version, with no fabricated second-language fields.
    for item in [bundle["units"][0], *bundle["skills"],
                 bundle["lessons"][0], bundle["questions"][0]]:
        for key in list(item):
            if key.endswith("_en"):
                del item[key]
    for item in [english_lesson, english_question]:
        for key in list(item):
            if key.endswith("_ar"):
                del item[key]
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    db.expire_all()
    assert db.get(CurriculumLesson, bundle["lessons"][0]["id"]).content_language == "ar"
    assert db.get(CurriculumLesson, english_lesson["id"]).content_language == "en"
    catalog = client.get("/api/v1/tutor/curriculum?subject_code=mathematics").json()[0]
    assert catalog["content_language"] is None
    items = []
    for subject, language in [("mathematics", "ar"), ("english", "en")]:
        question = client.get("/api/v1/tutor/practice/next", params={
            "subject_code": subject, "curriculum_version": bundle["version"]["code"],
        }).json()
        lesson = client.get("/api/v1/tutor/lessons/" + question["lesson_id"], params={
            "curriculum_version": bundle["version"]["code"],
        }).json()
        assert question["content_language"] == lesson["content_language"] == language
        result = client.post("/api/v1/tutor/practice/attempts", json={
            "question_id": question["id"],
            "submitted_answer": next(option["id"] for option in question["options_" + language] if option["label"] == "3"),
            # Even a mismatched client locale must not select official feedback language.
            "locale": "en-US" if language == "ar" else "ar-EG",
        })
        assert result.status_code == 201
        assert result.json()["content_language"] == language
        attempt = db.get(AssessmentAttempt, result.json()["attempt_id"])
        assert attempt.locale == ("ar-EG" if language == "ar" else "en-US")
        items.append({"question": question, "lesson": lesson, "result": result.json()})
    module = Path(__file__).resolve().parents[4] / "apps/tutor-mobile/src/learning.ts"
    script = """
        import assert from 'node:assert/strict';
        const {copy, readingStyle, officialQuestion, officialText, officialAnswerLocale, hasUndeclaredMathContent, officialCurriculumTitle} = await import(process.argv[2]);
        const {items, catalog} = JSON.parse(process.argv[1]);
        const render = ui => ({
            button: copy(ui, 'AR', 'EN'), direction: readingStyle(ui).writingDirection,
            content: items.map(({question, lesson, result}) => ({
                question: officialQuestion(question), answerLocale: officialAnswerLocale(question),
                title: officialText(lesson.content_language, lesson.title_ar, lesson.title_en),
                summary: officialText(lesson.content_language, lesson.summary_ar, lesson.summary_en),
                lesson: officialText(lesson.content_language, lesson.content_ar, lesson.content_en),
                explanation: officialText(result.content_language, result.explanation_ar, result.explanation_en),
            })),
        });
        const ar = render('ar-EG'), en = render('en-US');
        assert.notEqual(ar.button, en.button);
        assert.notEqual(ar.direction, en.direction);
        assert.deepEqual(ar.content, en.content);
        for (let i = 0; i < items.length; i++) {
            const {question, lesson, result} = items[i], language = lesson.content_language;
            assert.equal(ar.content[i].question.prompt, question['prompt_' + language]);
            assert.deepEqual(ar.content[i].question.choices, question['options_' + language]);
            assert.equal(ar.content[i].lesson, lesson['content_' + language]);
            assert.equal(ar.content[i].explanation, result['explanation_' + language]);
        }
        assert.equal(ar.content[0].question.language, 'ar');
        assert.equal(ar.content[1].question.language, 'en');
        assert.equal(ar.content[0].answerLocale, 'ar-EG');
        assert.equal(ar.content[1].answerLocale, 'en-US');
        const lessons = items.map(item => item.lesson);
        assert.equal(hasUndeclaredMathContent(lessons, catalog.code), false);
        // An unrelated subject without a language must not warn on the math journey.
        assert.equal(hasUndeclaredMathContent([
            lessons[0], {...lessons[1], content_language: null},
        ], catalog.code), false);
        assert.equal(hasUndeclaredMathContent([
            {...lessons[0], content_language: null}, lessons[1],
        ], catalog.code), true);
        assert.equal(officialCurriculumTitle(catalog), catalog.code);
    """
    completed = subprocess.run(
        ["node", "--experimental-strip-types", "--input-type=module", "-e", script,
         json.dumps({"items": items, "catalog": catalog}), module.as_uri()], capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_lesson_language_is_saved_validated_and_not_guessed(journey):
    client, db, bundle, _ = journey
    lesson_id = bundle["lessons"][0]["id"]
    url = "/api/v1/tutor/lessons/" + lesson_id + "?curriculum_version=" + bundle["version"]["code"]
    bundle["version"]["content_language"] = None
    with pytest.raises(HTTPException) as error:
        import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert error.value.status_code == 422
    assert client.get(url).json()["content_language"] == "ar"
    bundle["units"][0]["content_language"] = "ar"
    bundle["lessons"][0]["content_language"] = "ar"
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert client.get(url).json()["content_language"] == "ar"
    del bundle["lessons"][0]["content_language"]
    bundle["version"]["content_language"] = "en"
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert db.get(CurriculumLesson, lesson_id).content_language == "ar"
    assert client.get(url).json()["content_language"] == "ar"
    assert client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()["content_language"] == "ar"
    bundle["lessons"][0]["content_language"] = "fr"
    with pytest.raises(ValidationError):
        CurriculumImportPayload.model_validate(bundle)
    assert db.get(CurriculumLesson, lesson_id).content_language == "ar"
    bundle["lessons"][0]["content_language"] = None
    bundle["version"]["content_language"] = "en"
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert db.get(CurriculumLesson, lesson_id).content_language is None
    assert client.get(url).json()["content_language"] == "en"


def test_unknown_language_blocks_attempt_and_tutor_without_inference(journey):
    client, db, bundle, application = journey
    bundle["version"]["content_language"] = None
    bundle["lessons"][0]["content_language"] = None
    # Simulate pre-existing undeclared metadata, now rejected on import.
    db.get(CurriculumVersion, bundle["version"]["code"]).content_language = None
    db.get(CurriculumLesson, bundle["lessons"][0]["id"]).content_language = None
    db.commit()
    view = client.get("/api/v1/tutor/practice/next?subject_code=mathematics").json()
    assert view["content_language"] is None
    attempt = client.post("/api/v1/tutor/practice/attempts", json={
        "question_id": view["id"], "submitted_answer": "3", "locale": "ar-EG",
    })
    assert attempt.status_code == 422
    assert db.query(AssessmentAttempt).count() == 0
    gateway = Mock()
    application.dependency_overrides[get_tutor_gateway] = lambda: gateway
    session = client.post("/api/v1/tutor/sessions", json={
        "subject_code": "mathematics", "curriculum_version": bundle["version"]["code"],
    }).json()
    response = client.post("/api/v1/tutor/sessions/" + session["id"] + "/messages", json={
        "content": "Explain", "lesson_id": view["lesson_id"], "locale": "en-US",
    })
    assert response.status_code == 422
    gateway.generate.assert_not_called()


def test_unit_title_language_is_explicit_or_declared_fallback(journey):
    client, db, bundle, _ = journey
    url = "/api/v1/tutor/curriculum?subject_code=mathematics"
    bundle["version"]["content_language"] = None
    # Legacy data remains withheld, without admitting new undeclared imports.
    db.get(CurriculumVersion, bundle["version"]["code"]).content_language = None
    db.commit()
    assert client.get(url).json()[0]["units"][0]["content_language"] is None
    bundle["units"][0]["content_language"] = "ar"
    bundle["version"]["content_language"] = "en"
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    unit = client.get(url).json()[0]["units"][0]
    assert unit["content_language"] == "ar"
    del bundle["units"][0]["content_language"]
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert client.get(url).json()[0]["units"][0]["content_language"] == "ar"
    bundle["units"][0]["content_language"] = None
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    assert client.get(url).json()[0]["units"][0]["content_language"] == "en"
    module = Path(__file__).resolve().parents[4] / "apps/tutor-mobile/src/learning.ts"
    script = """
        import assert from 'node:assert/strict';
        const {officialUnitTitle, officialQuestion, officialAnswerLocale} = await import(process.argv[2]);
        const unit = JSON.parse(process.argv[1]);
        assert.equal(officialUnitTitle(unit), unit.title_ar);
        assert.equal(officialUnitTitle({...unit, content_language: 'en'}), unit.title_en);
        assert.equal(officialUnitTitle({...unit, content_language: null}), null);
        assert.equal(officialQuestion({content_language: null}), null);
        assert.equal(officialAnswerLocale({content_language: null}), null);
    """
    completed = subprocess.run(
        ["node", "--experimental-strip-types", "--input-type=module", "-e", script,
         json.dumps(unit), module.as_uri()], capture_output=True, text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_tutor_uses_lesson_language_instead_of_interface_locale(journey):
    from app.products.tutor.services import append_message
    from app.products.tutor.models import LearningSession
    _, db, bundle, _ = journey
    bundle["version"]["content_language"] = "en"
    bundle["lessons"][0]["content_language"] = "ar"
    import_curriculum_bundle(db, CurriculumImportPayload.model_validate(bundle))
    session = LearningSession(user_id=1, subject_code="mathematics",
                              curriculum_version=bundle["version"]["code"])
    db.add(session)
    db.commit()
    gateway = Mock()
    gateway.generate.return_value = "Mock answer"
    append_message(db, session, "Explain", bundle["lessons"][0]["id"], "en-US", gateway)
    context = json.loads(gateway.generate.call_args.args[0].split("\n", 1)[1])
    assert context["locale"] == "ar-EG"
    assert context["lesson_context"] == bundle["lessons"][0]["content_ar"]
    assert context["lesson_title"] == bundle["lessons"][0]["title_ar"]
