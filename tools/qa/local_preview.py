"""Disposable local preview. Run with Python 3.14 from the repository root.

No existing database or signing material is read. A fresh temporary SQLite file
provides separate connections for concurrent browser/mobile requests. Credentials are written only
to the current user's temporary directory, never to the repository or browser bundle.
"""
import json
import argparse
import ipaddress
import os
from pathlib import Path
import secrets
import socket
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "nexora_backend"))
preview_directory = Path(tempfile.mkdtemp(prefix="aqlith-preview-db-"))
os.environ["DATABASE_URL"] = "sqlite:///" + (preview_directory / "disposable.sqlite").as_posix()
os.environ["SECRET_KEY"] = secrets.token_urlsafe(48)
for key in list(os.environ):
    if key.startswith(("AZURE_", "OPENAI_", "ACS_")):
        os.environ.pop(key)
os.environ["AZURE_FOUNDRY_ENDPOINT"] = "http://127.0.0.1:9/disabled"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api.auth.router import router as auth
from app.products.tutor.api import router as tutor
from app.products.tutor.api import get_tutor_gateway
from app.products.tutor.classroom.api import router as classroom
from app.products.tutor.live.api import router as live
from app.database.base import Base
from app.database.connection import engine, SessionLocal
from app.models.role import Role
from app.models.user import User
from app.security.password import hash_password

app = FastAPI(title="AQLITH disposable local preview")
for router in (auth, tutor, classroom, live):
    app.include_router(router)


def no_paid_gateway():
    raise HTTPException(503, "AI generation is disabled in the disposable local preview")


app.dependency_overrides[get_tutor_gateway] = no_paid_gateway


@app.get("/health")
def health():
    return {"status": "running", "database": "disposable-temporary-sqlite", "paid_services": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lan-host", help="Optional private LAN IPv4 address; never 0.0.0.0")
    args = parser.parse_args()
    hosts = ["127.0.0.1"]
    if args.lan_host:
        address = ipaddress.IPv4Address(args.lan_host)
        if not address.is_private or address.is_loopback or address.is_unspecified or address.is_link_local:
            parser.error("--lan-host must be a specific private LAN IPv4 address")
        hosts.append(str(address))
    # Expo web uses bearer authentication, never cookies. Only the explicit local
    # renderer origins are allowed, and this middleware exists in this test launcher only.
    app.add_middleware(CORSMiddleware,
        allow_origins=["http://localhost:8081", *[f"http://{host}:8081" for host in hosts]],
        allow_credentials=False, allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Accept"])
    Base.metadata.create_all(engine)
    accounts = {}
    with SessionLocal() as db:
        for name, role_name in (("teacher", "TEACHER"), ("student", "STUDENT"), ("outsider", "STUDENT")):
            role = db.query(Role).filter_by(name=role_name).first()
            if role is None:
                role = Role(name=role_name)
                db.add(role)
                db.flush()
            password = secrets.token_urlsafe(20)
            email = f"{name}@preview.example.com"
            db.add(User(name=f"Preview {name}", email=email,
                        password_hash=hash_password(password), role_id=role.id))
            accounts[name] = {"email": email, "password": password}
        db.commit()
    credentials = Path(tempfile.gettempdir()) / "aqlith-preview-accounts.json"
    credentials.write_text(json.dumps(accounts), encoding="utf-8")
    print(f"Disposable account credentials: {credentials}", flush=True)
    sockets = []
    try:
        for host in hosts:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.bind((host, 8000))
            listener.listen(128)
            sockets.append(listener)
        print("Preview API: " + ", ".join(f"http://{host}:8000" for host in hosts), flush=True)
        uvicorn.Server(uvicorn.Config(app, access_log=False)).run(sockets=sockets)
    finally:
        for listener in sockets:
            listener.close()
