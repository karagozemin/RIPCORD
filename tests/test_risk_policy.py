import unittest

from ripcord.models import AccountSnapshot, OpenOrder, PolicyConfig, Position
from ripcord.policy import evaluate_policies
from ripcord.risk import evaluate_account_risk


def build_snapshot() -> AccountSnapshot:
    return AccountSnapshot(
        equity=8000.0,
        maintenance_margin_ratio=0.005,
        positions=[
            Position(
                symbol="BTC-PERP",
                side="long",
                size=0.7,
                entry_price=100000.0,
                mark_price=96000.0,
                leverage=20.0,
                isolated=False,
                funding_rate_hourly=0.00025,
            ),
            Position(
                symbol="ETH-PERP",
                side="long",
                size=10.0,
                entry_price=3800.0,
                mark_price=3500.0,
                leverage=15.0,
                isolated=False,
                funding_rate_hourly=0.0002,
            ),
        ],
        open_orders=[OpenOrder(symbol="BTC-PERP", side="buy", size=0.1, reduce_only=False)],
    )


class RiskPolicyTests(unittest.TestCase):
    def test_risk_report_is_high_for_stressed_account(self) -> None:
        report = evaluate_account_risk(build_snapshot())
        self.assertIn(report.level, {"HIGH", "CRITICAL"})
        self.assertGreaterEqual(report.score, 50)
        self.assertGreater(report.liquidation_proximity, 0.6)


    def test_policy_blocks_open_hedge_when_never_open_new_risk_enabled(self) -> None:
        snapshot = build_snapshot()
        report = evaluate_account_risk(snapshot)
        cfg = PolicyConfig(never_open_new_risk=True, hedge_enabled=True)
        evaluation = evaluate_policies(snapshot=snapshot, risk=report, config=cfg)
        self.assertIn("open_hedge", evaluation.blocked_actions)


if __name__ == "__main__":
    unittest.main()
