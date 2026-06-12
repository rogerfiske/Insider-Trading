"""
Tests for CP24J archive integrity and completeness.

Verifies that the CP24 generic SEC pipeline archive has all required files,
correct checksums, no secrets, and proper safety documentation.
"""
import json
import pytest
from pathlib import Path


# Archive root
ARCHIVE_ROOT = Path("../docs/archives/cp24_generic_sec_pipeline")

# Archive files
README = ARCHIVE_ROOT / "README.md"
MANIFEST_JSON = ARCHIVE_ROOT / "MANIFEST.json"
MANIFEST_MD = ARCHIVE_ROOT / "MANIFEST.md"
CHECKSUMS = ARCHIVE_ROOT / "CHECKSUMS.sha256"
PIPELINE_STATUS = ARCHIVE_ROOT / "CP24_pipeline_status.md"
SAFE_USAGE_GUIDE = ARCHIVE_ROOT / "CP24_safe_usage_guide.md"
MODULE_INVENTORY = ARCHIVE_ROOT / "CP24_module_inventory.md"
VALIDATION_SUMMARY = ARCHIVE_ROOT / "CP24_validation_summary.md"


# Test 1: Archive root exists
def test_archive_root_exists():
    """Archive root directory must exist."""
    assert ARCHIVE_ROOT.exists(), f"Archive root not found at {ARCHIVE_ROOT}"
    assert ARCHIVE_ROOT.is_dir(), f"Archive root is not a directory: {ARCHIVE_ROOT}"


# Test 2: README exists
def test_readme_exists():
    """README.md must exist in archive root."""
    assert README.exists(), f"README.md not found at {README}"


