"""Azure short-audio contract. Live transport is deliberately absent in this sprint."""
from dataclasses import dataclass, field
from io import BytesIO
from typing import Callable
import re
import wave

MAX_AUDIO_BYTES = 480_044  # 15s, mono PCM16, 16kHz + canonical WAV header
LOCALES = {"ar-EG", "en-US", "fr-FR"}


class SpeechUnavailable(Exception):
    pass


class InvalidAudio(ValueError):
    pass


def validate_audio(audio: bytes) -> None:
    if not audio or len(audio) > MAX_AUDIO_BYTES:
        raise InvalidAudio("Audio size outside limit")
    try:
        with wave.open(BytesIO(audio), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 16000, "NONE"):
                raise InvalidAudio("Expected mono PCM16 WAV at 16kHz")
            frames = wav.getnframes()
            if not 0 < frames <= 240_000 or len(wav.readframes(frames)) != frames * 2:
                raise InvalidAudio("Invalid or overlong recording")
    except (wave.Error, EOFError) as exc:
        raise InvalidAudio("Invalid WAV") from exc


@dataclass(frozen=True)
class AzureSpeechConfig:
    # Secrets never appear in repr, responses, public Expo config, or logs.
    region: str
    key: str = field(repr=False)

    def __post_init__(self):
        if not re.fullmatch(r"[a-z][a-z0-9]{1,31}", self.region) or not self.key:
            raise ValueError("Invalid server speech configuration")


class AzureSpeechAdapter:
    def __init__(self, config: AzureSpeechConfig, transport: Callable | None = None):
        self.config = config
        self.transport = transport

    def transcribe(self, audio: bytes, locale: str) -> str:
        if locale not in LOCALES:
            raise InvalidAudio("Unsupported locale")
        validate_audio(audio)
        if self.transport is None:
            raise SpeechUnavailable("Live Azure transport has not been enabled")
        # The injected transport is mocked in tests. It must implement timeout=10,
        # response-size bounds, no redirects, no retries, and no audio/log retention.
        endpoint = f"https://{self.config.region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        try:
            result = self.transport(endpoint, params={"language": locale, "format": "simple"},
                headers={"Ocp-Apim-Subscription-Key": self.config.key,
                         "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000"},
                body=audio, timeout=10)
            text = result.get("DisplayText", "")
            if result.get("RecognitionStatus") != "Success" or not isinstance(text, str) or not text.strip() or len(text) > 1000:
                raise SpeechUnavailable("No usable recognition result")
            return text
        except SpeechUnavailable:
            raise
        except Exception:
            raise SpeechUnavailable("Speech service unavailable") from None
