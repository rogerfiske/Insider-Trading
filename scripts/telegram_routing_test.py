#!/usr/bin/env python3
"""
Controlled one-shot Telegram routing test for CP16.

Sends exactly one test message to validate the alert routing layer.
Email is always disabled. This is not production live alert enablement.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alerts import (
    AlertClass,
    RoutingDecision,
    SeverityLevel,
    make_dedup_key,
    record_routing_decision,
)
from agents.common import send_telegram
from dotenv import load_dotenv


def create_test_routing_decision(send_once: bool) -> RoutingDecision:
    """Create a test routing decision for CP16."""
    # Use a non-ticker test symbol
    ticker = "CP16_TEST"
    direction = "SYSTEM_TEST"

    # Create deduplication key
    dedup_key = make_dedup_key(ticker, direction, hours=24)

    # Create routing decision with WATCH severity, Telegram-only
    decision = RoutingDecision(
        consensus_id=0,  # Test event, no consensus ID
        ticker=ticker,
        direction=direction,
        severity=SeverityLevel.WATCH,
        alert_class=AlertClass.TELEGRAM_ONLY,
        should_send_telegram=send_once,  # Only true when --send-once
        should_send_email=False,  # Always false for CP16
        is_duplicate=False,
        reason="CP16 controlled Telegram routing test",
        dedup_key=dedup_key,
        dry_run=not send_once,  # Dry-run unless --send-once
        source_signal_ids=[],
        created_at=datetime.now(timezone.utc),
    )

    return decision


def send_test_message(send_once: bool) -> tuple[bool, str | None]:
    """
    Send test Telegram message if send_once=True.

    Returns:
        tuple: (success, message_id or error)
    """
    # Load environment variables
    load_dotenv()

    # Override ROSS_DRY_RUN for this one-shot test if --send-once
    if send_once:
        os.environ["ROSS_DRY_RUN"] = "false"

    # Check required Telegram credentials
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token:
        return False, "TELEGRAM_BOT_TOKEN not set"
    if not chat_id:
        return False, "TELEGRAM_CHAT_ID not set"

    # CP16 approved test message
    test_message = (
        "*[CP16 SYSTEM TEST]*\n\n"
        "Insider-Trading CP16 Telegram routing test: "
        "controlled live Telegram-only alert verified.\n\n"
        "No trading signal. Email disabled."
    )

    if not send_once:
        print("\n[DRY-RUN PREVIEW]")
        print("Would send test message via Telegram:")
        print(f"Chat ID: {chat_id[:8]}...")
        print(f"Message: {test_message[:80]}...")
        return True, "dry_run_preview"

    # Send actual test message
    print("\n[LIVE TELEGRAM SEND]")
    print("Sending CP16 test message...")

    try:
        result = send_telegram(test_message)
        if result:
            print("[SUCCESS] Test message sent")
            return True, "sent"
        else:
            print("[FAILED] send_telegram returned False")
            return False, "send_failed"
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return False, str(exc)


def main() -> int:
    """Main entry point for CP16 controlled test."""
    parser = argparse.ArgumentParser(
        description="CP16 controlled Telegram routing test"
    )
    parser.add_argument(
        "--send-once",
        action="store_true",
        help="Send exactly one live Telegram test message (default: dry-run preview)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CP16 Controlled Telegram Routing Test")
    print("=" * 60)

    # Create test routing decision
    decision = create_test_routing_decision(send_once=args.send_once)

    print(f"\nRouting Decision:")
    print(f"  Ticker: {decision.ticker}")
    print(f"  Direction: {decision.direction}")
    print(f"  Severity: {decision.severity.value}")
    print(f"  Alert Class: {decision.alert_class.value}")
    print(f"  Should Send Telegram: {decision.should_send_telegram}")
    print(f"  Should Send Email: {decision.should_send_email}")
    print(f"  Dry-Run: {decision.dry_run}")
    print(f"  Dedup Key: {decision.dedup_key}")

    # Send test message
    success, result = send_test_message(send_once=args.send_once)

    # Record audit entry
    status = "sent" if success and args.send_once else "dry_run"
    error_msg = None if success else result

    try:
        record_routing_decision(
            decision,
            email_status="disabled",
            telegram_status=status,
            error_message=error_msg,
        )
        print(f"\n[AUDIT] Routing decision recorded: {status}")
    except Exception as exc:
        print(f"\n[WARNING] Failed to record audit: {exc}")

    # Summary
    print("\n" + "=" * 60)
    if args.send_once:
        if success:
            print("CP16 TEST COMPLETED: One Telegram message sent")
            print("Email: disabled (as required)")
        else:
            print(f"CP16 TEST FAILED: {result}")
            return 1
    else:
        print("CP16 DRY-RUN PREVIEW: No message sent")
        print("Run with --send-once to send test message")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
