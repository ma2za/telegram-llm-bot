import socket
import unittest
from unittest.mock import patch

import httpx

from telegram_llm_bot.app import build_application, check_telegram_api_reachable


class Response:
    status_code = 302


class AppTest(unittest.TestCase):
    def test_telegram_preflight_passes_when_dns_and_https_work(self):
        def resolve(host, port, type):
            return [(socket.AF_INET, type, 6, "", ("149.154.166.110", port))]

        def http_get(url, timeout, follow_redirects):
            return Response()

        check_telegram_api_reachable(resolve=resolve, http_get=http_get)

    def test_telegram_preflight_explains_dns_failure(self):
        def resolve(host, port, type):
            raise socket.gaierror("getaddrinfo failed")

        with self.assertRaisesRegex(RuntimeError, "Cannot resolve api.telegram.org"):
            check_telegram_api_reachable(resolve=resolve)

    def test_telegram_preflight_explains_https_failure(self):
        def resolve(host, port, type):
            return [(socket.AF_INET, type, 6, "", ("149.154.166.110", port))]

        def http_get(url, timeout, follow_redirects):
            raise httpx.ConnectError("connect failed")

        with self.assertRaisesRegex(RuntimeError, "Cannot reach api.telegram.org over HTTPS"):
            check_telegram_api_reachable(resolve=resolve, http_get=http_get)

    def test_telegram_clients_ignore_proxy_environment(self):
        with patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "123:test"}):
            app = build_application()

        request, get_updates_request = app.bot._request
        self.assertFalse(request._client_kwargs["trust_env"])
        self.assertFalse(get_updates_request._client_kwargs["trust_env"])
        self.assertIsNotNone(request._client_kwargs["transport"])
        self.assertIsNotNone(get_updates_request._client_kwargs["transport"])


if __name__ == "__main__":
    unittest.main()
