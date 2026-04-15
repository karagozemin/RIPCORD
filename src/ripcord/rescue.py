from __future__ import annotations

from dataclasses import replace
from typing import List

from .models import Action, AccountSnapshot, ExecutionResult, PolicyEvaluation, RescuePlan


def build_rescue_plan(snapshot: AccountSnapshot, policy_eval: PolicyEvaluation, risk_level: str, symbol_contributions: dict[str, float], hedge_enabled: bool) -> RescuePlan:
    actions: List[Action] = []
    rationale: List[str] = []

    has_non_reduce_orders = any(not order.reduce_only for order in snapshot.open_orders)
    if has_non_reduce_orders:
        actions.append(Action(action_type="cancel_non_reduce_orders", params={}))
        rationale.append("Canceling non-reduce-only orders lowers accidental risk expansion")

    top_symbols = [symbol for symbol, _ in sorted(symbol_contributions.items(), key=lambda item: item[1], reverse=True)[:2]]
    for symbol in top_symbols:
        actions.append(
            Action(
                action_type="batch_reduce_only_exit",
                params={"symbol": symbol, "fraction": 0.3},
            )
        )
    if top_symbols:
        rationale.append("Reducing top risk contributors cuts liquidation pressure quickly")

    for position in snapshot.positions:
        if not position.has_tpsl:
            actions.append(Action(action_type="attach_tpsl", params={"symbol": position.symbol}))
    if any(not position.has_tpsl for position in snapshot.positions):
        rationale.append("Attaching TP/SL prevents unmanaged downside tails")

    should_hedge = hedge_enabled and risk_level == "CRITICAL"
    if should_hedge and top_symbols:
        actions.append(Action(action_type="open_hedge", params={"symbol": top_symbols[0], "fraction": 0.2}))
        rationale.append("Temporary hedge dampens directional shock impact")

    estimated_risk_reduction = min(20.0 + len(actions) * 8.0, 75.0)
    return RescuePlan(actions=actions, rationale=rationale, estimated_risk_reduction_pct=estimated_risk_reduction)


def apply_plan(snapshot: AccountSnapshot, plan: RescuePlan, policy_eval: PolicyEvaluation) -> ExecutionResult:
    mutable = replace(snapshot)
    mutable.positions = [replace(position) for position in snapshot.positions]
    mutable.open_orders = [replace(order) for order in snapshot.open_orders]

    applied = []
    blocked = []

    for action in plan.actions:
        if action.action_type in policy_eval.blocked_actions:
            blocked.append(action.action_type)
            continue

        if action.action_type == "cancel_non_reduce_orders":
            mutable.open_orders = [order for order in mutable.open_orders if order.reduce_only]
            applied.append(action.action_type)
            continue

        if action.action_type == "batch_reduce_only_exit":
            symbol = str(action.params["symbol"])
            fraction = float(action.params["fraction"])
            for position in mutable.positions:
                if position.symbol == symbol:
                    position.size = max(position.size * (1.0 - fraction), 0.0)
            applied.append(f"{action.action_type}:{symbol}")
            continue

        if action.action_type == "attach_tpsl":
            symbol = str(action.params["symbol"])
            for position in mutable.positions:
                if position.symbol == symbol:
                    position.has_tpsl = True
            applied.append(f"{action.action_type}:{symbol}")
            continue

        if action.action_type == "open_hedge":
            symbol = str(action.params["symbol"])
            fraction = float(action.params["fraction"])
            target = None
            for position in mutable.positions:
                if position.symbol == symbol:
                    target = position
                    break
            if target:
                opposite = "short" if target.side == "long" else "long"
                hedge_size = max(target.size * fraction, 0.0)
                mutable.positions.append(
                    replace(
                        target,
                        side=opposite,
                        size=hedge_size,
                        leverage=min(target.leverage, 5.0),
                        isolated=True,
                        has_tpsl=True,
                    )
                )
                applied.append(f"{action.action_type}:{symbol}")
            continue

    return ExecutionResult(applied_actions=applied, blocked_actions=blocked, final_snapshot=mutable)
