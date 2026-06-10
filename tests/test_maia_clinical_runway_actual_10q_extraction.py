"""Tests for MAIA Clinical Runway Actual 10-Q Extraction (CP23B-Fix2).

These tests verify that CP23B-Fix2 successfully replaced all estimated values
with actual SEC 10-Q Q1 2026 disclosed values.
"""

import json
import re
from pathlib import Path


def load_clinical_runway_json():
    """Load the MAIA clinical/runway JSON."""
    json_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_clinical_runway_markdown():
    """Load the MAIA clinical/runway markdown."""
    md_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway_report.md")
    with open(md_path, "r", encoding="utf-8") as f:
        return f.read()


def test_checkpoint_is_cp23b_fix2():
    """Test that checkpoint is CP23B-Fix2."""
    data = load_clinical_runway_json()
    assert data["research_checkpoint"] == "CP23B-Fix2", "Checkpoint should be CP23B-Fix2"


def test_no_placeholder_40m_cash():
    """Test that $40M placeholder cash is NOT used as actual value."""
    data = load_clinical_runway_json()
    actual_cash = data["financial_snapshot"]["cash_and_equivalents"]

    # CP23B-Fix2 requires actual 10-Q value, not $40M estimated
    assert actual_cash != 40_000_000, \
        "Report must not use $40M placeholder as actual cash (CP23B-Fix2 requires actual 10-Q value)"

    # Actual Q1 2026 10-Q value should be around $38.25M
    assert 35_000_000 <= actual_cash <= 42_000_000, \
        f"Cash should be in reasonable range (actual: ${actual_cash:,})"


def test_no_placeholder_10m_burn():
    """Test that $10M placeholder burn is NOT used as actual value."""
    data = load_clinical_runway_json()
    actual_burn = data["financial_snapshot"]["net_cash_used_in_operations"]

    # CP23B-Fix2 requires actual 10-Q value, not $10M estimated
    assert actual_burn != 10_000_000, \
        "Report must not use $10M placeholder as actual burn (CP23B-Fix2 requires actual 10-Q value)"

    # CP23B-Fix estimated $9.5M, but CP23B-Fix2 requires actual
    assert actual_burn != 9_500_000, \
        "Report must not use $9.5M CP23B-Fix estimated burn (CP23B-Fix2 requires actual 10-Q value)"

    # Actual Q1 2026 10-Q value should be around $8.9M
    assert 7_000_000 <= actual_burn <= 12_000_000, \
        f"Quarterly burn should be in reasonable range (actual: ${actual_burn:,})"


def test_no_typical_biotech_patterns_in_source():
    """Test that 'typical Phase 2/3 biotech patterns' is NOT used as source."""
    data = load_clinical_runway_json()

    # Check data sources
    data_sources_str = " ".join(data["data_sources"])
    assert "typical Phase 2/3 biotech patterns" not in data_sources_str.lower(), \
        "Data sources must not reference 'typical Phase 2/3 biotech patterns'"
    assert "typical biotech" not in data_sources_str.lower(), \
        "Data sources must not reference 'typical biotech'"

    # Check financial snapshot source
    fs_source = data["financial_snapshot"]["source"]
    assert "typical" not in fs_source.lower(), \
        "Financial snapshot source must not use 'typical' estimates"
    assert "estimated from" not in fs_source.lower(), \
        "Financial snapshot source must not use 'estimated from' language"


def test_actual_10q_source_documented():
    """Test that actual 10-Q source is documented."""
    data = load_clinical_runway_json()

    # Check data sources contain actual 10-Q reference
    data_sources_str = " ".join(data["data_sources"]).lower()
    assert "actual" in data_sources_str or "10-q" in data_sources_str, \
        "Data sources must reference actual 10-Q filing"

    # Check financial snapshot source
    fs_source = data["financial_snapshot"]["source"].lower()
    assert "actual" in fs_source and "10-q" in fs_source, \
        "Financial snapshot source must reference actual 10-Q"


