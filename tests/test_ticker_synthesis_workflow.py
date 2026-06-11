"""
Tests for Generic Ticker Synthesis Workflow (CP23C)

Validates:
- MAIA baseline value preservation
- Safety flag correctness
- No buy/sell/hold recommendation language
- JSON schema compliance
- Generic framework functionality
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def generic_maia_synthesis():
    """Load generic MAIA synthesis packet (validation mode output)."""
    path = Path("docs/sample_reports/generic_ticker/MAIA/synthesis/MAIA_synthesis_packet.json")
    if not path.exists():
        pytest.skip(f"Generic MAIA synthesis not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def maia_baseline():
    """Return approved MAIA baseline values."""
    return {
        "ticker": "MAIA",
        "cik": "0001878313",
        "insider_purchases": 134,
        "insider_sales": 0,
        "purchase_value_usd": 4921437.58,
        "distinct_buyers": 10,
        "latest_purchase_date": "2026-06-01",
        "cash_balance_usd": 34413110,
        "working_capital_usd": 28992690,
        "offering_reference_price_usd": 1.50,
        "common_shares_outstanding": 60671491,
    }


def test_maia_insider_purchases_preserved(generic_maia_synthesis, maia_baseline):
    """Test MAIA insider purchase count preserved."""
    ia = generic_maia_synthesis["modules"]["insider_activity"]
    assert ia["open_market_purchases"] == maia_baseline["insider_purchases"]


def test_maia_insider_sales_preserved(generic_maia_synthesis, maia_baseline):
    """Test MAIA insider sale count preserved (zero)."""
    ia = generic_maia_synthesis["modules"]["insider_activity"]
    assert ia["open_market_sales"] == maia_baseline["insider_sales"]


def test_maia_purchase_value_preserved(generic_maia_synthesis, maia_baseline):
    """Test MAIA purchase value preserved."""
    ia = generic_maia_synthesis["modules"]["insider_activity"]
    assert ia["purchase_value_usd"] == pytest.approx(maia_baseline["purchase_value_usd"])


def test_maia_distinct_buyers_preserved(generic_maia_synthesis, maia_baseline):
    """Test MAIA distinct buyer count preserved."""
    ia = generic_maia_synthesis["modules"]["insider_activity"]
    assert ia["distinct_buyers"] == maia_baseline["distinct_buyers"]


def test_maia_cash_balance_preserved(generic_maia_synthesis, maia_baseline):
    """Test MAIA cash balance preserved."""
    cash_runway = generic_maia_synthesis["modules"]["cash_runway"]
    official_10q = cash_runway["official_10q_financials"]
    assert official_10q["cash_and_equivalents"] == maia_baseline["cash_balance_usd"]


def test_maia_working_capital_preserved(generic_maia_synthesis, maia_baseline):
    """Test MAIA working capital preserved."""
    cash_runway = generic_maia_synthesis["modules"]["cash_runway"]
    official_10q = cash_runway["official_10q_financials"]
    assert official_10q["working_capital"] == maia_baseline["working_capital_usd"]


def test_maia_offering_price_preserved(generic_maia_synthesis, maia_baseline):
    """Test MAIA offering reference price preserved."""
    mc = generic_maia_synthesis["modules"]["market_confirmation"]
    assert mc["reference_price"] == maia_baseline["offering_reference_price_usd"]


def test_maia_common_shares_preserved(generic_maia_synthesis, maia_baseline):
    """Test MAIA common shares outstanding preserved."""
    cash_runway = generic_maia_synthesis["modules"]["cash_runway"]
    official_10q = cash_runway["official_10q_financials"]
    assert official_10q["common_shares_outstanding"] == maia_baseline["common_shares_outstanding"]


def test_safety_flags_correct(generic_maia_synthesis):
    """Test safety flags are correctly set."""
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

    safety = generic_maia_synthesis["safety"]

    for flag, expected_value in expected.items():
        assert flag in safety, f"Missing safety flag: {flag}"
        assert safety[flag] == expected_value, f"Safety flag '{flag}': expected {expected_value}, got {safety[flag]}"


def test_no_recommendation_language(generic_maia_synthesis):
    """Test output contains no buy/sell/hold recommendation language."""
    text = json.dumps(generic_maia_synthesis).lower()

    # These phrases must NOT appear
    forbidden = [
        "strong buy",
        "strong sell",
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "price target",
        "expected return",
    ]

    for term in forbidden:
        assert term not in text, f"Found forbidden recommendation language: '{term}'"


def test_required_schema_keys(generic_maia_synthesis):
    """Test required schema keys are present."""
    required_top_level = [
        "ticker",
        "cik",
        "generated_at",
        "source_boundary",
        "modules",
        "evidence_matrix",
        "synthesis_scores",
        "safety",
    ]

    for key in required_top_level:
        assert key in generic_maia_synthesis, f"Missing required key: {key}"


def test_biotech_profile_has_clinical_module(generic_maia_synthesis):
    """Test biotech profile includes clinical_regulatory module."""
    assert generic_maia_synthesis.get("ticker_profile") == "biotech_clinical"
    assert "clinical_regulatory" in generic_maia_synthesis["modules"]
    clinical = generic_maia_synthesis["modules"]["clinical_regulatory"]
    assert clinical != "not_applicable"
    assert "clinical_programs" in clinical


def test_evidence_matrix_structure(generic_maia_synthesis):
    """Test evidence matrix has correct structure."""
    matrix = generic_maia_synthesis["evidence_matrix"]
    assert isinstance(matrix, list)
    assert len(matrix) > 0

    # Check first entry has required fields
    entry = matrix[0]
    required_fields = ["category", "evidence", "direction", "strength", "confidence", "source"]

    for field in required_fields:
        assert field in entry, f"Evidence matrix entry missing field: {field}"


def test_overall_posture_no_recommendation(generic_maia_synthesis):
    """Test overall posture uses descriptive (not prescriptive) language."""
    posture = generic_maia_synthesis["synthesis_scores"]["overall_research_posture"]

    # Must NOT contain
    forbidden = ["buy", "sell", "hold", "target", "recommendation"]

    for term in forbidden:
        assert term.lower() not in posture.lower(), f"Overall posture contains forbidden term: '{term}'"


def test_source_boundary_documented(generic_maia_synthesis):
    """Test source boundary is documented."""
    boundary = generic_maia_synthesis["source_boundary"]
    assert isinstance(boundary, list)
    assert len(boundary) > 0

    # Check for key phrases
    boundary_text = " ".join(boundary).lower()
    assert "sec edgar" in boundary_text or "sec" in boundary_text


def test_no_secrets_in_output(generic_maia_synthesis):
    """Test no secrets appear in synthesis output."""
    text = json.dumps(generic_maia_synthesis)

    forbidden_secrets = [
        "sk-ant-api",  # Anthropic API key prefix
        "xoxb-",  # Slack bot token prefix
        "ghp_",  # GitHub personal access token prefix
    ]

    for secret in forbidden_secrets:
        assert secret not in text, f"Found secret value in output: {secret}"
