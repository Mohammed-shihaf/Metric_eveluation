"""Tests for credential audit on hosted deployments without .env.local."""

import os
import unittest
from unittest.mock import patch

from lib.credentials import audit_credentials


class CredentialsAuditTests(unittest.TestCase):
    def test_urls_ok_without_env_file_when_process_env_set(self):
        env = {
            "IDENTITY_URL": "https://qa-api.testable.cc",
            "RUNTIME_URL": "https://qa-runtime.testable.cc",
            "VIEWS_URL": "https://qa-views.testable.cc",
        }
        with patch.dict(os.environ, env, clear=False):
            audit = audit_credentials(env_file="/nonexistent/.env.local")
        self.assertFalse(audit["env_file_present"])
        self.assertTrue(audit["testable_urls_ok"])
        self.assertFalse(audit["testable_ready"])

    def test_urls_not_ok_when_core_urls_missing(self):
        removed = {k: os.environ.pop(k, None) for k in (
            "IDENTITY_URL", "RUNTIME_URL", "VIEWS_URL",
        )}
        try:
            audit = audit_credentials(env_file="/nonexistent/.env.local")
        finally:
            for key, value in removed.items():
                if value is not None:
                    os.environ[key] = value
        self.assertFalse(audit["testable_urls_ok"])


if __name__ == "__main__":
    unittest.main()
