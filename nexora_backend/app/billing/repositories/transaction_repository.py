class TransactionRepository:


    def __init__(self):

        self.transactions = []


    def create(
        self,
        transaction
    ):

        self.transactions.append(
            transaction
        )

        return transaction


    def all(self):

        return self.transactions
