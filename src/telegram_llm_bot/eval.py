import argparse
import asyncio
import os
from pathlib import Path

import yaml

from telegram_llm_bot.config import load_bot_config
from telegram_llm_bot.paths import PROJECT_DIR, load_environment
from telegram_llm_bot.shared.chat import chat
from telegram_llm_bot.shared.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

DEFAULT_FIXTURE = PROJECT_DIR / "tests" / "fixtures" / "assistant_eval_cases.yml"


def load_eval_cases(path: Path = DEFAULT_FIXTURE) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    cases = data.get("cases") or []
    if not cases:
        raise ValueError(f"No eval cases found in {path}")
    return cases


def case_messages(case: dict, system_prompt: str) -> list[BaseMessage]:
    messages = [SystemMessage(content=system_prompt)]
    for item in case.get("history") or []:
        role = item.get("role")
        content = item.get("content", "")
        if role in {"human", "user"}:
            messages.append(HumanMessage(content=content))
        elif role in {"ai", "assistant"}:
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            raise ValueError(f"Unsupported history role in {case['id']}: {role}")
    messages.append(HumanMessage(content=case["prompt"]))
    return messages


def answer_words(answer: str) -> list[str]:
    return [word for word in answer.replace("\n", " ").split(" ") if word]


def evaluate_answer(answer: str, expectations: list[dict]) -> list[str]:
    failures = []
    text = answer.strip()
    lower_text = text.lower()
    for expectation in expectations:
        kind = expectation["type"]
        if kind == "non_empty":
            if not text:
                failures.append("answer is empty")
        elif kind == "contains_all":
            missing = [value for value in expectation["values"] if value.lower() not in lower_text]
            if missing:
                failures.append(f"missing required text: {', '.join(missing)}")
        elif kind == "contains_any":
            if not any(value.lower() in lower_text for value in expectation["values"]):
                failures.append(f"missing one of: {', '.join(expectation['values'])}")
        elif kind == "not_contains":
            found = [value for value in expectation["values"] if value.lower() in lower_text]
            if found:
                failures.append(f"contains forbidden text: {', '.join(found)}")
        elif kind == "max_words":
            count = len(answer_words(text))
            if count > int(expectation["value"]):
                failures.append(f"too many words: {count} > {expectation['value']}")
        elif kind == "question_count":
            count = text.count("?")
            if count != int(expectation["value"]):
                failures.append(f"question count mismatch: {count} != {expectation['value']}")
        elif kind == "ends_with_question":
            if not text.endswith("?"):
                failures.append("answer does not end with a question")
        else:
            raise ValueError(f"Unsupported expectation type: {kind}")
    return failures


async def answer_case(case: dict, provider: str = None, mock: bool = False) -> str:
    if mock:
        return case.get("mock_answer", "")
    old_provider = os.environ.get("LLM_PROVIDER")
    if provider:
        os.environ["LLM_PROVIDER"] = provider
    try:
        return await chat(case_messages(case, load_bot_config().system))
    finally:
        if provider and old_provider is None:
            os.environ.pop("LLM_PROVIDER", None)
        elif provider:
            os.environ["LLM_PROVIDER"] = old_provider


async def run_eval(path: Path, provider: str = None, mock: bool = False) -> int:
    cases = load_eval_cases(path)
    failures = 0
    for case in cases:
        answer = await answer_case(case, provider=provider, mock=mock)
        case_failures = evaluate_answer(answer, case.get("expectations") or [])
        status = "PASS" if not case_failures else "FAIL"
        print(f"{status} {case['id']}")
        print(answer.strip())
        if case_failures:
            failures += 1
            for failure in case_failures:
                print(f"- {failure}")
        print()
    return failures


def main() -> None:
    load_environment()
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--provider", choices=["ollama", "beam", "echo"])
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()
    failures = asyncio.run(run_eval(args.fixture, provider=args.provider, mock=args.mock))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
