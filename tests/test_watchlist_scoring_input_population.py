"""Tests for watchlist scoring input population from Form 4 transaction details.

Verifies that structured transaction metrics (distinct buyers, latest dates, roles, months)
are correctly extracted from Form 4 data and populate scoring inputs.
"""

from datetime import datetime, timezone

import pytest

from scripts.ticker_drilldown import extract_structured_transaction_metrics


def test_extract_structured_metrics_basic():
    """Test basic extraction of structured transaction metrics."""
    # This is an integration test that requires SEC network access
    # Skip in CI/CD, run manually for validation
    pytest.skip("Integration test - requires SEC network access")

    metrics = extract_structured_transaction_metrics(
        ticker="MAIA",
        lookback_days=1460,
        max_form4_filings=10,  # Limit for faster test
    )

    # Verify required fields are present
    assert "distinct_buyers" in metrics
    assert "distinct_buyer_names" in metrics
    assert "latest_purchase_date" in metrics
    assert "buyer_roles" in metrics
    assert "purchase_months" in metrics
    assert "form4_filings_found" in metrics
    assert "form4_filings_parsed" in metrics

    # If there's actual data, verify it's populated
    if metrics["form4_filings_parsed"] > 0:
        if metrics["purchase_count"] > 0:
            assert metrics["distinct_buyers"] >= 1
            assert isinstance(metrics["distinct_buyer_names"], list)
            assert isinstance(metrics["buyer_roles"], list)
            assert isinstance(metrics["purchase_months"], list)


def test_extract_structured_metrics_no_filings():
    """Test extraction when no Form 4 filings are found."""
    # Use a ticker unlikely to have recent Form 4 filings
    metrics = extract_structured_transaction_metrics(
        ticker="INVALID_TICKER_XYZ",
        lookback_days=30,
        max_form4_filings=0,
    )

    # Verify defaults are returned when no data available
    assert metrics["distinct_buyers"] == 0
    assert metrics["distinct_buyer_names"] == []
    assert metrics["latest_purchase_date"] is None
    assert metrics["buyer_roles"] == []
    assert metrics["purchase_months"] == []
    assert metrics["form4_filings_found"] == 0
    assert metrics["form4_filings_parsed"] == 0


def test_distinct_buyer_count():
    """Test that distinct buyers are counted correctly."""
    pytest.skip("Integration test - requires SEC network access")

    metrics = extract_structured_transaction_metrics(
        ticker="MAIA",
        lookback_days=1460,
        max_form4_filings=50,
    )

    if metrics["purchase_count"] > 0:
        # Should have at least one distinct buyer
        assert metrics["distinct_buyers"] >= 1
        # Buyer names list should match count
        assert len(metrics["distinct_buyer_names"]) == metrics["distinct_buyers"]


def test_buyer_roles_extracted():
    """Test that buyer roles are extracted from owner titles."""
    pytest.skip("Integration test - requires SEC network access")

    metrics = extract_structured_transaction_metrics(
        ticker="MAIA",
        lookback_days=1460,
        max_form4_filings=50,
    )

    if metrics["purchase_count"] > 0 and metrics["buyer_roles"]:
        # Buyer roles should be a list of strings
        assert isinstance(metrics["buyer_roles"], list)
        assert all(isinstance(role, str) for role in metrics["buyer_roles"])
        # Roles should be deduplicated
        assert len(metrics["buyer_roles"]) == len(set(metrics["buyer_roles"]))


def test_purchase_months_format():
    """Test that purchase months are in YYYY-MM format."""
    pytest.skip("Integration test - requires SEC network access")

    metrics = extract_structured_transaction_metrics(
        ticker="MAIA",
        lookback_days=1460,
        max_form4_filings=50,
    )

    if metrics["purchase_months"]:
        for month in metrics["purchase_months"]:
            # Verify YYYY-MM format
            assert len(month) == 7
            assert month[4] == "-"
            # Verify it's a valid year-month
            year, mon = month.split("-")
            assert 2020 <= int(year) <= 2030
            assert 1 <= int(mon) <= 12


def test_latest_purchase_date_format():
    """Test that latest purchase date is in ISO format."""
    pytest.skip("Integration test - requires SEC network access")

    metrics = extract_structured_transaction_metrics(
        ticker="MAIA",
        lookback_days=1460,
        max_form4_filings=50,
    )

    if metrics["latest_purchase_date"]:
        # Verify ISO date format (YYYY-MM-DD)
        date_str = metrics["latest_purchase_date"]
        assert len(date_str) == 10
        assert date_str[4] == "-" and date_str[7] == "-"
        # Verify it parses as a valid date
        datetime.fromisoformat(date_str)


def test_form4_filings_counts():
    """Test that Form 4 filing counts are consistent."""
    pytest.skip("Integration test - requires SEC network access")

    metrics = extract_structured_transaction_metrics(
        ticker="MAIA",
        lookback_days=1460,
        max_form4_filings=0,
    )

    # Parsed should never exceed found
    assert metrics["form4_filings_parsed"] <= metrics["form4_filings_found"]

    # If filings were found, some should be parsed
    if metrics["form4_filings_found"] > 0:
        assert metrics["form4_filings_parsed"] >= 0


def test_scoring_integration_with_structured_metrics():
    """Test that scoring inputs are correctly populated in watchlist pipeline."""
    pytest.skip("Integration test - requires full watchlist pipeline")

    from scripts.ticker_watchlist import extract_ticker_metrics

    # Generate a mock report (would normally come from generate_ticker_report)
    report_content = """
# MAIA — Manual Ticker Drilldown Diagnostic Report

**CIK**: 0001878313

**Company Name**: MAIA Biotechnology, Inc.

| Agent | Applicability | Evidence Status | Signal | Confidence | Reason |
|-------|--------------|-----------------|--------|------------|--------|
| Eddie | APPLICABLE_WITH_EVIDENCE | Parsed 214 Form 4 filing(s) | BULLISH_EVIDENCE | 2 | Recent insider purchases |
"""

    metrics = extract_ticker_metrics(
        report_content=report_content,
        ticker="MAIA",
        lookback_days=1460,
        max_form4_filings=0,
    )

    # Verify structured metrics were populated
    assert "distinct_buyers" in metrics
    assert "buyer_roles" in metrics
    assert "purchase_months" in metrics
    assert "latest_purchase_date" in metrics
