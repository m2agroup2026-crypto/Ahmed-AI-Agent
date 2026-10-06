from app.products.tutor.event_bus.events import (
    NexoraEvent,
    EventTypes,
)

from app.products.tutor.experience import (
    NexoraExperienceService,
)


class ExperienceSubscriber:

    def __init__(self):
        self.experience_service = (
            NexoraExperienceService()
        )


    def handle(
        self,
        event: NexoraEvent,
    ):

        payload = event.payload

        return self.experience_service.build_experience(
            success=payload.get(
                "success",
                False,
            ),
            confidence=payload.get(
                "confidence",
                0.0,
            ),
        )


experience_subscriber = ExperienceSubscriber()



def register_experience_subscriber(
    event_service,
):

    event_service.subscribe(
        EventTypes.STUDENT_RESPONSE,
        experience_subscriber.handle,
    )
