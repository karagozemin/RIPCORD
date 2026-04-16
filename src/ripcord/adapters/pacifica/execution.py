from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.request
from urllib.error import HTTPError
from typing import Any

from .config import PacificaConfig


def build_execution_preview(actions: list[dict[str, Any]], config: PacificaConfig) -> dict[str, Any]:
    enabled = bool(config.execution_enabled)
    ready = enabled and bool(config.execution_endpoint and config.agent_key and config.signing_secret)

    payload = {
        "agent_key": config.agent_key,
        "actions": actions,
        "timestamp": int(time.time()),
    }

    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = ""
    if config.signing_secret:
        signature = hmac.new(
            config.signing_secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    return {
        "enabled": enabled,
        "ready": ready,
        "endpoint": config.execution_endpoint,
        "signed_request": {
            "body": payload,
            "headers": {
                "Content-Type": "application/json",
                "X-RIPCORD-SIGNATURE": signature,
                "X-RIPCORD-AGENT-KEY": config.agent_key,
            },
        },
        "missing": [
            key
            for key, value in {
                "PACIFICA_EXECUTION_ENDPOINT": config.execution_endpoint,
                "PACIFICA_AGENT_KEY": config.agent_key,
                "RIPCORD_SIGNING_SECRET": config.signing_secret,
            }.items()
            if not value
        ],
    }


def dispatch_execution(
    actions: list[dict[str, Any]],
    config: PacificaConfig,
    *,
    arm: bool,
    dry_run: bool = True,
) -> dict[str, Any]:
    preview = build_execution_preview(actions=actions, config=config)

    if not preview["enabled"]:
        return {
            "attempted": False,
            "status": "disabled",
            "message": "Execution feature flag is disabled",
        }

    if not arm:
        return {
            "attempted": False,
            "status": "not_armed",
            "message": "Execution not armed by client",
        }

    if not preview["ready"]:
        return {
            "attempted": False,
            "status": "not_ready",
            "message": "Execution config is incomplete",
            "missing": preview.get("missing", []),
        }

    if dry_run:
        return {
            "attempted": True,
            "status": "dry_run",
            "message": "Execution dry-run simulated",
            "endpoint": preview["endpoint"],
        }

    request_body = json.dumps(preview["signed_request"]["body"]).encode("utf-8")
    request = urllib.request.Request(
        url=preview["endpoint"],
        data=request_body,
        method="POST",
    )

    for key, value in preview["signed_request"]["headers"].items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, timeout=config.timeout_seconds) as response:
            response_body = response.read().decode("utf-8")
            payload = json.loads(response_body) if response_body else {}
            return {
                "attempted": True,
                "status": "live_ok",
                "http_status": response.status,
                "response": payload,
            }
    except HTTPError as error:
        body = error.read().decode("utf-8") if error.fp else ""
        return {
            "attempted": True,
            "status": "live_error",
            "http_status": error.code,
            "message": body.strip() or str(error),
        }
