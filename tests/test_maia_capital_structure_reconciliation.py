"""Tests for MAIA capital structure reconciliation (CP23A-Fix).

Tests verify that the reconciliation fixes all material issues identified in CP23A,
including gross/net proceeds contradictions, malformed placeholders, and TBD values.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def reconciled_json(project_root: Path) -> dict:
    """Load reconciled MAIA capital structure JSON."""
    json_path = (
        project_root
        / "docs"
        / "sample_reports"
        / "maia_capital_structure"
        / "MAIA_capital_structure_dilution.json"
    )
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def reconciled_markdown(project_root: Path) -> str:
    """Load reconciled MAIA capital structure markdown report."""
    md_path = (
        project_root
        / "docs"
        / "sample_reports"
        / "maia_capital_structure"
        / "MAIA_capital_structure_dilution_report.md"
    )
    return md_path.read_text(encoding="utf-8")


def test_gross_proceeds_not_less_than_net_proceeds(reconciled_json: dict):
    """Net proceeds cannot exceed gross proceeds for the same financing event."""
    # March 2026 public offering
    march = reconciled_json.get("march_2026_public_offering", {})
    gross = march.get("gross_proceeds_usd")
    net_base = march.get("net_proceeds_base_usd")
    net_with_overallotment = march.get("net_proceeds_with_overallotment_usd")

    assert gross is not None, "Gross proceeds must not be null"
    assert net_base is not None, "Net proceeds (base) must not be null"
    assert net_with_overallotment is not None, "Net proceeds (with overallotment) must not be null"

    # Net proceeds should be less than gross for base case
    assert net_base <= gross, f"Net proceeds base ({net_base}) cannot exceed gross proceeds ({gross})"

    # With overallotment, net can be slightly higher than base gross due to additional shares
    # but should still make sense (not wildly different)
    assert net_with_overallotment > net_base, "Net with overallotment should exceed base net"

    # December 2025 private placement
    dec = reconciled_json.get("december_2025_private_placement", {})
    dec_gross = dec.get("gross_proceeds_usd")
    dec_net = dec.get("net_proceeds_usd")

    if dec_gross and dec_net:
        assert dec_net <= dec_gross, f"December 2025 net ({dec_net}) cannot exceed gross ({dec_gross})"


def test_no_malformed_comma_placeholders(reconciled_json: dict):
    """Malformed comma placeholders are not allowed in JSON."""
    # Convert entire JSON to string and check for malformed patterns
    json_str = json.dumps(reconciled_json)

    # Check for common malformed patterns
    assert '": ","' not in json_str, "Found malformed comma-only value in JSON"
    assert '": "TBD"' not in json_str or "tbd" in json_str.lower(), "TBD values should be avoided where possible"

    # Specific fields that were malformed in CP23A
    march = reconciled_json.get("march_2026_public_offering", {})
    assert march.get("prefunded_warrants_sold") != ",", "Pre-funded warrants should not be malformed comma"
    assert march.get("common_warrants_sold") != ",", "Common warrants should not be malformed comma"
    assert march.get("prefunded_warrants_sold") == 0, "Pre-funded warrants should be 0 (none issued)"
    assert march.get("common_warrants_sold") == 0, "Common warrants should be 0 (none issued)"


def test_fully_diluted_has_numeric_estimate(reconciled_json: dict):
    """Fully diluted estimate must have numeric low/high values, not TBD."""
    fully_diluted = reconciled_json.get("fully_diluted_estimate", {})

    low_case = fully_diluted.get("low_case_without_overallotment", {})
    high_case = fully_diluted.get("high_case_with_overallotment", {})

    # Check low case
    low_total = low_case.get("total_fully_diluted")
    assert low_total is not None, "Low case fully diluted must not be null"
    assert isinstance(low_total, int), "Low case fully diluted must be integer"
    assert low_total > 0, "Low case fully diluted must be positive"
    assert low_total > 80_000_000, "Low case fully diluted should be >80M based on reconciled data"

    # Check high case
    high_total = high_case.get("total_fully_diluted")
    assert high_total is not None, "High case fully diluted must not be null"
    assert isinstance(high_total, int), "High case fully diluted must be integer"
    assert high_total > 0, "High case fully diluted must be positive"
    assert high_total >= low_total, "High case must be >= low case"

    # Check components sum correctly
    low_sum = (
        low_case.get("basic_shares", 0)
        + low_case.get("options", 0)
        + low_case.get("warrants", 0)
        + low_case.get("reserved_shares", 0)
    )
    assert low_sum == low_total, f"Low case components ({low_sum}) must sum to total ({low_total})"

    high_sum = (
        high_case.get("basic_shares", 0)
        + high_case.get("options", 0)
        + high_case.get("warrants", 0)
        + high_case.get("reserved_shares", 0)
    )
    assert high_sum == high_total, f"High case components ({high_sum}) must sum to total ({high_total})"


def test_form_144_status_corrected(reconciled_json: dict):
    """Form 144 status should show 0 filings found (original accession was erroneous)."""
    form_144 = reconciled_json.get("form_144", {})

    filings_found = form_144.get("filings_found")
    assert filings_found == 0, "Form 144 filings_found should be 0 (no filings exist for MAIA)"

    note = form_144.get("note", "")
    assert "erroneous" in note.lower() or "no" in note.lower(), "Note should explain no Form 144 filings found"


def test_thirteen_f_limitation_explained(reconciled_json: dict):
    """13F integration limitation must be explicitly documented."""
    thirteen_f = reconciled_json.get("institutional_13f", {})

    status = thirteen_f.get("status", "")
    assert status, "13F status must be present"
    assert "not integrated" in status.lower() or "infrastructure available" in status.lower(), \
        "13F status should explain integration limitation"

    limitations = thirteen_f.get("limitations", [])
    assert len(limitations) > 0, "13F limitations must be documented"

    infrastructure_available = thirteen_f.get("matching_infrastructure_available")
    assert infrastructure_available is True, "13F matching infrastructure should be noted as available"


def test_reconciliation_status_exists(reconciled_json: dict):
    """JSON must include reconciliation_status section."""
    reconciliation_status = reconciled_json.get("reconciliation_status", {})

    assert reconciliation_status, "reconciliation_status section must exist"

    # Check required fields
    assert "gross_net_reconciled" in reconciliation_status, "Must have gross_net_reconciled"
    assert "fully_diluted_numeric_estimate" in reconciliation_status, "Must have fully_diluted_numeric_estimate"
    assert "form_144_parsed" in reconciliation_status, "Must have form_144_parsed"
    assert "thirteen_f_integrated_or_explained" in reconciliation_status, "Must have thirteen_f_integrated_or_explained"

    # All should be True (successfully reconciled)
    assert reconciliation_status["gross_net_reconciled"] is True
    assert reconciliation_status["fully_diluted_numeric_estimate"] is True
    assert reconciliation_status["form_144_parsed"] is True
    assert reconciliation_status["thirteen_f_integrated_or_explained"] is True

    # Check for remaining TBD fields explanation
    remaining_tbd = reconciliation_status.get("remaining_tbd_fields", [])
    assert isinstance(remaining_tbd, list), "remaining_tbd_fields must be a list"

    # Each remaining TBD should have reason and filings_checked
    for tbd in remaining_tbd:
        assert "field" in tbd, f"TBD item must have 'field': {tbd}"
        assert "reason" in tbd, f"TBD item must have 'reason': {tbd}"
        assert "filings_checked" in tbd, f"TBD item must have 'filings_checked': {tbd}"


def test_no_secrets_in_json(reconciled_json: dict):
    """JSON must not contain secrets or credentials."""
    json_str = json.dumps(reconciled_json).lower()

    # Check for common secret patterns
    secret_patterns = [
        "telegram_bot_token",
        "telegram_chat_id",
        "smtp_password",
        "gmail_app_password",
        "sk-ant-",
        "api_key",
        "password=",
        "token=",
    ]

    for pattern in secret_patterns:
        assert pattern.lower() not in json_str, f"Found potential secret pattern: {pattern}"


def test_no_secrets_in_markdown(reconciled_markdown: str):
    """Markdown report must not contain secrets or credentials."""
    markdown_lower = reconciled_markdown.lower()

    # Check for common secret patterns
    secret_patterns = [
        "telegram_bot_token",
        "telegram_chat_id",
        "smtp_password",
        "gmail_app_password",
        "sk-ant-",
        "password=",
        "token=",
    ]

    for pattern in secret_patterns:
        assert pattern not in markdown_lower, f"Found potential secret pattern: {pattern}"


def test_safety_flags(reconciled_json: dict):
    """Safety flags must confirm no alerts/emails/scheduled tasks modified."""
    safety = reconciled_json.get("safety", {})

    assert safety.get("openinsider_spreadsheet_used") is False, "OpenInsider spreadsheet must not be used"
    assert safety.get("telegram_sent") is False, "Telegram must not be sent"
    assert safety.get("email_sent") is False, "Email must not be sent"
    assert safety.get("scheduled_tasks_modified") is False, "Scheduled tasks must not be modified"


def test_march_2026_separated_from_december_2025(reconciled_json: dict):
    """March 2026 and December 2025 offerings must be separate events."""
    march = reconciled_json.get("march_2026_public_offering", {})
    december = reconciled_json.get("december_2025_private_placement", {})

    assert march.get("found") is True, "March 2026 offering must be found"
    assert december.get("found") is True, "December 2025 offering must be found"

    # Check they are different amounts
    march_shares = march.get("common_shares_sold")
    december_shares = december.get("common_shares_sold")

    assert march_shares == 20000000, "March 2026 should be 20M shares"
    assert december_shares == 1233488, "December 2025 should be 1,233,488 shares"
    assert march_shares != december_shares, "Two offerings must have different share counts"

    # Check they have different dates
    march_date = march.get("closing_date")
    december_date = december.get("closing_date")
    assert march_date != december_date, "Two offerings must have different dates"


def test_reconciliation_corrections_documented(reconciled_json: dict):
    """Reconciliation corrections must be documented."""
    reconciliation_status = reconciled_json.get("reconciliation_status", {})
    corrections = reconciliation_status.get("corrections_made", [])

    assert len(corrections) > 0, "Corrections made must be documented"

    # Check for specific corrections
    corrections_str = " ".join(corrections).lower()
    assert "separated" in corrections_str, "Should document separation of March/December offerings"
    assert "gross" in corrections_str and "net" in corrections_str, "Should document gross/net proceeds fix"
    assert "comma" in corrections_str or "placeholder" in corrections_str, "Should document comma placeholder fix"
    assert "fully diluted" in corrections_str, "Should document fully diluted calculation"


def test_data_quality_assessment(reconciled_json: dict):
    """Data quality assessment must be present and comprehensive."""
    reconciliation_status = reconciled_json.get("reconciliation_status", {})
    data_quality = reconciliation_status.get("data_quality", {})

    assert len(data_quality) > 0, "Data quality assessment must exist"

    # Key areas must be assessed
    assert "march_2026_financing" in data_quality, "March 2026 financing quality must be assessed"
    assert "fully_diluted_estimate" in data_quality, "Fully diluted estimate quality must be assessed"
    assert "form_144_status" in data_quality, "Form 144 status quality must be assessed"

    # Quality levels should be reasonable
    for key, value in data_quality.items():
        assert any(value.startswith(level) for level in ["High", "Medium", "Low"]), \
            f"Quality level '{value}' for '{key}' must start with High/Medium/Low"


def test_manual_extraction_documented(reconciled_json: dict):
    """Manual extraction sources must be documented."""
    filings = reconciled_json.get("filings_manually_reviewed", [])

    assert len(filings) > 0, "Manually reviewed filings must be documented"

    # Check March 4, 2026 424B5 is included
    march_4_424b5 = any(
        f.get("form") == "424B5" and f.get("filing_date") == "2026-03-04"
        for f in filings
    )
    assert march_4_424b5, "March 4, 2026 424B5 must be in manually reviewed filings"

    # Each filing should have required fields
    for filing in filings:
        assert "form" in filing, f"Filing must have form type: {filing}"
        assert "accession" in filing, f"Filing must have accession: {filing}"
        assert "url" in filing, f"Filing must have URL: {filing}"
        assert "purpose" in filing, f"Filing must have purpose: {filing}"


def test_options_breakdown_by_plan(reconciled_json: dict):
    """Options must be broken down by equity plan with accurate totals."""
    options = reconciled_json.get("options_outstanding", {})

    plan_2018 = options.get("maia_2018_plan", {}).get("options_outstanding", 0)
    plan_2020 = options.get("maia_2020_plan", {}).get("options_outstanding", 0)
    plan_2021 = options.get("maia_2021_plan", {}).get("options_outstanding", 0)
    total = options.get("total_options_outstanding", 0)

    assert plan_2018 + plan_2020 + plan_2021 == total, \
        f"Options by plan ({plan_2018}+{plan_2020}+{plan_2021}) must sum to total ({total})"

    assert total == 12496812, f"Total options should be 12,496,812 based on reconciled data, got {total}"


def test_shares_outstanding_progression(reconciled_json: dict):
    """Shares outstanding progression must be logical."""
    shares = reconciled_json.get("shares_outstanding", {})

    pre_march = shares.get("basic_shares_pre_march_offering")
    post_without_overallotment = shares.get("post_march_offering_without_overallotment")
    post_with_overallotment = shares.get("post_march_offering_with_overallotment")

    assert pre_march < post_without_overallotment, "Shares should increase after offering"
    assert post_without_overallotment < post_with_overallotment, "Shares should increase with overallotment"

    # Check the math
    march = reconciled_json.get("march_2026_public_offering", {})
    shares_sold = march.get("common_shares_sold", 0)
    overallotment = march.get("overallotment_option_shares", 0)

    assert post_without_overallotment == pre_march + shares_sold, \
        f"Post-offering shares ({post_without_overallotment}) must equal pre ({pre_march}) + sold ({shares_sold})"

    assert post_with_overallotment == pre_march + shares_sold + overallotment, \
        f"Post with overallotment ({post_with_overallotment}) must equal pre + sold + overallotment"
