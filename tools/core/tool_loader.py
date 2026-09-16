import importlib
import os


class ToolLoader:
    """
    Automatically discovers and loads tool definitions.
    """


    def __init__(self, tools_path="tools"):
        self.tools_path = tools_path


    def discover(self):

        definitions = []

        for root, dirs, files in os.walk(self.tools_path):

            for file in files:

                if file.endswith("_definition.py"):

                    module_path = (
                        root
                        .replace("/", ".")
                        .replace("\\", ".")
                        + "."
                        + file[:-3]
                    )

                    module = importlib.import_module(module_path)

                    for item in dir(module):

                        if item.endswith("_DEFINITION"):

                            definitions.append(
                                getattr(module, item)
                            )

        return definitions
