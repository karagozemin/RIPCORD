from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .web_api import run_cycle_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = PROJECT_ROOT / "web"


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

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._write_json(HTTPStatus.OK, {"ok": True, "service": "ripcord-web"})
            return

        if parsed.path == "/api/run-cycle":
            query = parse_qs(parsed.query)
            mode = query.get("mode", ["mock"])[0]
            try:
                payload = run_cycle_payload(mode=mode)
            except Exception as error:
                self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                return
            self._write_json(HTTPStatus.OK, payload)
            return

        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/run-cycle":
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b"{}"
            data = json.loads(raw.decode("utf-8"))
            mode = data.get("mode", "mock")
            snapshot_payload = data.get("snapshot")
            shock_pct = float(data.get("shock_pct", 0.07))
            payload = run_cycle_payload(mode=mode, snapshot_payload=snapshot_payload, shock_pct=shock_pct)
        except Exception as error:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        self._write_json(HTTPStatus.OK, payload)


def main() -> None:
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
