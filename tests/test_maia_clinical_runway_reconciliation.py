"""Tests for MAIA Clinical/Regulatory/Cash Runway Reconciliation (CP23B-Fix).

These tests verify that placeholder values have been replaced with actual or best-estimate
values, and that the reconciliation requirements from CP23B-Fix have been met.
"""

import json
import re
from pathlib import Path


def load_reconciled_json():
    """Load the reconciled MAIA clinical/runway JSON."""
    json_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_reconciled_markdown():
    """Load the reconciled MAIA clinical/runway markdown."""
    md_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway_report.md")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


def test_reconciliation_status_exists():
    """Test that reconciliation_status section exists in JSON."""
    data = load_reconciled_json()
    assert "reconciliation_status" in data, "reconciliation_status section missing from JSON"

    status = data["reconciliation_status"]
    assert "placeholder_cash_removed" in status
    # CP23B-Fix2 uses different field names than CP23B-Fix
    assert "actual_10q_cash_extracted" in status or "actual_cash_balance_used" in status
    assert "actual_10q_expenses_extracted" in status or "actual_burn_values_used" in status
    assert "remaining_unresolved_fields" in status


def test_checkpoint_is_cp23b_fix():
    """Test that checkpoint is CP23B-Fix or CP23B-Fix2."""
    data = load_reconciled_json()
    # Accept both CP23B-Fix and CP23B-Fix2 (Fix2 supersedes Fix)
    assert data["research_checkpoint"] in ["CP23B-Fix", "CP23B-Fix2"], \
        f"Checkpoint should be CP23B-Fix or CP23B-Fix2, got {data['research_checkpoint']}"
    assert "reconciliation_date" in data, "reconciliation_date missing"


def test_placeholder_cash_not_present_without_source():
    """Test that cash has proper sourcing (estimated or actual)."""
    data = load_reconciled_json()

    financial = data["financial_snapshot"]

    # Check that source is documented
    assert "source" in financial, "Financial snapshot missing source field"

    # CP23B-Fix2 uses ACTUAL values, CP23B-Fix uses estimated
    source = financial["source"].lower()
    is_actual = "actual" in source and "10-q" in source
    is_estimated = "estimated" in source or "estimate" in financial.get("confidence", "").lower()

    assert is_actual or is_estimated, \
        "Cash balance must be documented as either ACTUAL (from 10-Q) or estimated"

    # Check that reconciliation notes exist
    assert "reconciliation_notes" in financial, "Missing reconciliation_notes"
    assert len(financial["reconciliation_notes"]) > 0, "reconciliation_notes should not be empty"


def test_burn_rate_not_exact_10m_placeholder():
    """Test that quarterly burn is not exactly $10M placeholder."""
    data = load_reconciled_json()

    financial = data["financial_snapshot"]
    net_cash_used = financial["net_cash_used_in_operations"]

    # The reconciliation changed this from $10M to $9.5M
    assert net_cash_used != 10_000_000, \
        "Quarterly burn should not be exactly $10M placeholder (should be reconciled value like $9.5M)"

    # It should be a reasonable biotech burn rate
    assert 5_000_000 <= net_cash_used <= 20_000_000, \
        "Quarterly burn should be in reasonable biotech range ($5M-$20M)"


def test_cash_runway_scenarios_use_numeric_values():
    """Test that runway scenarios use numeric actual/estimated values."""
    data = load_reconciled_json()

    scenarios = data["cash_runway_scenarios"]
    assert len(scenarios) == 3, "Should have 3 runway scenarios (low/base/high)"

    for scenario in scenarios:
        assert isinstance(scenario["quarterly_burn"], (int, float)), "quarterly_burn should be numeric"
        assert isinstance(scenario["monthly_burn"], (int, float)), "monthly_burn should be numeric"
        assert isinstance(scenario["cash_balance"], (int, float)), "cash_balance should be numeric"
        assert isinstance(scenario["runway_months"], (int, float)), "runway_months should be numeric"

        assert scenario["quarterly_burn"] > 0, "quarterly_burn must be positive"
        assert scenario["monthly_burn"] > 0, "monthly_burn must be positive"
        assert scenario["cash_balance"] > 0, "cash_balance must be positive"
        assert scenario["runway_months"] > 0, "runway_months must be positive"


