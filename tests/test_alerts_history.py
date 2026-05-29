"""
Tests for alerts/history.py -- deduplication and audit storage.

Tests use temporary SQLite databases. No secrets stored.
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.common import ConsensusEvent, Signal
from alerts.history import (
    check_duplicate,
    get_duplicate_count,
    get_recent_alerts,
    make_dedup_key,
    record_routing_decision,
)
from alerts.routing import AlertClass, RoutingDecision, SeverityLevel


@pytest.fixture
def temp_db(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_state.db"
        # Patch the DB_PATH in alerts.history
        monkeypatch.setattr("alerts.history.DB_PATH", db_path)
        monkeypatch.setattr("alerts.history.STATE", Path(tmpdir))
        yield db_path


# -- Deduplication tests ------------------------------------------------------


def test_make_dedup_key_format() -> None:
    """Test dedup key format is TICKER:DIRECTION:YYYYMMDDHH."""
    key = make_dedup_key("AAPL", "BULLISH", hours=24)
    parts = key.split(":")
    assert len(parts) == 3
    assert parts[0] == "AAPL"
    assert parts[1] == "BULLISH"
    assert len(parts[2]) == 10  # YYYYMMDDHH


def test_make_dedup_key_uppercase() -> None:
    """Test dedup key uppercases ticker and direction."""
    key = make_dedup_key("aapl", "bullish", hours=24)
    assert key.startswith("AAPL:BULLISH:")


def test_check_duplicate_no_history(temp_db: Path) -> None:
    """Test check_duplicate returns False when no history."""
    is_dup = check_duplicate("AAPL:BULLISH:2026052900", hours=24)
    assert is_dup is False


def test_check_duplicate_within_window(temp_db: Path) -> None:
    """Test check_duplicate returns True for duplicate within window."""
    # Create a test routing decision and record it
    decision = RoutingDecision(
        consensus_id=1,
        ticker="TSLA",
        direction="BEARISH",
        severity=SeverityLevel.ACTIONABLE,
        alert_class=AlertClass.TELEGRAM_AND_EMAIL,
        should_send_telegram=False,
        should_send_email=False,
        is_duplicate=False,
        reason="test",
        dedup_key="TSLA:BEARISH:2026052900",
        dry_run=True,
        source_signal_ids=[],
        created_at=datetime.now(timezone.utc),
    )
    record_routing_decision(decision)

    # Check duplicate with same key
    is_dup = check_duplicate("TSLA:BEARISH:2026052900", hours=24)
    assert is_dup is True


def test_check_duplicate_outside_window(temp_db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test check_duplicate returns False for old duplicates outside window."""
    # Record a decision
    decision = RoutingDecision(
        consensus_id=1,
        ticker="NVDA",
        direction="BULLISH",
        severity=SeverityLevel.WATCH,
        alert_class=AlertClass.TELEGRAM_ONLY,
        should_send_telegram=False,
        should_send_email=False,
        is_duplicate=False,
        reason="test",
        dedup_key="NVDA:BULLISH:2026052900",
        dry_run=True,
        source_signal_ids=[],
        created_at=datetime.now(timezone.utc),
    )
    record_routing_decision(decision)

    # Check with very short window (should be outside)
    is_dup = check_duplicate("NVDA:BULLISH:2026052900", hours=0)
    assert is_dup is False


def test_check_duplicate_ignores_suppressed(temp_db: Path) -> None:
    """Test check_duplicate ignores already-suppressed duplicates."""
    # Record a suppressed duplicate
    decision = RoutingDecision(
        consensus_id=1,
        ticker="MSFT",
        direction="BULLISH",
        severity=SeverityLevel.INFO,
        alert_class=AlertClass.SUPPRESS_DUPLICATE,
        should_send_telegram=False,
        should_send_email=False,
        is_duplicate=True,
        reason="duplicate",
        dedup_key="MSFT:BULLISH:2026052900",
        dry_run=True,
        source_signal_ids=[],
        created_at=datetime.now(timezone.utc),
    )
    record_routing_decision(decision)

    # Check should return False because the first record was a duplicate
    is_dup = check_duplicate("MSFT:BULLISH:2026052900", hours=24)
    assert is_dup is False


# -- Audit storage tests ------------------------------------------------------


def test_record_routing_decision_basic(temp_db: Path) -> None:
    """Test recording a routing decision."""
    decision = RoutingDecision(
        consensus_id=1,
        ticker="AAPL",
        direction="BULLISH",
        severity=SeverityLevel.ACTIONABLE,
        alert_class=AlertClass.TELEGRAM_AND_EMAIL,
        should_send_telegram=True,
        should_send_email=True,
        is_duplicate=False,
        reason="3 scouts agree, confidence 12",
        dedup_key="AAPL:BULLISH:2026052900",
        dry_run=False,
        source_signal_ids=[1, 2, 3],
        created_at=datetime.now(timezone.utc),
    )

    row_id = record_routing_decision(
        decision, email_status="sent", telegram_status="sent"
    )
    assert row_id > 0


