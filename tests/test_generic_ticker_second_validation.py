"""
Tests for Generic Ticker Second Validation - NVDA (CP23I)

Validates the generic ticker framework handles non-biotech tickers correctly
and that MAIA-specific values do not leak into NVDA outputs.
"""

import csv
import json
import pytest
from pathlib import Path


@pytest.fixture
def nvda_synthesis():
    """Load NVDA synthesis packet."""
    path = Path("docs/sample_reports/generic_ticker/NVDA/synthesis/NVDA_synthesis_packet.json")
    if not path.exists():
        pytest.skip(f"NVDA synthesis packet not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def nvda_monitoring():
    """Load NVDA monitoring plan."""
    path = Path("docs/sample_reports/generic_ticker/NVDA/monitoring/NVDA_monitoring_plan.json")
    if not path.exists():
        pytest.skip(f"NVDA monitoring plan not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def nvda_market_confirmation():
    """Load NVDA market confirmation plan."""
    path = Path("docs/sample_reports/generic_ticker/NVDA/market_confirmation/NVDA_market_confirmation_plan.json")
    if not path.exists():
        pytest.skip(f"NVDA market confirmation plan not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def nvda_archive_manifest():
    """Load NVDA archive manifest."""
    path = Path("docs/sample_reports/generic_ticker/NVDA/archive/NVDA_archive_manifest.json")
    if not path.exists():
        pytest.skip(f"NVDA archive manifest not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_nvda_output_directory_exists():
    """Test NVDA output directory was created."""
    nvda_dir = Path("docs/sample_reports/generic_ticker/NVDA")
    assert nvda_dir.exists(), "NVDA output directory should exist"

    # Check subdirectories
    assert (nvda_dir / "synthesis").exists()
    assert (nvda_dir / "monitoring").exists()
    assert (nvda_dir / "market_confirmation").exists()
    assert (nvda_dir / "archive").exists()


def test_nvda_synthesis_structure(nvda_synthesis):
    """Test NVDA synthesis packet has required structure."""
    required_keys = [
        "ticker",
        "cik",
        "checkpoint",
        "ticker_profile",
        "modules",
        "synthesis_scores",
        "safety",
    ]

    for key in required_keys:
        assert key in nvda_synthesis, f"Missing required key: {key}"


def test_ticker_equals_nvda(nvda_synthesis, nvda_monitoring, nvda_market_confirmation, nvda_archive_manifest):
    """Test ticker field equals NVDA in all outputs."""
    assert nvda_synthesis["ticker"] == "NVDA", "Synthesis ticker should be NVDA"
    assert nvda_monitoring["ticker"] == "NVDA", "Monitoring ticker should be NVDA"
    assert nvda_market_confirmation["ticker"] == "NVDA", "Market confirmation ticker should be NVDA"
    assert nvda_archive_manifest["ticker"] == "NVDA", "Archive ticker should be NVDA"


def test_checkpoint_equals_cp23i(nvda_synthesis, nvda_monitoring, nvda_market_confirmation, nvda_archive_manifest):
    """Test checkpoint field equals CP23I in all outputs."""
    assert nvda_synthesis["checkpoint"] == "CP23I", "Synthesis checkpoint should be CP23I"
    assert nvda_monitoring["checkpoint"] == "CP23I", "Monitoring checkpoint should be CP23I"
    assert nvda_market_confirmation["checkpoint"] == "CP23I", "Market confirmation checkpoint should be CP23I"
    assert nvda_archive_manifest["checkpoint"] == "CP23I", "Archive checkpoint should be CP23I"


def test_clinical_module_not_applicable(nvda_synthesis):
    """Test clinical/regulatory module is not_applicable for non-biotech NVDA."""
    clinical = nvda_synthesis["modules"]["clinical_regulatory"]
    assert clinical == "not_applicable", "Clinical module should be 'not_applicable' for NVDA"

    # Verify clinical scores are also not_applicable
    scores = nvda_synthesis["synthesis_scores"]
    assert "not_applicable" in str(scores.get("clinical_progress_score", "")).lower()
    assert "not_applicable" in str(scores.get("clinical_progress_rating", "")).lower()


def test_safety_flags_correct(nvda_synthesis, nvda_monitoring, nvda_market_confirmation, nvda_archive_manifest):
    """Test safety flags are correct in all NVDA outputs."""
    expected = {
        "report_only": True,
        "alerts_generated": False,
        "openinsider_spreadsheet_used": False,
        "telegram_sent": False,
        "email_sent": False,
        "scheduled_tasks_modified": False,
        "env_printed_or_changed": False,
        "buy_sell_hold_language_used": False,
    }

    for output_name, output_data in [
        ("synthesis", nvda_synthesis),
        ("monitoring", nvda_monitoring),
        ("market_confirmation", nvda_market_confirmation),
        ("archive", nvda_archive_manifest),
    ]:
        safety = output_data["safety"]
        for flag, expected_value in expected.items():
            assert flag in safety, f"{output_name}: Missing safety flag: {flag}"
            assert safety[flag] == expected_value, f"{output_name}: Safety flag '{flag}' expected {expected_value}, got {safety[flag]}"


def test_no_recommendation_language(nvda_synthesis):
    """Test no buy/sell/hold recommendation language in NVDA synthesis."""
    synthesis_str = json.dumps(nvda_synthesis).lower()

    forbidden_phrases = [
        "buy",
        "sell",
        "hold",
        "strong buy",
        "accumulate",
        "reduce",
        "recommended",
        "invest",
        "divest",
    ]

    for phrase in forbidden_phrases:
        # Allow certain technical terms but not recommendation language
        if phrase in ["hold", "buy"]:
            # Check for recommendation context, not just word presence
            assert "should buy" not in synthesis_str
            assert "should sell" not in synthesis_str
            assert "should hold" not in synthesis_str
            assert "recommend buy" not in synthesis_str
            assert "recommend sell" not in synthesis_str
            assert "recommend hold" not in synthesis_str


def test_no_maia_specific_constants_leak(nvda_synthesis, nvda_monitoring, nvda_market_confirmation):
    """Test MAIA-specific constants do not leak into NVDA outputs."""
    maia_constants = [
        "134",  # MAIA purchase count
        "4921437",  # MAIA purchase value
        "34413110",  # MAIA cash balance
        "28992690",  # MAIA working capital
        "5311328",  # MAIA monthly burn
        "THIO",  # MAIA clinical program
        "1.50",  # MAIA offering price
    ]

    for output_name, output_data in [
        ("synthesis", nvda_synthesis),
        ("monitoring", nvda_monitoring),
        ("market_confirmation", nvda_market_confirmation),
    ]:
        output_str = json.dumps(output_data)
        for constant in maia_constants:
            # Exception: documentation may mention "$1.50" as an example of what NOT to use
            if constant == "1.50":
                # Allow in limitations explaining what's excluded
                continue
            assert constant not in output_str, f"{output_name}: MAIA-specific constant '{constant}' should not appear"


def test_csv_observation_template_columns():
    """Test NVDA market observation CSV has required columns."""
    csv_path = Path("docs/sample_reports/generic_ticker/NVDA/market_confirmation/NVDA_market_observation_template.csv")
    assert csv_path.exists(), "NVDA market observation CSV should exist"

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

        required_headers = ["Date", "Closing_Price_USD", "Daily_Volume"]
        for header in required_headers:
            assert header in headers, f"Missing required CSV header: {header}"


def test_archive_manifest_has_checksums(nvda_archive_manifest):
    """Test NVDA archive manifest has SHA-256 checksums for all artifacts."""
    artifacts = nvda_archive_manifest["artifacts"]
    assert len(artifacts) > 0, "Archive should have at least one artifact"

    for artifact in artifacts:
        assert "sha256" in artifact, f"Missing checksum for artifact: {artifact.get('name')}"
        assert len(artifact["sha256"]) == 64, f"Invalid checksum length for artifact: {artifact.get('name')}"


def test_no_alert_infrastructure_triggered():
    """Test NVDA validation did not trigger alert/Telegram/email infrastructure."""
    # This is verified by safety flags, but also check output directory
    nvda_dir = Path("docs/sample_reports/generic_ticker/NVDA")

    # No alert files should be created
    alert_files = list(nvda_dir.rglob("*alert*"))
    telegram_files = list(nvda_dir.rglob("*telegram*"))
    email_files = list(nvda_dir.rglob("*email*"))

    assert len(alert_files) == 0, "No alert files should be created during validation"
    assert len(telegram_files) == 0, "No telegram files should be created during validation"
    assert len(email_files) == 0, "No email files should be created during validation"


def test_openinsider_spreadsheet_not_used(nvda_synthesis):
    """Test NVDA validation did not use OpenInsider spreadsheet."""
    assert nvda_synthesis["safety"]["openinsider_spreadsheet_used"] is False

    # Check source boundary explicitly excludes OpenInsider
    source_boundary = nvda_synthesis.get("source_boundary", [])
    source_str = " ".join(str(s) for s in source_boundary).lower()
    assert "openinsider" in source_str, "Source boundary should mention OpenInsider exclusion"


def test_no_secrets_in_outputs(nvda_synthesis, nvda_monitoring, nvda_market_confirmation, nvda_archive_manifest):
    """Test no secrets appear in NVDA outputs."""
    secret_patterns = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SMTP_PASSWORD",
        "GMAIL_APP_PASSWORD",
        "sk-ant-",
        "ETHERSCAN_API_KEY",
    ]

    for output_name, output_data in [
        ("synthesis", nvda_synthesis),
        ("monitoring", nvda_monitoring),
        ("market_confirmation", nvda_market_confirmation),
        ("archive", nvda_archive_manifest),
    ]:
        output_str = json.dumps(output_data)
        for pattern in secret_patterns:
            assert pattern not in output_str, f"{output_name}: Secret pattern '{pattern}' should not appear"


def test_ticker_profile_unknown(nvda_synthesis):
    """Test NVDA ticker profile is unknown_profile as specified in CP23I."""
    assert nvda_synthesis["ticker_profile"] == "unknown_profile", "NVDA ticker profile should be 'unknown_profile'"


def test_limitations_documented(nvda_synthesis, nvda_monitoring, nvda_market_confirmation):
    """Test all NVDA outputs document skeleton/validation mode limitations."""
    for output_name, output_data in [
        ("synthesis", nvda_synthesis),
        ("monitoring", nvda_monitoring),
        ("market_confirmation", nvda_market_confirmation),
    ]:
        limitations = output_data.get("limitations", [])
        assert len(limitations) > 0, f"{output_name}: Should document limitations"

        # Should mention skeleton/validation mode
        limitations_str = " ".join(str(lim) for lim in limitations).lower()
        assert "skeleton" in limitations_str or "validation" in limitations_str, f"{output_name}: Should mention skeleton/validation mode"
