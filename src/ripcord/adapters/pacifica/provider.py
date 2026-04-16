from __future__ import annotations

import json
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol

from ...cli import build_sample_snapshot
from .config import PacificaConfig


class PacificaStateProvider(Protocol):
    def fetch_state(self) -> dict[str, Any]:
        ...


class MockPacificaProvider:
    def __init__(self, config: PacificaConfig) -> None:
        self.config = config

    def fetch_state(self) -> dict[str, Any]:
        if self.config.mock_file:
            raw = Path(self.config.mock_file).read_text(encoding="utf-8")
            return json.loads(raw)

        sample = build_sample_snapshot()
        return {
            "equity": sample.equity,
            "maintenance_margin_ratio": sample.maintenance_margin_ratio,
            "positions": [asdict(position) for position in sample.positions],
            "open_orders": [asdict(order) for order in sample.open_orders],
        }


class HttpPacificaProvider:
    def __init__(self, config: PacificaConfig) -> None:
        self.config = config

    def _request_json(self, path: str, account_query: str) -> dict[str, Any]:
        base = self.config.base_url.rstrip("/")
        endpoint = path if path.startswith("/") else f"/{path}"
        url = f"{base}{endpoint}?{account_query}"

        request = urllib.request.Request(url=url, method="GET")
        if self.config.api_key:
            request.add_header("Authorization", f"Bearer {self.config.api_key}")
        request.add_header("Accept", "application/json")

        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                payload = json.loads(body)
        except HTTPError as error:
            body = error.read().decode("utf-8") if error.fp else ""
            detail = body.strip() or str(error)
            raise ValueError(f"Pacifica API error ({error.code}) on {endpoint}: {detail}") from error

        if not isinstance(payload, dict):
            raise ValueError("Pacifica response must be a JSON object")
        return payload

    def fetch_state(self) -> dict[str, Any]:
        if not self.config.base_url:
            raise ValueError("PACIFICA_BASE_URL is required when RIPCORD_DATA_SOURCE=http")
        if not self.config.account_id:
            raise ValueError("PACIFICA_ACCOUNT_ID is required when RIPCORD_DATA_SOURCE=http")

        account_query = urllib.parse.urlencode({self.config.account_query_key: self.config.account_id})
        account_payload = self._request_json(self.config.state_path, account_query)
        positions_payload = self._request_json("/api/v1/positions", account_query)
        open_orders_payload = self._request_json(self.config.open_orders_path, account_query)

        return {
            "account": account_payload,
            "positions": positions_payload,
            "open_orders": open_orders_payload,
        }


def build_provider(config: PacificaConfig) -> PacificaStateProvider:
    source = config.source.lower().strip()
    if source == "http":
        return HttpPacificaProvider(config)
    return MockPacificaProvider(config)
