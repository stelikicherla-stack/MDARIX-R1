"""Provider API contract primitives used by all external connectors.

Transport is intentionally independent of FastAPI and persistence.  Callers
provide a request function in tests or use ``fetch_page`` in production.  No
credential value is ever included in returned diagnostics.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlparse
from urllib.request import Request, urlopen


RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}


@dataclass(frozen=True)
class ProviderFailure:
    category: str
    code: str
    retryable: bool
    status: int | None = None
    retry_after_seconds: float | None = None

    def safe_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def normalize_failure(error: Exception) -> ProviderFailure:
    if isinstance(error, HTTPError):
        status = int(error.code)
        category = "RATE_LIMIT" if status == 429 else "AUTHENTICATION" if status in {401, 403} else "PROVIDER_HTTP"
        retry_after = None
        value = error.headers.get("Retry-After")
        if value:
            try:
                retry_after = float(value)
            except ValueError:
                try:
                    retry_after = max(0.0, (parsedate_to_datetime(value).timestamp() - time.time()))
                except (TypeError, ValueError, OverflowError):
                    retry_after = None
        return ProviderFailure(category, f"HTTP_{status}", status in RETRYABLE_STATUS, status, retry_after)
    if isinstance(error, TimeoutError):
        return ProviderFailure("TIMEOUT", "PROVIDER_TIMEOUT", True)
    if isinstance(error, URLError):
        return ProviderFailure("CONNECTIVITY", "PROVIDER_UNREACHABLE", True)
    if isinstance(error, (json.JSONDecodeError, UnicodeError)):
        return ProviderFailure("PROVIDER_SCHEMA", "INVALID_JSON", False)
    return ProviderFailure("UNKNOWN", "PROVIDER_REQUEST_FAILED", False)


def idempotency_key(tenant_id: str, provider: str, entity: str, record: dict[str, Any]) -> str:
    identity = {
        "tenant_id": tenant_id,
        "provider": provider.upper(),
        "entity": entity,
        "external_id": str(record.get("external_id") or record.get("id") or ""),
        "version": str(record.get("record_version") or record.get("version") or ""),
        "payload": record,
    }
    return hashlib.sha256(json.dumps(identity, sort_keys=True, default=str).encode()).hexdigest()


def schema_fingerprint(fields: list[str] | set[str]) -> str:
    return hashlib.sha256(json.dumps(sorted(set(fields))).encode()).hexdigest()


def compare_schema(expected: list[str] | set[str], actual: list[str] | set[str]) -> dict[str, Any]:
    expected_set, actual_set = set(expected), set(actual)
    missing, added = sorted(expected_set - actual_set), sorted(actual_set - expected_set)
    return {"status": "MATCH" if not missing and not added else "DRIFT", "missing": missing, "added": added, "fingerprint": schema_fingerprint(actual_set)}


def _request(url: str, headers: dict[str, str], timeout: float) -> tuple[int, dict[str, str], bytes]:
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=timeout) as response:
        return int(response.status), dict(response.headers.items()), response.read(5_000_001)


def fetch_page(
    endpoint: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    limit: int = 100,
    cursor: str | None = None,
    since: str | None = None,
    timeout: float = 10.0,
    max_attempts: int = 3,
    request_fn: Callable[[str, dict[str, str], float], tuple[int, dict[str, str], bytes]] = _request,
) -> dict[str, Any]:
    """Fetch one bounded page with cursor propagation and safe retry metadata."""
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("CONNECTOR_ENDPOINT_INVALID")
    url = urljoin(endpoint.rstrip("/") + "/", path.lstrip("/"))
    query = {"limit": max(1, min(int(limit), 500))}
    if cursor is not None:
        query["cursor"] = cursor
    if since:
        query["since"] = since
    url = f"{url}?{urlencode(query)}"
    request_headers = {"Accept": "application/json", **(headers or {})}
    attempts = 0
    while attempts < max(1, max_attempts):
        attempts += 1
        try:
            status, response_headers, raw = request_fn(url, request_headers, timeout)
            if len(raw) > 5_000_000:
                raise ValueError("PROVIDER_RESPONSE_TOO_LARGE")
            body = json.loads(raw.decode("utf-8"))
            if not isinstance(body, dict):
                raise json.JSONDecodeError("object required", raw.decode("utf-8"), 0)
            body["_contract"] = {"attempts": attempts, "http_status": status, "next_cursor": body.get("next_cursor")}
            return body
        except Exception as error:
            failure = normalize_failure(error)
            if not failure.retryable or attempts >= max_attempts:
                raise RuntimeError(json.dumps({"code": failure.code, "category": failure.category, "retryable": failure.retryable, "attempts": attempts})) from error
            delay = failure.retry_after_seconds if failure.retry_after_seconds is not None else min(2 ** (attempts - 1), 8)
            time.sleep(delay)
    raise RuntimeError("PROVIDER_REQUEST_FAILED")


def iter_pages(*args: Any, **kwargs: Any):
    cursor = kwargs.pop("cursor", None)
    while True:
        page = fetch_page(*args, cursor=cursor, **kwargs)
        yield page
        cursor = page.get("next_cursor")
        if cursor in (None, ""):
            break
