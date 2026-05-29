"""
Alert history and deduplication for Insider-Trading.

Implements time-bucketed deduplication and audit storage:
- alert_history table in SQLite state DB
- Deduplication keys: (ticker, direction, time_bucket)
- ALERT_DEDUP_HOURS window (default 24 hours)
- Full audit trail of all routing decisions

No secrets are stored. All storage is local in .state/state.db.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alerts.routing import RoutingDecision

# -- Paths --------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".state"
DB_PATH = STATE / "state.db"


# -- Database initialization --------------------------------------------------


def _conn() -> sqlite3.Connection:
    """Open and initialize the alert_history table if needed."""
    STATE.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # Create alert_history table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consensus_id INTEGER NOT NULL,
            dedup_key TEXT NOT NULL,
            ticker TEXT NOT NULL,
            direction TEXT NOT NULL,
            severity TEXT NOT NULL,
            alert_class TEXT NOT NULL,
            should_send_telegram INTEGER NOT NULL,
            should_send_email INTEGER NOT NULL,
            is_duplicate INTEGER NOT NULL,
            reason TEXT NOT NULL,
            dry_run INTEGER NOT NULL,
            email_status TEXT,
            telegram_status TEXT,
            error_message TEXT,
            decision_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (consensus_id) REFERENCES consensus(id)
        )
    """)

    # Create index on dedup_key for fast duplicate lookups
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_alert_history_dedup
        ON alert_history(dedup_key, created_at)
    """)

    # Create index on created_at for time-based queries
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_alert_history_created_at
        ON alert_history(created_at)
    """)

    conn.commit()
    return conn


# -- Deduplication ------------------------------------------------------------


def make_dedup_key(ticker: str, direction: str, hours: int = 24) -> str:
    """Create a time-bucketed deduplication key.

    The key includes ticker, direction, and a time bucket. Alerts with the same
    ticker+direction in the same time bucket are considered duplicates.

    Args:
        ticker: Stock ticker or asset symbol
        direction: BULLISH or BEARISH
        hours: Deduplication window in hours (default 24)

    Returns:
        str: Deduplication key in format "TICKER:DIRECTION:YYYYMMDDHH"
    """
    now = datetime.now(timezone.utc)
    # Round down to nearest hour bucket
    bucket_start = now.replace(minute=0, second=0, microsecond=0)
    # Create bucket ID spanning the dedup window
    bucket_id = bucket_start.strftime("%Y%m%d%H")
    return f"{ticker.upper()}:{direction.upper()}:{bucket_id}"


def check_duplicate(dedup_key: str, hours: int = 24) -> bool:
    """Check if a dedup_key was alerted within the last N hours.

    Args:
        dedup_key: Deduplication key from make_dedup_key()
        hours: Deduplication window in hours (default 24)

    Returns:
        bool: True if duplicate found, False otherwise
    """
    dedup_hours = int(os.environ.get("ALERT_DEDUP_HOURS", str(hours)))
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=dedup_hours)).isoformat()

    conn = _conn()
    try:
        result = conn.execute(
            """
            SELECT COUNT(*) FROM alert_history
            WHERE dedup_key = ?
            AND created_at >= ?
            AND is_duplicate = 0
            """,
            (dedup_key, cutoff),
        ).fetchone()
        return (result[0] if result else 0) > 0
    finally:
        conn.close()


# -- Audit storage ------------------------------------------------------------


def record_routing_decision(
    decision: RoutingDecision,
    email_status: str | None = None,
    telegram_status: str | None = None,
    error_message: str | None = None,
) -> int:
    """Record a routing decision to the audit trail.

    Stores the complete routing decision for audit and deduplication.
    No secrets are stored.

    Args:
        decision: RoutingDecision object from make_routing_decision()
        email_status: Optional email delivery status (e.g., "sent", "failed", "skipped")
        telegram_status: Optional Telegram delivery status
        error_message: Optional error message if delivery failed

    Returns:
        int: Database row ID of the recorded audit entry
    """
    # Convert decision to JSON (excluding sensitive data)
    decision_dict = asdict(decision)
    decision_json = json.dumps(decision_dict, default=str)

    conn = _conn()
    try:
        cursor = conn.execute(
            """
            INSERT INTO alert_history (
                consensus_id, dedup_key, ticker, direction,
                severity, alert_class, should_send_telegram, should_send_email,
                is_duplicate, reason, dry_run,
                email_status, telegram_status, error_message,
                decision_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision.consensus_id,
                decision.dedup_key,
                decision.ticker,
                decision.direction,
                decision.severity.value,
                decision.alert_class.value,
                1 if decision.should_send_telegram else 0,
                1 if decision.should_send_email else 0,
                1 if decision.is_duplicate else 0,
                decision.reason,
                1 if decision.dry_run else 0,
                email_status,
                telegram_status,
                error_message,
                decision_json,
                decision.created_at.isoformat(),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid or 0)
    finally:
        conn.close()


def get_recent_alerts(hours: int = 24, limit: int = 100) -> list[dict]:
    """Retrieve recent alert history for inspection.

    Args:
        hours: Look back this many hours (default 24)
        limit: Maximum number of records to return (default 100)

    Returns:
        list[dict]: List of alert history records as dictionaries
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    conn = _conn()
    try:
        rows = conn.execute(
            """
            SELECT
                id, consensus_id, dedup_key, ticker, direction,
                severity, alert_class, should_send_telegram, should_send_email,
                is_duplicate, reason, dry_run,
                email_status, telegram_status, error_message, created_at
            FROM alert_history
            WHERE created_at >= ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (cutoff, limit),
        ).fetchall()

        return [
            {
                "id": r[0],
                "consensus_id": r[1],
                "dedup_key": r[2],
                "ticker": r[3],
                "direction": r[4],
                "severity": r[5],
                "alert_class": r[6],
                "should_send_telegram": bool(r[7]),
                "should_send_email": bool(r[8]),
                "is_duplicate": bool(r[9]),
                "reason": r[10],
                "dry_run": bool(r[11]),
                "email_status": r[12],
                "telegram_status": r[13],
                "error_message": r[14],
                "created_at": r[15],
            }
            for r in rows
        ]
    finally:
        conn.close()


def get_duplicate_count(ticker: str, direction: str, hours: int = 24) -> int:
    """Count how many times a ticker+direction was alerted in the last N hours.

    Args:
        ticker: Stock ticker or asset symbol
        direction: BULLISH or BEARISH
        hours: Look back this many hours (default 24)

    Returns:
        int: Number of alerts (excluding duplicates) in the time window
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    conn = _conn()
    try:
        result = conn.execute(
            """
            SELECT COUNT(*) FROM alert_history
            WHERE ticker = ?
            AND direction = ?
            AND created_at >= ?
            AND is_duplicate = 0
            """,
            (ticker.upper(), direction.upper(), cutoff),
        ).fetchone()
        return result[0] if result else 0
    finally:
        conn.close()
