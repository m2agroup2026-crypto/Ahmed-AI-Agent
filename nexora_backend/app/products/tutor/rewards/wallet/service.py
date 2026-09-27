from .account import StudentWallet


class NexoraWalletService:


    def create_wallet(
        self,
        student_id: int,
    ):

        return StudentWallet(
            student_id=student_id
        )


    def add_xp(
        self,
        wallet: StudentWallet,
        amount: int,
    ):

        wallet.xp += amount

        return wallet
