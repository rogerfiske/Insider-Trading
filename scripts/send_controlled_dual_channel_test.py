#!/usr/bin/env python3
"""CP22C - Controlled Dual-Channel Test Script

Sends exactly one controlled test email and exactly one controlled test
Telegram message for the same synthetic alert.

This script enforces all CP22C safety constraints:
1. Requires explicit --send-one-dual-channel-test flag
2. Refuses if ALERT_ENABLE_EMAIL=true (production email must stay disabled)
3. Refuses if recipient is not Roger's configured test address
4. Refuses if Telegram credentials are missing
5. Sends exactly one email
6. Sends exactly one Telegram message
7. Uses same synthetic content across both channels
8. Includes CP22C test markers
9. Does not call Ross production routing
10. Redacts passwords, tokens, chat IDs in error messages
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.common import send_telegram
from alerts.smtp_email import send_email


def check_preconditions() -> tuple[bool, str]:
    """Check all CP22C preconditions before sending.

    Returns:
        (passes, reason) tuple
    """
    # Check 1: ALERT_ENABLE_EMAIL must be false (production email disabled)
    email_enabled = os.environ.get("ALERT_ENABLE_EMAIL", "").lower() in ("true", "1", "yes")
    if email_enabled:
        return False, "ALERT_ENABLE_EMAIL is true — production email is enabled. CP22C requires production email to remain disabled."

    # Check 2: All SMTP credentials must be present
    smtp_host = os.environ.get("SMTP_HOST", "").strip()
    smtp_username = os.environ.get("SMTP_USERNAME", "").strip()
    smtp_password = os.environ.get("SMTP_PASSWORD", "").strip()
    smtp_from = os.environ.get("ALERT_EMAIL_FROM", "").strip()
    smtp_to = os.environ.get("ALERT_EMAIL_TO", "").strip()

    if not all([smtp_host, smtp_username, smtp_password, smtp_from, smtp_to]):
        return False, "Missing SMTP credentials. All SMTP settings must be configured."

    # Check 3: Recipient must be Roger's configured test address
    expected_recipient = "fiske1945@4securemail.com"
    if smtp_to != expected_recipient:
        return False, f"Recipient is '{smtp_to}' but expected '{expected_recipient}'. CP22C only sends to Roger's test address."

    # Check 4: Telegram credentials must be present
    telegram_bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not telegram_bot_token:
        return False, "TELEGRAM_BOT_TOKEN is missing. CP22C requires Telegram configuration."

    if not telegram_chat_id:
        return False, "TELEGRAM_CHAT_ID is missing. CP22C requires Telegram configuration."

    return True, "All preconditions met"


def send_controlled_dual_channel_test() -> int:
    """Send exactly one controlled email and one controlled Telegram message.

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    # Check preconditions
    passes, reason = check_preconditions()
    if not passes:
        print(f"[FAIL] Precondition check failed: {reason}")
        return 1

    print("\nChecking CP22C preconditions...")
    print(f"[OK] {reason}\n")

    # Prepare synthetic test content
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Email subject and body (per CP22C instruction lines 198-213)
    email_subject = "[INSIDER TEST] CP22C controlled dual-channel test"

    email_body = f"""CONTROLLED DUAL-CHANNEL TEST — CP22C

This is a one-time controlled dual-channel test.

Timestamp: {timestamp}

Production email alerts remain disabled.

One Telegram test message should also be sent.

Test symbol: MAIA (synthetic test data only)
Test action: ACTIONABLE BULLISH

No trade was placed.

Informational only. Not investment advice.
"""

    # Telegram message (per CP22C instruction lines 215-223)
    telegram_message = f"""CONTROLLED DUAL-CHANNEL TEST — CP22C

[INSIDER TEST] ACTIONABLE BULLISH on MAIA

Timestamp: {timestamp}

Production email alerts remain disabled.

One controlled email should also be sent.

Informational only. Not investment advice.
"""

    print(f"Sending CP22C controlled dual-channel test...")
    print(f"  Email Subject: {email_subject}")
    print(f"  Email Recipient: {os.environ.get('ALERT_EMAIL_TO', '')}")
    print(f"  Telegram Destination: [REDACTED]")
    print(f"  Timestamp: {timestamp}\n")

    # Send email
    try:
        email_result = send_email(email_subject, email_body)
    except Exception as exc:
        # Redact any potential secrets in error messages
        error_msg = str(exc)
        if os.environ.get("SMTP_PASSWORD"):
            error_msg = error_msg.replace(os.environ.get("SMTP_PASSWORD", ""), "[REDACTED]")
        print(f"[FAIL] Email send exception: {error_msg}")
        return 1

    if not email_result.get("success"):
        error_msg = email_result.get("error", "Unknown error")
        # Redact password in error message
        if os.environ.get("SMTP_PASSWORD"):
            error_msg = error_msg.replace(os.environ.get("SMTP_PASSWORD", ""), "[REDACTED]")
        print(f"[FAIL] Email send failed: {error_msg}")
        return 1

    print("[OK] Email sent successfully!")

    # Send Telegram (returns bool, not dict)
    try:
        telegram_result = send_telegram(telegram_message)
    except Exception as exc:
        # Redact any potential secrets in error messages
        error_msg = str(exc)
        if os.environ.get("TELEGRAM_BOT_TOKEN"):
            error_msg = error_msg.replace(os.environ.get("TELEGRAM_BOT_TOKEN", ""), "[REDACTED]")
        if os.environ.get("TELEGRAM_CHAT_ID"):
            error_msg = error_msg.replace(os.environ.get("TELEGRAM_CHAT_ID", ""), "[REDACTED]")
        print(f"[FAIL] Telegram send exception: {error_msg}")
        return 1

    if not telegram_result:
        # send_telegram returns False if dry-run, missing creds, or send failed
        print(f"[FAIL] Telegram send failed (returned False)")
        return 1

    print("[OK] Telegram message sent successfully!")
    print()
    print("[OK] CP22C controlled dual-channel test sent successfully!")
    print()
    print(f"Sent email to:      {os.environ.get('ALERT_EMAIL_TO', '')}")
    print(f"Sent Telegram to:   [REDACTED]")
    print()
    print("Next step: Roger should confirm receipt of both email and Telegram message.")

    return 0


def main() -> int:
    """Main entry point.

    Returns:
        Exit code
    """
    # Load .env
    env_file = Path(".env")
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()

    # Require explicit flag
    if "--send-one-dual-channel-test" not in sys.argv:
        print("[FAIL] Missing required flag: --send-one-dual-channel-test")
        print()
        print("CP22C controlled dual-channel test requires explicit confirmation.")
        print("This will send exactly one email and exactly one Telegram message.")
        print()
        print("Usage:")
        print("  python send_controlled_dual_channel_test.py --send-one-dual-channel-test")
        return 1

    return send_controlled_dual_channel_test()


if __name__ == "__main__":
    sys.exit(main())
