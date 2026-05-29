"""
Tests for alerts/smtp_email.py -- generic SMTP email delivery.

Tests use mocked SMTP connections. No real network calls.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from alerts.smtp_email import send_email

if TYPE_CHECKING:
    from alerts.smtp_email import SendResult


@pytest.fixture
def smtp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up valid SMTP environment variables for tests."""
    monkeypatch.setenv("SMTP_HOST", "mail.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "test_password_12345")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "alerts@example.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "recipient@example.com")


def test_send_email_ssl_success(smtp_env: None) -> None:
    """Test successful email send via SSL (port 465)."""
    with patch("alerts.smtp_email.smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        result = send_email("Test Subject", "Test body content")

        assert result["success"] is True
        assert result["error"] is None

        # Verify SMTP_SSL was called with correct host and port
        mock_smtp_ssl.assert_called_once_with("mail.example.com", 465, timeout=30)

        # Verify login and send were called
        mock_server.login.assert_called_once_with("user@example.com", "test_password_12345")
        mock_server.send_message.assert_called_once()


def test_send_email_starttls_success(smtp_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test successful email send via STARTTLS (port 587)."""
    monkeypatch.setenv("SMTP_USE_SSL", "false")
    monkeypatch.setenv("SMTP_PORT", "587")

    with patch("alerts.smtp_email.smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = send_email("Test Subject", "Test body content")

        assert result["success"] is True
        assert result["error"] is None

        # Verify SMTP was called (not SMTP_SSL)
        mock_smtp.assert_called_once_with("mail.example.com", 587, timeout=30)

        # Verify STARTTLS was called
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()


def test_send_email_missing_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing SMTP_HOST raises ValueError."""
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "test_password")
    monkeypatch.setenv("ALERT_EMAIL_FROM", "alerts@example.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "recipient@example.com")

    with pytest.raises(ValueError, match="Missing required SMTP configuration: SMTP_HOST"):
        send_email("Test", "Body")


def test_send_email_missing_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing SMTP_PASSWORD raises ValueError."""
    monkeypatch.setenv("SMTP_HOST", "mail.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    monkeypatch.setenv("SMTP_USERNAME", "user@example.com")
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.setenv("ALERT_EMAIL_FROM", "alerts@example.com")
    monkeypatch.setenv("ALERT_EMAIL_TO", "recipient@example.com")

    with pytest.raises(ValueError, match="Missing required SMTP configuration: SMTP_PASSWORD"):
        send_email("Test", "Body")


def test_send_email_invalid_port(smtp_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that invalid SMTP_PORT returns error result."""
    monkeypatch.setenv("SMTP_PORT", "not_a_number")

    result = send_email("Test", "Body")

    assert result["success"] is False
    assert "Invalid SMTP_PORT" in result["error"]


def test_send_email_auth_failure(smtp_env: None) -> None:
    """Test SMTP authentication failure."""
    import smtplib

    with patch("alerts.smtp_email.smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Bad credentials")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        result = send_email("Test", "Body")

        assert result["success"] is False
        assert "SMTP authentication failed" in result["error"]
        # Password should be redacted from error message
        assert "test_password_12345" not in result["error"]


def test_send_email_connection_error(smtp_env: None) -> None:
    """Test network connection error."""
    with patch("alerts.smtp_email.smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_smtp_ssl.side_effect = OSError("Connection refused")

        result = send_email("Test", "Body")

        assert result["success"] is False
        assert "Connection error" in result["error"]


def test_send_email_smtp_exception(smtp_env: None) -> None:
    """Test generic SMTP exception."""
    import smtplib

    with patch("alerts.smtp_email.smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPException("Server error")
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        result = send_email("Test", "Body")

        assert result["success"] is False
        assert "SMTP error" in result["error"]


def test_message_construction(smtp_env: None) -> None:
    """Test that email message is constructed correctly."""
    with patch("alerts.smtp_email.smtplib.SMTP_SSL") as mock_smtp_ssl:
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        subject = "Important Alert"
        body = "This is the email body content."

        send_email(subject, body)

        # Get the message that was sent
        call_args = mock_server.send_message.call_args
        msg = call_args[0][0]

        assert msg["Subject"] == subject
        assert msg["From"] == "alerts@example.com"
        assert msg["To"] == "recipient@example.com"
        assert body in msg.get_content()


def test_password_redaction_in_errors(smtp_env: None) -> None:
    """Test that password is redacted from all error messages."""
    import smtplib

    password = "super_secret_password_xyz"
    os.environ["SMTP_PASSWORD"] = password

    with patch("alerts.smtp_email.smtplib.SMTP_SSL") as mock_smtp_ssl:
        # Simulate an error that includes the password in the message
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, f"Bad credentials with {password}".encode()
        )
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server

        result = send_email("Test", "Body")

        assert result["success"] is False
        # Password should NOT appear in error
        assert password not in result["error"]
        # Redacted marker should appear
        assert "***REDACTED***" in result["error"] or "Bad credentials" in result["error"]


def test_use_ssl_parsing(smtp_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test various SMTP_USE_SSL values are parsed correctly."""
    # Test "true" (SSL)
    monkeypatch.setenv("SMTP_USE_SSL", "true")
    with patch("alerts.smtp_email.smtplib.SMTP_SSL") as mock_ssl:
        mock_ssl.return_value.__enter__.return_value = MagicMock()
        send_email("Test", "Body")
        assert mock_ssl.called

    # Test "false" (STARTTLS)
    monkeypatch.setenv("SMTP_USE_SSL", "false")
    monkeypatch.setenv("SMTP_PORT", "587")
    with patch("alerts.smtp_email.smtplib.SMTP") as mock_plain:
        mock_plain.return_value.__enter__.return_value = MagicMock()
        send_email("Test", "Body")
        assert mock_plain.called

    # Test "1" (SSL)
    monkeypatch.setenv("SMTP_USE_SSL", "1")
    monkeypatch.setenv("SMTP_PORT", "465")
    with patch("alerts.smtp_email.smtplib.SMTP_SSL") as mock_ssl:
        mock_ssl.return_value.__enter__.return_value = MagicMock()
        send_email("Test", "Body")
        assert mock_ssl.called

    # Test "0" (STARTTLS)
    monkeypatch.setenv("SMTP_USE_SSL", "0")
    monkeypatch.setenv("SMTP_PORT", "587")
    with patch("alerts.smtp_email.smtplib.SMTP") as mock_plain:
        mock_plain.return_value.__enter__.return_value = MagicMock()
        send_email("Test", "Body")
        assert mock_plain.called
