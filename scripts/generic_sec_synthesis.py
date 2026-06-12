"""
Generic SEC Synthesis CLI Tool

Command-line interface for composing generic SEC-only synthesis packets
from CP24B-CP24G extraction outputs.

Usage:
    python scripts/generic_sec_synthesis.py --ticker MAIA --output-dir docs/sample_reports/generic_synthesis/MAIA
    python scripts/generic_sec_synthesis.py --tickers MAIA,NVDA --output-dir docs/sample_reports/generic_synthesis/batch_maia_nvda

This tool operates in report-only mode with no alert/notification code paths.
"""

import argparse
import sys
from pathlib import Path

# Add sources to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.generic_synthesis_composer import GenericSynthesisComposer


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compose generic SEC synthesis packets from CP24B-CP24G outputs"
    )

    # Ticker arguments
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

    # Input/output arguments
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for synthesis reports"
    )
    parser.add_argument(
        "--input-root",
        type=str,
        default="docs/sample_reports",
        help="Root directory for CP24B-CP24G JSON outputs (default: docs/sample_reports)"
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Operate in offline mode (no network required)"
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

    # Initialize composer
    input_root = Path(args.input_root)
    output_dir = Path(args.output_dir)

    if not input_root.exists():
        print(f"Error: Input root does not exist: {input_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Generic SEC Synthesis Composer")
    print(f"Input root: {input_root}")
    print(f"Output dir: {output_dir}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"No-network mode: {args.no_network}")
    print()

    composer = GenericSynthesisComposer(input_root=input_root)

    # Process each ticker
    syntheses = {}

    for ticker in tickers:
        print(f"Processing {ticker}...")

        try:
            # Compose synthesis
            synthesis = composer.compose_synthesis(ticker)

            # Determine ticker output directory
            if len(tickers) == 1:
                # Single ticker mode: use output_dir directly
                ticker_output_dir = output_dir
            else:
                # Batch mode: create per-ticker subdirectory
                ticker_output_dir = output_dir / ticker

            # Write outputs
            composer.write_synthesis_outputs(ticker, synthesis, ticker_output_dir)

            syntheses[ticker] = synthesis

            print(f"  SUCCESS: {ticker} synthesis complete")
            print(f"    JSON: {ticker_output_dir / f'{ticker}_generic_sec_synthesis.json'}")
            print(f"    Markdown: {ticker_output_dir / f'{ticker}_generic_sec_synthesis.md'}")
            print(f"    Evidence CSV: {ticker_output_dir / f'{ticker}_evidence_matrix.csv'}")
            print()

        except Exception as e:
            print(f"  ERROR: {ticker} synthesis failed: {e}", file=sys.stderr)
            print()

    # Write batch summary if multiple tickers
    if len(tickers) > 1:
        print("Writing batch summary...")

        try:
            batch_summary = composer.compose_batch_summary(tickers, syntheses)
            composer.write_batch_summary_outputs(batch_summary, output_dir)

            print(f"  SUCCESS: Batch summary complete")
            print(f"    JSON: {output_dir / 'batch_generic_sec_synthesis_summary.json'}")
            print(f"    Markdown: {output_dir / 'batch_generic_sec_synthesis_summary.md'}")
            print()

        except Exception as e:
            print(f"  ERROR: Batch summary failed: {e}", file=sys.stderr)
            print()

    # Summary
    success_count = len(syntheses)
    failure_count = len(tickers) - success_count

    print("="*60)
    print(f"Synthesis complete: {success_count}/{len(tickers)} successful")

    if failure_count > 0:
        print(f"Failed: {failure_count}")
        sys.exit(1)

    print("="*60)


if __name__ == "__main__":
    main()
