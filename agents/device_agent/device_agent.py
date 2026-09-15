from agents.device_agent.system_info import get_system_info
from agents.device_agent.project_scanner import scan_projects


def generate_device_report(project_path):
    system = get_system_info()
    projects = scan_projects(project_path)

    return {
        "device": system,
        "projects": projects
    }


def print_device_report(project_path):

    report = generate_device_report(project_path)

    print("\n===== Ahmed AI Device Agent v0.1 =====\n")

    print("Device Information:\n")

    for key, value in report["device"].items():
        print(f"{key}: {value}")

    print("\nProjects:\n")

    if report["projects"]:
        for project in report["projects"]:
            print(f"- {project}")
    else:
        print("No projects found")
