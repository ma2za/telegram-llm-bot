import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from telegram_llm_bot.shared.tools import (
    bucharest_timezone,
    calculate,
    execute_tool_call,
    format_searchapi_results,
    normalize_timezone_name,
    tool_schemas,
    web_search,
)


class ToolsTest(unittest.TestCase):
    def test_normalizes_bucharest_timezone_alias(self):
        self.assertEqual(normalize_timezone_name("Bucharest"), "Europe/Bucharest")

    def test_keeps_iana_timezone_name(self):
        self.assertEqual(normalize_timezone_name("Europe/London"), "Europe/London")

    def test_calculates_expression_with_model_suffix(self):
        self.assertEqual(calculate("1 + 2 = ?"), "3")

    def test_tool_call_errors_do_not_raise(self):
        result = execute_tool_call(
            {
                "function": {
                    "name": "calculate",
                    "arguments": {"expression": "bad("},
                }
            }
        )

        self.assertIn("Tool error from calculate", result)

    def test_bucharest_fallback_uses_summer_offset(self):
        tz = bucharest_timezone(datetime(2026, 6, 28, 12, tzinfo=timezone.utc))

        self.assertEqual(tz.utcoffset(None).total_seconds(), 3 * 60 * 60)

    def test_bucharest_fallback_uses_winter_offset(self):
        tz = bucharest_timezone(datetime(2026, 1, 28, 12, tzinfo=timezone.utc))

        self.assertEqual(tz.utcoffset(None).total_seconds(), 2 * 60 * 60)

    def test_tool_schemas_include_web_search(self):
        names = [tool["function"]["name"] for tool in tool_schemas()]

        self.assertIn("web_search", names)

    def test_formats_searchapi_results(self):
        text = format_searchapi_results(
            {
                "organic_results": [
                    {
                        "title": "Example",
                        "source": "example.com",
                        "link": "https://example.com",
                        "snippet": "Result text",
                    }
                ]
            }
        )

        self.assertIn("Example", text)
        self.assertIn("Source: example.com", text)
        self.assertIn("URL: https://example.com", text)
        self.assertIn("Snippet: Result text", text)

    def test_web_search_uses_searchapi_bearer_token(self):
        response = Mock()
        response.json.return_value = {
            "organic_results": [
                {
                    "title": "Example",
                    "link": "https://example.com",
                    "snippet": "Result text",
                }
            ]
        }
        response.raise_for_status.return_value = None

        with patch.dict("os.environ", {"SEARCHAPI_API_KEY": "secret"}, clear=False):
            with patch("telegram_llm_bot.shared.tools.httpx.get", return_value=response) as get:
                text = web_search("hello", max_results=1)

        self.assertIn("Example", text)
        kwargs = get.call_args.kwargs
        self.assertEqual(kwargs["headers"], {"Authorization": "Bearer secret"})
        self.assertEqual(kwargs["params"]["engine"], "google")
        self.assertEqual(kwargs["params"]["q"], "hello")
        self.assertNotIn("api_key", kwargs["params"])

    def test_web_search_tool_reports_missing_key(self):
        with patch.dict("os.environ", {}, clear=True):
            result = execute_tool_call(
                {
                    "function": {
                        "name": "web_search",
                        "arguments": {"query": "hello"},
                    }
                }
            )

        self.assertIn("Tool error from web_search", result)
        self.assertIn("SEARCHAPI_API_KEY", result)


if __name__ == "__main__":
    unittest.main()
