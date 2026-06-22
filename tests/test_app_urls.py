"""Tests for OAuth redirect URI resolution."""

from __future__ import print_function

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.app_urls import (  # noqa: E402
    HOSTED_APP_ROOT,
    LOCAL_APP_ROOT,
    apply_github_oauth_redirect_uri,
    resolve_github_oauth_redirect_uri,
)


class AppUrlTests(unittest.TestCase):
    def setUp(self):
        self._saved = {
            k: os.environ.get(k)
            for k in (
                "GITHUB_OAUTH_REDIRECT_URI",
                "APP_PUBLIC_URL",
                "ASSURANCE_STUDIO_ENV",
            )
        }

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_explicit_localhost_allowed(self):
        os.environ["GITHUB_OAUTH_REDIRECT_URI"] = "http://localhost:8501/"
        self.assertEqual(resolve_github_oauth_redirect_uri(), LOCAL_APP_ROOT)

    def test_explicit_hosted_allowed(self):
        os.environ["GITHUB_OAUTH_REDIRECT_URI"] = "https://qa-assurance.testable.cc/"
        self.assertEqual(resolve_github_oauth_redirect_uri(), HOSTED_APP_ROOT)

    def test_ngrok_fallback_to_localhost(self):
        os.environ["GITHUB_OAUTH_REDIRECT_URI"] = "https://example.ngrok-free.app/"
        self.assertEqual(resolve_github_oauth_redirect_uri(), LOCAL_APP_ROOT)

    def test_app_public_url_hosted(self):
        os.environ.pop("GITHUB_OAUTH_REDIRECT_URI", None)
        os.environ["APP_PUBLIC_URL"] = "https://qa-assurance.testable.cc/"
        self.assertEqual(resolve_github_oauth_redirect_uri(), HOSTED_APP_ROOT)

    def test_assurance_studio_env_hosted(self):
        os.environ.pop("GITHUB_OAUTH_REDIRECT_URI", None)
        os.environ["ASSURANCE_STUDIO_ENV"] = "hosted"
        self.assertEqual(resolve_github_oauth_redirect_uri(), HOSTED_APP_ROOT)

    def test_apply_sets_environment(self):
        os.environ["GITHUB_OAUTH_REDIRECT_URI"] = "https://old.ngrok.app/"
        apply_github_oauth_redirect_uri()
        self.assertEqual(os.environ["GITHUB_OAUTH_REDIRECT_URI"], LOCAL_APP_ROOT)


if __name__ == "__main__":
    unittest.main()
