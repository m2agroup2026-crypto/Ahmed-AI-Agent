from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass
class AIContext:

    user_id: int

    last_intent: str | None = None

    last_action: str | None = None

    entity: str | None = None

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


class ContextManager:


    def __init__(self):

        self.contexts = {}


    def save(
        self,
        context: AIContext
    ):

        self.contexts[
            context.user_id
        ] = context

        return context


    def get(
        self,
        user_id: int
    ):

        return self.contexts.get(
            user_id
        )
