#!/usr/bin/env python3
"""Extract and normalize Form 4 insider transactions for one or more tickers.

This script loads SEC submissions inventory (from CP24B), fetches and parses Form 4
filings, extracts insider transactions, and generates JSON/Markdown/CSV reports.

Usage:
    # Single ticker with 1460-day lookback
    python scripts/sec_form4_transactions.py --ticker MAIA --output-dir docs/sample_reports/form4_transactions/MAIA

    # Multiple tickers (batch mode)
    python scripts/sec_form4_transactions.py --tickers MAIA,NVDA --output-dir docs/sample_reports/form4_transactions/batch

    # Custom lookback period
    python scripts/sec_form4_transactions.py --ticker NVDA --lookback-days 730 --output-dir docs/sample_reports/form4_transactions/NVDA
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sources.form4_aggregator import aggregate_form4_transactions
from sources.sec_common import utcnow_iso
from sources.sec_form4_details import fetch_and_parse_form4
from sources.sec_submissions import build_submissions_inventory, fetch_company_submissions
from sources.sec_ticker import resolve_ticker_to_cik


def _load_or_create_inventory(
    ticker: str, lookback_days: int, max_recent_filings: int
) -> dict:
    """Load existing inventory or create new one.

    Args:
        ticker: Stock ticker
        lookback_days: Lookback window in days
        max_recent_filings: Maximum recent filings to fetch

    Returns:
        Inventory dictionary
    """
    # Try to load existing inventory first
    inventory_path = (
        Path(__file__).parent.parent
        / "docs"
        / "sample_reports"
        / "sec_inventory"
        / ticker
        / f"{ticker}_sec_inventory.json"
    )

    if inventory_path.exists():
        print(f"  Loading existing inventory from {inventory_path}")
        with open(inventory_path, encoding="utf-8") as f:
            return json.load(f)

    # Create new inventory
    print(f"  No existing inventory found, creating new one...")
    resolver_result = resolve_ticker_to_cik(ticker)

    if not resolver_result.ok:
        return {
            "ticker": ticker,
            "cik": None,
            "company_name": None,
            "resolver": {"status": "failed", "error": resolver_result.error_type},
            "submissions": {"status": "not_attempted"},
        }

    inventory = build_submissions_inventory(
        ticker=ticker,
        cik=resolver_result.cik_padded,
        company_name=resolver_result.company_name,
        lookback_days=lookback_days,
        max_recent_filings=max_recent_filings,
    )

    return inventory


def _extract_ticker_form4_transactions(
    ticker: str,
    lookback_days: int,
    output_dir: Path,
) -> dict:
    """Extract Form 4 transactions for a single ticker.

    Args:
        ticker: Stock ticker
        lookback_days: Lookback window in days
        output_dir: Output directory for reports

    Returns:
        Form 4 extraction result dictionary
    """
    print(f"\n{'=' * 80}")
    print(f"Processing ticker: {ticker}")
    print(f"{'=' * 80}\n")

    # Load or create inventory
    inventory = _load_or_create_inventory(
        ticker=ticker, lookback_days=lookback_days, max_recent_filings=500
    )

    # Check resolver status
    if inventory["resolver"]["status"] != "resolved":
        print(f"  ERROR: Ticker {ticker} could not be resolved to CIK")
        return {
            "ticker": ticker,
            "cik": None,
            "company_name": None,
            "generated_at": utcnow_iso(),
            "lookback_days": lookback_days,
            "source_inventory_path": None,
            "summary": {
                "form4_filings_found": 0,
                "form4_filings_parsed": 0,
                "form4_filings_failed": 0,
                "transactions_extracted": 0,
                "open_market_purchases": 0,
                "open_market_sales": 0,
                "open_market_purchase_value": 0.0,
                "open_market_sale_value": 0.0,
                "net_open_market_value": 0.0,
                "distinct_buyers": 0,
                "distinct_sellers": 0,
                "latest_open_market_purchase_date": None,
                "latest_open_market_sale_date": None,
                "transaction_code_counts": {},
            },
            "transactions": [],
            "top_buyers_by_value": [],
            "top_sellers_by_value": [],
            "filing_parse_results": [],
            "degraded_mode": {
                "is_degraded": True,
                "reasons": ["ticker_resolution_failed"],
            },
            "evidence_provenance": [],
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

    cik = inventory["cik"]
    company_name = inventory["company_name"]

    # Check for Form 4 filings
    if not inventory.get("submissions", {}).get("coverage_flags", {}).get("has_form4", False):
        print(f"  WARNING: No Form 4 filings found for {ticker} in submissions inventory")
        return {
            "ticker": ticker,
            "cik": cik,
            "company_name": company_name,
            "generated_at": utcnow_iso(),
            "lookback_days": lookback_days,
            "source_inventory_path": str(Path(f"sec_inventory/{ticker}/{ticker}_sec_inventory.json")),
            "summary": {
                "form4_filings_found": 0,
                "form4_filings_parsed": 0,
                "form4_filings_failed": 0,
                "transactions_extracted": 0,
                "open_market_purchases": 0,
                "open_market_sales": 0,
                "open_market_purchase_value": 0.0,
                "open_market_sale_value": 0.0,
                "net_open_market_value": 0.0,
                "distinct_buyers": 0,
                "distinct_sellers": 0,
                "latest_open_market_purchase_date": None,
                "latest_open_market_sale_date": None,
                "transaction_code_counts": {},
            },
            "transactions": [],
            "top_buyers_by_value": [],
            "top_sellers_by_value": [],
            "filing_parse_results": [],
            "degraded_mode": {
                "is_degraded": True,
                "reasons": ["no_form4_filings_found"],
            },
            "evidence_provenance": [],
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

    # Fetch ALL Form 4 filings directly from SEC submissions API (not limited by inventory recent_filings)
    print(f"  Fetching full submissions data to find ALL Form 4 filings...")
    submissions_result = fetch_company_submissions(cik)

    if not submissions_result.get("ok", False):
        print(f"  WARNING: Failed to fetch submissions: {submissions_result.get('error', 'Unknown error')}")
        # Fall back to inventory recent_filings
        recent_filings = inventory.get("submissions", {}).get("recent_filings", [])
    else:
        # Extract all filings from submissions API response
        submissions_body = submissions_result["body"]
        recent_filings = []
        filing_data = submissions_body.get("filings", {}).get("recent", {})
        accession_numbers = filing_data.get("accessionNumber", [])

        for i in range(len(accession_numbers)):
            recent_filings.append({
                "accession_number": filing_data["accessionNumber"][i],
                "filing_date": filing_data["filingDate"][i],
                "form": filing_data["form"][i],
                "primary_document": filing_data["primaryDocument"][i],
            })

    # Filter Form 4 filings within lookback window
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    form4_filings = []
    for f in recent_filings:
        if f["form"] not in ("4", "4/A"):
            continue

        # Parse filing_date and make it timezone-aware for comparison
        filing_date_str = f["filing_date"]
        if "T" in filing_date_str:
            # ISO format with time
            filing_date = datetime.fromisoformat(filing_date_str.replace("Z", "+00:00"))
        else:
            # Date-only format (YYYY-MM-DD)
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        if filing_date >= cutoff_date:
            form4_filings.append(f)

    print(f"  Found {len(form4_filings)} Form 4 filings within {lookback_days}-day lookback (from {len(recent_filings)} total recent filings)")

    if not form4_filings:
        return {
            "ticker": ticker,
            "cik": cik,
            "company_name": company_name,
            "generated_at": utcnow_iso(),
            "lookback_days": lookback_days,
            "source_inventory_path": str(Path(f"sec_inventory/{ticker}/{ticker}_sec_inventory.json")),
            "summary": {
                "form4_filings_found": 0,
                "form4_filings_parsed": 0,
                "form4_filings_failed": 0,
                "transactions_extracted": 0,
                "open_market_purchases": 0,
                "open_market_sales": 0,
                "open_market_purchase_value": 0.0,
                "open_market_sale_value": 0.0,
                "net_open_market_value": 0.0,
                "distinct_buyers": 0,
                "distinct_sellers": 0,
                "latest_open_market_purchase_date": None,
                "latest_open_market_sale_date": None,
                "transaction_code_counts": {},
            },
            "transactions": [],
            "top_buyers_by_value": [],
            "top_sellers_by_value": [],
            "filing_parse_results": [],
            "degraded_mode": {
                "is_degraded": True,
                "reasons": ["no_form4_filings_in_lookback_window"],
            },
            "evidence_provenance": [],
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

    # Fetch and parse each Form 4 filing
    print(f"  Fetching and parsing {len(form4_filings)} Form 4 filings...")
    parsed_filings = []

    for i, filing in enumerate(form4_filings, 1):
        accession = filing["accession_number"]
        primary_doc = filing.get("primary_document")

        print(f"    [{i}/{len(form4_filings)}] Parsing {accession}...")

        parsed = fetch_and_parse_form4(
            accession_number=accession,
            cik=cik,
            primary_document=primary_doc,
        )

        # Update filing_date from inventory (not always in XML)
        parsed.filing_date = filing["filing_date"]

        parsed_filings.append(parsed)

        if parsed.parse_status == "failed":
            print(f"        FAILED: {parsed.error_message}")
        else:
            print(
                f"        SUCCESS: {len(parsed.transactions)} transactions, {len(parsed.owners)} owners"
            )

    # Aggregate transactions
    print(f"\n  Aggregating transactions...")
    aggregation = aggregate_form4_transactions(parsed_filings, ticker)

    # Build final result
    result = {
        "ticker": ticker,
        "cik": cik,
        "company_name": company_name,
        "generated_at": utcnow_iso(),
        "lookback_days": lookback_days,
        "source_inventory_path": str(Path(f"sec_inventory/{ticker}/{ticker}_sec_inventory.json")),
        "summary": aggregation["summary"],
        "transactions": aggregation["transactions"],
        "top_buyers_by_value": aggregation["top_buyers_by_value"][:10],  # Top 10
        "top_sellers_by_value": aggregation["top_sellers_by_value"][:10],  # Top 10
        "filing_parse_results": aggregation["filing_parse_results"],
        "degraded_mode": {
            "is_degraded": False,
            "reasons": [],
        },
        "evidence_provenance": [
            {
                "source": "SEC EDGAR Form 4 Filings",
                "url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=4&dateb=&owner=exclude&count=100",
                "retrieved_at": utcnow_iso(),
            }
        ],
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

    # Check for degraded mode
    if aggregation["summary"]["form4_filings_failed"] > 0:
        result["degraded_mode"]["is_degraded"] = True
        result["degraded_mode"]["reasons"].append(
            f"{aggregation['summary']['form4_filings_failed']} filings failed to parse"
        )

    # Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON output
    json_path = output_dir / f"{ticker}_form4_transactions.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\n  Saved JSON report: {json_path}")

    # CSV output
    csv_path = output_dir / f"{ticker}_form4_transactions.csv"
    _write_transactions_csv(result["transactions"], csv_path)
    print(f"  Saved CSV report: {csv_path}")

    # Markdown output
    md_path = output_dir / f"{ticker}_form4_transactions.md"
    _write_markdown_report(result, md_path)
    print(f"  Saved Markdown report: {md_path}")

    print(f"\n  Summary:")
    print(f"    Form 4 filings found: {result['summary']['form4_filings_found']}")
    print(f"    Form 4 filings parsed: {result['summary']['form4_filings_parsed']}")
    print(f"    Form 4 filings failed: {result['summary']['form4_filings_failed']}")
    print(f"    Transactions extracted: {result['summary']['transactions_extracted']}")
    print(f"    Open-market purchases: {result['summary']['open_market_purchases']}")
    print(f"    Open-market sales: {result['summary']['open_market_sales']}")
    print(
        f"    Open-market purchase value: ${result['summary']['open_market_purchase_value']:,.2f}"
    )
    print(f"    Open-market sale value: ${result['summary']['open_market_sale_value']:,.2f}")
    print(f"    Distinct buyers: {result['summary']['distinct_buyers']}")
    print(f"    Distinct sellers: {result['summary']['distinct_sellers']}")

    return result


def _write_transactions_csv(transactions: list[dict], csv_path: Path) -> None:
    """Write transactions to CSV file.

    Args:
        transactions: List of canonical transaction dictionaries
        csv_path: Output CSV file path
    """
    if not transactions:
        # Write header only
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "ticker",
                    "issuer_cik",
                    "accession_number",
                    "filing_date",
                    "period_of_report",
                    "reporting_owner_name",
                    "reporting_owner_cik",
                    "officer_title",
                    "director",
                    "ten_percent_owner",
                    "security_title",
                    "transaction_date",
                    "transaction_code",
                    "transaction_code_description",
                    "transaction_classification",
                    "is_open_market_purchase",
                    "is_open_market_sale",
                    "is_derivative",
                    "shares",
                    "price_per_share",
                    "transaction_value",
                    "shares_owned_following",
                    "ownership_nature_direct_or_indirect",
                    "ownership_nature_explanation",
                ]
            )
        return

    # Write header and rows
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "ticker",
                "issuer_cik",
                "accession_number",
                "filing_date",
                "period_of_report",
                "reporting_owner_name",
                "reporting_owner_cik",
                "officer_title",
                "director",
                "ten_percent_owner",
                "security_title",
                "transaction_date",
                "transaction_code",
                "transaction_code_description",
                "transaction_classification",
                "is_open_market_purchase",
                "is_open_market_sale",
                "is_derivative",
                "shares",
                "price_per_share",
                "transaction_value",
                "shares_owned_following",
                "ownership_nature_direct_or_indirect",
                "ownership_nature_explanation",
            ]
        )

        for t in transactions:
            writer.writerow(
                [
                    t["ticker"],
                    t["issuer_cik"],
                    t["accession_number"],
                    t["filing_date"],
                    t["period_of_report"],
                    t["reporting_owner_name"],
                    t["reporting_owner_cik"] or "",
                    t["officer_title"] or "",
                    t["director"],
                    t["ten_percent_owner"],
                    t["security_title"],
                    t["transaction_date"],
                    t["transaction_code"],
                    t["transaction_code_description"],
                    t["transaction_classification"],
                    t["is_open_market_purchase"],
                    t["is_open_market_sale"],
                    t["is_derivative"],
                    t["shares"],
                    t["price_per_share"] if t["price_per_share"] is not None else "",
                    t["transaction_value"] if t["transaction_value"] is not None else "",
                    t["shares_owned_following"] if t["shares_owned_following"] is not None else "",
                    t["ownership_nature_direct_or_indirect"],
                    t["ownership_nature_explanation"] or "",
                ]
            )


def _write_markdown_report(result: dict, md_path: Path) -> None:
    """Write Markdown report.

    Args:
        result: Form 4 extraction result dictionary
        md_path: Output Markdown file path
    """
    lines = []

    # Header
    lines.append(f"# Form 4 Insider Transaction Report: {result['ticker']}")
    lines.append("")
    lines.append(f"**Company:** {result['company_name']}")
    lines.append(f"**Ticker:** {result['ticker']}")
    lines.append(f"**CIK:** {result['cik']}")
    lines.append(f"**Generated:** {result['generated_at']}")
    lines.append(f"**Lookback Period:** {result['lookback_days']} days")
    lines.append("")

    # Purpose
    lines.append("## Purpose")
    lines.append("")
    lines.append(
        "This report extracts and normalizes Form 4 insider transactions from SEC EDGAR filings. "
        "It distinguishes open-market purchases (code P) and sales (code S) from non-open-market "
        "transactions such as grants (A), option exercises (M), tax withholding (F), and other "
        "transaction types."
    )
    lines.append("")

    # Source boundary
    lines.append("## Source Boundary")
    lines.append("")
    lines.append("- **Primary source:** SEC EDGAR Form 4 XML filings")
    lines.append("- **Secondary sources:** None (SEC-only extraction)")
    lines.append(f"- **Lookback window:** {result['lookback_days']} days")
    lines.append(f"- **Form 4 filings found:** {result['summary']['form4_filings_found']}")
    lines.append(f"- **Form 4 filings parsed:** {result['summary']['form4_filings_parsed']}")
    lines.append(f"- **Form 4 filings failed:** {result['summary']['form4_filings_failed']}")
    lines.append("")

    # Transaction summary
    lines.append("## Transaction Summary")
    lines.append("")
    lines.append(
        f"- **Total transactions extracted:** {result['summary']['transactions_extracted']}"
    )
    lines.append(
        f"- **Open-market purchases (P):** {result['summary']['open_market_purchases']}"
    )
    lines.append(f"- **Open-market sales (S):** {result['summary']['open_market_sales']}")
    lines.append(
        f"- **Open-market purchase value:** ${result['summary']['open_market_purchase_value']:,.2f}"
    )
    lines.append(
        f"- **Open-market sale value:** ${result['summary']['open_market_sale_value']:,.2f}"
    )
    lines.append(
        f"- **Net open-market value:** ${result['summary']['net_open_market_value']:,.2f}"
    )
    lines.append(f"- **Distinct buyers:** {result['summary']['distinct_buyers']}")
    lines.append(f"- **Distinct sellers:** {result['summary']['distinct_sellers']}")
    lines.append(
        f"- **Latest open-market purchase:** {result['summary']['latest_open_market_purchase_date'] or 'N/A'}"
    )
    lines.append(
        f"- **Latest open-market sale:** {result['summary']['latest_open_market_sale_date'] or 'N/A'}"
    )
    lines.append("")

    # Transaction code counts
    lines.append("## Transaction Code Counts")
    lines.append("")
    if result["summary"]["transaction_code_counts"]:
        lines.append("| Transaction Code | Description | Count |")
        lines.append("|------------------|-------------|-------|")
        code_descriptions = {
            "P": "Open-market purchase",
            "S": "Open-market sale",
            "M": "Option exercise",
            "A": "Grant or award",
            "F": "Tax withholding",
            "G": "Gift",
            "D": "Disposition to issuer",
            "J": "Other",
        }
        for code, count in sorted(result["summary"]["transaction_code_counts"].items()):
            desc = code_descriptions.get(code, "Unknown")
            lines.append(f"| {code} | {desc} | {count} |")
    else:
        lines.append("No transactions found.")
    lines.append("")

    # Top buyers
    lines.append("## Top Buyers by Value (Open-Market Purchases)")
    lines.append("")
    if result["top_buyers_by_value"]:
        lines.append("| Rank | Name | Title | Transactions | Total Value | Total Shares |")
        lines.append("|------|------|-------|--------------|-------------|--------------|")
        for i, buyer in enumerate(result["top_buyers_by_value"], 1):
            title = buyer["title"] or "N/A"
            lines.append(
                f"| {i} | {buyer['name']} | {title} | {buyer['transaction_count']} | "
                f"${buyer['total_value']:,.2f} | {buyer['total_shares']:,.0f} |"
            )
    else:
        lines.append("No open-market purchases found.")
    lines.append("")

    # Top sellers
    lines.append("## Top Sellers by Value (Open-Market Sales)")
    lines.append("")
    if result["top_sellers_by_value"]:
        lines.append("| Rank | Name | Title | Transactions | Total Value | Total Shares |")
        lines.append("|------|------|-------|--------------|-------------|--------------|")
        for i, seller in enumerate(result["top_sellers_by_value"], 1):
            title = seller["title"] or "N/A"
            lines.append(
                f"| {i} | {seller['name']} | {title} | {seller['transaction_count']} | "
                f"${seller['total_value']:,.2f} | {seller['total_shares']:,.0f} |"
            )
    else:
        lines.append("No open-market sales found.")
    lines.append("")

    # Parse failures
    lines.append("## Filing Parse Results")
    lines.append("")
    failed_filings = [
        f for f in result["filing_parse_results"] if f["parse_status"] == "failed"
    ]
    if failed_filings:
        lines.append(f"**Warning:** {len(failed_filings)} filings failed to parse:")
        lines.append("")
        for f in failed_filings:
            lines.append(f"- {f['accession_number']} ({f['filing_date']}): {f['error_message']}")
        lines.append("")
    else:
        lines.append("All filings parsed successfully.")
        lines.append("")

    # Evidence provenance
    lines.append("## Evidence Provenance")
    lines.append("")
    for ev in result["evidence_provenance"]:
        lines.append(f"- **{ev['source']}**")
        lines.append(f"  - URL: {ev['url']}")
        lines.append(f"  - Retrieved: {ev['retrieved_at']}")
    lines.append("")

    # Degraded mode
    if result["degraded_mode"]["is_degraded"]:
        lines.append("## Degraded Mode")
        lines.append("")
        lines.append("**This report is operating in degraded mode due to:**")
        lines.append("")
        for reason in result["degraded_mode"]["reasons"]:
            lines.append(f"- {reason}")
        lines.append("")

    # Safety confirmations
    lines.append("## Safety Confirmations")
    lines.append("")
    safety = result["safety"]
    lines.append(f"- **Report-only mode:** {safety['report_only']}")
    lines.append(f"- **Alerts generated:** {safety['alerts_generated']}")
    lines.append(f"- **OpenInsider spreadsheet used:** {safety['openinsider_spreadsheet_used']}")
    lines.append(f"- **Telegram sent:** {safety['telegram_sent']}")
    lines.append(f"- **Email sent:** {safety['email_sent']}")
    lines.append(f"- **Scheduled tasks modified:** {safety['scheduled_tasks_modified']}")
    lines.append(f"- **Environment printed or changed:** {safety['env_printed_or_changed']}")
    lines.append(f"- **Buy/sell/hold language used:** {safety['buy_sell_hold_language_used']}")
    lines.append("")

    # No-recommendation statement
    lines.append("## No-Recommendation Statement")
    lines.append("")
    lines.append(
        "This report is for informational purposes only. It does NOT constitute investment advice, "
        "a recommendation to buy or sell securities, or any other form of financial guidance. "
        "All data is extracted mechanically from SEC EDGAR filings without interpretation or "
        "editorial judgment."
    )
    lines.append("")

    # Write to file
    md_path.write_text("\n".join(lines), encoding="utf-8")


def _write_batch_summary(results: list[dict], output_dir: Path) -> None:
    """Write batch summary for multiple tickers.

    Args:
        results: List of Form 4 extraction result dictionaries
        output_dir: Output directory for batch summary
    """
    # JSON summary
    json_path = output_dir / "batch_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": utcnow_iso(),
                "tickers_processed": len(results),
                "results": results,
            },
            f,
            indent=2,
        )
    print(f"\nSaved batch summary JSON: {json_path}")

    # Markdown summary
    md_path = output_dir / "batch_summary.md"
    lines = []

    lines.append("# Form 4 Batch Summary")
    lines.append("")
    lines.append(f"**Generated:** {utcnow_iso()}")
    lines.append(f"**Tickers Processed:** {len(results)}")
    lines.append("")

    lines.append("| Ticker | Company | Filings Found | Purchases | Sales | Purchase Value | Sale Value | Distinct Buyers | Distinct Sellers |")
    lines.append("|--------|---------|---------------|-----------|-------|----------------|------------|-----------------|------------------|")

    for r in results:
        lines.append(
            f"| {r['ticker']} | {r['company_name'] or 'N/A'} | {r['summary']['form4_filings_found']} | "
            f"{r['summary']['open_market_purchases']} | {r['summary']['open_market_sales']} | "
            f"${r['summary']['open_market_purchase_value']:,.2f} | ${r['summary']['open_market_sale_value']:,.2f} | "
            f"{r['summary']['distinct_buyers']} | {r['summary']['distinct_sellers']} |"
        )

    lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved batch summary Markdown: {md_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract Form 4 insider transactions for one or more tickers"
    )
    parser.add_argument("--ticker", help="Single ticker symbol (e.g., MAIA)")
    parser.add_argument(
        "--tickers", help="Comma-separated list of ticker symbols (e.g., MAIA,NVDA)"
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=1460,
        help="Lookback window in days (default: 1460 = 4 years)",
    )
    parser.add_argument("--output-dir", required=True, help="Output directory for reports")

    args = parser.parse_args()

    if not args.ticker and not args.tickers:
        print("ERROR: Must specify either --ticker or --tickers")
        return 1

    output_dir = Path(args.output_dir)

    # Single ticker mode
    if args.ticker:
        _extract_ticker_form4_transactions(
            ticker=args.ticker.upper(),
            lookback_days=args.lookback_days,
            output_dir=output_dir,
        )
        return 0

    # Batch mode
    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    results = []

    for ticker in tickers:
        ticker_output_dir = output_dir / ticker
        result = _extract_ticker_form4_transactions(
            ticker=ticker,
            lookback_days=args.lookback_days,
            output_dir=ticker_output_dir,
        )
        results.append(result)

    # Write batch summary
    _write_batch_summary(results, output_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
