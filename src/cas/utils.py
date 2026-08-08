"""Shared helpers for the CAS package: safe execution and JSON serialization."""

import html
import json
import re
from typing import Any, Callable


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(value: str) -> str:
    """Strip HTML tags from CAS API text fields (names / molecular formulas)."""
    if not value:
        return value
    return html.unescape(_HTML_TAG_RE.sub("", value)).strip()


def to_json_safe(result: Any) -> str:
    """Serialize CAS API results to a JSON string."""
    return json.dumps(result, indent=2, ensure_ascii=False, default=str)


def safe_execute(func: Callable, *args: Any, **kwargs: Any) -> str:
    """Run ``func`` and return its JSON string; on any exception return ``Error: ...``."""
    try:
        return to_json_safe(func(*args, **kwargs))
    except Exception as exc:  # noqa: BLE001 - tool boundary: errors go back as text
        return f"Error: {str(exc)}"
