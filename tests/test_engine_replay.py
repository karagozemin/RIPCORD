import unittest

from ripcord.engine import run_cycle
from ripcord.models import AccountSnapshot, OpenOrder, PolicyConfig, Position


def build_snapshot() -> AccountSnapshot:
    return AccountSnapshot(
        equity=9000.0,
        maintenance_margin_ratio=0.005,
        positions=[
            Position(
                symbol="BTC-PERP",
                side="long",
                size=0.9,
                entry_price=99000.0,
                mark_price=96000.0,
                leverage=18.0,
                isolated=False,
                funding_rate_hourly=0.00025,
                has_tpsl=False,
            ),
            Position(
                symbol="SOL-PERP",
                side="long",
                size=220.0,
                entry_price=188.0,
                mark_price=181.0,
                leverage=12.0,
                isolated=False,
                funding_rate_hourly=0.0002,
                has_tpsl=False,
            ),
        ],
        open_orders=[OpenOrder(symbol="BTC-PERP", side="buy", size=0.15, reduce_only=False)],
    )


class EngineReplayTests(unittest.TestCase):
    def test_run_cycle_produces_positive_saved_loss_on_shock(self) -> None:
        config = PolicyConfig(never_open_new_risk=True, hedge_enabled=True)
        result = run_cycle(snapshot=build_snapshot(), config=config, shock_pct=0.08)
        replay = result["replay"]

        self.assertGreater(replay.saved_loss, 0)
        self.assertGreaterEqual(replay.with_ripcord.equity_after, replay.without_ripcord.equity_after)


    if __name__ == "__main__":
        unittest.main()
