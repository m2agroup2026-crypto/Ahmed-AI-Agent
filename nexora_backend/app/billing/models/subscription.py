from datetime import datetime, UTC


class Subscription:


    def __init__(
        self,
        user_id: int,
        plan_id: int,
        status: str = "ACTIVE"
    ):

        self.user_id = user_id

        self.plan_id = plan_id

        self.status = status

        self.start_date = datetime.now(UTC)

        self.end_date = None

        self.created_at = datetime.now(UTC)


    def cancel(self):

        self.status = "CANCELLED"

        self.end_date = datetime.now(UTC)
