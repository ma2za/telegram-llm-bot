import unittest
from datetime import datetime, timezone

from telegram_llm_bot.shared.tools import (
    bucharest_timezone,
    calculate,
    execute_tool_call,
    normalize_timezone_name,
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


if __name__ == "__main__":
    unittest.main()
