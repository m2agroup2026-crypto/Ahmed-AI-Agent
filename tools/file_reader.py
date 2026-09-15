from pathlib import Path

def read_file(path: str):
    file_path = Path(path)

    if not file_path.exists():
        return f"File not found: {path}"

    try:
        content = file_path.read_text(encoding="utf-8")
        return content
    except Exception as e:
        return f"Error reading file: {e}"
