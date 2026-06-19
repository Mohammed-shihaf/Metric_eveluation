"""Tests for S3 credential reload and AWS auth error classification."""

from __future__ import print_function

import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.sa_qa import reload_env_keys, reload_s3_credentials  # noqa: E402
from lib.s3_sync import _aws_auth_error, sync_run  # noqa: E402


class S3CredentialTests(unittest.TestCase):
    def test_reload_env_keys_overrides_existing(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as fh:
            fh.write("AWS_ACCESS_KEY_ID=NEWKEY\nAWS_SECRET_ACCESS_KEY=newsecret\n")
            path = fh.name
        try:
            os.environ["AWS_ACCESS_KEY_ID"] = "OLDKEY"
            os.environ["AWS_SECRET_ACCESS_KEY"] = "oldsecret"
            n = reload_env_keys(path, ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"), override=True)
            self.assertEqual(n, 2)
            self.assertEqual(os.environ["AWS_ACCESS_KEY_ID"], "NEWKEY")
            self.assertEqual(os.environ["AWS_SECRET_ACCESS_KEY"], "newsecret")
        finally:
            os.unlink(path)

    def test_reload_s3_credentials_updates_sts_token(self):
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as fh:
            fh.write(
                "AWS_ACCESS_KEY_ID=ASIATEST\n"
                "AWS_SECRET_ACCESS_KEY=secret\n"
                "AWS_SESSION_TOKEN=fresh-token\n"
            )
            path = fh.name
        try:
            os.environ["AWS_SESSION_TOKEN"] = "stale-token"
            n = reload_s3_credentials(path, root=ROOT)
            self.assertGreaterEqual(n, 3)
            self.assertEqual(os.environ["AWS_SESSION_TOKEN"], "fresh-token")
        finally:
            os.unlink(path)

    def test_aws_auth_error_detects_invalid_token_message(self):
        exc = Exception(
            "An error occurred (InvalidToken) when calling the ListObjectsV2 operation: "
            "The provided token is malformed or otherwise invalid."
        )
        self.assertTrue(_aws_auth_error(exc))

    def test_sync_run_returns_auth_not_error_on_invalid_token(self):
        class FakeClientError(Exception):
            def __init__(self):
                self.response = {"Error": {"Code": "InvalidToken"}}

        import lib.s3_sync as s3_sync

        original = s3_sync.find_s3_run_prefix

        def _raise_auth(*_args, **_kwargs):
            raise FakeClientError()

        s3_sync.find_s3_run_prefix = _raise_auth
        try:
            os.environ["AWS_ACCESS_KEY_ID"] = "ASIATEST"
            os.environ["AWS_SECRET_ACCESS_KEY"] = "secret"
            os.environ["AWS_SESSION_TOKEN"] = "token"
            result = sync_run(
                "SA_Decision-Outcome-Verification_Bug_2.6",
                "abc123",
                "run-001",
            )
            self.assertEqual(result["status"], "AUTH")
            self.assertIn(".env.local", result.get("reason", ""))
        finally:
            s3_sync.find_s3_run_prefix = original


if __name__ == "__main__":
    unittest.main()
