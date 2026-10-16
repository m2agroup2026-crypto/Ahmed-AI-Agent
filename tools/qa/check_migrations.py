"""Exercise the actual Alembic command chain in a new disposable directory only."""
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix="aqlith-migrations-") as directory:
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite:///" + (Path(directory) / "disposable.sqlite").as_posix()
    env["SECRET_KEY"] = secrets.token_urlsafe(48)
    for args in (("upgrade", "head"), ("downgrade", "base"), ("upgrade", "head")):
        subprocess.run([sys.executable, "-m", "alembic", *args],
                       cwd=root / "nexora_backend", env=env, check=True)
    print("PASS: disposable Alembic upgrade head / downgrade base / upgrade head")
