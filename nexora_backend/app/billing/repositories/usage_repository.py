class UsageRepository:


    def __init__(self):

        self.usages = []


    def create(
        self,
        usage
    ):

        self.usages.append(
            usage
        )

        return usage


    def all(self):

        return self.usages
