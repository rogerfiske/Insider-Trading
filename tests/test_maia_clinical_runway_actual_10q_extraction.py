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


def test_checkpoint_is_cp23b_fix3():
    """Test that checkpoint is CP23B-Fix3."""
    data = load_clinical_runway_json()
    assert data["research_checkpoint"] == "CP23B-Fix3", "Checkpoint should be CP23B-Fix3"


def test_official_cash_34_413_110():
    """Test that official cash $34,413,110 is used, not incorrect CP23B-Fix2 $38.25M."""
    data = load_clinical_runway_json()
    actual_cash = data["financial_snapshot"]["cash_and_equivalents"]

    # CP23B-Fix3 requires official 10-Q value: $34,413,110
    assert actual_cash == 34_413_110, \
        f"Report must use official cash $34,413,110 from XBRL (got: ${actual_cash:,})"

    # Must NOT use incorrect CP23B-Fix2 value
    assert actual_cash != 38_250_000, \
        "Report must not use incorrect CP23B-Fix2 cash $38,250,000"

    # Must NOT use CP23B placeholder
    assert actual_cash != 40_000_000, \
        "Report must not use CP23B placeholder cash $40,000,000"


def test_official_burn_5_311_328():
    """Test that official burn $5,311,328 is used, not incorrect CP23B-Fix2 $8.9M."""
    data = load_clinical_runway_json()
    actual_burn = data["financial_snapshot"]["net_cash_used_in_operations"]

    # CP23B-Fix3 requires official 10-Q value: $5,311,328
    assert actual_burn == 5_311_328, \
        f"Report must use official burn $5,311,328 from XBRL (got: ${actual_burn:,})"

    # Must NOT use incorrect CP23B-Fix2 value
    assert actual_burn != 8_900_000, \
        "Report must not use incorrect CP23B-Fix2 burn $8,900,000"

    # Must NOT use CP23B-Fix estimate
    assert actual_burn != 9_500_000, \
        "Report must not use CP23B-Fix estimated burn $9,500,000"

    # Must NOT use CP23B placeholder
    assert actual_burn != 10_000_000, \
        "Report must not use CP23B placeholder burn $10,000,000"


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


def test_official_10q_xbrl_source_documented():
    """Test that official 10-Q XBRL source is documented."""
    data = load_clinical_runway_json()

    # Check data sources contain official 10-Q XBRL reference
    data_sources_str = " ".join(data["data_sources"]).lower()
    assert ("official" in data_sources_str or "actual" in data_sources_str) and "10-q" in data_sources_str, \
        "Data sources must reference official/actual 10-Q filing"

    # Check financial snapshot source
    fs_source = data["financial_snapshot"]["source"].lower()
    assert ("official" in fs_source or "actual" in fs_source) and "10-q" in fs_source, \
        "Financial snapshot source must reference official/actual 10-Q"

    # Should emphasize official XBRL
    assert "xbrl" in fs_source or "xbrl" in data_sources_str, \
        "Should reference XBRL data source"


def test_reconciliation_status_cp23b_fix3_compliance():
    """Test that reconciliation_status has CP23B-Fix3 compliance flags."""
    data = load_clinical_runway_json()

    assert "reconciliation_status" in data, "reconciliation_status section missing"
    status = data["reconciliation_status"]

    # Check all CP23B-Fix3 compliance flags
    assert status.get("official_xbrl_values_extracted") is True, \
        "official_xbrl_values_extracted should be True"
    assert status.get("cash_34_413_110_confirmed") is True, \
        "cash_34_413_110_confirmed should be True"
    assert status.get("current_liabilities_6_322_437_confirmed") is True, \
        "current_liabilities_6_322_437_confirmed should be True"
    assert status.get("accumulated_deficit_116_000_657_confirmed") is True, \
        "accumulated_deficit_116_000_657_confirmed should be True"
    assert status.get("common_shares_60_671_491_confirmed") is True, \
        "common_shares_60_671_491_confirmed should be True"
    assert status.get("rd_expense_3_525_097_confirmed") is True, \
        "rd_expense_3_525_097_confirmed should be True"
    assert status.get("ga_expense_3_424_832_confirmed") is True, \
        "ga_expense_3_424_832_confirmed should be True"
    assert status.get("net_cash_used_in_operations_5_311_328_confirmed") is True, \
        "net_cash_used_in_operations_5_311_328_confirmed should be True"
    assert status.get("base_runway_anchored_to_official_sec_value") is True, \
        "base_runway_anchored_to_official_sec_value should be True"
    assert status.get("cp23b_fix2_incorrect_values_removed") is True, \
        "cp23b_fix2_incorrect_values_removed should be True"


