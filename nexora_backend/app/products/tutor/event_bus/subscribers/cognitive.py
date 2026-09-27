from app.products.tutor.event_bus.events import (
    NexoraEvent,
    EventTypes,
)

from app.products.tutor.cognitive_loop import (
    NexoraCognitiveService,
)


class CognitiveSubscriber:

    def __init__(self):
        self.cognitive_service = NexoraCognitiveService()

    def handle(
        self,
        event: NexoraEvent,
    ):

        payload = event.payload

        return self.cognitive_service.analyze_learning_event(
            student_id=event.student_id,
            skill=payload.get("skill", ""),
            action=payload.get("action", ""),
            result=payload.get("result", ""),
            confidence=payload.get(
                "confidence",
                0.0,
            ),
        )


cognitive_subscriber = CognitiveSubscriber()


def register_cognitive_subscriber(
    event_service,
):

    event_service.subscribe(
        EventTypes.STUDENT_RESPONSE,
        cognitive_subscriber.handle,
    )
