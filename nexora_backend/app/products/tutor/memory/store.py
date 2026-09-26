from .events import LearningEvent


class MemoryStore:

    def __init__(self):
        self.events: list[LearningEvent] = []

    def save(
        self,
        event: LearningEvent,
    ):

        self.events.append(event)
        return event

    def get_student_history(
        self,
        student_id: int,
    ):

        return [
            event
            for event in self.events
            if event.student_id == student_id
        ]
