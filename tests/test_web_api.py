import unittest
import os

from ripcord.web_api import run_cycle_payload


class WebApiTests(unittest.TestCase):
    def test_run_cycle_payload_mock_contains_sections(self) -> None:
        payload = run_cycle_payload(mode="mock", shock_pct=0.08)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["contract_version"], "2026-04-16")
        self.assertEqual(payload["source"], "mock")
        self.assertIn("data", payload)
        self.assertIn("risk", payload["data"])
        self.assertIn("replay", payload["data"])
        self.assertIn("execution", payload)
        self.assertIn("result", payload)

    def test_run_cycle_payload_custom_snapshot(self) -> None:
        custom = {
            "equity": 8000,
            "maintenance_margin_ratio": 0.005,
            "positions": [],
            "open_orders": [],
        }
        payload = run_cycle_payload(snapshot_payload=custom)
        self.assertEqual(payload["source"], "custom")
        self.assertEqual(payload["data"]["risk"]["level"], "LOW")

    def test_run_cycle_payload_policy_override(self) -> None:
        payload = run_cycle_payload(
            mode="mock",
            policy_payload={
                "never_open_new_risk": False,
                "hedge_enabled": True,
                "max_effective_leverage": 8.0,
            },
        )
        self.assertFalse(payload["policy"]["never_open_new_risk"])
        self.assertEqual(payload["policy"]["max_effective_leverage"], 8.0)

    def test_execution_dispatch_not_armed_when_disabled(self) -> None:
        payload = run_cycle_payload(mode="mock", arm_execution=False)
        self.assertEqual(payload["execution"]["dispatch"]["status"], "disabled")

    def test_execution_dispatch_dry_run_when_enabled_and_armed(self) -> None:
        old_env = {
            "RIPCORD_EXECUTION_ENABLED": os.getenv("RIPCORD_EXECUTION_ENABLED"),
            "PACIFICA_EXECUTION_ENDPOINT": os.getenv("PACIFICA_EXECUTION_ENDPOINT"),
            "PACIFICA_AGENT_KEY": os.getenv("PACIFICA_AGENT_KEY"),
            "RIPCORD_SIGNING_SECRET": os.getenv("RIPCORD_SIGNING_SECRET"),
        }
        try:
            os.environ["RIPCORD_EXECUTION_ENABLED"] = "true"
            os.environ["PACIFICA_EXECUTION_ENDPOINT"] = "https://example.test/execute"
            os.environ["PACIFICA_AGENT_KEY"] = "agent_123"
            os.environ["RIPCORD_SIGNING_SECRET"] = "secret_123"
            payload = run_cycle_payload(mode="mock", arm_execution=True, execution_dry_run=True)
            self.assertEqual(payload["execution"]["dispatch"]["status"], "dry_run")
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
