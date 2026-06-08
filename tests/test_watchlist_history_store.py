"""Tests for watchlist history store SQLite operations."""

import os
import sqlite3
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from watchlist.history_store import WatchlistHistoryStore


def test_database_initialization():
    """Test that database schema is created correctly."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        # Verify database file was created
        assert db_path.exists()

        # Verify tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        assert "watchlist_runs" in tables
        assert "watchlist_ticker_results" in tables
        assert "watchlist_ticker_deltas" in tables

        conn.close()


def test_save_and_retrieve_run():
    """Test saving and retrieving a run record."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        # Save a run
        run_id = store.save_run(
            mode="test_mode",
            tickers_requested=3,
            tickers_resolved=2,
            lookback_days=365,
            max_form4_filings=100,
            git_commit="abc1234",
            notes="Test run",
        )

        # Verify run_id is a UUID string
        assert isinstance(run_id, str)
        assert len(run_id) == 36  # UUID format

        # Retrieve run
        summary = store.get_run_summary(run_id)
        assert summary is not None
        assert summary["run_id"] == run_id
        assert summary["mode"] == "test_mode"
        assert summary["tickers_requested"] == 3
        assert summary["tickers_resolved"] == 2
        assert summary["lookback_days"] == 365
        assert summary["git_commit"] == "abc1234"


def test_save_ticker_result():
    """Test saving ticker result."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        # Save a run first
        run_id = store.save_run(
            mode="test_mode",
            tickers_requested=1,
            tickers_resolved=1,
            lookback_days=365,
            max_form4_filings=0,
        )

        # Save ticker result
        metrics = {
            "ticker": "TEST",
            "cik": "0001234567",
            "company_name": "Test Company",
            "eddie_signal": "BULLISH_EVIDENCE",
            "eddie_confidence": 2,
            "purchase_count": 10,
            "purchase_value": 100000.50,
            "sale_count": 0,
            "sale_value": 0.0,
            "net_purchase_value": 100000.50,
        }

        result_id = store.save_ticker_result(
            run_id=run_id, ticker="TEST", metrics=metrics
        )

        # Verify result_id is an integer
        assert isinstance(result_id, int)
        assert result_id > 0

        # Retrieve via run summary
        summary = store.get_run_summary(run_id)
        assert len(summary["ticker_results"]) == 1
        result = summary["ticker_results"][0]
        assert result["ticker"] == "TEST"
        assert result["cik"] == "0001234567"
        assert result["purchase_count"] == 10
        assert result["purchase_value"] == 100000.50


def test_get_most_recent_result_for_ticker():
    """Test retrieving most recent result for a ticker."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        # Save first run
        run_id_1 = store.save_run(
            mode="test", tickers_requested=1, tickers_resolved=1, lookback_days=365,
            max_form4_filings=0
        )

        metrics_1 = {
            "ticker": "TEST",
            "purchase_count": 5,
            "purchase_value": 50000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "net_purchase_value": 50000.0,
        }

        store.save_ticker_result(run_id=run_id_1, ticker="TEST", metrics=metrics_1)

        # Save second run (newer)
        run_id_2 = store.save_run(
            mode="test", tickers_requested=1, tickers_resolved=1, lookback_days=365,
            max_form4_filings=0
        )

        metrics_2 = {
            "ticker": "TEST",
            "purchase_count": 10,
            "purchase_value": 100000.0,
            "sale_count": 0,
            "sale_value": 0.0,
            "net_purchase_value": 100000.0,
        }

        store.save_ticker_result(run_id=run_id_2, ticker="TEST", metrics=metrics_2)

        # Get most recent (should be run_id_2)
        recent = store.get_most_recent_result_for_ticker("TEST")
        assert recent is not None
        assert recent["run_id"] == run_id_2
        assert recent["purchase_count"] == 10

        # Get most recent excluding run_id_2 (should be run_id_1)
        prior = store.get_most_recent_result_for_ticker("TEST", exclude_run_id=run_id_2)
        assert prior is not None
        assert prior["run_id"] == run_id_1
        assert prior["purchase_count"] == 5


def test_get_all_runs():
    """Test retrieving all runs."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        # Save multiple runs
        run_id_1 = store.save_run(
            mode="test1", tickers_requested=1, tickers_resolved=1, lookback_days=365,
            max_form4_filings=0
        )

        run_id_2 = store.save_run(
            mode="test2", tickers_requested=2, tickers_resolved=2, lookback_days=730,
            max_form4_filings=0
        )

        # Get all runs
        runs = store.get_all_runs()
        assert len(runs) >= 2

        # Most recent should be first
        assert runs[0]["run_id"] == run_id_2
        assert runs[1]["run_id"] == run_id_1


def test_get_ticker_history():
    """Test retrieving history for a specific ticker."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        # Save multiple runs for same ticker
        for i in range(3):
            run_id = store.save_run(
                mode=f"test{i}",
                tickers_requested=1,
                tickers_resolved=1,
                lookback_days=365,
                max_form4_filings=0,
            )

            metrics = {
                "ticker": "TEST",
                "purchase_count": (i + 1) * 10,
                "purchase_value": (i + 1) * 10000.0,
                "sale_count": 0,
                "sale_value": 0.0,
                "net_purchase_value": (i + 1) * 10000.0,
            }

            store.save_ticker_result(run_id=run_id, ticker="TEST", metrics=metrics)

        # Get ticker history
        history = store.get_ticker_history("TEST")
        assert len(history) == 3

        # Most recent first
        assert history[0]["purchase_count"] == 30
        assert history[1]["purchase_count"] == 20
        assert history[2]["purchase_count"] == 10


def test_database_path_default():
    """Test that default database path is under .state/."""
    store = WatchlistHistoryStore()
    assert ".state" in str(store.db_path)
    assert "watchlist_history.db" in str(store.db_path)


def test_json_blob_storage():
    """Test that JSON blob is stored and retrieved correctly."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        run_id = store.save_run(
            mode="test", tickers_requested=1, tickers_resolved=1, lookback_days=365,
            max_form4_filings=0
        )

        metrics = {"ticker": "TEST", "purchase_count": 5}
        json_blob = {"full": "data", "nested": {"key": "value"}}

        store.save_ticker_result(
            run_id=run_id, ticker="TEST", metrics=metrics, json_blob=json_blob
        )

        # Retrieve and verify JSON blob
        result = store.get_most_recent_result_for_ticker("TEST")
        assert result["json_blob"] is not None

        import json
        parsed_blob = json.loads(result["json_blob"])
        assert parsed_blob["full"] == "data"
        assert parsed_blob["nested"]["key"] == "value"
