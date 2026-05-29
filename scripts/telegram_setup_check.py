#!/usr/bin/env python3
"""Telegram setup check -- obtain chat ID via getUpdates API.

This helper validates the Telegram bot token and obtains the chat ID
from the most recent message sent to the bot. It updates .env with
TELEGRAM_CHAT_ID if found.

Requirements:
  - TELEGRAM_BOT_TOKEN must be set in .env
  - User must have sent at least one message to the bot

Security:
  - Never prints the bot token
  - Only writes the chat ID to .env (not logged or printed)
  - Uses HTTPS for all API calls
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Load .env
env_path = Path(".env")
if not env_path.exists():
    print("ERROR: .env not found")
    sys.exit(1)

env_vars = {}
for line in env_path.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    if "=" in line:
        key, value = line.split("=", 1)
        env_vars[key.strip()] = value.strip()

bot_token = env_vars.get("TELEGRAM_BOT_TOKEN", "")
if not bot_token:
    print("ERROR: TELEGRAM_BOT_TOKEN is not set in .env")
    print("Please add your bot token from @BotFather to .env")
    sys.exit(1)

# Call Telegram API getUpdates
url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
req = urllib.request.Request(url)
req.add_header("Accept", "application/json")

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
except (urllib.error.URLError, urllib.error.HTTPError) as e:
    print(f"ERROR: Failed to call Telegram API: {e}")
    sys.exit(1)

try:
    data = json.loads(body)
except json.JSONDecodeError:
    print("ERROR: Invalid JSON response from Telegram API")
    sys.exit(1)

if not data.get("ok"):
    print(f"ERROR: Telegram API returned error: {data.get('description', 'Unknown')}")
    sys.exit(1)

updates = data.get("result", [])
if not updates:
    print("ERROR: No updates found")
    print("Please send a message to your bot in Telegram (e.g., 'hello'), then rerun this script")
    sys.exit(1)

# Extract chat ID from most recent message
latest = updates[-1]
chat_id = None

if "message" in latest:
    chat_id = latest["message"].get("chat", {}).get("id")
elif "my_chat_member" in latest:
    chat_id = latest["my_chat_member"].get("chat", {}).get("id")

if not chat_id:
    print("ERROR: Could not extract chat ID from updates")
    sys.exit(1)

# Update .env with chat ID
env_lines = env_path.read_text(encoding="utf-8").splitlines()
updated = False
for i, line in enumerate(env_lines):
    if line.strip().startswith("TELEGRAM_CHAT_ID="):
        env_lines[i] = f"TELEGRAM_CHAT_ID={chat_id}"
        updated = True
        break

if not updated:
    # Key not found, append it
    env_lines.append(f"TELEGRAM_CHAT_ID={chat_id}")

env_path.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

print(f"SUCCESS: Chat ID obtained and saved to .env")
print(f"Chat ID: {chat_id}")
sys.exit(0)
