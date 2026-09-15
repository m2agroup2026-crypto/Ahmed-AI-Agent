from pathlib import Path


def load_knowledge(folder="knowledge"):
    knowledge = ""

    base_path = Path(folder)

    if not base_path.exists():
        return knowledge

    for file in base_path.rglob("*"):
        if file.is_file():
            try:
                content = file.read_text(encoding="utf-8")
                knowledge += f"\n\n--- {file.name} ---\n"
                knowledge += content
            except Exception:
                pass

    return knowledge
