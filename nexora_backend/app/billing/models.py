from datetime import datetime


class Plan:

    def __init__(
        self,
        name,
        currency,
        price,
        credits_limit
    ):
        self.name = name
        self.currency = currency
        self.price = price
        self.credits_limit = credits_limit
        self.created_at = datetime.utcnow()


class Subscription:

    def __init__(
        self,
        user_id,
        plan_id,
        status="active"
    ):
        self.user_id = user_id
        self.plan_id = plan_id
        self.status = status
        self.created_at = datetime.utcnow()


class CreditWallet:

    def __init__(
        self,
        user_id,
        balance=0
    ):
        self.user_id = user_id
        self.balance = balance
        self.total_used = 0


class UsageRecord:

    def __init__(
        self,
        user_id,
        action,
        credits
    ):
        self.user_id = user_id
        self.action = action
        self.credits = credits
        self.created_at = datetime.utcnow()
