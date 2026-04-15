from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Position:
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    leverage: float
    isolated: bool
    funding_rate_hourly: float
    has_tpsl: bool = False

    @property
    def notional(self) -> float:
        return abs(self.size * self.mark_price)

    @property
    def unrealized_pnl(self) -> float:
        if self.side == "long":
            return self.size * (self.mark_price - self.entry_price)
        return self.size * (self.entry_price - self.mark_price)


@dataclass
class OpenOrder:
    symbol: str
    side: str
    size: float
    reduce_only: bool


@dataclass
class AccountSnapshot:
    equity: float
    maintenance_margin_ratio: float
    positions: List[Position] = field(default_factory=list)
    open_orders: List[OpenOrder] = field(default_factory=list)


@dataclass
class RiskReport:
    score: float
    level: str
    liquidation_proximity: float
    cross_contagion: float
    funding_drag_hourly: float
    symbol_contributions: Dict[str, float]
    reasons: List[str]


@dataclass
class PolicyConfig:
    no_liquidation: bool = True
    max_daily_drawdown_pct: float = 3.0
    funding_negative_max_hours: float = 6.0
    max_effective_leverage: float = 12.0
    never_open_new_risk: bool = True
    hedge_enabled: bool = True


@dataclass
class PolicyEvaluation:
    violations: List[str]
    blocked_actions: List[str]


@dataclass
class Action:
    action_type: str
    params: Dict[str, float | str | bool]


@dataclass
class RescuePlan:
    actions: List[Action]
    rationale: List[str]
    estimated_risk_reduction_pct: float


@dataclass
class ExecutionResult:
    applied_actions: List[str]
    blocked_actions: List[str]
    final_snapshot: AccountSnapshot


@dataclass
class ScenarioOutcome:
    equity_before: float
    equity_after: float
    liquidated: bool


@dataclass
class ReplayResult:
    without_ripcord: ScenarioOutcome
    with_ripcord: ScenarioOutcome
    saved_loss: float
