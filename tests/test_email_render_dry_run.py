"""Tests for email alert render dry-run script."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.render_email_alert_dry_run import (
    SampleConsensusEvent,
    render_dry_run_email,
    render_sample_consensus,
)


def test_render_sample_consensus_returns_string():
    """Render function returns a string."""
    from datetime import datetime, timezone

    ev = SampleConsensusEvent(
        ticker="TEST",
        direction="BULLISH",
        timestamp=datetime.now(timezone.utc),
        scouts=["eddie", "maggie"],
        reasons=["Reason 1", "Reason 2"],
        aggregate_confidence=10,
    )

    result = render_sample_consensus(ev)

    assert isinstance(result, str)
    assert len(result) > 0


def test_rendered_body_includes_dry_run_header():
    """Rendered file includes dry-run header."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sample.md"
        render_dry_run_email(output_path)

        content = output_path.read_text(encoding="utf-8")

        assert "EMAIL RENDER DRY-RUN — NO EMAIL SENT" in content
        assert "Dry-run render test only" in content


def test_rendered_body_includes_evidence_context():
    """Rendered body includes evidence context."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sample.md"
        render_dry_run_email(output_path)

        content = output_path.read_text(encoding="utf-8")

        # Check all required evidence fields
        assert "Ticker:" in content
        assert "Direction:" in content
        assert "Severity:" in content
        assert "Scout count:" in content
        assert "Aggregate confidence:" in content
        assert "Per-scout reasoning included" in content
        assert "Timestamp included" in content
        assert "Disclaimer included" in content


def test_rendered_body_does_not_include_smtp_password():
    """Rendered body does not include SMTP password."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sample.md"

        # Set SMTP password in environment
        with patch.dict(os.environ, {"SMTP_PASSWORD": "secret123"}):
            render_dry_run_email(output_path)

            content = output_path.read_text(encoding="utf-8")

            # Should not contain the secret
            assert "secret123" not in content
            assert "SMTP_PASSWORD" not in content


def test_rendered_body_does_not_include_telegram_token():
    """Rendered body does not include Telegram token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sample.md"

        # Set Telegram token in environment
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "123456:ABCDEF"}):
            render_dry_run_email(output_path)

            content = output_path.read_text(encoding="utf-8")

            # Should not contain the secret
            assert "123456:ABCDEF" not in content
            assert "TELEGRAM_BOT_TOKEN" not in content


def test_render_command_does_not_call_smtp():
    """Render command does not call SMTP."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sample.md"

        # Mock smtplib to fail if called
        with patch("smtplib.SMTP_SSL") as mock_smtp_ssl, patch(
            "smtplib.SMTP"
        ) as mock_smtp:
            render_dry_run_email(output_path)

            # Verify SMTP was never called
            mock_smtp_ssl.assert_not_called()
            mock_smtp.assert_not_called()


def test_render_command_does_not_call_telegram():
    """Render command does not call Telegram."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sample.md"

        # Mock urllib to fail if called
        with patch("urllib.request.urlopen") as mock_urlopen:
            render_dry_run_email(output_path)

            # Verify Telegram API was never called
            mock_urlopen.assert_not_called()


def test_email_remains_disabled():
    """Email remains disabled during render."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sample.md"

        with patch.dict(os.environ, {"ALERT_ENABLE_EMAIL": "false"}):
            render_dry_run_email(output_path)

            content = output_path.read_text(encoding="utf-8")

            # Verify output confirms email is disabled
            assert "ALERT_ENABLE_EMAIL`: **false**" in content or "false" in content


def test_informational_only_disclaimer_present():
    """Informational-only disclaimer present."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "sample.md"
        render_dry_run_email(output_path)

        content = output_path.read_text(encoding="utf-8")

        # Check for disclaimer
        assert (
            "informational" in content.lower() or "not a trade instruction" in content
        )
        assert "No email sent" in content or "No live alert" in content


def test_render_creates_output_directory():
    """Render creates output directory if missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "nested" / "dir" / "sample.md"

        # Directory should not exist yet
        assert not output_path.parent.exists()

        render_dry_run_email(output_path)

        # Directory should be created
        assert output_path.parent.exists()
        assert output_path.exists()


def test_render_sample_consensus_includes_all_scouts():
    """Render includes all scout reasons."""
    from datetime import datetime, timezone

    ev = SampleConsensusEvent(
        ticker="TEST",
        direction="BULLISH",
        timestamp=datetime.now(timezone.utc),
        scouts=["scout1", "scout2", "scout3"],
        reasons=["Reason A", "Reason B", "Reason C"],
        aggregate_confidence=15,
    )

    result = render_sample_consensus(ev)

    # All scouts and reasons should be present
    assert "scout1" in result
    assert "scout2" in result
    assert "scout3" in result
    assert "Reason A" in result
    assert "Reason B" in result
    assert "Reason C" in result