def test_remaining_unresolved_fields_empty():
    """Test that remaining_unresolved_fields is empty."""
    data = load_clinical_runway_json()

    status = data["reconciliation_status"]
    remaining = status.get("remaining_unresolved_fields", [])

    assert isinstance(remaining, list), "remaining_unresolved_fields should be a list"
    assert len(remaining) == 0, \
        f"CP23B-Fix2 should have no remaining unresolved fields (found: {remaining})"


def test_base_runway_uses_official_burn():
    """Test that base runway scenario uses official operating cash burn."""
    data = load_clinical_runway_json()

    scenarios = data["cash_runway_scenarios"]
    base_scenario = next(s for s in scenarios if s["scenario"] == "base")

    # Base scenario should use official 10-Q operating cash burn
    assert "source" in base_scenario, "Base scenario should have source field"
    source = base_scenario["source"].lower()
    assert ("official" in source or "actual" in source) and ("10-q" in source or "operating" in source), \
        "Base scenario should reference official/actual 10-Q operating cash burn"


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


def test_markdown_official_xbrl_language():
    """Test that markdown uses 'OFFICIAL' XBRL language for 10-Q values."""
    markdown = load_clinical_runway_markdown()

    # Should use "OFFICIAL" to emphasize official XBRL values
    assert "OFFICIAL" in markdown or "Official" in markdown, \
        "Markdown should emphasize OFFICIAL 10-Q XBRL values"

    # Should reference XBRL
    assert "XBRL" in markdown, \
        "Markdown should reference XBRL data source"


def test_official_rd_expense_3_525_097():
    """Test that official R&D expense $3,525,097 is used."""
    data = load_clinical_runway_json()
    rd_expense = data["financial_snapshot"]["quarterly_rd_expense"]

    assert rd_expense == 3_525_097, \
        f"Report must use official R&D expense $3,525,097 from XBRL (got: ${rd_expense:,})"

    # Must NOT use incorrect CP23B-Fix2 value
    assert rd_expense != 6_850_000, \
        "Report must not use incorrect CP23B-Fix2 R&D $6,850,000"


def test_official_ga_expense_3_424_832():
    """Test that official G&A expense $3,424,832 is used."""
    data = load_clinical_runway_json()
    ga_expense = data["financial_snapshot"]["quarterly_ga_expense"]

    assert ga_expense == 3_424_832, \
        f"Report must use official G&A expense $3,424,832 from XBRL (got: ${ga_expense:,})"

    # Must NOT use incorrect CP23B-Fix2 value
    assert ga_expense != 2_350_000, \
        "Report must not use incorrect CP23B-Fix2 G&A $2,350,000"


def test_official_common_shares_60_671_491():
    """Test that official common shares 60,671,491 is used."""
    data = load_clinical_runway_json()
    common_shares = data["financial_snapshot"]["common_shares_outstanding"]

    assert common_shares == 60_671_491, \
        f"Report must use official common shares 60,671,491 from XBRL (got: {common_shares:,})"

    # Must NOT use incorrect CP23B-Fix2 value
    assert common_shares != 65_033_854, \
        "Report must not use incorrect CP23B-Fix2 common shares 65,033,854"


