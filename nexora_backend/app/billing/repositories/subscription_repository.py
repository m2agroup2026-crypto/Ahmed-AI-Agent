class SubscriptionRepository:


    def __init__(self):

        self.subscriptions = {}



    def create(
        self,
        subscription
    ):

        self.subscriptions[
            subscription.user_id
        ] = subscription

        return subscription



    def get(
        self,
        user_id: int
    ):

        return self.subscriptions.get(
            user_id
        )



    def update(
        self,
        subscription
    ):

        self.subscriptions[
            subscription.user_id
        ] = subscription

        return subscription
