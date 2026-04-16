from __future__ import annotations

import json
import urllib.parse
import urllib.request
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

    def fetch_state(self) -> dict[str, Any]:
        if not self.config.base_url:
            raise ValueError("PACIFICA_BASE_URL is required when RIPCORD_DATA_SOURCE=http")
        if not self.config.account_id:
            raise ValueError("PACIFICA_ACCOUNT_ID is required when RIPCORD_DATA_SOURCE=http")

        base = self.config.base_url.rstrip("/")
        path = self.config.state_path if self.config.state_path.startswith("/") else f"/{self.config.state_path}"
        query = urllib.parse.urlencode({"account_id": self.config.account_id})
        url = f"{base}{path}?{query}"

        request = urllib.request.Request(url=url, method="GET")
        if self.config.api_key:
            request.add_header("Authorization", f"Bearer {self.config.api_key}")
        request.add_header("Accept", "application/json")

        with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
            body = response.read().decode("utf-8")
            payload = json.loads(body)

        if not isinstance(payload, dict):
            raise ValueError("Pacifica state response must be a JSON object")
        return payload


def build_provider(config: PacificaConfig) -> PacificaStateProvider:
    source = config.source.lower().strip()
    if source == "http":
        return HttpPacificaProvider(config)
    return MockPacificaProvider(config)
