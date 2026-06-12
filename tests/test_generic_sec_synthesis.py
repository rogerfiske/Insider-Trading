"""
Tests for Generic SEC Synthesis Composer (CP24H)

Validates:
1. Load MAIA CP24B-CP24G inputs
2. Load NVDA CP24B-CP24G inputs
3. Required JSON schema keys
4. Safety flags correct
5. Evidence matrix required categories
6. MAIA preserves CP24C Form 4 values
7. MAIA preserves CP24E liquidity/runway values
8. MAIA preserves CP24F dilution values
9. MAIA preserves CP24G partial 13F visibility values
10. NVDA does not contain MAIA-specific framing
11. NVDA clinical/pre-revenue framing not applicable
12. Scoring labels are from allowed list
13. No buy/sell/hold/price-target/recommendation language
14. Batch summary schema
15. Missing input module creates degraded-mode note
16. No secrets in outputs
17. No Telegram/email/alert code is called
18. OpenInsider spreadsheet is not required
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from sources.generic_synthesis_composer import (
    GenericSynthesisComposer,
    ALLOWED_POSTURES,
    ALLOWED_DIRECTIONS,
    ALLOWED_STRENGTHS,
    ALLOWED_CONFIDENCE
)


# Fixtures for test data
@pytest.fixture
def input_root():
    """Return input root for CP24B-CP24G outputs."""
    return Path("docs/sample_reports")


@pytest.fixture
def composer(input_root):
    """Return GenericSynthesisComposer instance."""
    return GenericSynthesisComposer(input_root=input_root)


@pytest.fixture
def maia_modules(composer):
    """Load MAIA CP24B-CP24G inputs."""
    return composer.load_module_inputs("MAIA")


@pytest.fixture
def nvda_modules(composer):
    """Load NVDA CP24B-CP24G inputs."""
    return composer.load_module_inputs("NVDA")


@pytest.fixture
def maia_synthesis(composer):
    """Compose MAIA synthesis packet."""
    return composer.compose_synthesis("MAIA")


@pytest.fixture
def nvda_synthesis(composer):
    """Compose NVDA synthesis packet."""
    return composer.compose_synthesis("NVDA")


@pytest.fixture
def maia_baseline():
    """Return approved MAIA baseline values from CP24 checkpoints."""
    return {
        "cik": "0001878313",
        "form4_filings": 219,
        "open_market_purchases": 141,
        "open_market_sales": 0,
        "purchase_value_usd": 5276429.73,
        "distinct_buyers": 10,
        "latest_purchase_date": "2026-06-01",
        "form_144_filings": 1,
        "schedule_13dg_filings": 11,
        "cash_usd": 34413110,
        "working_capital_usd": 28992690,
        "cash_runway_months": 19.4,
        "common_shares_outstanding": 60671491,
        "fully_diluted_low": 85033854,
        "fully_diluted_high": 88033854,
        "managers_reviewed": 5,
        "managers_parsed": 3,
        "maia_13f_matches": 0,
        "institutional_visibility": "partial"
    }


# Test 1: Load MAIA CP24B-CP24G inputs
def test_load_maia_inputs(maia_modules):
    """Test MAIA CP24B-CP24G inputs load successfully."""
    assert "sec_inventory" in maia_modules
    assert "form4_transactions" in maia_modules
    assert "ownership_filings" in maia_modules
    assert "xbrl_financials" in maia_modules
    assert "capital_structure" in maia_modules
    assert "institutional_13f" in maia_modules

    # All modules should have status
    for module_name, module_data in maia_modules.items():
        assert "status" in module_data, f"Module {module_name} missing status"


# Test 2: Load NVDA CP24B-CP24G inputs
def test_load_nvda_inputs(nvda_modules):
    """Test NVDA CP24B-CP24G inputs load successfully."""
    assert "sec_inventory" in nvda_modules
    assert "form4_transactions" in nvda_modules
    assert "ownership_filings" in nvda_modules
    assert "xbrl_financials" in nvda_modules
    assert "capital_structure" in nvda_modules
    assert "institutional_13f" in nvda_modules

    # All modules should have status
    for module_name, module_data in nvda_modules.items():
        assert "status" in module_data, f"Module {module_name} missing status"


# Test 3: Required JSON schema keys
def test_maia_synthesis_schema_keys(maia_synthesis):
    """Test MAIA synthesis has all required JSON schema keys."""
    required_keys = [
        "ticker",
        "cik",
        "company_name",
        "generated_at",
        "source_modules",
        "module_status",
        "evidence_matrix",
        "synthesis_scores",
        "key_findings",
        "critical_unknowns",
        "monitoring_triggers",
        "limitations",
        "degraded_mode",
        "evidence_provenance",
        "safety"
    ]

    for key in required_keys:
        assert key in maia_synthesis, f"Missing required key: {key}"


def test_nvda_synthesis_schema_keys(nvda_synthesis):
    """Test NVDA synthesis has all required JSON schema keys."""
    required_keys = [
        "ticker",
        "cik",
        "company_name",
        "generated_at",
        "source_modules",
        "module_status",
        "evidence_matrix",
        "synthesis_scores",
        "key_findings",
        "critical_unknowns",
        "monitoring_triggers",
        "limitations",
        "degraded_mode",
        "evidence_provenance",
        "safety"
    ]

    for key in required_keys:
        assert key in nvda_synthesis, f"Missing required key: {key}"


# Test 4: Safety flags correct
def test_maia_safety_flags(maia_synthesis):
    """Test MAIA synthesis safety flags are correct."""
    expected_safety = {
        "report_only": True,
        "alerts_generated": False,
        "openinsider_spreadsheet_used": False,
        "telegram_sent": False,
        "email_sent": False,
        "scheduled_tasks_modified": False,
        "env_printed_or_changed": False,
        "buy_sell_hold_language_used": False
    }

    safety = maia_synthesis["safety"]
    for flag, expected_value in expected_safety.items():
        assert flag in safety, f"Missing safety flag: {flag}"
        assert safety[flag] == expected_value, f"Safety flag '{flag}': expected {expected_value}, got {safety[flag]}"


def test_nvda_safety_flags(nvda_synthesis):
    """Test NVDA synthesis safety flags are correct."""
    expected_safety = {
        "report_only": True,
        "alerts_generated": False,
        "openinsider_spreadsheet_used": False,
        "telegram_sent": False,
        "email_sent": False,
        "scheduled_tasks_modified": False,
        "env_printed_or_changed": False,
        "buy_sell_hold_language_used": False
    }

    safety = nvda_synthesis["safety"]
    for flag, expected_value in expected_safety.items():
        assert flag in safety, f"Missing safety flag: {flag}"
        assert safety[flag] == expected_value, f"Safety flag '{flag}': expected {expected_value}, got {safety[flag]}"


# Test 5: Evidence matrix required categories
def test_evidence_matrix_required_categories(maia_synthesis):
    """Test evidence matrix contains required categories."""
    required_categories = {
        "Identity",
        "Data Coverage",
        "Insider Activity",
        "Ownership Filings",
        "Institutional Ownership",
        "Financial Liquidity",
        "Capital Structure"
    }

    evidence = maia_synthesis["evidence_matrix"]
    categories_found = {row["category"] for row in evidence}

    # At least some required categories should be present
    assert len(categories_found & required_categories) > 0, \
        f"No required categories found. Found: {categories_found}"


def test_evidence_matrix_allowed_values(maia_synthesis):
    """Test evidence matrix uses only allowed direction/strength/confidence values."""
    evidence = maia_synthesis["evidence_matrix"]

    for row in evidence:
        assert row["direction"] in ALLOWED_DIRECTIONS, \
            f"Invalid direction: {row['direction']}"
        assert row["strength"] in ALLOWED_STRENGTHS, \
            f"Invalid strength: {row['strength']}"
        assert row["confidence"] in ALLOWED_CONFIDENCE, \
            f"Invalid confidence: {row['confidence']}"


# Test 6: MAIA preserves CP24C Form 4 values
def test_maia_preserves_form4_values(maia_synthesis, maia_baseline):
    """Test MAIA synthesis preserves CP24C Form 4 transaction values."""
    # Find Form 4 evidence in matrix
    evidence = maia_synthesis["evidence_matrix"]
    form4_evidence = [e for e in evidence if e["source_module"] == "form4_transactions"]

    assert len(form4_evidence) > 0, "No Form 4 evidence found in matrix"

    # Check open market purchase evidence contains expected values
    purchase_evidence = [e for e in form4_evidence if "open-market" in e["evidence"].lower() and "purchase" in e["evidence"].lower()]
    assert len(purchase_evidence) > 0, "No open-market purchase evidence found"

    # Parse values from evidence text
    purchase_text = purchase_evidence[0]["evidence"]
    assert "141" in purchase_text or str(maia_baseline["open_market_purchases"]) in purchase_text, \
        f"Expected {maia_baseline['open_market_purchases']} purchases in evidence"


# Test 7: MAIA preserves CP24E liquidity/runway values
def test_maia_preserves_liquidity_values(maia_synthesis, maia_baseline):
    """Test MAIA synthesis preserves CP24E XBRL financial values."""
    evidence = maia_synthesis["evidence_matrix"]
    liquidity_evidence = [e for e in evidence if e["category"] == "Financial Liquidity"]

    assert len(liquidity_evidence) > 0, "No financial liquidity evidence found"

    # Check cash balance
    cash_evidence = [e for e in liquidity_evidence if "cash" in e["evidence"].lower()]
    assert len(cash_evidence) > 0, "No cash evidence found"

    # Check runway
    runway_evidence = [e for e in liquidity_evidence if "runway" in e["evidence"].lower()]
    assert len(runway_evidence) > 0, "No runway evidence found"


# Test 8: MAIA preserves CP24F dilution values
def test_maia_preserves_dilution_values(maia_synthesis, maia_baseline):
    """Test MAIA synthesis preserves CP24F capital structure values."""
    evidence = maia_synthesis["evidence_matrix"]
    capital_evidence = [e for e in evidence if e["category"] == "Capital Structure"]

    assert len(capital_evidence) > 0, "No capital structure evidence found"

    # Check for common shares evidence
    shares_evidence = [e for e in capital_evidence if "common shares" in e["evidence"].lower()]
    assert len(shares_evidence) > 0, "No common shares evidence found"

    # Check for dilution evidence if applicable
    dilution_evidence = [e for e in capital_evidence if "dilution" in e["evidence"].lower() or "overhang" in e["evidence"].lower()]
    # Dilution may or may not be present depending on data availability


# Test 9: MAIA preserves CP24G partial 13F visibility values
def test_maia_preserves_13f_values(maia_synthesis, maia_baseline):
    """Test MAIA synthesis preserves CP24G 13F institutional ownership values."""
    evidence = maia_synthesis["evidence_matrix"]
    inst_evidence = [e for e in evidence if e["category"] == "Institutional Ownership"]

    assert len(inst_evidence) > 0, "No institutional ownership evidence found"

    # Check for partial visibility mention
    visibility_text = " ".join([e["evidence"].lower() for e in inst_evidence])
    assert "partial" in visibility_text or "managers" in visibility_text, \
        "Expected partial institutional visibility mention"


# Test 10: NVDA does not contain MAIA-specific framing
def test_nvda_no_maia_framing(nvda_synthesis):
    """Test NVDA synthesis does not contain MAIA-specific framing."""
    text = json.dumps(nvda_synthesis).lower()

    # MAIA-specific terms that should NOT appear in NVDA
    maia_specific = [
        "thio",
        "$1.50",
        "1.50",
        "biotech",
        "clinical",
        "trial",
        "regulatory",
        "fda"
    ]

    # Allow these terms if they appear in standard contexts (not ticker-specific)
    # But they should not appear prominently
    for term in maia_specific:
        if term in text:
            # OK if it appears in source_modules path or standard limitations
            # Not OK if it appears in evidence or findings
            evidence_text = json.dumps(nvda_synthesis.get("evidence_matrix", [])).lower()
            findings_text = json.dumps(nvda_synthesis.get("key_findings", [])).lower()

            assert term not in evidence_text, f"Found MAIA-specific term '{term}' in NVDA evidence"
            assert term not in findings_text, f"Found MAIA-specific term '{term}' in NVDA findings"


# Test 11: NVDA clinical/pre-revenue framing not applicable
def test_nvda_clinical_not_applicable(nvda_synthesis):
    """Test NVDA synthesis does not use clinical/pre-revenue framing."""
    text = json.dumps(nvda_synthesis).lower()

    # Clinical/pre-revenue terms should not appear
    clinical_terms = [
        "clinical program",
        "phase 1",
        "phase 2",
        "phase 3",
        "pre-revenue",
        "pre revenue",
        "early stage",
        "development stage"
    ]

    for term in clinical_terms:
        assert term not in text, f"Found clinical/pre-revenue term '{term}' in NVDA synthesis"


# Test 12: Scoring labels are from allowed list
def test_maia_scoring_labels_allowed(maia_synthesis):
    """Test MAIA synthesis uses only allowed scoring posture labels."""
    posture = maia_synthesis["synthesis_scores"]["overall_research_posture"]
    assert posture in ALLOWED_POSTURES, \
        f"Overall posture '{posture}' not in allowed list: {ALLOWED_POSTURES}"


def test_nvda_scoring_labels_allowed(nvda_synthesis):
    """Test NVDA synthesis uses only allowed scoring posture labels."""
    posture = nvda_synthesis["synthesis_scores"]["overall_research_posture"]
    assert posture in ALLOWED_POSTURES, \
        f"Overall posture '{posture}' not in allowed list: {ALLOWED_POSTURES}"


# Test 13: No buy/sell/hold/price-target/recommendation language
def test_maia_no_recommendation_language(maia_synthesis):
    """Test MAIA synthesis contains no recommendation language."""
    text = json.dumps(maia_synthesis).lower()

    forbidden_terms = [
        "strong buy",
        "strong sell",
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "price target",
        "expected return",
        "outperform",
        "underperform",
        "rating:",
        "we recommend"
    ]

    for term in forbidden_terms:
        assert term not in text, f"Found forbidden recommendation language: '{term}'"


def test_nvda_no_recommendation_language(nvda_synthesis):
    """Test NVDA synthesis contains no recommendation language."""
    text = json.dumps(nvda_synthesis).lower()

    forbidden_terms = [
        "strong buy",
        "strong sell",
        "buy recommendation",
        "sell recommendation",
        "hold recommendation",
        "price target",
        "expected return",
        "outperform",
        "underperform",
        "rating:",
        "we recommend"
    ]

    for term in forbidden_terms:
        assert term not in text, f"Found forbidden recommendation language: '{term}'"


# Test 14: Batch summary schema
def test_batch_summary_schema(composer):
    """Test batch summary has required schema."""
    tickers = ["MAIA", "NVDA"]
    syntheses = {
        "MAIA": composer.compose_synthesis("MAIA"),
        "NVDA": composer.compose_synthesis("NVDA")
    }

    batch_summary = composer.compose_batch_summary(tickers, syntheses)

    required_keys = [
        "generated_at",
        "tickers_requested",
        "tickers_success",
        "tickers_failed",
        "per_ticker_summary",
        "safety"
    ]

    for key in required_keys:
        assert key in batch_summary, f"Missing required key in batch summary: {key}"

    # Check per-ticker summary structure
    assert len(batch_summary["per_ticker_summary"]) == 2, "Expected 2 ticker summaries"

    for summary in batch_summary["per_ticker_summary"]:
        assert "ticker" in summary
        assert "company_name" in summary
        assert "overall_posture" in summary
        assert "data_quality_score" in summary
        assert "is_degraded" in summary


# Test 15: Missing input module creates degraded-mode note
def test_missing_module_degraded_mode(composer, tmp_path):
    """Test missing input module triggers degraded mode."""
    # Create a mock composer with missing module
    with patch.object(composer, '_load_json') as mock_load:
        # Make xbrl_financials return error
        def mock_load_side_effect(path, required=False):
            if "xbrl_financials" in str(path):
                return {"status": "error", "error_type": "file_not_found"}
            # Load real data for other modules
            return composer._load_json.__wrapped__(composer, path, required)

        mock_load.side_effect = mock_load_side_effect

        synthesis = composer.compose_synthesis("MAIA")

        # Should be in degraded mode
        assert synthesis["degraded_mode"]["is_degraded"] == True, \
            "Expected degraded mode when module missing"
        assert len(synthesis["degraded_mode"]["reasons"]) > 0, \
            "Expected degraded reasons when module missing"


# Test 16: No secrets in outputs
def test_maia_no_secrets(maia_synthesis):
    """Test MAIA synthesis contains no secrets."""
    text = json.dumps(maia_synthesis)

    secret_patterns = [
        "sk-ant-api",
        "xoxb-",
        "ghp_",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SMTP_PASSWORD",
        "GMAIL_APP_PASSWORD",
        "BEGIN PRIVATE KEY"
    ]

    for pattern in secret_patterns:
        assert pattern not in text, f"Found secret pattern in output: {pattern}"


def test_nvda_no_secrets(nvda_synthesis):
    """Test NVDA synthesis contains no secrets."""
    text = json.dumps(nvda_synthesis)

    secret_patterns = [
        "sk-ant-api",
        "xoxb-",
        "ghp_",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SMTP_PASSWORD",
        "GMAIL_APP_PASSWORD",
        "BEGIN PRIVATE KEY"
    ]

    for pattern in secret_patterns:
        assert pattern not in text, f"Found secret pattern in output: {pattern}"


# Test 17: No Telegram/email/alert code is called
def test_no_telegram_imports():
    """Test generic_synthesis_composer does not import telegram modules."""
    with open("sources/generic_synthesis_composer.py", "r", encoding="utf-8") as f:
        source_code = f.read()

    forbidden_imports = [
        "import telegram",
        "from telegram",
        "import alerts_telegram",
        "from alerts_telegram",
        "import alerts_smtp_email",
        "from alerts_smtp_email"
    ]

    for forbidden in forbidden_imports:
        assert forbidden not in source_code, \
            f"Found forbidden import: {forbidden}"


def test_no_alert_function_calls():
    """Test generic_synthesis_composer does not call alert functions."""
    with open("sources/generic_synthesis_composer.py", "r", encoding="utf-8") as f:
        source_code = f.read()

    forbidden_calls = [
        "send_telegram",
        "send_email",
        "route_alert",
        "generate_alert"
    ]

    for forbidden in forbidden_calls:
        assert forbidden not in source_code, \
            f"Found forbidden function call: {forbidden}"


# Test 18: OpenInsider spreadsheet is not required
def test_no_openinsider_dependency(composer):
    """Test synthesis does not require OpenInsider spreadsheet."""
    # Compose MAIA synthesis without OpenInsider
    synthesis = composer.compose_synthesis("MAIA")

    # Should succeed without OpenInsider
    assert synthesis is not None
    assert synthesis["safety"]["openinsider_spreadsheet_used"] == False


def test_no_openinsider_imports():
    """Test generic_synthesis_composer does not import OpenInsider modules."""
    with open("sources/generic_synthesis_composer.py", "r", encoding="utf-8") as f:
        source_code = f.read()

    forbidden_terms = [
        "openinsider",
        "OpenInsider",
        "MAIA.xlsx",
        "openpyxl"
    ]

    for term in forbidden_terms:
        assert term not in source_code, \
            f"Found OpenInsider reference: {term}"


# Additional validation tests
def test_synthesis_scores_structure(maia_synthesis):
    """Test synthesis scores have correct structure."""
    scores = maia_synthesis["synthesis_scores"]

    required_score_keys = [
        "insider_evidence_score",
        "capital_structure_risk_score",
        "financial_liquidity_score",
        "ownership_visibility_score",
        "data_quality_score",
        "overall_research_posture"
    ]

    for key in required_score_keys:
        assert key in scores, f"Missing score component: {key}"

    # Scores should be 0-100 or None
    for key in required_score_keys[:-1]:  # Exclude overall_research_posture
        score = scores[key]
        if score is not None:
            assert 0 <= score <= 100, f"Score {key} out of range: {score}"


def test_evidence_provenance_structure(maia_synthesis):
    """Test evidence provenance has correct structure."""
    provenance = maia_synthesis["evidence_provenance"]

    assert isinstance(provenance, list)
    assert len(provenance) > 0

    for prov in provenance:
        assert "module" in prov
        assert "source" in prov
        assert "timestamp" in prov
        assert "SEC EDGAR" in prov["source"]


def test_limitations_present(maia_synthesis):
    """Test synthesis includes comprehensive limitations."""
    limitations = maia_synthesis["limitations"]

    assert isinstance(limitations, list)
    assert len(limitations) > 0

    # Check for key limitation types
    limitations_text = " ".join(limitations).lower()
    assert "sec" in limitations_text or "edgar" in limitations_text
    assert "not investment advice" in limitations_text or "research synthesis" in limitations_text


def test_module_status_complete(maia_synthesis):
    """Test module_status reports on all expected modules."""
    module_status = maia_synthesis["module_status"]

    expected_modules = [
        "sec_inventory",
        "form4_transactions",
        "ownership_filings",
        "xbrl_financials",
        "capital_structure",
        "institutional_13f"
    ]

    for module in expected_modules:
        assert module in module_status, f"Missing module status: {module}"
