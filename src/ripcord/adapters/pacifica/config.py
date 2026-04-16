from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class PacificaConfig:
    source: str = "mock"
    base_url: str = ""
    account_id: str = ""
    account_query_key: str = "account"
    state_path: str = "/account/state"
    timeout_seconds: float = 8.0
    api_key: str = ""
    mock_file: str = ""
    open_orders_path: str = "/api/v1/open-orders"
    execution_enabled: bool = False
    execution_endpoint: str = ""
    agent_key: str = ""
    signing_secret: str = ""

    @classmethod
    def from_env(cls) -> "PacificaConfig":
        execution_enabled_raw = os.getenv("RIPCORD_EXECUTION_ENABLED", "false").lower().strip()
        return cls(
            source=os.getenv("RIPCORD_DATA_SOURCE", "mock"),
            base_url=os.getenv("PACIFICA_BASE_URL", ""),
            account_id=os.getenv("PACIFICA_ACCOUNT_ID", ""),
            account_query_key=os.getenv("PACIFICA_ACCOUNT_QUERY_KEY", "account"),
            state_path=os.getenv("PACIFICA_STATE_PATH", "/account/state"),
            timeout_seconds=float(os.getenv("PACIFICA_TIMEOUT_SECONDS", "8")),
            api_key=os.getenv("PACIFICA_API_KEY", ""),
            mock_file=os.getenv("RIPCORD_MOCK_FILE", ""),
            open_orders_path=os.getenv("PACIFICA_OPEN_ORDERS_PATH", "/api/v1/open-orders"),
            execution_enabled=execution_enabled_raw in {"1", "true", "yes", "on"},
            execution_endpoint=os.getenv("PACIFICA_EXECUTION_ENDPOINT", ""),
            agent_key=os.getenv("PACIFICA_AGENT_KEY", ""),
            signing_secret=os.getenv("RIPCORD_SIGNING_SECRET", ""),
        )
