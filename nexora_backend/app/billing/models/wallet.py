from datetime import datetime, UTC

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Wallet(Base):
    __tablename__ = "billing_wallets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        unique=True,
        index=True,
        nullable=False
    )

    balance: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    total_used: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    def __init__(
        self,
        user_id: int,
        balance: int = 0
    ):
        self.user_id = user_id
        self.balance = balance
        self.total_used = 0
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def add_credits(
        self,
        amount: int
    ):
        self.balance += amount
        self.updated_at = datetime.now(UTC)

    def consume_credits(
        self,
        amount: int
    ):
        if amount > self.balance:
            raise ValueError(
                "Insufficient credits"
            )

        self.balance -= amount
        self.total_used += amount
        self.updated_at = datetime.now(UTC)
