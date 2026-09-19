class GovernanceReport:


    def generate(
        self,
        activities
    ):

        total = len(activities)

        approved = len(
            [
                a for a in activities
                if a.status == "approved"
            ]
        )

        rejected = total - approved


        return {
            "total_actions": total,
            "approved": approved,
            "rejected": rejected
        }
