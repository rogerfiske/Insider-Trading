"""Tests for SEC capital structure and dilution extraction.

Tests use fixtures and mocks. No live network calls.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest


# Fixture: MAIA XBRL output with share counts
@pytest.fixture
def maia_xbrl_fixture():
    """MAIA XBRL financial data with share counts."""
    return {
        "ticker": "MAIA",
        "cik": "0001878313",
        "company_name": "MAIA Biotechnology, Inc.",
        "generated_at": "2026-06-12T16:00:00Z",
        "quarterly_metrics": {
            "common_shares_outstanding": {
                "value": 60671491,
                "unit": "shares",
                "concept": "CommonStockSharesOutstanding",
                "period_end": "2026-03-31",
                "fiscal_year": 2026,
                "fiscal_period": "Q1",
                "form": "10-Q",
                "filed": "2026-05-11",
                "accession": "0001493152-26-022154",
                "source": "sec_companyfacts",
                "status": "ok",
            },
            "common_shares_issued": {
                "value": 60671491,
                "unit": "shares",
                "concept": "CommonStockSharesIssued",
                "period_end": "2026-03-31",
                "fiscal_year": 2026,
                "fiscal_period": "Q1",
                "form": "10-Q",
                "filed": "2026-05-11",
                "accession": "0001493152-26-022154",
                "source": "sec_companyfacts",
                "status": "ok",
            },
            "weighted_average_shares_basic": {
                "value": 59230103,
                "unit": "shares",
                "concept": "WeightedAverageNumberOfSharesOutstandingBasic",
                "period_end": "2026-03-31",
                "period_start": "2026-01-01",
                "fiscal_year": 2026,
                "fiscal_period": "Q1",
                "form": "10-Q",
                "filed": "2026-05-11",
                "accession": "0001493152-26-022154",
                "source": "sec_companyfacts",
                "status": "ok",
            },
            "weighted_average_shares_diluted": {
                "value": 59230103,
                "unit": "shares",
                "concept": "WeightedAverageNumberOfDilutedSharesOutstanding",
                "period_end": "2026-03-31",
                "period_start": "2026-01-01",
                "fiscal_year": 2026,
                "fiscal_period": "Q1",
                "form": "10-Q",
                "filed": "2026-05-11",
                "accession": "0001493152-26-022154",
                "source": "sec_companyfacts",
                "status": "ok",
            },
        },
    }


# Fixture: March 2026 MAIA public offering terms
@pytest.fixture
def maia_march_2026_offering():
    """March 2026 MAIA public offering."""
    return {
        "form": "424B5",
        "accession_number": "0001104659-26-034567",
        "filing_date": "2026-03-17",
        "report_date": None,
        "event_type": "public_offering",
        "securities_offered": "Common Stock",
        "shares_offered": 20000000,
        "price_per_share": 1.50,
        "gross_proceeds": 30000000,
        "net_proceeds": 28000000,
        "warrants_included": False,
        "pre_funded_warrants_included": False,
        "placement_agent_or_underwriter_if_disclosed": "Maxim Group LLC",
        "overallotment_or_option_if_disclosed": True,
        "status": "effective",
        "parse_status": "success",
    }


# Fixture: S-8 registration
@pytest.fixture
def maia_s8_registration():
    """MAIA S-8 equity compensation registration."""
    return {
        "form": "S-8",
        "accession_number": "0001493152-25-012345",
        "filing_date": "2025-06-15",
        "report_date": None,
        "event_type": "equity_compensation_registration",
        "securities_offered": "Common Stock under 2024 Equity Incentive Plan",
        "shares_offered": 3000000,
        "price_per_share": None,
        "gross_proceeds": None,
        "net_proceeds": None,
        "warrants_included": False,
        "pre_funded_warrants_included": False,
        "status": "effective",
        "parse_status": "success",
    }


# Fixture: Shelf registration
@pytest.fixture
def maia_shelf_registration():
    """MAIA S-3 shelf registration."""
    return {
        "form": "S-3",
        "accession_number": "0001493152-24-001234",
        "filing_date": "2024-09-01",
        "report_date": None,
        "event_type": "shelf_registration",
        "securities_offered": "Mixed Securities",
        "shelf_amount": 100000000,
        "status": "effective",
        "parse_status": "success",
    }


# Test: Extract share counts from XBRL fixture
def test_extract_share_counts_from_xbrl(maia_xbrl_fixture):
    """Extract share counts from XBRL data."""
    from sources.sec_capital_structure import extract_share_counts_from_xbrl

    result = extract_share_counts_from_xbrl(maia_xbrl_fixture)

    assert result["common_shares_outstanding"] == 60671491
    assert result["common_shares_issued"] == 60671491
    assert result["weighted_average_basic_shares"] == 59230103
    assert result["weighted_average_diluted_shares"] == 59230103
    assert result["source"] == "sec_companyfacts"
    assert result["status"] == "ok"


# Test: Parse public offering terms
def test_parse_public_offering_terms(maia_march_2026_offering):
    """Parse public offering terms."""
    from sources.sec_offering_terms import parse_offering_terms

    result = parse_offering_terms(maia_march_2026_offering)

    assert result["shares_offered"] == 20000000
    assert result["price_per_share"] == 1.50
    assert result["gross_proceeds"] == 30000000
    assert result["net_proceeds"] == 28000000
    assert result["warrants_included"] is False
    assert result["pre_funded_warrants_included"] is False
    assert result["parse_status"] == "success"


# Test: No pre-funded warrants when not disclosed
def test_no_pre_funded_warrants_when_not_disclosed():
    """No pre-funded warrants when not disclosed."""
    from sources.sec_offering_terms import parse_offering_terms

    offering = {
        "form": "424B5",
        "accession_number": "0001104659-26-034567",
        "filing_date": "2026-03-17",
        "securities_offered": "Common Stock",
        "shares_offered": 10000000,
        "price_per_share": 2.00,
        "gross_proceeds": 20000000,
    }

    result = parse_offering_terms(offering)

    assert result["pre_funded_warrants_included"] is False
    assert result["warrants_included"] is False


# Test: No common warrants when not disclosed
def test_no_common_warrants_when_not_disclosed():
    """No common warrants when not disclosed."""
    from sources.sec_offering_terms import parse_offering_terms

    offering = {
        "form": "424B5",
        "accession_number": "0001104659-26-034567",
        "filing_date": "2026-03-17",
        "securities_offered": "Common Stock",
        "shares_offered": 10000000,
        "price_per_share": 2.00,
    }

    result = parse_offering_terms(offering)

    assert result["warrants_included"] is False


# Test: Fully diluted calculation
def test_fully_diluted_calculation():
    """Calculate fully diluted estimates."""
    from sources.sec_capital_structure import calculate_fully_diluted

    share_data = {
        "common_shares_outstanding": 60671491,
        "options_outstanding": 20000000,
        "rsus_outstanding": 4362363,
        "warrants_outstanding": 0,
        "convertible_debt_shares_equivalent": 0,
    }

    result = calculate_fully_diluted(share_data)

    assert result["fully_diluted_low_estimate"] == 85033854
    assert result["fully_diluted_high_estimate"] == 88033854


# Test: Dilution overhang calculation
def test_dilution_overhang_calculation():
    """Calculate dilution overhang percentages."""
    from sources.sec_capital_structure import calculate_dilution_overhang

    share_data = {
        "common_shares_outstanding": 60671491,
        "fully_diluted_low_estimate": 85033854,
        "fully_diluted_high_estimate": 88033854,
    }

    result = calculate_dilution_overhang(share_data)

    # (85033854 - 60671491) / 60671491 * 100 = 40.16%
    assert 40.0 <= result["dilution_overhang_percent_low"] <= 41.0
    # (88033854 - 60671491) / 60671491 * 100 = 45.11%
    assert 45.0 <= result["dilution_overhang_percent_high"] <= 46.0


# Test: Known unknowns captured
def test_known_unknowns_captured():
    """Known unknowns captured when data missing."""
    from sources.sec_capital_structure import extract_capital_structure

    inventory_data = {
        "ticker": "MAIA",
        "cik": "0001878313",
        "filings": [],
    }

    xbrl_data = {
        "quarterly_metrics": {
            "common_shares_outstanding": {"value": 60671491, "status": "ok"}
        }
    }

    result = extract_capital_structure(inventory_data, xbrl_data)

    # Should capture that warrant count is not disclosed
    assert len(result["known_unknowns"]) > 0
    assert any("warrant" in ku.lower() for ku in result["known_unknowns"])


# Test: Parse failure preservation
def test_parse_failure_preservation():
    """Parse failures preserved with provenance."""
    from sources.sec_offering_terms import parse_offering_terms

    offering = {
        "form": "424B5",
        "accession_number": "0001104659-26-999999",
        "filing_date": "2026-03-17",
        "securities_offered": "Unknown Securities",
    }

    result = parse_offering_terms(offering)

    assert result["parse_status"] in ["degraded", "partial", "failed"]
    if result.get("failure_reason"):
        assert len(result["failure_reason"]) > 0


# Test: MAIA reconciliation
def test_maia_reconciliation(maia_xbrl_fixture, maia_march_2026_offering):
    """MAIA reconciliation against approved values."""
    from sources.sec_capital_structure import reconcile_maia_capital_structure

    target_values = {
        "common_shares_outstanding": 60671491,
        "march_2026_offering_shares": 20000000,
        "march_2026_offering_price": 1.50,
        "march_2026_gross_proceeds": 30000000,
        "march_2026_pre_funded_warrants": False,
        "march_2026_common_warrants": False,
        "fully_diluted_low_estimate": 85033854,
        "fully_diluted_high_estimate": 88033854,
    }

    extracted_values = {
        "common_shares_outstanding": 60671491,
        "recent_offerings": [maia_march_2026_offering],
        "fully_diluted_low_estimate": 85033854,
        "fully_diluted_high_estimate": 88033854,
    }

    result = reconcile_maia_capital_structure(extracted_values, target_values)

    assert result["status"] in ["matched", "reconciled_with_differences"]
    assert result["common_shares_outstanding_match"] is True


# Test: NVDA non-small-cap framing
def test_nvda_non_small_cap_framing():
    """NVDA uses appropriate large-cap framing."""
    from sources.sec_capital_structure import generate_capital_structure_report

    nvda_data = {
        "ticker": "NVDA",
        "cik": "0001045810",
        "company_name": "NVIDIA CORP",
        "common_shares_outstanding": 24000000000,  # 24B shares
        "market_cap_category": "large_cap",
    }

    markdown = generate_capital_structure_report(nvda_data)

    # Should not use small-cap/pre-revenue language
    assert "pre-revenue" not in markdown.lower()
    assert "small-cap" not in markdown.lower()
    assert "dilution overhang" not in markdown.lower() or "context" in markdown.lower()


# Test: No buy/sell/hold language
def test_no_buy_sell_hold_language():
    """No investment recommendation language."""
    from sources.sec_capital_structure import generate_capital_structure_report

    data = {
        "ticker": "MAIA",
        "cik": "0001878313",
        "company_name": "MAIA Biotechnology, Inc.",
        "common_shares_outstanding": 60671491,
    }

    markdown = generate_capital_structure_report(data)

    # Should not contain investment language
    assert "buy" not in markdown.lower()
    assert "sell" not in markdown.lower()
    assert "hold" not in markdown.lower()
    assert "recommend" not in markdown.lower()
    assert "should purchase" not in markdown.lower()
    assert "should invest" not in markdown.lower()


# Test: Safety flags correct
def test_safety_flags():
    """Safety flags correctly set."""
    from sources.sec_capital_structure import extract_capital_structure

    inventory_data = {"ticker": "MAIA", "cik": "0001878313", "filings": []}
    xbrl_data = {
        "quarterly_metrics": {
            "common_shares_outstanding": {"value": 60671491, "status": "ok"}
        }
    }

    result = extract_capital_structure(inventory_data, xbrl_data)

    assert result["safety"]["report_only"] is True
    assert result["safety"]["alerts_generated"] is False
    assert result["safety"]["openinsider_spreadsheet_used"] is False
    assert result["safety"]["telegram_sent"] is False
    assert result["safety"]["email_sent"] is False
    assert result["safety"]["scheduled_tasks_modified"] is False
    assert result["safety"]["env_printed_or_changed"] is False
    assert result["safety"]["buy_sell_hold_language_used"] is False


# Test: No secrets in outputs
def test_no_secrets_in_output():
    """No secrets in JSON/Markdown outputs."""
    from sources.sec_capital_structure import extract_capital_structure

    inventory_data = {"ticker": "MAIA", "cik": "0001878313", "filings": []}
    xbrl_data = {
        "quarterly_metrics": {
            "common_shares_outstanding": {"value": 60671491, "status": "ok"}
        }
    }

    result = extract_capital_structure(inventory_data, xbrl_data)

    result_str = json.dumps(result)

    # No secrets
    assert "TELEGRAM_BOT_TOKEN" not in result_str
    assert "TELEGRAM_CHAT_ID" not in result_str
    assert "SMTP_PASSWORD" not in result_str
    assert "sk-ant-" not in result_str
    assert "API_KEY" not in result_str


# Test: No alert code paths
def test_no_alert_code_paths(monkeypatch):
    """No alert code is called."""
    from sources.sec_capital_structure import extract_capital_structure

    # Mock alert functions to raise if called
    def mock_send_telegram(*args, **kwargs):
        raise AssertionError("Telegram send called")

    def mock_send_email(*args, **kwargs):
        raise AssertionError("Email send called")

    # Monkeypatch if modules exist
    try:
        import notifier.telegram_notifier as telegram_notifier

        monkeypatch.setattr(telegram_notifier, "send_telegram_message", mock_send_telegram)
    except ImportError:
        pass

    try:
        import notifier.email_notifier as email_notifier

        monkeypatch.setattr(email_notifier, "send_email", mock_send_email)
    except ImportError:
        pass

    inventory_data = {"ticker": "MAIA", "cik": "0001878313", "filings": []}
    xbrl_data = {
        "quarterly_metrics": {
            "common_shares_outstanding": {"value": 60671491, "status": "ok"}
        }
    }

    # Should not raise
    result = extract_capital_structure(inventory_data, xbrl_data)
    assert result is not None


# Test: OpenInsider spreadsheet NOT required
def test_openinsider_not_required():
    """OpenInsider spreadsheet is not required or used."""
    from sources.sec_capital_structure import extract_capital_structure

    inventory_data = {"ticker": "MAIA", "cik": "0001878313", "filings": []}
    xbrl_data = {
        "quarterly_metrics": {
            "common_shares_outstanding": {"value": 60671491, "status": "ok"}
        }
    }

    # Should work without OpenInsider data
    result = extract_capital_structure(inventory_data, xbrl_data)

    assert result is not None
    assert result["safety"]["openinsider_spreadsheet_used"] is False
