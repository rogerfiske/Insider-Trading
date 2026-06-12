"""
Manual SEC Synthesis CLI Tool

Command-line interface for running manual ticker SEC synthesis using the
approved CP24 generic SEC pipeline in report-only mode.

Usage:
    python scripts/manual_sec_synthesis.py --ticker MAIA
    python scripts/manual_sec_synthesis.py --tickers MAIA,NVDA --mode synthesis-only
    python scripts/manual_sec_synthesis.py --tickers AAPL,MSFT,TSLA --mode inventory-first

This tool operates in report-only mode with no alert/notification code paths.
"""

import argparse
import sys
from pathlib import Path

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.manual_sec_synthesis_runner import ManualSECSynthesisRunner


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run manual ticker SEC synthesis using CP24 generic SEC pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Synthesis-only mode (no network, uses existing local outputs)
  python scripts/manual_sec_synthesis.py --ticker MAIA --mode synthesis-only

  # Inventory-first mode (lightweight, safe for broad ticker lists)
  python scripts/manual_sec_synthesis.py --tickers AAPL,MSFT,TSLA --mode inventory-first

  # Full mode (run all available modules)
  python scripts/manual_sec_synthesis.py --ticker MAIA --mode full --lookback-days 730

Safety:
  This command operates in report-only mode. It does not send alerts, Telegram
  messages, or email. It does not modify scheduled tasks or .env files.
        """
    )

    # Ticker arguments (mutually exclusive)
    ticker_group = parser.add_mutually_exclusive_group(required=True)
    ticker_group.add_argument(
        "--ticker",
        type=str,
        help="Single ticker symbol to process"
    )
    ticker_group.add_argument(
        "--tickers",
        type=str,
        help="Comma-separated list of ticker symbols to process"
    )

    # Mode argument
    parser.add_argument(
        "--mode",
        type=str,
        default="synthesis-only",
        choices=["full", "inventory-first", "synthesis-only"],
        help="Run mode (default: synthesis-only)"
    )

    # Output arguments
    parser.add_argument(
        "--output-root",
        type=str,
        default="docs/sample_reports/manual_sec_synthesis_runs",
        help="Output root directory (default: docs/sample_reports/manual_sec_synthesis_runs)"
    )
    parser.add_argument(
        "--run-name",
        type=str,
        help="Optional custom run name for output folder"
    )

    # Module parameters
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=1460,
        help="Form 4 lookback period in days (default: 1460)"
    )
    parser.add_argument(
        "--max-form4-filings",
        type=int,
        help="Optional maximum number of Form 4 filings to process"
    )
    parser.add_argument(
        "--skip-13f",
        action="store_true",
        help="Skip 13F institutional ownership module"
    )

    # Execution parameters
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse existing module outputs when available"
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Operate in offline mode (synthesis-only mode only)"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first module failure"
    )

    args = parser.parse_args()

    # Parse tickers
    if args.ticker:
        tickers = [args.ticker.upper()]
    else:
        tickers = [t.strip().upper() for t in args.tickers.split(",")]

    # Validate tickers
    if not tickers:
        print("Error: No tickers specified", file=sys.stderr)
        sys.exit(1)

    # Validate mode compatibility
    if args.no_network and args.mode != "synthesis-only":
        print("Error: --no-network only valid with --mode synthesis-only", file=sys.stderr)
        sys.exit(1)

    # Initialize runner
    output_root = Path(args.output_root)
    runner = ManualSECSynthesisRunner(output_root=output_root)

    print("=" * 80)
    print("Manual SEC Synthesis Command")
    print("=" * 80)
    print(f"Mode: {args.mode}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Output root: {output_root}")
    print(f"Run name: {args.run_name or '(auto-generated)'}")
    print()
    print("Safety: Report-only mode (no alerts, Telegram, email, or scheduled tasks)")
    print("=" * 80)
    print()

    # Create run folder
    run_folder = runner.create_run_folder(run_name=args.run_name, tickers=tickers)
    run_id = run_folder.name

    print(f"Run folder: {run_folder}")
    print()

    # Process tickers based on mode
    ticker_results = {}

    for ticker in tickers:
        print(f"Processing {ticker} (mode: {args.mode})...")

        if args.mode == "synthesis-only":
            result = runner.run_ticker_synthesis_only_mode(ticker, run_folder)
        elif args.mode == "inventory-first":
            result = runner.run_ticker_inventory_first_mode(ticker, run_folder)
        elif args.mode == "full":
            result = runner.run_ticker_full_mode(
                ticker,
                run_folder,
                lookback_days=args.lookback_days,
                max_form4_filings=args.max_form4_filings,
                skip_13f=args.skip_13f,
                fail_fast=args.fail_fast
            )
        else:
            print(f"Error: Unknown mode '{args.mode}'", file=sys.stderr)
            sys.exit(1)

        ticker_results[ticker] = result

        print(f"  Status: {result['status']}")
        if result.get("degraded"):
            print(f"  Degraded: Yes")
            for reason in result.get("degraded_reasons", []):
                print(f"    - {reason}")
        print()

    # Create run outputs
    print("Creating run outputs...")

    # Run manifest
    manifest_path = runner.create_run_manifest(
        run_folder,
        run_id,
        tickers,
        args.mode,
        ticker_results
    )
    print(f"  Created: {manifest_path}")

    # Safety audit
    audit_path = runner.create_safety_audit(
        run_folder,
        args.mode,
        tickers
    )
    print(f"  Created: {audit_path}")

    # Validation matrix
    matrix_path = runner.create_validation_matrix(
        run_folder,
        ticker_results
    )
    print(f"  Created: {matrix_path}")

    # Run summary
    json_path, md_path = runner.create_run_summary(
        run_folder,
        run_id,
        args.mode,
        tickers,
        ticker_results
    )
    print(f"  Created: {json_path}")
    print(f"  Created: {md_path}")

    print()
    print("=" * 80)
    print("Run complete!")
    print("=" * 80)
    print(f"Run ID: {run_id}")
    print(f"Run folder: {run_folder}")
    print()

    # Summary
    completed = [t for t, r in ticker_results.items() if r["status"] == "completed"]
    degraded = [t for t, r in ticker_results.items() if r.get("degraded", False)]
    failed = [t for t, r in ticker_results.items() if r["status"] == "failed"]

    print(f"Tickers completed: {len(completed)} / {len(tickers)}")
    if degraded:
        print(f"Tickers degraded: {len(degraded)} ({', '.join(degraded)})")
    if failed:
        print(f"Tickers failed: {len(failed)} ({', '.join(failed)})")

    print()
    print("Review outputs:")
    print(f"  Summary: {md_path}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Validation matrix: {matrix_path}")
    print(f"  Safety audit: {audit_path}")
    print()

    print("This is not investment advice. Perform your own due diligence.")
    print("=" * 80)

    # Exit with appropriate code
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
