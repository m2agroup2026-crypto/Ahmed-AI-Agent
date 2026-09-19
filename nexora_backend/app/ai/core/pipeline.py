from app.ai.intents.detector import detect_intent


class AgentPipeline:


    def run(
        self,
        state
    ):

        intent_result = detect_intent(
            state.input_text
        )

        state.intent = intent_result["intent"]

        state.permission = intent_result["definition"]["permission"]

        state.status = "intent_detected"

        return state
