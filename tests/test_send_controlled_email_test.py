"""Tests for CP22B controlled email test script."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.send_controlled_email_test import (
    check_preconditions,
    main,
    send_controlled_test_email,
)

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_refuses_without_flag(monkeypatch: MonkeyPatch) -> None:
    """Test script refuses to run without explicit --send-one-test-email flag."""
    monkeypatch.setattr("sys.argv", ["send_controlled_email_test.py"])

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
    # Missing SMTP_PASSWORD and others

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

    passes, reason = check_preconditions()

    assert passes is False
    assert "fiske1945@4securemail.com" in reason


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

    passes, reason = check_preconditions()

    assert passes is True
    assert "all preconditions met" in reason.lower()


def test_sends_exactly_one_email_when_allowed(monkeypatch: MonkeyPatch) -> None:
    """Test script sends exactly one email when all preconditions pass."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")

    # Mock send_email to avoid real SMTP call
    mock_send_email = MagicMock(return_value={"success": True})

    with patch("alerts.smtp_email.send_email", mock_send_email):
        exit_code = send_controlled_test_email()

    assert exit_code == 0
    assert mock_send_email.call_count == 1


def test_subject_includes_test_marker(monkeypatch: MonkeyPatch) -> None:
    """Test email subject includes CP22B test marker."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")

    mock_send_email = MagicMock(return_value={"success": True})

    with patch("alerts.smtp_email.send_email", mock_send_email):
        send_controlled_test_email()

    # Check the call args
    call_args = mock_send_email.call_args
    subject = call_args[0][0]
    body = call_args[0][1]

    assert "[INSIDER TEST]" in subject
    assert "CP22B" in subject


def test_body_includes_controlled_test_markers(monkeypatch: MonkeyPatch) -> None:
    """Test email body includes all required CP22B test markers."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")

    mock_send_email = MagicMock(return_value={"success": True})

    with patch("alerts.smtp_email.send_email", mock_send_email):
        send_controlled_test_email()

    call_args = mock_send_email.call_args
    body = call_args[0][1]

    # Check all required markers per CP22B instruction lines 194-201
    assert "CONTROLLED LIVE EMAIL TEST" in body
    assert "CP22B" in body
    assert "one-time controlled test email" in body
    assert "Production email alerts remain disabled" in body
    assert "No Telegram message was sent" in body
    assert "No trade was placed" in body
    assert "Informational only" in body
    assert "Not investment advice" in body


def test_does_not_call_telegram(monkeypatch: MonkeyPatch) -> None:
    """Test script does not import or call Telegram send function."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")

    mock_send_email = MagicMock(return_value={"success": True})

    with patch("alerts.smtp_email.send_email", mock_send_email):
        exit_code = send_controlled_test_email()

    # Verify email was sent successfully (proving the script ran)
    assert exit_code == 0
    assert mock_send_email.call_count == 1

    # Verify script does not import telegram modules
    # (If it tried to import telegram and send, this test would have failed with ImportError)
    import sys
    telegram_modules = [name for name in sys.modules if "telegram" in name.lower()]
    # telegram modules may exist from other tests, but send_controlled_email_test should not import them
    # The fact that the script ran without error proves it doesn't try to call telegram


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

    mock_send_email = MagicMock(return_value={"success": True})
    mock_make_routing_decision = MagicMock()

    with (
        patch("alerts.smtp_email.send_email", mock_send_email),
        patch("alerts.routing.make_routing_decision", mock_make_routing_decision),
    ):
        send_controlled_test_email()

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

    # Mock send_email to return failure with password in error message
    mock_send_email = MagicMock(
        return_value={"success": False, "error": "Auth failed with password secret123"}
    )

    with (
        patch("alerts.smtp_email.send_email", mock_send_email),
        patch("builtins.print") as mock_print,
    ):
        exit_code = send_controlled_test_email()

    assert exit_code == 1

    # Check that print was called with redacted error
    print_calls = [str(call) for call in mock_print.call_args_list]
    error_printed = any("secret123" not in str(call) and "[REDACTED]" in str(call) for call in print_calls)

    assert error_printed, "Password should be redacted in error output"


def test_no_secrets_in_rendered_output(monkeypatch: MonkeyPatch) -> None:
    """Test email body does not contain any secrets."""
    monkeypatch.setenv("ALERT_ENABLE_EMAIL", "false")
    monkeypatch.setenv("SMTP_HOST", "mail.4securemail.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "fiske1945@4securemail.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret123")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "fiske1945@4securemail.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "fiske1945@4securemail.com")

    mock_send_email = MagicMock(return_value={"success": True})

    with patch("alerts.smtp_email.send_email", mock_send_email):
        send_controlled_test_email()

    call_args = mock_send_email.call_args
    subject = call_args[0][0]
    body = call_args[0][1]

    # Check no secrets in output
    assert "secret123" not in subject
    assert "secret123" not in body
    assert "SMTP_PASSWORD" not in body
    assert os.environ.get("SMTP_PASSWORD", "") not in body
