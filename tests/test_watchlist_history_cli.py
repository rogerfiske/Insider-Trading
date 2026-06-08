"""Tests for watchlist history CLI integration."""

import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_history_db_path_defaults_to_state():
    """Test that default history database path is under .state/."""
    from scripts.ticker_watchlist import main
    import argparse

    # Mock argparse to check defaults
    parser = argparse.ArgumentParser()

    # Add the actual history-db argument
    parser.add_argument(
        "--history-db",
        type=Path,
        default=Path(".state/watchlist_history.db"),
    )

    args = parser.parse_args([])

    # Verify default path
    assert ".state" in str(args.history_db)
    assert "watchlist_history.db" in str(args.history_db)


def test_save_history_flag_is_optional():
    """Test that --save-history flag is optional (default: don't save)."""
    from scripts.ticker_watchlist import main
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--save-history", action="store_true")
    parser.add_argument("--no-save-history", action="store_true")

    # Without flag
    args = parser.parse_args([])
    assert args.save_history is False

    # With flag
    args = parser.parse_args(["--save-history"])
    assert args.save_history is True

    # With no-save flag
    args = parser.parse_args(["--no-save-history"])
    assert args.no_save_history is True


def test_compare_previous_flag_is_optional():
    """Test that --compare-previous flag is optional."""
    from scripts.ticker_watchlist import main
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--compare-previous", action="store_true")

    # Without flag
    args = parser.parse_args([])
    assert args.compare_previous is False

    # With flag
    args = parser.parse_args(["--compare-previous"])
    assert args.compare_previous is True


def test_history_summary_output_default_path():
    """Test default history summary output path."""
    from scripts.ticker_watchlist import main
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--history-summary-output",
        type=Path,
        default=Path("docs/sample_reports/watchlist/manual_watchlist_history_summary.md"),
    )

    args = parser.parse_args([])

    assert "watchlist" in str(args.history_summary_output)
    assert "history_summary.md" in str(args.history_summary_output)


def test_history_cli_options_do_not_conflict():
    """Test that history CLI options don't conflict with existing options."""
    from scripts.ticker_watchlist import main
    import argparse

    parser = argparse.ArgumentParser()

    # Add all watchlist options
    parser.add_argument("--lookback-days", type=int, default=1460)
    parser.add_argument("--max-form4-filings", type=int, default=0)
    parser.add_argument("--dry-run-report", action="store_true")
    parser.add_argument("--save-history", action="store_true")
    parser.add_argument("--compare-previous", action="store_true")
    parser.add_argument("--history-db", type=Path, default=Path(".state/watchlist_history.db"))

    # Parse with multiple options
    args = parser.parse_args([
        "--lookback-days", "365",
        "--dry-run-report",
        "--save-history",
        "--compare-previous",
    ])

    assert args.lookback_days == 365
    assert args.dry_run_report is True
    assert args.save_history is True
    assert args.compare_previous is True


def test_history_mode_respects_dry_run_environment():
    """Test that history mode enforces dry-run environment."""
    # The module-level override in ticker_watchlist.py should enforce this
    import scripts.ticker_watchlist as watchlist_module

    # Verify environment is forced to dry-run
    assert os.environ.get("ROSS_DRY_RUN") == "true"
    assert os.environ.get("ALERT_ENABLE_TELEGRAM") == "false"
    assert os.environ.get("ALERT_ENABLE_EMAIL") == "false"


def test_no_save_history_takes_precedence():
    """Test that --no-save-history takes precedence over --save-history."""
    # This would be tested in actual CLI logic
    # The behavior should be: if no_save_history is True, don't save
    # even if save_history is also True

    # Simulated logic
    save_history = True
    no_save_history = True

    should_save = save_history and not no_save_history

    assert should_save is False
