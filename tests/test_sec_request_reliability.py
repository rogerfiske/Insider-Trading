"""Tests for SEC request reliability (retry logic, user-agent, timeout)."""

import sys
import time
import urllib.error
from pathlib import Path
from unittest import mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sources.sec_common import (
    sec_fetch,
    get_user_agent,
    _is_retryable_error,
    _sec_fetch_once,
)


def test_get_user_agent_from_environment(monkeypatch):
    """Test that user-agent is read from SEC_USER_AGENT environment variable."""
    test_agent = "TestBot/1.0 (test@example.com)"
    monkeypatch.setenv("SEC_USER_AGENT", test_agent)

    assert get_user_agent() == test_agent


def test_get_user_agent_default():
    """Test that user-agent has a default when SEC_USER_AGENT is not set."""
    # Clear the environment variable if it exists
    import os
    os.environ.pop("SEC_USER_AGENT", None)

    agent = get_user_agent()
    assert "InsiderRoutines" in agent
    assert len(agent) > 10


def test_is_retryable_error_rate_limiting():
    """Test that 429 rate limiting errors are retryable."""
    assert _is_retryable_error(429, "Too Many Requests") is True


def test_is_retryable_error_server_errors():
    """Test that 5xx server errors are retryable."""
    assert _is_retryable_error(500, "Internal Server Error") is True
    assert _is_retryable_error(502, "Bad Gateway") is True
    assert _is_retryable_error(503, "Service Unavailable") is True
    assert _is_retryable_error(504, "Gateway Timeout") is True


def test_is_retryable_error_network_failures():
    """Test that network failures (status 0) are retryable."""
    assert _is_retryable_error(0, "Network error") is True


def test_is_retryable_error_non_retryable():
    """Test that client errors and success are not retryable."""
    assert _is_retryable_error(200, None) is False
    assert _is_retryable_error(404, "Not Found") is False
    assert _is_retryable_error(400, "Bad Request") is False
    assert _is_retryable_error(403, "Forbidden") is False


def test_sec_fetch_retry_on_429():
    """Test that sec_fetch retries on 429 rate limiting."""
    # Mock urllib to return 429 twice, then 200
    call_count = 0

    def mock_urlopen(req, timeout=None):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise urllib.error.HTTPError(
                req.full_url, 429, "Too Many Requests", {}, None
            )
        # Third attempt succeeds
        return mock.Mock(
            status=200,
            read=lambda: b'{"test": "data"}',
            __enter__=lambda self: self,
            __exit__=lambda *args: None,
        )

    with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
        with mock.patch("sources.sec_common._read_cache", return_value=None):
            with mock.patch("sources.sec_common._write_cache"):
                with mock.patch("time.sleep"):  # Skip backoff delays in tests
                    result = sec_fetch(
                        "https://data.sec.gov/test.json",
                        cache_max_age=0,
                        max_retries=3,
                    )

    assert result["ok"] is True
    assert result["retry_count"] == 2  # Failed twice, succeeded on third
    assert call_count == 3


def test_sec_fetch_exhausts_retries():
    """Test that sec_fetch stops after max retries."""

    def mock_urlopen(req, timeout=None):
        raise urllib.error.HTTPError(
            req.full_url, 503, "Service Unavailable", {}, None
        )

    with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
        with mock.patch("sources.sec_common._read_cache", return_value=None):
            with mock.patch("time.sleep"):  # Skip backoff delays in tests
                result = sec_fetch(
                    "https://data.sec.gov/test.json",
                    cache_max_age=0,
                    max_retries=2,
                )

    assert result["ok"] is False
    assert result["retry_count"] == 2
    assert "after 2 retries" in result["error"]


def test_sec_fetch_no_retry_on_404():
    """Test that sec_fetch does not retry on 404 (non-retryable error)."""
    call_count = 0

    def mock_urlopen(req, timeout=None):
        nonlocal call_count
        call_count += 1
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
        with mock.patch("sources.sec_common._read_cache", return_value=None):
            result = sec_fetch(
                "https://data.sec.gov/test.json",
                cache_max_age=0,
                max_retries=3,
            )

    assert result["ok"] is False
    assert result["status"] == 404
    assert result["retry_count"] == 0  # No retries for non-retryable error
    assert call_count == 1  # Only one attempt


def test_sec_fetch_includes_user_agent():
    """Test that sec_fetch includes User-Agent header."""
    captured_headers = {}

    def mock_urlopen(req, timeout=None):
        captured_headers.update(req.headers)
        return mock.Mock(
            status=200,
            read=lambda: b'{"test": "data"}',
            __enter__=lambda self: self,
            __exit__=lambda *args: None,
        )

    with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
        with mock.patch("sources.sec_common._read_cache", return_value=None):
            with mock.patch("sources.sec_common._write_cache"):
                result = sec_fetch(
                    "https://data.sec.gov/test.json",
                    cache_max_age=0,
                )

    assert result["ok"] is True
    assert "User-agent" in captured_headers
    assert "InsiderRoutines" in captured_headers["User-agent"]