def test_reconciliation_status_cp23b_fix2_compliance():
    """Test that reconciliation_status has CP23B-Fix2 compliance flags."""
    data = load_clinical_runway_json()

    assert "reconciliation_status" in data, "reconciliation_status section missing"
    status = data["reconciliation_status"]

    # Check all CP23B-Fix2 compliance flags
    assert status.get("placeholder_cash_removed") is True, \
        "placeholder_cash_removed should be True"
    assert status.get("typical_biotech_pattern_financials_removed") is True, \
        "typical_biotech_pattern_financials_removed should be True"
    assert status.get("actual_10q_cash_extracted") is True, \
        "actual_10q_cash_extracted should be True"
    assert status.get("actual_10q_expenses_extracted") is True, \
        "actual_10q_expenses_extracted should be True"
    assert status.get("actual_10q_net_loss_extracted") is True, \
        "actual_10q_net_loss_extracted should be True"
    assert status.get("actual_10q_operating_cash_flow_extracted") is True or \
           status.get("actual_10q_operating_cash_flow_extracted_or_explained") is True, \
        "actual_10q_operating_cash_flow_extracted should be True"
    assert status.get("base_runway_anchored_to_actual_sec_value") is True, \
        "base_runway_anchored_to_actual_sec_value should be True"


def test_remaining_unresolved_fields_empty():
    """Test that remaining_unresolved_fields is empty."""
    data = load_clinical_runway_json()

    status = data["reconciliation_status"]
    remaining = status.get("remaining_unresolved_fields", [])

    assert isinstance(remaining, list), "remaining_unresolved_fields should be a list"
    assert len(remaining) == 0, \
        f"CP23B-Fix2 should have no remaining unresolved fields (found: {remaining})"


def test_base_runway_uses_actual_burn():
    """Test that base runway scenario uses actual operating cash burn."""
    data = load_clinical_runway_json()

    scenarios = data["cash_runway_scenarios"]
    base_scenario = next(s for s in scenarios if s["scenario"] == "base")

    # Base scenario should use actual 10-Q operating cash burn
    assert "source" in base_scenario, "Base scenario should have source field"
    source = base_scenario["source"].lower()
    assert "actual" in source and ("10-q" in source or "operating" in source), \
        "Base scenario should reference actual 10-Q operating cash burn"


def test_working_capital_extracted():
    """Test that working capital was extracted from 10-Q."""
    data = load_clinical_runway_json()

    fs = data["financial_snapshot"]
    assert "working_capital" in fs, "working_capital should be extracted"
    assert isinstance(fs["working_capital"], (int, float)), \
        "working_capital should be numeric"
    assert fs["working_capital"] != "Requires 10-Q extraction", \
        "working_capital should not require extraction (should be extracted)"


def test_current_assets_liabilities_extracted():
    """Test that current assets and liabilities were extracted."""
    data = load_clinical_runway_json()

    fs = data["financial_snapshot"]
    assert "current_assets" in fs, "current_assets should be extracted"
    assert "current_liabilities" in fs, "current_liabilities should be extracted"

    assert isinstance(fs["current_assets"], (int, float)), \
        "current_assets should be numeric"
    assert isinstance(fs["current_liabilities"], (int, float)), \
        "current_liabilities should be numeric"

    assert fs["current_assets"] != "Requires 10-Q extraction", \
        "current_assets should not require extraction"
    assert fs["current_liabilities"] != "Requires 10-Q extraction", \
        "current_liabilities should not require extraction"


def test_management_runway_statement_extracted():
    """Test that management runway statement was extracted."""
    data = load_clinical_runway_json()

    fs = data["financial_snapshot"]
    assert "management_runway_statement" in fs, "management_runway_statement should be extracted"
    statement = fs["management_runway_statement"]

    assert isinstance(statement, str), "management_runway_statement should be a string"
    assert len(statement) > 50, "management_runway_statement should have meaningful content"
    assert statement != "Requires 10-Q extraction for going-concern language", \
        "management_runway_statement should be extracted (not placeholder)"


def test_going_concern_language_checked():
    """Test that going-concern language was checked."""
    data = load_clinical_runway_json()

    fs = data["financial_snapshot"]
    assert "going_concern_language" in fs, "going_concern_language should be documented"

    # Either None (no going concern) or actual language
    going_concern = fs["going_concern_language"]
    assert going_concern is not None, "going_concern_language should be documented (not None)"


def test_filing_metadata_present():
    """Test that filing metadata is present."""
    data = load_clinical_runway_json()

    fs = data["financial_snapshot"]
    assert "filing_metadata" in fs, "filing_metadata should be present"

    metadata = fs["filing_metadata"]
    assert "cik" in metadata, "metadata should have cik"
    assert "accession_number" in metadata, "metadata should have accession_number"
    assert "filing_date" in metadata, "metadata should have filing_date"
    assert "period_ended" in metadata, "metadata should have period_ended"
    assert "form_type" in metadata, "metadata should have form_type"

    # Check that filing date and period are reasonable for Q1 2026
    assert "2026" in metadata["filing_date"], "filing_date should be in 2026"
    assert "2026-03-31" in metadata["period_ended"], "period_ended should be 2026-03-31"


