"""Offline standard-library suite; no application database or network imports."""
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
import wave

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "nexora_backend"))
from app.voice.azure import (AzureSpeechAdapter, AzureSpeechConfig, InvalidAudio,
                             MAX_AUDIO_BYTES, SpeechUnavailable, validate_audio)


def recording(frames=1600, rate=16000, channels=1):
    target = io.BytesIO()
    with wave.open(target, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\0\0" * frames * channels)
    return target.getvalue()


class AzureSpeechTests(unittest.TestCase):
    def setUp(self):
        self.transport = Mock(return_value={"RecognitionStatus": "Success", "DisplayText": "اشرحلي ٢س + ٣ = ٧"})
        self.config = AzureSpeechConfig("uaenorth", "test-only-key")
        self.adapter = AzureSpeechAdapter(self.config, self.transport)

    def test_arabic_response_and_contract(self):
        audio = recording()
        self.assertEqual(self.adapter.transcribe(audio, "ar-EG"), "اشرحلي ٢س + ٣ = ٧")
        endpoint = self.transport.call_args.args[0]
        self.assertTrue(endpoint.startswith("https://uaenorth.stt.speech.microsoft.com/"))
        self.assertEqual(self.transport.call_args.kwargs["params"]["language"], "ar-EG")
        self.assertEqual(self.transport.call_args.kwargs["timeout"], 10)
        self.assertNotIn("test-only-key", repr(self.config))

    def test_exact_duration_and_size_boundary(self):
        audio = recording(240_000)
        self.assertEqual(len(audio), MAX_AUDIO_BYTES)
        validate_audio(audio)
        with self.assertRaises(InvalidAudio): validate_audio(recording(240_001))

    def test_invalid_audio_never_reaches_transport(self):
        for audio in [b"", b"invalid", recording(0), recording(rate=8000), recording(channels=2), recording()[:-2]]:
            with self.subTest(size=len(audio)):
                with self.assertRaises(InvalidAudio): self.adapter.transcribe(audio, "ar-EG")
        self.transport.assert_not_called()

    def test_only_allowlisted_languages(self):
        for locale in ["en-US", "fr-FR"]: self.adapter.transcribe(recording(), locale)
        with self.assertRaises(InvalidAudio): self.adapter.transcribe(recording(), "ar-EG&url=evil")

    def test_live_transport_disabled(self):
        with self.assertRaises(SpeechUnavailable): AzureSpeechAdapter(self.config).transcribe(recording(), "ar-EG")

    def test_service_failure_has_no_secret_or_provider_details(self):
        self.transport.side_effect = RuntimeError("test-only-key private provider error")
        with self.assertRaises(SpeechUnavailable) as raised: self.adapter.transcribe(recording(), "ar-EG")
        self.assertEqual(str(raised.exception), "Speech service unavailable")

    def test_empty_oversized_and_failed_results_rejected(self):
        for result in [{}, {"RecognitionStatus": "NoMatch"}, {"RecognitionStatus": "Success", "DisplayText": "x" * 1001}]:
            self.transport.return_value = result
            with self.assertRaises(SpeechUnavailable): self.adapter.transcribe(recording(), "ar-EG")

    def test_region_cannot_inject_url(self):
        for region in ["https://evil", "x/../../", "uaenorth?key=x"]:
            with self.assertRaises(ValueError): AzureSpeechConfig(region, "test-only-key")


if __name__ == "__main__":
    unittest.main()
