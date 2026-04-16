from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .adapters.pacifica import PacificaConfig, build_execution_preview, build_snapshot_from_pacifica, dispatch_execution
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


def _policy_from_payload(policy_payload: dict[str, Any] | None) -> PolicyConfig:
    base = _default_policy()
    if not policy_payload:
        return base

    return PolicyConfig(
        no_liquidation=bool(policy_payload.get("no_liquidation", base.no_liquidation)),
        max_daily_drawdown_pct=float(policy_payload.get("max_daily_drawdown_pct", base.max_daily_drawdown_pct)),
        funding_negative_max_hours=float(policy_payload.get("funding_negative_max_hours", base.funding_negative_max_hours)),
        max_effective_leverage=float(policy_payload.get("max_effective_leverage", base.max_effective_leverage)),
        never_open_new_risk=bool(policy_payload.get("never_open_new_risk", base.never_open_new_risk)),
        hedge_enabled=bool(policy_payload.get("hedge_enabled", base.hedge_enabled)),
    )


def _normalize_mode(mode: str) -> str:
    candidate = (mode or "mock").strip().lower()
    if candidate in {"adapter", "mock"}:
        return candidate
    raise ValueError("mode must be 'mock' or 'adapter'")


def run_cycle_payload(
    mode: str = "mock",
    snapshot_payload: dict[str, Any] | None = None,
    shock_pct: float = 0.07,
    policy_payload: dict[str, Any] | None = None,
    account_id: str | None = None,
    arm_execution: bool = False,
    execution_dry_run: bool = True,
) -> dict[str, Any]:
    normalized_mode = _normalize_mode(mode)
    if shock_pct <= 0 or shock_pct > 0.5:
        raise ValueError("shock_pct must be between 0 and 0.5")

    pacifica_config = PacificaConfig.from_env()
    if account_id:
        pacifica_config.account_id = account_id
    policy = _policy_from_payload(policy_payload)

    if snapshot_payload is not None:
        snapshot: AccountSnapshot = map_state_to_snapshot(snapshot_payload)
        source = "custom"
    elif normalized_mode == "adapter":
        snapshot = build_snapshot_from_pacifica(pacifica_config)
        source = "adapter"
    else:
        snapshot = build_sample_snapshot()
        source = "mock"

    result = run_cycle(snapshot=snapshot, config=policy, shock_pct=shock_pct)
    result_data = {key: asdict(value) for key, value in result.items()}
    action_payload = result_data.get("plan", {}).get("actions", [])
    execution_prep = build_execution_preview(actions=action_payload, config=pacifica_config)
    execution_dispatch = dispatch_execution(
        actions=action_payload,
        config=pacifica_config,
        arm=arm_execution,
        dry_run=execution_dry_run,
    )

    return {
        "ok": True,
        "contract_version": "2026-04-16",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": normalized_mode,
        "source": source,
        "shock_pct": shock_pct,
        "policy": asdict(policy),
        "data": result_data,
        "execution": {
            **execution_prep,
            "dispatch": execution_dispatch,
            "arm_requested": arm_execution,
            "dry_run": execution_dry_run,
        },
        "result": result_data,
    }
