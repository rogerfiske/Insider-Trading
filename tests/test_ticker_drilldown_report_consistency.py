"""Tests for ticker drilldown report internal consistency."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ticker_drilldown import generate_ticker_report


def test_summary_table_matches_detailed_eddie_status():
    """Test that Eddie status in summary table matches detailed Eddie section."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=0)

    # Find summary table Eddie row
    summary_table_start = report.find("## Agent Applicability Summary")
    assert summary_table_start > 0, "Summary table not found"

    # Find Eddie detailed section
    eddie_section_start = report.find("## Eddie — SEC Form 4 Insider Transactions")
    assert eddie_section_start > 0, "Eddie section not found"

    # Extract summary table (from summary header to next section)
    next_section_after_summary = report.find("\n## ", summary_table_start + 10)
    summary_table = report[summary_table_start:next_section_after_summary]

    # Extract Eddie section (from Eddie header to next section)
    next_section_after_eddie = report.find("\n## ", eddie_section_start + 10)
    if next_section_after_eddie == -1:
        eddie_section = report[eddie_section_start:]
    else:
        eddie_section = report[eddie_section_start:next_section_after_eddie]

    # Extract Eddie status from detailed section
    # Format: "**Applicability**: APPLICABLE_WITH_EVIDENCE"
    assert "**Applicability**:" in eddie_section, "Eddie applicability not found in detailed section"
    applicability_start = eddie_section.find("**Applicability**:")
    applicability_line_end = eddie_section.find("\n", applicability_start)
    applicability_line = eddie_section[applicability_start:applicability_line_end]

    # Extract status value (after **: )
    detailed_status = applicability_line.split("**Applicability**: ")[1].strip()

    # Summary table should contain the same status
    assert detailed_status in summary_table, f"Summary table Eddie status does not match detailed section. Expected '{detailed_status}' in summary table"


def test_no_status_inconsistency_when_transactions_extracted():
    """Test that Eddie status is not APPLICABLE_NO_RECENT_FILINGS when transactions exist."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=0)

    # If transactions are extracted, Eddie should not say "no recent filings"
    if "transaction(s)" in report and "Total filings parsed:" in report:
        # Check that summary table does not show stale "no recent filings" status
        summary_table_start = report.find("## Agent Applicability Summary")
        next_section = report.find("\n## ", summary_table_start + 10)
        summary_table = report[summary_table_start:next_section]

        # Eddie row should not contain "APPLICABLE_NO_RECENT_FILINGS"
        assert "| Eddie | APPLICABLE_NO_RECENT_FILINGS |" not in summary_table, "Summary table shows stale 'no recent filings' status despite transactions being extracted"


def test_eddie_signal_matches_status():
    """Test that Eddie signal is consistent with status."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=0)

    eddie_section_start = report.find("## Eddie — SEC Form 4 Insider Transactions")
    assert eddie_section_start > 0

    next_section = report.find("\n## ", eddie_section_start + 10)
    if next_section == -1:
        eddie_section = report[eddie_section_start:]
    else:
        eddie_section = report[eddie_section_start:next_section]

    # Extract status and signal
    has_applicability = "**Applicability**: APPLICABLE_WITH_EVIDENCE" in eddie_section
    has_bullish_signal = "**Signal**: BULLISH_EVIDENCE" in eddie_section
    has_bearish_signal = "**Signal**: BEARISH_EVIDENCE" in eddie_section
    has_neutral_signal = "**Signal**: NEUTRAL" in eddie_section

    # If status is APPLICABLE_WITH_EVIDENCE, signal should be present
    if has_applicability:
        assert has_bullish_signal or has_bearish_signal or has_neutral_signal, "Eddie status is APPLICABLE_WITH_EVIDENCE but no signal found"


def test_eddie_confidence_present_when_status_set():
    """Test that Eddie includes confidence rating when status is set."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=0)

    eddie_section_start = report.find("## Eddie — SEC Form 4 Insider Transactions")
    assert eddie_section_start > 0

    next_section = report.find("\n## ", eddie_section_start + 10)
    if next_section == -1:
        eddie_section = report[eddie_section_start:]
    else:
        eddie_section = report[eddie_section_start:next_section]

    # Confidence should be present
    assert "**Confidence**:" in eddie_section, "Eddie section missing confidence rating"


def test_purchases_trigger_bullish_signal():
    """Test that insider purchases result in BULLISH_EVIDENCE signal."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=0)

    # MAIA has purchases
    if "Open-market purchases: 134 transaction(s)" in report:
        # Should have BULLISH_EVIDENCE signal
        assert "BULLISH_EVIDENCE" in report, "Report shows purchases but no BULLISH_EVIDENCE signal"
        assert "**Signal**: BULLISH_EVIDENCE" in report, "Eddie section missing BULLISH_EVIDENCE signal"


def test_report_does_not_send_telegram_or_email():
    """Test that manual ticker report does not send Telegram or email."""
    report = generate_ticker_report("MAIA", lookback_days=1460, max_form4_filings=0)

    # Report should explicitly state no alerts sent
    assert "DRY-RUN" in report or "No Telegram or email was sent" in report
    assert "Telegram message sent" not in report
    assert "Email sent" not in report
