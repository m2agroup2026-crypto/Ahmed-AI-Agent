from app.ai.agents.base import BaseAgent
from app.ai.core.agent import NexoraAgent


class GeneralAgent(BaseAgent):

    name = "general"

    capabilities = [
        "general_query"
    ]


    def __init__(self):
        self.engine = NexoraAgent()


    def process(
        self,
        db,
        user_id: int,
        text: str
    ):

        return self.engine.process(
            db,
            user_id,
            text
        )
