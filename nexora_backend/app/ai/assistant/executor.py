from app.ai.intents.registry import get_intent


class AIExecutor:


    def execute(
        self,
        intent_name: str,
        user_id: int
    ):

        intent = get_intent(intent_name)

        if not intent:
            return {
                "status": "error",
                "message": "Unknown intent"
            }


        return {
            "status": "ready",
            "user_id": user_id,
            "intent": intent_name,
            "required_permission": intent["permission"],
            "message": "Action prepared"
        }
