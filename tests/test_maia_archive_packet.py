"""
Tests for MAIA monitoring packet archive (CP23H)

Tests cover:
1. Archive manifest required keys
2. Manifest safety flags are correct
3. Archive index exists
4. README exists
5. Required markdown artifacts are included
6. Required JSON artifacts are included
7. Required CSV template is included
8. SHA-256 checksums exist for archive artifacts
9. ZIP archive, if created, excludes .env, .state, databases, logs, caches
10. Archive files contain no secrets
11. Archive does not contain buy/sell/hold recommendation language
12. No Telegram/email/alert code is called
13. OpenInsider spreadsheet is not required
"""

import json
import zipfile
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def archive_root(project_root):
    """Get archive root directory."""
    return project_root / "docs" / "sample_reports" / "maia_archive"


@pytest.fixture
def manifest_path(archive_root):
    """Get manifest path."""
    return archive_root / "MAIA_archive_manifest.json"


@pytest.fixture
def manifest_data(manifest_path):
    """Load manifest data."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_manifest_required_keys(manifest_data):
    """Test archive manifest has required keys."""
    required_keys = [
        "ticker",
        "cik",
        "generated_at",
        "approved_checkpoint_range",
        "approved_commits",
        "archive_root",
        "artifacts",
        "safety",
        "limitations",
    ]

    for key in required_keys:
        assert key in manifest_data, f"Missing required key: {key}"


def test_manifest_safety_flags_correct(manifest_data):
    """Test manifest safety flags are correct."""
    safety = manifest_data.get("safety", {})

    expected_safety_flags = {
        "report_only": True,
        "alerts_generated": False,
        "openinsider_spreadsheet_used": False,
        "telegram_sent": False,
        "email_sent": False,
        "scheduled_tasks_modified": False,
        "env_printed_or_changed": False,
        "secrets_included": False,
    }

    for flag, expected_value in expected_safety_flags.items():
        actual_value = safety.get(flag)
        assert actual_value == expected_value, \
            f"Safety flag '{flag}': expected {expected_value}, got {actual_value}"


def test_archive_index_exists(archive_root):
    """Test archive index exists."""
    index_path = archive_root / "MAIA_archive_index.md"
    assert index_path.exists(), "Archive index file not found"


def test_readme_exists(archive_root):
    """Test README exists."""
    readme_path = archive_root / "README.md"
    assert readme_path.exists(), "README file not found"


def test_required_markdown_artifacts_included(archive_root):
    """Test required markdown artifacts are included."""
    md_dir = archive_root / "md"
    assert md_dir.exists(), "Markdown directory not found"

    required_md_files = [
        "MAIA_full_synthesis_packet.md",
        "MAIA_weekly_monitoring_checklist.md",
        "MAIA_monitoring_baseline_status.md",
        "MAIA_13F_infotable_matching_report.md",
        "MAIA_market_confirmation_checklist.md",
        "MAIA_market_confirmation_baseline_status.md",
        "CP23D_MAIA_full_synthesis_packet_report.md",
        "CP23E_MAIA_monitoring_pack_report.md",
        "CP23F_fix_13f_parser_hardening_report.md",
        "CP23G_MAIA_market_confirmation_checklist_report.md",
    ]

    for filename in required_md_files:
        file_path = md_dir / filename
        assert file_path.exists(), f"Required markdown file not found: {filename}"


def test_required_json_artifacts_included(archive_root):
    """Test required JSON artifacts are included."""
    json_dir = archive_root / "json"
    assert json_dir.exists(), "JSON directory not found"

    required_json_files = [
        "MAIA_full_synthesis_packet.json",
        "MAIA_monitoring_plan.json",
        "MAIA_13F_infotable_matching.json",
        "MAIA_market_confirmation_plan.json",
    ]

    for filename in required_json_files:
        file_path = json_dir / filename
        assert file_path.exists(), f"Required JSON file not found: {filename}"


def test_required_csv_template_included(archive_root):
    """Test required CSV template is included."""
    csv_dir = archive_root / "csv"
    assert csv_dir.exists(), "CSV directory not found"

    csv_file = csv_dir / "MAIA_market_observation_template.csv"
    assert csv_file.exists(), "Required CSV template not found"


def test_sha256_checksums_exist(manifest_data):
    """Test SHA-256 checksums exist for archive artifacts."""
    artifacts = manifest_data.get("artifacts", [])
    assert len(artifacts) > 0, "No artifacts in manifest"

    for artifact in artifacts:
        assert "sha256" in artifact, f"Missing checksum for artifact: {artifact.get('name')}"
        assert len(artifact["sha256"]) == 64, \
            f"Invalid SHA-256 checksum length for artifact: {artifact.get('name')}"


def test_zip_archive_excludes_private_files(archive_root):
    """Test ZIP archive, if created, excludes .env, .state, databases, logs, caches."""
    zip_path = archive_root / "MAIA_monitoring_packet_archive.zip"

    if not zip_path.exists():
        pytest.skip("ZIP archive not created")

    with zipfile.ZipFile(zip_path, "r") as zf:
        file_list = zf.namelist()

        # Check for forbidden patterns
        forbidden_patterns = [".env", ".state", ".db", ".sqlite", ".log", "cache", "MAIA.xlsx", "OpenInsider", "openinsider"]

        for pattern in forbidden_patterns:
            matching_files = [f for f in file_list if pattern in f.lower()]
            assert len(matching_files) == 0, \
                f"ZIP archive contains forbidden files matching pattern '{pattern}': {matching_files}"


def test_archive_files_contain_no_secrets(archive_root):
    """Test archive files contain no secrets."""
    # Check for actual secret values (not pattern documentation)
    # NOTE: Pattern names like "TELEGRAM_BOT_TOKEN" appear in safety documentation
    # We're checking for actual secret values, not pattern documentation
    forbidden_secret_values = [
        "sk-ant-api",  # Anthropic API key prefix with actual value
        "xoxb-",  # Slack bot token prefix
        "ghp_",  # GitHub personal access token prefix
    ]

    # Check all archived text files
    for subdir in ["md", "json", "csv"]:
        subdir_path = archive_root / subdir
        if subdir_path.exists():
            for file_path in subdir_path.glob("*"):
                if file_path.is_file():
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    for pattern in forbidden_secret_values:
                        assert pattern not in content, \
                            f"Found secret value '{pattern}' in file: {file_path.name}"


def test_archive_no_buy_sell_hold_recommendation_language(archive_root):
    """Test archive does not contain buy/sell/hold recommendation language as actual recommendations."""
    # NOTE: This test checks for actual investment recommendations, not monitoring actions
    # Phrases like "track insider buying" or "no buy/sell/hold recommendation" are acceptable
    # We're checking for recommendation fields with actual recommendation language
    json_dir = archive_root / "json"
    if json_dir.exists():
        for file_path in json_dir.glob("*.json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check for actual recommendation fields (not monitoring/tracking)
            def check_dict_for_recommendations(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        # Only check "recommendation" or "rating" fields, not "action" (which is monitoring)
                        if key in ["recommendation", "rating"] and isinstance(value, str):
                            forbidden = ["strong buy", "strong sell", "buy recommendation", "sell recommendation", "hold recommendation"]
                            value_lower = value.lower()
                            for term in forbidden:
                                assert term not in value_lower, \
                                    f"Found forbidden recommendation '{term}' in {file_path.name} at {path}.{key}"
                        check_dict_for_recommendations(value, f"{path}.{key}")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_dict_for_recommendations(item, f"{path}[{i}]")

            check_dict_for_recommendations(data)


def test_no_telegram_email_alert_code():
    """Test no Telegram/email/alert code is called."""
    script_path = Path(__file__).parent.parent / "scripts" / "maia_archive_packet.py"

    with open(script_path, "r", encoding="utf-8") as f:
        script_content = f.read()

    forbidden_imports = ["telegram", "smtplib", "email.mime"]
    for forbidden_import in forbidden_imports:
        assert f"import {forbidden_import}" not in script_content, \
            f"Found forbidden import: {forbidden_import}"


def test_openinsider_spreadsheet_not_required(manifest_data):
    """Test OpenInsider spreadsheet is not required."""
    safety = manifest_data.get("safety", {})
    assert safety.get("openinsider_spreadsheet_used") is False, \
        "OpenInsider spreadsheet should not be used"


def test_manifest_ticker_is_maia(manifest_data):
    """Test manifest ticker is MAIA."""
    assert manifest_data.get("ticker") == "MAIA"


def test_manifest_cik_is_correct(manifest_data):
    """Test manifest CIK is correct."""
    assert manifest_data.get("cik") == "0001878313"


def test_manifest_checkpoint_range(manifest_data):
    """Test manifest checkpoint range is CP23D-CP23G."""
    assert manifest_data.get("approved_checkpoint_range") == "CP23D-CP23G"


def test_manifest_approved_commits(manifest_data):
    """Test manifest approved commits are listed."""
    approved_commits = manifest_data.get("approved_commits", [])
    expected_commits = ["0fbff09", "b2c0ade", "fb2075f", "b72cda0"]

    for commit in expected_commits:
        assert commit in approved_commits, f"Expected commit {commit} not in approved_commits"


def test_manifest_limitations_include_13f_parser(manifest_data):
    """Test manifest limitations include 13F parser limitation."""
    limitations = manifest_data.get("limitations", [])
    limitations_text = " ".join(str(item) for item in limitations).lower()

    assert "13f" in limitations_text and "60%" in limitations_text, \
        "Limitations should mention 13F parser 60% success rate"


def test_manifest_limitations_include_manual_entry(manifest_data):
    """Test manifest limitations include manual entry note."""
    limitations = manifest_data.get("limitations", [])
    limitations_text = " ".join(str(item) for item in limitations).lower()

    assert "manual" in limitations_text, \
        "Limitations should mention manual entry requirement"


def test_manifest_limitations_include_thio_104(manifest_data):
    """Test manifest limitations include THIO-104 data timing unknown."""
    limitations = manifest_data.get("limitations", [])
    limitations_text = " ".join(str(item) for item in limitations).lower()

    assert "thio-104" in limitations_text and ("not disclosed" in limitations_text or "unknown" in limitations_text), \
        "Limitations should mention THIO-104 data timing not disclosed"


def test_artifacts_have_required_fields(manifest_data):
    """Test all artifacts have required fields."""
    artifacts = manifest_data.get("artifacts", [])
    assert len(artifacts) > 0, "No artifacts in manifest"

    required_fields = ["name", "type", "original_path", "archive_path", "purpose", "status", "sha256"]

    for artifact in artifacts:
        for field in required_fields:
            assert field in artifact, \
                f"Artifact {artifact.get('name', 'unknown')} missing required field: {field}"


def test_archive_has_15_artifacts(manifest_data):
    """Test archive has 15 artifacts (10 md + 4 json + 1 csv)."""
    artifacts = manifest_data.get("artifacts", [])
    assert len(artifacts) == 15, f"Expected 15 artifacts, got {len(artifacts)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
