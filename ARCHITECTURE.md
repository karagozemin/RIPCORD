# RIPCORD Architecture

## 1. Purpose and Scope

RIPCORD is a risk-execution firewall for perpetual trading environments. It continuously evaluates account risk, applies policy constraints, generates rescue actions, and provides counterfactual replay (`with` vs `without` rescue) to support safe operational decisions.

This document covers:

- Runtime architecture (frontend, backend, adapter, engine)
- Request lifecycle and data contracts
- Security boundaries and trust model
- Deployment topology (Vercel + Render)
- Operational guidance and future hardening

## 2. High-Level System Topology

```text
+---------------------+             +------------------------------+
| Browser (User)      |  HTTPS      | Vercel (Frontend Hosting)    |
| React App           +-----------> | Vite static build            |
| Session token store |             | Rewrite /api/* -> Render API |
+----------+----------+             +---------------+--------------+
           |                                          |
           | /api/* (same origin from browser)        | HTTPS
           |                                          v
+----------v------------------------------------------+----------------+
| Render Web Service (Python)                                          |
| `ripcord.web_server`                                                  |
| - API endpoints                                                       |
| - Session signer/store                                                |
| - Adapter mode (Pacifica HTTP)                                        |
| - Mock mode (local sample payload)                                    |
| - Risk/Policy/Rescue/Replay engine                                    |
+---------------------+---------------------------+---------------------+
                      |                           |
                      | Pacifica HTTP API         | Local fallback/mock
                      v                           v
            +---------+-----------+      +--------+------------------+
            | Pacifica test API   |      | Embedded sample/mock data |
            | account/positions   |      | examples + CLI builders   |
            | open-orders/orders  |      +---------------------------+
            +---------------------+
```

## 3. Core Components

### 3.1 Frontend (`frontend/`)

- Built with React + Vite.
- Main flow: connect account context, create session, configure policy/execution flags, run cycle, display result payload.
- Calls backend through relative paths (`/api/...`) to keep browser-side integration simple.
- In production, Vercel rewrites `/api/*` to Render backend.

Key files:

- `frontend/src/App.jsx`
- `frontend/src/components/*`
- `frontend/vercel.json`

### 3.2 Web API Server (`src/ripcord/web_server.py`)

- Python `ThreadingHTTPServer` serves both static assets and REST-like JSON endpoints.
- Supports deploy-friendly binding:
  - `RIPCORD_HOST` (default `0.0.0.0`)
  - `PORT` or `RIPCORD_PORT` (default `8787`)
- Handles session token extraction from:
  - `Authorization: Bearer <token>`
  - `X-RIPCORD-Session`

Primary endpoints:

- `GET /api/health`
- `POST /api/auth/session`
- `GET /api/auth/me`
- `GET /api/run-cycle`
- `POST /api/run-cycle`

### 3.3 Orchestration Layer (`src/ripcord/web_api.py`)

`run_cycle_payload(...)` is the orchestration entrypoint. It:

1. Normalizes mode (`mock` or `adapter`)
2. Builds effective policy from defaults + user payload
3. Resolves account snapshot source:
   - `custom` from request payload
   - `adapter` from Pacifica
   - `mock` from sample snapshot
4. Runs core engine
5. Builds execution preview and dispatch metadata
6. Returns stable contract payload (`contract_version: 2026-04-16`)

### 3.4 Core Engine (`src/ripcord/engine.py`)

Pipeline order:

1. `evaluate_account_risk`
2. `evaluate_policies`
3. `build_rescue_plan`
4. `apply_plan`
5. `run_replay`

Outputs:

- `risk`
- `policy`
- `plan`
- `execution`
- `replay`

### 3.5 Pacifica Adapter (`src/ripcord/adapters/pacifica/`)

Responsibilities:

- Load configuration from environment
- Fetch account/positions/open-orders through HTTP provider
- Map external payloads into internal `AccountSnapshot`

Important endpoint configuration:

- `PACIFICA_STATE_PATH` (e.g. `/api/v1/account`)
- positions path is currently fixed at `/api/v1/positions`
- `PACIFICA_OPEN_ORDERS_PATH` (production-verified path: `/api/v1/orders`)

## 4. Request and Data Flow

### 4.1 Session Creation

1. Frontend sends `POST /api/auth/session` with `account_id`.
2. Backend creates short-lived session record and signs token.
3. Frontend stores token and uses it on subsequent calls.

### 4.2 Run Cycle (Adapter Mode)

