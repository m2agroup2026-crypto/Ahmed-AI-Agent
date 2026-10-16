"""Local ASGI + migrated SQLite only. Azure identity and recording are mocks."""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import inspect

from app.database.dependencies import get_db
from app.products.tutor.classroom.models import now
from app.products.tutor.live import api
from app.products.tutor.live.models import (LiveAuditEvent, LiveConsent, LiveGrant, LiveParticipant,
                                          LiveRecording, LiveSession)
from app.products.tutor.live.providers import (AcsTeamsProvider, Capabilities, LocalPreviewProvider,
                                              ProviderUnavailable, get_provider)
from app.tests.test_classroom_mvp import journey as classroom_journey

ROOT = "/api/v1/classroom"
TABLES = (LiveAuditEvent, LiveRecording, LiveConsent, LiveGrant, LiveParticipant, LiveSession)


def migration():
    path = Path(__file__).parents[2] / "alembic/versions/e2f3a4b5c678_add_live_classroom_control_plane.py"
    spec = importlib.util.spec_from_file_location("live_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def live(classroom_journey):
    client, db, h, users = classroom_journey
    client.app.include_router(api.router)
    db.rollback()
    with db.get_bind().begin() as connection:
        for model in TABLES:
            model.__table__.drop(connection)
        with Operations.context(MigrationContext.configure(connection)):
            migration().upgrade()
    response = client.post(ROOT + "/classes", json={"name": "Live mathematics"}, headers=h["teacher"])
    assert response.status_code == 201
    classroom = response.json()
    assert client.post(ROOT + "/join", json={"invite": classroom["invite"]}, headers=h["student"]).status_code == 200
    yield client, db, h, users, classroom


def schedule(live, **patch):
    client, _, h, _, classroom = live
    payload = {"title": "Original mathematics discussion", "provider": "local_preview",
               "starts_at": (now() - timedelta(minutes=1)).isoformat(),
               "ends_at": (now() + timedelta(minutes=10)).isoformat(), **patch}
    response = client.post(ROOT + f"/classes/{classroom['id']}/live", json=payload, headers=h["teacher"])
    assert response.status_code == 201, response.text
    return response.json()


def start(live, **patch):
    item = schedule(live, **patch)
    client, _, h, _, _ = live
    response = client.post(ROOT + f"/live/{item['id']}/start", headers=h["teacher"])
    assert response.status_code == 200, response.text
    return response.json()


def join(live, item, name="student"):
    client, _, h, _, _ = live
    response = client.post(ROOT + f"/live/{item['id']}/join", headers=h[name])
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()


def test_preview_lifecycle_roles_moderation_attendance_and_audit(live):
    client, db, h, users, classroom = live
    item = start(live)
    url = ROOT + f"/live/{item['id']}"
    assert item["capabilities"]["metadata_preview"] and not item["capabilities"]["media"]
    assert "provider_reference" not in item
    teacher = join(live, item, "teacher")
    student = join(live, item)
    assert student["token_purpose"] == "aqlith_application_presence_only"
    assert student["media_credentials"] is None
    assert not student["session"]["participant"]["can_speak"]
    assert teacher["session"]["participant"]["can_speak"]
    token = student["access_token"]
    assert db.get(LiveGrant, hashlib.sha256(token.encode()).hexdigest()).user_id == users["student"].id
    assert db.get(LiveGrant, token) is None
    assert client.post(url + "/heartbeat", json={"access_token": token}, headers=h["student"]).status_code == 200
    moderation = url + f"/participants/{users['student'].id}/audio"
    assert client.post(moderation, json={"allowed": True}, headers=h["teacher"]).status_code == 409
    assert client.post(url + "/hand", json={"access_token": token, "raised": True}, headers=h["student"]).status_code == 200
    assert client.post(moderation, json={"allowed": True}, headers=h["student"]).status_code == 403
    allowed = client.post(moderation, json={"allowed": True}, headers=h["teacher"])
    assert allowed.status_code == 200 and allowed.json()["can_speak"]
    assert client.post(moderation, json={"allowed": False}, headers=h["teacher"]).json()["can_speak"] is False
    roster = client.get(url + "/participants", headers=h["teacher"]).json()
    assert {p["user_id"] for p in roster} == {users["teacher"].id, users["student"].id}
    own = client.get(url + "/participants", headers=h["student"]).json()
    assert [p["user_id"] for p in own] == [users["student"].id]
    assert own[0]["presence_source"] == "application_heartbeat"
    assert client.get(ROOT + f"/classes/{classroom['id']}/live", headers=h["student"]).json()[0]["id"] == item["id"]
    assert client.post(url + "/end", headers=h["teacher"]).json()["state"] == "ended"
    assert client.post(url + "/end", headers=h["teacher"]).status_code == 200
    assert client.post(url + "/heartbeat", json={"access_token": token}, headers=h["student"]).status_code == 409
    assert client.post(url + "/join", headers=h["student"]).status_code == 409
    actions = client.get(url + "/audit", headers=h["teacher"])
    assert {"scheduled", "started", "joined", "hand.raised", "audio.allowed", "ended"} <= {e["action"] for e in actions.json()}
    assert token not in actions.text and teacher["access_token"] not in actions.text
    assert client.get(url + "/audit", headers=h["student"]).status_code == 403


@pytest.mark.parametrize("name,expected", [("other_teacher", 404), ("student", 403), ("admin", 403)])
def test_owner_only_controls(live, name, expected):
    client, _, h, users, classroom = live
    item = start(live)
    url = ROOT + f"/live/{item['id']}"
    for action in ("start", "end", "recording/start", "recording/stop", f"participants/{users['student'].id}/revoke"):
        assert client.post(url + "/" + action, headers=h[name]).status_code == expected
    assert client.post(url + f"/participants/{users['student'].id}/audio", json={"allowed": True}, headers=h[name]).status_code == expected
    payload = {"title": "No", "starts_at": now().isoformat(), "ends_at": (now() + timedelta(minutes=10)).isoformat()}
    assert client.post(ROOT + f"/classes/{classroom['id']}/live", json=payload, headers=h[name]).status_code == expected


def test_auth_and_nonmember_cross_class_isolation(live):
    client, _, h, _, _ = live
    item = start(live)
    url = ROOT + f"/live/{item['id']}"
    assert client.get(url).status_code == 401
    assert client.post(url + "/join").status_code == 401
    for name in ("other_teacher", "other_student", "admin"):
        assert client.get(url, headers=h[name]).status_code == 404
        assert client.post(url + "/join", headers=h[name]).status_code == 404
        assert client.get(url + "/recording/playback", headers=h[name]).status_code == 404


def test_grant_is_bound_to_session_user_and_expiration(live, monkeypatch):
    client, db, h, _, classroom = live
    item = start(live)
    first = join(live, item)
    second = start(live)
    join(live, second)
    token = first["access_token"]
    assert client.post(ROOT + f"/live/{second['id']}/heartbeat", json={"access_token": token}, headers=h["student"]).status_code == 403
    assert client.post(ROOT + "/join", json={"invite": classroom["invite"]}, headers=h["other_student"]).status_code == 200
    join(live, item, "other_student")
    assert client.post(ROOT + f"/live/{item['id']}/heartbeat", json={"access_token": token}, headers=h["other_student"]).status_code == 403
    grant = db.get(LiveGrant, hashlib.sha256(token.encode()).hexdigest())
    monkeypatch.setattr(api, "now", lambda: api.utc(grant.expires_at) + timedelta(seconds=1))
    assert client.post(ROOT + f"/live/{item['id']}/heartbeat", json={"access_token": token}, headers=h["student"]).status_code == 403


def test_grant_rotation_revocation_and_rejoin_denial(live):
    client, _, h, users, _ = live
    item = start(live)
    url = ROOT + f"/live/{item['id']}"
    old = join(live, item)["access_token"]
    new = join(live, item)["access_token"]
    assert old != new
    assert client.post(url + "/heartbeat", json={"access_token": old}, headers=h["student"]).status_code == 403
    assert client.post(url + "/leave", headers=h["student"]).status_code == 200
    assert client.post(url + "/heartbeat", json={"access_token": new}, headers=h["student"]).status_code == 403
    new = join(live, item)["access_token"]
    assert client.post(url + f"/participants/{users['student'].id}/revoke", headers=h["teacher"]).status_code == 200
    assert client.post(url + "/heartbeat", json={"access_token": new}, headers=h["student"]).status_code == 403
    assert client.post(url + "/join", headers=h["student"]).status_code == 403


@pytest.mark.parametrize("change,expected", [("membership", 404), ("inactive", 403), ("role", 404), ("archive", 409)])
def test_every_access_revalidates_identity_and_membership(live, change, expected):
    client, db, h, users, classroom = live
    item = start(live)
    token = join(live, item)["access_token"]
    if change == "membership":
        client.delete(ROOT + f"/classes/{classroom['id']}/students/{users['student'].id}", headers=h["teacher"])
    elif change == "inactive":
        users["student"].is_active = False
        db.commit()
    elif change == "role":
        users["student"].role = users["admin"].role
        db.commit()
    else:
        client.patch(ROOT + f"/classes/{classroom['id']}", json={"name": "Archived", "archived": True}, headers=h["teacher"])
    db.expire_all()
    assert client.post(ROOT + f"/live/{item['id']}/heartbeat", json={"access_token": token}, headers=h["student"]).status_code == expected


def test_session_expiration_and_schedule_validation(live, monkeypatch):
    client, db, h, _, classroom = live
    future = schedule(live, starts_at=(now() + timedelta(minutes=10)).isoformat(), ends_at=(now() + timedelta(minutes=20)).isoformat())
    assert client.post(ROOT + f"/live/{future['id']}/start", headers=h["teacher"]).status_code == 409
    item = start(live)
    join(live, item)
    timestamp = api.utc(db.get(LiveSession, item["id"]).ends_at)
    monkeypatch.setattr(api, "now", lambda: timestamp)
    assert client.get(ROOT + f"/live/{item['id']}", headers=h["student"]).json()["state"] == "expired"
    assert client.post(ROOT + f"/live/{item['id']}/join", headers=h["student"]).status_code == 409
    base = {"title": "Bad", "starts_at": now().isoformat(), "ends_at": (now() + timedelta(minutes=10)).isoformat()}
    for patch in ({"provider": "arbitrary"}, {"provider_reference": "client-controlled"},
                  {"ends_at": (now() + timedelta(hours=3)).isoformat()}, {"starts_at": "2026-10-15T09:00:00"}):
        assert client.post(ROOT + f"/classes/{classroom['id']}/live", json={**base, **patch}, headers=h["teacher"]).status_code == 422


def test_schedule_normalizes_timezone_offsets_before_sqlite_persistence(live):
    client, db, h, _, _ = live
    local_zone = timezone(timedelta(hours=3))
    begins = now() - timedelta(minutes=1)
    ends = now() + timedelta(minutes=10)
    item = schedule(live, starts_at=begins.astimezone(local_zone).isoformat(), ends_at=ends.astimezone(local_zone).isoformat())
    assert datetime.fromisoformat(item["starts_at"]) == begins
    assert api.utc(db.get(LiveSession, item["id"]).ends_at) == ends
    assert client.post(ROOT + f"/live/{item['id']}/start", headers=h["teacher"]).status_code == 200


def test_recording_notice_consent_and_decline_are_explicit(live):
    client, db, h, _, _ = live
    item = start(live, recording_notice=True)
    url = ROOT + f"/live/{item['id']}"
    assert set(item["recording_notice"]) == {"en", "ar"}
    assert client.post(url + "/join", headers=h["student"]).status_code == 403
    assert client.post(url + "/consent", json={"notice_version": 2, "accepted": True}, headers=h["student"]).status_code == 409
    assert client.post(url + "/consent", json={"notice_version": 1, "accepted": False}, headers=h["student"]).status_code == 200
    assert client.post(url + "/join", headers=h["student"]).status_code == 403
    assert client.post(url + "/consent", json={"notice_version": 1, "accepted": True}, headers=h["student"]).status_code == 200
    join(live, item)
    assert db.query(LiveConsent).count() == 1
    assert client.post(url + "/consent", json={"notice_version": 1, "accepted": False}, headers=h["student"]).status_code == 409
    assert client.post(url + "/leave", headers=h["student"]).status_code == 200
    assert client.post(url + "/consent", json={"notice_version": 1, "accepted": False}, headers=h["student"]).status_code == 200


def test_recording_unsupported_is_safe_and_does_not_call_provider(live, monkeypatch):
    client, db, h, _, _ = live
    provider = LocalPreviewProvider()
    provider.start_recording = Mock(side_effect=AssertionError("Must not be called"))
    monkeypatch.setattr(api, "get_provider", lambda name: provider)
    item = start(live, recording_notice=True)
    url = ROOT + f"/live/{item['id']}"
    assert client.post(url + "/recording/start", headers=h["teacher"]).status_code == 501
    assert client.post(url + "/recording/stop", headers=h["teacher"]).status_code == 501
    provider.start_recording.assert_not_called()
    assert db.get(LiveRecording, item["id"]).state == "not_started"
    assert client.get(url + "/recording/playback", headers=h["teacher"]).status_code == 404


class MockRecordingProvider(LocalPreviewProvider):
    capabilities = Capabilities(metadata_preview=True, recording=True)
    start_recording = Mock(return_value="mock-recording-reference")
    stop_recording = Mock(return_value=None)


def test_recording_control_consent_gate_and_private_playback(live, monkeypatch):
    client, db, h, users, classroom = live
    provider = MockRecordingProvider()
    monkeypatch.setattr(api, "get_provider", lambda name: provider)
    item = start(live, recording_notice=True)
    url = ROOT + f"/live/{item['id']}"
    assert client.post(url + "/recording/start", headers=h["teacher"]).status_code == 409
    for name in ("teacher", "student"):
        assert client.post(url + "/consent", json={"notice_version": 1, "accepted": True}, headers=h[name]).status_code == 200
        join(live, item, name)
    receipt = db.get(LiveConsent, (item["id"], users["student"].id))
    receipt.accepted = False
    db.commit()
    assert client.post(url + "/recording/start", headers=h["teacher"]).status_code == 409
    receipt.accepted = True
    db.commit()
    assert client.post(url + "/recording/start", headers=h["teacher"]).json() == {"state": "recording"}
    assert client.get(url, headers=h["student"]).json()["recording_state"] == "recording"
    assert client.post(url + "/recording/stop", headers=h["teacher"]).json() == {"state": "processing"}
    recording = db.get(LiveRecording, item["id"])
    recording.state, recording.storage_key, recording.encrypted = "ready", "private/test-object", True
    db.commit()
    store = SimpleNamespace(encrypted=True, stream=Mock(return_value=iter([b"test-only-mp4-fixture"])))
    monkeypatch.setattr(api, "get_recording_store", lambda: store)
    playback = client.get(url + "/recording/playback", headers=h["student"])
    assert playback.status_code == 200 and playback.content == b"test-only-mp4-fixture"
    assert playback.headers["cache-control"] == "private, no-store"
    assert playback.headers["content-disposition"] == "inline"
    assert "location" not in playback.headers
    assert recording.storage_key not in client.get(url, headers=h["student"]).text
    assert client.get(url + "/recording/playback").status_code == 401
    assert client.get(url + "/recording/playback", headers=h["other_teacher"]).status_code == 404
    client.post(ROOT + "/join", json={"invite": classroom["invite"]}, headers=h["other_student"])
    assert client.get(url + "/recording/playback", headers=h["other_student"]).status_code == 404
    assert client.post(url + f"/participants/{users['student'].id}/revoke", headers=h["teacher"]).status_code == 200
    assert client.get(url + "/recording/playback", headers=h["student"]).status_code == 404
    recording.encrypted = False
    db.commit()
    assert client.get(url + "/recording/playback", headers=h["teacher"]).status_code == 404


def test_provider_failures_do_not_expose_sensitive_details_and_fail_closed(live, monkeypatch):
    client, db, h, users, _ = live
    provider = LocalPreviewProvider()
    provider.start = Mock(side_effect=RuntimeError("synthetic-sensitive-provider-details"))
    monkeypatch.setattr(api, "get_provider", lambda name: provider)
    item = schedule(live)
    response = client.post(ROOT + f"/live/{item['id']}/start", headers=h["teacher"])
    assert response.status_code == 503 and "synthetic-sensitive" not in response.text
    assert db.get(LiveSession, item["id"]).state == "scheduled"
    provider.start = Mock(return_value="mock-session-reference")
    item = start(live)
    token = join(live, item)["access_token"]
    provider.revoke = Mock(side_effect=RuntimeError("synthetic-sensitive-provider-details"))
    url = ROOT + f"/live/{item['id']}"
    assert client.post(url + f"/participants/{users['student'].id}/revoke", headers=h["teacher"]).status_code == 503
    assert client.post(url + "/heartbeat", json={"access_token": token}, headers=h["student"]).status_code == 403
    provider.end = Mock(side_effect=RuntimeError("synthetic-sensitive-provider-details"))
    assert client.post(url + "/end", headers=h["teacher"]).status_code == 503
    assert db.get(LiveSession, item["id"]).state == "ending"
    assert client.post(url + "/join", headers=h["teacher"]).status_code == 409


def test_acs_disabled_by_default_no_identity_or_media_calls(live):
    client, db, h, _, _ = live
    item = schedule(live, provider="acs_teams")
    assert item["capabilities"]["media"] is False
    response = client.post(ROOT + f"/live/{item['id']}/start", headers=h["teacher"])
    assert response.status_code == 503
    assert db.query(LiveGrant).count() == 0
    assert db.get(LiveSession, item["id"]).state == "scheduled"
    sdk = Mock()
    provider = AcsTeamsProvider(sdk)
    with pytest.raises(ProviderUnavailable):
        provider.issue_identity_token("mock-identity")
    with pytest.raises(ProviderUnavailable):
        provider.revoke_identity_tokens("mock-identity")
    assert sdk.mock_calls == []


def test_media_provider_without_remote_enforcement_cannot_activate(live, monkeypatch):
    client, db, h, _, _ = live
    provider = LocalPreviewProvider()
    provider.capabilities = Capabilities(media=True, teacher_video=True, teacher_audio=True)
    provider.start = Mock(side_effect=AssertionError("Must not activate insecure media"))
    monkeypatch.setattr(api, "get_provider", lambda name: provider)
    item = schedule(live)
    assert client.post(ROOT + f"/live/{item['id']}/start", headers=h["teacher"]).status_code == 503
    provider.start.assert_not_called()
    assert db.get(LiveSession, item["id"]).state == "scheduled"


def test_recording_capable_mock_still_requires_notice_before_session(live, monkeypatch):
    client, _, h, _, _ = live
    provider = MockRecordingProvider()
    provider.start_recording = Mock()
    monkeypatch.setattr(api, "get_provider", lambda name: provider)
    item = start(live)
    join(live, item, "teacher")
    assert client.post(ROOT + f"/live/{item['id']}/recording/start", headers=h["teacher"]).status_code == 409
    provider.start_recording.assert_not_called()


def test_private_playback_rejects_unconfigured_or_unencrypted_storage(live, monkeypatch):
    client, db, h, _, _ = live
    item = start(live)
    recording = db.get(LiveRecording, item["id"])
    recording.state, recording.storage_key, recording.encrypted = "ready", "server-only-test-key", True
    db.commit()
    url = ROOT + f"/live/{item['id']}/recording/playback"
    response = client.get(url, headers=h["teacher"])
    assert response.status_code == 503 and "server-only-test-key" not in response.text
    stream = Mock(side_effect=AssertionError("Must not read unencrypted storage"))
    monkeypatch.setattr(api, "get_recording_store", lambda: SimpleNamespace(encrypted=False, stream=stream))
    assert client.get(url, headers=h["teacher"]).status_code == 503
    stream.assert_not_called()


def test_microphone_downgrade_provider_failure_blocks_local_permission(live, monkeypatch):
    client, db, h, users, _ = live
    item = start(live)
    join(live, item)
    participant = db.get(LiveParticipant, (item["id"], users["student"].id))
    participant.can_speak = True
    db.commit()
    provider = LocalPreviewProvider()
    provider.moderate_audio = Mock(side_effect=RuntimeError("synthetic-sensitive-detail"))
    monkeypatch.setattr(api, "get_provider", lambda name: provider)
    response = client.post(ROOT + f"/live/{item['id']}/participants/{users['student'].id}/audio",
                           json={"allowed": False}, headers=h["teacher"])
    assert response.status_code == 503 and "synthetic-sensitive-detail" not in response.text
    db.expire_all()
    assert db.get(LiveParticipant, (item["id"], users["student"].id)).can_speak is False


def test_documented_acs_identity_sdk_calls_are_mocked_not_classroom_credentials():
    sdk = Mock()
    sdk.get_token.return_value = SimpleNamespace(token="synthetic-test-token", expires_on=9999999999)
    provider = AcsTeamsProvider(sdk, external_calls_approved=True)
    token = provider.issue_identity_token("mock-identity")
    sdk.get_token.assert_called_once_with("mock-identity", scopes=["voip"], token_expires_in=timedelta(hours=1))
    assert token.expires_on == 9999999999 and token.token not in repr(token)
    provider.revoke_identity_tokens("mock-identity")
    sdk.revoke_tokens.assert_called_once_with("mock-identity")
    with pytest.raises(ProviderUnavailable):
        provider.admit("mock-meeting", 1, "teacher")
    assert get_provider("acs_teams").capabilities.recording is False


def test_live_migration_downgrade_preserves_classroom_tables(live):
    _, db, _, _, _ = live
    db.rollback()
    with db.get_bind().begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            migration().downgrade()
            assert "tutor_classrooms" in inspect(connection).get_table_names()
            assert "tutor_live_sessions" not in inspect(connection).get_table_names()
            migration().upgrade()
            assert "tutor_live_grants" in inspect(connection).get_table_names()


def test_live_routes_integrated_in_real_application(live):
    from app.main import app
    _, db, h, _, _ = live
    item = schedule(live)
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as client:
            assert client.get(ROOT + f"/live/{item['id']}", headers=h["teacher"]).status_code == 200
            assert client.get(ROOT + f"/live/{item['id']}").status_code == 401
    finally:
        app.dependency_overrides.pop(get_db, None)
