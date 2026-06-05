"""
Daily guard for Ross production alert runs.

Prevents multiple production alert runs per local calendar day.
Independent of alert deduplication (which is per-ticker+direction).

Storage: SQLite table `ross_daily_runs` in .state/state.db
Scope: Ross production alert runs only (dry-run doesn't consume guard)
Override: ROSS_FORCE_RUN=true environment variable
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

# -- Paths --------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".state"
DB_PATH = STATE / "state.db"


# -- Database initialization --------------------------------------------------


def _conn() -> sqlite3.Connection:
    """Open and initialize the ross_daily_runs table if needed."""
    STATE.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # Create ross_daily_runs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ross_daily_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_date TEXT NOT NULL UNIQUE,
            run_started_at TEXT NOT NULL,
            run_finished_at TEXT,
            status TEXT NOT NULL,
            alerts_sent_count INTEGER NOT NULL DEFAULT 0,
            trigger_source TEXT,
            dry_run INTEGER NOT NULL DEFAULT 1,
            exit_code INTEGER,
            error_message TEXT,
            override_reason TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            CONSTRAINT unique_local_date UNIQUE (local_date)
        )
    """)

    # Create index on local_date for fast lookups
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ross_daily_runs_local_date
        ON ross_daily_runs(local_date)
    """)

    # Create index on status for queries
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_ross_daily_runs_status
        ON ross_daily_runs(status)
    """)

    conn.commit()
    return conn


# -- Guard check logic --------------------------------------------------------


def should_bypass_guard() -> bool:
    """Check if manual override is enabled.

    Returns:
        bool: True if ROSS_FORCE_RUN=true, False otherwise
    """
    force_run = os.environ.get("ROSS_FORCE_RUN", "false").strip().lower()
    return force_run in ("true", "1", "yes")


def check_daily_guard() -> tuple[bool, str]:
    """Check if Ross production alerting already ran today.

    Returns:
        (should_run, reason):
            - (True, "No production run today") if guard allows run
            - (False, "Already ran today at HH:MM") if guard blocks run
    """
    # Get today's local date (Windows time zone)
    local_date = datetime.now().date().isoformat()  # "YYYY-MM-DD"

    conn = _conn()
    try:
        result = conn.execute(
            """
            SELECT run_started_at, status, alerts_sent_count
            FROM ross_daily_runs
            WHERE local_date = ?
            AND status IN ('completed', 'failed')
            AND dry_run = 0
            """,
            (local_date,),
        ).fetchone()

        if result:
            run_time = datetime.fromisoformat(result[0]).strftime("%H:%M")
            status = result[1]
            alerts = result[2]
            return (
                False,
                f"Production run already {status} today at {run_time} ({alerts} alert(s))",
            )
        else:
            return (True, "No production run today")
    finally:
        conn.close()


# -- Guard record logic -------------------------------------------------------


def record_daily_run(
    local_date: str,
    run_started_at: datetime,
    run_finished_at: datetime | None,
    status: str,
    alerts_sent_count: int,
    trigger_source: str,
    dry_run: bool,
    exit_code: int | None = None,
    error_message: str | None = None,
    override_reason: str | None = None,
) -> None:
    """Record Ross run in daily guard table.

    Args:
        local_date: Local calendar date (YYYY-MM-DD)
        run_started_at: Run start timestamp (UTC)
        run_finished_at: Run finish timestamp (UTC), None if crashed
        status: Run status ('started', 'completed', 'skipped_already_ran', 'failed', 'forced')
        alerts_sent_count: Number of alerts sent
        trigger_source: Trigger type ('logon', 'scheduled_08am', 'scheduled_18:30', 'manual', 'test')
        dry_run: True if dry-run mode, False if production
        exit_code: Ross process exit code
        error_message: Error details if failed
        override_reason: PM override justification if ROSS_FORCE_RUN=true
    """
    conn = _conn()
    try:
        conn.execute(
            """
            INSERT INTO ross_daily_runs (
                local_date, run_started_at, run_finished_at, status,
                alerts_sent_count, trigger_source, dry_run, exit_code,
                error_message, override_reason, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(local_date) DO UPDATE SET
                run_finished_at = excluded.run_finished_at,
                status = excluded.status,
                alerts_sent_count = excluded.alerts_sent_count,
                exit_code = excluded.exit_code,
                error_message = excluded.error_message,
                updated_at = excluded.updated_at
            """,
            (
                local_date,
                run_started_at.isoformat(),
                run_finished_at.isoformat() if run_finished_at else None,
                status,
                alerts_sent_count,
                trigger_source,
                1 if dry_run else 0,
                exit_code,
                error_message,
                override_reason,
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# -- Helper functions ---------------------------------------------------------


def detect_trigger_source() -> str:
    """Detect how Ross was triggered.

    Returns:
        str: Trigger source ('logon', 'scheduled_08am', 'scheduled_18:30', 'manual', 'unknown')
    """
    # Check if running under Windows Task Scheduler
    # Task Scheduler sets environment variables, but detection is heuristic
    # For now, return 'unknown' - can be refined based on timestamps or args
    return "unknown"


def get_recent_runs(days: int = 7) -> list[dict]:
    """Get recent Ross run records.

    Args:
        days: Number of days to look back

    Returns:
        list[dict]: Recent run records, most recent first
    """
    conn = _conn()
    try:
        cursor = conn.execute(
            """
            SELECT
                local_date,
                run_started_at,
                run_finished_at,
                status,
                alerts_sent_count,
                trigger_source,
                dry_run,
                exit_code
            FROM ross_daily_runs
            WHERE local_date >= date('now', 'localtime', ? || ' days')
            ORDER BY local_date DESC
            """,
            (f"-{days}",),
        )
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()
