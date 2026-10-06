from .engine import NexoraXPEngine


class NexoraXPService:


    def __init__(self):

        self.engine = NexoraXPEngine()



    def reward_action(
        self,
        action: str,
    ):

        return self.engine.calculate(
            action
        )
