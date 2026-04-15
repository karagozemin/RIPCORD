from __future__ import annotations

from dataclasses import replace

from .models import AccountSnapshot, ReplayResult, ScenarioOutcome


def _maintenance_requirement(snapshot: AccountSnapshot) -> float:
    return sum(position.notional for position in snapshot.positions) * snapshot.maintenance_margin_ratio


def _apply_market_shock(snapshot: AccountSnapshot, shock_pct: float) -> AccountSnapshot:
    mutable = replace(snapshot)
    mutable.positions = [replace(position) for position in snapshot.positions]

    pnl_delta = 0.0
    for position in mutable.positions:
        old_pnl = position.unrealized_pnl
        if position.side == "long":
            position.mark_price *= (1.0 - shock_pct)
        else:
            position.mark_price *= (1.0 + shock_pct)
        new_pnl = position.unrealized_pnl
        pnl_delta += (new_pnl - old_pnl)

    mutable.equity += pnl_delta
    return mutable


def run_replay(before: AccountSnapshot, after_rescue: AccountSnapshot, shock_pct: float = 0.06) -> ReplayResult:
    without_state = _apply_market_shock(before, shock_pct)
    with_state = _apply_market_shock(after_rescue, shock_pct)

    without_outcome = ScenarioOutcome(
        equity_before=before.equity,
        equity_after=without_state.equity,
        liquidated=without_state.equity <= _maintenance_requirement(without_state),
    )
    with_outcome = ScenarioOutcome(
        equity_before=after_rescue.equity,
        equity_after=with_state.equity,
        liquidated=with_state.equity <= _maintenance_requirement(with_state),
    )

    without_loss = without_outcome.equity_before - without_outcome.equity_after
    with_loss = with_outcome.equity_before - with_outcome.equity_after

    return ReplayResult(
        without_ripcord=without_outcome,
        with_ripcord=with_outcome,
        saved_loss=round(without_loss - with_loss, 4),
    )
