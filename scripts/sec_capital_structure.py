"""SEC capital structure extraction CLI.

Extract capital structure and dilution metrics from SEC filings.

Usage:
    python scripts/sec_capital_structure.py --ticker MAIA --output-dir docs/sample_reports/capital_structure/MAIA
    python scripts/sec_capital_structure.py --tickers MAIA,NVDA --output-dir docs/sample_reports/capital_structure/batch_maia_nvda
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.sec_capital_structure import (
    extract_capital_structure,
    generate_capital_structure_report,
    reconcile_maia_capital_structure,
)


def load_json_file(file_path: Path) -> dict | None:
    """Load JSON file."""
    if not file_path.exists():
        return None
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def save_json_file(data: dict, file_path: Path) -> None:
    """Save JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def save_markdown_file(content: str, file_path: Path) -> None:
    """Save Markdown file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def save_csv_file(rows: list[dict], file_path: Path, fieldnames: list[str]) -> None:
    """Save CSV file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def extract_ticker_capital_structure(
    ticker: str,
    output_dir: Path,
    inventory_json: Path | None = None,
    xbrl_json: Path | None = None,
    lookback_days: int = 1460,
) -> dict:
    """Extract capital structure for a single ticker.

    Args:
        ticker: Ticker symbol
        output_dir: Output directory
        inventory_json: Optional inventory JSON path
        xbrl_json: Optional XBRL JSON path
        lookback_days: Lookback days for filings

    Returns:
        Capital structure dict
    """
    # Load inventory if provided, otherwise use minimal placeholder
    inventory_data = None
    if inventory_json and inventory_json.exists():
        inventory_data = load_json_file(inventory_json)
    else:
        # Try default path
        default_inventory = (
            Path("docs/sample_reports/sec_inventory")
            / ticker
            / f"{ticker}_sec_inventory.json"
        )
        if default_inventory.exists():
            inventory_data = load_json_file(default_inventory)

    if not inventory_data:
        print(
            f"Warning: Inventory not found for {ticker}, using minimal placeholder"
        )
        inventory_data = {
            "ticker": ticker,
            "cik": "unknown",
            "company_name": f"{ticker} (CIK unknown)",
            "filings": [],
        }

    # Load XBRL if provided
    if xbrl_json and xbrl_json.exists():
        xbrl_data = load_json_file(xbrl_json)
    else:
        # Try default path
        default_xbrl = (
            Path("docs/sample_reports/xbrl_financials")
            / ticker
            / f"{ticker}_xbrl_financials.json"
        )
        if default_xbrl.exists():
            xbrl_data = load_json_file(default_xbrl)
        else:
            print(
                f"Warning: XBRL financials not found for {ticker}, proceeding without XBRL data"
            )
            xbrl_data = None

    # Extract capital structure
    capital_structure = extract_capital_structure(inventory_data, xbrl_data)

    # MAIA reconciliation if ticker is MAIA
    if ticker.upper() == "MAIA":
        target_values = {
            "common_shares_outstanding": 60671491,
            "march_2026_offering_shares": 20000000,
            "march_2026_offering_price": 1.50,
            "march_2026_gross_proceeds": 30000000,
            "march_2026_pre_funded_warrants": False,
            "march_2026_common_warrants": False,
            "fully_diluted_low_estimate": 85033854,
            "fully_diluted_high_estimate": 88033854,
        }

        extracted_values = {
            "common_shares_outstanding": capital_structure.get("share_counts", {}).get("common_shares_outstanding"),
            "recent_offerings": capital_structure.get("capital_events", []),
            "fully_diluted_low_estimate": capital_structure.get("derived_dilution_metrics", {}).get("fully_diluted_low_estimate"),
            "fully_diluted_high_estimate": capital_structure.get("derived_dilution_metrics", {}).get("fully_diluted_high_estimate"),
        }

        reconciliation_result = reconcile_maia_capital_structure(
            extracted_values, target_values
        )

        capital_structure["reconciliation"] = {
            "has_reconciliation_target": True,
            "status": reconciliation_result["status"],
            "differences": reconciliation_result["differences"],
        }

    # Save outputs
    json_path = output_dir / f"{ticker}_capital_structure.json"
    md_path = output_dir / f"{ticker}_capital_structure.md"
    csv_path = output_dir / f"{ticker}_capital_events.csv"

    save_json_file(capital_structure, json_path)

    # Generate Markdown report
    markdown = generate_capital_structure_report(capital_structure)
    save_markdown_file(markdown, md_path)

    # Save capital events CSV
    capital_events = capital_structure.get("capital_events", [])
    if capital_events:
        fieldnames = [
            "ticker",
            "cik",
            "form",
            "accession_number",
            "filing_date",
            "report_date",
            "event_type",
            "securities_offered",
            "shares_offered",
            "price_per_share",
            "gross_proceeds",
            "net_proceeds",
            "warrants_included",
            "pre_funded_warrants_included",
            "status",
            "parse_status",
            "failure_reason",
        ]
        save_csv_file(capital_events, csv_path, fieldnames)
    else:
        # Create empty CSV with headers
        save_csv_file([], csv_path, ["ticker", "cik", "event_type", "filing_date"])

    print(f"OK {ticker} capital structure extracted")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    print(f"  CSV: {csv_path}")

    return capital_structure