def test_record_routing_decision_no_secrets(temp_db: Path) -> None:
    """Test routing decision does not contain secrets."""
    decision = RoutingDecision(
        consensus_id=1,
        ticker="TSLA",
        direction="BEARISH",
        severity=SeverityLevel.URGENT,
        alert_class=AlertClass.TELEGRAM_AND_EMAIL,
        should_send_telegram=True,
        should_send_email=True,
        is_duplicate=False,
        reason="urgent",
        dedup_key="TSLA:BEARISH:2026052900",
        dry_run=False,
        source_signal_ids=[],
        created_at=datetime.now(timezone.utc),
    )

    row_id = record_routing_decision(decision)

    # Retrieve and verify no secrets
    import sqlite3

    conn = sqlite3.connect(temp_db)
    row = conn.execute(
        "SELECT decision_json FROM alert_history WHERE id = ?", (row_id,)
    ).fetchone()
    conn.close()

    decision_json = row[0]
    # Verify common secret patterns are not in JSON
    assert "SMTP_PASSWORD" not in decision_json
    assert "TELEGRAM_BOT_TOKEN" not in decision_json
    assert "ANTHROPIC_API_KEY" not in decision_json


def test_get_recent_alerts_empty(temp_db: Path) -> None:
    """Test get_recent_alerts returns empty list when no history."""
    alerts = get_recent_alerts(hours=24, limit=100)
    assert len(alerts) == 0


def test_get_recent_alerts_basic(temp_db: Path) -> None:
    """Test get_recent_alerts returns recorded alerts."""
    decision = RoutingDecision(
        consensus_id=1,
        ticker="GOOG",
        direction="BULLISH",
        severity=SeverityLevel.WATCH,
        alert_class=AlertClass.TELEGRAM_ONLY,
        should_send_telegram=True,
        should_send_email=False,
        is_duplicate=False,
        reason="watch level",
        dedup_key="GOOG:BULLISH:2026052900",
        dry_run=True,
        source_signal_ids=[],
        created_at=datetime.now(timezone.utc),
    )
    record_routing_decision(decision)

    alerts = get_recent_alerts(hours=24, limit=100)
    assert len(alerts) == 1
    assert alerts[0]["ticker"] == "GOOG"
    assert alerts[0]["direction"] == "BULLISH"
    assert alerts[0]["severity"] == "WATCH"
    assert alerts[0]["alert_class"] == "TELEGRAM_ONLY"


def test_get_recent_alerts_limit(temp_db: Path) -> None:
    """Test get_recent_alerts respects limit."""
    for i in range(5):
        decision = RoutingDecision(
            consensus_id=i + 1,
            ticker=f"TICK{i}",
            direction="BULLISH",
            severity=SeverityLevel.INFO,
            alert_class=AlertClass.LOG_ONLY,
            should_send_telegram=False,
            should_send_email=False,
            is_duplicate=False,
            reason="info",
            dedup_key=f"TICK{i}:BULLISH:2026052900",
            dry_run=True,
            source_signal_ids=[],
            created_at=datetime.now(timezone.utc),
        )
        record_routing_decision(decision)

    alerts = get_recent_alerts(hours=24, limit=3)
    assert len(alerts) == 3


def test_get_duplicate_count_zero(temp_db: Path) -> None:
    """Test get_duplicate_count returns 0 when no history."""
    count = get_duplicate_count("AAPL", "BULLISH", hours=24)
    assert count == 0


def test_get_duplicate_count_basic(temp_db: Path) -> None:
    """Test get_duplicate_count counts non-duplicate alerts."""
    # Record 2 non-duplicate alerts
    for i in range(2):
        decision = RoutingDecision(
            consensus_id=i + 1,
            ticker="META",
            direction="BEARISH",
            severity=SeverityLevel.ACTIONABLE,
            alert_class=AlertClass.TELEGRAM_AND_EMAIL,
            should_send_telegram=False,
            should_send_email=False,
            is_duplicate=False,
            reason="actionable",
            dedup_key=f"META:BEARISH:202605290{i}",
            dry_run=True,
            source_signal_ids=[],
            created_at=datetime.now(timezone.utc),
        )
        record_routing_decision(decision)

    count = get_duplicate_count("META", "BEARISH", hours=24)
    assert count == 2


def test_get_duplicate_count_ignores_duplicates(temp_db: Path) -> None:
    """Test get_duplicate_count ignores suppressed duplicates."""
    # Record 1 non-duplicate
    decision1 = RoutingDecision(
        consensus_id=1,
        ticker="AMZN",
        direction="BULLISH",
        severity=SeverityLevel.URGENT,
        alert_class=AlertClass.TELEGRAM_AND_EMAIL,
        should_send_telegram=False,
        should_send_email=False,
        is_duplicate=False,
        reason="urgent",
        dedup_key="AMZN:BULLISH:2026052900",
        dry_run=True,
        source_signal_ids=[],
        created_at=datetime.now(timezone.utc),
    )
    record_routing_decision(decision1)

    # Record 1 suppressed duplicate
    decision2 = RoutingDecision(
        consensus_id=2,
        ticker="AMZN",
        direction="BULLISH",
        severity=SeverityLevel.URGENT,
        alert_class=AlertClass.SUPPRESS_DUPLICATE,
        should_send_telegram=False,
        should_send_email=False,
        is_duplicate=True,
        reason="duplicate",
        dedup_key="AMZN:BULLISH:2026052900",
        dry_run=True,
        source_signal_ids=[],
        created_at=datetime.now(timezone.utc),
    )
    record_routing_decision(decision2)

    # Count should be 1 (ignoring the duplicate)
    count = get_duplicate_count("AMZN", "BULLISH", hours=24)
    assert count == 1
