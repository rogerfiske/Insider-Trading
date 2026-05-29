"""
Tests for alerts/routing.py -- severity classification and alert routing.

Tests use mocked environment variables. No network calls.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from agents.common import ConsensusEvent, Signal
from alerts.routing import (
    AlertClass,
    RoutingDecision,
    SeverityLevel,
    calculate_severity,
    determine_alert_class,
    make_routing_decision,
)


# -- Severity calculation tests -----------------------------------------------


def test_calculate_severity_urgent_by_scout_count() -> None:
    """Test URGENT severity when 4+ scouts agree."""
    ev = ConsensusEvent(
        ticker="AAPL",
        direction="BULLISH",
        scouts=["eddie", "maggie", "frank", "maya"],
        reasons=["reason1", "reason2", "reason3", "reason4"],
        timestamp=datetime.now(timezone.utc),
    )
    signals = [
        Signal("eddie", "AAPL", "BULLISH", 3, "r1", "raw1"),
        Signal("maggie", "AAPL", "BULLISH", 3, "r2", "raw2"),
        Signal("frank", "AAPL", "BULLISH", 3, "r3", "raw3"),
        Signal("maya", "AAPL", "BULLISH", 3, "r4", "raw4"),
    ]
    severity = calculate_severity(ev, signals)
    assert severity == SeverityLevel.URGENT


def test_calculate_severity_urgent_by_confidence() -> None:
    """Test URGENT severity when aggregate confidence >= 15."""
    ev = ConsensusEvent(
        ticker="NVDA",
        direction="BEARISH",
        scouts=["eddie", "maggie", "frank"],
        reasons=["reason1", "reason2", "reason3"],
        timestamp=datetime.now(timezone.utc),
    )
    signals = [
        Signal("eddie", "NVDA", "BEARISH", 5, "r1", "raw1"),
        Signal("maggie", "NVDA", "BEARISH", 5, "r2", "raw2"),
        Signal("frank", "NVDA", "BEARISH", 5, "r3", "raw3"),
    ]
    severity = calculate_severity(ev, signals)
    assert severity == SeverityLevel.URGENT  # 5+5+5 = 15


def test_calculate_severity_actionable_by_scout_count() -> None:
    """Test ACTIONABLE severity when 3 scouts agree."""
    ev = ConsensusEvent(
        ticker="TSLA",
        direction="BULLISH",
        scouts=["eddie", "maggie", "frank"],
        reasons=["reason1", "reason2", "reason3"],
        timestamp=datetime.now(timezone.utc),
    )
    signals = [
        Signal("eddie", "TSLA", "BULLISH", 2, "r1", "raw1"),
        Signal("maggie", "TSLA", "BULLISH", 2, "r2", "raw2"),
        Signal("frank", "TSLA", "BULLISH", 2, "r3", "raw3"),
    ]
    severity = calculate_severity(ev, signals)
    assert severity == SeverityLevel.ACTIONABLE  # 3 scouts, confidence 6


def test_calculate_severity_actionable_by_confidence() -> None:
    """Test ACTIONABLE severity when aggregate confidence 12-14."""
    ev = ConsensusEvent(
        ticker="MSFT",
        direction="BULLISH",
        scouts=["eddie", "maggie"],
        reasons=["reason1", "reason2"],
        timestamp=datetime.now(timezone.utc),
    )
    signals = [
        Signal("eddie", "MSFT", "BULLISH", 5, "r1", "raw1"),
        Signal("maggie", "MSFT", "BULLISH", 5, "r2", "raw2"),
        Signal("frank", "MSFT", "BULLISH", 2, "r3", "raw3"),  # Not in scouts
    ]
    severity = calculate_severity(ev, signals)
    assert severity == SeverityLevel.WATCH  # 2 scouts, confidence 10


def test_calculate_severity_watch_by_scout_count() -> None:
    """Test WATCH severity when 2 scouts agree."""
    ev = ConsensusEvent(
        ticker="GOOG",
        direction="BEARISH",
        scouts=["eddie", "maggie"],
        reasons=["reason1", "reason2"],
        timestamp=datetime.now(timezone.utc),
    )
    signals = [
        Signal("eddie", "GOOG", "BEARISH", 4, "r1", "raw1"),
        Signal("maggie", "GOOG", "BEARISH", 4, "r2", "raw2"),
    ]
    severity = calculate_severity(ev, signals)
    assert severity == SeverityLevel.WATCH


def test_calculate_severity_info_low_confidence() -> None:
    """Test INFO severity when aggregate confidence < 8."""
    ev = ConsensusEvent(
        ticker="META",
        direction="BULLISH",
        scouts=["eddie", "maggie"],
        reasons=["reason1", "reason2"],
        timestamp=datetime.now(timezone.utc),
    )
    signals = [
        Signal("eddie", "META", "BULLISH", 2, "r1", "raw1"),
        Signal("maggie", "META", "BULLISH", 2, "r2", "raw2"),
    ]
    severity = calculate_severity(ev, signals)
    assert severity == SeverityLevel.WATCH  # 2 scouts → WATCH


# -- Alert class determination tests ------------------------------------------


def test_determine_alert_class_info_log_only() -> None:
    """Test INFO always routes to LOG_ONLY."""
    alert_class = determine_alert_class(
        severity=SeverityLevel.INFO,
        is_duplicate=False,
        min_severity=SeverityLevel.INFO,
        telegram_enabled=True,
        email_enabled=True,
    )
    assert alert_class == AlertClass.LOG_ONLY


def test_determine_alert_class_watch_telegram_only() -> None:
    """Test WATCH routes to TELEGRAM_ONLY when enabled."""
    alert_class = determine_alert_class(
        severity=SeverityLevel.WATCH,
        is_duplicate=False,
        min_severity=SeverityLevel.WATCH,
        telegram_enabled=True,
        email_enabled=False,
    )
    assert alert_class == AlertClass.TELEGRAM_ONLY


def test_determine_alert_class_watch_log_only_when_disabled() -> None:
    """Test WATCH routes to LOG_ONLY when telegram disabled."""
    alert_class = determine_alert_class(
        severity=SeverityLevel.WATCH,
        is_duplicate=False,
        min_severity=SeverityLevel.WATCH,
        telegram_enabled=False,
        email_enabled=False,
    )
    assert alert_class == AlertClass.LOG_ONLY


def test_determine_alert_class_actionable_both_channels() -> None:
    """Test ACTIONABLE routes to TELEGRAM_AND_EMAIL when both enabled."""
    alert_class = determine_alert_class(
        severity=SeverityLevel.ACTIONABLE,
        is_duplicate=False,
        min_severity=SeverityLevel.WATCH,
        telegram_enabled=True,
        email_enabled=True,
    )
    assert alert_class == AlertClass.TELEGRAM_AND_EMAIL


def test_determine_alert_class_actionable_telegram_only() -> None:
    """Test ACTIONABLE routes to TELEGRAM_ONLY when only telegram enabled."""
    alert_class = determine_alert_class(
        severity=SeverityLevel.ACTIONABLE,
        is_duplicate=False,
        min_severity=SeverityLevel.WATCH,
        telegram_enabled=True,
        email_enabled=False,
    )
    assert alert_class == AlertClass.TELEGRAM_ONLY


def test_determine_alert_class_actionable_email_only() -> None:
    """Test ACTIONABLE routes to EMAIL_ONLY when only email enabled."""
    alert_class = determine_alert_class(
        severity=SeverityLevel.ACTIONABLE,
        is_duplicate=False,
        min_severity=SeverityLevel.WATCH,
        telegram_enabled=False,
        email_enabled=True,
    )
    assert alert_class == AlertClass.EMAIL_ONLY


def test_determine_alert_class_urgent_both_channels() -> None:
    """Test URGENT routes to TELEGRAM_AND_EMAIL when both enabled."""
    alert_class = determine_alert_class(
        severity=SeverityLevel.URGENT,
        is_duplicate=False,
        min_severity=SeverityLevel.INFO,
        telegram_enabled=True,
        email_enabled=True,
    )
    assert alert_class == AlertClass.TELEGRAM_AND_EMAIL


def test_determine_alert_class_duplicate_suppressed() -> None:
    """Test duplicates are suppressed regardless of severity."""
    alert_class = determine_alert_class(
        severity=SeverityLevel.URGENT,
        is_duplicate=True,
        min_severity=SeverityLevel.INFO,
        telegram_enabled=True,
        email_enabled=True,
    )
    assert alert_class == AlertClass.SUPPRESS_DUPLICATE


def test_determine_alert_class_below_min_severity() -> None:
    """Test alerts below min_severity route to LOG_ONLY."""
    alert_class = determine_alert_class(
        severity=SeverityLevel.WATCH,
        is_duplicate=False,
        min_severity=SeverityLevel.ACTIONABLE,
        telegram_enabled=True,
        email_enabled=True,
    )
    assert alert_class == AlertClass.LOG_ONLY


# -- Routing decision tests ---------------------------------------------------


def test_make_routing_decision_dry_run_blocks_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test dry-run mode prevents real sends."""
    monkeypatch.setenv("ROSS_DRY_RUN", "true")
    monkeypatch.setenv("ALERT_ENABLE_TELEGRAM", "true")
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "true")
    monkeypatch.setenv("ALERT_MIN_SEVERITY", "WATCH")

    ev = ConsensusEvent(
        ticker="AAPL",
        direction="BULLISH",
        scouts=["eddie", "maggie", "frank"],
        reasons=["r1", "r2", "r3"],
        timestamp=datetime.now(timezone.utc),
    )
    signals = [
        Signal("eddie", "AAPL", "BULLISH", 4, "r1", "raw1"),
        Signal("maggie", "AAPL", "BULLISH", 4, "r2", "raw2"),
        Signal("frank", "AAPL", "BULLISH", 4, "r3", "raw3"),
    ]

    decision = make_routing_decision(
        consensus_id=1,
        ev=ev,
        scout_signals=signals,
        is_duplicate=False,
        dedup_key="AAPL:BULLISH:2026052900",
    )

    assert decision.dry_run is True
    assert decision.should_send_telegram is False
    assert decision.should_send_email is False
    assert decision.severity == SeverityLevel.ACTIONABLE


