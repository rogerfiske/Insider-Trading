"""
Tests for CP25 Manual SEC Synthesis Command

Verifies that the manual ticker SEC synthesis command works correctly
with proper safety controls, mode support, and degraded-mode handling.
"""

import json
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.manual_sec_synthesis_runner import ManualSECSynthesisRunner


# Test 1: Runner initializes correctly
def test_runner_initialization():
    """Runner must initialize with valid paths."""
    runner = ManualSECSynthesisRunner()
    assert runner.output_root is not None
    assert runner.input_root is not None
    assert runner.project_root is not None


# Test 2: Create run folder with default naming
def test_create_run_folder_default():
    """Create run folder with auto-generated timestamp name."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = runner.create_run_folder()
        assert run_folder.exists()
        assert run_folder.is_dir()
        # Folder name should be timestamp (YYYYMMDD_HHMMSS)
        assert len(run_folder.name) == 15  # YYYYMMDD_HHMMSS format


# Test 3: Create run folder with custom name
def test_create_run_folder_custom_name():
    """Create run folder with custom run name."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = runner.create_run_folder(run_name="test_run")
        assert run_folder.exists()
        assert "test_run" in run_folder.name


# Test 4: Create run folder with ticker naming
def test_create_run_folder_ticker_naming():
    """Create run folder with ticker-based naming."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = runner.create_run_folder(tickers=["MAIA", "NVDA"])
        assert run_folder.exists()
        assert "MAIA_NVDA" in run_folder.name


# Test 5: Create run manifest with required schema
def test_create_run_manifest_schema():
    """Run manifest must include all required fields."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        ticker_results = {
            "MAIA": {
                "status": "completed",
                "modules_run": ["synthesis"],
                "modules_status": {"synthesis": "success"},
                "degraded": False,
                "degraded_reasons": []
            }
        }

        manifest_path = runner.create_run_manifest(
            run_folder,
            "test_run_001",
            ["MAIA"],
            "synthesis-only",
            ticker_results
        )

        assert manifest_path.exists()

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        # Verify required fields
        assert "run_id" in manifest
        assert "generated_at" in manifest
        assert "tickers_requested" in manifest
        assert "mode" in manifest
        assert "output_root" in manifest
        assert "project_root" in manifest
        assert "modules_requested" in manifest
        assert "modules_run_by_ticker" in manifest
        assert "outputs_by_ticker" in manifest
        assert "validation_matrix_path" in manifest
        assert "run_summary_json_path" in manifest
        assert "run_summary_markdown_path" in manifest
        assert "safety_audit_path" in manifest
        assert "degraded_tickers" in manifest
        assert "failed_tickers" in manifest
        assert "safety" in manifest

        # Verify safety flags
        safety = manifest["safety"]
        assert safety["report_only"] is True
        assert safety["alerts_generated"] is False
        assert safety["openinsider_spreadsheet_used"] is False
        assert safety["telegram_sent"] is False
        assert safety["email_sent"] is False
        assert safety["scheduled_tasks_modified"] is False
        assert safety["env_printed_or_changed"] is False
        assert safety["buy_sell_hold_language_used"] is False


