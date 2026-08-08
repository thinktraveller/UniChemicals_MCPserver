"""Shared helpers: safe execution and JSON serialization for tool output."""

import json
from typing import Any, Callable


def to_json_safe(result: Any) -> str:
    """Serialize PubChemPy objects (with ``to_dict``) or plain data to a JSON string."""
    if hasattr(result, "to_dict"):
        try:
            return json.dumps(result.to_dict(), indent=2)
        except Exception:
            # PubChemPy's to_dict can crash on records with missing optional
            # fields (e.g. fingerprint on 3D records); fall back to attributes.
            return json.dumps(_json_default(result), indent=2)
    if isinstance(result, list) and result and hasattr(result[0], "to_dict"):
        try:
            return json.dumps([item.to_dict() for item in result], indent=2)
        except Exception:
            return json.dumps([_json_default(item) for item in result], indent=2)
    return json.dumps(result, indent=2, default=_json_default)


def _json_default(obj: Any) -> Any:
    """JSON serializer fallback for objects with ``__dict__`` (e.g. pubchempy Atom/Bond)."""
    if hasattr(obj, "__dict__"):
        return {key: _json_default(value) for key, value in vars(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [_json_default(value) for value in obj]
    if isinstance(obj, dict):
        return {key: _json_default(value) for key, value in obj.items()}
    return str(obj)


def safe_execute(func: Callable, *args: Any, **kwargs: Any) -> str:
    """Run ``func`` and return its JSON string; on any exception return ``Error: ...``."""
    try:
        return to_json_safe(func(*args, **kwargs))
    except Exception as exc:  # noqa: BLE001 - tool boundary: errors go back as text
        return f"Error: {str(exc)}"
