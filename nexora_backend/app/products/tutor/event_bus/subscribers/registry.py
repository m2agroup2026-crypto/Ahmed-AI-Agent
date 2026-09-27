from app.products.tutor.event_bus.service import (
    event_service,
)

from .cognitive import (
    register_cognitive_subscriber,
)


def register_all_subscribers():

    register_cognitive_subscriber(
        event_service
    )


    return event_service
