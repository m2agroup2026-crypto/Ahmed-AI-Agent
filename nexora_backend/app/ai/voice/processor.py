from app.ai.intents.detector import detect_intent


class VoiceProcessor:


    def process(
        self,
        text_command: str
    ):

        intent_result = detect_intent(
            text_command
        )

        return {
            "input": text_command,
            "intent": intent_result["intent"],
            "definition": intent_result["definition"]
        }
