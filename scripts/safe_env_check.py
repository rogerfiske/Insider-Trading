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
smtp_creds_present = (
    check_string_env("SMTP_HOST") and
    check_string_env("SMTP_PORT") and
    check_string_env("SMTP_USERNAME") and
    check_string_env("SMTP_PASSWORD")
)

# Report (safe)
print("ALERT_ENABLE_EMAIL present:", "yes" if email_present else "no")
print("ALERT_ENABLE_EMAIL enabled:", email_enabled)
print()
print("ALERT_ENABLE_TELEGRAM present:", "yes" if telegram_present else "no")
print("ALERT_ENABLE_TELEGRAM enabled:", telegram_enabled)
print()
print("SMTP credentials present:", "yes" if smtp_creds_present else "no")
