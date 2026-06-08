#!/usr/bin/env python3
"""
Ticker Watchlist Helper -- Manual watchlist research for multiple tickers.

Usage:
    python scripts/ticker_watchlist.py --tickers MAIA ABCD XYZ --dry-run-report
    python scripts/ticker_watchlist.py --tickers-file config/watchlists/manual_tickers.example.txt --dry-run-report

Generates per-ticker reports, consolidated summary, and JSON output for watchlist analysis.

Safety:
  - Runs in dry-run mode (no alerts sent)
  - Does not consume daily production guard
  - Does not modify scheduled tasks
  - Does not use uploaded spreadsheets
  - Uses only existing project connectors
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# SAFETY: Force dry-run mode for manual watchlist research
# This ensures watchlist mode can never send Telegram/email
os.environ["ROSS_DRY_RUN"] = "true"
os.environ["ALERT_ENABLE_TELEGRAM"] = "false"
os.environ["ALERT_ENABLE_EMAIL"] = "false"

from scripts.ticker_drilldown import generate_ticker_report
from sources.sec_ticker import SecTickerResolver
from sources.sec_common import utcnow_iso


def normalize_tickers(tickers: list[str]) -> list[str]:
    """Normalize ticker symbols: uppercase, strip whitespace, remove duplicates.

    Args:
        tickers: List of raw ticker symbols

    Returns:
        List of normalized tickers (deduplicated, preserving order)
    """
    seen = set()
    normalized = []

    for ticker in tickers:
        # Normalize: uppercase, strip whitespace
        normalized_ticker = ticker.strip().upper()

        # Skip empty or invalid-looking symbols
        if not normalized_ticker:
            continue
        if not normalized_ticker.replace("-", "").replace(".", "").isalnum():
            print(f"[WARNING] Skipping invalid ticker symbol: {ticker}")
            continue

        # Remove duplicates while preserving order
        if normalized_ticker not in seen:
            seen.add(normalized_ticker)
            normalized.append(normalized_ticker)

    return normalized


def load_tickers_from_file(file_path: Path) -> list[str]:
    """Load tickers from a text file (one per line, # for comments).

    Args:
        file_path: Path to ticker file

    Returns:
        List of ticker symbols
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Ticker file not found: {file_path}")

    tickers = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Strip comments and whitespace
            line = line.split("#")[0].strip()
            if line:
                tickers.append(line)

    return tickers


def extract_ticker_metrics(report_content: str, ticker: str) -> dict[str, Any]:
    """Extract key metrics from ticker report for JSON output.

    Args:
        report_content: Markdown report content
        ticker: Ticker symbol

    Returns:
        Dictionary of metrics
    """
    # Parse key metrics from report
    # This is a simple extraction - in production you'd use the structured results
    metrics = {
        "ticker": ticker,
        "cik": None,
        "company_name": None,
        "eddie_status": "UNKNOWN",
        "eddie_signal": "NEUTRAL",
        "eddie_confidence": 0,
        "maggie_status": "UNKNOWN",
        "maggie_signal": "NEUTRAL",
        "maggie_confidence": 0,
        "form4_filings_found": 0,
        "form4_filings_parsed": 0,
        "transactions_extracted": 0,
        "purchase_count": 0,
        "purchase_value": 0.0,
        "sale_count": 0,
        "sale_value": 0.0,
        "net_purchase_value": 0.0,
        "distinct_buyers": 0,
        "latest_purchase_date": None,
    }

    # Extract CIK from report (format: "CIK: 0001878313")
    for line in report_content.split("\n"):
        if line.startswith("**CIK**:"):
            metrics["cik"] = line.split(":", 1)[1].strip()
        elif line.startswith("**Company Name**:"):
            metrics["company_name"] = line.split(":", 1)[1].strip()
        elif "| Eddie |" in line:
            # Parse Eddie row: | Eddie | STATUS | ... | SIGNAL | CONFIDENCE | ...
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 6:
                metrics["eddie_status"] = parts[2]
                metrics["eddie_signal"] = parts[4]
                try:
                    metrics["eddie_confidence"] = int(parts[5])
                except (ValueError, IndexError):
                    pass
        elif "| Maggie |" in line:
            # Parse Maggie row
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 6:
                metrics["maggie_status"] = parts[2]
                metrics["maggie_signal"] = parts[4]
                try:
                    metrics["maggie_confidence"] = int(parts[5])
                except (ValueError, IndexError):
                    pass
        elif "Found:" in line and "Form 4 filings" in line:
            # Parse: "- Found: 214 Form 4 filings"
            try:
                metrics["form4_filings_found"] = int(line.split(":")[1].split()[0])
            except (ValueError, IndexError):
                pass
        elif "Parsed:" in line and "Form 4" in line:
            try:
                metrics["form4_filings_parsed"] = int(line.split(":")[1].split()[0])
            except (ValueError, IndexError):
                pass
        elif "Transactions:" in line:
            try:
                metrics["transactions_extracted"] = int(line.split(":")[1].split()[0])
            except (ValueError, IndexError):
                pass
        elif "Open-market purchases:" in line:
            # Parse: "- Open-market purchases: 134 transaction(s), $4,921,437.58"
            try:
                # Split by ":" first to get the value part
                value_part = line.split(":", 1)[1].strip()
                # Extract count (first number before "transaction")
                count_str = value_part.split("transaction")[0].strip()
                metrics["purchase_count"] = int(count_str)
                # Extract value (find $ and get everything after it until end of numbers/commas/dots)
                if "$" in value_part:
                    value_str = value_part.split("$")[1].strip().split()[0]
                    metrics["purchase_value"] = float(value_str.replace(",", ""))
                    metrics["net_purchase_value"] = metrics["purchase_value"]
            except (ValueError, IndexError):
                pass
        elif "Open-market sales:" in line:
            try:
                value_part = line.split(":", 1)[1].strip()
                count_str = value_part.split("transaction")[0].strip()
                metrics["sale_count"] = int(count_str)
                if "$" in value_part:
                    value_str = value_part.split("$")[1].strip().split()[0]
                    metrics["sale_value"] = float(value_str.replace(",", ""))
                    metrics["net_purchase_value"] = metrics["purchase_value"] - metrics["sale_value"]
            except (ValueError, IndexError):
                pass

    return metrics


def rank_tickers(ticker_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank tickers by insider evidence strength.

    Ranking priority:
    1. Eddie signal (BULLISH_EVIDENCE > NEUTRAL > BEARISH_EVIDENCE)
    2. Net purchase value (higher is better)
    3. Purchase count (higher is better)
    4. Latest purchase date (more recent is better)

    Args:
        ticker_metrics: List of ticker metric dictionaries

    Returns:
        Sorted list of ticker metrics
    """
    def signal_score(signal: str) -> int:
        """Convert signal to numeric score for sorting."""
        if signal == "BULLISH_EVIDENCE":
            return 3
        elif signal == "NEUTRAL":
            return 2
        elif signal == "BEARISH_EVIDENCE":
            return 1
        else:
            return 0

    def rank_key(metrics: dict[str, Any]) -> tuple:
        """Generate sort key for ranking."""
        return (
            -signal_score(metrics["eddie_signal"]),  # Negate for descending
            -metrics["net_purchase_value"],  # Higher is better
            -metrics["purchase_count"],  # Higher is better
            -metrics["form4_filings_parsed"],  # More data is better
        )

    return sorted(ticker_metrics, key=rank_key)


def generate_markdown_summary(
    ticker_metrics: list[dict[str, Any]],
    lookback_days: int,
    max_form4_filings: int,
    tickers_requested: int,
    tickers_resolved: int,
    tickers_failed: int,
) -> str:
    """Generate consolidated markdown watchlist summary.

    Args:
        ticker_metrics: Ranked list of ticker metrics
        lookback_days: Lookback window in days
        max_form4_filings: Max Form 4 filings per ticker
        tickers_requested: Number of tickers requested
        tickers_resolved: Number successfully resolved
        tickers_failed: Number that failed

    Returns:
        Markdown summary content
    """
    now = utcnow_iso()

    summary = [
        "# Manual Ticker Watchlist Summary",
        "",
        f"**Generated**: {now}",
        f"**Mode**: DRY-RUN — No Telegram or email was sent. This report is for analysis only.",
        "",
        "## Configuration",
        "",
        f"- **Lookback Days**: {lookback_days}",
        f"- **Max Form 4 Filings**: {'Unlimited' if max_form4_filings == 0 else max_form4_filings}",
        f"- **Tickers Requested**: {tickers_requested}",
        f"- **Tickers Resolved**: {tickers_resolved}",
        f"- **Tickers Failed**: {tickers_failed}",
        "",
        "## Data Sources",
        "",
        "- SEC EDGAR API",
        "- Project connectors (SEC Form 4, SEC 13F)",
        "- **Roger's OpenInsider spreadsheet was not used**",
        "",
        "## Ranked Watchlist",
        "",
        "Tickers ranked by insider buying evidence strength:",
        "",
        "| Rank | Ticker | Company | Eddie Signal | Confidence | Purchases | Purchase Value | Sales | Net Value |",
        "|------|--------|---------|--------------|------------|-----------|----------------|-------|-----------|",
    ]

    for rank, metrics in enumerate(ticker_metrics, 1):
        company_short = (metrics["company_name"] or "Unknown")[:30]
        summary.append(
            f"| {rank} | {metrics['ticker']} | {company_short} | "
            f"{metrics['eddie_signal']} | {metrics['eddie_confidence']} | "
            f"{metrics['purchase_count']} | ${metrics['purchase_value']:,.2f} | "
            f"{metrics['sale_count']} | ${metrics['net_purchase_value']:,.2f} |"
        )

    summary.extend([
        "",
        "## Per-Ticker Reports",
        "",
    ])

    for metrics in ticker_metrics:
        summary.append(f"- [{metrics['ticker']}](./watchlist/{metrics['ticker']}_manual_ticker_report.md)")

    summary.extend([
        "",
        "## Ranking Method",
        "",
        "Tickers are ranked by:",
        "",
        "1. **Eddie Signal**: BULLISH_EVIDENCE > NEUTRAL > BEARISH_EVIDENCE",
        "2. **Net Purchase Value**: Higher insider buying value ranks higher",
        "3. **Purchase Count**: More purchase transactions rank higher",
        "4. **Data Completeness**: More Form 4 filings parsed ranks higher",
        "",
        "## Safety Confirmations",
        "",
        "- ✅ No Telegram messages sent",
        "- ✅ No email sent",
        "- ✅ Roger's OpenInsider spreadsheet not used",
        "- ✅ Data sourced from SEC EDGAR only",
        "",
        "## Disclaimer",
        "",
        "**This analysis is informational only and is not trading advice.**",
        "",
        "Insider transactions can occur for many reasons unrelated to stock price expectations. "
        "This report presents SEC filing data for research purposes only. "
        "Do not use this information as the sole basis for investment decisions.",
        "",
    ])

    return "\n".join(summary)


def generate_json_output(
    ticker_metrics: list[dict[str, Any]],
    lookback_days: int,
    max_form4_filings: int,
) -> dict[str, Any]:
    """Generate machine-readable JSON output.

    Args:
        ticker_metrics: Ranked list of ticker metrics
        lookback_days: Lookback window in days
        max_form4_filings: Max Form 4 filings per ticker

    Returns:
        JSON-serializable dictionary
    """
    return {
        "generated_at": utcnow_iso(),
        "mode": "manual_watchlist_dry_run",
        "lookback_days": lookback_days,
        "max_form4_filings": max_form4_filings,
        "data_sources": ["SEC EDGAR", "project connectors"],
        "alerts_sent": False,
        "tickers": [
            {
                "ticker": m["ticker"],
                "cik": m["cik"],
                "company_name": m["company_name"],
                "eddie_status": m["eddie_status"],
                "eddie_signal": m["eddie_signal"],
                "eddie_confidence": m["eddie_confidence"],
                "maggie_status": m["maggie_status"],
                "maggie_signal": m["maggie_signal"],
                "maggie_confidence": m["maggie_confidence"],
                "form4_filings_found": m["form4_filings_found"],
                "form4_filings_parsed": m["form4_filings_parsed"],
                "transactions_extracted": m["transactions_extracted"],
                "purchase_count": m["purchase_count"],
                "purchase_value": m["purchase_value"],
                "sale_count": m["sale_count"],
                "sale_value": m["sale_value"],
                "net_purchase_value": m["net_purchase_value"],
                "report_path": f"docs/sample_reports/watchlist/{m['ticker']}_manual_ticker_report.md",
            }
            for m in ticker_metrics
        ],
    }


def main():
    """Main watchlist execution."""
    parser = argparse.ArgumentParser(
        description="Manual ticker watchlist research tool"
    )

    # Ticker input methods
    ticker_group = parser.add_mutually_exclusive_group(required=True)
    ticker_group.add_argument(
        "--tickers",
        nargs="+",
        help="One or more ticker symbols (e.g., --tickers MAIA ABCD XYZ)",
    )
    ticker_group.add_argument(
        "--tickers-file",
        type=Path,
        help="Path to ticker list file (one ticker per line)",
    )

    # Configuration
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=1460,
        help="Number of days to look back for Form 4 filings (default: 1460)",
    )
    parser.add_argument(
        "--max-form4-filings",
        type=int,
        default=0,
        help="Maximum Form 4 filings per ticker (0 = unlimited, default: 0)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/sample_reports/watchlist"),
        help="Output directory for per-ticker reports",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("docs/sample_reports/watchlist/manual_watchlist_summary.md"),
        help="Path for consolidated summary markdown",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("docs/sample_reports/watchlist/manual_watchlist_results.json"),
        help="Path for machine-readable JSON output",
    )
    parser.add_argument(
        "--dry-run-report",
        action="store_true",
        help="Dry-run mode (always enabled for watchlist, for compatibility)",
    )

    args = parser.parse_args()

    # Load and normalize tickers
    if args.tickers:
        raw_tickers = args.tickers
    else:
        raw_tickers = load_tickers_from_file(args.tickers_file)

    tickers = normalize_tickers(raw_tickers)

    if not tickers:
        print("[ERROR] No valid tickers provided")
        sys.exit(1)

    print(f"[ticker_watchlist] Processing {len(tickers)} ticker(s)...")
    print(f"[ticker_watchlist] Lookback window: {args.lookback_days} days")
    print(f"[ticker_watchlist] Form 4 parsing limit: {'unlimited' if args.max_form4_filings == 0 else args.max_form4_filings}")
    print(f"[ticker_watchlist] Mode: DRY-RUN (no alerts will be sent)")
    print()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Process each ticker
    ticker_metrics = []
    tickers_resolved = 0
    tickers_failed = 0

    for ticker in tickers:
        print(f"[ticker_watchlist] Processing {ticker}...")

        try:
            # Generate per-ticker report
            output_path = args.output_dir / f"{ticker}_manual_ticker_report.md"
            report_content = generate_ticker_report(
                ticker=ticker,
                output_path=output_path,
                lookback_days=args.lookback_days,
                max_form4_filings=args.max_form4_filings,
            )

            # Extract metrics for ranking
            metrics = extract_ticker_metrics(report_content, ticker)
            metrics["report_path"] = str(output_path)
            ticker_metrics.append(metrics)

            tickers_resolved += 1
            print(f"[ticker_watchlist] [OK] {ticker} report saved: {output_path}")

        except Exception as e:
            print(f"[ticker_watchlist] [FAIL] {ticker} failed: {e}")
            tickers_failed += 1

    print()

    # Rank tickers
    ticker_metrics = rank_tickers(ticker_metrics)

    # Generate consolidated summary
    summary_content = generate_markdown_summary(
        ticker_metrics=ticker_metrics,
        lookback_days=args.lookback_days,
        max_form4_filings=args.max_form4_filings,
        tickers_requested=len(tickers),
        tickers_resolved=tickers_resolved,
        tickers_failed=tickers_failed,
    )

    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(summary_content, encoding="utf-8")
    print(f"[ticker_watchlist] Summary saved: {args.summary_output}")

    # Generate JSON output
    json_data = generate_json_output(
        ticker_metrics=ticker_metrics,
        lookback_days=args.lookback_days,
        max_form4_filings=args.max_form4_filings,
    )

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(json_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[ticker_watchlist] JSON saved: {args.json_output}")

    # Console summary
    print()
    print("=" * 60)
    print("WATCHLIST SUMMARY")
    print("=" * 60)
    print(f"Tickers processed: {tickers_resolved}/{len(tickers)}")
    print(f"Tickers failed: {tickers_failed}")
    print()
    print("Top 5 by insider buying evidence:")
    for rank, metrics in enumerate(ticker_metrics[:5], 1):
        print(f"  {rank}. {metrics['ticker']:6s} - {metrics['eddie_signal']:20s} (${metrics['net_purchase_value']:,.0f} net)")
    print()
    print(f"Full summary: {args.summary_output}")
    print(f"JSON output:  {args.json_output}")
    print()
    print("[OK] Watchlist generation complete")
    print("[OK] No Telegram or email was sent (dry-run mode)")


if __name__ == "__main__":
    main()
