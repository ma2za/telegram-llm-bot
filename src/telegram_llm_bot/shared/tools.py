import ast
import json
import operator
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

TIMEZONE_ALIASES = {
    "bucharest": "Europe/Bucharest",
    "bucuresti": "Europe/Bucharest",
    "bucurești": "Europe/Bucharest",
    "romania": "Europe/Bucharest",
    "utc": "UTC",
}


def tool_schemas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_current_datetime",
                "description": "Get the current date and time for a timezone",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone_name": {
                            "type": "string",
                            "description": "IANA timezone name, or UTC",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Evaluate a basic arithmetic expression",
                "parameters": {
                    "type": "object",
                    "required": ["expression"],
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Arithmetic expression using numbers and operators",
                        }
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web with SearchApi Google results for current information",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum result count to return, from 1 to 10",
                        },
                        "location": {
                            "type": "string",
                            "description": "Optional canonical search location",
                        },
                        "time_period": {
                            "type": "string",
                            "description": "Optional freshness filter such as last_day, last_week, or last_month",
                        },
                    },
                },
            },
        },
    ]


def get_current_datetime(timezone_name: str = "UTC") -> str:
    timezone_name = normalize_timezone_name(timezone_name)
    tz = resolve_timezone(timezone_name)
    return datetime.now(tz).isoformat(timespec="seconds")


def resolve_timezone(timezone_name: str):
    if timezone_name.upper() == "UTC":
        return timezone.utc
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        if timezone_name == "Europe/Bucharest":
            return bucharest_timezone(datetime.now(timezone.utc))
        raise


def bucharest_timezone(now_utc: datetime):
    year = now_utc.year
    dst_start = last_sunday_utc(year, 3)
    dst_end = last_sunday_utc(year, 10)
    if dst_start <= now_utc < dst_end:
        return timezone(timedelta(hours=3), "Europe/Bucharest")
    return timezone(timedelta(hours=2), "Europe/Bucharest")


def last_sunday_utc(year: int, month: int):
    value = datetime(year, month + 1, 1, 1, tzinfo=timezone.utc) - timedelta(days=1)
    return value - timedelta(days=(value.weekday() + 1) % 7)


def normalize_timezone_name(timezone_name: str = "UTC") -> str:
    value = (timezone_name or "UTC").strip()
    return TIMEZONE_ALIASES.get(value.lower(), value)


def calculate(expression: str) -> str:
    expression = normalize_expression(expression)
    if not expression:
        raise ValueError("Expression cannot be empty")
    return str(_eval_node(ast.parse(expression, mode="eval").body))


def web_search(
    query: str,
    max_results: int = 5,
    location: str = None,
    time_period: str = None,
) -> str:
    api_key = os.getenv("SEARCHAPI_API_KEY")
    if not api_key:
        raise RuntimeError("Set SEARCHAPI_API_KEY before using web_search")

    max_results = max(1, min(int(max_results or 5), 10))
    params = {
        "engine": "google",
        "q": (query or "").strip(),
        "safe": os.getenv("SEARCHAPI_SAFE", "active"),
        "hl": os.getenv("SEARCHAPI_HL", "en"),
        "gl": os.getenv("SEARCHAPI_GL", "us"),
    }
    if not params["q"]:
        raise ValueError("Search query cannot be empty")
    if location:
        params["location"] = location
    if time_period:
        params["time_period"] = time_period

    response = httpx.get(
        os.getenv("SEARCHAPI_URL", "https://www.searchapi.io/api/v1/search"),
        params=params,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=float(os.getenv("SEARCHAPI_TIMEOUT", "20")),
    )
    response.raise_for_status()
    return format_searchapi_results(response.json(), max_results=max_results)


def format_searchapi_results(data: dict, max_results: int = 5) -> str:
    results = data.get("organic_results") or []
    lines = []
    for result in results[:max_results]:
        title = result.get("title") or "Untitled"
        link = result.get("link") or ""
        snippet = result.get("snippet") or ""
        source = result.get("source") or result.get("domain") or ""
        parts = [title]
        if source:
            parts.append(f"Source: {source}")
        if link:
            parts.append(f"URL: {link}")
        if snippet:
            parts.append(f"Snippet: {snippet}")
        lines.append("\n".join(parts))
    if not lines:
        return "No search results found."
    return "\n\n".join(lines)


def normalize_expression(expression: str) -> str:
    value = (expression or "").strip()
    if "=" in value:
        value = value.split("=", 1)[0].strip()
    if value.endswith("?"):
        value = value[:-1].strip()
    return value


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Only arithmetic expressions are supported")


def execute_tool_call(tool_call: dict) -> str:
    function = tool_call.get("function", {})
    name = function.get("name")
    arguments = function.get("arguments") or {}
    try:
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        if name == "get_current_datetime":
            return get_current_datetime(**arguments)
        if name == "calculate":
            return calculate(**arguments)
        if name == "web_search":
            return web_search(**arguments)
    except Exception as ex:
        return f"Tool error from {name}: {ex}"
    return f"Unknown tool: {name}"
