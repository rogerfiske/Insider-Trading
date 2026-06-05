"""Tests for SEC ticker-to-CIK resolution."""

import pytest
from sources.sec_ticker import (
    SecTickerResolver,
    TickerCikResult,
    _normalize_ticker,
    resolve_ticker_to_cik,
)


def test_normalize_ticker_uppercase():
    """Test that tickers are normalized to uppercase."""
    assert _normalize_ticker("maia") == "MAIA"
    assert _normalize_ticker("Maia") == "MAIA"
    assert _normalize_ticker("MAIA") == "MAIA"


def test_normalize_ticker_whitespace():
    """Test that whitespace is trimmed."""
    assert _normalize_ticker("  MAIA  ") == "MAIA"
    assert _normalize_ticker("\tMSFT\n") == "MSFT"


def test_ticker_cik_result_success():
    """Test TickerCikResult.success factory."""
    result = TickerCikResult.success(
        ticker="MAIA",
        cik=1878313,
        company_name="MAIA Biotechnology, Inc.",
        source_url="https://www.sec.gov/files/company_tickers.json",
    )

    assert result.ok is True
    assert result.ticker == "MAIA"
    assert result.cik == 1878313
    assert result.cik_padded == "0001878313"
    assert result.company_name == "MAIA Biotechnology, Inc."
    assert result.source_url == "https://www.sec.gov/files/company_tickers.json"
    assert result.retrieved_at != ""
    assert result.error_type is None
    assert result.error_message is None


def test_ticker_cik_result_failure():
    """Test TickerCikResult.failure factory."""
    result = TickerCikResult.failure(
        ticker="INVALID",
        error_type="ticker_not_found",
        error_message="Ticker 'INVALID' not found in SEC company tickers mapping",
    )

    assert result.ok is False
    assert result.ticker == "INVALID"
    assert result.cik == 0
    assert result.cik_padded == ""
    assert result.company_name == ""
    assert result.source_url == ""
    assert result.retrieved_at != ""
    assert result.error_type == "ticker_not_found"
    assert result.error_message == "Ticker 'INVALID' not found in SEC company tickers mapping"


def test_resolve_ticker_to_cik_success():
    """Test resolving a valid ticker to CIK."""
    # Use a well-known ticker that should exist in SEC mapping
    result = resolve_ticker_to_cik("AAPL")

    # Apple should resolve successfully
    assert result.ok is True
    assert result.ticker == "AAPL"
    assert result.cik > 0
    assert result.cik_padded != ""
    assert len(result.cik_padded) == 10
    assert result.company_name != ""
    assert "apple" in result.company_name.lower()
    assert result.source_url == "https://www.sec.gov/files/company_tickers.json"
    assert result.retrieved_at != ""
    assert result.error_type is None
    assert result.error_message is None


def test_resolve_ticker_to_cik_case_insensitive():
    """Test that ticker resolution is case-insensitive."""
    result_upper = resolve_ticker_to_cik("AAPL")
    result_lower = resolve_ticker_to_cik("aapl")
    result_mixed = resolve_ticker_to_cik("Aapl")

    # All should resolve to the same CIK
    assert result_upper.ok is True
    assert result_lower.ok is True
    assert result_mixed.ok is True
    assert result_upper.cik == result_lower.cik == result_mixed.cik


def test_resolve_ticker_to_cik_invalid():
    """Test resolving an invalid ticker."""
    # Use a ticker that definitely doesn't exist
    result = resolve_ticker_to_cik("THISDOESNOTEXIST999")

    assert result.ok is False
    assert result.ticker == "THISDOESNOTEXIST999"
    assert result.cik == 0
    assert result.cik_padded == ""
    assert result.company_name == ""
    assert result.source_url == ""
    assert result.error_type == "ticker_not_found"
    assert "not found" in result.error_message.lower()


def test_sec_ticker_resolver_class():
    """Test SecTickerResolver class interface."""
    resolver = SecTickerResolver()

    # Should successfully resolve a known ticker
    result = resolver.resolve("MSFT")
    assert result.ok is True
    assert result.ticker == "MSFT"
    assert result.cik > 0
    assert "microsoft" in result.company_name.lower()


def test_cik_padding():
    """Test that CIKs are zero-padded to 10 digits."""
    result = resolve_ticker_to_cik("AAPL")

    if result.ok:
        assert len(result.cik_padded) == 10
        assert result.cik_padded[0] == "0"
        assert int(result.cik_padded) == result.cik
