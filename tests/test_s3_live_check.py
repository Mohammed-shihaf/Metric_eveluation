"""Tests for s3_live_check()."""

from __future__ import print_function

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.s3_sync import s3_live_check  # noqa: E402


class S3LiveCheckTests(unittest.TestCase):
    def test_skipped_when_no_credentials(self):
        for key in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
            os.environ.pop(key, None)
        with patch("pathlib.Path.is_file", return_value=False):
            result = s3_live_check()
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "SKIPPED")

    def test_ok_on_successful_list(self):
        os.environ["AWS_ACCESS_KEY_ID"] = "AKIATEST"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "secret"
        client = MagicMock()
        client.list_objects_v2.return_value = {"Contents": []}
        with patch("lib.s3_sync._s3_client", return_value=client):
            result = s3_live_check()
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], "OK")

    def test_auth_on_invalid_token(self):
        os.environ["AWS_ACCESS_KEY_ID"] = "ASIATEST"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "secret"

        class FakeClientError(Exception):
            def __init__(self):
                self.response = {"Error": {"Code": "InvalidToken"}}

        client = MagicMock()
        client.list_objects_v2.side_effect = FakeClientError()
        with patch("lib.s3_sync._s3_client", return_value=client):
            result = s3_live_check()
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "AUTH")


if __name__ == "__main__":
    unittest.main()
