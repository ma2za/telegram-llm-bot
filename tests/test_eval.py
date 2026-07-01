from io import StringIO
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from telegram_llm_bot.eval import DEFAULT_FIXTURE, evaluate_answer, load_eval_cases, run_eval


class EvalFixtureTest(unittest.TestCase):
    def test_loads_eval_cases(self):
        cases = load_eval_cases()

        self.assertGreaterEqual(len(cases), 7)
        self.assertTrue(all(case.get("id") for case in cases))
        self.assertTrue(all(case.get("prompt") for case in cases))

    def test_evaluates_expected_answer(self):
        failures = evaluate_answer(
            "Use poetry run python -m unittest.",
            [
                {"type": "contains_all", "values": ["poetry", "unittest"]},
                {"type": "max_words", "value": 8},
            ],
        )

        self.assertEqual(failures, [])

    def test_reports_failed_expectation(self):
        failures = evaluate_answer(
            "I will guess it is Apollo.",
            [{"type": "not_contains", "values": ["guess", "Apollo"]}],
        )

        self.assertEqual(len(failures), 1)


class EvalRunnerTest(unittest.IsolatedAsyncioTestCase):
    async def test_mock_eval_passes_fixture_cases(self):
        with patch("sys.stdout", new=StringIO()):
            failures = await run_eval(DEFAULT_FIXTURE, mock=True)

        self.assertEqual(failures, 0)

    async def test_missing_fixture_cases_fail_fast(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.yml"
            path.write_text("cases: []\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "No eval cases"):
                await run_eval(path, mock=True)


if __name__ == "__main__":
    unittest.main()
