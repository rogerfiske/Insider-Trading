"""Tests for ticker drilldown safety guards (no Telegram/email, dry-run enforcement)."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_ticker_drilldown_forces_dry_run_environment():
    """Test that importing ticker_drilldown forces dry-run environment variables."""
    # Import (may already be imported in this test session)
    import scripts.ticker_drilldown
    import importlib

    # Clear environment before reload
    os.environ.pop("ROSS_DRY_RUN", None)
    os.environ.pop("ALERT_ENABLE_TELEGRAM", None)
    os.environ.pop("ALERT_ENABLE_EMAIL", None)

    # Reload module to re-execute environment setting code
    importlib.reload(scripts.ticker_drilldown)

    # Should set safety environment variables
    assert os.environ.get("ROSS_DRY_RUN") == "true"
    assert os.environ.get("ALERT_ENABLE_TELEGRAM") == "false"
    assert os.environ.get("ALERT_ENABLE_EMAIL") == "false"


def test_ticker_drilldown_overrides_existing_alert_settings():
    """Test that ticker_drilldown overrides any existing alert settings."""
    # Set dangerous values before import
    os.environ["ROSS_DRY_RUN"] = "false"
    os.environ["ALERT_ENABLE_TELEGRAM"] = "true"
    os.environ["ALERT_ENABLE_EMAIL"] = "true"

    # Reload the module to re-execute the environment override
    import scripts.ticker_drilldown
    import importlib
    importlib.reload(scripts.ticker_drilldown)

    # Should be overridden to safe values
    assert os.environ.get("ROSS_DRY_RUN") == "true"
    assert os.environ.get("ALERT_ENABLE_TELEGRAM") == "false"
    assert os.environ.get("ALERT_ENABLE_EMAIL") == "false"


def test_manual_ticker_report_dry_run_marker():
    """Test that manual ticker report includes DRY-RUN marker."""
    from scripts.ticker_drilldown import generate_ticker_report

    report = generate_ticker_report("MAIA", lookback_days=365, max_form4_filings=10)

    # Report should clearly indicate dry-run mode
    assert "DRY-RUN" in report
    assert "No Telegram or email was sent" in report


def test_manual_ticker_report_does_not_send_alerts():
    """Test that manual ticker report explicitly states no alerts sent."""
    from scripts.ticker_drilldown import generate_ticker_report

    report = generate_ticker_report("MAIA", lookback_days=365, max_form4_filings=10)

    # Should not contain evidence of alerts being sent
    assert "Telegram message sent" not in report
    assert "Email sent" not in report
    assert "Alert sent" not in report

    # Should contain explicit confirmation
    assert "DRY-RUN" in report or "No Telegram or email was sent" in report


def test_ticker_drilldown_safety_disclaimer():
    """Test that ticker drilldown includes informational-only disclaimer."""
    from scripts.ticker_drilldown import generate_ticker_report

    report = generate_ticker_report("MAIA", lookback_days=365, max_form4_filings=10)

    # Should include safety disclaimer
    assert "informational only" in report.lower() or "not trading advice" in report.lower()
    assert "disclaimer" in report.lower()
