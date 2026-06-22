"""Tests that QA login does not clear GitHub session keys."""

from __future__ import print_function

import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)


class AuthIsolationTests(unittest.TestCase):
    def test_apply_qa_login_does_not_bind_qa_email_as_app_user(self):
        import ui.app as app

        class FakeSession(dict):
            def get(self, key, default=None):
                return dict.get(self, key, default)

            def pop(self, key, default=None):
                return dict.pop(self, key, default)

        fake = FakeSession({
            "github_login_ok": True,
            "github_user_login": "octocat",
            "github_token_saved": "gho_test",
            "_bound_app_user": "octocat",
        })
        with patch.object(app, "st") as st_mock, patch.object(
            app, "verify_login", return_value=(True, "OK"),
        ):
            st_mock.session_state = fake
            ok, msg = app._apply_qa_login(".env.local", "qa@test.com", "secret")
        self.assertTrue(ok)
        self.assertEqual(fake.get("github_login_ok"), True)
        self.assertEqual(fake.get("github_user_login"), "octocat")
        self.assertEqual(fake.get("github_token_saved"), "gho_test")
        self.assertEqual(fake.get("_bound_app_user"), "octocat")
        self.assertEqual(fake.get("qa_email_saved"), "qa@test.com")


if __name__ == "__main__":
    unittest.main()
