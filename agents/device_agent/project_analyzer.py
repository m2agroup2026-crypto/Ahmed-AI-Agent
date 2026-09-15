from pathlib import Path


def analyze_project(project_path):

    path = Path(project_path)

    result = {
        "name": path.name,
        "technologies": []
    }

    files = []

    for item in path.rglob("*"):
        if item.is_file():
            files.append(item.name.lower())


    if "manage.py" in files:
        result["technologies"].append("Django")

    if "requirements.txt" in files:
        result["technologies"].append("Python")

    if "package.json" in files:
        result["technologies"].append("React / Node.js")

    if "docker-compose.yml" in files or "docker-compose.yaml" in files:
        result["technologies"].append("Docker")

    if ".git" in [x.name for x in path.iterdir()]:
        result["technologies"].append("Git Repository")

    return result


def print_project_analysis(project_path):

    report = analyze_project(project_path)

    print("\n=== Ahmed AI Project Analysis v0.2 ===\n")

    print("Project:")
    print(report["name"])

    print("\nDetected Technologies:\n")

    if report["technologies"]:
        for tech in report["technologies"]:
            print(f"✓ {tech}")
    else:
        print("No technologies detected")
