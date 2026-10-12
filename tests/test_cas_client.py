"""Regression tests for the CAS client's gateway wiring.

These cover the two properties that made every ``cas_*`` tool fail against the
live API, and they need no network access:

1. the base URL points at the current gateway (``/direct-api``);
2. every request carries the ``x-origin`` header that gateway requires.

Run from the repository root:

    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cas import client  # noqa: E402

LIVE_BASE_URL = "https://commonchemistry.cas.org/direct-api"
LIVE_ORIGIN = "https://commonchemistry.cas.org/api-overview"


class CasClientWiringTests(unittest.TestCase):
    def setUp(self):
        self._saved_env = {
            name: os.environ.get(name)
            for name in (client.API_KEY_ENV, client.BASE_URL_ENV, client.ORIGIN_ENV)
        }
        # Keep the test independent of any developer .env file on disk.
        self._saved_load_dotenv = client.load_dotenv
        client.load_dotenv = lambda *args, **kwargs: False

        os.environ[client.API_KEY_ENV] = "test-token"
        for name in (client.BASE_URL_ENV, client.ORIGIN_ENV):
            os.environ.pop(name, None)

    def tearDown(self):
        client.load_dotenv = self._saved_load_dotenv
        for name, value in self._saved_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    def test_default_base_url_targets_the_live_gateway(self):
        self.assertEqual(client._base_url(), LIVE_BASE_URL)
        # The retired /api gateway must not come back as the constant default.
        self.assertEqual(client.BASE_URL, LIVE_BASE_URL)

    def test_headers_include_the_required_origin_header(self):
        headers = client._headers()
        self.assertEqual(headers["X-Api-Key"], "test-token")
        self.assertEqual(headers["X-Origin"], LIVE_ORIGIN)
        self.assertEqual(headers["Accept"], "application/json")

    def test_environment_overrides_win_over_defaults(self):
        os.environ[client.BASE_URL_ENV] = "https://example.test/direct-api/"
        os.environ[client.ORIGIN_ENV] = "https://example.test/api-overview"

        # The trailing slash is trimmed so paths never become "//search".
        self.assertEqual(client._base_url(), "https://example.test/direct-api")
        self.assertEqual(client._headers()["X-Origin"], "https://example.test/api-overview")

    def test_401_message_does_not_blame_the_api_key_alone(self):
        message = client._error_message(401, '{"message":"Unauthorized"}')
        self.assertIn("x-origin", message)

    def test_403_message_mentions_the_gateway_override(self):
        message = client._error_message(403, '{"message":"Forbidden"}')
        self.assertIn(client.BASE_URL_ENV, message)

    def test_missing_api_key_still_raises(self):
        os.environ.pop(client.API_KEY_ENV, None)
        with self.assertRaises(RuntimeError):
            client._api_key()


if __name__ == "__main__":
    unittest.main()