def test_runway_scenarios_ordering():
    """Test that low/base/high runway scenarios are properly ordered."""
    data = load_reconciled_json()

    scenarios = {s["scenario"]: s for s in data["cash_runway_scenarios"]}

    low = scenarios["low"]
    base = scenarios["base"]
    high = scenarios["high"]

    # Runway months should decrease from low -> base -> high (higher burn = shorter runway)
    assert low["runway_months"] > base["runway_months"], \
        "Low scenario should have longer runway than base"
    assert base["runway_months"] > high["runway_months"], \
        "Base scenario should have longer runway than high"

    # Quarterly burn should increase from low -> base -> high
    assert low["quarterly_burn"] < base["quarterly_burn"], \
        "Low scenario should have lower burn than base"
    assert base["quarterly_burn"] < high["quarterly_burn"], \
        "Base scenario should have lower burn than high"


def test_thio_101_not_extract_from_filing():
    """Test that THIO-101 fields don't contain 'Extract from filing' placeholder."""
    data = load_reconciled_json()

    thio_101 = next((p for p in data["clinical_programs"] if p["program_name"] == "THIO-101"), None)
    assert thio_101 is not None, "THIO-101 program not found"

    # Convert to JSON string to search for placeholder text
    thio_101_str = json.dumps(thio_101, indent=2)

    assert "Extract from filing" not in thio_101_str, \
        "THIO-101 should not contain 'Extract from filing' placeholder (use 'not disclosed' instead)"

    # Should use 'not disclosed' for fields without public disclosure
    assert "not disclosed" in thio_101_str.lower(), \
        "THIO-101 should use 'not disclosed' for undisclosed fields"


def test_milestone_timing_has_timing_basis():
    """Test that milestones have timing_basis field (disclosed/inferred/not disclosed)."""
    data = load_reconciled_json()

    milestones = data["milestone_calendar"]
    assert len(milestones) > 0, "Milestone calendar should not be empty"

    valid_timing_bases = ["disclosed", "inferred", "not disclosed"]

    for milestone in milestones:
        assert "timing_basis" in milestone, \
            f"Milestone '{milestone['milestone']}' missing timing_basis field"

        timing_basis = milestone["timing_basis"]
        assert timing_basis in valid_timing_bases, \
            f"Milestone '{milestone['milestone']}' has invalid timing_basis: {timing_basis} " \
            f"(must be one of {valid_timing_bases})"


def test_cp23a_fix_financing_integrated():
    """Test that CP23A-Fix financing data is integrated."""
    data = load_reconciled_json()

    financial = data["financial_snapshot"]

    # Should have March 2026 offering proceeds
    assert "march_2026_offering_proceeds" in financial, \
        "Missing March 2026 offering proceeds from CP23A-Fix"

    proceeds = financial["march_2026_offering_proceeds"]
    assert proceeds == 28_000_000, \
        "March 2026 base offering proceeds should be $28M from CP23A-Fix"

    # Should have overallotment option
    assert "march_2026_offering_with_overallotment" in financial, \
        "Missing March 2026 overallotment proceeds"

    overallotment = financial["march_2026_offering_with_overallotment"]
    assert overallotment == 32_300_000, \
        "March 2026 overallotment proceeds should be $32.3M from CP23A-Fix"


def test_dilution_timing_risk_updated():
    """Test that dilution timing risk uses corrected runway estimates."""
    data = load_reconciled_json()

    dilution = data["dilution_timing_risk"]

    # Should reference corrected runway
    assert "current_runway_estimate" in dilution
    assert "months" in dilution["current_runway_estimate"].lower()

    # Should have CP23A-Fix fully diluted shares
    assert "fully_diluted_from_cp23a" in dilution
    assert "85,033,854" in dilution["fully_diluted_from_cp23a"], \
        "Should reference CP23A-Fix low-case fully diluted shares"


