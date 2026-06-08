"""Tests for watchlist history delta computation."""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from watchlist.history_store import WatchlistHistoryStore


def test_delta_computation_no_prior():
    """Test delta computation when there is no prior run."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        current_metrics = {
            "ticker": "TEST",
            "purchase_count": 10,
            "purchase_value": 100000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
        }

        delta = store.compute_delta(current_metrics, prior_result=None)

        assert delta["has_prior"] is False
        assert delta["prior_run_id"] is None
        assert delta["purchase_value_delta"] is None
        assert delta["purchase_count_delta"] is None
        assert delta["signal_changed"] is False
        assert "First run" in delta["summary"]


def test_delta_computation_unchanged():
    """Test delta computation with no changes."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        prior_result = {
            "run_id": "prior-123",
            "created_at": "2026-01-01T00:00:00Z",
            "purchase_count": 10,
            "purchase_value": 100000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "transactions_extracted": 10,
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
        }

        current_metrics = {
            "ticker": "TEST",
            "purchase_count": 10,
            "purchase_value": 100000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "transactions_extracted": 10,
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
        }

        delta = store.compute_delta(current_metrics, prior_result)

        assert delta["has_prior"] is True
        assert delta["prior_run_id"] == "prior-123"
        assert delta["purchase_value_delta"] == 0
        assert delta["purchase_count_delta"] == 0
        assert delta["sale_value_delta"] == 0
        assert delta["sale_count_delta"] == 0
        assert delta["signal_changed"] is False
        assert "No purchase value change" in delta["summary"]


def test_delta_computation_increased_purchases():
    """Test delta computation with increased purchase value."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        prior_result = {
            "run_id": "prior-123",
            "created_at": "2026-01-01T00:00:00Z",
            "purchase_count": 10,
            "purchase_value": 100000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "transactions_extracted": 10,
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
        }

        current_metrics = {
            "ticker": "TEST",
            "purchase_count": 15,
            "purchase_value": 150000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "transactions_extracted": 15,
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
        }

        delta = store.compute_delta(current_metrics, prior_result)

        assert delta["has_prior"] is True
        assert delta["purchase_value_delta"] == 50000.0
        assert delta["purchase_count_delta"] == 5
        assert delta["new_transactions_estimate"] == 5
        assert delta["signal_changed"] is False
        assert "+$50,000.00 purchases" in delta["summary"]


def test_delta_computation_new_sales():
    """Test delta computation with new sales."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        prior_result = {
            "run_id": "prior-123",
            "created_at": "2026-01-01T00:00:00Z",
            "purchase_count": 10,
            "purchase_value": 100000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "transactions_extracted": 10,
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
        }

        current_metrics = {
            "ticker": "TEST",
            "purchase_count": 10,
            "purchase_value": 100000.0,
            "sale_count": 2,
            "sale_value": 20000.0,
            "transactions_extracted": 12,
            "eddie_signal": "NEUTRAL",
            "eddie_confidence": 1,
        }

        delta = store.compute_delta(current_metrics, prior_result)

        assert delta["has_prior"] is True
        assert delta["sale_value_delta"] == 20000.0
        assert delta["sale_count_delta"] == 2
        assert delta["signal_changed"] is True
        assert delta["confidence_delta"] == -1
        assert "+$20,000.00 sales" in delta["summary"]
        assert "Signal changed" in delta["summary"]


def test_delta_computation_signal_change():
    """Test delta computation with signal change."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        prior_result = {
            "run_id": "prior-123",
            "created_at": "2026-01-01T00:00:00Z",
            "purchase_count": 5,
            "purchase_value": 50000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "transactions_extracted": 5,
            "eddie_signal": "NEUTRAL",
            "eddie_confidence": 1,
        }

        current_metrics = {
            "ticker": "TEST",
            "purchase_count": 5,
            "purchase_value": 50000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "transactions_extracted": 5,
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
        }

        delta = store.compute_delta(current_metrics, prior_result)

        assert delta["has_prior"] is True
        assert delta["signal_changed"] is True
        assert delta["confidence_delta"] == 1
        assert "Signal changed: NEUTRAL → BULLISH_EVIDENCE" in delta["summary"]


def test_save_and_retrieve_delta():
    """Test saving and retrieving delta records."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        # Save first run
        run_id_1 = store.save_run(
            mode="test", tickers_requested=1, tickers_resolved=1, lookback_days=365,
            max_form4_filings=0
        )

        # Save second run
        run_id_2 = store.save_run(
            mode="test", tickers_requested=1, tickers_resolved=1, lookback_days=365,
            max_form4_filings=0
        )

        # Compute and save delta
        delta = {
            "has_prior": True,
            "prior_run_id": run_id_1,
            "purchase_value_delta": 50000.0,
            "purchase_count_delta": 5,
            "sale_value_delta": 0.0,
            "sale_count_delta": 0,
            "new_transactions_estimate": 5,
            "signal_changed": False,
            "confidence_delta": 0,
            "summary": "Increased purchases",
        }

        delta_id = store.save_delta(run_id=run_id_2, ticker="TEST", delta=delta)

        assert isinstance(delta_id, int)
        assert delta_id > 0

        # Retrieve via run summary
        summary = store.get_run_summary(run_id_2)
        assert len(summary["deltas"]) == 1
        saved_delta = summary["deltas"][0]
        assert saved_delta["ticker"] == "TEST"
        assert saved_delta["prior_run_id"] == run_id_1
        assert saved_delta["purchase_value_delta"] == 50000.0
        assert saved_delta["signal_changed"] == 0  # Stored as int


def test_delta_with_null_values():
    """Test delta computation handles None/null values gracefully."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        prior_result = {
            "run_id": "prior-123",
            "created_at": "2026-01-01T00:00:00Z",
            "purchase_count": None,
            "purchase_value": None,
            "sale_count": None,
            "sale_value": None,
            "transactions_extracted": 0,
            "eddie_signal": None,
            "eddie_confidence": None,
        }

        current_metrics = {
            "ticker": "TEST",
            "purchase_count": 10,
            "purchase_value": 100000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "transactions_extracted": 10,
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
        }

        # Should not raise an exception
        delta = store.compute_delta(current_metrics, prior_result)

        assert delta["has_prior"] is True
        assert delta["purchase_value_delta"] == 100000.0
        assert delta["purchase_count_delta"] == 10
