"""CAS Common Chemistry API data access layer.

Wraps the three official endpoints (``/search``, ``/detail``, ``/export``)
documented by CAS Common Chemistry. Authentication uses the ``X-Api-Key``
header with the API token from the ``CAS_COMMON_CHEMISTRY_API_KEY`` environment
variable (loaded from ``.env`` when present).

Probing notes (2026-08-08, live against commonchemistry.cas.org):
- Header name is case-insensitive; ``X-Api-Key`` works (server error message
  prints ``X-API-KEY``).
- ``/search`` returns ``count`` (int) and ``results`` with ``rn`` / ``name`` /
  ``images`` (list of SVG strings). Names and formulas may contain HTML markup
  (e.g. ``<em>``, ``<sub>``) which this client strips for tool output.
- ``/detail`` returns ``inchiKey`` with an ``InChIKey=`` prefix and
  ``molecularFormula`` as HTML; ``smile`` may be empty while
  ``canonicalSmile`` holds the value; ``hasMolfile`` indicates export support.
- ``/export`` requires the exact ``uri`` returned by ``/detail`` (a guessed
  URI 404s); returns a V2000 molfile as ``text/plain``.
"""

import os
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from .utils import strip_html

BASE_URL = "https://commonchemistry.cas.org/api"
API_KEY_ENV = "CAS_COMMON_CHEMISTRY_API_KEY"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 2
MAX_PAGE_SIZE = 100


class CasApiError(RuntimeError):
    """Raised when the CAS Common Chemistry API returns an error status."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def _api_key() -> str:
    """Return the CAS API key from the environment (loading .env if present)."""
    load_dotenv()
    key = os.environ.get(API_KEY_ENV, "").strip()
    if not key:
        raise RuntimeError(
            f"环境变量 {API_KEY_ENV} 未配置：请在项目根目录 .env 中设置 CAS Common Chemistry API key"
        )
    return key


def _headers() -> Dict[str, str]:
    return {"X-Api-Key": _api_key(), "Accept": "application/json"}


def _get(path: str, params: Optional[Dict[str, Any]] = None, text: bool = False) -> requests.Response:
    """GET an endpoint with retries on transient failures, raising CasApiError on errors."""
    url = f"{BASE_URL}/{path}"
    headers = _headers()
    last_exc: Optional[Exception] = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES:
                time.sleep(1 + attempt)
                continue
            if resp.status_code >= 400:
                raise CasApiError(resp.status_code, _error_message(resp.status_code, resp.text))
            return resp
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                time.sleep(1 + attempt)
                continue
            raise RuntimeError(f"CAS API 网络请求失败（{type(exc).__name__}），请稍后重试") from exc
    raise RuntimeError(f"CAS API 请求失败：{last_exc}")


def _error_message(status: int, body: str) -> str:
    """Build a user-friendly message for a non-2xx CAS API response."""
    try:
        detail = body.strip()
        if detail.startswith("{"):
            import json as _json

            parsed = _json.loads(detail)
            detail = str(parsed.get("message") or parsed.get("error") or detail)
    except Exception:
        detail = body.strip()[:200]
    if status == 400:
        return f"请求参数无效（HTTP 400）：{detail}"
    if status == 403:
        return f"API key 无效或未授权（HTTP 403），请检查 .env 中的 {API_KEY_ENV}"
    if status == 404:
        return f"未找到该物质或资源不存在（HTTP 404）：{detail}"
    if status == 429:
        return "CAS API 限流（HTTP 429），请稍后重试"
    return f"CAS API 服务端错误（HTTP {status}）：{detail}"


def _normalize_inchi(value: str) -> str:
    """Add the ``InChI=`` prefix if missing (both forms are accepted by /search)."""
    return value if value.startswith("InChI=") else f"InChI={value}"


def _normalize_inchikey(value: str) -> str:
    """Add the ``InChIKey=`` prefix if missing (required by /search in practice)."""
    return value if value.upper().startswith("INCHIKEY=") else f"InChIKey={value}"


def _clean_substance(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a search-result / detail record for tool output."""
    out = dict(item)
    if "name" in out:
        out["name"] = strip_html(str(out["name"]))
    if "molecularFormula" in out:
        out["molecularFormula"] = strip_html(str(out["molecularFormula"]))
    return out


def search(q: str, offset: int = 0, size: int = 10) -> Dict[str, Any]:
    """Search the Common Chemistry data source by CAS RN / SMILES / InChI /
    InChIKey / name (with trailing wildcard support)."""
    if not q or not q.strip():
        raise ValueError("搜索词 q 不能为空")
    if offset < 0:
        raise ValueError("offset 必须 >= 0")
    if not 1 <= size <= MAX_PAGE_SIZE:
        raise ValueError(f"size 必须在 1~{MAX_PAGE_SIZE} 之间")
    query = q.strip()
    if query.lower().startswith("inchi=") or query.lower().startswith("inchi/"):
        query = _normalize_inchi(query)
    elif query.upper().startswith("INCHIKEY="):
        query = _normalize_inchikey(query)
    elif _looks_like_plain_inchikey(query):
        # Plain InChIKey (e.g. WSFSSNUMVMOOMR-UHFFFAOYSA-N): the API requires
        # the InChIKey= prefix in practice, so add it for the user.
        query = _normalize_inchikey(query)
    resp = _get("search", {"q": query, "offset": offset, "size": size})
    payload = resp.json()
    results = [_clean_substance(item) for item in payload.get("results", [])]
    return {
        "q": query,
        "offset": offset,
        "size": size,
        "returned": len(results),
        "count": payload.get("count"),
        "results": results,
    }


def _looks_like_plain_inchikey(value: str) -> bool:
    """Heuristic: 14 uppercase alphanumerics, dash, 9 alphanumerics, dash, 1 char."""
    parts = value.split("-")
    if len(parts) != 3:
        return False
    head, middle, tail = parts
    if len(head) != 14 or len(middle) != 9 or len(tail) != 1:
        return False
    return head.isalnum() and head.isupper() and middle.isalnum() and tail.isalnum()


def detail(cas_rn: Optional[str] = None, uri: Optional[str] = None) -> Dict[str, Any]:
    """Get full substance details by CAS RN or URI (exactly one required)."""
    if bool(cas_rn) == bool(uri):
        raise ValueError("cas_rn 与 uri 必须且只能提供一个")
    params = {"cas_rn": cas_rn} if cas_rn else {"uri": uri}
    resp = _get("detail", params)
    return _clean_substance(resp.json())


def export(uri: str) -> str:
    """Get the molfile (V2000 text) for the substance identified by ``uri``."""
    if not uri or not uri.strip():
        raise ValueError("uri 不能为空")
    resp = _get("export", {"uri": uri}, text=True)
    return resp.text


def export_by_casrn(cas_rn: str) -> str:
    """Two-step convenience: detail by CAS RN, then export the molfile by URI."""
    data = detail(cas_rn=cas_rn)
    uri = data.get("uri") or ""
    if not uri:
        raise ValueError(f"CAS RN {cas_rn} 的 detail 响应缺少 uri，无法导出 molfile")
    if data.get("hasMolfile") is False:
        raise ValueError(f"CAS RN {cas_rn} 没有可导出的 molfile（hasMolfile=false）")
    return export(uri)
