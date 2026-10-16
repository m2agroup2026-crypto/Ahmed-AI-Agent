from collections import deque
from threading import Lock
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request
from app.api.auth.dependencies import get_current_user
from app.models.user import User
from .azure import AzureSpeechAdapter, InvalidAudio, MAX_AUDIO_BYTES, SpeechUnavailable

router = APIRouter(prefix="/api/v1/voice", tags=["Voice"])


class VoiceRateLimiter:
    """Single-process MVP limiter; shared storage is required before multi-worker use."""
    def __init__(self, clock=monotonic):
        self.clock = clock
        self.entries = {}
        self.lock = Lock()

    def check(self, user_id: int):
        now = self.clock()
        with self.lock:
            self.entries = {key: value for key, value in self.entries.items() if value[-1] > now - 60}
            if user_id not in self.entries and len(self.entries) >= 4096:
                raise HTTPException(429, "Speech capacity exceeded", headers={"Retry-After": "60"})
            attempts = self.entries.setdefault(user_id, deque())
            while attempts and attempts[0] <= now - 60:
                attempts.popleft()
            if len(attempts) >= 5:
                raise HTTPException(429, "Too many speech requests", headers={"Retry-After": "60"})
            attempts.append(now)


limiter = VoiceRateLimiter()


def get_speech_adapter() -> AzureSpeechAdapter | None:
    # Intentionally no environment switch or live transport: paid usage is forbidden.
    return None


@router.get("/capabilities")
def capabilities(user: User = Depends(get_current_user)):
    return {"azure_enabled": False, "upload_enabled": False,
            "locales": ["ar-EG", "en-US", "fr-FR"], "max_duration_seconds": 15,
            "max_audio_bytes": MAX_AUDIO_BYTES, "retains_audio": False}


@router.post("/transcriptions")
async def transcribe(request: Request, locale: str = "ar-EG", user: User = Depends(get_current_user),
                     adapter: AzureSpeechAdapter | None = Depends(get_speech_adapter)):
    limiter.check(user.id)
    # Reject before reading audio. Clients must not upload while capabilities say disabled.
    if adapter is None:
        raise HTTPException(503, "Speech uploads are disabled")
    if request.headers.get("x-audio-consent") != "true":
        raise HTTPException(400, "Explicit audio upload consent required")
    if request.headers.get("content-type", "").split(";")[0].strip() != "audio/wav":
        raise HTTPException(415, "PCM WAV required")
    audio = bytearray()
    async for chunk in request.stream():
        if len(audio) + len(chunk) > MAX_AUDIO_BYTES:
            raise HTTPException(413, "Audio exceeds size limit")
        audio.extend(chunk)
    try:
        return {"text": adapter.transcribe(bytes(audio), locale)}
    except InvalidAudio:
        raise HTTPException(422, "Unsupported or invalid recording") from None
    except SpeechUnavailable:
        raise HTTPException(503, "Speech recognition unavailable") from None
    finally:
        audio.clear()
