from app.database.base import Base
from app.database.connection import engine

from app.models import (
    User,
    Role,
    Permission,
    RolePermission,
)

# Register billing models with SQLAlchemy metadata
from app.billing.models import (
    Plan,
    Subscription,
    CreditTransaction,
    UsageRecord,
    Wallet,
)


def create_tables():
    Base.metadata.create_all(
        bind=engine
    )


if __name__ == "__main__":
    create_tables()
