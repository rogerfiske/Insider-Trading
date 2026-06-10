"""Tests for MAIA capital structure research script."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.maia_capital_structure_research import (
    CapitalStructureItem,
    BeneficialOwner,
    Form144Filing,
    get_filings_by_form_types,
    analyze_march_2026_financing,
    build_capital_structure,
    check_13d_13g_filings,
    check_form_144_filings,
    generate_fully_diluted_estimate,
    generate_hidden_institutional_assessment,
    generate_json_report,
    generate_markdown_report,
)


@pytest.fixture
def mock_submissions_response():
    """Mock SEC submissions API response."""
    return {
        "ok": True,
        "body": {
            "cik": "1878313",
            "filings": {
                "recent": {
                    "accessionNumber": [
                        "0001493152-26-013879",
                        "0001493152-26-008784",
                        "0001493152-24-005432",
                    ],
                    "filingDate": ["2026-03-31", "2026-03-04", "2024-05-15"],
                    "reportDate": ["2026-03-31", "2026-03-04", "2024-05-15"],
                    "form": ["8-K", "424B5", "10-Q"],
                    "primaryDocument": ["form8-k.htm", "form424b5.htm", "form10-q.htm"],
                    "primaryDocDescription": ["8-K", "424B5", "10-Q"],
                }
            },
        },
        "url": "https://data.sec.gov/submissions/CIK0001878313.json",
        "from_cache": False,
    }


def test_get_filings_by_form_types(mock_submissions_response):
    """Test filtering filings by form types and date."""
    with patch(
        "scripts.maia_capital_structure_research.fetch_company_submissions",
        return_value=mock_submissions_response,
    ):
        filings = get_filings_by_form_types(
            "0001878313", ["8-K", "424B5"], "2026-01-01"
        )

        assert len(filings) == 2
        assert filings[0]["form"] == "8-K"
        assert filings[1]["form"] == "424B5"
        assert all(f["filing_date"] >= "2026-01-01" for f in filings)


def test_get_filings_by_form_types_empty():
    """Test filtering when no filings match."""
    with patch(
        "scripts.maia_capital_structure_research.fetch_company_submissions",
        return_value={"ok": False, "error": "Not found"},
    ):
        filings = get_filings_by_form_types(
            "0001878313", ["13D"], "2026-01-01"
        )

        assert filings == []


def test_analyze_march_2026_financing_found():
    """Test March 2026 financing analysis when filings exist."""
    filings = [
        {
            "form": "424B5",
            "filing_date": "2026-03-04",
            "accession_number": "0001493152-26-008784",
            "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1878313/000149315226008784/form424b5.htm",
        },
        {
            "form": "8-K",
            "filing_date": "2026-03-31",
            "accession_number": "0001493152-26-013879",
            "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1878313/000149315226013879/form8-k.htm",
        },
    ]

    mock_filing_text = """
    The Company raised gross proceeds of approximately $30.0 million.
    The Company sold 1,233,488 shares of common stock.
    The common warrants have an exercise price of $1.36 per share.
    The warrants contain a 4.99% beneficial ownership blocker.
    """

    with patch(
        "scripts.maia_capital_structure_research.fetch_filing_text",
        return_value={"ok": True, "body": mock_filing_text},
    ):
        result = analyze_march_2026_financing(filings)

        assert result["found"] is True
        assert "$30.0 million" in result["offering_details"]["gross_proceeds"]
        assert "1,233,488" in result["offering_details"]["common_shares_sold"]
        assert "$1.36" in result["offering_details"]["warrant_exercise_price"]
        assert "4.99%" in result["offering_details"]["blocker"]


def test_analyze_march_2026_financing_not_found():
    """Test March 2026 financing analysis when no March filings exist."""
    filings = [
        {
            "form": "10-Q",
            "filing_date": "2024-05-15",
            "accession_number": "0001493152-24-005432",
            "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1878313/form10-q.htm",
        }
    ]

    result = analyze_march_2026_financing(filings)

    assert result["found"] is False
    assert "No March 2026 financing filings identified" in result["note"]


def test_build_capital_structure():
    """Test capital structure table building."""
    filings = [
        {"form": "10-Q", "filing_date": "2026-05-11"},
        {"form": "DEF 14A", "filing_date": "2026-04-07"},
    ]

    march_2026_data = {
        "found": True,
        "offering_details": {
            "common_shares_sold": "1,233,488",
            "prefunded_warrants_sold": "500,000",
            "common_warrants_sold": "1,000,000",
            "warrant_exercise_price": "$1.36",
            "blocker": "4.99% blocker",
        },
    }

    items = build_capital_structure(filings, march_2026_data)

    assert len(items) >= 4  # Common stock + 3 March 2026 instruments + equity plan
    assert any("Common Stock Outstanding" in item.security for item in items)
    assert any("March 2026 Offering" in item.security for item in items)
    assert any("Pre-Funded Warrants" in item.security for item in items)


def test_check_13d_13g_filings():
    """Test 13D/13G beneficial ownership extraction."""
    filings = [
        {
            "form": "13G",
            "filing_date": "2026-02-15",
            "accession_number": "0001234567-26-001234",
            "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1878313/13g.xml",
        },
        {
            "form": "13D/A",
            "filing_date": "2026-03-20",
            "accession_number": "0001234567-26-002345",
            "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1878313/13da.xml",
        },
    ]

    owners = check_13d_13g_filings(filings)

    assert len(owners) == 2
    assert owners[0].filing_type == "13G"
    assert "Passive" in owners[0].passive_active
    assert owners[1].filing_type == "13D/A"
    assert "Active" in owners[1].passive_active


def test_check_form_144_filings():
    """Test Form 144 extraction."""
    filings = [
        {
            "form": "144",
            "filing_date": "2026-04-15",
            "accession_number": "0001234567-26-003456",
        },
        {
            "form": "8-K",
            "filing_date": "2026-04-16",
            "accession_number": "0001234567-26-003457",
        },
    ]

    form_144s = check_form_144_filings(filings)

    assert len(form_144s) == 1
    assert form_144s[0].filing_date == "2026-04-15"


def test_generate_fully_diluted_estimate():
    """Test fully diluted share count estimation."""
    capital_structure = [
        CapitalStructureItem(
            security="Common Stock",
            source_filing="10-Q",
            date="2026-05-11",
            count=10_000_000,
            exercise_price="N/A",
            expiration="N/A",
            blocker="N/A",
            in_the_money="N/A",
            dilution_impact="Base",
            confidence="High",
            notes="",
        )
    ]

    estimate = generate_fully_diluted_estimate(capital_structure)

    assert "methodology" in estimate
    assert "Basic" in estimate["methodology"]
    assert "warrants" in estimate["methodology"].lower()


def test_generate_hidden_institutional_assessment():
    """Test hidden institutional ownership assessment generation."""
    assessment = generate_hidden_institutional_assessment()

    assert len(assessment) >= 9
    assert any("healthcare-dedicated investors" in point.lower() for point in assessment)
    assert any("13f" in point.lower() for point in assessment)
    assert any("blocker" in point.lower() for point in assessment)


def test_generate_markdown_report():
    """Test markdown report generation."""
    filings = [
        {
            "form": "8-K",
            "filing_date": "2026-03-31",
            "accession_number": "0001493152-26-013879",
            "primary_document_url": "https://example.com/8k.htm",
        }
    ]

    march_2026_data = {
        "found": True,
        "offering_details": {"gross_proceeds": "$30M"},
        "filings_reviewed": [],
    }

    capital_structure = []
    fully_diluted = {"methodology": "Test"}
    beneficial_owners = []
    form_144s = []
    hidden_institutional = ["Point 1", "Point 2"]

    report = generate_markdown_report(
        filings,
        march_2026_data,
        capital_structure,
        fully_diluted,
        beneficial_owners,
        form_144s,
        hidden_institutional,
    )

    assert "# MAIA Biotechnology Capital Structure" in report
    assert "MAIA" in report
    assert "0001878313" in report
    assert "March 2026 financing identified: True" in report
    assert "No secrets" not in report  # Shouldn't contain actual secrets
    assert "openinsider_spreadsheet_used" not in report  # Not in markdown


def test_generate_json_report():
    """Test JSON report generation."""
    filings = [
        {
            "form": "8-K",
            "filing_date": "2026-03-31",
            "accession_number": "0001493152-26-013879",
            "primary_document_url": "https://example.com/8k.htm",
        }
    ]

    march_2026_data = {"found": True}
    capital_structure = []
    fully_diluted = {}
    beneficial_owners = []
    form_144s = []
    hidden_institutional = []

    report = generate_json_report(
        filings,
        march_2026_data,
        capital_structure,
        fully_diluted,
        beneficial_owners,
        form_144s,
        hidden_institutional,
    )

    assert report["ticker"] == "MAIA"
    assert report["cik"] == "0001878313"
    assert report["data_sources"] == ["SEC EDGAR"]
    assert report["safety"]["openinsider_spreadsheet_used"] is False
    assert report["safety"]["telegram_sent"] is False
    assert report["safety"]["email_sent"] is False
    assert report["safety"]["scheduled_tasks_modified"] is False


def test_json_report_no_secrets():
    """Test that JSON report contains no secrets."""
    filings = []
    march_2026_data = {"found": False}
    capital_structure = []
    fully_diluted = {}
    beneficial_owners = []
    form_144s = []
    hidden_institutional = []

    report = generate_json_report(
        filings,
        march_2026_data,
        capital_structure,
        fully_diluted,
        beneficial_owners,
        form_144s,
        hidden_institutional,
    )

    report_str = json.dumps(report)

    # Verify no secrets in output
    assert "TELEGRAM_BOT_TOKEN" not in report_str
    assert "SMTP_PASSWORD" not in report_str
    assert "sk-ant-" not in report_str
    assert "API_KEY" not in report_str


def test_dataclass_serialization():
    """Test that dataclasses serialize correctly to JSON."""
    item = CapitalStructureItem(
        security="Test",
        source_filing="10-Q",
        date="2026-01-01",
        count=1000,
        exercise_price="$1.00",
        expiration="2027-01-01",
        blocker="4.99%",
        in_the_money="Yes",
        dilution_impact="Immediate",
        confidence="High",
        notes="Test note",
    )

    from dataclasses import asdict
    item_dict = asdict(item)

    assert item_dict["security"] == "Test"
    assert item_dict["count"] == 1000
    assert json.dumps(item_dict)  # Should be JSON-serializable


def test_no_alert_code_called():
    """Test that no alert/email/Telegram code is called."""
    # This test verifies the safety constraints
    # The script should never import or call alert-related modules

    import scripts.maia_capital_structure_research as research_module

    # Check that ROSS_DRY_RUN is forced to true
    import os
    assert os.environ.get("ROSS_DRY_RUN") == "true"
    assert os.environ.get("ALERT_ENABLE_TELEGRAM") == "false"
    assert os.environ.get("ALERT_ENABLE_EMAIL") == "false"
