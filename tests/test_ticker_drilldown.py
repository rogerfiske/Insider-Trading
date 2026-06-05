"""Tests for ticker drilldown diagnostic script."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ticker_drilldown import generate_ticker_report


def test_generate_ticker_report_maia():
    """Test generating a ticker report for MAIA."""
    report = generate_ticker_report("MAIA")

    # Report should be non-empty
    assert len(report) > 0

    # Report should include title
    assert "MAIA — Manual Ticker Drilldown Diagnostic Report" in report

    # Report should include ticker resolution section
    assert "## Ticker Resolution" in report

    # Report should include all seven agents
    assert "## Eddie — SEC Form 4 Insider Transactions" in report
    assert "## Maggie — SEC 13F Institutional Holdings" in report
    assert "## Frank — Federal Reserve / Macro Context" in report
    assert "## Maya — On-Chain / Whale Movement" in report
    assert "## Janet — Portfolio Drift" in report
    assert "## Sophie — Consensus Aggregator" in report
    assert "## Ross — Routing / Reporting" in report

    # Report should include safety disclaimer
    assert "informational only" in report.lower()
    assert "not trading advice" in report.lower()


def test_generate_ticker_report_uppercase_normalization():
    """Test that ticker symbols are normalized to uppercase."""
    report_lower = generate_ticker_report("aapl")
    report_upper = generate_ticker_report("AAPL")

    # Both should generate reports with uppercase ticker
    assert "AAPL" in report_lower
    assert "AAPL" in report_upper


def test_generate_ticker_report_with_output_path(tmp_path):
    """Test generating report with output file."""
    output_file = tmp_path / "test_report.md"

    report = generate_ticker_report("MSFT", output_path=output_file)

    # File should be created
    assert output_file.exists()

    # File content should match returned report
    file_content = output_file.read_text(encoding="utf-8")
    assert file_content == report

    # Report should include ticker
    assert "MSFT" in report


def test_ticker_drilldown_includes_ticker_resolution():
    """Test that report includes ticker resolution status."""
    report = generate_ticker_report("AAPL")

    # Should include ticker resolution section
    assert "## Ticker Resolution" in report
    assert "**Ticker**: AAPL" in report

    # Should show resolution status (success or failure)
    assert ("✅" in report) or ("❌" in report)


def test_ticker_drilldown_does_not_use_roger_spreadsheet():
    """Test that report does not reference Roger's OpenInsider spreadsheet."""
    report = generate_ticker_report("MAIA")

    # Should explicitly state Roger's spreadsheet is excluded
    assert "Data Source Boundary" in report
    assert "OpenInsider" in report

    # Should be in the "NOT Used" section
    sources_not_used_start = report.find("**Sources NOT Used**:")
    openinsider_pos = report.find("OpenInsider")

    assert sources_not_used_start > 0
    assert openinsider_pos > sources_not_used_start


def test_ticker_drilldown_dry_run_only():
    """Test that report confirms no alerts were sent."""
    report = generate_ticker_report("MAIA")

    # Should confirm dry-run mode
    assert "No Telegram or email was sent" in report or "DRY-RUN" in report


def test_ticker_drilldown_all_agents_present():
    """Test that all seven agents are present in report."""
    report = generate_ticker_report("MAIA")

    agents = ["Eddie", "Maggie", "Frank", "Maya", "Janet", "Sophie", "Ross"]

    # All agents should be mentioned in the report
    for agent in agents:
        assert agent in report

    # Agent Applicability Summary table should exist
    assert "## Agent Applicability Summary" in report
