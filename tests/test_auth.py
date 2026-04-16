import tempfile
import time
import unittest
from pathlib import Path

from ripcord.auth import SessionSigner, SessionStore


class AuthTests(unittest.TestCase):
    def test_session_store_create_and_get(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SessionStore(Path(temp_dir) / "sessions.db")
            record = store.create(account_id="acc_1", ttl_seconds=60)
            loaded = store.get(record.session_id)
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.account_id, "acc_1")

    def test_session_signer_roundtrip(self) -> None:
        signer = SessionSigner("secret")
        exp = int(time.time()) + 60
        token = signer.sign("sid_1", exp)
        sid, parsed_exp = signer.verify(token)
        self.assertEqual(sid, "sid_1")
        self.assertEqual(parsed_exp, exp)


if __name__ == "__main__":
    unittest.main()
