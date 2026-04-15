import unittest

from ripcord.models import AccountSnapshot, OpenOrder, PolicyConfig, Position
from ripcord.policy import evaluate_policies
from ripcord.rescue import apply_plan, build_rescue_plan
from ripcord.risk import evaluate_account_risk


def build_snapshot() -> AccountSnapshot:
    return AccountSnapshot(
        equity=10000.0,
        maintenance_margin_ratio=0.005,
        positions=[
            Position(
                symbol="BTC-PERP",
                side="long",
                size=1.0,
                entry_price=102000.0,
                mark_price=98000.0,
                leverage=20.0,
                isolated=False,
                funding_rate_hourly=0.0003,
                has_tpsl=False,
            ),
            Position(
                symbol="ETH-PERP",
                side="long",
                size=14.0,
                entry_price=3700.0,
                mark_price=3480.0,
                leverage=14.0,
                isolated=False,
                funding_rate_hourly=0.0002,
                has_tpsl=False,
            ),
        ],
        open_orders=[
            OpenOrder(symbol="ETH-PERP", side="buy", size=1.0, reduce_only=False),
            OpenOrder(symbol="BTC-PERP", side="sell", size=0.2, reduce_only=True),
        ],
    )


class RescueExecutionTests(unittest.TestCase):
    def test_rescue_plan_contains_core_actions(self) -> None:
        snapshot = build_snapshot()
        risk = evaluate_account_risk(snapshot)
        policy = evaluate_policies(snapshot, risk, PolicyConfig())
        plan = build_rescue_plan(snapshot, policy, risk.level, risk.symbol_contributions, hedge_enabled=True)

        action_types = [action.action_type for action in plan.actions]
        self.assertIn("cancel_non_reduce_orders", action_types)
        self.assertIn("batch_reduce_only_exit", action_types)
        self.assertIn("attach_tpsl", action_types)


    def test_firewall_applies_reduction_and_tpsl(self) -> None:
        snapshot = build_snapshot()
        risk = evaluate_account_risk(snapshot)
        policy = evaluate_policies(snapshot, risk, PolicyConfig(never_open_new_risk=True, hedge_enabled=True))
        plan = build_rescue_plan(snapshot, policy, "CRITICAL", risk.symbol_contributions, hedge_enabled=True)
        result = apply_plan(snapshot, plan, policy)

        self.assertTrue(all(order.reduce_only for order in result.final_snapshot.open_orders))
        self.assertTrue(any("batch_reduce_only_exit" in item for item in result.applied_actions))
        self.assertTrue(all(position.has_tpsl for position in result.final_snapshot.positions if position.symbol in {"BTC-PERP", "ETH-PERP"}))
        self.assertIn("open_hedge", result.blocked_actions)


    if __name__ == "__main__":
        unittest.main()
