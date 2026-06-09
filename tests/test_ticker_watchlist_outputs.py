"""Tests for ticker watchlist output generation."""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ticker_watchlist import (
    generate_markdown_summary,
    generate_json_output,
    extract_ticker_metrics,
)


def test_generate_markdown_summary_structure():
    """Test that markdown summary has required sections."""
    ticker_metrics = [
        {
            "ticker": "MAIA",
            "cik": "0001878313",
            "company_name": "MAIA Biotechnology, Inc.",
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
            "purchase_count": 134,
            "purchase_value": 4921437.58,
            "sale_count": 0,
            "net_purchase_value": 4921437.58,
        }
    ]

    summary = generate_markdown_summary(
        ticker_metrics=ticker_metrics,
        lookback_days=1460,
        max_form4_filings=0,
        tickers_requested=1,
        tickers_resolved=1,
        tickers_failed=0,
    )

    # Check required sections
    assert "# Manual Ticker Watchlist Summary" in summary
    assert "**Mode**: DRY-RUN" in summary
    assert "## Data Sources" in summary
    assert "SEC EDGAR API" in summary
    assert "Roger's OpenInsider spreadsheet was not used" in summary
    assert "## Ranked Watchlist" in summary
    assert "## Per-Ticker Reports" in summary
    assert "## Ranking Method" in summary
    assert "## Safety Confirmations" in summary
    assert "No Telegram messages sent" in summary
    assert "No email sent" in summary
    assert "## Disclaimer" in summary
    assert "not trading advice" in summary


def test_generate_json_output_schema():
    """Test that JSON output has required schema."""
    ticker_metrics = [
        {
            "ticker": "MAIA",
            "cik": "0001878313",
            "company_name": "MAIA Biotechnology, Inc.",
            "eddie_status": "APPLICABLE_WITH_EVIDENCE",
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
            "maggie_status": "APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING",
            "maggie_signal": "NEUTRAL",
            "maggie_confidence": 1,
            "form4_filings_found": 214,
            "form4_filings_parsed": 214,
            "transactions_extracted": 136,
            "purchase_count": 134,
            "purchase_value": 4921437.58,
            "sale_count": 0,
            "sale_value": 0.0,
            "net_purchase_value": 4921437.58,
        }
    ]

    json_data = generate_json_output(
        ticker_metrics=ticker_metrics,
        lookback_days=1460,
        max_form4_filings=0,
    )

    # Check required top-level fields
    assert "generated_at" in json_data
    assert "mode" in json_data
    assert json_data["mode"] == "manual_watchlist_dry_run"
    assert "lookback_days" in json_data
    assert json_data["lookback_days"] == 1460
    assert "max_form4_filings" in json_data
    assert "data_sources" in json_data
    assert "SEC EDGAR" in json_data["data_sources"]
    assert "alerts_sent" in json_data
    assert json_data["alerts_sent"] is False
    assert "tickers" in json_data
    assert len(json_data["tickers"]) == 1

    # Check ticker fields
    ticker = json_data["tickers"][0]
    assert ticker["ticker"] == "MAIA"
    assert ticker["cik"] == "0001878313"
    assert ticker["company_name"] == "MAIA Biotechnology, Inc."
    assert ticker["eddie_status"] == "APPLICABLE_WITH_EVIDENCE"
    assert ticker["eddie_signal"] == "BULLISH_EVIDENCE"
    assert ticker["eddie_confidence"] == 2
    assert ticker["purchase_count"] == 134
    assert ticker["purchase_value"] == 4921437.58
    assert "report_path" in ticker


def test_extract_ticker_metrics_from_report(monkeypatch):
    """Test extracting metrics from ticker report markdown."""
    # Mock the structured extraction to avoid SEC network calls in unit tests
    def mock_extract_structured(ticker, lookback_days, max_form4_filings):
        return {
            "form4_filings_found": 214,
            "form4_filings_parsed": 214,
            "transactions_extracted": 136,
            "purchase_count": 134,
            "purchase_value": 4921437.58,
            "sale_count": 0,
            "sale_value": 0.0,
            "distinct_buyers": 10,
            "distinct_buyer_names": ["Buyer 1", "Buyer 2"],
            "distinct_sellers": 0,
            "distinct_seller_names": [],
            "latest_purchase_date": "2026-06-01",
            "latest_sale_date": None,
            "buyer_roles": ["CEO", "CFO"],
            "seller_roles": [],
            "purchase_months": ["2022-07", "2023-01"],
            "sale_months": [],
        }

    monkeypatch.setattr(
        "scripts.ticker_watchlist.extract_structured_transaction_metrics",
        mock_extract_structured,
    )

    # Sample report content (simplified)
    report_content = """
**CIK**: 0001878313
**Company Name**: MAIA Biotechnology, Inc.

| Eddie | APPLICABLE_WITH_EVIDENCE | ... | BULLISH_EVIDENCE | 2 | ... |
| Maggie | APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING | ... | NEUTRAL | 1 | ... |

- Found: 214 Form 4 filings
- Parsed: 214 Form 4 filings
- Transactions: 136 transaction(s)
- Open-market purchases: 134 transaction(s), $4,921,437.58
- Open-market sales: 0 transaction(s), $0.00
"""

    metrics = extract_ticker_metrics(report_content, "MAIA", lookback_days=365, max_form4_filings=0)

    assert metrics["ticker"] == "MAIA"
    assert metrics["cik"] == "0001878313"
    assert metrics["company_name"] == "MAIA Biotechnology, Inc."
    assert metrics["eddie_status"] == "APPLICABLE_WITH_EVIDENCE"
    assert metrics["eddie_signal"] == "BULLISH_EVIDENCE"
    assert metrics["eddie_confidence"] == 2
    assert metrics["maggie_status"] == "APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING"
    assert metrics["maggie_signal"] == "NEUTRAL"
    assert metrics["maggie_confidence"] == 1
    assert metrics["form4_filings_found"] == 214
    assert metrics["form4_filings_parsed"] == 214
    assert metrics["transactions_extracted"] == 136
    assert metrics["purchase_count"] == 134
    assert metrics["purchase_value"] == 4921437.58
    assert metrics["sale_count"] == 0
    assert metrics["net_purchase_value"] == 4921437.58


def test_json_output_serializable():
    """Test that JSON output can be serialized."""
    ticker_metrics = [
        {
            "ticker": "MAIA",
            "cik": "0001878313",
            "company_name": "MAIA Biotechnology, Inc.",
            "eddie_status": "APPLICABLE_WITH_EVIDENCE",
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
            "maggie_status": "APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING",
            "maggie_signal": "NEUTRAL",
            "maggie_confidence": 1,
            "form4_filings_found": 214,
            "form4_filings_parsed": 214,
            "transactions_extracted": 136,
            "purchase_count": 134,
            "purchase_value": 4921437.58,
            "sale_count": 0,
            "sale_value": 0.0,
            "net_purchase_value": 4921437.58,
        }
    ]

    json_data = generate_json_output(
        ticker_metrics=ticker_metrics,
        lookback_days=1460,
        max_form4_filings=0,
    )

    # Should be able to serialize to JSON string
    json_str = json.dumps(json_data, indent=2)
    assert isinstance(json_str, str)
    assert "MAIA" in json_str

    # Should be able to deserialize back
    parsed = json.loads(json_str)
    assert parsed["mode"] == "manual_watchlist_dry_run"
    assert len(parsed["tickers"]) == 1
