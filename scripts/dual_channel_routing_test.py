#!/usr/bin/env python3
"""
Controlled one-shot dual-channel routing test for CP17.

Sends exactly one Telegram message AND exactly one email to validate
the full dual-channel alert routing layer. This is not production
live alert enablement.
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
from agents.common import send_email, send_telegram
from dotenv import load_dotenv


def create_dual_channel_routing_decision(send_once: bool) -> RoutingDecision:
    """Create a dual-channel test routing decision for CP17."""
    # Use a non-ticker test symbol
    ticker = "CP17_TEST"
    direction = "SYSTEM_TEST"

    # Create deduplication key
    dedup_key = make_dedup_key(ticker, direction, hours=24)

    # Create routing decision with ACTIONABLE severity, TELEGRAM_AND_EMAIL
    decision = RoutingDecision(
        consensus_id=0,  # Test event, no consensus ID
        ticker=ticker,
        direction=direction,
        severity=SeverityLevel.ACTIONABLE,
        alert_class=AlertClass.TELEGRAM_AND_EMAIL,
        should_send_telegram=send_once,  # Only true when --send-once
        should_send_email=send_once,  # Only true when --send-once
        is_duplicate=False,
        reason="CP17 controlled dual-channel routing test",
        dedup_key=dedup_key,
        dry_run=not send_once,  # Dry-run unless --send-once
        source_signal_ids=[],
        created_at=datetime.now(timezone.utc),
    )

    return decision


def send_dual_channel_test(send_once: bool) -> tuple[bool, bool, dict]:
    """
    Send dual-channel test messages if send_once=True.

    Returns:
        tuple: (telegram_success, email_success, status_dict)
    """
    # Load environment variables
    load_dotenv()

    # Override ROSS_DRY_RUN for this one-shot test if --send-once
    if send_once:
        os.environ["ROSS_DRY_RUN"] = "false"

    # Check required Telegram credentials
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Check required SMTP credentials
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_from = os.getenv("ALERT_EMAIL_FROM")
    email_to = os.getenv("ALERT_EMAIL_TO")

    # Verify all credentials
    missing_creds = []
    if not bot_token:
        missing_creds.append("TELEGRAM_BOT_TOKEN")
    if not chat_id:
        missing_creds.append("TELEGRAM_CHAT_ID")
    if not smtp_host:
        missing_creds.append("SMTP_HOST")
    if not smtp_port:
        missing_creds.append("SMTP_PORT")
    if not smtp_username:
        missing_creds.append("SMTP_USERNAME")
    if not smtp_password:
        missing_creds.append("SMTP_PASSWORD")
    if not email_from:
        missing_creds.append("ALERT_EMAIL_FROM")
    if not email_to:
        missing_creds.append("ALERT_EMAIL_TO")

    if missing_creds:
        return False, False, {
            "error": f"Missing credentials: {', '.join(missing_creds)}"
        }

    # CP17 approved test messages
    telegram_text = (
        "*[CP17 SYSTEM TEST]*\n\n"
        "Insider-Trading CP17 dual-channel routing test: "
        "controlled live Telegram + email alert verified.\n\n"
        "No trading signal. Production alerts remain disabled."
    )

    email_subject = "Insider-Trading CP17 Dual-Channel Alert Test"
    email_body = (
        "CP17 SYSTEM TEST\n\n"
        "Insider-Trading CP17 dual-channel routing test: "
        "controlled live Telegram + email alert verified.\n\n"
        "No trading signal. Production alerts remain disabled.\n\n"
        "This is a controlled test of the dual-channel alert routing layer. "
        "Production live alerts are not yet enabled."
    )

    if not send_once:
        print("\n[DRY-RUN PREVIEW]")
        print("Would send dual-channel test messages:")
        print(f"\nTelegram:")
        print(f"  Chat ID: {chat_id[:8]}...")
        print(f"  Message: {telegram_text[:80]}...")
        print(f"\nEmail:")
        print(f"  From: {email_from}")
        print(f"  To: {email_to}")
        print(f"  Subject: {email_subject}")
        print(f"  Body: {email_body[:80]}...")
        return True, True, {"status": "dry_run_preview"}

    # Send actual dual-channel test
    print("\n[LIVE DUAL-CHANNEL SEND]")

    # Send Telegram
    print("Sending Telegram test message...")
    telegram_success = False
    telegram_error = None
    try:
        telegram_result = send_telegram(telegram_text)
        if telegram_result:
            print("[SUCCESS] Telegram message sent")
            telegram_success = True
        else:
            print("[FAILED] send_telegram returned False")
            telegram_error = "send_telegram returned False"
    except Exception as exc:
        print(f"[ERROR] Telegram send failed: {exc}")
        telegram_error = str(exc)

    # Send Email
    print("Sending email test message...")
    email_success = False
    email_error = None
    try:
        send_email(email_subject, email_body)
        print("[SUCCESS] Email sent")
        email_success = True
    except Exception as exc:
        print(f"[ERROR] Email send failed: {exc}")
        email_error = str(exc)

    return telegram_success, email_success, {
        "telegram_error": telegram_error,
        "email_error": email_error,
    }


def main() -> int:
    """Main entry point for CP17 dual-channel test."""
    parser = argparse.ArgumentParser(
        description="CP17 controlled dual-channel routing test"
    )
    parser.add_argument(
        "--send-once",
        action="store_true",
        help="Send exactly one Telegram + email test message (default: dry-run preview)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CP17 Controlled Dual-Channel Routing Test")
    print("=" * 60)

    # Create dual-channel routing decision
    decision = create_dual_channel_routing_decision(send_once=args.send_once)

    print(f"\nRouting Decision:")
    print(f"  Ticker: {decision.ticker}")
    print(f"  Direction: {decision.direction}")
    print(f"  Severity: {decision.severity.value}")
    print(f"  Alert Class: {decision.alert_class.value}")
    print(f"  Should Send Telegram: {decision.should_send_telegram}")
    print(f"  Should Send Email: {decision.should_send_email}")
    print(f"  Dry-Run: {decision.dry_run}")
    print(f"  Dedup Key: {decision.dedup_key}")

    # Send dual-channel test
    telegram_success, email_success, status = send_dual_channel_test(
        send_once=args.send_once
    )

    # Record audit entry
    if args.send_once:
        telegram_status = "sent" if telegram_success else "failed"
        email_status = "sent" if email_success else "failed"
    else:
        telegram_status = "dry_run"
        email_status = "dry_run"

    error_msg = None
    if not telegram_success and args.send_once:
        error_msg = status.get("telegram_error", "unknown")
    elif not email_success and args.send_once:
        if error_msg:
            error_msg += f"; {status.get('email_error', 'unknown')}"
        else:
            error_msg = status.get("email_error", "unknown")

    try:
        record_routing_decision(
            decision,
            email_status=email_status,
            telegram_status=telegram_status,
            error_message=error_msg,
        )
        print(f"\n[AUDIT] Routing decision recorded")
    except Exception as exc:
        print(f"\n[WARNING] Failed to record audit: {exc}")

    # Summary
    print("\n" + "=" * 60)
    if args.send_once:
        if telegram_success and email_success:
            print("CP17 TEST COMPLETED: Dual-channel delivery successful")
            print("  Telegram: sent [OK]")
            print("  Email: sent [OK]")
        else:
            print("CP17 TEST FAILED:")
            if not telegram_success:
                print(f"  Telegram: failed ({status.get('telegram_error', 'unknown')})")
            else:
                print("  Telegram: sent [OK]")
            if not email_success:
                print(f"  Email: failed ({status.get('email_error', 'unknown')})")
            else:
                print("  Email: sent [OK]")
            print("=" * 60)
            return 1
    else:
        print("CP17 DRY-RUN PREVIEW: No messages sent")
        print("Run with --send-once to send test messages")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
