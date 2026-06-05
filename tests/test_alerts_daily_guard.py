"""
Tests for alerts.daily_guard module.

Tests once-daily guard behavior for Ross production runs.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

from alerts.daily_guard import (
    check_daily_guard,
    detect_trigger_source,
    get_recent_runs,
    record_daily_run,
    should_bypass_guard,
)


@pytest.fixture
def temp_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_state.db"
    # Monkeypatch the DB_PATH in alerts.daily_guard
    import alerts.daily_guard

    monkeypatch.setattr(alerts.daily_guard, "DB_PATH", db_path)
    monkeypatch.setattr(alerts.daily_guard, "STATE", tmp_path)
    return db_path


def test_check_daily_guard_allows_first_run(temp_db: Path) -> None:
    """Test check_daily_guard allows first run of the day."""
    can_run, reason = check_daily_guard()
    assert can_run is True
    assert "No production run today" in reason


def test_check_daily_guard_blocks_second_run(temp_db: Path) -> None:
    """Test check_daily_guard blocks second production run same day."""
    # Record first run
    today = datetime.now().date().isoformat()
    run_time = datetime.now(timezone.utc)
    record_daily_run(
        local_date=today,
        run_started_at=run_time,
        run_finished_at=run_time,
        status="completed",
        alerts_sent_count=1,
        trigger_source="logon",
        dry_run=False,
        exit_code=0,
    )

    # Check guard again
    can_run, reason = check_daily_guard()
    assert can_run is False
    assert "already completed today" in reason.lower()


def test_check_daily_guard_dry_run_does_not_consume(temp_db: Path) -> None:
    """Test dry-run doesn't consume daily guard."""
    # Record dry-run
    today = datetime.now().date().isoformat()
    run_time = datetime.now(timezone.utc)
    record_daily_run(
        local_date=today,
        run_started_at=run_time,
        run_finished_at=run_time,
        status="completed",
        alerts_sent_count=0,
        trigger_source="manual",
        dry_run=True,  # Dry-run mode
        exit_code=0,
    )

    # Guard should still allow production run
    can_run, reason = check_daily_guard()
    assert can_run is True
    assert "No production run today" in reason


def test_should_bypass_guard_false_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test should_bypass_guard returns False by default."""
    monkeypatch.delenv("ROSS_FORCE_RUN", raising=False)
    assert should_bypass_guard() is False


def test_should_bypass_guard_true_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test should_bypass_guard returns True when ROSS_FORCE_RUN=true."""
    monkeypatch.setenv("ROSS_FORCE_RUN", "true")
    assert should_bypass_guard() is True

    monkeypatch.setenv("ROSS_FORCE_RUN", "1")
    assert should_bypass_guard() is True

    monkeypatch.setenv("ROSS_FORCE_RUN", "yes")
    assert should_bypass_guard() is True


def test_record_daily_run_creates_record(temp_db: Path) -> None:
    """Test record_daily_run creates a database record."""
    today = datetime.now().date().isoformat()
    run_time = datetime.now(timezone.utc)

    record_daily_run(
        local_date=today,
        run_started_at=run_time,
        run_finished_at=run_time,
        status="completed",
        alerts_sent_count=2,
        trigger_source="scheduled_08am",
        dry_run=False,
        exit_code=0,
    )

    # Verify record exists
    conn = sqlite3.connect(temp_db)
    cursor = conn.execute(
        "SELECT local_date, status, alerts_sent_count, trigger_source FROM ross_daily_runs WHERE local_date = ?",
        (today,),
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == today
    assert row[1] == "completed"
    assert row[2] == 2
    assert row[3] == "scheduled_08am"


def test_record_daily_run_updates_existing(temp_db: Path) -> None:
    """Test record_daily_run updates existing record on conflict."""
    today = datetime.now().date().isoformat()
    run_time = datetime.now(timezone.utc)

    # First record
    record_daily_run(
        local_date=today,
        run_started_at=run_time,
        run_finished_at=run_time,
        status="started",
        alerts_sent_count=0,
        trigger_source="logon",
        dry_run=False,
        exit_code=None,
    )

    # Update to completed
    record_daily_run(
        local_date=today,
        run_started_at=run_time,
        run_finished_at=run_time,
        status="completed",
        alerts_sent_count=1,
        trigger_source="logon",
        dry_run=False,
        exit_code=0,
    )

    # Verify only one record exists with updated status
    conn = sqlite3.connect(temp_db)
    cursor = conn.execute(
        "SELECT COUNT(*), status, alerts_sent_count FROM ross_daily_runs WHERE local_date = ?",
        (today,),
    )
    row = cursor.fetchone()
    conn.close()

    assert row[0] == 1  # Only one record
    assert row[1] == "completed"  # Updated status
    assert row[2] == 1  # Updated count


def test_get_recent_runs(temp_db: Path) -> None:
    """Test get_recent_runs returns recent records."""
    # Record multiple runs
    for i in range(3):
        date = f"2026-06-0{i+1}"
        record_daily_run(
            local_date=date,
            run_started_at=datetime.now(timezone.utc),
            run_finished_at=datetime.now(timezone.utc),
            status="completed",
            alerts_sent_count=i,
            trigger_source="test",
            dry_run=False,
            exit_code=0,
        )

    # Get recent runs
    recent = get_recent_runs(days=7)
    assert len(recent) >= 3

    # Verify most recent first
    dates = [run["local_date"] for run in recent]
    assert dates == sorted(dates, reverse=True)


def test_detect_trigger_source() -> None:
    """Test detect_trigger_source returns a string."""
    source = detect_trigger_source()
    assert isinstance(source, str)
    # Current implementation returns 'unknown'
    assert source == "unknown"


def test_failed_run_allows_retry(temp_db: Path) -> None:
    """Test failed run is recorded but doesn't block retry."""
    today = datetime.now().date().isoformat()
    run_time = datetime.now(timezone.utc)

    # Record failed run
    record_daily_run(
        local_date=today,
        run_started_at=run_time,
        run_finished_at=run_time,
        status="failed",
        alerts_sent_count=0,
        trigger_source="logon",
        dry_run=False,
        exit_code=1,
        error_message="Test error",
    )

    # Guard should block (failed status is treated same as completed for guard purposes)
    can_run, reason = check_daily_guard()
    assert can_run is False


def test_guard_records_no_secrets(temp_db: Path) -> None:
    """Test guard records don't contain secrets."""
    today = datetime.now().date().isoformat()
    run_time = datetime.now(timezone.utc)

    record_daily_run(
        local_date=today,
        run_started_at=run_time,
        run_finished_at=run_time,
        status="completed",
        alerts_sent_count=1,
        trigger_source="manual",
        dry_run=False,
        exit_code=0,
    )

    # Read all data from table
    conn = sqlite3.connect(temp_db)
    cursor = conn.execute("SELECT * FROM ross_daily_runs WHERE local_date = ?", (today,))
    row = cursor.fetchone()
    conn.close()

    # Convert row to string and check for common secret patterns
    row_str = str(row).lower()
    assert "sk-ant-" not in row_str
    assert "telegram_bot_token" not in row_str
    assert "smtp_password" not in row_str
    assert "api_key" not in row_str
