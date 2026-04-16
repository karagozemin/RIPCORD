from __future__ import annotations

from ...models import AccountSnapshot
from .config import PacificaConfig
from .mapper import map_state_to_snapshot
from .provider import build_provider


def build_snapshot_from_pacifica(config: PacificaConfig | None = None) -> AccountSnapshot:
    cfg = config or PacificaConfig.from_env()
    provider = build_provider(cfg)
    payload = provider.fetch_state()
    return map_state_to_snapshot(payload)
