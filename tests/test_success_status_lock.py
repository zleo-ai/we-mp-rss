import threading
import time
import unittest
from unittest.mock import patch

import driver.success as success


class GetStatusLockTest(unittest.TestCase):
    def setUp(self):
        saved = success.WX_LOGIN_ED
        self.addCleanup(setattr, success, "WX_LOGIN_ED", saved)

    def run_get_status(self, token_data):
        result = {}

        def target():
            result["value"] = success.getStatus()

        with patch.object(success.redis_client, "_client", None), \
                patch.object(success, "getLoginInfo", return_value=token_data):
            self.assertFalse(success.redis_client.is_connected)
            worker = threading.Thread(target=target, daemon=True)
            worker.start()
            worker.join(timeout=2)
        self.assertFalse(worker.is_alive(), "getStatus() deadlocked on login_lock")
        return result["value"]

    def test_expired_token_without_redis_returns_false_without_deadlock(self):
        success.WX_LOGIN_ED = True
        expired = {"token": "t", "expiry": {"expiry_timestamp": time.time() - 60}}

        self.assertFalse(self.run_get_status(expired))
        self.assertFalse(success.WX_LOGIN_ED)

    def test_valid_token_without_redis_returns_true(self):
        success.WX_LOGIN_ED = True
        valid = {"token": "t", "expiry": {"expiry_timestamp": time.time() + 3600}}

        self.assertTrue(self.run_get_status(valid))
        self.assertTrue(success.WX_LOGIN_ED)

    def test_logged_out_without_redis_returns_false(self):
        success.WX_LOGIN_ED = False

        self.assertFalse(self.run_get_status(None))


if __name__ == "__main__":
    unittest.main()
