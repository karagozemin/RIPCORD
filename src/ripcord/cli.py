from __future__ import annotations

import json
from dataclasses import asdict

from .engine import run_cycle
from .models import AccountSnapshot, OpenOrder, PolicyConfig, Position


def build_sample_snapshot() -> AccountSnapshot:
    return AccountSnapshot(
        equity=10000.0,
        maintenance_margin_ratio=0.005,
        positions=[
            Position(
                symbol="BTC-PERP",
                side="long",
                size=0.8,
                entry_price=98000.0,
                mark_price=96500.0,
                leverage=20.0,
                isolated=False,
                funding_rate_hourly=0.00025,
                has_tpsl=False,
            ),
            Position(
                symbol="ETH-PERP",
                side="long",
                size=12.0,
                entry_price=3600.0,
                mark_price=3460.0,
                leverage=15.0,
                isolated=False,
                funding_rate_hourly=0.0002,
                has_tpsl=False,
            ),
            Position(
                symbol="SOL-PERP",
                side="short",
                size=180.0,
                entry_price=185.0,
                mark_price=191.0,
                leverage=12.0,
                isolated=True,
                funding_rate_hourly=0.00015,
                has_tpsl=True,
            ),
        ],
        open_orders=[
            OpenOrder(symbol="BTC-PERP", side="buy", size=0.2, reduce_only=False),
            OpenOrder(symbol="ETH-PERP", side="sell", size=2.0, reduce_only=True),
        ],
    )


def main() -> None:
    snapshot = build_sample_snapshot()
    config = PolicyConfig(
        no_liquidation=True,
        max_daily_drawdown_pct=3.0,
        funding_negative_max_hours=6.0,
        max_effective_leverage=12.0,
        never_open_new_risk=True,
        hedge_enabled=True,
    )

    result = run_cycle(snapshot=snapshot, config=config, shock_pct=0.07)
    payload = {key: asdict(value) for key, value in result.items()}
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
