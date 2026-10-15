"""Focused auth regressions using disposable identities and in-memory SQLite."""

from datetime import UTC, datetime, timedelta
import logging
import secrets
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import JWTError, jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.auth.router import router
from app.database.base import Base
from app.database.dependencies import get_db
from app.models.user import User
from app.security import jwt as jwt_security
from app.security.password import hash_password
from app.services import auth_service


@pytest.fixture
def signing_config(monkeypatch):
    # Never use a configured or historical signing key for these tests.
    config = SimpleNamespace(SECRET_KEY=secrets.token_urlsafe(48), ALGORITHM="HS256")
    monkeypatch.setattr(jwt_security, "settings", config)
    return config


@pytest.fixture
def auth_client(signing_config):
    engine = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as db:
            password = secrets.token_urlsafe(24)
            users = [
                User(
                    name=name,
                    email=f"{name}@auth-security.example.com",
                    password_hash=hash_password(password),
                    is_active=active,
                )
                for name, active in (("active", True), ("inactive", False))
            ]
            db.add_all(users)
            db.commit()

            # Mount only auth routes; no external providers or unrelated routes.
            app = FastAPI()
            app.include_router(router)

            def override_db():
                yield db

            app.dependency_overrides[get_db] = override_db
            try:
                with TestClient(app) as client:
                    yield client, db, users, password
            finally:
                app.dependency_overrides.clear()
    finally:
        engine.dispose()


def bearer_headers(token):
    return {"Authorization": "Bearer " + token}


def test_active_login_preserves_response_and_me_identity(auth_client):
    client, _, users, password = auth_client
    response = client.post(
        "/auth/login", json={"email": users[0].email, "password": password}
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type"}
    assert body["token_type"] == "bearer"
    payload = jwt_security.verify_token(body["access_token"])
    assert payload is not None
    assert payload["user_id"] == users[0].id
    assert payload["exp"] > datetime.now(UTC).timestamp()
    identity = client.get("/auth/me", headers=bearer_headers(body["access_token"]))
    assert identity.status_code == 200
    assert identity.json() == {
        "id": users[0].id,
        "name": users[0].name,
        "email": users[0].email,
        "is_active": True,
    }


@pytest.mark.parametrize("correct_password, expected", [(True, 403), (False, 401)])
def test_inactive_login_never_issues_a_token(auth_client, monkeypatch, correct_password, expected):
    client, _, users, password = auth_client
    issued = []
    monkeypatch.setattr(auth_service, "create_access_token", lambda data: issued.append(data))
    response = client.post(
        "/auth/login",
        json={
            "email": users[1].email,
            "password": password if correct_password else secrets.token_urlsafe(24),
        },
    )
    assert response.status_code == expected
    assert "access_token" not in response.json()
    assert issued == []


def test_unknown_login_remains_unauthorized(auth_client):
    client, _, _, password = auth_client
    response = client.post(
        "/auth/login", json={"email": "missing@auth-security.example.com", "password": password}
    )
    assert response.status_code == 401
    assert "access_token" not in response.json()


@pytest.mark.parametrize("account_change, expected", [("delete", 401), ("disable", 403)])
def test_me_revalidates_account_after_token_issuance(auth_client, account_change, expected):
    client, db, users, _ = auth_client
    token = jwt_security.create_access_token({"user_id": users[0].id})
    if account_change == "delete":
        db.delete(users[0])
    else:
        users[0].is_active = False
    db.commit()
    response = client.get("/auth/me", headers=bearer_headers(token))
    assert response.status_code == expected
    assert "email" not in response.json()
    if expected == 401:
        assert response.headers["www-authenticate"] == "Bearer"


def test_me_requires_authentication(auth_client):
    client, _, _, _ = auth_client
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("token_case", ["expired", "missing_exp", "wrong_signature", "malformed"])
def test_me_rejects_invalid_tokens(auth_client, signing_config, token_case):
    client, _, users, _ = auth_client
    claims = {"user_id": users[0].id}
    key = signing_config.SECRET_KEY
    if token_case != "missing_exp":
        delta = timedelta(minutes=-1 if token_case == "expired" else 5)
        claims["exp"] = datetime.now(UTC) + delta
    if token_case == "wrong_signature":
        key = secrets.token_urlsafe(48)
    token = (
        "not-a-jwt"
        if token_case == "malformed"
        else jwt.encode(claims, key, algorithm=signing_config.ALGORITHM)
    )
    response = client.get("/auth/me", headers=bearer_headers(token))
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert "email" not in response.json()


@pytest.mark.parametrize("expiry_case", ["null", "bool", "string", "list", "object", "nan", "infinity"])
def test_exp_must_be_a_finite_numeric_date(signing_config, expiry_case):
    future = int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())
    expiries = {
        "null": None,
        "bool": True,
        "string": str(future),
        "list": [],
        "object": {},
        "nan": float("nan"),
        "infinity": float("inf"),
    }
    token = jwt.encode(
        {"user_id": 1, "exp": expiries[expiry_case]},
        signing_config.SECRET_KEY,
        algorithm=signing_config.ALGORITHM,
    )
    payload = jwt_security.verify_token(token)
    assert payload is None


@pytest.mark.parametrize("numeric_type", [int, float])
def test_valid_numeric_exp_is_accepted(signing_config, numeric_type):
    future = numeric_type((datetime.now(UTC) + timedelta(minutes=5)).timestamp())
    token = jwt.encode(
        {"user_id": 1, "exp": future},
        signing_config.SECRET_KEY,
        algorithm=signing_config.ALGORITHM,
    )
    payload = jwt_security.verify_token(token)
    assert payload is not None
    assert payload["user_id"] == 1


@pytest.mark.parametrize("error_type", [JWTError, RuntimeError])
def test_validation_errors_do_not_log_exception_details(signing_config, monkeypatch, caplog, capsys, error_type):
    def fail_decode(*args, **kwargs):
        raise error_type("synthetic internal validation details")

    monkeypatch.setattr(jwt_security.jwt, "decode", fail_decode)
    with caplog.at_level(logging.WARNING, logger=jwt_security.__name__):
        payload = jwt_security.verify_token("synthetic-token")
    assert payload is None
    messages = [record.getMessage() for record in caplog.records]
    assert messages == [
        "JWT validation failed"
        if error_type is JWTError
        else "JWT validation failed unexpectedly"
    ]
    assert all(record.exc_info is None for record in caplog.records)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "synthetic internal validation details" not in captured.err