def generate_batch_summary(
    ticker_results: dict[str, dict], output_dir: Path
) -> None:
    """Generate batch summary JSON and Markdown.

    Args:
        ticker_results: Dict of ticker -> capital structure result
        output_dir: Output directory
    """
    ticker_summaries: dict[str, dict] = {}
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tickers": list(ticker_results.keys()),
        "ticker_count": len(ticker_results),
        "ticker_summaries": ticker_summaries,
        "safety": {
            "report_only": True,
            "alerts_generated": False,
            "openinsider_spreadsheet_used": False,
            "telegram_sent": False,
            "email_sent": False,
            "scheduled_tasks_modified": False,
            "env_printed_or_changed": False,
            "buy_sell_hold_language_used": False,
        },
    }

    for ticker, result in ticker_results.items():
        ticker_summaries[ticker] = {
            "cik": result.get("cik"),
            "company_name": result.get("company_name"),
            "common_shares_outstanding": result.get("share_counts", {}).get(
                "common_shares_outstanding"
            ),
            "fully_diluted_low_estimate": result.get(
                "derived_dilution_metrics", {}
            ).get("fully_diluted_low_estimate"),
            "fully_diluted_high_estimate": result.get(
                "derived_dilution_metrics", {}
            ).get("fully_diluted_high_estimate"),
            "dilution_overhang_percent_low": result.get(
                "derived_dilution_metrics", {}
            ).get("dilution_overhang_percent_low"),
            "dilution_overhang_percent_high": result.get(
                "derived_dilution_metrics", {}
            ).get("dilution_overhang_percent_high"),
            "reconciliation_status": result.get("reconciliation", {}).get("status"),
            "degraded_mode": result.get("degraded_mode", {}).get("is_degraded"),
        }

    # Save JSON
    json_path = output_dir / "batch_capital_structure_summary.json"
    save_json_file(summary, json_path)

    # Generate Markdown
    tickers_list = summary.get("tickers", [])
    if not isinstance(tickers_list, list):
        tickers_list = []

    markdown_lines = [
        "# Batch Capital Structure Summary",
        "",
        f"**Generated:** {summary['generated_at']}",
        f"**Tickers:** {', '.join(tickers_list)}",
        "",
        "## Per-Ticker Summary",
        "",
        "| Ticker | CIK | Common Shares | Fully Diluted Low | Fully Diluted High | Overhang % Low | Overhang % High |",
        "|--------|-----|---------------|-------------------|--------------------| --------------- |-----------------|",
    ]

    for ticker, ticker_summary in ticker_summaries.items():
        common = ticker_summary.get("common_shares_outstanding", "N/A")
        fd_low = ticker_summary.get("fully_diluted_low_estimate", "N/A")
        fd_high = ticker_summary.get("fully_diluted_high_estimate", "N/A")
        oh_low = ticker_summary.get("dilution_overhang_percent_low", "N/A")
        oh_high = ticker_summary.get("dilution_overhang_percent_high", "N/A")

        if isinstance(common, int):
            common = f"{common:,}"
        if isinstance(fd_low, int):
            fd_low = f"{fd_low:,}"
        if isinstance(fd_high, int):
            fd_high = f"{fd_high:,}"
        if isinstance(oh_low, (int, float)):
            oh_low = f"{oh_low:.1f}%"
        if isinstance(oh_high, (int, float)):
            oh_high = f"{oh_high:.1f}%"

        markdown_lines.append(
            f"| {ticker} | {ticker_summary.get('cik', 'N/A')} | {common} | {fd_low} | {fd_high} | {oh_low} | {oh_high} |"
        )

    markdown_lines.extend(
        [
            "",
            "## Safety Confirmations",
            "",
            "- Report-only mode: OK",
            "- No alerts generated: OK",
            "- No OpenInsider data used: OK",
            "- No Telegram sent: OK",
            "- No email sent: OK",
            "- No scheduled tasks modified: OK",
            "",
            "## Informational Only",
            "",
            "This report is for informational purposes only. It does not constitute investment advice.",
            "Consult a licensed financial advisor for investment decisions.",
        ]
    )

    markdown = "\n".join(markdown_lines)
    md_path = output_dir / "batch_capital_structure_summary.md"
    save_markdown_file(markdown, md_path)

    print(f"\nOK Batch summary generated")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract SEC capital structure and dilution metrics"
    )
    parser.add_argument("--ticker", help="Single ticker symbol")
    parser.add_argument("--tickers", help="Comma-separated ticker symbols")
    parser.add_argument(
        "--output-dir", required=True, help="Output directory", type=Path
    )
    parser.add_argument("--inventory-json", help="Inventory JSON path", type=Path)
    parser.add_argument("--xbrl-json", help="XBRL JSON path", type=Path)
    parser.add_argument(
        "--lookback-days", type=int, default=1460, help="Lookback days (default: 1460)"
    )

    args = parser.parse_args()

    if not args.ticker and not args.tickers:
        print("Error: Must provide --ticker or --tickers")
        sys.exit(1)

    # Parse tickers
    if args.ticker:
        tickers = [args.ticker.upper()]
    else:
        tickers = [t.strip().upper() for t in args.tickers.split(",")]

    print(f"SEC Capital Structure Extraction")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Output: {args.output_dir}")
    print()

    # Extract capital structure for each ticker
    ticker_results = {}
    for ticker in tickers:
        result = extract_ticker_capital_structure(
            ticker,
            args.output_dir / ticker if len(tickers) > 1 else args.output_dir,
            args.inventory_json,
            args.xbrl_json,
            args.lookback_days,
        )
        ticker_results[ticker] = result

    # Generate batch summary if multiple tickers
    if len(tickers) > 1:
        generate_batch_summary(ticker_results, args.output_dir)

    print("\nOK Capital structure extraction complete")


if __name__ == "__main__":
    main()
