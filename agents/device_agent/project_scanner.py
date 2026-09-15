from pathlib import Path


PROJECT_KEYWORDS = [
    "git",
    "package.json",
    "manage.py",
    "requirements.txt",
    "docker-compose.yml",
    "docker-compose.yaml"
]


def is_project(folder: Path):
    try:
        files = {f.name.lower() for f in folder.iterdir()}

        for keyword in PROJECT_KEYWORDS:
            if keyword in files:
                return True

    except PermissionError:
        pass

    return False


def scan_projects(root_path):
    root = Path(root_path)
    projects = []

    if not root.exists():
        return projects

    for item in root.iterdir():
        if item.is_dir() and is_project(item):
            projects.append(item.name)

    return projects


def print_projects(root_path):
    projects = scan_projects(root_path)

    print("\n=== Ahmed AI Project Scanner ===\n")

    if not projects:
        print("No projects found")
        return

    for project in projects:
        print(f"- {project}")
