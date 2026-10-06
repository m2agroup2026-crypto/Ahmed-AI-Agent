from .bus import NexoraEventBus


class NexoraEventService:

    def __init__(self):
        self.bus = NexoraEventBus()

    def subscribe(
        self,
        event_type: str,
        handler,
    ):

        return self.bus.subscribe(
            event_type,
            handler,
        )

    def publish(
        self,
        event,
    ):

        return self.bus.publish(
            event
        )


event_service = NexoraEventService()
