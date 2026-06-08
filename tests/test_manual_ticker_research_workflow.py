"""Tests for manual ticker research workflow.

Tests cover:
- Manual report mode does not send Telegram
- Manual report mode does not send email
- Manual report mode does not consume Ross daily guard
- Private spreadsheet is not required
- Lookback window functionality
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_manual_report_no_telegram_sent():
    """Test that manual ticker research does not send Telegram messages."""
    # ticker_drilldown.py runs in --dry-run-report mode and never imports alert routing
    # This test verifies the script completes successfully and report confirms no alerts sent
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "365",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_no_telegram.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "DRY-RUN" in result.stdout

    # Verify report confirms no alerts sent
    report_path = Path("docs/sample_reports/test_no_telegram.md")
    assert report_path.exists()
    report_content = report_path.read_text()
    assert "No Telegram or email was sent" in report_content

    # Cleanup
    report_path.unlink()


def test_manual_report_dry_run_message():
    """Test that manual ticker research report indicates dry-run mode."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "365",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_dry_run.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "DRY-RUN" in result.stdout

    # Verify report contains dry-run indicator
    report_path = Path("docs/sample_reports/test_dry_run.md")
    assert report_path.exists()
    report_content = report_path.read_text()
    assert "DRY-RUN" in report_content or "dry-run" in report_content.lower()
    assert "No Telegram or email was sent" in report_content

    # Cleanup
    report_path.unlink()


def test_manual_report_no_spreadsheet_required():
    """Test that manual ticker research does not require OpenInsider spreadsheet."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "365",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_no_spreadsheet.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify report confirms spreadsheet was not used
    report_path = Path("docs/sample_reports/test_no_spreadsheet.md")
    assert report_path.exists()
    report_content = report_path.read_text()
    assert "OpenInsider spreadsheet" in report_content
    assert "NOT Used" in report_content or "not used" in report_content.lower()

    # Cleanup
    report_path.unlink()


def test_manual_report_uses_sec_sources_only():
    """Test that manual ticker research uses only SEC/project-supported sources."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "365",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_sec_sources.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify report confirms SEC sources only
    report_path = Path("docs/sample_reports/test_sec_sources.md")
    assert report_path.exists()
    report_content = report_path.read_text()
    assert "Data Source Boundary" in report_content
    assert "Project connectors only" in report_content
    assert "SEC" in report_content

    # Cleanup
    report_path.unlink()


def test_manual_report_includes_all_agents():
    """Test that manual ticker research report includes all seven agents."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "365",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_all_agents.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify report includes all seven agents
    report_path = Path("docs/sample_reports/test_all_agents.md")
    assert report_path.exists()
    report_content = report_path.read_text()

    # Check for agent sections
    assert "## Eddie" in report_content
    assert "## Maggie" in report_content
    assert "## Frank" in report_content
    assert "## Maya" in report_content
    assert "## Janet" in report_content
    assert "## Sophie" in report_content
    assert "## Ross" in report_content

    # Cleanup
    report_path.unlink()


def test_manual_report_lookback_configuration():
    """Test that different lookback windows produce different queries."""
    # Run with 30-day lookback
    result_30 = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "30",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_lookback_30_config.md",
        ],
        capture_output=True,
        text=True,
    )
    assert result_30.returncode == 0

    # Run with 1460-day lookback
    result_1460 = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "1460",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_lookback_1460_config.md",
        ],
        capture_output=True,
        text=True,
    )
    assert result_1460.returncode == 0

    # Verify both reports show different lookback windows
    report_30_path = Path("docs/sample_reports/test_lookback_30_config.md")
    report_1460_path = Path("docs/sample_reports/test_lookback_1460_config.md")

    assert report_30_path.exists()
    assert report_1460_path.exists()

    content_30 = report_30_path.read_text()
    content_1460 = report_1460_path.read_text()

    assert "**Lookback Window**: 30 days" in content_30
    assert "**Lookback Window**: 1460 days" in content_1460

    assert "Eddie fetches issuer-specific Form 4 filings from SEC submissions API" in content_30
    assert "Lookback: 30 days" in content_30
    assert "Eddie fetches issuer-specific Form 4 filings from SEC submissions API" in content_1460
    assert "Lookback: 1460 days" in content_1460

    # Cleanup
    report_30_path.unlink()
    report_1460_path.unlink()


def test_manual_report_informational_disclaimer():
    """Test that manual ticker research includes informational-only disclaimer."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "365",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_disclaimer.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify report includes safety disclaimer
    report_path = Path("docs/sample_reports/test_disclaimer.md")
    assert report_path.exists()
    report_content = report_path.read_text()
    assert "informational only" in report_content.lower()
    assert "not trading advice" in report_content.lower()

    # Cleanup
    report_path.unlink()
