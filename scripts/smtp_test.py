#!/usr/bin/env python3
"""
SMTP configuration checker and test email sender for Insider-Trading.

Usage:
  python scripts/smtp_test.py               # Check config only (dry-run)
  python scripts/smtp_test.py --send-test   # Send one controlled test email

Never prints SMTP_PASSWORD. Reports config status as SET/BLANK/MISSING.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def check_smtp_config() -> tuple[bool, list[str]]:
    """
    Check SMTP configuration completeness.

    Returns:
        (all_set, missing_keys): True if all required keys are set, plus list of missing keys
    """
    required_keys = [
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USE_SSL",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "ALERT_EMAIL_FROM",
        "ALERT_EMAIL_TO",
    ]

    print("Checking SMTP configuration...")
    print()

    missing = []
    for key in required_keys:
        val = os.environ.get(key)
        if val is None:
            status = "MISSING"
            missing.append(key)
        elif val.strip() == "":
            status = "BLANK"
            missing.append(key)
        else:
            status = f"SET (length: {len(val)})"

        # Never print SMTP_PASSWORD value
        if key == "SMTP_PASSWORD" and status.startswith("SET"):
            print(f"  {key}: SET (value redacted)")
        else:
            print(f"  {key}: {status}")

    print()

    if missing:
        print(f"[FAIL] {len(missing)} required key(s) missing or blank: {', '.join(missing)}")
        print()
        print("Please set these values in your local .env file before sending test email.")
        return False, missing

    print("[OK] All required SMTP keys are configured.")
    return True, []


def send_test_email() -> int:
    """
    Send one controlled test email via generic SMTP.

    Returns:
        Exit code: 0 on success, 1 on failure
    """
    # Import here so config check can run even if alerts module has issues
    try:
        from alerts.smtp_email import send_email
    except ImportError as exc:
        print(f"[FAIL] Failed to import alerts.smtp_email: {exc}")
        return 1

    subject = "Insider-Trading CP13B SMTP Test"
    body = (
        "Insider-Trading CP13B SMTP test: email delivery channel verified. "
        "Ross remains in dry-run mode."
    )

    print("Sending controlled test email...")
    print(f"  Subject: {subject}")
    print(f"  Body: {body[:50]}...")
    print()

    result = send_email(subject, body)

    if result["success"]:
        print("[OK] Test email sent successfully!")
        print()
        print(f"Sent from: {os.environ.get('ALERT_EMAIL_FROM')}")
        print(f"Sent to:   {os.environ.get('ALERT_EMAIL_TO')}")
        return 0

    print(f"[FAIL] Test email failed: {result['error']}")
    return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SMTP configuration checker and test email sender",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check SMTP config without sending email
  python scripts/smtp_test.py

  # Send one controlled test email
  python scripts/smtp_test.py --send-test
        """,
    )
    parser.add_argument(
        "--send-test",
        action="store_true",
        help="Send one controlled test email (requires explicit flag)",
    )

    args = parser.parse_args()

    # Always check config first
    all_set, missing = check_smtp_config()

    if not args.send_test:
        print()
        print("Config check complete. Use --send-test to send a test email.")
        return 0 if all_set else 1

    # --send-test requested
    if not all_set:
        print()
        print("Cannot send test email: SMTP configuration incomplete.")
        return 1

    print()
    return send_test_email()


if __name__ == "__main__":
    raise SystemExit(main())
