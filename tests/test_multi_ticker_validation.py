"""
Tests for CP24I multi-ticker validation coverage.

Verifies that all five requested tickers (MAIA, NVDA, AAPL, MSFT, TSLA)
have appropriate validation records with correct statuses.
"""
import json
import pytest
from pathlib import Path


# Test fixture paths
VALIDATION_ROOT = Path("../docs/sample_reports/cp24i_validation")
BATCH_SUMMARY_JSON = VALIDATION_ROOT / "batch_generic_sec_synthesis_summary.json"
VALIDATION_MATRIX_CSV = VALIDATION_ROOT / "validation_matrix.csv"


# Test 1: Batch summary JSON exists
def test_batch_summary_json_exists():
    """Batch summary JSON file must exist."""
    assert BATCH_SUMMARY_JSON.exists(), f"Batch summary JSON not found at {BATCH_SUMMARY_JSON}"


# Test 2: Batch summary JSON includes all 5 tickers in tickers_requested
def test_batch_summary_includes_all_five_tickers():
    """Batch summary tickers_requested must include all 5 tickers."""
    with open(BATCH_SUMMARY_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tickers_requested = data.get("tickers_requested", [])
    assert "MAIA" in tickers_requested, "MAIA missing from tickers_requested"
    assert "NVDA" in tickers_requested, "NVDA missing from tickers_requested"
    assert "AAPL" in tickers_requested, "AAPL missing from tickers_requested"
    assert "MSFT" in tickers_requested, "MSFT missing from tickers_requested"
    assert "TSLA" in tickers_requested, "TSLA missing from tickers_requested"
    assert len(tickers_requested) == 5, f"Expected 5 tickers, got {len(tickers_requested)}"


# Test 3: Batch summary JSON includes MAIA, NVDA in tickers_success
def test_batch_summary_tickers_success():
    """Batch summary tickers_success must include MAIA and NVDA."""
    with open(BATCH_SUMMARY_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tickers_success = data.get("tickers_success", [])
    assert "MAIA" in tickers_success, "MAIA missing from tickers_success"
    assert "NVDA" in tickers_success, "NVDA missing from tickers_success"
    assert len(tickers_success) == 2, f"Expected 2 success tickers, got {len(tickers_success)}"


# Test 4: Batch summary JSON includes AAPL, MSFT, TSLA in tickers_not_run
def test_batch_summary_tickers_not_run():
    """Batch summary tickers_not_run must include AAPL, MSFT, and TSLA."""
    with open(BATCH_SUMMARY_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tickers_not_run = data.get("tickers_not_run", [])
    assert "AAPL" in tickers_not_run, "AAPL missing from tickers_not_run"
    assert "MSFT" in tickers_not_run, "MSFT missing from tickers_not_run"
    assert "TSLA" in tickers_not_run, "TSLA missing from tickers_not_run"
    assert len(tickers_not_run) == 3, f"Expected 3 not-run tickers, got {len(tickers_not_run)}"


# Test 5: MAIA, NVDA have validation_status "completed"
def test_maia_nvda_validation_status_completed():
    """MAIA and NVDA per_ticker_summary entries must have validation_status='completed'."""
    with open(BATCH_SUMMARY_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    per_ticker = {entry["ticker"]: entry for entry in data.get("per_ticker_summary", [])}

    assert "MAIA" in per_ticker, "MAIA missing from per_ticker_summary"
    assert per_ticker["MAIA"]["validation_status"] == "completed", \
        f"MAIA validation_status is {per_ticker['MAIA']['validation_status']}, expected 'completed'"

    assert "NVDA" in per_ticker, "NVDA missing from per_ticker_summary"
    assert per_ticker["NVDA"]["validation_status"] == "completed", \
        f"NVDA validation_status is {per_ticker['NVDA']['validation_status']}, expected 'completed'"


# Test 6: AAPL, MSFT, TSLA have validation_status "not_run_with_reason"
def test_aapl_msft_tsla_validation_status_not_run():
    """AAPL, MSFT, and TSLA per_ticker_summary entries must have validation_status='not_run_with_reason'."""
    with open(BATCH_SUMMARY_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    per_ticker = {entry["ticker"]: entry for entry in data.get("per_ticker_summary", [])}

    for ticker in ["AAPL", "MSFT", "TSLA"]:
        assert ticker in per_ticker, f"{ticker} missing from per_ticker_summary"
        assert per_ticker[ticker]["validation_status"] == "not_run_with_reason", \
            f"{ticker} validation_status is {per_ticker[ticker]['validation_status']}, expected 'not_run_with_reason'"


# Test 7: Validation matrix CSV exists
def test_validation_matrix_csv_exists():
    """Validation matrix CSV file must exist."""
    assert VALIDATION_MATRIX_CSV.exists(), f"Validation matrix CSV not found at {VALIDATION_MATRIX_CSV}"


# Test 8: Validation matrix CSV includes all 5 tickers
def test_validation_matrix_includes_all_tickers():
    """Validation matrix CSV must include all 5 tickers."""
    with open(VALIDATION_MATRIX_CSV, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "MAIA" in content, "MAIA missing from validation_matrix.csv"
    assert "NVDA" in content, "NVDA missing from validation_matrix.csv"
    assert "AAPL" in content, "AAPL missing from validation_matrix.csv"
    assert "MSFT" in content, "MSFT missing from validation_matrix.csv"
    assert "TSLA" in content, "TSLA missing from validation_matrix.csv"


# Test 9: AAPL validation summary JSON exists
def test_aapl_validation_summary_exists():
    """AAPL validation summary JSON must exist."""
    aapl_summary = VALIDATION_ROOT / "AAPL" / "AAPL_validation_summary.json"
    assert aapl_summary.exists(), f"AAPL validation summary not found at {aapl_summary}"


# Test 10: MSFT validation summary JSON exists
def test_msft_validation_summary_exists():
    """MSFT validation summary JSON must exist."""
    msft_summary = VALIDATION_ROOT / "MSFT" / "MSFT_validation_summary.json"
    assert msft_summary.exists(), f"MSFT validation summary not found at {msft_summary}"


# Test 11: TSLA validation summary JSON exists
def test_tsla_validation_summary_exists():
    """TSLA validation summary JSON must exist."""
    tsla_summary = VALIDATION_ROOT / "TSLA" / "TSLA_validation_summary.json"
    assert tsla_summary.exists(), f"TSLA validation summary not found at {tsla_summary}"


# Test 12: AAPL validation summary has is_degraded: true
def test_aapl_is_degraded():
    """AAPL validation summary must have degraded_mode.is_degraded = true."""
    aapl_summary = VALIDATION_ROOT / "AAPL" / "AAPL_validation_summary.json"
    with open(aapl_summary, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert "degraded_mode" in data, "degraded_mode missing from AAPL validation summary"
    assert data["degraded_mode"]["is_degraded"] is True, \
        f"AAPL is_degraded is {data['degraded_mode']['is_degraded']}, expected True"


# Test 13: MSFT validation summary has is_degraded: true
def test_msft_is_degraded():
    """MSFT validation summary must have degraded_mode.is_degraded = true."""
    msft_summary = VALIDATION_ROOT / "MSFT" / "MSFT_validation_summary.json"
    with open(msft_summary, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert "degraded_mode" in data, "degraded_mode missing from MSFT validation summary"
    assert data["degraded_mode"]["is_degraded"] is True, \
        f"MSFT is_degraded is {data['degraded_mode']['is_degraded']}, expected True"


# Test 14: TSLA validation summary has is_degraded: true
def test_tsla_is_degraded():
    """TSLA validation summary must have degraded_mode.is_degraded = true."""
    tsla_summary = VALIDATION_ROOT / "TSLA" / "TSLA_validation_summary.json"
    with open(tsla_summary, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert "degraded_mode" in data, "degraded_mode missing from TSLA validation summary"
    assert data["degraded_mode"]["is_degraded"] is True, \
        f"TSLA is_degraded is {data['degraded_mode']['is_degraded']}, expected True"


# Test 15: All safety flags are correct
def test_all_safety_flags():
    """All tickers must have correct safety flags in batch summary."""
    with open(BATCH_SUMMARY_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    safety = data.get("safety", {})
    assert safety.get("report_only") is True, "safety.report_only must be True"
    assert safety.get("alerts_generated") is False, "safety.alerts_generated must be False"
    assert safety.get("external_spreadsheet_used") is False, "safety.external_spreadsheet_used must be False"
    assert safety.get("telegram_sent") is False, "safety.telegram_sent must be False"
    assert safety.get("email_sent") is False, "safety.email_sent must be False"
    assert safety.get("scheduled_tasks_modified") is False, "safety.scheduled_tasks_modified must be False"
    assert safety.get("env_printed_or_changed") is False, "safety.env_printed_or_changed must be False"
    assert safety.get("buy_sell_hold_language_used") is False, "safety.buy_sell_hold_language_used must be False"