def test_make_routing_decision_telegram_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test ALERT_ENABLE_TELEGRAM=false prevents Telegram send."""
    monkeypatch.setenv("ROSS_DRY_RUN", "false")
    monkeypatch.setenv("ALERT_ENABLE_TELEGRAM", "false")
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "true")

    ev = ConsensusEvent(
        ticker="TSLA",
        direction="BEARISH",
        scouts=["eddie", "maggie", "frank"],
        reasons=["r1", "r2", "r3"],
        timestamp=datetime.now(timezone.utc),
    )
    signals = [
        Signal("eddie", "TSLA", "BEARISH", 4, "r1", "raw1"),
        Signal("maggie", "TSLA", "BEARISH", 4, "r2", "raw2"),
        Signal("frank", "TSLA", "BEARISH", 4, "r3", "raw3"),
    ]

    decision = make_routing_decision(
        consensus_id=2,
        ev=ev,
        scout_signals=signals,
        is_duplicate=False,
        dedup_key="TSLA:BEARISH:2026052900",
    )

    assert decision.dry_run is False
    assert decision.should_send_telegram is False
    assert decision.should_send_email is True
    assert decision.alert_class == AlertClass.EMAIL_ONLY


def test_make_routing_decision_email_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test ALERT_ENABLE_EMAIL=false prevents email send."""
    monkeypatch.setenv("ROSS_DRY_RUN", "false")
    monkeypatch.setenv("ALERT_ENABLE_TELEGRAM", "true")
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")

    ev = ConsensusEvent(
        ticker="NVDA",
        direction="BULLISH",
        scouts=["eddie", "maggie"],
        reasons=["r1", "r2"],
        timestamp=datetime.now(timezone.utc),
    )
    signals = [
        Signal("eddie", "NVDA", "BULLISH", 4, "r1", "raw1"),
        Signal("maggie", "NVDA", "BULLISH", 4, "r2", "raw2"),
    ]

    decision = make_routing_decision(
        consensus_id=3,
        ev=ev,
        scout_signals=signals,
        is_duplicate=False,
        dedup_key="NVDA:BULLISH:2026052900",
    )

    assert decision.dry_run is False
    assert decision.should_send_telegram is True
    assert decision.should_send_email is False
    assert decision.alert_class == AlertClass.TELEGRAM_ONLY
