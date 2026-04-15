from __future__ import annotations

from .models import AccountSnapshot, PolicyConfig
from .policy import evaluate_policies
from .replay import run_replay
from .rescue import apply_plan, build_rescue_plan
from .risk import evaluate_account_risk


def run_cycle(snapshot: AccountSnapshot, config: PolicyConfig, shock_pct: float = 0.06) -> dict:
    risk = evaluate_account_risk(snapshot)
    policy_eval = evaluate_policies(snapshot=snapshot, risk=risk, config=config)
    plan = build_rescue_plan(
        snapshot=snapshot,
        policy_eval=policy_eval,
        risk_level=risk.level,
        symbol_contributions=risk.symbol_contributions,
        hedge_enabled=config.hedge_enabled,
    )
    execution = apply_plan(snapshot=snapshot, plan=plan, policy_eval=policy_eval)
    replay = run_replay(before=snapshot, after_rescue=execution.final_snapshot, shock_pct=shock_pct)

    return {
        "risk": risk,
        "policy": policy_eval,
        "plan": plan,
        "execution": execution,
        "replay": replay,
    }
