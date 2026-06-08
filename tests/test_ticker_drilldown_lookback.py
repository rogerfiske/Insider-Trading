"""Tests for ticker drilldown lookback functionality.

Tests cover:
- --lookback-days argument parsing
- Default lookback behavior
- Lookback validation (zero/negative/over-limit)
- Lookback window appears in report
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def test_lookback_days_default():
    """Test that default lookback is 365 days when not specified."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_lookback_default.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "Lookback window: 365 days" in result.stdout

    # Verify report contains default lookback
    report_path = Path("docs/sample_reports/test_lookback_default.md")
    assert report_path.exists()
    report_content = report_path.read_text()
    assert "**Lookback Window**: 365 days" in report_content

    # Cleanup
    report_path.unlink()


def test_lookback_days_custom_30():
    """Test that --lookback-days 30 is accepted and used."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "30",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_lookback_30.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "Lookback window: 30 days" in result.stdout

    # Verify report contains custom lookback
    report_path = Path("docs/sample_reports/test_lookback_30.md")
    assert report_path.exists()
    report_content = report_path.read_text()
    assert "**Lookback Window**: 30 days" in report_content

    # Cleanup
    report_path.unlink()


def test_lookback_days_custom_1460():
    """Test that --lookback-days 1460 (4 years, maximum) is accepted."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "1460",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_lookback_1460.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"
    assert "Lookback window: 1460 days" in result.stdout

    # Verify report contains 4-year lookback
    report_path = Path("docs/sample_reports/test_lookback_1460.md")
    assert report_path.exists()
    report_content = report_path.read_text()
    assert "**Lookback Window**: 1460 days" in report_content

    # Cleanup
    report_path.unlink()


def test_lookback_days_reject_zero():
    """Test that --lookback-days 0 is rejected."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "0",
            "--dry-run-report",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, "Expected failure for zero lookback"
    assert "--lookback-days must be positive" in result.stdout


def test_lookback_days_reject_negative():
    """Test that negative --lookback-days is rejected."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "-10",
            "--dry-run-report",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, "Expected failure for negative lookback"
    assert "--lookback-days must be positive" in result.stdout


def test_lookback_days_reject_over_limit():
    """Test that --lookback-days over 1460 is rejected."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "2000",
            "--dry-run-report",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, "Expected failure for over-limit lookback"
    assert "--lookback-days cannot exceed 1460" in result.stdout


def test_lookback_appears_in_eddie_section():
    """Test that lookback window appears in Eddie's Form 4 section."""
    result = subprocess.run(
        [
            sys.executable,
            "scripts/ticker_drilldown.py",
            "--ticker",
            "MAIA",
            "--lookback-days",
            "180",
            "--dry-run-report",
            "--output",
            "docs/sample_reports/test_lookback_eddie.md",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify Eddie's section mentions the lookback
    report_path = Path("docs/sample_reports/test_lookback_eddie.md")
    assert report_path.exists()
    report_content = report_path.read_text()

    # Check Eddie section shows the lookback
    assert "Eddie fetches issuer-specific Form 4 filings from SEC submissions API" in report_content
    assert "Lookback: 180 days" in report_content

    # Cleanup
    report_path.unlink()