# Test 6: Create safety audit with required schema
def test_create_safety_audit_schema():
    """Safety audit must include all required fields."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        audit_path = runner.create_safety_audit(
            run_folder,
            "synthesis-only",
            ["MAIA", "NVDA"]
        )

        assert audit_path.exists()

        with open(audit_path, 'r', encoding='utf-8') as f:
            audit = json.load(f)

        # Verify required fields
        assert "timestamp" in audit
        assert "mode" in audit
        assert "tickers" in audit
        assert "no_alerts_confirmed" in audit
        assert "no_telegram_confirmed" in audit
        assert "no_email_confirmed" in audit
        assert "scheduled_tasks_unchanged_or_not_touched" in audit
        assert "env_not_printed_or_changed" in audit
        assert "openinsider_spreadsheet_not_used" in audit
        assert "secrets_not_written" in audit
        assert "recommendation_language_absent" in audit
        assert "private_file_exclusion_confirmed" in audit
        assert "notes" in audit

        # Verify all safety flags are True
        assert audit["no_alerts_confirmed"] is True
        assert audit["no_telegram_confirmed"] is True
        assert audit["no_email_confirmed"] is True
        assert audit["scheduled_tasks_unchanged_or_not_touched"] is True
        assert audit["env_not_printed_or_changed"] is True
        assert audit["openinsider_spreadsheet_not_used"] is True
        assert audit["secrets_not_written"] is True
        assert audit["recommendation_language_absent"] is True
        assert audit["private_file_exclusion_confirmed"] is True


# Test 7: Create validation matrix with required columns
def test_create_validation_matrix_columns():
    """Validation matrix must have all required columns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        ticker_results = {
            "MAIA": {
                "status": "completed",
                "modules_run": ["synthesis"],
                "modules_status": {"synthesis": "success"},
                "degraded": False,
                "degraded_reasons": []
            }
        }

        matrix_path = runner.create_validation_matrix(run_folder, ticker_results)

        assert matrix_path.exists()

        with open(matrix_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Check header
        header = lines[0].strip()
        required_columns = [
            "ticker",
            "cik",
            "company_name",
            "mode",
            "inventory_status",
            "form4_status",
            "ownership_status",
            "xbrl_status",
            "capital_structure_status",
            "thirteenf_status",
            "synthesis_status",
            "evidence_rows",
            "posture",
            "degraded",
            "primary_degraded_reason",
            "safety_passed"
        ]

        for column in required_columns:
            assert column in header


# Test 8: Modes supported (full, inventory-first, synthesis-only)
def test_modes_supported():
    """Runner must support all three modes."""
    runner = ManualSECSynthesisRunner()

    # Test _get_modules_for_mode
    full_modules = runner._get_modules_for_mode("full")
    assert "inventory" in full_modules
    assert "synthesis" in full_modules

    inventory_modules = runner._get_modules_for_mode("inventory-first")
    assert inventory_modules == ["inventory"]

    synthesis_modules = runner._get_modules_for_mode("synthesis-only")
    assert synthesis_modules == ["synthesis"]


# Test 9: Degraded mode handling
def test_degraded_mode_handling():
    """Runner must handle degraded mode correctly."""
    runner = ManualSECSynthesisRunner()

    # Create a ticker result with degraded status
    result = runner._create_ticker_result(
        ticker="TEST",
        modules_run=["inventory", "synthesis"],
        modules_status={"inventory": "success", "synthesis": "error"},
        degraded=True,
        degraded_reasons=["Synthesis failed due to missing inputs"]
    )

    assert result["ticker"] == "TEST"
    assert result["status"] == "degraded"
    assert result["degraded"] is True
    assert len(result["degraded_reasons"]) > 0


# Test 10: Create run summary (JSON and Markdown)
def test_create_run_summary():
    """Run summary must create both JSON and Markdown files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        ticker_results = {
            "MAIA": {
                "status": "completed",
                "modules_run": ["synthesis"],
                "modules_status": {"synthesis": "success"},
                "degraded": False,
                "degraded_reasons": []
            }
        }

        json_path, md_path = runner.create_run_summary(
            run_folder,
            "test_run_001",
            "synthesis-only",
            ["MAIA"],
            ticker_results
        )

        assert json_path.exists()
        assert md_path.exists()
        assert json_path.suffix == ".json"
        assert md_path.suffix == ".md"

        # Verify JSON content
        with open(json_path, 'r', encoding='utf-8') as f:
            summary = json.load(f)
            assert "run_id" in summary
            assert "mode" in summary
            assert "safety" in summary

        # Verify Markdown content
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
            assert "Manual SEC Synthesis Run Summary" in md_content
            assert "not investment advice" in md_content.lower()


# Test 11: No buy/sell/hold language in outputs
def test_no_recommendation_language():
    """Run summary must not contain buy/sell/hold recommendation language."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        ticker_results = {"MAIA": {"status": "completed", "modules_run": [], "modules_status": {}, "degraded": False, "degraded_reasons": []}}

        json_path, md_path = runner.create_run_summary(
            run_folder,
            "test_run_001",
            "synthesis-only",
            ["MAIA"],
            ticker_results
        )

        # Check Markdown for prohibited language
        with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # Check for prohibited phrases, skipping lines that document what NOT to do
        prohibited = ["strong buy", "weak buy", "buy recommendation", "sell recommendation", "hold recommendation", "price target", "we recommend buying", "we recommend selling"]

        for line in lines:
            line_lower = line.lower()
            # Skip lines documenting prohibited language (marked with "no", "prohibited", "forbidden", "avoid", or negative context)
            if 'no ' in line_lower or 'prohibit' in line_lower or 'forbidden' in line_lower or 'avoid' in line_lower or '✗' in line:
                continue
            # Check for actual recommendation language
            for phrase in prohibited:
                assert phrase not in line_lower, f"Prohibited phrase '{phrase}' found in line: {line.strip()}"


# Test 12: No secrets in outputs
def test_no_secrets_in_outputs():
    """Run outputs must not contain secrets or sensitive data."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        ticker_results = {"MAIA": {"status": "completed", "modules_run": [], "modules_status": {}, "degraded": False, "degraded_reasons": []}}

        # Create all outputs
        runner.create_run_manifest(run_folder, "test_run_001", ["MAIA"], "synthesis-only", ticker_results)
        runner.create_safety_audit(run_folder, "synthesis-only", ["MAIA"])
        runner.create_validation_matrix(run_folder, ticker_results)
        json_path, md_path = runner.create_run_summary(run_folder, "test_run_001", "synthesis-only", ["MAIA"], ticker_results)

        # Check all output files for secrets
        output_files = [
            run_folder / "run_manifest.json",
            run_folder / "safety_audit.json",
            run_folder / "validation_matrix.csv",
            json_path,
            md_path
        ]

        secret_patterns = [
            "TELEGRAM_BOT_TOKEN=",
            "TELEGRAM_CHAT_ID=",
            "SMTP_PASSWORD=",
            "GMAIL_APP_PASSWORD=",
            "sk-ant-",
            "BEGIN PRIVATE KEY"
        ]

        for file_path in output_files:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for pattern in secret_patterns:
                    assert pattern not in content, f"Secret pattern '{pattern}' found in {file_path.name}"


# Test 13: Safety audit confirms no Telegram/email/alerts
def test_safety_audit_no_external_communication():
    """Safety audit must confirm no external communication."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        audit_path = runner.create_safety_audit(run_folder, "synthesis-only", ["MAIA"])

        with open(audit_path, 'r', encoding='utf-8') as f:
            audit = json.load(f)

        # Verify no external communication
        assert audit["no_alerts_confirmed"] is True
        assert audit["no_telegram_confirmed"] is True
        assert audit["no_email_confirmed"] is True


# Test 14: Safety audit confirms no scheduled task modifications
def test_safety_audit_no_scheduled_tasks():
    """Safety audit must confirm no scheduled task modifications."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        audit_path = runner.create_safety_audit(run_folder, "synthesis-only", ["MAIA"])

        with open(audit_path, 'r', encoding='utf-8') as f:
            audit = json.load(f)

        assert audit["scheduled_tasks_unchanged_or_not_touched"] is True


# Test 15: Safety audit confirms no .env access
def test_safety_audit_no_env_access():
    """Safety audit must confirm no .env access or modifications."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        audit_path = runner.create_safety_audit(run_folder, "synthesis-only", ["MAIA"])

        with open(audit_path, 'r', encoding='utf-8') as f:
            audit = json.load(f)

        assert audit["env_not_printed_or_changed"] is True


# Test 16: Safety audit confirms no OpenInsider spreadsheet usage
def test_safety_audit_no_openinsider():
    """Safety audit must confirm no OpenInsider spreadsheet usage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        audit_path = runner.create_safety_audit(run_folder, "synthesis-only", ["MAIA"])

        with open(audit_path, 'r', encoding='utf-8') as f:
            audit = json.load(f)

        assert audit["openinsider_spreadsheet_not_used"] is True


# Test 17: Ticker result structure
def test_ticker_result_structure():
    """Ticker result must have correct structure."""
    runner = ManualSECSynthesisRunner()

    result = runner._create_ticker_result(
        ticker="MAIA",
        modules_run=["inventory", "synthesis"],
        modules_status={"inventory": "success", "synthesis": "success"},
        degraded=False,
        degraded_reasons=[]
    )

    assert "ticker" in result
    assert "status" in result
    assert "modules_run" in result
    assert "modules_status" in result
    assert "degraded" in result
    assert "degraded_reasons" in result


# Test 18: Manifest identifies degraded tickers
def test_manifest_identifies_degraded_tickers():
    """Manifest must correctly identify degraded tickers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        ticker_results = {
            "MAIA": {
                "status": "completed",
                "modules_run": ["synthesis"],
                "modules_status": {"synthesis": "success"},
                "degraded": False,
                "degraded_reasons": []
            },
            "NVDA": {
                "status": "degraded",
                "modules_run": ["synthesis"],
                "modules_status": {"synthesis": "error"},
                "degraded": True,
                "degraded_reasons": ["Missing input data"]
            }
        }

        manifest_path = runner.create_run_manifest(
            run_folder,
            "test_run_001",
            ["MAIA", "NVDA"],
            "synthesis-only",
            ticker_results
        )

        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        assert "NVDA" in manifest["degraded_tickers"]
        assert "MAIA" not in manifest["degraded_tickers"]


# Test 19: Run summary includes disclaimer
def test_run_summary_includes_disclaimer():
    """Run summary must include 'not investment advice' disclaimer."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        ticker_results = {"MAIA": {"status": "completed", "modules_run": [], "modules_status": {}, "degraded": False, "degraded_reasons": []}}

        json_path, md_path = runner.create_run_summary(
            run_folder,
            "test_run_001",
            "synthesis-only",
            ["MAIA"],
            ticker_results
        )

        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()

        assert "not investment advice" in md_content.lower()


# Test 20: Validation matrix marks safety as passed
def test_validation_matrix_safety_passed():
    """Validation matrix must mark safety as passed for all tickers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runner = ManualSECSynthesisRunner(output_root=Path(temp_dir))
        run_folder = Path(temp_dir) / "test_run"
        run_folder.mkdir(parents=True)

        ticker_results = {
            "MAIA": {"status": "completed", "modules_run": [], "modules_status": {}, "degraded": False, "degraded_reasons": []}
        }

        matrix_path = runner.create_validation_matrix(run_folder, ticker_results)

        with open(matrix_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Check data row (skip header)
        data_row = lines[1].strip()
        assert "true" in data_row  # safety_passed should be true
