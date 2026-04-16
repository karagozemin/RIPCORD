from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .auth import build_session_signer, build_session_store
from .web_api import run_cycle_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_STATIC_DIR = PROJECT_ROOT / "web"
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
STATIC_DIR = FRONTEND_DIST_DIR if FRONTEND_DIST_DIR.exists() else LEGACY_STATIC_DIR
SESSION_TTL_SECONDS = int(os.getenv("RIPCORD_SESSION_TTL_SECONDS", "43200"))
REQUIRE_SESSION = os.getenv("RIPCORD_REQUIRE_SESSION", "false").lower().strip() in {"1", "true", "yes", "on"}
SESSION_STORE = build_session_store()
SESSION_SIGNER = build_session_signer()


def _validate_startup_config() -> None:
    if REQUIRE_SESSION:
        session_secret = os.getenv("RIPCORD_SESSION_SECRET", "")
        if not session_secret or session_secret == "dev-insecure-session-secret":
            raise ValueError("RIPCORD_SESSION_SECRET must be set to a strong value when RIPCORD_REQUIRE_SESSION=true")

    execution_enabled = os.getenv("RIPCORD_EXECUTION_ENABLED", "false").lower().strip() in {"1", "true", "yes", "on"}
    if execution_enabled and not os.getenv("RIPCORD_SIGNING_SECRET", ""):
        raise ValueError("RIPCORD_SIGNING_SECRET is required when RIPCORD_EXECUTION_ENABLED=true")


class RipcordHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error_payload(self, message: str, status: int) -> dict:
        return {
            "ok": False,
            "error": {
                "message": message,
                "status": status,
            },
        }

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _extract_session_token(self) -> str | None:
        header_token = self.headers.get("X-RIPCORD-Session")
        if header_token:
            return header_token
        auth_header = self.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            return auth_header.split(" ", 1)[1].strip()
        return None

    def _resolve_account_from_session(self) -> str | None:
        token = self._extract_session_token()
        if not token:
            return None
        session_id, _ = SESSION_SIGNER.verify(token)
        record = SESSION_STORE.get(session_id)
        if not record:
            raise ValueError("Session not found or expired")
        return record.account_id

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._write_json(HTTPStatus.OK, {"ok": True, "service": "ripcord-web"})
            return

        if parsed.path == "/api/auth/me":
            try:
                account_id = self._resolve_account_from_session()
                if not account_id:
                    self._write_json(HTTPStatus.UNAUTHORIZED, self._error_payload("No active session", HTTPStatus.UNAUTHORIZED))
                    return
                self._write_json(HTTPStatus.OK, {"ok": True, "account_id": account_id})
                return
            except Exception as error:
                self._write_json(HTTPStatus.UNAUTHORIZED, self._error_payload(str(error), HTTPStatus.UNAUTHORIZED))
                return

        if parsed.path == "/api/run-cycle":
            query = parse_qs(parsed.query)
            mode = query.get("mode", ["mock"])[0]
            shock_pct = float(query.get("shock_pct", ["0.07"])[0])
            try:
                account_id = self._resolve_account_from_session()
                if REQUIRE_SESSION and mode == "adapter" and not account_id:
                    self._write_json(HTTPStatus.UNAUTHORIZED, self._error_payload("Session required for adapter mode", HTTPStatus.UNAUTHORIZED))
                    return
                payload = run_cycle_payload(mode=mode, shock_pct=shock_pct, account_id=account_id)
            except Exception as error:
                self._write_json(HTTPStatus.BAD_REQUEST, self._error_payload(str(error), HTTPStatus.BAD_REQUEST))
                return
            self._write_json(HTTPStatus.OK, payload)
            return

        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/auth/session":
            try:
                data = self._read_json()
                account_id = str(data.get("account_id", "")).strip()
                if not account_id:
                    raise ValueError("account_id is required")
                record = SESSION_STORE.create(account_id=account_id, ttl_seconds=SESSION_TTL_SECONDS)
                token = SESSION_SIGNER.sign(session_id=record.session_id, expires_at=record.expires_at)
                self._write_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "account_id": account_id,
                        "token": token,
                        "expires_at": record.expires_at,
                    },
                )
                return
            except Exception as error:
                self._write_json(HTTPStatus.BAD_REQUEST, self._error_payload(str(error), HTTPStatus.BAD_REQUEST))
                return

        if parsed.path != "/api/run-cycle":
            self._write_json(HTTPStatus.NOT_FOUND, self._error_payload("Endpoint not found", HTTPStatus.NOT_FOUND))
            return

        try:
            data = self._read_json()
            mode = data.get("mode", "mock")
            snapshot_payload = data.get("snapshot")
            policy_payload = data.get("policy")
            shock_pct = float(data.get("shock_pct", 0.07))
            execution_payload = data.get("execution", {})
            arm_execution = bool(execution_payload.get("arm", False))
            execution_dry_run = bool(execution_payload.get("dry_run", True))

            account_id = self._resolve_account_from_session()
            if REQUIRE_SESSION and mode == "adapter" and not account_id:
                self._write_json(HTTPStatus.UNAUTHORIZED, self._error_payload("Session required for adapter mode", HTTPStatus.UNAUTHORIZED))
                return

            payload = run_cycle_payload(
                mode=mode,
                snapshot_payload=snapshot_payload,
                shock_pct=shock_pct,
                policy_payload=policy_payload,
                account_id=account_id,
                arm_execution=arm_execution,
                execution_dry_run=execution_dry_run,
            )
        except Exception as error:
            self._write_json(HTTPStatus.BAD_REQUEST, self._error_payload(str(error), HTTPStatus.BAD_REQUEST))
            return

        self._write_json(HTTPStatus.OK, payload)


def main() -> None:
    _validate_startup_config()
    host = "127.0.0.1"
    port = 8787
    server = ThreadingHTTPServer((host, port), RipcordHTTPRequestHandler)
    print(f"RIPCORD web server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
