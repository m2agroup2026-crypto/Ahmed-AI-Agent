class MemoryRecall:
    """
    Retrieves relevant experiences from Ahmed AI memory.
    """


    def __init__(self, memory_store):

        self.memory_store = memory_store



    def recall(self, context):

        words = [
            word.lower()
            for word in context.split()
            if len(word) > 3
        ]


        results = []


        for word in words:

            matches = self.memory_store.search(word)

            results.extend(matches)


        unique_results = []

        seen = set()


        for item in results:

            key = (
                item["project"],
                item["task"]
            )

            if key not in seen:

                seen.add(key)
                unique_results.append(item)


        return unique_results
