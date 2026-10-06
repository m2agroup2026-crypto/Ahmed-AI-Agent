from abc import ABC, abstractmethod


class BaseAgent(ABC):

    name = "base"

    capabilities = []

    def __init__(self):
        pass

    @abstractmethod
    def process(
        self,
        db,
        user_id: int,
        text: str
    ):
        raise NotImplementedError
