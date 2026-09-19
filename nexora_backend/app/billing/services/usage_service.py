class UsageService:


    def create_usage_record(
        self,
        user_id,
        action,
        credits
    ):

        return {
            "user_id": user_id,
            "action": action,
            "credits": credits
        }
