from __future__ import annotations

from .models import AccountSnapshot, RiskReport


def _liquidation_distance_pct(mark_price: float, entry_price: float, side: str, leverage: float, mmr: float) -> float:
    leverage = max(leverage, 1.0)
    if side == "long":
        liq_price = entry_price * (1.0 - (1.0 / leverage) + mmr)
        return max((mark_price - liq_price) / max(mark_price, 1e-9), 0.0)
    liq_price = entry_price * (1.0 + (1.0 / leverage) - mmr)
    return max((liq_price - mark_price) / max(mark_price, 1e-9), 0.0)


def evaluate_account_risk(snapshot: AccountSnapshot) -> RiskReport:
    if not snapshot.positions:
        return RiskReport(
            score=0.0,
            level="LOW",
            liquidation_proximity=1.0,
            cross_contagion=0.0,
            funding_drag_hourly=0.0,
            symbol_contributions={},
            reasons=["No open positions"],
        )

    distances = {}
    raw_contrib = {}
    funding_drag = 0.0
    total_notional = 0.0

    for position in snapshot.positions:
        distance = _liquidation_distance_pct(
            mark_price=position.mark_price,
            entry_price=position.entry_price,
            side=position.side,
            leverage=position.leverage,
            mmr=snapshot.maintenance_margin_ratio,
        )
        distances[position.symbol] = min(distances.get(position.symbol, 1.0), distance)

        total_notional += position.notional
        raw_contrib[position.symbol] = raw_contrib.get(position.symbol, 0.0) + (
            position.notional * position.leverage / max(distance, 0.01)
        )

        direction = 1.0 if position.side == "long" else -1.0
        funding_cost = position.notional * position.funding_rate_hourly * direction
        if funding_cost > 0:
            funding_drag += funding_cost

    symbol_contributions = {
        symbol: (value / max(sum(raw_contrib.values()), 1e-9)) * 100.0
        for symbol, value in raw_contrib.items()
    }

    min_distance = min(distances.values())
    liquidation_proximity = 1.0 - min_distance

    cross_positions = [position for position in snapshot.positions if not position.isolated]
    cross_notional = sum(position.notional for position in cross_positions)
    top_cross_symbol_notional = 0.0
    if cross_positions:
        per_symbol = {}
        for position in cross_positions:
            per_symbol[position.symbol] = per_symbol.get(position.symbol, 0.0) + position.notional
        top_cross_symbol_notional = max(per_symbol.values())
    cross_contagion = top_cross_symbol_notional / max(cross_notional, 1e-9) if cross_notional else 0.0

    score = (
        min(liquidation_proximity * 60.0, 60.0)
        + min(cross_contagion * 25.0, 25.0)
        + min((funding_drag / max(snapshot.equity, 1e-9)) * 300.0, 15.0)
    )

    if score >= 75:
        level = "CRITICAL"
    elif score >= 50:
        level = "HIGH"
    elif score >= 25:
        level = "MEDIUM"
    else:
        level = "LOW"

    reasons = []
    if liquidation_proximity > 0.7:
        reasons.append("Liquidation proximity is elevated")
    if cross_contagion > 0.55:
        reasons.append("Cross-margin concentration is elevated")
    if funding_drag > snapshot.equity * 0.001:
        reasons.append("Funding drag is non-trivial")
    if not reasons:
        reasons.append("Risk levels are manageable")

    return RiskReport(
        score=round(score, 2),
        level=level,
        liquidation_proximity=round(liquidation_proximity, 4),
        cross_contagion=round(cross_contagion, 4),
        funding_drag_hourly=round(funding_drag, 6),
        symbol_contributions={k: round(v, 2) for k, v in symbol_contributions.items()},
        reasons=reasons,
    )
