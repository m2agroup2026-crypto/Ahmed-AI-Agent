from collections import defaultdict
from typing import Callable

from .events import NexoraEvent


class NexoraEventBus:

    def __init__(self):
        self.listeners = defaultdict(list)

    def subscribe(
        self,
        event_type: str,
        handler: Callable,
    ):

        self.listeners[event_type].append(
            handler
        )

    def publish(
        self,
        event: NexoraEvent,
    ):

        handlers = self.listeners.get(
            event.event_type,
            [],
        )

        results = []

        for handler in handlers:
            results.append(
                handler(event)
            )

        return results
