from core.memory.memory_store import MemoryStore
from core.memory.memory_recall import MemoryRecall


class MemoryManager:
    """
    Main interface for Ahmed AI memory operations.
    """


    def __init__(self):

        self.store = MemoryStore()
        self.recall_engine = MemoryRecall(
            self.store
        )


    def remember(self, experience):

        self.store.add(experience)


    def recall(self, context):

        return self.recall_engine.recall(
            context
        )


    def get_all_memories(self):

        return self.store.all()
