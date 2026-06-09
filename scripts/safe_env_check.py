#!/usr/bin/env python3
"""Safe .env configuration checker - only reports boolean presence, not values."""
import os
from pathlib import Path

# Load .env if it exists
env_file = Path(".env")
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv()

# Check key presence and boolean values (never print actual secrets)
def check_bool_env(key: str) -> tuple[bool, bool]:
    """Returns (present, enabled) tuple"""
    value = os.environ.get(key)
    if value is None:
        return (False, False)
    return (True, value.lower() in ("true", "1", "yes"))

# Check string presence
def check_string_env(key: str) -> bool:
    """Returns True if key is present and non-empty"""
    value = os.environ.get(key)
    return bool(value and len(value) > 0)

# Email configuration
email_present, email_enabled = check_bool_env("ALERT_ENABLE_EMAIL")
telegram_present, telegram_enabled = check_bool_env("ALERT_ENABLE_TELEGRAM")

# SMTP credentials (check presence only, never print values)
smtp_host_present = check_string_env("SMTP_HOST")
smtp_port_present = check_string_env("SMTP_PORT")
smtp_username_present = check_string_env("SMTP_USERNAME")
smtp_password_present = check_string_env("SMTP_PASSWORD")
smtp_from_present = check_string_env("ALERT_EMAIL_FROM")
smtp_to_present = check_string_env("ALERT_EMAIL_TO")

smtp_creds_present = (
    smtp_host_present and
    smtp_port_present and
    smtp_username_present and
    smtp_password_present and
    smtp_from_present and
    smtp_to_present
)

# Telegram credentials (check presence only, never print values)
telegram_bot_token_present = check_string_env("TELEGRAM_BOT_TOKEN")
telegram_chat_id_present = check_string_env("TELEGRAM_CHAT_ID")

telegram_creds_present = telegram_bot_token_present and telegram_chat_id_present

# Check recipient (safe to show email address for Roger's known test account)
recipient = os.environ.get("ALERT_EMAIL_TO", "").strip()
expected_recipient = "fiske1945@4securemail.com"
recipient_is_roger = recipient == expected_recipient

# Report (safe)
print("ALERT_ENABLE_EMAIL present:", "yes" if email_present else "no")
print("ALERT_ENABLE_EMAIL enabled:", email_enabled)
print()
print("ALERT_ENABLE_TELEGRAM present:", "yes" if telegram_present else "no")
print("ALERT_ENABLE_TELEGRAM enabled:", telegram_enabled)
print()
print("SMTP host present:", "yes" if smtp_host_present else "no")
print("SMTP username present:", "yes" if smtp_username_present else "no")
print("SMTP password present:", "yes" if smtp_password_present else "no")
print("SMTP recipient present:", "yes" if smtp_to_present else "no")
print()
if smtp_to_present:
    print(f"Recipient: {recipient}")
    print(f"Expected: {expected_recipient}")
    print(f"Recipient is Roger:", "yes" if recipient_is_roger else "no")
else:
    print("Recipient: [not configured]")
print()
print("Telegram bot token present:", "yes" if telegram_bot_token_present else "no")
print("Telegram chat ID present:", "yes" if telegram_chat_id_present else "no")
