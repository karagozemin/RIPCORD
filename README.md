# RIPCORD Protocol

<p align="center">
  <img src="public/ripcord-logo.jpeg" alt="RIPCORD logo" width="220" />
</p>

RIPCORD is an MVP risk execution firewall for Pacifica-like perpetual trading environments. It monitors account risk and generates automated rescue plans before liquidation.

## Features

- Account Risk Twin: liquidation proximity, cross contagion, funding drag, symbol risk contribution
- Policy Firewall: `no_liquidation`, `max_daily_drawdown_pct`, `funding_negative_max_hours`, `never_open_new_risk`
- Rescue Engine: cancel non-reduce orders, reduce-only batch exits, TP/SL attach, optional hedge
- Counterfactual Replay: `with` vs `without RIPCORD`

## Quick Start

```bash
python3 -m pip install .
PYTHONPATH=src python3 -m ripcord.cli
PYTHONPATH=src python3 -m ripcord.pacifica_cli
PYTHONPATH=src python3 -m ripcord.web_server
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

After running `ripcord.web_server`, open `http://127.0.0.1:8787`.

## New Frontend (Vite + Solana Wallet Connect)

A React frontend is available under `frontend/`:

- Solana Wallet Adapter (Phantom/Solflare)

Run:

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://127.0.0.1:5173`

Run backend API in a separate terminal:

```bash
PYTHONPATH=src python3 -m ripcord.web_server
```

### Pre-submit Smoke Checklist

1. Start backend server and verify `https://ripcord-1.onrender.com`.
2. Start frontend with `npm run dev` and open `http://127.0.0.1:5173`.
3. Connect Solana wallet and enter Pacifica `account_id`.
4. Create session and confirm `Session ready` appears.
5. Click `Run Cycle` and verify Risk + Replay values render.
6. Toggle `Arm execution` + `Dry run` and re-run cycle once.

## Pacifica Adapter (RIP-01 baseline)

`ripcord.pacifica_cli` loads snapshots through the adapter layer and runs the same risk/rescue cycle.

1. Configure environment variables from `.env.example`.
2. Use `RIPCORD_DATA_SOURCE=mock` for mock payloads or `RIPCORD_DATA_SOURCE=http` for HTTP source.
3. Run:

```bash
set -a
source .env.example
set +a
PYTHONPATH=src python3 -m ripcord.pacifica_cli
```

To customize mock payload input, set `RIPCORD_MOCK_FILE` to your JSON file.

## Frontend Dashboard

The `frontend/` React dashboard pulls data from API endpoints and renders risk/policy/plan/replay blocks.

- Information architecture: `Overview`, `Risk Breakdown`, `Rescue`, `Replay`, `Policies`
- Live data flow: auto-refresh, loading/error/empty states, retry, stale indicator

- `GET /api/health`
- `POST /api/auth/session` (`account_id`) creates a session token
- `GET /api/auth/me` with `Authorization: Bearer <token>` or `X-RIPCORD-Session` returns active account
- `GET /api/run-cycle?mode=mock|adapter&shock_pct=0.07`
- `POST /api/run-cycle` with `mode`, `shock_pct`, optional `snapshot`, optional `policy`, optional `execution`

## Production User Flow

Short answer: **Yes**, users can open your site and view their own Pacifica account data.

Current MVP flow:

1. Frontend takes Pacifica account identity input.
2. `POST /api/auth/session` creates a session token.
3. In `adapter` mode, `run-cycle` uses session `account_id` to query Pacifica endpoints.
4. Users see their account risk/rescue/replay data in the dashboard.

Note: Wallet signature challenge (SIWE-like) is not implemented yet. The next hardening step is wallet signature verification.

## `/api/run-cycle` Contract (stable)

`contract_version: 2026-04-16`

Response body summary:

- `ok`: boolean
- `contract_version`: string
- `generated_at`: ISO datetime
- `mode`: `mock|adapter`
- `source`: `mock|adapter|custom`
- `shock_pct`: float
- `policy`: effective policy config
- `data`: `risk`, `policy`, `plan`, `execution`, `replay`
- `execution`: signed execution request preparation payload (`enabled`, `ready`, `missing`, `signed_request`)

For backward compatibility, `result` mirrors `data`.

## Execution Integration Preparation

Feature flags and signed request preparation are controlled via `.env`:

- `RIPCORD_EXECUTION_ENABLED=true|false`
- `PACIFICA_EXECUTION_ENDPOINT=https://...`
- `PACIFICA_AGENT_KEY=...`
- `RIPCORD_SIGNING_SECRET=...`
- `PACIFICA_OPEN_ORDERS_PATH=/api/v1/orders`
- `RIPCORD_REQUIRE_SESSION=true|false`
- `RIPCORD_SESSION_SECRET=...`
- `RIPCORD_SESSION_TTL_SECONDS=43200`
- `RIPCORD_STATE_DIR=.ripcord_state`

Execution control inside `POST /api/run-cycle`:

```json
{
  "mode": "adapter",
  "execution": {
    "arm": true,
    "dry_run": true
  }
}
```

- `arm=false` prevents live execution attempts.
- `dry_run=true` simulates signed execution only.

## CLI Output

CLI builds a sample account snapshot and runs these steps:

1. Evaluate risk
2. Evaluate policy violations
3. Build rescue plan
4. Apply firewall controls
5. Run replay `with/without`

## Notes

This phase includes the Pacifica adapter layer. `mock` is fully local; `http` pulls account state from your endpoint and feeds the same risk/rescue/replay engine.
