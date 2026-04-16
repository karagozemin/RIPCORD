import os
import tempfile
import unittest

from ripcord.adapters.pacifica.config import PacificaConfig
from ripcord.adapters.pacifica.mapper import map_state_to_snapshot
from ripcord.adapters.pacifica.service import build_snapshot_from_pacifica


class PacificaAdapterTests(unittest.TestCase):
    def test_mapper_converts_payload_to_snapshot(self) -> None:
        payload = {
            "account": {
                "success": True,
                "data": {
                    "account_equity": "12000.0",
                },
            },
            "positions": {
                "success": True,
                "data": [
                    {
                        "symbol": "BTC-PERP",
                        "side": "ask",
                        "amount": "0.5",
                        "entry_price": "98000",
                        "isolated": False,
                        "margin": "1000",
                    }
                ],
            },
            "open_orders": {"success": True, "data": []},
        }

        snapshot = map_state_to_snapshot(payload)
        self.assertEqual(snapshot.equity, 12000)
        self.assertEqual(len(snapshot.positions), 1)
        self.assertEqual(snapshot.positions[0].symbol, "BTC-PERP")
        self.assertEqual(snapshot.positions[0].side, "short")
        self.assertEqual(len(snapshot.open_orders), 0)

    def test_service_reads_from_mock_file(self) -> None:
        data = """
        {
          "equity": 11111,
          "maintenance_margin_ratio": 0.005,
          "positions": [],
          "open_orders": []
        }
        """.strip()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as handle:
            handle.write(data)
            path = handle.name

        try:
            config = PacificaConfig(source="mock", mock_file=path)
            snapshot = build_snapshot_from_pacifica(config)
            self.assertEqual(snapshot.equity, 11111)
            self.assertEqual(snapshot.positions, [])
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
