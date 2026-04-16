import os
import tempfile
import unittest

from ripcord.adapters.pacifica.config import PacificaConfig
from ripcord.adapters.pacifica.mapper import map_state_to_snapshot
from ripcord.adapters.pacifica.service import build_snapshot_from_pacifica


class PacificaAdapterTests(unittest.TestCase):
    def test_mapper_converts_payload_to_snapshot(self) -> None:
        payload = {
            "equity": 12000,
            "maintenance_margin_ratio": 0.005,
            "positions": [
                {
                    "symbol": "BTC-PERP",
                    "side": "long",
                    "size": 0.5,
                    "entry_price": 98000,
                    "mark_price": 97000,
                    "leverage": 15,
                    "isolated": False,
                    "funding_rate_hourly": 0.0002,
                    "has_tpsl": False,
                }
            ],
            "open_orders": [
                {
                    "symbol": "BTC-PERP",
                    "side": "sell",
                    "size": 0.1,
                    "reduce_only": True,
                }
            ],
        }

        snapshot = map_state_to_snapshot(payload)
        self.assertEqual(snapshot.equity, 12000)
        self.assertEqual(len(snapshot.positions), 1)
        self.assertEqual(snapshot.positions[0].symbol, "BTC-PERP")
        self.assertEqual(len(snapshot.open_orders), 1)

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
