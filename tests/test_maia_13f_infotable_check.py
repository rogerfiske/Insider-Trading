"""Tests for MAIA 13F InfoTable check.

This test suite validates the MAIA 13F InfoTable matching validation script
from CP23F.
"""

import json
from pathlib import Path


def load_maia_13f_json() -> dict:
    """Load MAIA 13F matching JSON output."""
    json_path = Path("docs/sample_reports/maia_13f/MAIA_13F_infotable_matching.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_json_schema_required_keys():
    """Test that MAIA 13F JSON has all required keys."""
    data = load_maia_13f_json()

    required_keys = [
        "ticker",
        "cik",
        "generated_at",
        "target_resolution",
        "filings_reviewed",
        "infotables_parsed",
        "matches",
        "aggregate_summary",
        "limitations",
        "safety",
    ]

    for key in required_keys:
        assert key in data, f"Missing required key: {key}"


def test_target_resolution_structure():
    """Test target resolution has correct structure."""
    data = load_maia_13f_json()

    target_resolution = data["target_resolution"]

    assert "issuer_name" in target_resolution
    assert "cusip_candidates" in target_resolution
    assert "cusip_confidence" in target_resolution

    assert target_resolution["issuer_name"] == "MAIA Biotechnology, Inc."
    assert isinstance(target_resolution["cusip_candidates"], list)


def test_aggregate_summary_structure():
    """Test aggregate summary has correct structure."""
    data = load_maia_13f_json()

    summary = data["aggregate_summary"]

    assert "reliable_matches_found" in summary
    assert "total_managers" in summary
    assert "total_shares" in summary
    assert "total_reported_value" in summary
    assert "highest_confidence" in summary

    assert isinstance(summary["reliable_matches_found"], bool)
    assert isinstance(summary["total_managers"], int)
    assert isinstance(summary["total_shares"], (int, float))
    assert isinstance(summary["total_reported_value"], (int, float))


def test_safety_flags_correct():
    """Test that safety flags are correctly set."""
    data = load_maia_13f_json()

    safety = data["safety"]

    assert safety["openinsider_spreadsheet_used"] is False
    assert safety["telegram_sent"] is False
    assert safety["email_sent"] is False
    assert safety["scheduled_tasks_modified"] is False
    assert safety["env_printed_or_changed"] is False


def test_maia_ticker_and_cik():
    """Test MAIA ticker and CIK are correct."""
    data = load_maia_13f_json()

    assert data["ticker"] == "MAIA"
    assert data["cik"] == "0001878313"


def test_filings_reviewed_structure():
    """Test filings reviewed has correct structure."""
    data = load_maia_13f_json()

    filings = data["filings_reviewed"]

    assert isinstance(filings, list)
    assert len(filings) > 0

    for filing in filings:
        assert "manager_name" in filing
        assert "manager_cik" in filing
        assert "status" in filing


def test_limitations_documented():
    """Test that data quality limitations are documented."""
    data = load_maia_13f_json()

    limitations = data["limitations"]

    assert isinstance(limitations, list)
    assert len(limitations) > 0

    # Check for key limitations
    limitations_text = " ".join(limitations).lower()

    assert "13f" in limitations_text
    assert "lag" in limitations_text or "delay" in limitations_text
    assert "cusip" in limitations_text


def test_no_match_path_explicit():
    """Test no-match scenario is explicitly handled."""
    data = load_maia_13f_json()

    summary = data["aggregate_summary"]

    # If no matches found, should be explicitly false
    if not summary["reliable_matches_found"]:
        assert summary["total_managers"] == 0
        assert summary["total_shares"] == 0
        assert summary["total_reported_value"] == 0
        assert summary["highest_confidence"] == "none"
        assert len(data["matches"]) == 0


def test_matches_structure_if_present():
    """Test matches structure if any matches are present."""
    data = load_maia_13f_json()

    matches = data["matches"]

    if matches:
        for match in matches:
            assert "manager_name" in match
            assert "manager_cik" in match
            assert "issuer_name" in match
            assert "cusip" in match
            assert "shares" in match
            assert "value_usd" in match
            assert "confidence" in match
            assert "match_method" in match


def test_report_does_not_contain_secrets():
    """Test that report does not contain secrets."""
    json_path = Path("docs/sample_reports/maia_13f/MAIA_13F_infotable_matching.json")
    content = json_path.read_text(encoding="utf-8")

    secret_patterns = [
        "TELEGRAM_BOT_TOKEN=",
        "TELEGRAM_CHAT_ID=",
        "SMTP_PASSWORD=",
        "sk-ant-",
        "ETHERSCAN_API_KEY=",
        "BEGIN PRIVATE KEY",
    ]

    for pattern in secret_patterns:
        assert pattern not in content, \
            f"Report should not contain secret pattern: {pattern}"


def test_markdown_report_exists():
    """Test that markdown report exists and has content."""
    markdown_path = Path("docs/sample_reports/maia_13f/MAIA_13F_infotable_matching_report.md")

    assert markdown_path.exists(), "Markdown report should exist"

    content = markdown_path.read_text(encoding="utf-8")

    assert len(content) > 0, "Markdown report should have content"
    assert "MAIA Biotechnology" in content
    assert "13F" in content


def test_openinsider_spreadsheet_not_required():
    """Test that OpenInsider spreadsheet is not required."""
    data = load_maia_13f_json()

    safety = data["safety"]

    assert safety["openinsider_spreadsheet_used"] is False


def test_no_alert_infrastructure_invoked():
    """Test that no alert/Telegram/email code is referenced."""
    data = load_maia_13f_json()

    safety = data["safety"]

    assert safety["telegram_sent"] is False
    assert safety["email_sent"] is False
    assert safety["scheduled_tasks_modified"] is False


def test_parser_diagnostics_structure():
    """Test parser diagnostics structure (CP23F-Fix)."""
    data = load_maia_13f_json()

    # Parser diagnostics should be present
    assert "parser_diagnostics" in data

    diagnostics = data["parser_diagnostics"]

    # Required diagnostic fields
    assert "managers_reviewed" in diagnostics
    assert "infotables_successfully_parsed" in diagnostics
    assert "infotables_failed" in diagnostics
    assert "fallback_successes" in diagnostics
    assert "manager_results" in diagnostics

    # Types should be correct
    assert isinstance(diagnostics["managers_reviewed"], int)
    assert isinstance(diagnostics["infotables_successfully_parsed"], int)
    assert isinstance(diagnostics["infotables_failed"], int)
    assert isinstance(diagnostics["fallback_successes"], int)
    assert isinstance(diagnostics["manager_results"], list)


def test_parser_diagnostics_manager_results():
    """Test manager results in parser diagnostics."""
    data = load_maia_13f_json()

    diagnostics = data["parser_diagnostics"]
    manager_results = diagnostics["manager_results"]

    if len(manager_results) > 0:
        # Check structure of first manager result
        manager = manager_results[0]

        required_fields = [
            "manager_name",
            "manager_cik",
            "accession_number",
            "report_period",
            "parse_status",
            "holdings_parsed",
        ]

        for field in required_fields:
            assert field in manager, f"Missing field in manager result: {field}"

        # Parse status should be one of the expected values
        assert manager["parse_status"] in [
            "success",
            "fallback_namespace_success",
            "fallback_html_success",
            "failed",
            "partial",
        ]


def test_parser_success_rate_calculation():
    """Test parser success rate is correctly calculated."""
    data = load_maia_13f_json()

    diagnostics = data["parser_diagnostics"]

    managers_reviewed = diagnostics["managers_reviewed"]
    successfully_parsed = diagnostics["infotables_successfully_parsed"]
    failed = diagnostics["infotables_failed"]

    # Sum should match total managers reviewed
    assert successfully_parsed + failed == managers_reviewed

    # Success rate should be non-negative
    if managers_reviewed > 0:
        success_rate = successfully_parsed / managers_reviewed
        assert 0 <= success_rate <= 1


def test_no_match_scoped_to_parsed_filings():
    """Test no-match result is scoped to successfully parsed filings only."""
    data = load_maia_13f_json()

    summary = data["aggregate_summary"]
    diagnostics = data["parser_diagnostics"]

    # If no matches found
    if not summary["reliable_matches_found"]:
        # Check that this is explicitly stated to be scoped
        # to successfully parsed managers only
        assert diagnostics["managers_reviewed"] > 0

        # If some filings failed, there should be a note
        if diagnostics["infotables_failed"] > 0:
            # Check limitations mention this
            limitations = data["limitations"]
            limitations_text = " ".join(limitations).lower()

            assert "parsed" in limitations_text or "success" in limitations_text


def test_failed_filings_not_silently_dropped():
    """Test failed filings are not silently dropped."""
    data = load_maia_13f_json()

    diagnostics = data["parser_diagnostics"]
    manager_results = diagnostics["manager_results"]

    # Count failed managers in detailed results
    failed_in_results = sum(
        1 for m in manager_results if m["parse_status"] == "failed"
    )

    # Should match aggregate count
    assert failed_in_results == diagnostics["infotables_failed"]


def test_fallback_successes_tracked():
    """Test fallback parse successes are tracked separately."""
    data = load_maia_13f_json()

    diagnostics = data["parser_diagnostics"]

    # Fallback successes should be non-negative
    assert diagnostics["fallback_successes"] >= 0

    # Fallback successes should not exceed successfully parsed count
    assert diagnostics["fallback_successes"] <= diagnostics["infotables_successfully_parsed"]


def test_cp23f_fix_acceptance_criteria():
    """Test CP23F-Fix acceptance criteria are met."""
    data = load_maia_13f_json()

    diagnostics = data["parser_diagnostics"]

    # At least some managers should have been reviewed
    assert diagnostics["managers_reviewed"] >= 5

    # For any failed managers, check they have detailed diagnostics
    manager_results = diagnostics["manager_results"]

    for manager in manager_results:
        if manager["parse_status"] == "failed":
            # Should have accession number and filing info
            assert "accession_number" in manager
            assert manager["accession_number"] != ""

            # Should have failure reason if available
            # (error_message may be present)

    # If no matches found, should be explicitly stated
    summary = data["aggregate_summary"]
    if not summary["reliable_matches_found"]:
        assert summary["total_managers"] == 0
        assert summary["total_shares"] == 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
