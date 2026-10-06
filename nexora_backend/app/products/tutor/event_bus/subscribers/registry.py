from app.products.tutor.event_bus.service import (
    event_service,
)

from .cognitive import (
    register_cognitive_subscriber,
)

from .experience import (
    register_experience_subscriber,
)


def register_all_subscribers():

    register_cognitive_subscriber(
        event_service
    )

    register_experience_subscriber(
        event_service
    )

    return event_service
