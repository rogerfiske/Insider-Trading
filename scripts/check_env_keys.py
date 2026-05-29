#!/usr/bin/env python3
"""Check .env keys without printing sensitive values."""
import os
from pathlib import Path

def check_env_keys():
    """Check required .env keys and report status."""
    env_path = Path(".env")

    if not env_path.exists():
        print(".env file not found")
        return

    keys_to_check = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "ALERT_ENABLE_TELEGRAM",
        "ALERT_ENABLE_EMAIL",
        "ROSS_DRY_RUN",
    ]

    with open(env_path, "r") as f:
        content = f.read()

    for key in keys_to_check:
        found = False
        for line in content.splitlines():
            if line.strip().startswith(key + "="):
                value = line.split("=", 1)[1].strip()
                if value:
                    print(f"{key}=SET")
                else:
                    print(f"{key}=BLANK")
                found = True
                break
        if not found:
            print(f"{key}=MISSING")

if __name__ == "__main__":
    check_env_keys()
