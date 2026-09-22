from app.database.connection import SessionLocal
from app.database.init_db import create_tables
from app.billing.repositories.wallet_repository import WalletRepository


def test_wallet_database_persistence():

    create_tables()

    db = SessionLocal()

    try:
        repo = WalletRepository(db=db)

        wallet = repo.get_wallet(900001)

        if wallet:
            db.delete(wallet)
            db.commit()

        wallet = repo.create_wallet(
            900001,
            500
        )

        assert wallet.user_id == 900001
        assert wallet.balance == 500
        assert wallet.total_used == 0

        wallet.consume_credits(50)

        repo.update(wallet)

    finally:
        db.close()

    db2 = SessionLocal()

    try:
        repo2 = WalletRepository(db=db2)

        persisted = repo2.get_wallet(
            900001
        )

        assert persisted is not None
        assert persisted.user_id == 900001
        assert persisted.balance == 450
        assert persisted.total_used == 50

    finally:
        db2.close()
