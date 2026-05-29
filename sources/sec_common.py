"""Shared SEC EDGAR utilities -- user-agent, rate limiting, caching, HTTP helpers.

SEC fair-access guidance requires:
  - A descriptive User-Agent header with contact information
  - No more than 10 requests per second
  - Graceful handling of 403/429 responses
  - No aggressive crawling

This module provides a configured HTTP helper that enforces these rules.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# -- Configuration -----------------------------------------------------------

_DEFAULT_USER_AGENT = (
    "InsiderRoutines/1.0 (configure SEC_USER_AGENT in .env)"
)

_MIN_REQUEST_INTERVAL = 0.2  # 200ms -> max 5 req/sec (conservative)
_REQUEST_TIMEOUT = 30  # seconds
_CACHE_DIR_NAME = "cache"

# Module-level state for rate limiting
_last_request_time: float = 0.0


def get_user_agent() -> str:
    """Return the SEC user-agent string from environment or default."""
    return os.environ.get("SEC_USER_AGENT", _DEFAULT_USER_AGENT)


def _cache_dir() -> Path:
    """Return the cache directory, creating it if needed."""
    root = Path(__file__).resolve().parents[1]
    cache = root / ".state" / _CACHE_DIR_NAME
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def _cache_key(url: str) -> str:
    """Generate a safe cache filename from a URL."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _read_cache(url: str, max_age_seconds: int) -> str | None:
    """Read a cached response if it exists and is fresh enough."""
    cache = _cache_dir()
    key = _cache_key(url)
    data_file = cache / f"{key}.json"
    meta_file = cache / f"{key}.meta"

    if not data_file.exists() or not meta_file.exists():
        return None

    try:
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        cached_at = float(meta.get("cached_at", 0))
        if time.time() - cached_at >= max_age_seconds:
            return None
        return data_file.read_text(encoding="utf-8")
    except (json.JSONDecodeError, ValueError, OSError):
        return None


def _write_cache(url: str, body: str) -> None:
    """Write a response to the cache."""
    cache = _cache_dir()
    key = _cache_key(url)
    data_file = cache / f"{key}.json"
    meta_file = cache / f"{key}.meta"

    data_file.write_text(body, encoding="utf-8")
    meta_file.write_text(
        json.dumps({"url": url, "cached_at": time.time()}),
        encoding="utf-8",
    )


def _rate_limit() -> None:
    """Enforce minimum interval between SEC requests."""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


def sec_fetch(
    url: str,
    *,
    cache_max_age: int = 3600,
    timeout: int = _REQUEST_TIMEOUT,
    accept: str = "application/json",
) -> dict[str, Any]:
    """Fetch a URL from SEC with rate limiting, caching, and error handling.

    Returns a dict with keys:
        ok: bool
        status: int
        body: str
        error: str | None
        from_cache: bool
    """
    # Try cache first
    cached = _read_cache(url, cache_max_age)
    if cached is not None:
        return {
            "ok": True,
            "status": 200,
            "body": cached,
            "error": None,
            "from_cache": True,
        }

    # Rate limit
    _rate_limit()

    # Build request
    req = urllib.request.Request(url)
    req.add_header("User-Agent", get_user_agent())
    req.add_header("Accept", accept)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        return {
            "ok": False,
            "status": e.code,
            "body": "",
            "error": f"HTTP {e.code}: {e.reason}",
            "from_cache": False,
        }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "status": 0,
            "body": "",
            "error": f"URL error: {e.reason}",
            "from_cache": False,
        }
    except TimeoutError:
        return {
            "ok": False,
            "status": 0,
            "body": "",
            "error": f"Timeout after {timeout}s",
            "from_cache": False,
        }

    if 200 <= status < 300:
        _write_cache(url, body)
        return {
            "ok": True,
            "status": status,
            "body": body,
            "error": None,
            "from_cache": False,
        }

    return {
        "ok": False,
        "status": status,
        "body": body,
        "error": f"HTTP {status}",
        "from_cache": False,
    }


def utcnow_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()
