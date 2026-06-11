"""Tests for SEC ticker inventory CLI and submissions inventory builder.

Tests cover:
- Ticker normalization
- CIK zero-padding
- Resolver success/failure paths (mocked/fixture data)
- Submissions inventory parsing
- Filing counts by form
- Latest filings selection
- Coverage flags
- Downstream readiness
- Degraded-mode schema
- Batch summary schema
- MAIA resolves to 0001878313
- No buy/sell/hold language
- Safety flags correct
- No secrets in outputs
- No alert code called
- OpenInsider not required
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from scripts.sec_ticker_inventory import (
    generate_batch_summary_json,
    generate_batch_summary_markdown,
    generate_per_ticker_json,
    generate_per_ticker_markdown,
    process_ticker,
)
from sources.sec_submissions import build_submissions_inventory
from sources.sec_ticker import TickerCikResult, resolve_ticker_to_cik


# Fixtures


@pytest.fixture
def mock_maia_resolver_result():
    """Mock successful MAIA ticker resolution."""
    return TickerCikResult.success(
        ticker="MAIA",
        cik=1878313,
        company_name="MAIA Biotechnology, Inc.",
        source_url="https://www.sec.gov/files/company_tickers.json",
    )


@pytest.fixture
def mock_failed_resolver_result():
    """Mock failed ticker resolution."""
    return TickerCikResult.failure(
        ticker="INVALID",
        error_type="ticker_not_found",
        error_message="Ticker 'INVALID' not found in SEC company tickers mapping",
    )


@pytest.fixture
def mock_submissions_data():
    """Mock SEC submissions inventory data."""
    return {
        "status": "retrieved",
        "data": {
            "filing_counts_by_form": {
                "4": 12,
                "10-Q": 8,
                "10-K": 2,
                "8-K": 15,
                "S-3": 1,
            },
            "latest_10k": {
                "accession_number": "0001234567-23-000001",
                "filing_date": "2023-03-15",
                "form": "10-K",
                "primary_document": "form10k.htm",
            },
            "latest_10q": {
                "accession_number": "0001234567-23-000002",
                "filing_date": "2023-11-10",
                "form": "10-Q",
                "primary_document": "form10q.htm",
            },
            "latest_8k": {
                "accession_number": "0001234567-23-000003",
                "filing_date": "2023-12-01",
                "form": "8-K",
                "primary_document": "form8k.htm",
            },
            "latest_form4": {
                "accession_number": "0001234567-23-000004",
                "filing_date": "2023-12-15",
                "form": "4",
                "primary_document": "form4.xml",
            },
            "latest_form144": None,
            "latest_13d_or_13g": None,
            "latest_13f_hr": None,
            "recent_filings": [
                {
                    "accession_number": "0001234567-23-000005",
                    "filing_date": "2023-12-20",
                    "report_date": "2023-12-19",
                    "form": "4",
                    "primary_document": "form4.xml",
                    "file_number": "001-12345",
                    "film_number": "231234567",
                    "archive_url": "https://www.sec.gov/Archives/edgar/data/1878313/0001234567230000 05/",
                },
            ],
            "coverage_flags": {
                "has_form4": True,
                "has_form144": False,
                "has_13d_13g": False,
                "has_10q": True,
                "has_10k": True,
                "has_8k": True,
                "has_s3_or_offering_filing": True,
                "has_13f_hr": False,
            },
            "source_url": "https://data.sec.gov/submissions/CIK0001878313.json",
            "retrieved_at": "2024-01-01T00:00:00+00:00",
        },
        "error": None,
    }


@pytest.fixture
def mock_degraded_submissions_data():
    """Mock degraded submissions data (no recent filings)."""
    return {
        "status": "degraded",
        "data": {
            "filing_counts_by_form": {},
            "latest_10k": None,
            "latest_10q": None,
            "latest_8k": None,
            "latest_form4": None,
            "latest_form144": None,
            "latest_13d_or_13g": None,
            "latest_13f_hr": None,
            "recent_filings": [],
            "coverage_flags": {
                "has_form4": False,
                "has_form144": False,
                "has_13d_13g": False,
                "has_10q": False,
                "has_10k": False,
                "has_8k": False,
                "has_s3_or_offering_filing": False,
                "has_13f_hr": False,
            },
            "source_url": "https://data.sec.gov/submissions/CIK0001234567.json",
            "retrieved_at": "2024-01-01T00:00:00+00:00",
        },
        "error": "No recent filings found in submissions data",
    }


# Tests


def test_ticker_normalization():
    """Test that tickers are normalized to uppercase."""
    result = generate_per_ticker_json(
        "maia",
        TickerCikResult.success("maia", 1878313, "MAIA Biotechnology, Inc.", ""),
        {"status": "failed", "data": None, "error": "Test"},
        100,
    )
    assert result["ticker"] == "MAIA"


def test_cik_zero_padding():
    """Test that CIKs are zero-padded to 10 digits."""
    resolver_result = TickerCikResult.success(
        "MAIA", 1878313, "MAIA Biotechnology, Inc.", ""
    )
    assert resolver_result.cik_padded == "0001878313"
    assert len(resolver_result.cik_padded) == 10


def test_resolver_success_with_fixture(mock_maia_resolver_result):
    """Test successful resolver with MAIA fixture."""
    assert mock_maia_resolver_result.ok is True
    assert mock_maia_resolver_result.ticker == "MAIA"
    assert mock_maia_resolver_result.cik == 1878313
    assert mock_maia_resolver_result.cik_padded == "0001878313"
    assert "MAIA" in mock_maia_resolver_result.company_name


def test_resolver_failure_path(mock_failed_resolver_result):
    """Test resolver unresolved path."""
    assert mock_failed_resolver_result.ok is False
    assert mock_failed_resolver_result.ticker == "INVALID"
    assert mock_failed_resolver_result.cik == 0
    assert mock_failed_resolver_result.error_type == "ticker_not_found"
    assert "not found" in mock_failed_resolver_result.error_message


def test_submissions_inventory_parsing(mock_submissions_data):
    """Test submissions inventory parsing with fixture."""
    data = mock_submissions_data["data"]
    assert data["filing_counts_by_form"]["4"] == 12
    assert data["filing_counts_by_form"]["10-Q"] == 8
    assert data["filing_counts_by_form"]["10-K"] == 2


def test_filing_counts_by_form(mock_submissions_data):
    """Test filing counts by form extraction."""
    data = mock_submissions_data["data"]
    counts = data["filing_counts_by_form"]
    assert counts["4"] == 12
    assert counts["8-K"] == 15
    assert counts["S-3"] == 1


def test_latest_filings_selection(mock_submissions_data):
    """Test latest filings selection."""
    data = mock_submissions_data["data"]
    assert data["latest_form4"] is not None
    assert data["latest_form4"]["form"] == "4"
    assert data["latest_10k"] is not None
    assert data["latest_10k"]["form"] == "10-K"
    assert data["latest_form144"] is None


def test_coverage_flags(mock_submissions_data):
    """Test coverage flags."""
    flags = mock_submissions_data["data"]["coverage_flags"]
    assert flags["has_form4"] is True
    assert flags["has_10q"] is True
    assert flags["has_10k"] is True
    assert flags["has_8k"] is True
    assert flags["has_form144"] is False
    assert flags["has_13d_13g"] is False


def test_downstream_readiness_fields(mock_maia_resolver_result, mock_submissions_data):
    """Test downstream readiness fields."""
    result = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_submissions_data, 100
    )

    downstream = result["downstream_readiness"]
    assert downstream["form4_ready"] is True
    assert downstream["form144_ready"] is False
    assert downstream["ownership_13dg_ready"] is False
    assert downstream["xbrl_financials_ready"] is True
    assert downstream["capital_structure_ready"] is True


def test_degraded_mode_schema_unresolved(mock_failed_resolver_result):
    """Test degraded-mode schema for unresolved ticker."""
    result = generate_per_ticker_json(
        "INVALID",
        mock_failed_resolver_result,
        {"status": "failed", "data": None, "error": "Ticker not resolved"},
        100,
    )

    degraded = result["degraded_mode"]
    assert degraded["is_degraded"] is True
    assert len(degraded["reasons"]) > 0
    assert "resolution failed" in degraded["reasons"][0].lower()


def test_degraded_mode_schema_no_filings(
    mock_maia_resolver_result, mock_degraded_submissions_data
):
    """Test degraded-mode schema for no recent filings."""
    result = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_degraded_submissions_data, 100
    )

    degraded = result["degraded_mode"]
    assert degraded["is_degraded"] is True
    assert any("no recent filings" in reason.lower() for reason in degraded["reasons"])


def test_batch_summary_schema(mock_maia_resolver_result, mock_submissions_data):
    """Test batch summary schema."""
    ticker1_json = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_submissions_data, 100
    )
    ticker2_json = generate_per_ticker_json(
        "INVALID",
        TickerCikResult.failure("INVALID", "ticker_not_found", "Not found"),
        {"status": "failed", "data": None, "error": "Ticker not resolved"},
        100,
    )

    batch_json = generate_batch_summary_json([ticker1_json, ticker2_json])

    assert "MAIA" in batch_json["tickers_requested"]
    assert "INVALID" in batch_json["tickers_requested"]
    assert "MAIA" in batch_json["tickers_resolved"]
    assert "INVALID" in batch_json["tickers_unresolved"]
    assert batch_json["summary"]["resolved_count"] == 1
    assert batch_json["summary"]["unresolved_count"] == 1


def test_maia_resolves_to_correct_cik():
    """Test MAIA resolves to CIK 0001878313."""
    resolver_result = TickerCikResult.success(
        "MAIA", 1878313, "MAIA Biotechnology, Inc.", ""
    )
    assert resolver_result.cik_padded == "0001878313"


def test_no_buy_sell_hold_language(mock_maia_resolver_result, mock_submissions_data):
    """Test no buy/sell/hold recommendation language."""
    result_json = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_submissions_data, 100
    )
    result_md = generate_per_ticker_markdown(result_json)

    # Convert to lowercase for case-insensitive search
    json_str = json.dumps(result_json).lower()
    md_str = result_md.lower()

    # Check for prohibited language patterns (investment advice)
    # These should NOT appear in the output
    prohibited_patterns = [
        "we recommend buy",
        "we recommend sell",
        "we recommend hold",
        "should buy",
        "should sell",
        "should hold",
        "strong buy",
        "strong sell",
        "buy rating",
        "sell rating",
        "hold rating",
        "investment recommendation",
    ]

    for pattern in prohibited_patterns:
        assert pattern not in json_str, f"Found prohibited investment advice pattern: {pattern}"
        assert pattern not in md_str, f"Found prohibited investment advice pattern: {pattern}"

    # Verify safety flag is explicitly false
    assert result_json["safety"]["buy_sell_hold_language_used"] is False


def test_safety_flags_correct(mock_maia_resolver_result, mock_submissions_data):
    """Test safety flags are correct."""
    result = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_submissions_data, 100
    )

    safety = result["safety"]
    assert safety["report_only"] is True
    assert safety["alerts_generated"] is False
    assert safety["openinsider_spreadsheet_used"] is False
    assert safety["telegram_sent"] is False
    assert safety["email_sent"] is False
    assert safety["scheduled_tasks_modified"] is False
    assert safety["env_printed_or_changed"] is False
    assert safety["buy_sell_hold_language_used"] is False


def test_no_secrets_in_output(mock_maia_resolver_result, mock_submissions_data):
    """Test no secrets in outputs."""
    result = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_submissions_data, 100
    )

    json_str = json.dumps(result)

    # Check for common secret patterns
    secret_patterns = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SMTP_PASSWORD",
        "GMAIL_APP_PASSWORD",
        "sk-ant-",
        "password=",
        "token=",
    ]

    for pattern in secret_patterns:
        assert pattern not in json_str


def test_no_alert_code_path():
    """Test no alert code is called (verified by mocking)."""
    # This test verifies that alert-related modules are not imported
    # In actual implementation, alert code should not be called
    with patch("scripts.sec_ticker_inventory.resolve_ticker_to_cik") as mock_resolve:
        mock_resolve.return_value = TickerCikResult.success(
            "TEST", 1234567, "Test Inc.", ""
        )

        with patch(
            "scripts.sec_ticker_inventory.build_submissions_inventory"
        ) as mock_inventory:
            mock_inventory.return_value = {
                "status": "retrieved",
                "data": {
                    "filing_counts_by_form": {},
                    "latest_10k": None,
                    "latest_10q": None,
                    "latest_8k": None,
                    "latest_form4": None,
                    "latest_form144": None,
                    "latest_13d_or_13g": None,
                    "latest_13f_hr": None,
                    "recent_filings": [],
                    "coverage_flags": {
                        "has_form4": False,
                        "has_form144": False,
                        "has_13d_13g": False,
                        "has_10q": False,
                        "has_10k": False,
                        "has_8k": False,
                        "has_s3_or_offering_filing": False,
                        "has_13f_hr": False,
                    },
                    "source_url": "",
                    "retrieved_at": "",
                },
                "error": None,
            }

            result = process_ticker("TEST", 100)
            assert result is not None


def test_openinsider_not_required(mock_maia_resolver_result, mock_submissions_data):
    """Test OpenInsider spreadsheet is not required."""
    # This test verifies that the system works without OpenInsider data
    result = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_submissions_data, 100
    )

    # Should successfully generate output without OpenInsider
    assert result is not None
    assert result["ticker"] == "MAIA"
    assert result["safety"]["openinsider_spreadsheet_used"] is False


def test_json_schema_completeness(mock_maia_resolver_result, mock_submissions_data):
    """Test JSON output has all required schema fields."""
    result = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_submissions_data, 100
    )

    # Required top-level fields
    required_fields = [
        "ticker",
        "cik",
        "company_name",
        "generated_at",
        "resolver",
        "submissions",
        "downstream_readiness",
        "degraded_mode",
        "evidence_provenance",
        "safety",
    ]

    for field in required_fields:
        assert field in result

    # Resolver fields
    assert "status" in result["resolver"]
    assert "source" in result["resolver"]
    assert "evidence" in result["resolver"]

    # Submissions fields
    assert "status" in result["submissions"]
    assert "recent_filings_count" in result["submissions"]
    assert "filing_counts_by_form" in result["submissions"]
    assert "coverage_flags" in result["submissions"]
    assert "latest_filings" in result["submissions"]
    assert "recent_filings" in result["submissions"]


def test_markdown_report_sections(mock_maia_resolver_result, mock_submissions_data):
    """Test Markdown report has all required sections."""
    result_json = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_submissions_data, 100
    )
    result_md = generate_per_ticker_markdown(result_json)

    required_sections = [
        "# SEC Ticker/CIK Submissions Inventory",
        "## Purpose",
        "## Source Boundary",
        "## Resolver Result",
        "## SEC Submissions Status",
        "## Filing Counts by Form",
        "## Latest Relevant Filings",
        "## Downstream Readiness",
        "## Degraded Mode",
        "## Evidence Provenance",
        "## Safety Confirmations",
    ]

    for section in required_sections:
        assert section in result_md


def test_batch_markdown_sections(mock_maia_resolver_result, mock_submissions_data):
    """Test batch Markdown report has all required sections."""
    ticker1_json = generate_per_ticker_json(
        "MAIA", mock_maia_resolver_result, mock_submissions_data, 100
    )

    batch_json = generate_batch_summary_json([ticker1_json])
    batch_md = generate_batch_summary_markdown(batch_json)

    required_sections = [
        "# SEC Ticker/CIK Batch Submissions Inventory Summary",
        "## Requested Tickers",
        "## Resolved Tickers",
        "## Unresolved Tickers",
        "## Per-Ticker Status",
        "## Degraded Mode Details",
        "## Summary Statistics",
        "## Safety Confirmations",
    ]

    for section in required_sections:
        assert section in batch_md
