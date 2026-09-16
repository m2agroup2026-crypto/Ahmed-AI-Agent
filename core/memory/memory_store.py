class MemoryStore:
    """
    Stores and manages Ahmed AI experiences.
    """

    def __init__(self):
        self.memories = []


    def add(self, experience):

        self.memories.append(experience)


    def all(self):

        return [
            memory.summarize()
            for memory in self.memories
        ]


    def search(self, keyword):

        keyword = keyword.lower()

        results = []

        for memory in self.memories:

            data = memory.summarize()

            searchable_text = " ".join([
                str(data["project"]),
                str(data["task"]),
                str(data["decision"]),
                str(data["lesson"]),
                " ".join(data["tags"])
            ]).lower()


            if keyword in searchable_text:
                results.append(data)


        return results
