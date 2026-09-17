from dataclasses import dataclass


@dataclass
class AIRequest:

    source: str
    content: str
    user_id: int


class AIAssistantRouter:


    def process(
        self,
        request: AIRequest
    ):

        return {
            "source": request.source,
            "intent": "GENERAL_QUERY",
            "message": "AI Assistant Core Ready"
        }
