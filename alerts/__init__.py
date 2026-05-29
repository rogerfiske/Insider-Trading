"""
Insider-Trading alert delivery subsystem.

Provides email and Telegram delivery channels for consensus alerts.
"""

from alerts.smtp_email import send_email

__all__ = ["send_email"]
