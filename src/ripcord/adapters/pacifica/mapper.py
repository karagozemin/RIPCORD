from __future__ import annotations

from ...models import AccountSnapshot, OpenOrder, Position


def map_state_to_snapshot(payload: dict) -> AccountSnapshot:
    equity = float(payload.get("equity", 0.0))
    maintenance_margin_ratio = float(payload.get("maintenance_margin_ratio", 0.005))

    positions = []
    for item in payload.get("positions", []):
        positions.append(
            Position(
                symbol=str(item["symbol"]),
                side=str(item["side"]),
                size=float(item["size"]),
                entry_price=float(item["entry_price"]),
                mark_price=float(item["mark_price"]),
                leverage=float(item["leverage"]),
                isolated=bool(item.get("isolated", False)),
                funding_rate_hourly=float(item.get("funding_rate_hourly", 0.0)),
                has_tpsl=bool(item.get("has_tpsl", False)),
            )
        )

    open_orders = []
    for item in payload.get("open_orders", []):
        open_orders.append(
            OpenOrder(
                symbol=str(item["symbol"]),
                side=str(item["side"]),
                size=float(item["size"]),
                reduce_only=bool(item.get("reduce_only", False)),
            )
        )

    return AccountSnapshot(
        equity=equity,
        maintenance_margin_ratio=maintenance_margin_ratio,
        positions=positions,
        open_orders=open_orders,
    )
