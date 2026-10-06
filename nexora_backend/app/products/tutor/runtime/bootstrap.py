from app.products.tutor.event_bus.subscribers.registry import (
    register_all_subscribers,
)


class NexoraRuntime:

    def __init__(self):
        self.event_service = None
        self.started = False

    def initialize(self):

        self.event_service = (
            register_all_subscribers()
        )

        self.started = True

        return {
            "status": "ready",
            "systems": [
                "event_bus",
                "cognitive_loop",
            ],
        }


nexora_runtime = NexoraRuntime()


def initialize_nexora():

    return nexora_runtime.initialize()
