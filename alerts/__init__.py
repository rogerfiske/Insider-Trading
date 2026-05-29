"""
Insider-Trading alert delivery subsystem.

Provides email and Telegram delivery channels for consensus alerts,
plus routing policy, severity classification, and deduplication.
"""

from alerts.history import (
    check_duplicate,
    get_duplicate_count,
    get_recent_alerts,
    make_dedup_key,
    record_routing_decision,
)
from alerts.routing import (
    AlertClass,
    RoutingDecision,
    SeverityLevel,
    calculate_severity,
    determine_alert_class,
    make_routing_decision,
)
from alerts.smtp_email import send_email

__all__ = [
    "send_email",
    "SeverityLevel",
    "AlertClass",
    "RoutingDecision",
    "calculate_severity",
    "determine_alert_class",
    "make_routing_decision",
    "make_dedup_key",
    "check_duplicate",
    "record_routing_decision",
    "get_recent_alerts",
    "get_duplicate_count",
]
