import asyncio
import importlib
import inspect
import os
import sys
import unittest
from unittest.mock import AsyncMock, patch

import driver.wx
import driver.wx_api

RELOADED = ("driver.base", "apis.auth")


class AuthDriverSelectionTest(unittest.TestCase):
    def setUp(self):
        saved = {name: sys.modules.get(name) for name in RELOADED}

        def restore():
            for name, module in saved.items():
                if module is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = module

        self.addCleanup(restore)

    def import_auth_api(self, auth_web):
        for name in RELOADED:
            sys.modules.pop(name, None)
        with patch.dict(os.environ, {"WERSS_AUTH_WEB": auth_web}):
            return importlib.import_module("apis.auth")

    def test_http_login_driver_when_auth_web_disabled(self):
        auth = self.import_auth_api("False")
        self.assertIs(auth.WX_API, driver.wx_api.WeChat_api)

    def test_browser_login_driver_when_auth_web_enabled(self):
        auth = self.import_auth_api("True")
        self.assertIs(auth.WX_API, driver.wx.WX_API)

    def test_qr_over_endpoint_works_with_http_driver(self):
        auth = self.import_auth_api("False")
        response = asyncio.run(auth.qr_success(current_user={}))
        self.assertEqual(response["code"], 0)

    def test_http_driver_switch_account_forwards_progress_callback(self):
        self.assertIn(
            "progress_callback",
            inspect.signature(driver.wx_api.WeChatAPI.switch_account).parameters,
        )
        api = driver.wx_api.WeChatAPI()

        def progress(stage, message, progress):
            pass

        with patch.object(api, "login_with_token"), \
                patch.object(driver.wx.WX_API, "switch_account", new=AsyncMock(return_value=True)) as switch:
            self.assertTrue(asyncio.run(api.switch_account(username="u", progress_callback=progress)))
        switch.assert_awaited_once_with("u", progress_callback=progress)


if __name__ == "__main__":
    unittest.main()
