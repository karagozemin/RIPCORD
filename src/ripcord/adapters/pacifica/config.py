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

    @classmethod
    def from_env(cls) -> "PacificaConfig":
        return cls(
            source=os.getenv("RIPCORD_DATA_SOURCE", "mock"),
            base_url=os.getenv("PACIFICA_BASE_URL", ""),
            account_id=os.getenv("PACIFICA_ACCOUNT_ID", ""),
            account_query_key=os.getenv("PACIFICA_ACCOUNT_QUERY_KEY", "account"),
            state_path=os.getenv("PACIFICA_STATE_PATH", "/account/state"),
            timeout_seconds=float(os.getenv("PACIFICA_TIMEOUT_SECONDS", "8")),
            api_key=os.getenv("PACIFICA_API_KEY", ""),
            mock_file=os.getenv("RIPCORD_MOCK_FILE", ""),
        )