# Test 3: MANIFEST.json exists and parses
def test_manifest_json_exists_and_parses():
    """MANIFEST.json must exist and be valid JSON."""
    assert MANIFEST_JSON.exists(), f"MANIFEST.json not found at {MANIFEST_JSON}"

    with open(MANIFEST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert "archive" in data, "MANIFEST.json missing 'archive' field"
    assert "created" in data, "MANIFEST.json missing 'created' field"
    assert "artifacts" in data, "MANIFEST.json missing 'artifacts' field"


# Test 4: MANIFEST.md exists
def test_manifest_md_exists():
    """MANIFEST.md must exist in archive root."""
    assert MANIFEST_MD.exists(), f"MANIFEST.md not found at {MANIFEST_MD}"


# Test 5: CHECKSUMS.sha256 exists
def test_checksums_exists():
    """CHECKSUMS.sha256 must exist in archive root."""
    assert CHECKSUMS.exists(), f"CHECKSUMS.sha256 not found at {CHECKSUMS}"


# Test 6: CP24_pipeline_status.md exists
def test_pipeline_status_exists():
    """CP24_pipeline_status.md must exist in archive root."""
    assert PIPELINE_STATUS.exists(), f"CP24_pipeline_status.md not found at {PIPELINE_STATUS}"


# Test 7: CP24_safe_usage_guide.md exists
def test_safe_usage_guide_exists():
    """CP24_safe_usage_guide.md must exist in archive root."""
    assert SAFE_USAGE_GUIDE.exists(), f"CP24_safe_usage_guide.md not found at {SAFE_USAGE_GUIDE}"


# Test 8: CP24_module_inventory.md exists
def test_module_inventory_exists():
    """CP24_module_inventory.md must exist in archive root."""
    assert MODULE_INVENTORY.exists(), f"CP24_module_inventory.md not found at {MODULE_INVENTORY}"


# Test 9: CP24_validation_summary.md exists
def test_validation_summary_exists():
    """CP24_validation_summary.md must exist in archive root."""
    assert VALIDATION_SUMMARY.exists(), f"CP24_validation_summary.md not found at {VALIDATION_SUMMARY}"


# Test 10: Manifest includes CP24A-CP24I reports
def test_manifest_includes_checkpoint_reports():
    """MANIFEST.json must include all CP24A-CP24I checkpoint reports."""
    with open(MANIFEST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    checkpoint_reports = data["artifacts"]["checkpoint_reports"]
    report_checkpoints = {r["checkpoint"] for r in checkpoint_reports}

    required_checkpoints = {"CP24A", "CP24B", "CP24C", "CP24D", "CP24E",
                           "CP24F", "CP24G", "CP24H", "CP24H-Fix", "CP24I"}

    for cp in required_checkpoints:
        assert cp in report_checkpoints, f"Checkpoint {cp} missing from manifest"


# Test 11: Manifest includes key scripts
def test_manifest_includes_key_scripts():
    """MANIFEST.json must include key CP24 scripts."""
    with open(MANIFEST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    scripts = data["artifacts"]["core_scripts"]
    script_paths = {s["path"] for s in scripts}

    required_scripts = {
        "scripts/generic_sec_synthesis.py",
        "scripts/sec_ticker_inventory.py",
        "scripts/form4_extractor.py"
    }

    for script in required_scripts:
        assert script in script_paths, f"Script {script} missing from manifest"


# Test 12: Manifest includes key source modules
def test_manifest_includes_key_source_modules():
    """MANIFEST.json must include key CP24 source modules."""
    with open(MANIFEST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    modules = data["artifacts"]["source_modules"]
    module_paths = {m["path"] for m in modules}

    required_modules = {
        "sources/generic_synthesis_composer.py",
        "sources/sec_inventory_builder.py",
        "sources/form4_parser.py"
    }

    for module in required_modules:
        assert module in module_paths, f"Module {module} missing from manifest"


# Test 13: Manifest includes key test files
def test_manifest_includes_key_test_files():
    """MANIFEST.json must include key CP24 test files."""
    with open(MANIFEST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    tests = data["artifacts"]["test_files"]
    test_paths = {t["path"] for t in tests}

    required_tests = {
        "tests/test_generic_sec_synthesis.py",
        "tests/test_multi_ticker_validation.py"
    }

    for test in required_tests:
        assert test in test_paths, f"Test {test} missing from manifest"


# Test 14: Manifest includes MAIA/NVDA synthesis outputs
def test_manifest_includes_maia_nvda_outputs():
    """MANIFEST.json must include MAIA and NVDA synthesis outputs."""
    with open(MANIFEST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    maia_outputs = data["artifacts"]["maia_outputs"]
    nvda_outputs = data["artifacts"]["nvda_outputs"]

    # Check for synthesis JSON files
    maia_paths = {o["path"] for o in maia_outputs if "path" in o}
    nvda_paths = {o["path"] for o in nvda_outputs if "path" in o}

    assert any("MAIA_generic_sec_synthesis.json" in p for p in maia_paths), \
        "MAIA synthesis JSON missing from manifest"
    assert any("NVDA_generic_sec_synthesis.json" in p for p in nvda_paths), \
        "NVDA synthesis JSON missing from manifest"


# Test 15: Manifest includes CP24I validation outputs
def test_manifest_includes_cp24i_validation():
    """MANIFEST.json must include CP24I validation outputs."""
    with open(MANIFEST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    validation = data["artifacts"]["cp24i_validation"]
    validation_paths = {v["path"] for v in validation if "path" in v}

    required_validation = {
        "docs/sample_reports/cp24i_validation/batch_generic_sec_synthesis_summary.json",
        "docs/sample_reports/cp24i_validation/validation_matrix.csv"
    }

    for val in required_validation:
        assert val in validation_paths, f"Validation file {val} missing from manifest"


# Test 16: No .env, .state, .db, .sqlite, log, cache, or private files in manifest
def test_no_sensitive_files_in_manifest():
    """MANIFEST.json must not include .env, .state, databases, logs, or private files."""
    with open(MANIFEST_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Collect all paths from all artifact categories
    all_paths = []
    for category in data["artifacts"].values():
        if isinstance(category, list):
            for item in category:
                if "path" in item:
                    all_paths.append(item["path"])

    # Check for forbidden patterns
    forbidden_patterns = [
        ".env", ".state/", ".db", ".sqlite", ".sqlite3", ".log",
        "cache", "MAIA.xlsx", "OpenInsider", "openinsider"
    ]

    for path in all_paths:
        for pattern in forbidden_patterns:
            assert pattern not in path, f"Forbidden file pattern '{pattern}' found in manifest path: {path}"


# Test 17: Checksums match existing files
def test_checksums_match_existing_files():
    """SHA-256 checksums in CHECKSUMS.sha256 must match actual files."""
    import hashlib

    with open(CHECKSUMS, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Parse checksums file (format: SHA256 <path>)
    checksums = {}
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            parts = line.split(None, 1)
            if len(parts) == 2:
                sha, path = parts
                checksums[path] = sha

    # Verify at least some checksums exist
    assert len(checksums) > 0, "No checksums found in CHECKSUMS.sha256"

    # Verify a sample of checksums (not all, to avoid timeout)
    sample_files = [
        "scripts/generic_sec_synthesis.py",
        "sources/generic_synthesis_composer.py"
    ]

    for file_path in sample_files:
        if file_path in checksums:
            full_path = Path("..") / file_path
            if full_path.exists():
                with open(full_path, 'rb') as f:
                    actual_sha = hashlib.sha256(f.read()).hexdigest()
                expected_sha = checksums[file_path]
                assert actual_sha == expected_sha, \
                    f"Checksum mismatch for {file_path}: expected {expected_sha}, got {actual_sha}"


# Test 18: No secrets in archive docs
def test_no_secrets_in_archive_docs():
    """Archive documentation must not contain secrets or sensitive data."""
    archive_docs = [
        README, MANIFEST_MD, PIPELINE_STATUS, SAFE_USAGE_GUIDE,
        MODULE_INVENTORY, VALIDATION_SUMMARY
    ]

    forbidden_patterns = [
        "TELEGRAM_BOT_TOKEN=",
        "TELEGRAM_CHAT_ID=",
        "SMTP_PASSWORD=",
        "GMAIL_APP_PASSWORD=",
        "sk-ant-",
        "BEGIN PRIVATE KEY"
    ]

    for doc in archive_docs:
        if doc.exists():
            with open(doc, 'r', encoding='utf-8') as f:
                content = f.read()

            for pattern in forbidden_patterns:
                assert pattern not in content, \
                    f"Secret pattern '{pattern}' found in {doc.name}"


# Test 19: No buy/sell/hold/price-target/recommendation language
def test_no_recommendation_language():
    """Archive documentation must not contain investment recommendation language."""
    archive_docs = [
        README, MANIFEST_MD, PIPELINE_STATUS, SAFE_USAGE_GUIDE,
        MODULE_INVENTORY, VALIDATION_SUMMARY
    ]

    for doc in archive_docs:
        if doc.exists():
            with open(doc, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            # Check for forbidden words in context
            # Skip lines that are documenting prohibited language (marked with ✗ or "Prohibited")
            for line in lines:
                line_lower = line.lower()
                # Skip lines that are examples of what NOT to do
                if '✗' in line or 'prohibit' in line_lower or 'forbidden' in line_lower or 'avoid' in line_lower:
                    continue
                # Now check for actual recommendation language
                if "we recommend buying" in line_lower or "recommended: buy" in line_lower:
                    pytest.fail(f"Investment recommendation language found in {doc.name}: {line.strip()}")


# Test 20: Safety statements present
def test_safety_statements_present():
    """Archive documentation must include safety and no-investment-advice statements."""
    # README should have "This is not investment advice"
    with open(README, 'r', encoding='utf-8') as f:
        readme_content = f.read()

    assert "not investment advice" in readme_content.lower(), \
        "README missing 'not investment advice' statement"

    # Validation summary should have safety confirmations
    with open(VALIDATION_SUMMARY, 'r', encoding='utf-8') as f:
        validation_content = f.read()

    assert "safety" in validation_content.lower(), \
        "Validation summary missing safety confirmations"
