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

from scripts.ticker_drilldown import generate_ticker_report, extract_structured_transaction_metrics
from sources.sec_ticker import SecTickerResolver
from sources.sec_common import utcnow_iso
from watchlist.history_store import WatchlistHistoryStore
from watchlist.scoring import compute_insider_evidence_score


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


def extract_ticker_metrics(
    report_content: str,
    ticker: str,
    lookback_days: int = 365,
    max_form4_filings: int = 0,
) -> dict[str, Any]:
    """Extract key metrics from ticker report for JSON output.

    Args:
        report_content: Markdown report content
        ticker: Ticker symbol
        lookback_days: Number of days to look back for Form 4 filings
        max_form4_filings: Maximum number of Form 4 filings to parse (0 = unlimited)

    Returns:
        Dictionary of metrics including structured transaction details for scoring
    """
    # Parse key metrics from report (for fields not available via structured extraction)
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
        "distinct_buyers": None,
        "distinct_buyer_names": None,
        "distinct_sellers": None,
        "distinct_seller_names": None,
        "latest_purchase_date": None,
        "latest_sale_date": None,
        "buyer_roles": None,
        "seller_roles": None,
        "purchase_months": None,
        "sale_months": None,
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

    # Extract structured transaction details for scoring inputs
    # This provides transaction-level data (buyer names, roles, dates, months) that markdown parsing cannot provide
    structured_metrics = extract_structured_transaction_metrics(
        ticker=ticker,
        lookback_days=lookback_days,
        max_form4_filings=max_form4_filings,
    )

    # Merge structured metrics into result
    # Structured metrics have higher fidelity than markdown parsing, so they override where present
    metrics.update({
        "form4_filings_found": structured_metrics["form4_filings_found"],
        "form4_filings_parsed": structured_metrics["form4_filings_parsed"],
        "transactions_extracted": structured_metrics["transactions_extracted"],
        "purchase_count": structured_metrics["purchase_count"],
        "purchase_value": structured_metrics["purchase_value"],
        "sale_count": structured_metrics["sale_count"],
        "sale_value": structured_metrics["sale_value"],
        "net_purchase_value": structured_metrics["purchase_value"] - structured_metrics["sale_value"],
        "distinct_buyers": structured_metrics["distinct_buyers"],
        "distinct_buyer_names": structured_metrics["distinct_buyer_names"],
        "distinct_sellers": structured_metrics["distinct_sellers"],
        "distinct_seller_names": structured_metrics["distinct_seller_names"],
        "latest_purchase_date": structured_metrics["latest_purchase_date"],
        "latest_sale_date": structured_metrics["latest_sale_date"],
        "buyer_roles": structured_metrics["buyer_roles"],
        "seller_roles": structured_metrics["seller_roles"],
        "purchase_months": structured_metrics["purchase_months"],
        "sale_months": structured_metrics["sale_months"],
    })

    return metrics


