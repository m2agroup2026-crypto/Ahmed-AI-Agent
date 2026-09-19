from dataclasses import dataclass


@dataclass
class VoiceInput:

    source: str
    audio_reference: str | None = None


class VoiceListener:


    def capture(
        self,
        voice_input: VoiceInput
    ):

        return {
            "status": "received",
            "source": voice_input.source,
            "message": "Voice input ready for processing"
        }
