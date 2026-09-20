from datetime import datetime, UTC


class UsageRecord:


    def __init__(
        self,
        user_id: int,
        action: str,
        credits_used: int,
        request_id: str = None
    ):

        self.user_id = user_id

        self.action = action

        self.credits_used = credits_used

        self.request_id = request_id

        self.created_at = datetime.now(UTC)
