"""Tests for structured ticker research results (Eddie/Maggie result classes)."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sources.ticker_research_results import (
    EddieTickerResult,
    MaggieTickerResult,
    TickerResearchReport,
)


def test_eddie_result_has_required_fields():
    """Test that EddieTickerResult contains all required fields."""
    result = EddieTickerResult(
        ticker="MAIA",
        cik="0001878313",
        company_name="MAIA Biotechnology, Inc.",
        lookback_days=1460,
        status="APPLICABLE_WITH_EVIDENCE",
        signal="BULLISH_EVIDENCE",
        confidence=2,
        reason="Recent insider purchases detected",
        filings_found=214,
        filings_attempted=214,
        filings_parsed=214,
        filings_failed=0,
        transactions_extracted=136,
        purchase_count=134,
        purchase_value=4921437.58,
        sale_count=0,
        sale_value=0.0,
        option_exercise_count=2,
        grant_award_count=0,
        reporting_owners=["CHAOUKI STEVEN M (Director)"],
        source_accessions=["0001878313-26-000062"],
        error_message=None,
    )

    # Verify all required fields are present
    assert result.ticker == "MAIA"
    assert result.cik == "0001878313"
    assert result.company_name == "MAIA Biotechnology, Inc."
    assert result.lookback_days == 1460
    assert result.status == "APPLICABLE_WITH_EVIDENCE"
    assert result.signal == "BULLISH_EVIDENCE"
    assert result.confidence == 2
    assert result.reason == "Recent insider purchases detected"
    assert result.filings_found == 214
    assert result.filings_attempted == 214
    assert result.filings_parsed == 214
    assert result.filings_failed == 0
    assert result.transactions_extracted == 136
    assert result.purchase_count == 134
    assert result.purchase_value == 4921437.58
    assert result.sale_count == 0
    assert result.sale_value == 0.0
    assert result.option_exercise_count == 2
    assert result.grant_award_count == 0
    assert len(result.reporting_owners) == 1
    assert len(result.source_accessions) == 1
    assert result.error_message is None


def test_maggie_result_has_required_fields():
    """Test that MaggieTickerResult contains all required fields."""
    result = MaggieTickerResult(
        ticker="MAIA",
        cik="0001878313",
        company_name="MAIA Biotechnology, Inc.",
        status="APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING",
        signal="NEUTRAL",
        confidence=1,
        reason="Issuer-name matching used (CUSIP unavailable)",
        managers_reviewed=5,
        filings_found=5,
        filings_parsed=0,
        holdings_found=0,
        match_method="issuer_name",
        total_shares=0,
        total_value=0.0,
        limitations=["CUSIP not available"],
        source_urls=[],
        error_message=None,
    )

    # Verify all required fields are present
    assert result.ticker == "MAIA"
    assert result.cik == "0001878313"
    assert result.status == "APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING"
    assert result.signal == "NEUTRAL"
    assert result.confidence == 1
    assert result.managers_reviewed == 5
    assert result.filings_found == 5
    assert result.filings_parsed == 0
    assert result.holdings_found == 0
    assert result.match_method == "issuer_name"
    assert len(result.limitations) == 1
    assert result.error_message is None


def test_ticker_research_report_combines_results():
    """Test that TickerResearchReport combines Eddie and Maggie results."""
    eddie = EddieTickerResult(
        ticker="MAIA",
        cik="0001878313",
        company_name="MAIA Biotechnology, Inc.",
        lookback_days=1460,
        status="APPLICABLE_WITH_EVIDENCE",
        signal="BULLISH_EVIDENCE",
        confidence=2,
        reason="Recent insider purchases detected",
        filings_found=214,
        filings_attempted=214,
        filings_parsed=214,
        filings_failed=0,
        transactions_extracted=136,
        purchase_count=134,
        purchase_value=4921437.58,
        sale_count=0,
        sale_value=0.0,
        option_exercise_count=2,
        grant_award_count=0,
    )

    maggie = MaggieTickerResult(
        ticker="MAIA",
        cik="0001878313",
        company_name="MAIA Biotechnology, Inc.",
        status="APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING",
        signal="NEUTRAL",
        confidence=1,
        reason="Issuer-name matching used (CUSIP unavailable)",
        managers_reviewed=5,
        filings_found=5,
        filings_parsed=0,
        holdings_found=0,
        match_method="issuer_name",
        total_shares=0,
        total_value=0.0,
    )

    report = TickerResearchReport(
        ticker="MAIA",
        generated_at="2026-06-08T16:00:00.000000+00:00",
        eddie_result=eddie,
        maggie_result=maggie,
        markdown_report="# MAIA Report\n\nTest content",
    )

    assert report.ticker == "MAIA"
    assert report.eddie_result.ticker == "MAIA"
    assert report.maggie_result.ticker == "MAIA"
    assert "MAIA Report" in report.markdown_report


def test_eddie_result_default_empty_lists():
    """Test that EddieTickerResult has default empty lists for optional fields."""
    result = EddieTickerResult(
        ticker="TEST",
        cik="0000000000",
        company_name="Test Corp",
        lookback_days=365,
        status="FAILED_GRACEFULLY",
        signal="NEUTRAL",
        confidence=0,
        reason="Ticker resolution failed",
        filings_found=0,
        filings_attempted=0,
        filings_parsed=0,
        filings_failed=0,
        transactions_extracted=0,
        purchase_count=0,
        purchase_value=0.0,
        sale_count=0,
        sale_value=0.0,
        option_exercise_count=0,
        grant_award_count=0,
        # Do not provide reporting_owners or source_accessions
    )

    # Default lists should be empty
    assert result.reporting_owners == []
    assert result.source_accessions == []
    assert result.error_message is None


def test_maggie_result_with_error():
    """Test that MaggieTickerResult can capture error messages."""
    result = MaggieTickerResult(
        ticker="BAD",
        cik="0000000000",
        company_name="Unknown",
        status="FAILED_GRACEFULLY",
        signal="NEUTRAL",
        confidence=0,
        reason="13F parsing failed",
        managers_reviewed=0,
        filings_found=0,
        filings_parsed=0,
        holdings_found=0,
        match_method="none",
        total_shares=0,
        total_value=0.0,
        error_message="XML parsing failed: malformed document",
    )

    assert result.status == "FAILED_GRACEFULLY"
    assert result.error_message is not None
    assert "XML parsing failed" in result.error_message
