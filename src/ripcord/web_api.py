from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .adapters.pacifica import PacificaConfig, build_snapshot_from_pacifica
from .adapters.pacifica.mapper import map_state_to_snapshot
from .cli import build_sample_snapshot
from .engine import run_cycle
from .models import AccountSnapshot, PolicyConfig


def _default_policy() -> PolicyConfig:
    return PolicyConfig(
        no_liquidation=True,
        max_daily_drawdown_pct=3.0,
        funding_negative_max_hours=6.0,
        max_effective_leverage=12.0,
        never_open_new_risk=True,
        hedge_enabled=True,
    )


def run_cycle_payload(
    mode: str = "mock",
    snapshot_payload: dict[str, Any] | None = None,
    shock_pct: float = 0.07,
) -> dict[str, Any]:
    if snapshot_payload is not None:
        snapshot: AccountSnapshot = map_state_to_snapshot(snapshot_payload)
        source = "custom"
    elif mode == "adapter":
        snapshot = build_snapshot_from_pacifica(PacificaConfig.from_env())
        source = "adapter"
    else:
        snapshot = build_sample_snapshot()
        source = "mock"

    result = run_cycle(snapshot=snapshot, config=_default_policy(), shock_pct=shock_pct)

    return {
        "source": source,
        "shock_pct": shock_pct,
        "result": {key: asdict(value) for key, value in result.items()},
    }
