import unittest
from types import SimpleNamespace
from unittest.mock import patch

import jobs.mps as mps
from core.wx.model.weread_mp import MpsWereadMP


class FakeCollector:
    def __init__(self):
        self.articles = []
        self.calls = []

    def get_Articles(self, faker_id, **kwargs):
        self.calls.append((faker_id, kwargs))

    def all_count(self):
        return 0


def weread_auth(cookie):
    def _load(self):
        self._weread_cookies = cookie
        self._weread_ticket = ""
        self._weread_vid = ""
        self._weread_name = ""

    return _load


class SelectCollectorTest(unittest.TestCase):
    def setUp(self):
        self.default = FakeCollector()
        patcher = patch.object(mps, "WxGather")
        gather = patcher.start()
        self.addCleanup(patcher.stop)
        gather.return_value.Model.return_value = self.default
        self.mp = SimpleNamespace(id="MP_WXS_123", faker_id="MzA1", mp_name="demo")

    def test_mp_wxs_without_weread_cookie_uses_default_collector(self):
        with patch.object(MpsWereadMP, "_load_weread_auth", weread_auth("")):
            self.assertIs(mps.select_collector(self.mp), self.default)

    def test_mp_wxs_with_weread_cookie_uses_weread_collector(self):
        with patch.object(MpsWereadMP, "_load_weread_auth", weread_auth("wr_vid=1")):
            self.assertIsInstance(mps.select_collector(self.mp), MpsWereadMP)

    def test_weread_auth_error_falls_back_to_default_collector(self):
        with patch.object(MpsWereadMP, "_load_weread_auth", side_effect=OSError("wx.lic unreadable")):
            self.assertIs(mps.select_collector(self.mp), self.default)

    def test_do_job_collects_mp_wxs_feed_without_weread_cookie(self):
        task = SimpleNamespace(id="task-1")
        with patch.object(MpsWereadMP, "_load_weread_auth", weread_auth("")), \
                patch.object(mps, "web_hook"), \
                patch.object(mps, "tracker") as tracker:
            mps.do_job(mp=self.mp, task=task)

        self.assertEqual([call[0] for call in self.default.calls], ["MzA1"])
        tracker.record_mp_result.assert_called_once()
        self.assertIsNone(tracker.record_mp_result.call_args.kwargs["error"])


if __name__ == "__main__":
    unittest.main()
