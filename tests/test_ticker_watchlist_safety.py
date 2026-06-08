"""Tests for ticker watchlist safety guards."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_ticker_watchlist_forces_dry_run_environment():
    """Test that importing ticker_watchlist forces dry-run environment variables."""
    # Import (may already be imported in this test session)
    import scripts.ticker_watchlist
    import importlib

    # Clear environment before reload
    os.environ.pop("ROSS_DRY_RUN", None)
    os.environ.pop("ALERT_ENABLE_TELEGRAM", None)
    os.environ.pop("ALERT_ENABLE_EMAIL", None)

    # Reload module to re-execute environment setting code
    importlib.reload(scripts.ticker_watchlist)

    # Should set safety environment variables
    assert os.environ.get("ROSS_DRY_RUN") == "true"
    assert os.environ.get("ALERT_ENABLE_TELEGRAM") == "false"
    assert os.environ.get("ALERT_ENABLE_EMAIL") == "false"


def test_ticker_watchlist_overrides_existing_alert_settings():
    """Test that ticker_watchlist overrides any existing alert settings."""
    # Set dangerous values before import
    os.environ["ROSS_DRY_RUN"] = "false"
    os.environ["ALERT_ENABLE_TELEGRAM"] = "true"
    os.environ["ALERT_ENABLE_EMAIL"] = "true"

    # Reload the module to re-execute the environment override
    import scripts.ticker_watchlist
    import importlib
    importlib.reload(scripts.ticker_watchlist)

    # Should be overridden to safe values
    assert os.environ.get("ROSS_DRY_RUN") == "true"
    assert os.environ.get("ALERT_ENABLE_TELEGRAM") == "false"
    assert os.environ.get("ALERT_ENABLE_EMAIL") == "false"


def test_watchlist_summary_dry_run_marker():
    """Test that watchlist summary includes DRY-RUN marker."""
    from scripts.ticker_watchlist import generate_markdown_summary

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

    # Summary should clearly indicate dry-run mode
    assert "DRY-RUN" in summary
    assert "No Telegram or email was sent" in summary


def test_watchlist_summary_does_not_mention_alerts_sent():
    """Test that watchlist summary explicitly states no alerts sent."""
    from scripts.ticker_watchlist import generate_markdown_summary

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

    # Should not contain evidence of alerts being sent
    assert "Telegram message sent" not in summary
    assert "Email sent" not in summary
    assert "Alert sent" not in summary

    # Should contain explicit confirmation
    assert "No Telegram messages sent" in summary
    assert "No email sent" in summary


def test_watchlist_summary_excludes_private_spreadsheet():
    """Test that watchlist summary confirms private spreadsheet not used."""
    from scripts.ticker_watchlist import generate_markdown_summary

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

    # Should explicitly confirm private spreadsheet not used
    assert "Roger's OpenInsider spreadsheet was not used" in summary or "OpenInsider spreadsheet not used" in summary


def test_watchlist_json_confirms_no_alerts():
    """Test that JSON output confirms no alerts sent."""
    from scripts.ticker_watchlist import generate_json_output

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

    # JSON should explicitly state no alerts
    assert json_data["mode"] == "manual_watchlist_dry_run"
    assert json_data["alerts_sent"] is False
