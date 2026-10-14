"""Signing startup and database guards without configured or historical secrets."""

import os
from pathlib import Path
import secrets
import subprocess
import sys
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine

from app.config import settings as signing
from app.tests.conftest import require_isolated_database_url


@pytest.mark.parametrize("key", [None, "", " \t\n", "short-test-key", "x" * 64, "default" * 12])
def test_invalid_signing_keys_are_rejected(key):
    with pytest.raises(RuntimeError, match="SECRET_KEY must be explicitly supplied"):
        signing._validate_signing_key(key)


def test_whitespace_is_not_silently_removed():
    with pytest.raises(RuntimeError, match="SECRET_KEY must be explicitly supplied"):
        signing._validate_signing_key(" " + secrets.token_urlsafe(48))


def test_retired_fingerprint_is_rejected_without_retired_material(monkeypatch):
    monkeypatch.setattr(
        signing.hashlib, "sha256",
        lambda value: SimpleNamespace(hexdigest=lambda: signing._UNSAFE_KEY_DIGEST),
    )
    with pytest.raises(RuntimeError, match="SECRET_KEY must be explicitly supplied"):
        signing._validate_signing_key(secrets.token_urlsafe(48))


def test_runtime_key_is_preserved_across_instances(monkeypatch):
    key = secrets.token_urlsafe(48)
    monkeypatch.setenv("SECRET_KEY", key)
    first = signing.Settings()
    second = signing.Settings()
    unchanged = first.SECRET_KEY == second.SECRET_KEY == key
    assert unchanged
    assert first.ALGORITHM == second.ALGORITHM == "HS256"


@pytest.mark.parametrize("case", ["missing", "empty", "blank", "short", "repeated", "retired_fingerprint", "valid"])
def test_application_startup_fails_closed(case):
    # Build a small child environment; never inherit real credentials.
    env = {"DATABASE_URL": "sqlite://", "PYTHONDONTWRITEBYTECODE": "1"}
    if os.name == "nt":
        for name in ("SystemRoot", "WINDIR"):
            if name in os.environ:
                env[name] = os.environ[name]
    if case == "empty":
        env["SECRET_KEY"] = ""
    elif case == "blank":
        env["SECRET_KEY"] = " \t "
    elif case == "short":
        env["SECRET_KEY"] = "short-test-key"
    elif case == "repeated":
        env["SECRET_KEY"] = "x" * 64
    elif case in {"valid", "retired_fingerprint"}:
        env["SECRET_KEY"] = secrets.token_urlsafe(48)
    code = "from app.main import app; print('STARTUP_OK')"
    if case == "retired_fingerprint":
        # Exercise the fingerprint rejection path with a fresh random key.
        code = (
            "import hashlib; from types import SimpleNamespace; "
            "hashlib.sha256 = lambda value: SimpleNamespace(hexdigest=lambda: "
            + repr(signing._UNSAFE_KEY_DIGEST) + "); " + code
        )
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=Path(__file__).resolve().parents[2],
        env=env, capture_output=True, text=True, timeout=30,
    )
    succeeded = result.returncode == 0
    assert succeeded == (case == "valid")
    if case == "valid":
        assert result.stdout.strip() == "STARTUP_OK"
    else:
        assert "SECRET_KEY must be explicitly supplied" in result.stderr


@pytest.mark.parametrize("url", ["sqlite:///./nexora.db", "sqlite:///existing.sqlite3", "postgresql://localhost/production"])
def test_database_configuration_guard_rejects_persistent_targets(url):
    with pytest.raises(pytest.UsageError):
        require_isolated_database_url(url)


@pytest.mark.parametrize("existing", [False, True])
def test_connection_guard_prevents_persistent_database_access(tmp_path, existing):
    target = tmp_path / "disposable_sentinel.sqlite3"
    if existing:
        target.write_bytes(b"Disposable test sentinel")
    engine = create_engine("sqlite:///" + target.as_posix())
    try:
        with pytest.raises(pytest.UsageError):
            engine.connect()
        if existing:
            assert target.read_bytes() == b"Disposable test sentinel"
        else:
            assert not target.exists()
    finally:
        engine.dispose()