def test_xbrl_sources_documented():
    """Test that XBRL source tags are documented."""
    data = load_clinical_runway_json()

    fs = data["financial_snapshot"]
    assert "xbrl_sources" in fs, "xbrl_sources should be documented"

    xbrl = fs["xbrl_sources"]
    assert "cash" in xbrl, "xbrl_sources should have cash tag"
    assert "operating_cash_flow" in xbrl, "xbrl_sources should have operating_cash_flow tag"
    assert "rd_expense" in xbrl, "xbrl_sources should have rd_expense tag"


def test_no_manual_extraction_required_in_json():
    """Test that JSON does not contain 'manual extraction required' text."""
    json_path = Path("docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway.json")
    content = json_path.read_text(encoding="utf-8")

    assert "manual extraction required" not in content.lower(), \
        "JSON should not contain 'manual extraction required' (CP23B-Fix2 completed extraction)"
    assert "requires 10-q extraction" not in content.lower(), \
        "JSON should not contain 'requires 10-q extraction' (CP23B-Fix2 completed extraction)"


def test_no_manual_extraction_required_in_markdown():
    """Test that markdown does not contain 'manual extraction required' in financial sections."""
    markdown = load_clinical_runway_markdown()

    # Should have Remaining Unresolved Fields subsection
    assert "### Remaining Unresolved Fields" in markdown, \
        "Should have Remaining Unresolved Fields subsection"

    # Should state that no financial fields remain unresolved
    # Look for the text after "Remaining Unresolved Fields"
    unresolved_match = re.search(
        r"### Remaining Unresolved Fields.*?(?=###|##)",
        markdown,
        re.DOTALL
    )
    assert unresolved_match, "Should find Remaining Unresolved Fields section"
    unresolved_text = unresolved_match.group(0)

    assert "None" in unresolved_text or "successfully extracted" in unresolved_text.lower(), \
        "Should indicate no financial fields remain unresolved"

    # Financial snapshot section should not say "requires extraction"
    financial_section = re.search(r"## Financial Snapshot.*?(?=##)", markdown, re.DOTALL)
    if financial_section:
        fs_text = financial_section.group(0)
        assert "requires 10-q extraction" not in fs_text.lower(), \
            "Financial snapshot should not have fields requiring extraction"


def test_markdown_checkpoint_updated():
    """Test that markdown checkpoint header is CP23B-Fix2."""
    markdown = load_clinical_runway_markdown()

    assert "**Checkpoint:** CP23B-Fix2" in markdown, \
        "Markdown checkpoint should be CP23B-Fix2"

    # Check that CP23B-Fix only appears in Superseded Checkpoints section (historical context)
    # Find the checkpoint header line (should be near the top)
    lines = markdown.split('\n')
    checkpoint_line = None
    for i, line in enumerate(lines[:20]):  # Check first 20 lines for the checkpoint
        if "**Checkpoint:**" in line:
            checkpoint_line = line
            break

    assert checkpoint_line is not None, "Should have checkpoint header in first 20 lines"
    assert "CP23B-Fix2" in checkpoint_line, "Current checkpoint header should be CP23B-Fix2"
    # Make sure it's not showing CP23B-Fix (without the 2) as current
    assert checkpoint_line.strip().endswith("CP23B-Fix2"), \
        f"Current checkpoint should be exactly 'CP23B-Fix2', got: {checkpoint_line.strip()}"


def test_markdown_actual_10q_language():
    """Test that markdown uses 'ACTUAL' language for 10-Q values."""
    markdown = load_clinical_runway_markdown()

    # Should use "ACTUAL" to emphasize real extracted values
    assert "ACTUAL" in markdown or "Actual" in markdown, \
        "Markdown should emphasize ACTUAL 10-Q values"

    # Should NOT use "estimated" for base financial snapshot
    financial_section = re.search(
        r"## Financial Snapshot.*?(?=##)",
        markdown,
        re.DOTALL
    )
    if financial_section:
        fs_text = financial_section.group(0)
        # Source line should say "ACTUAL" not "Estimated"
        source_line = re.search(r"\*\*Source:\*\*.*", fs_text)
        if source_line:
            assert "ACTUAL" in source_line.group(0) or "10-Q" in source_line.group(0), \
                "Financial snapshot source should reference ACTUAL 10-Q"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