def test_no_secrets_in_json():
    """Test that JSON contains no secrets."""
    json_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway.json")
    content = json_path.read_text(encoding="utf-8")

    secret_patterns = [
        r"TELEGRAM_BOT_TOKEN",
        r"TELEGRAM_CHAT_ID",
        r"SMTP_PASSWORD",
        r"SMTP_USERNAME",
        r"GMAIL_APP_PASSWORD",
        r"sk-ant-",
        r"ETHERSCAN_API_KEY",
        r"SEC_API_IO_API_KEY",
        r"BEGIN PRIVATE KEY",
        r"password\s*=",
        r"token\s*=",
        r"chat_id\s*=",
    ]

    for pattern in secret_patterns:
        assert not re.search(pattern, content, re.IGNORECASE), \
            f"JSON contains secret pattern: {pattern}"


def test_no_secrets_in_markdown():
    """Test that markdown contains no secrets."""
    md_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway_report.md")
    content = md_path.read_text(encoding="utf-8")

    secret_patterns = [
        r"TELEGRAM_BOT_TOKEN",
        r"TELEGRAM_CHAT_ID",
        r"SMTP_PASSWORD",
        r"SMTP_USERNAME",
        r"GMAIL_APP_PASSWORD",
        r"sk-ant-",
        r"ETHERSCAN_API_KEY",
        r"SEC_API_IO_API_KEY",
        r"BEGIN PRIVATE KEY",
    ]

    for pattern in secret_patterns:
        assert not re.search(pattern, content, re.IGNORECASE), \
            f"Markdown contains secret pattern: {pattern}"


def test_safety_confirmations_exist():
    """Test that safety confirmations section exists."""
    data = load_reconciled_json()

    assert "safety_confirmations" in data, "Missing safety_confirmations section"

    safety = data["safety_confirmations"]
    assert safety["no_openinsider_spreadsheet_used"] is True
    assert safety["no_telegram_sent"] is True
    assert safety["no_email_sent"] is True
    assert safety["no_scheduled_tasks_modified"] is True
    assert safety["no_scheduled_tasks_triggered"] is True
    assert safety["no_secrets_in_output"] is True


def test_no_alert_code_references():
    """Test that reconciliation script doesn't reference alert/email/telegram code."""
    recon_script = Path("scripts/maia_clinical_runway_reconciliation.py")
    content = recon_script.read_text(encoding="utf-8")

    forbidden_patterns = [
        r"import\s+telegram",
        r"from\s+telegram",
        r"import\s+smtplib",
        r"from\s+smtplib",
        r"send_telegram",
        r"send_email",
        r"ALERT_ENABLE",
        r"trigger_alert",
    ]

    for pattern in forbidden_patterns:
        assert not re.search(pattern, content, re.IGNORECASE), \
            f"Reconciliation script contains forbidden pattern: {pattern}"


def test_markdown_has_reconciliation_section():
    """Test that markdown report has reconciliation status section."""
    content = load_reconciled_markdown()

    assert "RECONCILIATION STATUS" in content, \
        "Markdown should have RECONCILIATION STATUS section"

    assert "Remaining Unresolved Fields" in content, \
        "Markdown should document remaining unresolved fields"

    assert "CP23B-Fix" in content, \
        "Markdown should reference CP23B-Fix checkpoint"


def test_estimated_values_clearly_labeled():
    """Test that values are clearly labeled (estimated or actual)."""
    data = load_reconciled_json()

    financial = data["financial_snapshot"]

    # Should have clear source labeling
    assert "source" in financial, "Missing source field"

    source = financial["source"].lower()
    confidence = financial.get("confidence", "").lower()

    # CP23B-Fix2 uses ACTUAL, CP23B-Fix uses estimated
    is_actual = "actual" in source and "10-q" in source
    is_estimated = "estimated" in source or "estimate" in confidence

    assert is_actual or is_estimated, \
        "Values must be clearly labeled as either ACTUAL (from 10-Q) or estimated"

    # Should have reconciliation notes
    assert "reconciliation_notes" in financial, "Missing reconciliation_notes"
    assert len(financial["reconciliation_notes"]) > 0, "Reconciliation notes should not be empty"


def test_cp23a_fix_referenced_in_data_sources():
    """Test that CP23A-Fix is referenced in data sources."""
    data = load_reconciled_json()

    data_sources = data["data_sources"]
    assert any("CP23A-Fix" in source for source in data_sources), \
        "Data sources should reference CP23A-Fix"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
