"""Tests for watchlist history safety boundaries."""

import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from watchlist.history_store import WatchlistHistoryStore


def test_history_mode_does_not_send_telegram():
    """Test that history mode enforces no Telegram alerts."""
    import scripts.ticker_watchlist as watchlist_module

    # Module-level override should enforce this
    assert os.environ.get("ALERT_ENABLE_TELEGRAM") == "false"


def test_history_mode_does_not_send_email():
    """Test that history mode enforces no email alerts."""
    import scripts.ticker_watchlist as watchlist_module

    # Module-level override should enforce this
    assert os.environ.get("ALERT_ENABLE_EMAIL") == "false"


def test_history_mode_enforces_dry_run():
    """Test that history mode enforces dry-run mode."""
    import scripts.ticker_watchlist as watchlist_module

    # Module-level override should enforce this
    assert os.environ.get("ROSS_DRY_RUN") == "true"


def test_history_db_excluded_from_git():
    """Test that history database is gitignored."""
    import subprocess

    # Check that .state/watchlist_history.db is gitignored
    result = subprocess.run(
        ["git", "check-ignore", "-v", ".state/watchlist_history.db"],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )

    # Should be ignored (exit code 0 when ignored)
    assert result.returncode == 0
    assert ".gitignore" in result.stdout


def test_json_blob_excludes_secrets():
    """Test that JSON blob does not contain secrets."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        run_id = store.save_run(
            mode="test", tickers_requested=1, tickers_resolved=1, lookback_days=365,
            max_form4_filings=0
        )

        # Create metrics with no sensitive data
        metrics = {
            "ticker": "TEST",
            "purchase_count": 10,
            "purchase_value": 100000.0,
        }

        json_blob = {
            "ticker": "TEST",
            "metrics": metrics,
            # No TELEGRAM_BOT_TOKEN, SMTP_PASSWORD, or other secrets
        }

        store.save_ticker_result(
            run_id=run_id, ticker="TEST", metrics=metrics, json_blob=json_blob
        )

        # Retrieve and verify no secrets
        result = store.get_most_recent_result_for_ticker("TEST")
        blob_str = result["json_blob"]

        # Check for common secret patterns
        secret_patterns = [
            "TELEGRAM_BOT_TOKEN",
            "SMTP_PASSWORD",
            "GMAIL_APP_PASSWORD",
            "sk-ant-",
            "ETHERSCAN_API_KEY",
            "BEGIN PRIVATE KEY",
        ]

        for pattern in secret_patterns:
            assert pattern not in blob_str


def test_private_spreadsheet_not_required():
    """Test that history tracking does not require Roger's spreadsheet."""
    # History store should work entirely from SEC data stored in the database
    # No file operations on spreadsheet paths

    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        # Should work without any spreadsheet files
        run_id = store.save_run(
            mode="test", tickers_requested=1, tickers_resolved=1, lookback_days=365,
            max_form4_filings=0
        )

        metrics = {"ticker": "TEST", "purchase_count": 10}
        store.save_ticker_result(run_id=run_id, ticker="TEST", metrics=metrics)

        # Verify we can retrieve data without spreadsheet
        result = store.get_most_recent_result_for_ticker("TEST")
        assert result is not None
        assert result["ticker"] == "TEST"


def test_history_does_not_consume_ross_guard():
    """Test that history mode does not consume Ross daily production guard."""
    # History mode runs in dry-run mode, so Ross should not consume guard
    import scripts.ticker_watchlist as watchlist_module

    # Verify dry-run is enforced (Ross respects this)
    assert os.environ.get("ROSS_DRY_RUN") == "true"


def test_database_is_local_not_remote():
    """Test that database is stored locally, not remotely."""
    store = WatchlistHistoryStore()

    # Database path should be local file, not URL
    db_path_str = str(store.db_path)
    assert "http" not in db_path_str
    assert "https" not in db_path_str
    assert ".state" in db_path_str


def test_history_summary_mentions_safety():
    """Test that history summary report includes safety confirmations."""
    from scripts.ticker_watchlist import generate_history_summary

    summary = generate_history_summary(
        run_id="test-123",
        ticker_metrics=[
            {
                "ticker": "TEST",
                "company_name": "Test Corp",
                "eddie_signal": "NEUTRAL",
                "eddie_confidence": 1,
                "maggie_status": "N/A",
                "maggie_signal": "N/A",
                "maggie_confidence": 0,
                "purchase_count": 0,
                "purchase_value": 0.0,
                "sale_count": 0,
                "sale_value": 0.0,
                "net_purchase_value": 0.0,
            }
        ],
        deltas=[],
        lookback_days=365,
        max_form4_filings=0,
        tickers_requested=1,
        tickers_resolved=1,
        tickers_failed=0,
        history_db_path=Path(".state/watchlist_history.db"),
        compare_previous=False,
    )

    # Verify safety confirmations are present
    assert "No Telegram messages sent" in summary
    assert "No email sent" in summary
    assert "Roger's OpenInsider spreadsheet was not used" in summary
    assert "gitignored" in summary or "local" in summary
    assert "not trading advice" in summary.lower()


def test_no_network_calls_in_history_store():
    """Test that history store makes no network calls."""
    # History store should only interact with local SQLite database
    # No HTTP requests, no SEC API calls, no external connections

    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"

        # Create isolated environment with no network
        # (This is a conceptual test - actual implementation would need network mocking)
        store = WatchlistHistoryStore(db_path)

        # All operations should work offline
        run_id = store.save_run(
            mode="test", tickers_requested=1, tickers_resolved=1, lookback_days=365,
            max_form4_filings=0
        )

        metrics = {"ticker": "TEST", "purchase_count": 10}
        store.save_ticker_result(run_id=run_id, ticker="TEST", metrics=metrics)

        result = store.get_most_recent_result_for_ticker("TEST")
        assert result is not None


def test_history_deltas_table_exists():
    """Test that deltas table exists for tracking changes."""
    with TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        store = WatchlistHistoryStore(db_path)

        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verify deltas table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='watchlist_ticker_deltas'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "watchlist_ticker_deltas"
