from __future__ import annotations

from ...models import AccountSnapshot, OpenOrder, Position


def _normalize_side(raw_side: str) -> str:
    side = raw_side.lower().strip()
    if side in {"ask", "short", "sell"}:
        return "short"
    return "long"


def map_state_to_snapshot(payload: dict) -> AccountSnapshot:
    is_pacifica_envelope = "account" in payload and "positions" in payload

    if is_pacifica_envelope:
        account_block = payload.get("account", {})
        account_data = account_block.get("data", {}) if isinstance(account_block, dict) else {}
        equity = float(account_data.get("account_equity", account_data.get("balance", 0.0)))
        maintenance_margin_ratio = float(payload.get("maintenance_margin_ratio", 0.005))
        raw_positions = payload.get("positions", {}).get("data", [])
        raw_orders = payload.get("open_orders", {}).get("data", [])
    else:
        equity = float(payload.get("equity", 0.0))
        maintenance_margin_ratio = float(payload.get("maintenance_margin_ratio", 0.005))
        raw_positions = payload.get("positions", [])
        raw_orders = payload.get("open_orders", [])

    positions = []
    for item in raw_positions:
        side = _normalize_side(str(item.get("side", "long")))
        size = abs(float(item.get("size", item.get("amount", 0.0))))
        entry_price = float(item.get("entry_price", 0.0))
        mark_price = float(item.get("mark_price", entry_price))
        isolated = bool(item.get("isolated", False))

        leverage = float(item.get("leverage", 0.0))
        if leverage <= 0:
            margin_value = float(item.get("margin", 0.0))
            notional = size * max(entry_price, 0.0)
            leverage = (notional / margin_value) if margin_value > 0 else 5.0

        funding_rate_hourly = float(item.get("funding_rate_hourly", 0.0))
        if funding_rate_hourly == 0.0:
            funding_rate_hourly = 0.0

        positions.append(
            Position(
                symbol=str(item["symbol"]),
                side=side,
                size=size,
                entry_price=entry_price,
                mark_price=mark_price,
                leverage=leverage,
                isolated=isolated,
                funding_rate_hourly=funding_rate_hourly,
                has_tpsl=bool(item.get("has_tpsl", False)),
            )
        )

    open_orders = []
    for item in raw_orders:
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
