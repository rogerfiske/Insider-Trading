"""Safety boundary tests for watchlist scoring."""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from watchlist.scoring import compute_insider_evidence_score


def test_scoring_does_not_send_alerts():
    """Test that scoring module does not trigger Telegram or email alerts."""
    # Scoring is a pure computation module with no I/O side effects
    # It should never import or call alert modules

    import watchlist.scoring as scoring_module
    import inspect

    source = inspect.getsource(scoring_module)

    # Should not import alert modules
    forbidden_imports = [
        "from alerts.",
        "import alerts",
        "from alert_routing",
        "import alert_routing",
        "telegram",
        "smtp",
    ]

    for forbidden in forbidden_imports:
        assert forbidden.lower() not in source.lower(), f"Scoring module should not import {forbidden}"


def test_scoring_does_not_read_spreadsheet():
    """Test that scoring module does not read Roger's spreadsheet."""
    import watchlist.scoring as scoring_module
    import inspect

    source = inspect.getsource(scoring_module)

    # Should not reference spreadsheet paths or operations
    forbidden_patterns = [
        "OpenInsider",
        "spreadsheet",
        ".xlsx",
        ".csv",
        "pd.read_",
        "openpyxl",
    ]

    for pattern in forbidden_patterns:
        assert pattern not in source, f"Scoring module should not reference {pattern}"


def test_scoring_does_not_access_secrets():
    """Test that scoring module does not access environment secrets."""
    import watchlist.scoring as scoring_module
    import inspect

    source = inspect.getsource(scoring_module)

    # Should not access secret environment variables
    forbidden_secrets = [
        "TELEGRAM_BOT_TOKEN",
        "SMTP_PASSWORD",
        "GMAIL_APP_PASSWORD",
        "os.getenv",
        "os.environ",
    ]

    for secret in forbidden_secrets:
        assert secret not in source, f"Scoring module should not access {secret}"


def test_scoring_does_not_write_files():
    """Test that scoring module does not write to filesystem."""
    import watchlist.scoring as scoring_module
    import inspect

    source = inspect.getsource(scoring_module)

    # Should not write files
    forbidden_io = [
        "open(",
        "write(",
        "Path.write",
        "with open",
    ]

    # Allow reading for inspection but not writing
    for pattern in forbidden_io:
        if pattern in source:
            # If 'open' is present, verify it's not in write mode
            if "open(" in source:
                assert "'w'" not in source and '"w"' not in source, "Scoring should not open files in write mode"


def test_scoring_does_not_modify_database():
    """Test that scoring module does not perform database writes."""
    import watchlist.scoring as scoring_module
    import inspect

    source = inspect.getsource(scoring_module)

    # Should not perform database operations
    forbidden_db = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "CREATE TABLE",
        "DROP TABLE",
        ".commit()",
        ".execute(",
    ]

    for pattern in forbidden_db:
        assert pattern not in source, f"Scoring module should not perform {pattern}"


def test_scoring_is_pure_computation():
    """Test that scoring functions are pure (no side effects)."""
    # Pure functions should:
    # 1. Return deterministic output for same input
    # 2. Not modify input
    # 3. Not have observable side effects

    metrics = {
        "ticker": "PURE",
        "purchase_value": 100000.0,
        "sale_value": 0.0,
        "purchase_count": 10,
        "sale_count": 0,
        "form4_filings_found": 30,
        "form4_filings_parsed": 28,
    }

    # Create copy to verify no mutation
    import copy
    metrics_copy = copy.deepcopy(metrics)

    score = compute_insider_evidence_score("PURE", metrics)

    # Input should not be modified
    assert metrics == metrics_copy

    # Same input should produce same output
    score2 = compute_insider_evidence_score("PURE", metrics)
    assert score.total_score == score2.total_score
    assert score.rating_label == score2.rating_label


def test_scoring_handles_missing_data_safely():
    """Test that scoring handles missing data without crashing."""
    # Missing optional fields should not raise exceptions
    minimal_metrics = {
        "ticker": "SAFE",
        "purchase_value": 50000.0,
        "sale_value": 0.0,
        "purchase_count": 5,
        "sale_count": 0,
        "form4_filings_found": 20,
        "form4_filings_parsed": 18,
        # Missing: distinct_buyers, latest_purchase_date, buyer_roles, purchase_months
    }

    # Should not raise exception
    score = compute_insider_evidence_score("SAFE", minimal_metrics)

    # Should produce valid score
    assert score.ticker == "SAFE"
    assert 0 <= score.total_score <= 100

    # Should have warnings about missing fields
    assert len(score.warnings) > 0


