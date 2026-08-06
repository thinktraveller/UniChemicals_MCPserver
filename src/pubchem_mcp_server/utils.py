"""Shared helpers: safe execution and JSON serialization for tool output."""

import json
from typing import Any, Callable


def to_json_safe(result: Any) -> str:
    """Serialize PubChemPy objects (with ``to_dict``) or plain data to a JSON string."""
    if hasattr(result, "to_dict"):
        return json.dumps(result.to_dict(), indent=2)
    if isinstance(result, list) and result and hasattr(result[0], "to_dict"):
        return json.dumps([item.to_dict() for item in result], indent=2)
    return json.dumps(result, indent=2)


def safe_execute(func: Callable, *args: Any, **kwargs: Any) -> str:
    """Run ``func`` and return its JSON string; on any exception return ``Error: ...``."""
    try:
        return to_json_safe(func(*args, **kwargs))
    except Exception as exc:  # noqa: BLE001 - tool boundary: errors go back as text
        return f"Error: {str(exc)}"