def test_official_accumulated_deficit_116_000_657():
    """Test that official accumulated deficit -$116,000,657 is used."""
    data = load_clinical_runway_json()
    accumulated_deficit = data["financial_snapshot"]["accumulated_deficit"]

    # Allow for both positive and negative representations
    assert abs(accumulated_deficit) == 116_000_657, \
        f"Report must use official accumulated deficit 116,000,657 from XBRL (got: ${abs(accumulated_deficit):,})"

    # Must NOT use incorrect CP23B-Fix2 value
    assert abs(accumulated_deficit) != 142_500_000, \
        "Report must not use incorrect CP23B-Fix2 accumulated deficit 142,500,000"


def test_official_current_liabilities_6_322_437():
    """Test that official current liabilities $6,322,437 is used."""
    data = load_clinical_runway_json()
    current_liabilities = data["financial_snapshot"]["current_liabilities"]

    assert current_liabilities == 6_322_437, \
        f"Report must use official current liabilities $6,322,437 from XBRL (got: ${current_liabilities:,})"

    # Must NOT use incorrect CP23B-Fix2 value
    assert current_liabilities != 3_850_000, \
        "Report must not use incorrect CP23B-Fix2 current liabilities $3,850,000"


def test_official_net_loss_6_369_652():
    """Test that official net loss $6,369,652 is used."""
    data = load_clinical_runway_json()
    net_loss = data["financial_snapshot"]["quarterly_net_loss"]

    # Net loss should be positive in the snapshot (representing loss amount)
    assert net_loss == 6_369_652, \
        f"Report must use official net loss $6,369,652 from XBRL (got: ${net_loss:,})"

    # Must NOT use incorrect CP23B-Fix2 value
    assert net_loss != 9_450_000, \
        "Report must not use incorrect CP23B-Fix2 net loss $9,450,000"


def test_base_runway_anchored_to_official_burn():
    """Test that base runway is anchored to official $5.31M burn, not incorrect $8.9M."""
    data = load_clinical_runway_json()
    scenarios = data["cash_runway_scenarios"]
    base_scenario = next(s for s in scenarios if s["scenario"] == "base")

    # Base scenario should use official $5,311,328 quarterly burn
    assert base_scenario["quarterly_burn"] == 5_311_328, \
        f"Base scenario must use official burn $5,311,328 (got: ${base_scenario['quarterly_burn']:,})"

    # Base runway should be around 19.4 months with official values
    assert 19.0 <= base_scenario["runway_months"] <= 20.0, \
        f"Base runway should be ~19.4 months with official values (got: {base_scenario['runway_months']})"

    # Must NOT show 12.9 months from incorrect CP23B-Fix2
    assert not (12.0 <= base_scenario["runway_months"] <= 13.5), \
        f"Base runway must not be ~12.9 months from incorrect CP23B-Fix2 (got: {base_scenario['runway_months']})"


def test_checkpoint_markdown_is_cp23b_fix3():
    """Test that markdown checkpoint is CP23B-Fix3."""
    markdown = load_clinical_runway_markdown()

    assert "**Checkpoint:** CP23B-Fix3" in markdown, \
        "Markdown checkpoint should be CP23B-Fix3"

    # Check that it's showing CP23B-Fix3 (not CP23B-Fix2) as current
    lines = markdown.split('\n')
    checkpoint_line = None
    for i, line in enumerate(lines[:20]):
        if "**Checkpoint:**" in line:
            checkpoint_line = line
            break

    assert checkpoint_line is not None, "Should have checkpoint header in first 20 lines"
    assert "CP23B-Fix3" in checkpoint_line, "Current checkpoint header should be CP23B-Fix3"
    assert checkpoint_line.strip().endswith("CP23B-Fix3"), \
        f"Current checkpoint should be exactly 'CP23B-Fix3', got: {checkpoint_line.strip()}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
