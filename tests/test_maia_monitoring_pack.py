"""Tests for MAIA monitoring pack (CP23E).

This test suite validates the MAIA monitoring plan JSON schema and baseline values
from CP23E monitoring pack creation.
"""

import json
from pathlib import Path


def load_monitoring_plan() -> dict:
    """Load MAIA monitoring plan JSON."""
    json_path = Path("docs/sample_reports/maia_monitoring/MAIA_monitoring_plan.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_json_schema_required_keys():
    """Test that monitoring plan JSON has all required keys."""
    data = load_monitoring_plan()

    required_keys = [
        "ticker",
        "cik",
        "generated_at",
        "checkpoint",
        "baseline",
        "monitoring_categories",
        "weekly_checklist",
        "event_triggers",
        "pm_review_triggers",
        "engineering_followups",
        "status_labels",
        "limitations",
        "safety"
    ]

    for key in required_keys:
        assert key in data, f"Missing required key: {key}"


def test_baseline_insider_purchases():
    """Test that baseline insider purchases equal 134."""
    data = load_monitoring_plan()

    baseline = data["baseline"]["insider_activity"]
    assert baseline["open_market_purchases"] == 134, \
        f"Baseline insider purchases should be 134, got {baseline['open_market_purchases']}"


def test_baseline_insider_sales():
    """Test that baseline insider sales equal 0."""
    data = load_monitoring_plan()

    baseline = data["baseline"]["insider_activity"]
    assert baseline["open_market_sales"] == 0, \
        f"Baseline insider sales should be 0, got {baseline['open_market_sales']}"


def test_baseline_cash():
    """Test that baseline cash equals $34,413,110."""
    data = load_monitoring_plan()

    baseline = data["baseline"]["official_10q_financials"]
    assert baseline["cash_and_equivalents"] == 34413110, \
        f"Baseline cash should be $34,413,110, got ${baseline['cash_and_equivalents']:,}"


def test_baseline_working_capital():
    """Test that baseline working capital equals $28,992,690."""
    data = load_monitoring_plan()

    baseline = data["baseline"]["official_10q_financials"]
    assert baseline["working_capital"] == 28992690, \
        f"Baseline working capital should be $28,992,690, got ${baseline['working_capital']:,}"


def test_baseline_operating_cash_burn():
    """Test that baseline operating cash burn equals $5,311,328."""
    data = load_monitoring_plan()

    baseline = data["baseline"]["official_10q_financials"]
    # Note: stored as negative in JSON
    expected_burn = -5311328
    assert baseline["q1_2026_operating_cash_burn"] == expected_burn, \
        f"Baseline operating cash burn should be ${expected_burn:,}, got ${baseline['q1_2026_operating_cash_burn']:,}"


def test_weekly_checklist_includes_all_categories():
    """Test that weekly checklist includes all required monitoring categories."""
    data = load_monitoring_plan()

    weekly_items = data["weekly_checklist"]

    # Extract unique categories from weekly checklist
    categories = set(item["category"] for item in weekly_items)

    required_categories = [
        "Insider Activity",
        "Form 144",
        "13D/G Ownership",
        "13F Institutional",
        "Clinical/Regulatory",
        "Cash Runway",
        "Safety"
    ]

    for category in required_categories:
        assert category in categories, \
            f"Weekly checklist missing category: {category}"


def test_pm_review_triggers_include_critical_events():
    """Test that PM review triggers include all critical events."""
    data = load_monitoring_plan()

    pm_triggers = data["pm_review_triggers"]
    trigger_names = [t["trigger"] for t in pm_triggers]

    critical_triggers = [
        "First open-market insider sale",
        "First Form 144 filing",
        "THIO-104 data timing disclosed",
        "New financing filing",
        "Cash runway drops below 12 months"
    ]

    for trigger in critical_triggers:
        assert trigger in trigger_names, \
            f"PM review triggers missing: {trigger}"


def test_safety_flags_correct():
    """Test that safety flags are correctly set."""
    data = load_monitoring_plan()

    safety = data["safety"]

    assert safety["report_only"] is True, "Should be report-only monitoring"
    assert safety["alerts_generated"] is False, "Should not generate alerts"
    assert safety["openinsider_spreadsheet_used"] is False, "Should not use OpenInsider"
    assert safety["telegram_sent"] is False, "Should not send Telegram"
    assert safety["email_sent"] is False, "Should not send email"
    assert safety["scheduled_tasks_modified"] is False, "Should not modify scheduled tasks"
    assert safety["env_printed_or_changed"] is False, "Should not print/change .env"


def test_report_does_not_contain_recommendation_language():
    """Test that report does not contain buy/sell/hold recommendation language."""
    json_path = Path("docs/sample_reports/maia_monitoring/MAIA_monitoring_plan.json")
    content = json_path.read_text(encoding="utf-8")

    forbidden_words = [
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "strong buy",
        "strong sell",
        "price target",
        "target price",
        "expected return"
    ]

    for word in forbidden_words:
        assert word.lower() not in content.lower(), \
            f"Report should not contain '{word}' (investment recommendation language)"


def test_report_does_not_contain_secrets():
    """Test that report does not contain secrets."""
    json_path = Path("docs/sample_reports/maia_monitoring/MAIA_monitoring_plan.json")
    content = json_path.read_text(encoding="utf-8")

    secret_patterns = [
        "TELEGRAM_BOT_TOKEN=",
        "TELEGRAM_CHAT_ID=",
        "SMTP_PASSWORD=",
        "sk-ant-",
        "ETHERSCAN_API_KEY=",
        "BEGIN PRIVATE KEY"
    ]

    for pattern in secret_patterns:
        assert pattern not in content, \
            f"Report should not contain secret pattern: {pattern}"


def test_no_alert_infrastructure_invoked():
    """Test that no alert/Telegram/email code is referenced in monitoring pack."""
    data = load_monitoring_plan()

    safety = data["safety"]

    assert safety["alert_infrastructure_invoked"] is False, \
        "Alert infrastructure should not be invoked"
    assert safety["telegram_sent"] is False, \
        "No Telegram messages should be sent"
    assert safety["email_sent"] is False, \
        "No email should be sent"


def test_openinsider_spreadsheet_not_required():
    """Test that OpenInsider spreadsheet is not required."""
    data = load_monitoring_plan()

    safety = data["safety"]

    assert safety["openinsider_spreadsheet_used"] is False, \
        "OpenInsider spreadsheet should not be used"


def test_baseline_values_from_cp23d():
    """Test that all baseline values match CP23D synthesis."""
    data = load_monitoring_plan()

    # Insider activity baseline
    insider = data["baseline"]["insider_activity"]
    assert insider["open_market_purchases"] == 134
    assert insider["open_market_sales"] == 0
    assert insider["purchase_value_usd"] == 4921437.58
    assert insider["distinct_buyers"] == 10
    assert insider["latest_purchase_date"] == "2026-06-01"
    assert insider["insider_score"] == 100

    # Capital structure baseline
    capital = data["baseline"]["capital_structure"]
    assert capital["common_shares_outstanding"] == 60671491
    assert capital["stock_options"] == 13097991
    assert capital["warrants"] == 13086220
    assert capital["approximate_fully_diluted"] == 86855702

    # Financial baseline
    financials = data["baseline"]["official_10q_financials"]
    assert financials["cash_and_equivalents"] == 34413110
    assert financials["working_capital"] == 28992690
    assert financials["q1_2026_operating_cash_burn"] == -5311328
    assert financials["base_runway_months"] == 19.4


def test_engineering_followups_include_13f_and_market_tracking():
    """Test that engineering follow-ups include 13F integration and market tracking."""
    data = load_monitoring_plan()

    followups = data["engineering_followups"]
    followup_tasks = [f["task"] for f in followups]

    assert "Integrate 13F InfoTable XML matching" in followup_tasks, \
        "Engineering follow-ups should include 13F integration"
    assert "Implement market price/volume tracking" in followup_tasks, \
        "Engineering follow-ups should include market tracking"


def test_monitoring_categories_count():
    """Test that monitoring pack includes all 8 required categories."""
    data = load_monitoring_plan()

    categories = data["monitoring_categories"]
    category_names = [c["category"] for c in categories]

    required_categories = [
        "Insider Activity (Form 4)",
        "Form 144 / Sale-Intent Monitoring",
        "13D/G Beneficial Ownership Monitoring",
        "13F Institutional Visibility",
        "Clinical/Regulatory Monitoring",
        "Cash Runway / Dilution Monitoring",
        "Market Confirmation Monitoring",
        "Alert-Routing Separation"
    ]

    for category in required_categories:
        assert category in category_names, \
            f"Monitoring categories missing: {category}"


def test_status_labels_defined():
    """Test that status labels are defined."""
    data = load_monitoring_plan()

    labels = data["status_labels"]
    label_names = [l["label"] for l in labels]

    expected_labels = [
        "No change",
        "Positive development",
        "Caution development",
        "Material uncertainty",
        "Requires PM review"
    ]

    for label in expected_labels:
        assert label in label_names, \
            f"Status labels missing: {label}"


def test_limitations_documented():
    """Test that data quality limitations are documented."""
    data = load_monitoring_plan()

    limitations = data["limitations"]

    assert len(limitations) > 0, "Limitations should be documented"

    # Check for key limitations
    limitations_text = " ".join(limitations).lower()

    assert "13f" in limitations_text, \
        "Limitations should mention 13F institutional visibility gap"
    assert "market" in limitations_text or "price" in limitations_text, \
        "Limitations should mention market tracking gap"
    assert "clinical" in limitations_text or "data timing" in limitations_text, \
        "Limitations should mention clinical disclosure gaps"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
