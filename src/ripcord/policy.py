from __future__ import annotations

from .models import AccountSnapshot, PolicyConfig, PolicyEvaluation, RiskReport


def evaluate_policies(snapshot: AccountSnapshot, risk: RiskReport, config: PolicyConfig) -> PolicyEvaluation:
    violations = []
    blocked_actions = []

    effective_leverage = sum(p.notional for p in snapshot.positions) / max(snapshot.equity, 1e-9)

    if config.no_liquidation and risk.level in {"HIGH", "CRITICAL"} and risk.liquidation_proximity > 0.65:
        violations.append("no_liquidation")

    if effective_leverage > config.max_effective_leverage:
        violations.append("max_effective_leverage")

    funding_drag_pct_daily = (risk.funding_drag_hourly * 24.0 / max(snapshot.equity, 1e-9)) * 100.0
    if funding_drag_pct_daily > (config.max_daily_drawdown_pct / 2.0):
        violations.append("funding_negative_window")

    if config.never_open_new_risk:
        blocked_actions.append("open_hedge")

    return PolicyEvaluation(violations=sorted(set(violations)), blocked_actions=sorted(set(blocked_actions)))
