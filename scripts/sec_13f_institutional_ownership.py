"""SEC 13F Institutional Ownership CLI for Generic Ticker Workflow (CP24G).

Integrates 13F InfoTable matching into the generic ticker workflow to identify
institutional ownership by major asset managers.

This is a report-only tool. It does not generate alerts, send Telegram/email,
modify scheduled tasks, or use Roger's OpenInsider spreadsheet.

Usage:
    python scripts/sec_13f_institutional_ownership.py --ticker MAIA --output-dir docs/sample_reports/13f_institutional_ownership/MAIA
    python scripts/sec_13f_institutional_ownership.py --tickers MAIA,NVDA --output-dir docs/sample_reports/13f_institutional_ownership/batch
    python scripts/sec_13f_institutional_ownership.py --ticker NVDA --output-dir docs/sample_reports/13f_institutional_ownership/NVDA --manager-ciks 0001067983,0001350694
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from sources.sec_13f import DEFAULT_MANAGERS
from sources.sec_13f_parser import (
    Form13FHolding,
    Form13FParseResult,
    fetch_and_parse_13f_info_table,
)
from sources.sec_13f_matcher import (
    IssuerIdentifier,
    match_ticker_to_13f_holdings,
    summarize_13f_matches_for_report,
)
from sources.sec_common import utcnow_iso
from sources.sec_submissions import fetch_company_submissions
from sources.sec_ticker import resolve_ticker_to_cik


def process_single_ticker_13f_ownership(
    ticker: str,
    manager_universe: list[tuple[str, str]],
) -> dict[str, Any]:
    """Process a single ticker for 13F institutional ownership.

    Args:
        ticker: Stock ticker symbol
        manager_universe: List of (manager_name, manager_cik) tuples

    Returns:
        Dictionary with 13F ownership results
    """
    print(f"\nProcessing ticker: {ticker}")

    # Resolve ticker to CIK
    resolver_result = resolve_ticker_to_cik(ticker)

    if not resolver_result.ok:
        print(f"  ERROR: Ticker resolution failed: {resolver_result.error_message}")
        return {
            "ticker": ticker.upper(),
            "status": "failed",
            "error_type": "ticker_resolution_failed",
            "error_message": resolver_result.error_message,
            "cik": None,
            "company_name": None,
            "managers_reviewed": [],
            "managers_parsed_successfully": [],
            "managers_parse_failed": [],
            "matches": [],
            "aggregate_stats": {
                "total_managers_reviewed": len(manager_universe),
                "total_managers_parsed_successfully": 0,
                "total_managers_parse_failed": len(manager_universe),
                "total_holdings_parsed": 0,
                "match_count": 0,
                "total_value_usd": 0.0,
                "total_shares": 0.0,
            },
            "partial_visibility_note": f"Ticker {ticker} could not be resolved to a CIK. No 13F matching was performed.",
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

    cik = resolver_result.cik_padded
    company_name = resolver_result.company_name

    print(f"  Resolved: {ticker} -> CIK {cik} ({company_name})")

    # Build issuer identifier for matching
    issuer = IssuerIdentifier(
        ticker=ticker,
        cik=cik,
        company_name=company_name,
        cusip=None,  # CUSIP not available from ticker resolution
    )

    print(f"  Issuer matching keys: {issuer.normalized_names}")

    # Process each manager in the universe
    managers_reviewed = []
    managers_parsed_successfully = []
    managers_parse_failed = []
    all_matches = []
    total_holdings_parsed = 0

    for manager_name, manager_cik in manager_universe:
        print(f"  Processing manager: {manager_name} (CIK {manager_cik})")

        manager_diagnostic = {
            "manager_name": manager_name,
            "manager_cik": manager_cik,
            "parse_status": "pending",
            "holdings_count": 0,
            "matches_count": 0,
            "error_type": None,
            "error_message": None,
        }

        # Fetch manager's submissions to get latest 13F-HR
        submissions = fetch_company_submissions(manager_cik)

        if not submissions["ok"]:
            print(f"    ERROR: Failed to fetch submissions: {submissions.get('error', 'Unknown error')}")
            manager_diagnostic["parse_status"] = "failed"
            manager_diagnostic["error_type"] = "submissions_fetch_failed"
            manager_diagnostic["error_message"] = submissions.get("error", "Unknown error")
            managers_parse_failed.append(manager_diagnostic)
            managers_reviewed.append(manager_diagnostic)
            continue

        # Get submissions data (already parsed as dict)
        submissions_data = submissions.get("body", {})
        if not isinstance(submissions_data, dict):
            print(f"    ERROR: Unexpected submissions format: {type(submissions_data)}")
            manager_diagnostic["parse_status"] = "failed"
            manager_diagnostic["error_type"] = "submissions_format_error"
            manager_diagnostic["error_message"] = f"Unexpected format: {type(submissions_data)}"
            managers_parse_failed.append(manager_diagnostic)
            managers_reviewed.append(manager_diagnostic)
            continue

        # Find latest 13F-HR filing
        recent_filings = submissions_data.get("filings", {}).get("recent", {})
        forms = recent_filings.get("form", [])
        accessions = recent_filings.get("accessionNumber", [])
        filing_dates = recent_filings.get("filingDate", [])
        report_dates = recent_filings.get("reportDate", [])
        primary_docs = recent_filings.get("primaryDocument", [])

        latest_13f = None
        for idx, form in enumerate(forms):
            if form in ("13F-HR", "13F-HR/A"):
                latest_13f = {
                    "accession_number": accessions[idx] if idx < len(accessions) else "",
                    "filing_date": filing_dates[idx] if idx < len(filing_dates) else "",
                    "report_period": report_dates[idx] if idx < len(report_dates) else "",
                    "primary_document": primary_docs[idx] if idx < len(primary_docs) else "",
                }
                break

        if not latest_13f:
            print(f"    No 13F-HR filing found")
            manager_diagnostic["parse_status"] = "failed"
            manager_diagnostic["error_type"] = "no_13f_filing_found"
            manager_diagnostic["error_message"] = "No 13F-HR filing found in recent submissions"
            managers_parse_failed.append(manager_diagnostic)
            managers_reviewed.append(manager_diagnostic)
            continue

        print(
            f"    Found 13F-HR: {latest_13f['accession_number']} "
            f"(filed {latest_13f['filing_date']}, period {latest_13f['report_period']})"
        )

        # Fetch and parse 13F InfoTable
        parse_result = fetch_and_parse_13f_info_table(
            accession_number=latest_13f["accession_number"],
            cik=manager_cik,
            manager_name=manager_name,
            filing_date=latest_13f["filing_date"],
            report_period=latest_13f["report_period"],
            primary_document=latest_13f["primary_document"],
        )

        if parse_result.parse_status == "failed":
            print(f"    ERROR: Parse failed: {parse_result.error_message}")
            manager_diagnostic["parse_status"] = "failed"
            manager_diagnostic["error_type"] = parse_result.error_type
            manager_diagnostic["error_message"] = parse_result.error_message
            managers_parse_failed.append(manager_diagnostic)
            managers_reviewed.append(manager_diagnostic)
            continue

        holdings_count = len(parse_result.holdings)
        print(f"    Parsed {holdings_count} holdings (status: {parse_result.parse_status})")

        total_holdings_parsed += holdings_count

        # Match target issuer against holdings
        matches = match_ticker_to_13f_holdings(
            ticker=ticker,
            resolved_company_name=company_name,
            resolved_cik=cik,
            holdings=parse_result.holdings,
            cusip=None,
        )

        matches_count = len(matches)
        print(f"    Found {matches_count} matches for {ticker}")

        manager_diagnostic["parse_status"] = parse_result.parse_status
        manager_diagnostic["holdings_count"] = holdings_count
        manager_diagnostic["matches_count"] = matches_count

        managers_parsed_successfully.append(manager_diagnostic)
        managers_reviewed.append(manager_diagnostic)
        all_matches.extend(matches)

    # Summarize matches
    match_summary = summarize_13f_matches_for_report(ticker, all_matches)

    # Build aggregate stats
    aggregate_stats = {
        "total_managers_reviewed": len(manager_universe),
        "total_managers_parsed_successfully": len(managers_parsed_successfully),
        "total_managers_parse_failed": len(managers_parse_failed),
        "total_holdings_parsed": total_holdings_parsed,
        "match_count": match_summary["match_count"],
        "total_value_usd": match_summary["total_value_usd"],
        "total_shares": match_summary["total_shares"],
    }

    print(f"\nAggregate stats:")
    print(f"  Managers reviewed: {aggregate_stats['total_managers_reviewed']}")
    print(f"  Managers parsed successfully: {aggregate_stats['total_managers_parsed_successfully']}")
    print(f"  Managers parse failed: {aggregate_stats['total_managers_parse_failed']}")
    print(f"  Total holdings parsed: {aggregate_stats['total_holdings_parsed']}")
    print(f"  Matches found: {aggregate_stats['match_count']}")
    print(f"  Total value (USD): ${aggregate_stats['total_value_usd']:,.2f}")
    print(f"  Total shares: {aggregate_stats['total_shares']:,.0f}")

    # Build partial visibility note
    if aggregate_stats["match_count"] == 0:
        partial_visibility_note = (
            f"No reliable matches among successfully parsed reviewed managers. "
            f"Institutional visibility is partial: limited to {aggregate_stats['total_managers_reviewed']} "
            f"managers reviewed, {aggregate_stats['total_managers_parsed_successfully']} parsed successfully. "
            f"Parse failures: {', '.join([m['manager_name'] for m in managers_parse_failed])}."
        )
    else:
        partial_visibility_note = (
            f"Matched {aggregate_stats['match_count']} holdings among "
            f"{aggregate_stats['total_managers_parsed_successfully']} successfully parsed managers. "
            f"Institutional visibility is partial: limited to {aggregate_stats['total_managers_reviewed']} "
            f"managers reviewed. Parse failures: {', '.join([m['manager_name'] for m in managers_parse_failed]) if managers_parse_failed else 'None'}."
        )

    # Build result
    result = {
        "ticker": ticker.upper(),
        "status": "success",
        "cik": cik,
        "company_name": company_name,
        "generated_at": utcnow_iso(),
        "manager_universe": [
            {"name": name, "cik": cik_val} for name, cik_val in manager_universe
        ],
        "managers_reviewed": managers_reviewed,
        "managers_parsed_successfully": managers_parsed_successfully,
        "managers_parse_failed": managers_parse_failed,
        "matches": [
            {
                "manager_name": match.holding.manager_name,
                "manager_cik": match.holding.manager_cik,
                "report_period": match.holding.report_period,
                "issuer_name": match.holding.issuer_name,
                "cusip": match.holding.cusip,
                "value_usd": match.holding.value_usd,
                "shares": match.holding.shares_or_principal_amount,
                "confidence": match.confidence,
                "match_method": match.match_method,
            }
            for match in all_matches
        ],
        "aggregate_stats": aggregate_stats,
        "partial_visibility_note": partial_visibility_note,
        "cp23f_reconciliation": None,  # Will be added for MAIA
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

    # Add CP23F reconciliation for MAIA
    if ticker.upper() == "MAIA":
        result["cp23f_reconciliation"] = {
            "cp23f_baseline": {
                "manager_universe": 5,
                "managers_parsed": 3,
                "bridgewater_holdings": 993,
                "bridgewater_maia_matches": 0,
                "citadel_holdings": 15589,
                "citadel_maia_matches": 0,
                "two_sigma_holdings": 4546,
                "two_sigma_maia_matches": 0,
                "total_parsed_holdings": 21128,
                "maia_matches": 0,
            },
            "cp24g_result": {
                "manager_universe": aggregate_stats["total_managers_reviewed"],
                "managers_parsed": aggregate_stats["total_managers_parsed_successfully"],
                "total_parsed_holdings": aggregate_stats["total_holdings_parsed"],
                "maia_matches": aggregate_stats["match_count"],
            },
            "reconciliation_status": "pending_comparison",
            "reconciliation_note": (
                "CP23F baseline (2024-02-14): 3/5 managers parsed, 21,128 holdings, 0 MAIA matches. "
                "If CP24G differs, check filing updates or parser improvements."
            ),
        }

    return result


def generate_per_ticker_json(result: dict[str, Any]) -> dict[str, Any]:
    """Generate per-ticker JSON output (already in correct format)."""
    return result


def generate_per_ticker_markdown(result: dict[str, Any]) -> str:
    """Generate per-ticker Markdown report."""
    ticker = result["ticker"]
    status = result["status"]
    generated_at = result.get("generated_at", utcnow_iso())

    if status == "failed":
        return f"""# SEC 13F Institutional Ownership: {ticker}

