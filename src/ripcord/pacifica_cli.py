from __future__ import annotations

import json
from dataclasses import asdict

from .adapters.pacifica import PacificaConfig, build_snapshot_from_pacifica
from .engine import run_cycle
from .models import PolicyConfig


def main() -> None:
    pacifica_config = PacificaConfig.from_env()
    snapshot = build_snapshot_from_pacifica(pacifica_config)

    config = PolicyConfig(
        no_liquidation=True,
        max_daily_drawdown_pct=3.0,
        funding_negative_max_hours=6.0,
        max_effective_leverage=12.0,
        never_open_new_risk=True,
        hedge_enabled=True,
    )

    result = run_cycle(snapshot=snapshot, config=config, shock_pct=0.07)
    payload = {
        "data_source": pacifica_config.source,
        "account_id": pacifica_config.account_id,
        **{key: asdict(value) for key, value in result.items()},
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
