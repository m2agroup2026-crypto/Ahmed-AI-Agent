"""Speech boundary tests use only disposable in-memory SQLite and mocked Azure."""
import asyncio
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock
import wave

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.auth.dependencies import get_current_user
from app.voice import api
from app.voice.azure import AzureSpeechAdapter, AzureSpeechConfig, MAX_AUDIO_BYTES


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "limiter", api.VoiceRateLimiter())
    app = FastAPI()
    app.include_router(api.router)
    with TestClient(app) as client:
        yield client


def authorize(client):
    client.app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=999, is_active=True)


def audio():
    data = BytesIO()
    with wave.open(data, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\0\0" * 1600)
    return data.getvalue()


def test_auth_required(client):
    assert client.get("/api/v1/voice/capabilities").status_code == 401
    assert client.post("/api/v1/voice/transcriptions").status_code == 401


def test_default_disabled_and_no_audio_retention(client):
    authorize(client)
    assert client.get("/api/v1/voice/capabilities").json()["upload_enabled"] is False
    assert client.post("/api/v1/voice/transcriptions", content=b"audio").status_code == 503


def test_disabled_route_never_reads_request_stream():
    request = Mock()
    with pytest.raises(HTTPException) as error:
        asyncio.run(api.transcribe(request, "ar-EG", SimpleNamespace(id=998), None))
    assert error.value.status_code == 503
    request.stream.assert_not_called()


def test_rate_limit_and_expiry_are_per_user():
    now = [0.0]
    limiter = api.VoiceRateLimiter(clock=lambda: now[0])
    for _ in range(5): limiter.check(1)
    with pytest.raises(HTTPException) as error: limiter.check(1)
    assert error.value.status_code == 429
    limiter.check(2)
    now[0] = 60.0
    limiter.check(1)


def test_mocked_transcription_consent_format_size_and_no_match(client):
    authorize(client)
    transport = Mock(return_value={"RecognitionStatus": "Success", "DisplayText": "وريني تقدمي"})
    adapter = AzureSpeechAdapter(AzureSpeechConfig("uaenorth", "test-only-key"), transport)
    client.app.dependency_overrides[api.get_speech_adapter] = lambda: adapter
    headers = {"x-audio-consent": "true", "content-type": "audio/wav"}
    url = "/api/v1/voice/transcriptions"
    assert client.post(url, content=audio()).status_code == 400
    assert client.post(url, content=audio(), headers={"x-audio-consent": "true"}).status_code == 415
    assert client.post(url, content=b"x" * (MAX_AUDIO_BYTES + 1), headers=headers).status_code == 413
    response = client.post(url, content=audio(), headers=headers)
    assert response.status_code == 200
    assert response.json() == {"text": "وريني تقدمي"}
    transport.assert_called_once()
    transport.return_value = {"RecognitionStatus": "NoMatch"}
    assert client.post(url, content=audio(), headers=headers).status_code == 503


def test_limiter_capacity_fails_closed():
    limiter = api.VoiceRateLimiter(clock=lambda: 1.0)
    for index in range(4096): limiter.check(index)
    with pytest.raises(HTTPException) as error: limiter.check(4097)
    assert error.value.status_code == 429
