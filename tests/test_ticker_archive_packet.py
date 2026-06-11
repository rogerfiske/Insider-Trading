"""
Tests for Generic Ticker Archive Packet (CP23C)
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def generic_maia_archive_manifest():
    """Load generic MAIA archive manifest."""
    path = Path("docs/sample_reports/generic_ticker/MAIA/archive/MAIA_archive_manifest.json")
    if not path.exists():
        pytest.skip(f"Generic MAIA archive manifest not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_archive_manifest_structure(generic_maia_archive_manifest):
    """Test archive manifest has required structure."""
    required_keys = ["ticker", "cik", "generated_at", "artifacts", "safety"]

    for key in required_keys:
        assert key in generic_maia_archive_manifest, f"Missing required key: {key}"


def test_artifacts_have_checksums(generic_maia_archive_manifest):
    """Test all artifacts have SHA-256 checksums."""
    artifacts = generic_maia_archive_manifest["artifacts"]
    assert len(artifacts) > 0, "No artifacts in manifest"

    for artifact in artifacts:
        assert "sha256" in artifact, f"Missing checksum for artifact: {artifact.get('name')}"
        assert len(artifact["sha256"]) == 64, f"Invalid checksum length for artifact: {artifact.get('name')}"


def test_archive_safety_flags(generic_maia_archive_manifest):
    """Test archive safety flags are correct."""
    expected = {
        "report_only": True,
        "alerts_generated": False,
        "openinsider_spreadsheet_used": False,
        "telegram_sent": False,
        "email_sent": False,
        "scheduled_tasks_modified": False,
        "env_printed_or_changed": False,
        "buy_sell_hold_language_used": False,
    }

    safety = generic_maia_archive_manifest["safety"]

    for flag, expected_value in expected.items():
        assert flag in safety, f"Missing safety flag: {flag}"
        assert safety[flag] == expected_value, f"Safety flag '{flag}': expected {expected_value}, got {safety[flag]}"