def test_scoring_handles_none_values_safely():
    """Test that scoring handles None values without crashing."""
    metrics = {
        "ticker": "NONE",
        "purchase_value": None,
        "sale_value": None,
        "purchase_count": 0,
        "sale_count": 0,
        "distinct_buyers": None,
        "latest_purchase_date": None,
        "buyer_roles": None,
        "purchase_months": None,
        "form4_filings_found": 0,
        "form4_filings_parsed": 0,
    }

    # Should not raise exception
    score = compute_insider_evidence_score("NONE", metrics)

    # Should produce zero or very low score
    assert score.ticker == "NONE"
    assert score.total_score >= 0


def test_scoring_does_not_consume_network():
    """Test that scoring does not make network requests."""
    import watchlist.scoring as scoring_module
    import inspect

    source = inspect.getsource(scoring_module)

    # Should not make HTTP requests
    forbidden_network = [
        "requests.",
        "urllib.",
        "http.",
        "socket.",
        "requests.get",
        "requests.post",
    ]

    for pattern in forbidden_network:
        assert pattern not in source, f"Scoring module should not use {pattern}"


def test_scoring_does_not_import_sec_connectors():
    """Test that scoring does not directly call SEC connectors."""
    import watchlist.scoring as scoring_module
    import inspect

    source = inspect.getsource(scoring_module)

    # Should not import SEC data fetching modules
    forbidden_imports = [
        "from connectors.sec_form4",
        "from connectors.sec_13f",
        "import sec_form4",
        "import sec_13f",
    ]

    for pattern in forbidden_imports:
        assert pattern not in source, f"Scoring module should not import {pattern}"


def test_scoring_module_has_no_global_state():
    """Test that scoring module does not use global mutable state."""
    import watchlist.scoring as scoring_module

    # Get all module-level variables
    module_vars = vars(scoring_module)

    # Check for potentially dangerous global state
    for name, value in module_vars.items():
        # Skip imports, functions, classes, and dunder attributes
        if name.startswith("_") or callable(value) or isinstance(value, type):
            continue

        # Remaining globals should be constants (immutable)
        if isinstance(value, (list, dict, set)):
            # Mutable globals are dangerous for pure computation
            # Only allow empty defaults or frozen structures
            if value:
                # If non-empty, should be documented as constant
                assert name.isupper(), f"Mutable global {name} should be UPPER_CASE constant"


def test_scoring_does_not_use_subprocess():
    """Test that scoring does not spawn subprocesses."""
    import watchlist.scoring as scoring_module
    import inspect

    source = inspect.getsource(scoring_module)

    # Should not spawn subprocesses
    forbidden_subprocess = [
        "subprocess.",
        "os.system",
        "os.popen",
        "Popen",
    ]

    for pattern in forbidden_subprocess:
        assert pattern not in source, f"Scoring module should not use {pattern}"


def test_scoring_does_not_use_threads():
    """Test that scoring does not create threads or async tasks."""
    import watchlist.scoring as scoring_module
    import inspect

    source = inspect.getsource(scoring_module)

    # Should not use threading or async
    forbidden_concurrency = [
        "threading.",
        "Thread(",
        "multiprocessing.",
        "Process(",
        "asyncio.",
        "async def",
        "await ",
    ]

    for pattern in forbidden_concurrency:
        assert pattern not in source, f"Scoring module should not use {pattern}"


def test_scoring_only_imports_safe_modules():
    """Test that scoring only imports safe standard library modules."""
    import watchlist.scoring as scoring_module

    # Get actual imports from module
    import_names = [name for name in dir(scoring_module) if not name.startswith("_")]

    # Allowed safe imports
    allowed_prefixes = [
        "dataclass",  # dataclasses
        "field",  # dataclasses
        "datetime",  # datetime
        "timezone",  # datetime
        "Any",  # typing
        "compute_",  # own functions
        "get_",  # own functions
        "Insider",  # own classes
    ]

    # Check each non-dunder name
    for name in import_names:
        if callable(getattr(scoring_module, name)) or isinstance(getattr(scoring_module, name), type):
            # It's a function or class - check if it's allowed
            is_allowed = any(name.startswith(prefix) for prefix in allowed_prefixes)
            assert is_allowed or name.isupper(), f"Unexpected import or definition: {name}"
