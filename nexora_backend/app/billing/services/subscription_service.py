from app.billing.models.subscription import Subscription
from app.billing.repositories.subscription_repository import SubscriptionRepository


class SubscriptionService:


    def __init__(
        self,
        repository=None
    ):

        self.repository = repository or SubscriptionRepository()



    def create_subscription(
        self,
        user_id: int,
        plan_id: int
    ):

        subscription = Subscription(
            user_id,
            plan_id
        )

        return self.repository.create(
            subscription
        )



    def get_subscription(
        self,
        user_id: int
    ):

        return self.repository.get(
            user_id
        )



    def cancel_subscription(
        self,
        user_id: int
    ):

        subscription = self.get_subscription(
            user_id
        )

        if subscription:

            subscription.cancel()

            self.repository.update(
                subscription
            )

        return subscription