**Generated:** {generated_at}

## Status

**FAILED:** {result.get('error_message', 'Unknown error')}

## Partial Visibility Note

{result.get('partial_visibility_note', 'No data available')}

## Safety Confirmations

- **Report Only:** True
- **Alerts Generated:** False
- **OpenInsider Spreadsheet Used:** False
- **Telegram Sent:** False
- **Email Sent:** False
"""

    company_name = result["company_name"]
    cik = result["cik"]
    aggregate = result["aggregate_stats"]
    partial_note = result["partial_visibility_note"]
    safety = result["safety"]

    md_lines = [
        f"# SEC 13F Institutional Ownership: {ticker}",
        "",
        f"**Generated:** {generated_at}",
        f"**Company:** {company_name}",
        f"**CIK:** {cik}",
        "",
        "## Purpose",
        "",
        "This report identifies institutional ownership by major asset managers using SEC 13F-HR filings and InfoTable matching.",
        "",
        "This is a report-only tool. No alerts were generated, no Telegram/email was sent, no scheduled tasks were modified, and OpenInsider data was not used.",
        "",
        "## Manager Universe",
        "",
        f"**Total managers reviewed:** {aggregate['total_managers_reviewed']}",
        "",
    ]

    for mgr in result["manager_universe"]:
        md_lines.append(f"- {mgr['name']} (CIK {mgr['cik']})")

    md_lines.append("")

    md_lines.extend(
        [
            "## Parsing Results",
            "",
            f"**Managers parsed successfully:** {aggregate['total_managers_parsed_successfully']}",
            f"**Managers parse failed:** {aggregate['total_managers_parse_failed']}",
            f"**Total holdings parsed:** {aggregate['total_holdings_parsed']}",
            "",
        ]
    )

    # Manager diagnostics table
    md_lines.extend(
        [
            "### Manager Diagnostics",
            "",
            "| Manager | Parse Status | Holdings | Matches | Error |",
            "|---------|-------------|----------|---------|-------|",
        ]
    )

    for mgr in result["managers_reviewed"]:
        error = mgr.get("error_message", "-")[:50] if mgr.get("error_message") else "-"
        md_lines.append(
            f"| {mgr['manager_name']} | {mgr['parse_status']} | "
            f"{mgr['holdings_count']} | {mgr['matches_count']} | {error} |"
        )

    md_lines.append("")

    # Matches summary
    md_lines.extend(
        [
            "## Matches Summary",
            "",
            f"**Match count:** {aggregate['match_count']}",
            f"**Total value (USD):** ${aggregate['total_value_usd']:,.2f}",
            f"**Total shares:** {aggregate['total_shares']:,.0f}",
            "",
        ]
    )

    if result["matches"]:
        md_lines.extend(
            [
                "### Matched Holdings",
                "",
                "| Manager | Report Period | Issuer | CUSIP | Value (USD) | Shares | Confidence |",
                "|---------|---------------|--------|-------|-------------|--------|------------|",
            ]
        )

        for match in result["matches"]:
            md_lines.append(
                f"| {match['manager_name']} | {match['report_period']} | "
                f"{match['issuer_name']} | {match['cusip']} | "
                f"${match['value_usd']:,.2f} | {match['shares']:,.0f} | {match['confidence']} |"
            )

        md_lines.append("")
    else:
        md_lines.extend(
            [
                "No reliable matches found among successfully parsed reviewed managers.",
                "",
            ]
        )

    # Partial visibility note
    md_lines.extend(
        [
            "## Partial Visibility Note",
            "",
            partial_note,
            "",
            "**Important limitations:**",
            "",
            "- Institutional visibility is partial: limited to reviewed managers only",
            "- Parse failures reduce coverage",
            "- 13F filings reflect quarter-end positions, not real-time holdings",
            "- Small positions (<$200k or <10,000 shares) may be omitted from 13F",
            "",
        ]
    )

    # CP23F reconciliation for MAIA
    if result.get("cp23f_reconciliation"):
        recon = result["cp23f_reconciliation"]
        md_lines.extend(
            [
                "## CP23F Reconciliation (MAIA)",
                "",
                f"**CP23F Baseline:**",
                "",
                f"- Managers parsed: {recon['cp23f_baseline']['managers_parsed']}/{recon['cp23f_baseline']['manager_universe']}",
                f"- Bridgewater: {recon['cp23f_baseline']['bridgewater_holdings']} holdings, {recon['cp23f_baseline']['bridgewater_maia_matches']} MAIA matches",
                f"- Citadel: {recon['cp23f_baseline']['citadel_holdings']} holdings, {recon['cp23f_baseline']['citadel_maia_matches']} MAIA matches",
                f"- Two Sigma: {recon['cp23f_baseline']['two_sigma_holdings']} holdings, {recon['cp23f_baseline']['two_sigma_maia_matches']} MAIA matches",
                f"- Total parsed holdings: {recon['cp23f_baseline']['total_parsed_holdings']}",
                f"- MAIA matches: {recon['cp23f_baseline']['maia_matches']}",
                "",
                f"**CP24G Result:**",
                "",
                f"- Managers parsed: {recon['cp24g_result']['managers_parsed']}/{recon['cp24g_result']['manager_universe']}",
                f"- Total parsed holdings: {recon['cp24g_result']['total_parsed_holdings']}",
                f"- MAIA matches: {recon['cp24g_result']['maia_matches']}",
                "",
                f"**Reconciliation Note:**",
                "",
                recon["reconciliation_note"],
                "",
            ]
        )

    # Safety confirmations
    md_lines.extend(
        [
            "## Safety Confirmations",
            "",
            f"- **Report Only:** {safety['report_only']}",
            f"- **Alerts Generated:** {safety['alerts_generated']}",
            f"- **OpenInsider Spreadsheet Used:** {safety['openinsider_spreadsheet_used']}",
            f"- **Telegram Sent:** {safety['telegram_sent']}",
            f"- **Email Sent:** {safety['email_sent']}",
            f"- **Scheduled Tasks Modified:** {safety['scheduled_tasks_modified']}",
            f"- **Env Printed or Changed:** {safety['env_printed_or_changed']}",
            f"- **Buy/Sell/Hold Language Used:** {safety['buy_sell_hold_language_used']}",
            "",
        ]
    )

    return "\n".join(md_lines)


def generate_matches_csv(result: dict[str, Any]) -> str:
    """Generate CSV of matched holdings."""
    if not result["matches"]:
        return "manager_name,manager_cik,report_period,issuer_name,cusip,value_usd,shares,confidence,match_method\n"

    rows = []
    for match in result["matches"]:
        rows.append(
            [
                match["manager_name"],
                match["manager_cik"],
                match["report_period"],
                match["issuer_name"],
                match["cusip"],
                f"{match['value_usd']:.2f}",
                f"{match['shares']:.0f}",
                match["confidence"],
                match["match_method"],
            ]
        )

    output = "manager_name,manager_cik,report_period,issuer_name,cusip,value_usd,shares,confidence,match_method\n"
    for row in rows:
        output += ",".join(row) + "\n"

    return output


def generate_manager_diagnostics_csv(result: dict[str, Any]) -> str:
    """Generate CSV of manager diagnostics."""
    if not result["managers_reviewed"]:
        return "manager_name,manager_cik,parse_status,holdings_count,matches_count,error_type,error_message\n"

    rows = []
    for mgr in result["managers_reviewed"]:
        rows.append(
            [
                mgr["manager_name"],
                mgr["manager_cik"],
                mgr["parse_status"],
                str(mgr["holdings_count"]),
                str(mgr["matches_count"]),
                mgr.get("error_type") or "",
                mgr.get("error_message") or "",
            ]
        )

    output = "manager_name,manager_cik,parse_status,holdings_count,matches_count,error_type,error_message\n"
    for row in rows:
        # Escape commas and quotes in error messages
        escaped_row = []
        for field in row:
            if "," in field or '"' in field:
                escaped_row.append(f'"{field.replace(chr(34), chr(34)+chr(34))}"')
            else:
                escaped_row.append(field)
        output += ",".join(escaped_row) + "\n"

    return output


def generate_batch_summary_json(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate batch summary JSON for multiple tickers."""
    tickers_requested = [r["ticker"] for r in results]
    tickers_success = [r["ticker"] for r in results if r["status"] == "success"]
    tickers_failed = [r["ticker"] for r in results if r["status"] == "failed"]

    total_managers_reviewed = results[0]["aggregate_stats"]["total_managers_reviewed"] if results else 0
    total_matches = sum(r["aggregate_stats"]["match_count"] for r in results if r["status"] == "success")

    return {
        "generated_at": utcnow_iso(),
        "tickers_requested": tickers_requested,
        "tickers_success": tickers_success,
        "tickers_failed": tickers_failed,
        "manager_universe": results[0]["manager_universe"] if results else [],
        "per_ticker_results": results,
        "aggregate_stats": {
            "tickers_processed": len(results),
            "tickers_with_matches": sum(
                1 for r in results if r["status"] == "success" and r["aggregate_stats"]["match_count"] > 0
            ),
            "total_managers_reviewed": total_managers_reviewed,
            "total_matches": total_matches,
        },
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


def generate_batch_summary_markdown(batch_json: dict[str, Any]) -> str:
    """Generate batch summary Markdown report."""
    generated_at = batch_json["generated_at"]
    tickers_requested = batch_json["tickers_requested"]
    aggregate = batch_json["aggregate_stats"]
    safety = batch_json["safety"]

    md_lines = [
        "# SEC 13F Institutional Ownership - Batch Summary",
        "",
        f"**Generated:** {generated_at}",
        "",
        "## Requested Tickers",
        "",
        ", ".join(tickers_requested),
        "",
        "## Aggregate Statistics",
        "",
        f"- **Tickers processed:** {aggregate['tickers_processed']}",
        f"- **Tickers with matches:** {aggregate['tickers_with_matches']}",
        f"- **Managers reviewed per ticker:** {aggregate['total_managers_reviewed']}",
        f"- **Total matches across all tickers:** {aggregate['total_matches']}",
        "",
        "## Per-Ticker Results",
        "",
        "| Ticker | Status | Matches | Total Value (USD) |",
        "|--------|--------|---------|------------------|",
    ]

    for result in batch_json["per_ticker_results"]:
        ticker = result["ticker"]
        status = result["status"]
        if status == "success":
            matches = result["aggregate_stats"]["match_count"]
            value = result["aggregate_stats"]["total_value_usd"]
            md_lines.append(f"| {ticker} | {status} | {matches} | ${value:,.2f} |")
        else:
            md_lines.append(f"| {ticker} | {status} | - | - |")

    md_lines.append("")

    md_lines.extend(
        [
            "## Safety Confirmations",
            "",
            f"- **Report Only:** {safety['report_only']}",
            f"- **Alerts Generated:** {safety['alerts_generated']}",
            f"- **OpenInsider Spreadsheet Used:** {safety['openinsider_spreadsheet_used']}",
            f"- **Telegram Sent:** {safety['telegram_sent']}",
            f"- **Email Sent:** {safety['email_sent']}",
            f"- **Scheduled Tasks Modified:** {safety['scheduled_tasks_modified']}",
            f"- **Env Printed or Changed:** {safety['env_printed_or_changed']}",
            f"- **Buy/Sell/Hold Language Used:** {safety['buy_sell_hold_language_used']}",
            "",
        ]
    )

    return "\n".join(md_lines)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SEC 13F Institutional Ownership for Generic Ticker Workflow (CP24G)"
    )
    parser.add_argument("--ticker", help="Single ticker symbol")
    parser.add_argument("--tickers", help="Comma-separated ticker symbols")
    parser.add_argument("--output-dir", required=True, help="Output directory for reports")
    parser.add_argument(
        "--manager-ciks",
        help="Optional comma-separated manager CIKs (default: use DEFAULT_MANAGERS)",
    )

    args = parser.parse_args()

    # Determine ticker list
    if args.ticker:
        tickers = [args.ticker.strip()]
    elif args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",")]
    else:
        print("Error: Must specify --ticker or --tickers", file=sys.stderr)
        sys.exit(1)

    # Determine manager universe
    if args.manager_ciks:
        # Parse custom manager CIKs (must also provide names in a real implementation)
        # For simplicity, use DEFAULT_MANAGERS filtered by CIKs
        custom_ciks = [c.strip() for c in args.manager_ciks.split(",")]
        manager_universe = [
            (name, cik) for name, cik in DEFAULT_MANAGERS if cik in custom_ciks
        ]
        if not manager_universe:
            print(f"Warning: No managers found for CIKs {custom_ciks}, using DEFAULT_MANAGERS", file=sys.stderr)
            manager_universe = DEFAULT_MANAGERS
    else:
        manager_universe = DEFAULT_MANAGERS

    print(f"Manager universe: {len(manager_universe)} managers")
    for name, cik in manager_universe:
        print(f"  - {name} (CIK {cik})")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process tickers
    results = []
    for ticker in tickers:
        result = process_single_ticker_13f_ownership(ticker, manager_universe)
        results.append(result)

        # Write per-ticker outputs
        ticker_upper = ticker.upper()

        # JSON
        json_path = output_dir / f"{ticker_upper}_13f_institutional_ownership.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"  Wrote: {json_path}")

        # Markdown
        md_path = output_dir / f"{ticker_upper}_13f_institutional_ownership.md"
        md_content = generate_per_ticker_markdown(result)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"  Wrote: {md_path}")

        # Matches CSV
        matches_csv_path = output_dir / f"{ticker_upper}_13f_matches.csv"
        matches_csv_content = generate_matches_csv(result)
        with open(matches_csv_path, "w", encoding="utf-8") as f:
            f.write(matches_csv_content)
        print(f"  Wrote: {matches_csv_path}")

        # Manager diagnostics CSV
        diagnostics_csv_path = output_dir / f"{ticker_upper}_13f_manager_diagnostics.csv"
        diagnostics_csv_content = generate_manager_diagnostics_csv(result)
        with open(diagnostics_csv_path, "w", encoding="utf-8") as f:
            f.write(diagnostics_csv_content)
        print(f"  Wrote: {diagnostics_csv_path}")

    # Generate batch summary if multiple tickers
    if len(tickers) > 1:
        batch_json = generate_batch_summary_json(results)
        batch_md = generate_batch_summary_markdown(batch_json)

        batch_json_path = output_dir / "batch_13f_institutional_ownership_summary.json"
        batch_md_path = output_dir / "batch_13f_institutional_ownership_summary.md"

        with open(batch_json_path, "w", encoding="utf-8") as f:
            json.dump(batch_json, f, indent=2)
        print(f"  Wrote: {batch_json_path}")

        with open(batch_md_path, "w", encoding="utf-8") as f:
            f.write(batch_md)
        print(f"  Wrote: {batch_md_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