1. Frontend calls `POST /api/run-cycle` with `mode="adapter"` and options.
2. Backend resolves session account id.
3. Adapter queries Pacifica endpoints.
4. Mapper converts payload to internal model.
5. Engine computes risk/policy/plan/execution/replay.
6. API returns unified JSON for dashboard rendering.

### 4.3 Run Cycle (Mock Mode)

Same API contract as adapter mode, but snapshot comes from local sample data. This enables reliable demos when external API is unavailable.

## 5. Data Model Boundaries

External shape (Pacifica-like payloads) is normalized into internal domain models in `models.py` via mapper layer. This decouples engine logic from provider-specific response formats.

Boundary rule:

- **Provider/adapter code may change for API compatibility.**
- **Engine and policy logic remain stable against internal model contracts.**

## 6. Security and Trust Model

### 6.1 Current Controls

- Session-signed API access for account-scoped runs
- Optional strict mode: `RIPCORD_REQUIRE_SESSION=true`
- Startup config validation for critical secrets
- Optional execution gating with:
  - `RIPCORD_EXECUTION_ENABLED`
  - `RIPCORD_SIGNING_SECRET`
  - `dry_run` / `arm` flags

### 6.2 Known Gaps (MVP)

- No wallet-signature challenge yet (planned hardening item)
- API key lifecycle and rotation must be managed operationally
- TLS termination/security headers rely on hosting provider defaults

### 6.3 Recommended Hardening Next

- Add wallet-signed challenge for session issuance
- Add request rate limiting and abuse controls
- Add structured audit logs for run/execution actions
- Restrict CORS and trusted origins explicitly if architecture changes from rewrite model

## 7. Deployment Architecture

### 7.1 Frontend (Vercel)

- Build: Vite static output
- Rewrites:

```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://ripcord-1.onrender.com/api/:path*"
    }
  ]
}
```

This keeps browser calls same-origin (`/api/*`) while routing server-side to backend.

### 7.2 Backend (Render)

- Service type: Web Service
- Start command:

```bash
PYTHONPATH=src python3 -m ripcord.web_server
```

- Build command:

```bash
pip install --upgrade pip && pip install -e .
```

### 7.3 Required Environment Variables

Minimum for Pacifica HTTP mode:

- `RIPCORD_DATA_SOURCE=http`
- `PACIFICA_BASE_URL=https://test-api.pacifica.fi`
- `PACIFICA_ACCOUNT_QUERY_KEY=account`
- `PACIFICA_ACCOUNT_ID=<default/fallback account id>`
- `PACIFICA_STATE_PATH=/api/v1/account`
- `PACIFICA_OPEN_ORDERS_PATH=/api/v1/orders`
- `PACIFICA_API_KEY=<secret>`

Recommended:

- `RIPCORD_REQUIRE_SESSION=true`
- `RIPCORD_SESSION_SECRET=<strong random value>`

## 8. Observability and Operations

### 8.1 Health and Smoke Checks

- Backend liveness: `GET /api/health`
- Session check: `GET /api/auth/me`
- End-to-end check: `POST /api/run-cycle`

### 8.2 Failure Modes

- Pacifica endpoint mismatch (`404`) -> adapter fetch failure
- Credential/account mismatch (`400`) -> upstream rejection
- Missing secrets in strict modes -> startup validation failure

### 8.3 Runbook (High Priority)

1. Verify Render env values and redeploy.
2. Test Pacifica endpoints directly with account + API key.
3. Confirm Vercel rewrite destination points to active Render URL.
4. Confirm frontend obtains and sends session token.

## 9. Scalability Considerations

Current server model (`ThreadingHTTPServer`) is sufficient for MVP/demo workloads. For higher concurrency and production reliability, consider migration to ASGI/WSGI stack (e.g. FastAPI/Starlette + Uvicorn/Gunicorn), structured middleware, and external session storage.

## 10. Extensibility Roadmap

- Multi-account orchestration and portfolio-level policy evaluation
- Rich policy templates with versioned policy sets
- Execution provider abstraction beyond Pacifica
- Replay scenarios for stress-test catalogs
- Alerting integrations (webhook/Slack/Pager)

## 11. Architecture Decisions (ADR Summary)

1. **Adapter boundary first:** isolate external API instability from risk engine.
2. **Stable response contract:** keep frontend integration simple via versioned payload.
3. **Rewrite-based frontend/backend integration:** avoid browser CORS complexity.
4. **Session-scoped account access:** improve control and observability.

---

For implementation details, see:

- `src/ripcord/web_server.py`
- `src/ripcord/web_api.py`
- `src/ripcord/engine.py`
- `src/ripcord/adapters/pacifica/*`
- `frontend/vercel.json`
