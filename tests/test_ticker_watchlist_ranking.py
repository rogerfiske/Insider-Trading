"""Tests for ticker watchlist ranking logic."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ticker_watchlist import rank_tickers


def test_rank_by_bullish_signal():
    """Test that BULLISH_EVIDENCE ranks higher than NEUTRAL."""
    ticker_metrics = [
        {
            "ticker": "NEUTRAL1",
            "eddie_signal": "NEUTRAL",
            "net_purchase_value": 1000000.0,
            "purchase_count": 10,
            "form4_filings_parsed": 100,
        },
        {
            "ticker": "BULLISH1",
            "eddie_signal": "BULLISH_EVIDENCE",
            "net_purchase_value": 500000.0,
            "purchase_count": 5,
            "form4_filings_parsed": 50,
        },
    ]

    ranked = rank_tickers(ticker_metrics)

    # BULLISH should rank first even with lower purchase value
    assert ranked[0]["ticker"] == "BULLISH1"
    assert ranked[1]["ticker"] == "NEUTRAL1"


def test_rank_by_net_purchase_value():
    """Test that higher net purchase value ranks higher within same signal."""
    ticker_metrics = [
        {
            "ticker": "LOW_VALUE",
            "eddie_signal": "BULLISH_EVIDENCE",
            "net_purchase_value": 100000.0,
            "purchase_count": 10,
            "form4_filings_parsed": 50,
        },
        {
            "ticker": "HIGH_VALUE",
            "eddie_signal": "BULLISH_EVIDENCE",
            "net_purchase_value": 5000000.0,
            "purchase_count": 10,
            "form4_filings_parsed": 50,
        },
    ]

    ranked = rank_tickers(ticker_metrics)

    # Higher value should rank first
    assert ranked[0]["ticker"] == "HIGH_VALUE"
    assert ranked[1]["ticker"] == "LOW_VALUE"


def test_rank_by_purchase_count():
    """Test that total_score is primary ranking criterion (not purchase_count)."""
    ticker_metrics = [
        {
            "ticker": "LOW_SCORE",
            "eddie_signal": "BULLISH_EVIDENCE",
            "net_purchase_value": 1000000.0,
            "purchase_count": 100,  # More purchases
            "form4_filings_parsed": 50,
            "total_score": 40.0,  # Lower score
        },
        {
            "ticker": "HIGH_SCORE",
            "eddie_signal": "BULLISH_EVIDENCE",
            "net_purchase_value": 1000000.0,
            "purchase_count": 5,  # Fewer purchases
            "form4_filings_parsed": 50,
            "total_score": 75.0,  # Higher score
        },
    ]

    ranked = rank_tickers(ticker_metrics)

    # Higher score should rank first (regardless of purchase count)
    assert ranked[0]["ticker"] == "HIGH_SCORE"
    assert ranked[1]["ticker"] == "LOW_SCORE"


def test_rank_by_data_completeness():
    """Test that total_score is primary ranking criterion (not form4_filings_parsed)."""
    ticker_metrics = [
        {
            "ticker": "LOW_SCORE_MORE_DATA",
            "eddie_signal": "BULLISH_EVIDENCE",
            "net_purchase_value": 1000000.0,
            "purchase_count": 10,
            "form4_filings_parsed": 200,  # More data
            "total_score": 42.0,  # Lower score
        },
        {
            "ticker": "HIGH_SCORE_LESS_DATA",
            "eddie_signal": "BULLISH_EVIDENCE",
            "net_purchase_value": 1000000.0,
            "purchase_count": 10,
            "form4_filings_parsed": 10,  # Less data
            "total_score": 68.0,  # Higher score
        },
    ]

    ranked = rank_tickers(ticker_metrics)

    # Higher score should rank first (regardless of data completeness)
    assert ranked[0]["ticker"] == "HIGH_SCORE_LESS_DATA"
    assert ranked[1]["ticker"] == "LOW_SCORE_MORE_DATA"


def test_rank_bearish_below_neutral():
    """Test that BEARISH_EVIDENCE ranks below NEUTRAL."""
    ticker_metrics = [
        {
            "ticker": "BEARISH1",
            "eddie_signal": "BEARISH_EVIDENCE",
            "net_purchase_value": 0.0,
            "purchase_count": 0,
            "form4_filings_parsed": 100,
        },
        {
            "ticker": "NEUTRAL1",
            "eddie_signal": "NEUTRAL",
            "net_purchase_value": 0.0,
            "purchase_count": 0,
            "form4_filings_parsed": 100,
        },
    ]

    ranked = rank_tickers(ticker_metrics)

    # NEUTRAL should rank above BEARISH
    assert ranked[0]["ticker"] == "NEUTRAL1"
    assert ranked[1]["ticker"] == "BEARISH1"


def test_rank_comprehensive():
    """Test comprehensive ranking with multiple tickers."""
    ticker_metrics = [
        {
            "ticker": "RANK3",
            "eddie_signal": "NEUTRAL",
            "net_purchase_value": 5000000.0,
            "purchase_count": 100,
            "form4_filings_parsed": 200,
        },
        {
            "ticker": "RANK1",
            "eddie_signal": "BULLISH_EVIDENCE",
            "net_purchase_value": 10000000.0,
            "purchase_count": 200,
            "form4_filings_parsed": 300,
        },
        {
            "ticker": "RANK2",
            "eddie_signal": "BULLISH_EVIDENCE",
            "net_purchase_value": 8000000.0,
            "purchase_count": 150,
            "form4_filings_parsed": 250,
        },
        {
            "ticker": "RANK4",
            "eddie_signal": "BEARISH_EVIDENCE",
            "net_purchase_value": -1000000.0,
            "purchase_count": 0,
            "form4_filings_parsed": 50,
        },
    ]

    ranked = rank_tickers(ticker_metrics)

    # Check expected ranking order
    assert ranked[0]["ticker"] == "RANK1"  # BULLISH with highest value
    assert ranked[1]["ticker"] == "RANK2"  # BULLISH with second highest value
    assert ranked[2]["ticker"] == "RANK3"  # NEUTRAL
    assert ranked[3]["ticker"] == "RANK4"  # BEARISH
