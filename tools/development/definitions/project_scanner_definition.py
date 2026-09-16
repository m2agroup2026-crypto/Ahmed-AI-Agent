from tools.development.project_scanner import ProjectScanner


def project_scanner_tool(project_path="."):
    """
    Tool wrapper for project scanning.
    """

    scanner = ProjectScanner(project_path)

    return scanner.scan()


PROJECT_SCANNER_DEFINITION = {
    "name": "project_scanner",
    "category": "development",
    "description": "Analyze project structure and detect programming languages",
    "risk_level": "low",
    "requires_approval": False,
    "handler": project_scanner_tool
}
