"""Tests for CP22C controlled dual-channel test script."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.send_controlled_dual_channel_test import (
    check_preconditions,
    main,
    send_controlled_dual_channel_test,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_refuses_without_flag(monkeypatch: MonkeyPatch) -> None:
    """Test script refuses to run without explicit --send-one-dual-channel-test flag."""
    monkeypatch.setattr("sys.argv", ["send_controlled_dual_channel_test.py"])

    exit_code = main()

    assert exit_code == 1


def test_refuses_if_email_enabled(monkeypatch: MonkeyPatch) -> None:
    """Test script refuses if ALERT_ENABLE_EMAIL=true."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "true")
    monkeypatch.setenv("SMTP_HOST", "mail.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "test@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "test@example.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    passes, reason = check_preconditions()

    assert passes is False
    assert "production email is enabled" in reason.lower()


def test_refuses_if_smtp_credentials_missing(monkeypatch: MonkeyPatch) -> None:
    """Test script refuses if any SMTP credential is missing."""
    # Clear all SMTP env vars to ensure clean test
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_PORT", raising=False)
    monkeypatch.delenv("SMTP_USE_SSL", raising=False)
    monkeypatch.delenv("SMTP_USERNAME", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("ALERT_EMAIL_FROM", raising=False)
    monkeypatch.delenv("ALERT_EMAIL_TO", raising=False)

    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    passes, reason = check_preconditions()

    assert passes is False
    assert "missing smtp credentials" in reason.lower()


def test_refuses_unexpected_recipient(monkeypatch: MonkeyPatch) -> None:
    """Test script refuses if recipient is not Roger's configured test address."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "test@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "test@example.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "wrong@example.com")  # Wrong recipient
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    passes, reason = check_preconditions()

    assert passes is False
    assert "fiske1945@4securemail.com" in reason


def test_refuses_if_telegram_bot_token_missing(monkeypatch: MonkeyPatch) -> None:
    """Test script refuses if Telegram bot token is missing."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    passes, reason = check_preconditions()

    assert passes is False
    assert "TELEGRAM_BOT_TOKEN" in reason


def test_refuses_if_telegram_chat_id_missing(monkeypatch: MonkeyPatch) -> None:
    """Test script refuses if Telegram chat ID is missing."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    passes, reason = check_preconditions()

    assert passes is False
    assert "TELEGRAM_CHAT_ID" in reason


def test_preconditions_pass_when_all_set(monkeypatch: MonkeyPatch) -> None:
    """Test preconditions pass when all requirements are met."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    passes, reason = check_preconditions()

    assert passes is True
    assert "all preconditions met" in reason.lower()


def test_sends_exactly_one_email_and_one_telegram_when_allowed(monkeypatch: MonkeyPatch) -> None:
    """Test script sends exactly one email and one Telegram message when all preconditions pass."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    # Mock both send functions
    mock_send_email = MagicMock(return_value={"success": True})
    mock_send_telegram = MagicMock(return_value=True)

    with (
        patch("scripts.send_controlled_dual_channel_test.send_email", mock_send_email),
        patch("scripts.send_controlled_dual_channel_test.send_telegram", mock_send_telegram),
    ):
        exit_code = send_controlled_dual_channel_test()

    assert exit_code == 0
    assert mock_send_email.call_count == 1
    assert mock_send_telegram.call_count == 1


def test_email_subject_includes_test_marker(monkeypatch: MonkeyPatch) -> None:
    """Test email subject includes CP22C test marker."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    mock_send_email = MagicMock(return_value={"success": True})
    mock_send_telegram = MagicMock(return_value=True)

    with (
        patch("scripts.send_controlled_dual_channel_test.send_email", mock_send_email),
        patch("scripts.send_controlled_dual_channel_test.send_telegram", mock_send_telegram),
    ):
        send_controlled_dual_channel_test()

    # Check email call args
    email_call_args = mock_send_email.call_args
    email_subject = email_call_args[0][0]

    assert "[INSIDER TEST]" in email_subject
    assert "CP22C" in email_subject


def test_email_body_includes_controlled_test_markers(monkeypatch: MonkeyPatch) -> None:
    """Test email body includes all required CP22C test markers."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    mock_send_email = MagicMock(return_value={"success": True})
    mock_send_telegram = MagicMock(return_value=True)

    with (
        patch("scripts.send_controlled_dual_channel_test.send_email", mock_send_email),
        patch("scripts.send_controlled_dual_channel_test.send_telegram", mock_send_telegram),
    ):
        send_controlled_dual_channel_test()

    email_call_args = mock_send_email.call_args
    email_body = email_call_args[0][1]

    # Check all required markers per CP22C instruction lines 205-213
    assert "CONTROLLED DUAL-CHANNEL TEST" in email_body
    assert "CP22C" in email_body
    assert "one-time controlled dual-channel test" in email_body
    assert "Production email alerts remain disabled" in email_body
    assert "One Telegram test message should also be sent" in email_body
    assert "No trade was placed" in email_body
    assert "Informational only" in email_body
    assert "Not investment advice" in email_body


def test_telegram_body_includes_controlled_test_markers(monkeypatch: MonkeyPatch) -> None:
    """Test Telegram body includes all required CP22C test markers."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    mock_send_email = MagicMock(return_value={"success": True})
    mock_send_telegram = MagicMock(return_value=True)

    with (
        patch("scripts.send_controlled_dual_channel_test.send_email", mock_send_email),
        patch("scripts.send_controlled_dual_channel_test.send_telegram", mock_send_telegram),
    ):
        send_controlled_dual_channel_test()

    telegram_call_args = mock_send_telegram.call_args
    telegram_message = telegram_call_args[0][0]

    # Check all required markers per CP22C instruction lines 215-223
    assert "CONTROLLED DUAL-CHANNEL TEST" in telegram_message
    assert "CP22C" in telegram_message
    assert "[INSIDER TEST]" in telegram_message
    assert "ACTIONABLE BULLISH on MAIA" in telegram_message
    assert "Production email alerts remain disabled" in telegram_message
    assert "One controlled email should also be sent" in telegram_message
    assert "Informational only" in telegram_message
    assert "Not investment advice" in telegram_message


def test_does_not_call_ross_routing(monkeypatch: MonkeyPatch) -> None:
    """Test script does not call Ross production routing."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    mock_send_email = MagicMock(return_value={"success": True})
    mock_send_telegram = MagicMock(return_value=True)
    mock_make_routing_decision = MagicMock()

    with (
        patch("scripts.send_controlled_dual_channel_test.send_email", mock_send_email),
        patch("scripts.send_controlled_dual_channel_test.send_telegram", mock_send_telegram),
        patch("alerts.routing.make_routing_decision", mock_make_routing_decision),
    ):
        send_controlled_dual_channel_test()

    # Ross routing should never be called
    assert mock_make_routing_decision.call_count == 0


def test_redacts_smtp_password_in_error_output(monkeypatch: MonkeyPatch) -> None:
    """Test script redacts SMTP password in error messages."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    # Mock send_email to return failure with password in error message
    mock_send_email = MagicMock(
        return_value={"success": False, "error": "Auth failed with password secret123"}
    )

    with (
        patch("scripts.send_controlled_dual_channel_test.send_email", mock_send_email),
        patch("builtins.print") as mock_print,
    ):
        exit_code = send_controlled_dual_channel_test()

    assert exit_code == 1

    # Check that print was called with redacted error
    print_calls = [str(call) for call in mock_print.call_args_list]
    error_printed = any("secret123" not in str(call) and "[REDACTED]" in str(call) for call in print_calls)

    assert error_printed, "Password should be redacted in error output"


def test_redacts_telegram_credentials_in_error_output(monkeypatch: MonkeyPatch) -> None:
    """Test script redacts Telegram bot token and chat ID in error messages."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    # Mock successful email send but failed Telegram with credentials in error
    mock_send_email = MagicMock(return_value={"success": True})
    mock_send_telegram = MagicMock(return_value=False)

    with (
        patch("scripts.send_controlled_dual_channel_test.send_email", mock_send_email),
        patch("scripts.send_controlled_dual_channel_test.send_telegram", mock_send_telegram),
        patch("builtins.print") as mock_print,
    ):
        exit_code = send_controlled_dual_channel_test()

    assert exit_code == 1

    # Check that print was called with redacted error
    print_calls = [str(call) for call in mock_print.call_args_list]

    # Verify credentials are redacted
    error_printed = any("[REDACTED]" in str(call) for call in print_calls)
    no_token_leaked = all("test_token_123" not in str(call) for call in print_calls)
    no_chat_leaked = all("test_chat_456" not in str(call) for call in print_calls)

    assert error_printed, "Redacted message should be present"
    assert no_token_leaked, "Telegram bot token should be redacted in error output"
    assert no_chat_leaked, "Telegram chat ID should be redacted in error output"


def test_no_secrets_in_rendered_output(monkeypatch: MonkeyPatch) -> None:
    """Test email and Telegram messages do not contain any secrets."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_token_123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test_chat_456")

    mock_send_email = MagicMock(return_value={"success": True})
    mock_send_telegram = MagicMock(return_value=True)

    with (
        patch("scripts.send_controlled_dual_channel_test.send_email", mock_send_email),
        patch("scripts.send_controlled_dual_channel_test.send_telegram", mock_send_telegram),
    ):
        send_controlled_dual_channel_test()

    email_call_args = mock_send_email.call_args
    email_subject = email_call_args[0][0]
    email_body = email_call_args[0][1]

    telegram_call_args = mock_send_telegram.call_args
    telegram_message = telegram_call_args[0][0]

    # Check no secrets in email output
    assert "secret123" not in email_subject
    assert "secret123" not in email_body
    assert "SMTP_PASSWORD" not in email_body

    # Check no secrets in Telegram output
    assert "test_token_123" not in telegram_message
    assert "test_chat_456" not in telegram_message
    assert "TELEGRAM_BOT_TOKEN" not in telegram_message
    assert "TELEGRAM_CHAT_ID" not in telegram_message
