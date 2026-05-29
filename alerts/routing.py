"""
Alert routing policy implementation for Insider-Trading.

Implements the CP14 alert routing policy:
- Severity levels: INFO, WATCH, ACTIONABLE, URGENT
- Alert classes: LOG_ONLY, TELEGRAM_ONLY, EMAIL_ONLY, TELEGRAM_AND_EMAIL, SUPPRESS_DUPLICATE
- Routing decisions based on scout count and aggregate confidence
- Channel enablement checks
- Dry-run mode support

All decisions are made in memory. No network calls.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.common import ConsensusEvent, Signal


# -- Severity levels ----------------------------------------------------------


class SeverityLevel(str, Enum):
    """Alert severity levels based on scout count and aggregate confidence."""

    INFO = "INFO"
    WATCH = "WATCH"
    ACTIONABLE = "ACTIONABLE"
    URGENT = "URGENT"


# -- Alert classes ------------------------------------------------------------


class AlertClass(str, Enum):
    """Alert delivery classes defining which channels receive the alert."""

    LOG_ONLY = "LOG_ONLY"  # Record only, no delivery
    TELEGRAM_ONLY = "TELEGRAM_ONLY"  # Telegram only
    EMAIL_ONLY = "EMAIL_ONLY"  # Email only
    TELEGRAM_AND_EMAIL = "TELEGRAM_AND_EMAIL"  # Both channels
    SUPPRESS_DUPLICATE = "SUPPRESS_DUPLICATE"  # Duplicate, suppress delivery


# -- Routing decision ---------------------------------------------------------


@dataclass
class RoutingDecision:
    """Complete routing decision for a consensus event."""

    consensus_id: int
    ticker: str
    direction: str
    severity: SeverityLevel
    alert_class: AlertClass
    should_send_telegram: bool
    should_send_email: bool
    is_duplicate: bool
    reason: str
    dedup_key: str
    dry_run: bool
    source_signal_ids: list[int]
    created_at: datetime


# -- Severity calculation -----------------------------------------------------


def calculate_severity(
    ev: ConsensusEvent, scout_signals: list[Signal]
) -> SeverityLevel:
    """Calculate severity level based on scout count and aggregate confidence.

    Algorithm:
    1. Scout count: 4+ scouts → URGENT, 3 scouts → ACTIONABLE, 2 scouts → WATCH, else → INFO
    2. Aggregate confidence (sum of all agreeing scouts' confidence):
       >=15 → URGENT, 12-14 → ACTIONABLE, 8-11 → WATCH, <8 → INFO
    3. Take maximum severity from both factors

    Args:
        ev: Consensus event with ticker, direction, scouts list
        scout_signals: List of Signal objects from agreeing scouts

    Returns:
        SeverityLevel: INFO, WATCH, ACTIONABLE, or URGENT
    """
    # Factor 1: Scout count
    scout_count = len(ev.scouts)
    if scout_count >= 4:
        scout_severity = SeverityLevel.URGENT
    elif scout_count == 3:
        scout_severity = SeverityLevel.ACTIONABLE
    elif scout_count == 2:
        scout_severity = SeverityLevel.WATCH
    else:
        scout_severity = SeverityLevel.INFO

    # Factor 2: Aggregate confidence
    # Match signals from agreeing scouts only
    matching_signals = [
        sig
        for sig in scout_signals
        if sig.scout in ev.scouts
        and sig.ticker == ev.ticker
        and sig.direction == ev.direction
    ]
    aggregate_confidence = sum(sig.confidence for sig in matching_signals)

    if aggregate_confidence >= 15:
        confidence_severity = SeverityLevel.URGENT
    elif aggregate_confidence >= 12:
        confidence_severity = SeverityLevel.ACTIONABLE
    elif aggregate_confidence >= 8:
        confidence_severity = SeverityLevel.WATCH
    else:
        confidence_severity = SeverityLevel.INFO

    # Take maximum severity
    severity_order = [
        SeverityLevel.INFO,
        SeverityLevel.WATCH,
        SeverityLevel.ACTIONABLE,
        SeverityLevel.URGENT,
    ]
    max_severity = max(
        scout_severity, confidence_severity, key=lambda s: severity_order.index(s)
    )

    return max_severity


# -- Alert class determination ------------------------------------------------


def determine_alert_class(
    severity: SeverityLevel,
    is_duplicate: bool,
    min_severity: SeverityLevel,
    telegram_enabled: bool,
    email_enabled: bool,
) -> AlertClass:
    """Determine alert class based on severity, deduplication, and channel policy.

    Routing policy (from CP14):
    - INFO → LOG_ONLY
    - WATCH → TELEGRAM_ONLY (if telegram enabled and meets min_severity)
    - ACTIONABLE → TELEGRAM_AND_EMAIL (if channels enabled and meets min_severity)
    - URGENT → TELEGRAM_AND_EMAIL (if channels enabled and meets min_severity)

    Args:
        severity: Calculated severity level
        is_duplicate: Whether this is a duplicate alert
        min_severity: Minimum severity threshold from ALERT_MIN_SEVERITY
        telegram_enabled: Whether Telegram delivery is enabled
        email_enabled: Whether email delivery is enabled

    Returns:
        AlertClass: Routing decision
    """
    # Suppress duplicates
    if is_duplicate:
        return AlertClass.SUPPRESS_DUPLICATE

    # Check minimum severity threshold
    severity_order = [
        SeverityLevel.INFO,
        SeverityLevel.WATCH,
        SeverityLevel.ACTIONABLE,
        SeverityLevel.URGENT,
    ]
    if severity_order.index(severity) < severity_order.index(min_severity):
        return AlertClass.LOG_ONLY

    # INFO always logs only
    if severity == SeverityLevel.INFO:
        return AlertClass.LOG_ONLY

    # WATCH → Telegram only
    if severity == SeverityLevel.WATCH:
        if telegram_enabled:
            return AlertClass.TELEGRAM_ONLY
        return AlertClass.LOG_ONLY

    # ACTIONABLE and URGENT → Both channels
    if severity in (SeverityLevel.ACTIONABLE, SeverityLevel.URGENT):
        if telegram_enabled and email_enabled:
            return AlertClass.TELEGRAM_AND_EMAIL
        elif telegram_enabled:
            return AlertClass.TELEGRAM_ONLY
        elif email_enabled:
            return AlertClass.EMAIL_ONLY
        return AlertClass.LOG_ONLY

    # Fallback
    return AlertClass.LOG_ONLY


# -- Routing decision ---------------------------------------------------------


def make_routing_decision(
    consensus_id: int,
    ev: ConsensusEvent,
    scout_signals: list[Signal],
    is_duplicate: bool,
    dedup_key: str,
) -> RoutingDecision:
    """Make a complete routing decision for a consensus event.

    Reads environment variables:
    - ROSS_DRY_RUN (default: true)
    - ALERT_ENABLE_TELEGRAM (default: false)
    - ALERT_ENABLE_EMAIL (default: false)
    - ALERT_MIN_SEVERITY (default: WATCH)

    Args:
        consensus_id: Database row ID of the consensus event
        ev: Consensus event to route
        scout_signals: List of Signal objects from the signal window
        is_duplicate: Whether deduplication detected a duplicate
        dedup_key: Deduplication key for history

    Returns:
        RoutingDecision: Complete routing decision with all fields populated
    """
    # Read environment configuration
    dry_run = os.environ.get("ROSS_DRY_RUN", "true").strip().lower() not in (
        "false",
        "0",
        "no",
    )
    telegram_enabled = (
        os.environ.get("ALERT_ENABLE_TELEGRAM", "false").strip().lower()
        in ("true", "1", "yes")
    )
    email_enabled = (
        os.environ.get("ALERT_ENABLE_EMAIL", "false").strip().lower()
        in ("true", "1", "yes")
    )
    min_severity_str = os.environ.get("ALERT_MIN_SEVERITY", "WATCH").strip().upper()
    try:
        min_severity = SeverityLevel(min_severity_str)
    except ValueError:
        min_severity = SeverityLevel.WATCH

    # Calculate severity
    severity = calculate_severity(ev, scout_signals)

    # Determine alert class
    alert_class = determine_alert_class(
        severity, is_duplicate, min_severity, telegram_enabled, email_enabled
    )

    # Determine channel delivery flags
    should_send_telegram = (
        alert_class in (AlertClass.TELEGRAM_ONLY, AlertClass.TELEGRAM_AND_EMAIL)
        and telegram_enabled
        and not dry_run
    )
    should_send_email = (
        alert_class in (AlertClass.EMAIL_ONLY, AlertClass.TELEGRAM_AND_EMAIL)
        and email_enabled
        and not dry_run
    )

    # Build reason
    if is_duplicate:
        reason = f"Duplicate: {dedup_key} within dedup window"
    elif alert_class == AlertClass.LOG_ONLY:
        reason = f"{severity.value}: Below threshold or no channels enabled"
    else:
        channels = []
        if should_send_telegram:
            channels.append("Telegram")
        if should_send_email:
            channels.append("email")
        if not channels:
            channels.append("dry-run only")
        reason = f"{severity.value}: {alert_class.value} → {', '.join(channels)}"

    # Extract signal IDs (placeholder - in real implementation, fetch from DB)
    source_signal_ids: list[int] = []

    return RoutingDecision(
        consensus_id=consensus_id,
        ticker=ev.ticker,
        direction=ev.direction,
        severity=severity,
        alert_class=alert_class,
        should_send_telegram=should_send_telegram,
        should_send_email=should_send_email,
        is_duplicate=is_duplicate,
        reason=reason,
        dedup_key=dedup_key,
        dry_run=dry_run,
        source_signal_ids=source_signal_ids,
        created_at=datetime.now(timezone.utc),
    )
