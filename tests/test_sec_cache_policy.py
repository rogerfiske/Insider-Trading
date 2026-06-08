"""Tests for SEC cache policy (TTL, cache hits, corruption handling)."""

import json
import sys
import time
from pathlib import Path
from unittest import mock

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sources.sec_common import (
    sec_fetch,
    _cache_dir,
    _cache_key,
    _read_cache,
    _write_cache,
)


def test_cache_dir_creation():
    """Test that cache directory is created under .state/cache/."""
    cache = _cache_dir()

    assert cache.exists()
    assert cache.is_dir()
    assert ".state" in str(cache)
    assert "cache" in str(cache)


def test_cache_key_deterministic():
    """Test that cache key is deterministic for same URL."""
    url = "https://data.sec.gov/test.json"

    key1 = _cache_key(url)
    key2 = _cache_key(url)

    assert key1 == key2
    assert len(key1) == 16  # SHA256 truncated to 16 chars


def test_cache_key_different_for_different_urls():
    """Test that different URLs produce different cache keys."""
    url1 = "https://data.sec.gov/test1.json"
    url2 = "https://data.sec.gov/test2.json"

    key1 = _cache_key(url1)
    key2 = _cache_key(url2)

    assert key1 != key2


def test_write_and_read_cache():
    """Test that cache write and read work correctly."""
    url = "https://data.sec.gov/test_cache_rw.json"
    body = '{"test": "data"}'

    # Write to cache
    _write_cache(url, body)

    # Read from cache (with long TTL)
    cached = _read_cache(url, max_age_seconds=3600)

    assert cached == body


def test_read_cache_expired():
    """Test that expired cache entries return None."""
    url = "https://data.sec.gov/test_cache_expired.json"
    body = '{"test": "data"}'

    # Write to cache
    _write_cache(url, body)

    # Read with zero TTL (should be expired)
    cached = _read_cache(url, max_age_seconds=0)

    assert cached is None


def test_read_cache_nonexistent():
    """Test that reading nonexistent cache returns None."""
    url = "https://data.sec.gov/nonexistent_cache_entry.json"

    cached = _read_cache(url, max_age_seconds=3600)

    assert cached is None


def test_read_cache_corrupted_meta():
    """Test that corrupted cache meta file is handled gracefully."""
    cache = _cache_dir()
    url = "https://data.sec.gov/test_corrupted_meta.json"
    key = _cache_key(url)

    # Write valid data file
    data_file = cache / f"{key}.json"
    data_file.write_text('{"test": "data"}', encoding="utf-8")

    # Write corrupted meta file
    meta_file = cache / f"{key}.meta"
    meta_file.write_text("not valid json", encoding="utf-8")

    # Should return None (corrupted cache)
    cached = _read_cache(url, max_age_seconds=3600)

    assert cached is None


def test_sec_fetch_cache_hit_avoids_network():
    """Test that cache hit avoids network call."""
    url = "https://data.sec.gov/test_cache_hit.json"
    body = '{"test": "cached"}'

    # Write to cache
    _write_cache(url, body)

    # Mock urllib to ensure it's not called
    with mock.patch("urllib.request.urlopen") as mock_urlopen:
        result = sec_fetch(url, cache_max_age=3600)

        # Should not have made network call
        mock_urlopen.assert_not_called()

    assert result["ok"] is True
    assert result["body"] == body
    assert result["from_cache"] is True


def test_sec_fetch_cache_miss_fetches_network():
    """Test that cache miss triggers network fetch."""
    url = "https://data.sec.gov/test_cache_miss.json"
    response_body = '{"test": "fresh"}'

    def mock_urlopen(req, timeout=None):
        return mock.Mock(
            status=200,
            read=lambda: response_body.encode("utf-8"),
            __enter__=lambda self: self,
            __exit__=lambda *args: None,
        )

    with mock.patch("urllib.request.urlopen", side_effect=mock_urlopen):
        result = sec_fetch(url, cache_max_age=0)  # cache_max_age=0 ensures miss

    assert result["ok"] is True
    assert result["body"] == response_body
    assert result["from_cache"] is False

    # Verify it was written to cache
    cached = _read_cache(url, max_age_seconds=3600)
    assert cached == response_body


def test_cache_ttl_different_for_different_resources():
    """Test that different TTLs can be used for different resource types."""
    url_short_ttl = "https://data.sec.gov/test_short_ttl.json"
    url_long_ttl = "https://data.sec.gov/test_long_ttl.json"

    body = '{"test": "data"}'

    # Write both to cache
    _write_cache(url_short_ttl, body)
    _write_cache(url_long_ttl, body)

    # Short TTL should expire quickly
    cached_short = _read_cache(url_short_ttl, max_age_seconds=0)
    assert cached_short is None

    # Long TTL should still be valid
    cached_long = _read_cache(url_long_ttl, max_age_seconds=3600)
    assert cached_long == body
