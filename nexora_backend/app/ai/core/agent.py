from app.ai.core.state import AgentState
from app.ai.core.pipeline import AgentPipeline


class NexoraAgent:


    def __init__(self):

        self.pipeline = AgentPipeline()


    def process(
        self,
        user_id: int,
        text: str
    ):

        state = AgentState(
            user_id,
            text
        )

        return self.pipeline.run(
            state
        )
