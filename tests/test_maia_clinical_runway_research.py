"""Tests for MAIA clinical runway research (CP23B).

Tests verify that the research output has required structure and safety confirmations.
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
def clinical_runway_json(project_root: Path) -> dict:
    """Load MAIA clinical runway JSON."""
    json_path = (
        project_root
        / "docs"
        / "sample_reports"
        / "maia_clinical_runway"
        / "MAIA_clinical_regulatory_cash_runway.json"
    )
    return json.loads(json_path.read_text(encoding="utf-8"))


@pytest.fixture
def clinical_runway_markdown(project_root: Path) -> str:
    """Load MAIA clinical runway markdown report."""
    md_path = (
        project_root
        / "docs"
        / "sample_reports"
        / "maia_clinical_runway"
        / "MAIA_clinical_regulatory_cash_runway_report.md"
    )
    return md_path.read_text(encoding="utf-8")


def test_json_has_required_top_level_keys(clinical_runway_json: dict):
    """JSON must have all required top-level keys."""
    required_keys = [
        "ticker",
        "cik",
        "generated_at",
        "clinical_programs",
        "milestone_calendar",
        "financial_snapshot",
        "cash_runway_scenarios",
        "dilution_timing_risk",
        "clinical_risk_assessment",
        "market_confirmation_watchlist",
        "limitations",
        "safety"
    ]

    for key in required_keys:
        assert key in clinical_runway_json, f"Missing required key: {key}"


def test_ticker_and_cik_correct(clinical_runway_json: dict):
    """Ticker and CIK must be MAIA / 0001878313."""
    assert clinical_runway_json["ticker"] == "MAIA"
    assert clinical_runway_json["cik"] == "0001878313"


def test_clinical_programs_is_list(clinical_runway_json: dict):
    """Clinical programs must be a list."""
    assert isinstance(clinical_runway_json["clinical_programs"], list)
    assert len(clinical_runway_json["clinical_programs"]) > 0


def test_thio_104_program_exists(clinical_runway_json: dict):
    """THIO-104 program must be in clinical programs."""
    programs = clinical_runway_json["clinical_programs"]
    thio_104 = [p for p in programs if p.get("program_name") == "THIO-104"]
    assert len(thio_104) > 0, "THIO-104 program not found"

    # Check required fields
    program = thio_104[0]
    assert "asset" in program
    assert "indication" in program
    assert "phase" in program
    assert "regulatory_status" in program


def test_milestone_calendar_is_list(clinical_runway_json: dict):
    """Milestone calendar must be a list."""
    assert isinstance(clinical_runway_json["milestone_calendar"], list)
    assert len(clinical_runway_json["milestone_calendar"]) > 0


def test_milestone_has_required_fields(clinical_runway_json: dict):
    """Each milestone must have required fields."""
    milestones = clinical_runway_json["milestone_calendar"]

    required_fields = [
        "milestone",
        "program",
        "expected_timing",
        "timing_confidence",
        "why_it_matters",
        "source",
        "risk_if_delayed"
    ]

    for milestone in milestones:
        for field in required_fields:
            assert field in milestone, f"Milestone missing field: {field}"


def test_cash_runway_scenarios_is_list(clinical_runway_json: dict):
    """Cash runway scenarios must be a list."""
    scenarios = clinical_runway_json["cash_runway_scenarios"]
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 3  # low, base, high


def test_cash_runway_scenarios_have_low_base_high(clinical_runway_json: dict):
    """Cash runway must have low, base, and high scenarios."""
    scenarios = clinical_runway_json["cash_runway_scenarios"]
    scenario_names = [s["scenario"] for s in scenarios]

    assert "low" in scenario_names
    assert "base" in scenario_names
    assert "high" in scenario_names


def test_runway_scenarios_ordered(clinical_runway_json: dict):
    """Runway scenarios must be ordered: low (longest) -> base -> high (shortest)."""
    scenarios = clinical_runway_json["cash_runway_scenarios"]

    # Find scenarios by name
    low = next(s for s in scenarios if s["scenario"] == "low")
    base = next(s for s in scenarios if s["scenario"] == "base")
    high = next(s for s in scenarios if s["scenario"] == "high")

    # Runway should decrease from low -> base -> high
    assert low["runway_months"] > base["runway_months"]
    assert base["runway_months"] > high["runway_months"]


def test_safety_flags_all_false(clinical_runway_json: dict):
    """All safety flags must be False (no alerts/emails/spreadsheets)."""
    safety = clinical_runway_json["safety"]

    assert safety["openinsider_spreadsheet_used"] is False
    assert safety["telegram_sent"] is False
    assert safety["email_sent"] is False
    assert safety["scheduled_tasks_modified"] is False


def test_no_secrets_in_json(clinical_runway_json: dict):
    """JSON must not contain secrets."""
    json_str = json.dumps(clinical_runway_json).lower()

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


def test_no_secrets_in_markdown(clinical_runway_markdown: str):
    """Markdown report must not contain secrets."""
    markdown_lower = clinical_runway_markdown.lower()

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


def test_markdown_has_safety_confirmations(clinical_runway_markdown: str):
    """Markdown must have safety confirmation section."""
    assert "Safety Confirmations" in clinical_runway_markdown or "safety" in clinical_runway_markdown.lower()
    assert "OpenInsider Spreadsheet" in clinical_runway_markdown or "NOT USED" in clinical_runway_markdown


def test_dilution_timing_risk_has_monitoring_triggers(clinical_runway_json: dict):
    """Dilution timing risk must have monitoring triggers."""
    dilution_risk = clinical_runway_json["dilution_timing_risk"]

    assert "monitoring_triggers" in dilution_risk
    assert isinstance(dilution_risk["monitoring_triggers"], list)
    assert len(dilution_risk["monitoring_triggers"]) > 0

    # Should include S-3, 424B, ATM monitoring
    triggers_str = " ".join(dilution_risk["monitoring_triggers"]).lower()
    assert "s-3" in triggers_str or "424b" in triggers_str or "atm" in triggers_str


def test_clinical_risk_assessment_has_key_sections(clinical_runway_json: dict):
    """Clinical risk assessment must have key risk categories."""
    risk_assessment = clinical_runway_json["clinical_risk_assessment"]

    required_sections = [
        "positive_signals",
        "clinical_execution_risks",
        "trial_design_risks",
        "endpoint_risks",
        "safety_tolerability_risks",
        "regulatory_risk"
    ]

    for section in required_sections:
        assert section in risk_assessment, f"Missing risk section: {section}"


def test_market_confirmation_watchlist_is_list(clinical_runway_json: dict):
    """Market confirmation watchlist must be a list."""
    watchlist = clinical_runway_json["market_confirmation_watchlist"]

    assert isinstance(watchlist, list)
    assert len(watchlist) > 0


def test_market_watchlist_items_have_required_fields(clinical_runway_json: dict):
    """Each market watchlist item must have signal, why_it_matters, monitoring_method."""
    watchlist = clinical_runway_json["market_confirmation_watchlist"]

    for item in watchlist:
        assert "signal" in item
        assert "why_it_matters" in item
        assert "monitoring_method" in item


def test_limitations_documented(clinical_runway_json: dict):
    """Limitations must be documented."""
    limitations = clinical_runway_json["limitations"]

    assert isinstance(limitations, list)
    assert len(limitations) > 0


def test_data_sources_documented(clinical_runway_json: dict):
    """Data sources must be documented."""
    data_sources = clinical_runway_json.get("data_sources", [])

    assert isinstance(data_sources, list)
    assert len(data_sources) > 0

    # Should include SEC EDGAR
    sources_str = " ".join(data_sources).lower()
    assert "sec" in sources_str or "edgar" in sources_str


def test_no_investment_advice_language(clinical_runway_markdown: str):
    """Report must not present as investment advice."""
    # Should NOT have phrases like "we recommend", "buy", "sell", "strong buy", etc.
    problematic_phrases = [
        "we recommend buying",
        "we recommend selling",
        "strong buy",
        "strong sell",
        "this is a buy",
        "this is a sell"
    ]

    markdown_lower = clinical_runway_markdown.lower()
    for phrase in problematic_phrases:
        assert phrase not in markdown_lower, f"Found investment advice language: {phrase}"


def test_unknown_milestone_timing_handled(clinical_runway_json: dict):
    """Milestones with unknown timing should say 'not disclosed' or 'unknown'."""
    milestones = clinical_runway_json["milestone_calendar"]

    # At least some milestones should have unknown or not disclosed timing
    timing_confidences = [m["timing_confidence"] for m in milestones]
    assert "unknown" in timing_confidences or "Unknown" in timing_confidences


def test_runway_scenarios_have_assumptions(clinical_runway_json: dict):
    """Each runway scenario must document its assumptions."""
    scenarios = clinical_runway_json["cash_runway_scenarios"]

    for scenario in scenarios:
        assert "assumptions" in scenario
        assert len(scenario["assumptions"]) > 0
