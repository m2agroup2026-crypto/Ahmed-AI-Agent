from datetime import datetime, UTC


class UsageRecord:

    def __init__(
        self,
        user_id: int,
        action: str,
        credits: int = None,
        request_id: str = None,
        credits_used: int = None
    ):

        if credits is None:
            credits = credits_used

        self.user_id = user_id

        self.action = action

        self.credits_used = credits

        # Legacy compatibility
        self.credits = credits

        self.request_id = request_id

        self.created_at = datetime.now(UTC)
