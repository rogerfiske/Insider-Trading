"""Tests for SEC common utilities -- user-agent, rate limiting, caching."""

from __future__ import annotations

import json
import os
import time
from unittest.mock import MagicMock, patch

from sources.sec_common import (
    _cache_key,
    _read_cache,
    _write_cache,
    get_user_agent,
    sec_fetch,
    utcnow_iso,
)


class TestGetUserAgent:
    def test_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            ua = get_user_agent()
            assert "InsiderRoutines" in ua
            assert "configure" in ua  # Should indicate it needs configuration

    def test_from_env(self) -> None:
        with patch.dict(
            os.environ, {"SEC_USER_AGENT": "MyApp/2.0 (test@test.com)"}
        ):
            ua = get_user_agent()
            assert ua == "MyApp/2.0 (test@test.com)"


class TestCaching:
    def test_cache_key_deterministic(self) -> None:
        key1 = _cache_key("https://example.com/a")
        key2 = _cache_key("https://example.com/a")
        assert key1 == key2

    def test_cache_key_different_urls(self) -> None:
        key1 = _cache_key("https://example.com/a")
        key2 = _cache_key("https://example.com/b")
        assert key1 != key2

    def test_write_and_read_cache(self, tmp_path: object) -> None:
        with patch("sources.sec_common._cache_dir", return_value=tmp_path):
            _write_cache("https://test.com", '{"data": "test"}')
            result = _read_cache("https://test.com", max_age_seconds=3600)
            assert result == '{"data": "test"}'

    def test_read_cache_expired(self, tmp_path: object) -> None:
        with patch("sources.sec_common._cache_dir", return_value=tmp_path):
            _write_cache("https://test.com", '{"data": "test"}')
            # Expired cache (0 seconds max age)
            result = _read_cache("https://test.com", max_age_seconds=0)
            assert result is None

    def test_read_cache_missing(self, tmp_path: object) -> None:
        with patch("sources.sec_common._cache_dir", return_value=tmp_path):
            result = _read_cache("https://nonexistent.com", max_age_seconds=3600)
            assert result is None


class TestSecFetch:
    def test_success(self) -> None:
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"status": "ok"}'
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch("sources.sec_common._read_cache", return_value=None),
            patch("sources.sec_common.urllib.request.urlopen", return_value=mock_response),
            patch("sources.sec_common._write_cache"),
            patch("sources.sec_common._rate_limit"),
        ):
            result = sec_fetch("https://test.com")
            assert result["ok"] is True
            assert result["status"] == 200

    def test_cached_response(self) -> None:
        with patch(
            "sources.sec_common._read_cache",
            return_value='{"cached": true}',
        ):
            result = sec_fetch("https://test.com")
            assert result["ok"] is True
            assert result["from_cache"] is True
            assert result["body"] == '{"cached": true}'

    def test_http_error(self) -> None:
        import urllib.error

        with (
            patch("sources.sec_common._read_cache", return_value=None),
            patch(
                "sources.sec_common.urllib.request.urlopen",
                side_effect=urllib.error.HTTPError(
                    "https://test.com", 403, "Forbidden", {}, None
                ),
            ),
            patch("sources.sec_common._rate_limit"),
        ):
            result = sec_fetch("https://test.com")
            assert result["ok"] is False
            assert result["status"] == 403
            assert "403" in result["error"]

    def test_timeout(self) -> None:
        with (
            patch("sources.sec_common._read_cache", return_value=None),
            patch(
                "sources.sec_common.urllib.request.urlopen",
                side_effect=TimeoutError,
            ),
            patch("sources.sec_common._rate_limit"),
        ):
            result = sec_fetch("https://test.com")
            assert result["ok"] is False
            assert "Timeout" in result["error"]


class TestUtcnowIso:
    def test_returns_string(self) -> None:
        ts = utcnow_iso()
        assert isinstance(ts, str)
        assert "T" in ts
