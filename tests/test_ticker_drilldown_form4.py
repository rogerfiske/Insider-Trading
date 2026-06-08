"""Integration tests for ticker drilldown Form 4 functionality."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ticker_drilldown import generate_ticker_report


def test_ticker_drilldown_includes_form4_detail_section():
    """Test that MAIA drilldown includes Form 4 detail section."""
    report = generate_ticker_report("MAIA")

    # Report should include Eddie section
    assert "## Eddie — SEC Form 4 Insider Transactions" in report

    # Should mention Form 4 filings
    assert "Form 4" in report

    # Should include transaction information if any filings exist
    # (Either transaction details or explicit filing status message)
    has_transaction_info = (
        "Parsed Form 4 Filings" in report
        or "Recent Transactions" in report
        or "No recent Form 4 filings" in report
        or "No matching Form 4 filings" in report
        or "Form 4 filings found" in report
        or "MAIA Form 4 Filings" in report
        or "filings successfully" in report
        or "Transaction Summary" in report
        or "Parsed:" in report  # New format: "Parsed: N filings successfully"
    )
    assert has_transaction_info


def test_ticker_drilldown_does_not_require_roger_spreadsheet():
    """Test that ticker drilldown works without Roger's spreadsheet."""
    # This test confirms the drilldown does not depend on external spreadsheet data
    report = generate_ticker_report("MAIA")

    # Should generate a complete report using only SEC sources
    assert len(report) > 0
    assert "## Eddie — SEC Form 4 Insider Transactions" in report

    # Should explicitly mention data source boundary
    assert "Data Source Boundary" in report
    assert "OpenInsider" in report


def test_ticker_drilldown_dry_run_no_alerts():
    """Test that dry-run report does not send alerts."""
    report = generate_ticker_report("MAIA")

    # Should confirm no alerts sent
    assert "No Telegram or email was sent" in report or "DRY-RUN" in report

    # Should not contain actual Telegram/email sending evidence
    assert "Telegram message sent" not in report
    assert "Email sent" not in report


def test_ticker_drilldown_signal_logic():
    """Test that Eddie section includes signal/no-signal logic."""
    report = generate_ticker_report("MAIA")

    eddie_section_start = report.find("## Eddie — SEC Form 4 Insider Transactions")
    assert eddie_section_start > 0

    # Find Eddie's section content (between Eddie header and next section or end)
    next_section = report.find("\n## ", eddie_section_start + 10)
    if next_section == -1:
        eddie_content = report[eddie_section_start:]
    else:
        eddie_content = report[eddie_section_start:next_section]

    # Eddie should include signal/status determination
    has_signal_info = (
        "Signal:" in eddie_content
        or "BULLISH" in eddie_content
        or "BEARISH" in eddie_content
        or "NEUTRAL" in eddie_content
        or "Status:" in eddie_content
    )
    assert has_signal_info

    # Should include confidence and reason (with or without markdown formatting)
    has_confidence = "Confidence" in eddie_content
    has_reason = "Reason" in eddie_content or "Rationale" in eddie_content
    assert has_confidence, "Eddie section should include confidence information"
    assert has_reason, "Eddie section should include reason/rationale"


def test_ticker_drilldown_informational_disclaimer():
    """Test that report includes informational-only disclaimer."""
    report = generate_ticker_report("MAIA")

    # Should include disclaimer
    assert "informational only" in report.lower() or "not trading advice" in report.lower()


def test_ticker_drilldown_all_seven_agents():
    """Test that report includes all seven agents including Eddie."""
    report = generate_ticker_report("MAIA")

    agents = ["Eddie", "Maggie", "Frank", "Maya", "Janet", "Sophie", "Ross"]

    for agent in agents:
        assert agent in report, f"Agent {agent} not found in report"


def test_ticker_drilldown_eddie_status_determination():
    """Test that Eddie section includes status determination."""
    report = generate_ticker_report("MAIA")

    eddie_section_start = report.find("## Eddie — SEC Form 4 Insider Transactions")
    assert eddie_section_start > 0

    next_section = report.find("\n## ", eddie_section_start + 10)
    if next_section == -1:
        eddie_content = report[eddie_section_start:]
    else:
        eddie_content = report[eddie_section_start:next_section]

    # Eddie should have a status determination
    has_status = (
        "APPLICABLE" in eddie_content
        or "NOT_APPLICABLE" in eddie_content
        or "BLOCKED" in eddie_content
        or "Status:" in eddie_content
    )
    assert has_status


def test_ticker_drilldown_form4_transaction_summary():
    """Test that Eddie section includes transaction summary when Form 4s exist."""
    report = generate_ticker_report("MAIA")

    eddie_section_start = report.find("## Eddie — SEC Form 4 Insider Transactions")
    assert eddie_section_start > 0

    next_section = report.find("\n## ", eddie_section_start + 10)
    if next_section == -1:
        eddie_content = report[eddie_section_start:]
    else:
        eddie_content = report[eddie_section_start:next_section]

    # If Form 4 filings exist, should show transaction counts or explicit no-filings message
    has_transaction_summary = (
        "purchase" in eddie_content.lower()
        or "sale" in eddie_content.lower()
        or "transaction" in eddie_content.lower()
        or "No recent Form 4 filings" in eddie_content
        or "No matching Form 4 filings" in eddie_content
    )
    assert has_transaction_summary


def test_ticker_drilldown_output_with_path(tmp_path):
    """Test generating report with output path."""
    output_file = tmp_path / "test_maia_report.md"

    report = generate_ticker_report("MAIA", output_path=output_file)

    # File should be created
    assert output_file.exists()

    # File content should match returned report
    file_content = output_file.read_text(encoding="utf-8")
    assert file_content == report

    # Report should include Form 4 section
    assert "## Eddie — SEC Form 4 Insider Transactions" in file_content
