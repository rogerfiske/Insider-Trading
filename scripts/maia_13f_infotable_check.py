"""MAIA 13F InfoTable matching validation script.

Validates 13F InfoTable XML parsing and ticker/issuer matching by checking for
MAIA Biotechnology, Inc. institutional holdings in recent 13F-HR filings.

This script:
1. Fetches recent 13F-HR filings from configured institutional managers
2. Parses 13F information table XML
3. Matches MAIA holdings by CUSIP and/or normalized issuer name
4. Produces markdown report and JSON output
5. Reports match confidence and limitations

Safety:
- Report-only (no alerts, no Telegram, no email)
- Does not modify scheduled tasks
- Does not use Roger's spreadsheet or OpenInsider data
- Does not print .env or secrets

Usage:
    python scripts/maia_13f_infotable_check.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from sources.sec_13f import DEFAULT_MANAGERS
from sources.sec_13f_parser import fetch_and_parse_13f_info_table
from sources.sec_13f_matcher import match_ticker_to_13f_holdings
from sources.sec_common import sec_fetch


# MAIA target identifiers
MAIA_TICKER = "MAIA"
MAIA_CIK = "0001878313"
MAIA_COMPANY_NAME = "MAIA Biotechnology, Inc."
MAIA_CUSIP = None  # CUSIP not readily available from public ticker resolution


def fetch_recent_13f_filing_metadata(manager_cik: str) -> dict | None:
    """Fetch recent 13F-HR filing metadata for a manager.

    Args:
        manager_cik: Manager CIK (10-digit zero-padded)

    Returns:
        Dict with accession, filing_date, report_date, primary_document or None
    """
    url = f"https://data.sec.gov/submissions/CIK{manager_cik}.json"
    resp = sec_fetch(url, cache_max_age=86400)  # 24h cache

    if not resp["ok"]:
        return None

    try:
        data = json.loads(resp["body"])
    except json.JSONDecodeError:
        return None

    # Find the most recent 13F-HR
    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])
    report_dates = recent.get("reportDate", [])

    for idx, form in enumerate(forms):
        if form in ("13F-HR", "13F-HR/A"):
            return {
                "accession": accessions[idx] if idx < len(accessions) else "",
                "filing_date": dates[idx] if idx < len(dates) else "",
                "report_date": report_dates[idx] if idx < len(report_dates) else "",
                "primary_document": primary_docs[idx] if idx < len(primary_docs) else "",
            }

    return None


def check_maia_13f_holdings() -> dict:
    """Check for MAIA holdings in recent 13F-HR filings.

    Returns:
        Dict with filings reviewed, matches found, and aggregate summary
    """
    filings_reviewed = []
    infotables_parsed = []
    all_matches = []

    print(f"Checking for {MAIA_COMPANY_NAME} ({MAIA_TICKER}) in recent 13F-HR filings...")
    print(f"Target CIK: {MAIA_CIK}")
    print(f"Target CUSIP: {MAIA_CUSIP or 'Not available (will use issuer name matching)'}")
    print()

    for manager_name, manager_cik in DEFAULT_MANAGERS:
        print(f"Checking {manager_name} (CIK {manager_cik})...")

        # Fetch recent 13F filing metadata
        filing_meta = fetch_recent_13f_filing_metadata(manager_cik)

        if not filing_meta:
            print(f"  WARNING: No recent 13F-HR filing found")
            filings_reviewed.append({
                "manager_name": manager_name,
                "manager_cik": manager_cik,
                "status": "no_filing_found",
                "error": "No recent 13F-HR filing found in submissions",
            })
            continue

        accession = filing_meta["accession"]
        filing_date = filing_meta["filing_date"]
        report_date = filing_meta["report_date"]
        primary_doc = filing_meta["primary_document"]

        print(f"  Found filing: {accession} (filed {filing_date}, period {report_date})")

        filings_reviewed.append({
            "manager_name": manager_name,
            "manager_cik": manager_cik,
            "accession": accession,
            "filing_date": filing_date,
            "report_date": report_date,
            "primary_document": primary_doc,
            "status": "fetched",
        })

        # Fetch and parse 13F information table
        print(f"  Parsing InfoTable XML...")
        parse_result = fetch_and_parse_13f_info_table(
            accession_number=accession,
            cik=manager_cik,
            manager_name=manager_name,
            filing_date=filing_date,
            report_period=report_date,
            primary_document=primary_doc,
        )

        if parse_result.parse_status == "failed":
            print(f"  WARNING: Parse failed: {parse_result.error_message}")
            infotables_parsed.append({
                "manager_name": manager_name,
                "accession": accession,
                "parse_status": "failed",
                "error_type": parse_result.error_type,
                "error_message": parse_result.error_message,
                "holdings_count": 0,
            })
            continue

        print(f"  OK: Parsed {parse_result.total_holdings} holdings (total value: ${parse_result.total_value_usd:,.0f})")

        infotables_parsed.append({
            "manager_name": manager_name,
            "accession": accession,
            "parse_status": parse_result.parse_status,
            "holdings_count": parse_result.total_holdings,
            "total_value_usd": parse_result.total_value_usd,
        })

        # Match MAIA holdings
        print(f"  Matching {MAIA_TICKER} holdings...")
        matches = match_ticker_to_13f_holdings(
            ticker=MAIA_TICKER,
            resolved_company_name=MAIA_COMPANY_NAME,
            resolved_cik=MAIA_CIK,
            holdings=parse_result.holdings,
            cusip=MAIA_CUSIP,
        )

        if matches:
            for match in matches:
                print(f"  ** MATCH FOUND: {match.holding.issuer_name}")
                print(f"      Confidence: {match.confidence}")
                print(f"      Method: {match.match_method}")
                print(f"      Shares: {match.holding.shares_or_principal_amount:,.0f}")
                print(f"      Value: ${match.holding.value_usd:,.0f}")
                print(f"      Report period: {match.holding.report_period}")

                all_matches.append({
                    "manager_name": match.holding.manager_name,
                    "manager_cik": match.holding.manager_cik,
                    "accession": match.holding.filing_accession,
                    "report_period": match.holding.report_period,
                    "issuer_name": match.holding.issuer_name,
                    "title_of_class": match.holding.title_of_class,
                    "cusip": match.holding.cusip,
                    "shares": match.holding.shares_or_principal_amount,
                    "value_usd": match.holding.value_usd,
                    "confidence": match.confidence,
                    "match_method": match.match_method,
                })
        else:
            print(f"  No MAIA matches found")

        print()

    # Aggregate summary
    total_managers_with_matches = len(set(m["manager_name"] for m in all_matches))
    total_shares = sum(m["shares"] for m in all_matches)
    total_value_usd = sum(m["value_usd"] for m in all_matches)

    highest_confidence = "none"
    if all_matches:
        confidence_priority = {
            "EXACT_CUSIP": 4,
            "EXACT_ISSUER_NAME": 3,
            "NORMALIZED_ISSUER_NAME": 2,
            "FUZZY_ISSUER_NAME": 1,
        }
        highest_confidence = max(
            all_matches,
            key=lambda m: confidence_priority.get(m["confidence"], 0)
        )["confidence"]

    return {
        "ticker": MAIA_TICKER,
        "cik": MAIA_CIK,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "target_resolution": {
            "issuer_name": MAIA_COMPANY_NAME,
            "cusip_candidates": [],
            "cusip_confidence": "unknown",
        },
        "filings_reviewed": filings_reviewed,
        "infotables_parsed": infotables_parsed,
        "matches": all_matches,
        "aggregate_summary": {
            "reliable_matches_found": len(all_matches) > 0,
            "total_managers": total_managers_with_matches,
            "total_shares": total_shares,
            "total_reported_value": total_value_usd,
            "highest_confidence": highest_confidence,
        },
        "limitations": [
            "13F has 45-day reporting lag from quarter-end",
            "13F only reports long positions >$200k or >10k shares threshold",
            "Derivatives, shorts, and synthetic positions not fully visible",
            "Private placements and warrants may not appear cleanly",
            "CUSIP not available for MAIA ticker resolution (name matching used)",
            "Name matching may have false positives/negatives without CUSIP confirmation",
        ],
        "safety": {
            "openinsider_spreadsheet_used": False,
            "telegram_sent": False,
            "email_sent": False,
            "scheduled_tasks_modified": False,
            "env_printed_or_changed": False,
        },
    }


def generate_markdown_report(results: dict) -> str:
    """Generate markdown report from 13F matching results.

    Args:
        results: Results dict from check_maia_13f_holdings()

    Returns:
        Markdown report content
    """
    report_lines = []

    report_lines.append(f"# MAIA Biotechnology, Inc. — 13F Institutional Holdings Matching Report")
    report_lines.append("")
    report_lines.append(f"**Ticker:** {results['ticker']}")
    report_lines.append(f"**CIK:** {results['cik']}")
    report_lines.append(f"**Generated:** {results['generated_at']}")
    report_lines.append(f"**Checkpoint:** CP23F")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Executive Summary
    report_lines.append("## Executive Summary")
    report_lines.append("")

    summary = results["aggregate_summary"]
    if summary["reliable_matches_found"]:
        report_lines.append(f"**{summary['total_managers']} institutional manager(s)** with MAIA holdings found in recent 13F-HR filings.")
        report_lines.append("")
        report_lines.append(f"- **Total shares:** {summary['total_shares']:,.0f}")
        report_lines.append(f"- **Total reported value:** ${summary['total_reported_value']:,.0f}")
        report_lines.append(f"- **Highest confidence:** {summary['highest_confidence']}")
    else:
        report_lines.append("**No reliable 13F InfoTable matches found** for MAIA in the reviewed filing sample.")
        report_lines.append("")
        report_lines.append("This does not necessarily mean zero institutional ownership. Possible explanations:")
        report_lines.append("")
        report_lines.append("- Holdings below 13F reporting threshold ($200k or 10k shares)")
        report_lines.append("- Holdings held by managers not in reviewed sample (5 large managers)")
        report_lines.append("- Reporting lag (13F filed 45 days after quarter-end)")
        report_lines.append("- Name/CUSIP mismatch preventing automated matching")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Source Boundary
    report_lines.append("## Source Boundary")
    report_lines.append("")
    report_lines.append("**Sources used:**")
    report_lines.append("- SEC EDGAR 13F-HR filings (public data)")
    report_lines.append("- SEC submissions API for filing metadata")
    report_lines.append("- 13F information table XML parsing")
    report_lines.append("")
    report_lines.append("**Sources NOT used:**")
    report_lines.append("- Roger's uploaded MAIA spreadsheet")
    report_lines.append("- OpenInsider data")
    report_lines.append("- Third-party institutional ownership pages")
    report_lines.append("- Private/paid data sources")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Target Resolution
    report_lines.append("## Target Issuer/Ticker/CUSIP Resolution")
    report_lines.append("")
    report_lines.append(f"**Ticker:** {results['ticker']}")
    report_lines.append(f"**CIK:** {results['cik']}")
    report_lines.append(f"**Issuer Name:** {results['target_resolution']['issuer_name']}")
    report_lines.append(f"**CUSIP:** {results['target_resolution']['cusip_candidates'] or 'Not available (using issuer name matching)'}")
    report_lines.append(f"**CUSIP Confidence:** {results['target_resolution']['cusip_confidence']}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # 13F Method
    report_lines.append("## 13F Method Used")
    report_lines.append("")
    report_lines.append("1. Fetch recent 13F-HR filing metadata from SEC submissions API")
    report_lines.append("2. Locate and fetch 13F information table XML from SEC EDGAR")
    report_lines.append("3. Parse XML to extract individual security holdings")
    report_lines.append("4. Match MAIA holdings using:")
    report_lines.append("   - CUSIP exact match (if available) → High confidence")
    report_lines.append("   - Issuer name exact match → Medium confidence")
    report_lines.append("   - Issuer name normalized match → Medium confidence")
    report_lines.append("   - Issuer name fuzzy match → Low confidence (excluded from results)")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Filings Reviewed
    report_lines.append("## 13F Filings/Periods Reviewed")
    report_lines.append("")
    report_lines.append(f"**Managers reviewed:** {len(results['filings_reviewed'])}")
    report_lines.append("")

    for filing in results["filings_reviewed"]:
        if filing["status"] == "fetched":
            report_lines.append(f"- **{filing['manager_name']}** (CIK {filing['manager_cik']})")
            report_lines.append(f"  - Accession: {filing['accession']}")
            report_lines.append(f"  - Filing date: {filing['filing_date']}")
            report_lines.append(f"  - Report period: {filing['report_date']}")
        else:
            report_lines.append(f"- **{filing['manager_name']}** (CIK {filing['manager_cik']}): {filing.get('error', 'No filing found')}")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # InfoTable Parse Results
    report_lines.append("## InfoTable Parse Results")
    report_lines.append("")
    report_lines.append(f"**InfoTables parsed:** {len(results['infotables_parsed'])}")
    report_lines.append("")

    for parsed in results["infotables_parsed"]:
        status_icon = "[OK]" if parsed["parse_status"] == "success" else "[WARN]"
        report_lines.append(f"{status_icon} **{parsed['manager_name']}**")
        report_lines.append(f"  - Parse status: {parsed['parse_status']}")
        report_lines.append(f"  - Holdings parsed: {parsed['holdings_count']:,}")
        if parsed.get("total_value_usd"):
            report_lines.append(f"  - Total portfolio value: ${parsed['total_value_usd']:,.0f}")
        if parsed.get("error_message"):
            report_lines.append(f"  - Error: {parsed['error_message']}")
        report_lines.append("")

    report_lines.append("---")
    report_lines.append("")

    # Matched Holdings
    report_lines.append("## Matched MAIA Holdings")
    report_lines.append("")

    if results["matches"]:
        report_lines.append("| Manager | Report Period | Shares | Value (USD) | Confidence | Match Method |")
        report_lines.append("|---------|---------------|--------|-------------|------------|--------------|")

        for match in results["matches"]:
            report_lines.append(
                f"| {match['manager_name']} | "
                f"{match['report_period']} | "
                f"{match['shares']:,.0f} | "
                f"${match['value_usd']:,.0f} | "
                f"{match['confidence']} | "
                f"{match['match_method']} |"
            )
    else:
        report_lines.append("No MAIA matches found in reviewed filings.")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Match Confidence
    report_lines.append("## Match Confidence and Basis")
    report_lines.append("")

    if results["matches"]:
        report_lines.append(f"**Highest confidence level:** {summary['highest_confidence']}")
        report_lines.append("")
        report_lines.append("**Confidence scale:**")
        report_lines.append("- `EXACT_CUSIP`: CUSIP-based match (highest confidence)")
        report_lines.append("- `EXACT_ISSUER_NAME`: Exact issuer name match (high confidence)")
        report_lines.append("- `NORMALIZED_ISSUER_NAME`: Normalized name match (medium confidence)")
        report_lines.append("- `FUZZY_ISSUER_NAME`: Fuzzy/substring match (low confidence, excluded)")
        report_lines.append("")
        report_lines.append("**Match basis:**")

        for match in results["matches"]:
            report_lines.append(f"- {match['manager_name']}: {match['match_method']}")
    else:
        report_lines.append("No matches found. Confidence assessment not applicable.")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Limitations
    report_lines.append("## Limitations")
    report_lines.append("")

    for limitation in results["limitations"]:
        report_lines.append(f"- {limitation}")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Monitoring Baseline Impact
    report_lines.append("## Impact on CP23D/CP23E Monitoring Baseline")
    report_lines.append("")

    if summary["reliable_matches_found"]:
        report_lines.append("**13F InfoTable matching implemented and validated with MAIA matches found.**")
        report_lines.append("")
        report_lines.append(f"**Recommended baseline update:**")
        report_lines.append(f"- Update MAIA monitoring baseline to reflect {summary['total_managers']} institutional holder(s)")
        report_lines.append(f"- Note report period lag (13F filed 45 days after quarter-end)")
        report_lines.append(f"- Include match confidence level in monitoring notes")
    else:
        report_lines.append("**13F InfoTable matching implemented but no reliable MAIA matches found in reviewed sample.**")
        report_lines.append("")
        report_lines.append("**Recommended baseline update:**")
        report_lines.append("- Update MAIA monitoring baseline to note: \"13F InfoTable matching implemented; no reliable matches found in reviewed sample (5 large managers, most recent quarter)\"")
        report_lines.append("- Continue manual quarterly 13F checks")
        report_lines.append("- Future automation can expand to more managers or direct CUSIP lookup")

    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    # Safety Confirmations
    report_lines.append("## Safety Confirmations")
    report_lines.append("")
    report_lines.append("- Roger's uploaded MAIA spreadsheet: **NOT USED**")
    report_lines.append("- OpenInsider data: **NOT USED**")
    report_lines.append("- Telegram messages sent: **NO**")
    report_lines.append("- Email sent: **NO**")
    report_lines.append("- Scheduled tasks modified: **NO**")
    report_lines.append("- Scheduled tasks triggered: **NO**")
    report_lines.append("- .env printed or changed: **NO**")
    report_lines.append("- Secrets printed: **NO**")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("**End of MAIA 13F InfoTable Matching Report**")
    report_lines.append("")
    report_lines.append(f"**Checkpoint:** CP23F")
    report_lines.append(f"**Generated:** {results['generated_at']}")

    return "\n".join(report_lines)


def main() -> int:
    """Main entry point."""
    print("=" * 80)
    print("MAIA 13F InfoTable Matching Validation")
    print("=" * 80)
    print()

    # Check for MAIA 13F holdings
    results = check_maia_13f_holdings()

    # Create output directory
    output_dir = Path("docs/sample_reports/maia_13f")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON output
    json_path = output_dir / "MAIA_13F_infotable_matching.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"OK: JSON output written to: {json_path}")

    # Write markdown report
    markdown_content = generate_markdown_report(results)
    markdown_path = output_dir / "MAIA_13F_infotable_matching_report.md"
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f"OK: Markdown report written to: {markdown_path}")
    print()

    # Summary
    summary = results["aggregate_summary"]
    if summary["reliable_matches_found"]:
        print(f"** RESULT: {summary['total_managers']} institutional manager(s) with MAIA holdings found")
        print(f"   Total shares: {summary['total_shares']:,.0f}")
        print(f"   Total value: ${summary['total_reported_value']:,.0f}")
        print(f"   Highest confidence: {summary['highest_confidence']}")
    else:
        print("WARNING: No reliable MAIA matches found in reviewed sample")
        print("   (This does not necessarily mean zero institutional ownership)")

    print()
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
