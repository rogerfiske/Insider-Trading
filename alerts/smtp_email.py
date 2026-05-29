#!/usr/bin/env python3
"""
Generic SMTP email delivery for Insider-Trading alerts.

Supports any SMTP provider (Gmail, 4SecureMail, etc.) via environment
variables. Uses standard library smtplib + email.message.EmailMessage.

Environment variables:
  SMTP_HOST            - SMTP server hostname (e.g., mail.4securemail.com)
  SMTP_PORT            - SMTP port (465 for SSL, 587 for STARTTLS)
  SMTP_USE_SSL         - "true" for SSL (port 465), "false" for STARTTLS (port 587)
  SMTP_USERNAME        - SMTP authentication username
  SMTP_PASSWORD        - SMTP authentication password (never printed)
  ALERT_EMAIL_FROM     - From address for alerts
  ALERT_EMAIL_TO       - To address for alerts

Never prints or logs SMTP_PASSWORD. Redacts secrets in error messages.
Returns structured result: {"success": bool, "error": str or None}
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import TypedDict


class SendResult(TypedDict):
    """Result of send_email operation."""
    success: bool
    error: str | None


def _redact_password(text: str) -> str:
    """Redact SMTP password from error messages."""
    password = os.environ.get("SMTP_PASSWORD", "")
    if password and password in text:
        return text.replace(password, "***REDACTED***")
    return text


def send_email(subject: str, body: str) -> SendResult:
    """
    Send an email via generic SMTP.

    Args:
        subject: Email subject line
        body: Email body (plain text)

    Returns:
        SendResult with success=True on success, or success=False with error message

    Raises:
        ValueError: If required SMTP configuration is missing
    """
    # Required config
    host = os.environ.get("SMTP_HOST", "").strip()
    port_str = os.environ.get("SMTP_PORT", "").strip()
    use_ssl_str = os.environ.get("SMTP_USE_SSL", "").strip().lower()
    username = os.environ.get("SMTP_USERNAME", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "")
    from_addr = os.environ.get("ALERT_EMAIL_FROM", "").strip()
    to_addr = os.environ.get("ALERT_EMAIL_TO", "").strip()

    # Validate required fields
    missing = []
    if not host:
        missing.append("SMTP_HOST")
    if not port_str:
        missing.append("SMTP_PORT")
    if not use_ssl_str:
        missing.append("SMTP_USE_SSL")
    if not username:
        missing.append("SMTP_USERNAME")
    if not password:
        missing.append("SMTP_PASSWORD")
    if not from_addr:
        missing.append("ALERT_EMAIL_FROM")
    if not to_addr:
        missing.append("ALERT_EMAIL_TO")

    if missing:
        raise ValueError(
            f"Missing required SMTP configuration: {', '.join(missing)}. "
            f"Please set these environment variables in .env"
        )

    # Parse port
    try:
        port = int(port_str)
    except ValueError:
        return SendResult(
            success=False,
            error=f"Invalid SMTP_PORT: {port_str!r} (must be an integer)"
        )

    # Parse SSL mode
    use_ssl = use_ssl_str in ("true", "1", "yes")

    # Build message
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    # Send via SMTP
    try:
        if use_ssl:
            # SMTP over SSL/TLS (port 465)
            with smtplib.SMTP_SSL(host, port, timeout=30) as server:
                server.login(username, password)
                server.send_message(msg)
        else:
            # SMTP with STARTTLS (port 587)
            with smtplib.SMTP(host, port, timeout=30) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

        return SendResult(success=True, error=None)

    except smtplib.SMTPAuthenticationError as exc:
        # Redact password from exception message
        error_msg = _redact_password(str(exc))
        return SendResult(
            success=False,
            error=f"SMTP authentication failed: {error_msg}"
        )

    except smtplib.SMTPException as exc:
        error_msg = _redact_password(str(exc))
        return SendResult(
            success=False,
            error=f"SMTP error: {error_msg}"
        )

    except OSError as exc:
        # Network/connection errors
        error_msg = _redact_password(str(exc))
        return SendResult(
            success=False,
            error=f"Connection error: {error_msg}"
        )

    except Exception as exc:  # noqa: BLE001
        # Catch-all for unexpected errors
        error_msg = _redact_password(str(exc))
        return SendResult(
            success=False,
            error=f"Unexpected error: {error_msg}"
        )
