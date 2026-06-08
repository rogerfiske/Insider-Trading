"""Tests for ticker drilldown Form 4 filing limit parameter."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ticker_drilldown import generate_ticker_report


def test_default_max_form4_filings_is_unlimited():
    """Test that default behavior parses all Form 4 filings (unlimited)."""
    # Generate report without max_form4_filings parameter (should use default of 0 = unlimited)
    report = generate_ticker_report("MAIA", lookback_days=1460)

    # Report should parse all 214 filings, not be limited to 10
    assert "Parsed: 214 filings successfully" in report or "Parsed 214 Form 4 filing(s)" in report
    assert "214/214" not in report or "214 filings" in report


def test_max_form4_filings_zero_means_unlimited():
    """Test that max_form4_filings=0 explicitly means unlimited."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=0)

    # Should parse all 214 filings
    assert "Parsed: 214 filings successfully" in report or "Parsed 214 Form 4 filing(s)" in report
    assert "Total filings parsed: 214" in report


def test_max_form4_filings_limits_parsing():
    """Test that max_form4_filings parameter limits number of filings parsed."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=10)

    # Should parse only 10 filings
    assert "Total filings parsed: 10" in report
    # Should not parse all 214
    assert "Total filings parsed: 214" not in report


def test_max_form4_filings_one_parses_single_filing():
    """Test that max_form4_filings=1 parses only one filing."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=1)

    # Should parse only 1 filing
    assert "Total filings parsed: 1" in report
    assert "Total filings parsed: 10" not in report
    assert "Total filings parsed: 214" not in report


def test_max_form4_filings_larger_than_available():
    """Test that max_form4_filings larger than available filings parses all available."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=1000)

    # Should parse all 214 available filings (not fail trying to get 1000)
    assert "Total filings parsed: 214" in report
    assert "Total filings parsed: 1000" not in report
