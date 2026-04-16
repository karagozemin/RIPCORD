from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SessionRecord:
    session_id: str
    account_id: str
    expires_at: int


class SessionStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.db_path))

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                )
                """
            )
            connection.commit()

    def create(self, account_id: str, ttl_seconds: int) -> SessionRecord:
        now = int(time.time())
        expires_at = now + ttl_seconds
        session_id = secrets.token_urlsafe(24)

        with self._connect() as connection:
            connection.execute(
                "INSERT INTO sessions (session_id, account_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
                (session_id, account_id, expires_at, now),
            )
            connection.commit()

        return SessionRecord(session_id=session_id, account_id=account_id, expires_at=expires_at)

    def get(self, session_id: str) -> SessionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT session_id, account_id, expires_at FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()

        if not row:
            return None

        record = SessionRecord(session_id=row[0], account_id=row[1], expires_at=int(row[2]))
        if record.expires_at <= int(time.time()):
            self.delete(session_id)
            return None
        return record

    def delete(self, session_id: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            connection.commit()


class SessionSigner:
    def __init__(self, secret: str) -> None:
        self.secret = secret.encode("utf-8")

    def sign(self, session_id: str, expires_at: int) -> str:
        payload = {"sid": session_id, "exp": expires_at}
        payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
        signature = hmac.new(self.secret, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"{payload_b64}.{signature}"

    def verify(self, token: str) -> tuple[str, int]:
        if "." not in token:
            raise ValueError("Invalid session token")
        payload_b64, signature = token.split(".", 1)
        expected = hmac.new(self.secret, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("Invalid session signature")

        padding = "=" * (-len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes.decode("utf-8"))
        exp = int(payload["exp"])
        if exp <= int(time.time()):
            raise ValueError("Session expired")
        return str(payload["sid"]), exp


def build_session_store() -> SessionStore:
    root = Path(os.getenv("RIPCORD_STATE_DIR", ".ripcord_state"))
    db_path = root / "sessions.db"
    return SessionStore(db_path=db_path)


def build_session_signer() -> SessionSigner:
    secret = os.getenv("RIPCORD_SESSION_SECRET", "dev-insecure-session-secret")
    return SessionSigner(secret=secret)
