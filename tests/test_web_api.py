import unittest

from ripcord.web_api import run_cycle_payload


class WebApiTests(unittest.TestCase):
    def test_run_cycle_payload_mock_contains_sections(self) -> None:
        payload = run_cycle_payload(mode="mock", shock_pct=0.08)
        self.assertEqual(payload["source"], "mock")
        self.assertIn("result", payload)
        self.assertIn("risk", payload["result"])
        self.assertIn("replay", payload["result"])

    def test_run_cycle_payload_custom_snapshot(self) -> None:
        custom = {
            "equity": 8000,
            "maintenance_margin_ratio": 0.005,
            "positions": [],
            "open_orders": [],
        }
        payload = run_cycle_payload(snapshot_payload=custom)
        self.assertEqual(payload["source"], "custom")
        self.assertEqual(payload["result"]["risk"]["level"], "LOW")


if __name__ == "__main__":
    unittest.main()