def rank_tickers(ticker_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank tickers by insider evidence strength.

    Ranking priority:
    1. Insider evidence total score (0-100, higher is better)
    2. Eddie signal (BULLISH_EVIDENCE > NEUTRAL > BEARISH_EVIDENCE)
    3. Net purchase value (higher is better)

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
            -metrics.get("total_score", 0),  # Primary: insider evidence score
            -signal_score(metrics["eddie_signal"]),  # Secondary: Eddie signal
            -metrics["net_purchase_value"],  # Tertiary: net purchase value
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
        "Tickers ranked by insider buying evidence strength (score 0-100):",
        "",
        "| Rank | Ticker | Company | Score | Rating | Eddie Signal | Purchase Value | Net Value | Buyers |",
        "|------|--------|---------|-------|--------|--------------|----------------|-----------|--------|",
    ]

    for rank, metrics in enumerate(ticker_metrics, 1):
        company_short = (metrics["company_name"] or "Unknown")[:25]
        score = metrics.get("total_score", 0)
        rating = (metrics.get("rating_label", "Unknown") or "Unknown")[:20]
        distinct_buyers = metrics.get("distinct_buyers", 0) or 0

        summary.append(
            f"| {rank} | {metrics['ticker']} | {company_short} | "
            f"{score:.1f} | {rating} | "
            f"{metrics['eddie_signal']} | "
            f"${metrics['purchase_value']:,.0f} | "
            f"${metrics['net_purchase_value']:,.0f} | "
            f"{distinct_buyers} |"
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
        "Tickers are ranked by **Insider Evidence Score** (0-100 points):",
        "",
        "### Scoring Components",
        "",
        "1. **Net Insider Buying Value** (0-25 pts): Purchase value minus sale value",
        "2. **Buy/Sell Imbalance** (0-20 pts): Reward strong buying with little/no selling",
        "3. **Distinct Buyer Breadth** (0-15 pts): More distinct insider buyers",
        "4. **Recency** (0-15 pts): How recently insiders purchased",
        "5. **Role Quality** (0-10 pts): CEO/CFO/Director purchases weighted higher",
        "6. **Persistence** (0-10 pts): Purchases across multiple months",
        "7. **Data Quality** (0-5 pts): Form 4 parsing completeness",
        "",
        "### Rating Labels",
        "",
        "- **80-100**: Very Strong Insider Buying Evidence",
        "- **60-79**: Strong Insider Buying Evidence",
        "- **40-59**: Moderate Insider Buying Evidence",
        "- **20-39**: Weak Insider Buying Evidence",
        "- **0-19**: Little/No Insider Buying Evidence",
        "",
        "**Note**: Scores are for ranking/research only. Not trading recommendations.",
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
                "distinct_buyers": m.get("distinct_buyers"),
                "latest_purchase_date": m.get("latest_purchase_date"),
                "buyer_roles": m.get("buyer_roles"),
                "purchase_months": m.get("purchase_months"),
                "scoring": m.get("scoring"),
                "report_path": f"docs/sample_reports/watchlist/{m['ticker']}_manual_ticker_report.md",
            }
            for m in ticker_metrics
        ],
    }


