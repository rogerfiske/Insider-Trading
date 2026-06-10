"""
Tests for MAIA market confirmation checklist (CP23G)

Tests cover:
1. JSON schema required keys
2. Baseline insider purchases equal 134
3. Baseline offering price equals 1.50
4. PM review triggers include required conditions
5. CSV template has required columns
6. Report/JSON do not contain buy/sell/hold recommendation language
7. Report/JSON contain no secrets
8. Safety flags are correct
9. No Telegram/email/alert code is called
10. OpenInsider spreadsheet is not required
"""

import json
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def json_path(project_root):
    """Get JSON plan path."""
    return project_root / "docs" / "sample_reports" / "maia_market_confirmation" / "MAIA_market_confirmation_plan.json"


@pytest.fixture
def csv_path(project_root):
    """Get CSV template path."""
    return project_root / "docs" / "sample_reports" / "maia_market_confirmation" / "MAIA_market_observation_template.csv"


@pytest.fixture
def json_data(json_path):
    """Load JSON plan data."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_json_schema_required_keys(json_data):
    """Test JSON schema has required keys."""
    required_keys = [
        "ticker",
        "cik",
        "baseline",
        "reference_levels",
        "weekly_checklist",
        "event_driven_checks",
        "pm_review_triggers",
        "manual_observation_template",
        "status_labels",
        "limitations",
        "future_automation",
        "safety",
    ]

    for key in required_keys:
        assert key in json_data, f"Missing required key: {key}"


def test_baseline_insider_purchases_equal_134(json_data):
    """Test baseline insider purchases equal 134."""
    insider_activity = json_data.get("baseline", {}).get("insider_activity", {})
    assert insider_activity.get("open_market_purchases") == 134, \
        f"Expected 134 purchases, got {insider_activity.get('open_market_purchases')}"


def test_baseline_insider_sales_equal_0(json_data):
    """Test baseline insider sales equal 0."""
    insider_activity = json_data.get("baseline", {}).get("insider_activity", {})
    assert insider_activity.get("open_market_sales") == 0, \
        f"Expected 0 sales, got {insider_activity.get('open_market_sales')}"


def test_baseline_offering_price_equals_1_50(json_data):
    """Test baseline offering price equals 1.50."""
    capital_structure = json_data.get("baseline", {}).get("capital_structure", {})
    offering_price = capital_structure.get("march_2026_offering_price")
    assert offering_price == 1.50, f"Expected offering price 1.50, got {offering_price}"


def test_pm_review_triggers_include_below_1_50_5_days(json_data):
    """Test PM review triggers include 'below $1.50 for 5 days' condition."""
    pm_triggers = json_data.get("pm_review_triggers", [])
    trigger_names = [t.get("trigger_name", "") for t in pm_triggers]

    found = any("below $1.50" in trigger and "5" in trigger for trigger in trigger_names)
    assert found, "Missing PM review trigger: Price closes below $1.50 for 5 consecutive trading days"


def test_pm_review_triggers_include_reclaim_1_50_5_days(json_data):
    """Test PM review triggers include 'reclaims $1.50 for 5 days' condition."""
    pm_triggers = json_data.get("pm_review_triggers", [])
    trigger_names = [t.get("trigger_name", "") for t in pm_triggers]

    found = any("reclaim" in trigger.lower() and "$1.50" in trigger and "5" in trigger for trigger in trigger_names)
    assert found, "Missing PM review trigger: Price reclaims $1.50 and holds for 5 consecutive trading days"


def test_pm_review_triggers_include_volume_3x(json_data):
    """Test PM review triggers include '>3x volume' condition."""
    pm_triggers = json_data.get("pm_review_triggers", [])
    trigger_names = [t.get("trigger_name", "") for t in pm_triggers]

    found = any(">3x" in trigger or "3x" in trigger for trigger in trigger_names)
    assert found, "Missing PM review trigger: Single-day volume spike >3x recent average"


def test_pm_review_triggers_include_first_sale(json_data):
    """Test PM review triggers include 'first Form 4 sale' condition."""
    pm_triggers = json_data.get("pm_review_triggers", [])
    trigger_names = [t.get("trigger_name", "") for t in pm_triggers]

    found = any("first" in trigger.lower() and "form 4" in trigger.lower() and "sale" in trigger.lower() for trigger in trigger_names)
    assert found, "Missing PM review trigger: First Form 4 open-market sale"


def test_pm_review_triggers_include_form_144(json_data):
    """Test PM review triggers include 'Form 144' condition."""
    pm_triggers = json_data.get("pm_review_triggers", [])
    trigger_names = [t.get("trigger_name", "") for t in pm_triggers]

    found = any("form 144" in trigger.lower() for trigger in trigger_names)
    assert found, "Missing PM review trigger: First Form 144 filing"


def test_pm_review_triggers_include_new_financing(json_data):
    """Test PM review triggers include 'new financing' condition."""
    pm_triggers = json_data.get("pm_review_triggers", [])
    trigger_names = [t.get("trigger_name", "") for t in pm_triggers]

    found = any("financing" in trigger.lower() for trigger in trigger_names)
    assert found, "Missing PM review trigger: New financing filing"


def test_pm_review_triggers_include_thio_104_timing(json_data):
    """Test PM review triggers include 'THIO-104 timing' condition."""
    pm_triggers = json_data.get("pm_review_triggers", [])
    trigger_names = [t.get("trigger_name", "") for t in pm_triggers]

    found = any("thio-104" in trigger.lower() and ("timing" in trigger.lower() or "data" in trigger.lower()) for trigger in trigger_names)
    assert found, "Missing PM review trigger: THIO-104 data timing disclosed"


def test_csv_template_has_required_columns(csv_path):
    """Test CSV template has required columns."""
    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip()

    required_columns = [
        "date",
        "closing_price",
        "weekly_high",
        "weekly_low",
        "weekly_volume",
        "avg_volume_reference",
        "days_above_1_50",
        "days_below_1_50",
        "major_news",
        "sec_filings",
        "form4_activity",
        "form144_activity",
        "clinical_updates",
        "financing_updates",
        "price_volume_read",
        "pm_review_triggered",
        "notes",
    ]

    for column in required_columns:
        assert column in header, f"Missing required CSV column: {column}"


def test_no_buy_sell_hold_recommendation_language(json_path):
    """Test report/JSON do not contain buy/sell/hold recommendation language."""
    with open(json_path, "r", encoding="utf-8") as f:
        json_content = f.read().lower()

    forbidden_phrases = ["buy recommendation", "sell recommendation", "hold recommendation", "strong buy", "strong sell"]
    for phrase in forbidden_phrases:
        assert phrase not in json_content, f"Found forbidden recommendation language: {phrase}"


def test_no_secrets(json_path):
    """Test report/JSON contain no secrets."""
    with open(json_path, "r", encoding="utf-8") as f:
        json_content = f.read()

    secret_patterns = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SMTP_PASSWORD",
        "sk-ant-",
        "ETHERSCAN_API_KEY",
    ]

    for pattern in secret_patterns:
        assert pattern not in json_content, f"Found secret pattern in JSON: {pattern}"


def test_safety_flags_correct(json_data):
    """Test safety flags are correct."""
    safety = json_data.get("safety", {})

    expected_safety_flags = {
        "report_only": True,
        "alerts_generated": False,
        "openinsider_spreadsheet_used": False,
        "telegram_sent": False,
        "email_sent": False,
        "scheduled_tasks_modified": False,
        "env_printed_or_changed": False,
        "buy_sell_hold_language_used": False,
    }

    for flag, expected_value in expected_safety_flags.items():
        actual_value = safety.get(flag)
        assert actual_value == expected_value, \
            f"Safety flag '{flag}': expected {expected_value}, got {actual_value}"


def test_no_telegram_email_alert_code():
    """Test no Telegram/email/alert code is called."""
    # This test verifies that the script does not import or use alert modules
    script_path = Path(__file__).parent.parent / "scripts" / "maia_market_confirmation_checklist.py"

    with open(script_path, "r", encoding="utf-8") as f:
        script_content = f.read()

    forbidden_imports = ["telegram", "smtplib", "email.mime"]
    for forbidden_import in forbidden_imports:
        assert f"import {forbidden_import}" not in script_content, \
            f"Found forbidden import: {forbidden_import}"


def test_openinsider_spreadsheet_not_required(json_data):
    """Test OpenInsider spreadsheet is not required."""
    safety = json_data.get("safety", {})
    assert safety.get("openinsider_spreadsheet_used") is False, \
        "OpenInsider spreadsheet should not be used"

    # Also check source boundary
    source_boundary_mentioned = any(
        "openinsider" in str(item).lower()
        for item in json_data.get("limitations", [])
    )
    # Limitations may mention OpenInsider as something NOT used, which is fine
    # The important check is the safety flag


def test_status_labels_defined(json_data):
    """Test status labels are defined."""
    status_labels = json_data.get("status_labels", [])
    expected_labels = ["confirming", "neutral", "cautionary", "requires_pm_review"]

    for label in expected_labels:
        assert label in status_labels, f"Missing status label: {label}"


def test_baseline_13f_parser_success_rate(json_data):
    """Test baseline 13F parser success rate is 60%."""
    institutional_visibility = json_data.get("baseline", {}).get("institutional_visibility", {})
    parser_success_rate = institutional_visibility.get("form_13f_parser_success_rate")
    assert parser_success_rate == 0.60, \
        f"Expected 13F parser success rate 0.60 (60%), got {parser_success_rate}"


def test_baseline_13f_maia_matches_found(json_data):
    """Test baseline 13F MAIA matches found is 0."""
    institutional_visibility = json_data.get("baseline", {}).get("institutional_visibility", {})
    maia_matches = institutional_visibility.get("maia_matches_found")
    assert maia_matches == 0, \
        f"Expected 0 MAIA matches in 13F sample, got {maia_matches}"


def test_baseline_form_13d_13g_filings(json_data):
    """Test baseline Form 13D/G filings is 0."""
    capital_structure = json_data.get("baseline", {}).get("capital_structure", {})
    filings_13d_13g = capital_structure.get("form_13d_13g_filings")
    assert filings_13d_13g == 0, \
        f"Expected 0 Form 13D/G filings, got {filings_13d_13g}"


def test_baseline_form_144_filings(json_data):
    """Test baseline Form 144 filings is 0."""
    capital_structure = json_data.get("baseline", {}).get("capital_structure", {})
    filings_144 = capital_structure.get("form_144_filings")
    assert filings_144 == 0, \
        f"Expected 0 Form 144 filings, got {filings_144}"


def test_baseline_thio_104_data_timing_not_disclosed(json_data):
    """Test baseline THIO-104 data timing is not disclosed."""
    clinical_programs = json_data.get("baseline", {}).get("clinical_programs", {})
    data_timing = clinical_programs.get("data_timing")
    assert data_timing == "Not disclosed", \
        f"Expected data timing 'Not disclosed', got {data_timing}"


def test_weekly_checklist_has_manual_entry_flags(json_data):
    """Test weekly checklist items have manual_entry_required flags."""
    weekly_checklist = json_data.get("weekly_checklist", [])
    assert len(weekly_checklist) > 0, "Weekly checklist should not be empty"

    for check in weekly_checklist:
        assert "manual_entry_required" in check, \
            f"Weekly check '{check.get('check_name')}' missing manual_entry_required flag"


def test_event_driven_checks_have_confirmation_levels(json_data):
    """Test event-driven checks have confirmation_levels defined."""
    event_driven_checks = json_data.get("event_driven_checks", [])
    assert len(event_driven_checks) > 0, "Event-driven checks should not be empty"

    for check in event_driven_checks:
        assert "confirmation_levels" in check, \
            f"Event-driven check '{check.get('event_name')}' missing confirmation_levels"


def test_limitations_include_manual_entry_note(json_data):
    """Test limitations include manual entry note."""
    limitations = json_data.get("limitations", [])
    limitations_text = " ".join(str(item) for item in limitations).lower()

    assert "manual" in limitations_text, \
        "Limitations should mention manual entry requirement"


def test_future_automation_includes_quote_api(json_data):
    """Test future automation includes quote API integration idea."""
    future_automation = json_data.get("future_automation", [])
    automation_text = " ".join(str(item) for item in future_automation).lower()

    assert "quote" in automation_text or "price" in automation_text, \
        "Future automation should mention quote/price API integration"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
