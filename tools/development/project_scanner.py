import os


class ProjectScanner:
    """
    Scans a project directory and extracts basic structure information.
    """

    def __init__(self, project_path):
        self.project_path = project_path


    def scan(self):
        result = {
            "project_path": self.project_path,
            "files": [],
            "languages": set(),
            "directories": []
        }

        for root, dirs, files in os.walk(self.project_path):

            for directory in dirs:
                result["directories"].append(directory)


            for file in files:
                result["files"].append(file)

                extension = os.path.splitext(file)[1]

                if extension == ".py":
                    result["languages"].add("Python")

                elif extension in [".js", ".jsx"]:
                    result["languages"].add("JavaScript")

                elif extension == ".ts":
                    result["languages"].add("TypeScript")

                elif extension == ".java":
                    result["languages"].add("Java")

                elif extension in [".html", ".css"]:
                    result["languages"].add("Web")


        result["languages"] = list(result["languages"])

        return result