def generate_history_summary(
    run_id: str,
    ticker_metrics: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    lookback_days: int,
    max_form4_filings: int,
    tickers_requested: int,
    tickers_resolved: int,
    tickers_failed: int,
    history_db_path: Path,
    compare_previous: bool,
) -> str:
    """Generate history summary markdown report.

    Args:
        run_id: Unique run identifier
        ticker_metrics: List of ticker metric dicts
        deltas: List of delta dicts for each ticker
        lookback_days: Lookback window in days
        max_form4_filings: Form 4 filing limit
        tickers_requested: Total tickers requested
        tickers_resolved: Tickers successfully resolved
        tickers_failed: Tickers that failed
        history_db_path: Path to history database
        compare_previous: Whether deltas were computed

    Returns:
        Markdown formatted history summary
    """
    lines = []
    lines.append("# Manual Ticker Watchlist History Summary")
    lines.append("")
    lines.append(f"**Generated**: {utcnow_iso()}")
    lines.append(f"**Run ID**: `{run_id}`")
    lines.append(
        "**Mode**: DRY-RUN — No Telegram or email was sent. This is research history only."
    )
    lines.append("")

    # Configuration
    lines.append("## Configuration")
    lines.append("")
    lines.append(f"- **History Database**: `{history_db_path}`")
    lines.append(f"- **Lookback Days**: {lookback_days}")
    lines.append(
        f"- **Max Form 4 Filings**: {'Unlimited' if max_form4_filings == 0 else max_form4_filings}"
    )
    lines.append(f"- **Tickers Requested**: {tickers_requested}")
    lines.append(f"- **Tickers Resolved**: {tickers_resolved}")
    lines.append(f"- **Tickers Failed**: {tickers_failed}")
    lines.append(f"- **Compared with Prior Runs**: {'Yes' if compare_previous else 'No'}")
    lines.append("")

    # Data sources
    lines.append("## Data Sources")
    lines.append("")
    lines.append("- SEC EDGAR API")
    lines.append("- Project connectors (SEC Form 4, SEC 13F)")
    lines.append("- **Roger's OpenInsider spreadsheet was not used**")
    lines.append("")

    # Current run results
    lines.append("## Current Run Results")
    lines.append("")
    lines.append("Tickers ranked by insider buying evidence strength:")
    lines.append("")
    lines.append(
        "| Rank | Ticker | Company | Eddie Signal | Confidence | Purchases | Purchase Value | Sales | Net Value |"
    )
    lines.append(
        "|------|--------|---------|--------------|------------|-----------|----------------|-------|-----------"
    )

    for rank, m in enumerate(ticker_metrics, 1):
        # Handle None company_name for unresolved tickers
        company_name = m['company_name'] if m['company_name'] else "Unknown"
        lines.append(
            f"| {rank} | {m['ticker']} | {company_name[:30]} | "
            f"{m['eddie_signal']} | {m['eddie_confidence']} | "
            f"{m['purchase_count']} | ${m['purchase_value']:,.2f} | "
            f"{m['sale_count']} | ${m['net_purchase_value']:,.2f} |"
        )

    lines.append("")

    # Delta comparison
    if compare_previous and deltas:
        lines.append("## Comparison with Prior Runs")
        lines.append("")
        lines.append(
            "Changes since most recent prior run for each ticker:"
        )
        lines.append("")
        lines.append(
            "| Ticker | Prior Run Date | Purchase Value Δ | Purchase Count Δ | Sale Value Δ | Sale Count Δ | Signal Changed | Note |"
        )
        lines.append(
            "|--------|----------------|------------------|------------------|--------------|--------------|----------------|------|"
        )

        for item in deltas:
            ticker = item["ticker"]
            delta = item["delta"]

            if delta["has_prior"]:
                prior_date = delta["prior_created_at"][:10] if delta["prior_created_at"] else "N/A"
                pv_delta = delta["purchase_value_delta"]
                pv_delta_str = f"${pv_delta:,.2f}" if pv_delta is not None else "N/A"
                if pv_delta and pv_delta > 0:
                    pv_delta_str = f"+{pv_delta_str}"

                pc_delta = delta["purchase_count_delta"]
                pc_delta_str = str(pc_delta) if pc_delta is not None else "N/A"
                if pc_delta and pc_delta > 0:
                    pc_delta_str = f"+{pc_delta_str}"

                sv_delta = delta["sale_value_delta"]
                sv_delta_str = f"${sv_delta:,.2f}" if sv_delta is not None else "N/A"
                if sv_delta and sv_delta > 0:
                    sv_delta_str = f"+{sv_delta_str}"

                sc_delta = delta["sale_count_delta"]
                sc_delta_str = str(sc_delta) if sc_delta is not None else "N/A"
                if sc_delta and sc_delta > 0:
                    sc_delta_str = f"+{sc_delta_str}"

                signal_changed = "Yes" if delta["signal_changed"] else "No"
                summary = delta["summary"]

                lines.append(
                    f"| {ticker} | {prior_date} | {pv_delta_str} | {pc_delta_str} | "
                    f"{sv_delta_str} | {sc_delta_str} | {signal_changed} | {summary} |"
                )
            else:
                lines.append(
                    f"| {ticker} | N/A | N/A | N/A | N/A | N/A | N/A | First run - no prior data |"
                )

        lines.append("")
    elif compare_previous and not deltas:
        lines.append("## Comparison with Prior Runs")
        lines.append("")
        lines.append("No prior runs found for comparison.")
        lines.append("")

    # Per-ticker reports
    lines.append("## Per-Ticker Reports")
    lines.append("")
    for m in ticker_metrics:
        lines.append(
            f"- [{m['ticker']}](./{m['ticker']}_manual_ticker_report.md)"
        )
    lines.append("")

    # Limitations
    lines.append("## Limitations")
    lines.append("")
    lines.append("- This is manual research history only, not trading advice")
    lines.append("- Deltas show changes in SEC filing data, not price movements")
    lines.append("- Insider transactions can occur for many reasons unrelated to expectations")
    lines.append("- Historical comparison requires multiple saved runs over time")
    lines.append("")

    # Safety confirmations
    lines.append("## Safety Confirmations")
    lines.append("")
    lines.append("- ✅ No Telegram messages sent")
    lines.append("- ✅ No email sent")
    lines.append("- ✅ Roger's OpenInsider spreadsheet not used")
    lines.append("- ✅ Data sourced from SEC EDGAR only")
    lines.append("- ✅ History database is local and gitignored")
    lines.append("")

    # Disclaimer
    lines.append("## Disclaimer")
    lines.append("")
    lines.append("**This analysis is informational only and is not trading advice.**")
    lines.append("")
    lines.append(
        "Insider transactions can occur for many reasons unrelated to stock price expectations. "
        "This report presents SEC filing data for research purposes only. "
        "Do not use this information as the sole basis for investment decisions."
    )
    lines.append("")

    return "\n".join(lines)


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

    # History tracking options
    parser.add_argument(
        "--save-history",
        action="store_true",
        help="Save this run to local history database for tracking over time",
    )
    parser.add_argument(
        "--no-save-history",
        action="store_true",
        help="Do not save history (default behavior)",
    )
    parser.add_argument(
        "--history-db",
        type=Path,
        default=Path(".state/watchlist_history.db"),
        help="Path to SQLite history database (default: .state/watchlist_history.db)",
    )
    parser.add_argument(
        "--history-summary-output",
        type=Path,
        default=Path("docs/sample_reports/watchlist/manual_watchlist_history_summary.md"),
        help="Path for history summary markdown",
    )
    parser.add_argument(
        "--compare-previous",
        action="store_true",
        help="Compare current results with most recent prior run for each ticker",
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

            # Extract metrics for ranking (including structured transaction details for scoring)
            metrics = extract_ticker_metrics(
                report_content=report_content,
                ticker=ticker,
                lookback_days=args.lookback_days,
                max_form4_filings=args.max_form4_filings,
            )
            metrics["report_path"] = str(output_path)

            # Compute insider evidence score
            score = compute_insider_evidence_score(ticker, metrics)
            metrics["scoring"] = score.to_dict()
            metrics["total_score"] = score.total_score
            metrics["rating_label"] = score.rating_label

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

    # History tracking and delta computation
    run_id = None
    deltas = []
    if args.save_history and not args.no_save_history:
        print()
        print("[ticker_watchlist] Saving run to history database...")

        store = WatchlistHistoryStore(args.history_db)

        # Get current git commit if available
        git_commit = None
        try:
            import subprocess
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if result.returncode == 0:
                git_commit = result.stdout.strip()[:8]
        except Exception:
            pass

        # Save run metadata
        run_id = store.save_run(
            mode="manual_watchlist_dry_run",
            tickers_requested=len(tickers),
            tickers_resolved=tickers_resolved,
            lookback_days=args.lookback_days,
            max_form4_filings=args.max_form4_filings,
            git_commit=git_commit,
            notes="CP21H persistent watchlist tracking",
        )

        print(f"[ticker_watchlist] Run ID: {run_id}")

        # Save ticker results and compute deltas
        for metrics in ticker_metrics:
            ticker = metrics["ticker"]

            # Find prior result if --compare-previous
            prior_result = None
            if args.compare_previous:
                prior_result = store.get_most_recent_result_for_ticker(
                    ticker, exclude_run_id=run_id
                )

            # Compute delta
            delta = store.compute_delta(metrics, prior_result)
            deltas.append({"ticker": ticker, "delta": delta})

            # Save ticker result
            store.save_ticker_result(
                run_id=run_id,
                ticker=ticker,
                metrics=metrics,
                json_blob=metrics,
            )

            # Save delta
            store.save_delta(
                run_id=run_id,
                ticker=ticker,
                delta=delta,
            )

            if delta["has_prior"]:
                print(f"[ticker_watchlist]   {ticker}: {delta['summary']}")
            else:
                print(f"[ticker_watchlist]   {ticker}: First run - no prior data")

        # Generate history summary report
        history_summary = generate_history_summary(
            run_id=run_id,
            ticker_metrics=ticker_metrics,
            deltas=deltas,
            lookback_days=args.lookback_days,
            max_form4_filings=args.max_form4_filings,
            tickers_requested=len(tickers),
            tickers_resolved=tickers_resolved,
            tickers_failed=tickers_failed,
            history_db_path=args.history_db,
            compare_previous=args.compare_previous,
        )

        args.history_summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.history_summary_output.write_text(history_summary, encoding="utf-8")
        print(f"[ticker_watchlist] History summary saved: {args.history_summary_output}")

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
