#!/usr/bin/env python3
"""Extract Form 144 and Schedule 13D/G ownership filings for one or more tickers.

This script loads SEC submissions inventory (from CP24B), fetches and parses Form 144
and 13D/G filings, and generates JSON/Markdown/CSV reports.

Form 144 = Notice of proposed sale (NOT actual sale)
Schedule 13D = Active beneficial ownership (>5%, intent to influence)
Schedule 13G = Passive beneficial ownership (>5%, no intent to influence)

Usage:
    # Single ticker with 1460-day lookback
    python scripts/sec_ownership_filings.py --ticker MAIA --output-dir docs/sample_reports/ownership_filings/MAIA

    # Multiple tickers (batch mode)
    python scripts/sec_ownership_filings.py --tickers MAIA,NVDA --output-dir docs/sample_reports/ownership_filings/batch

    # Custom lookback period
    python scripts/sec_ownership_filings.py --ticker NVDA --lookback-days 730 --output-dir docs/sample_reports/ownership_filings/NVDA
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sources.sec_13dg import (
    Ownership13DG,
    OwnershipSummary,
    parse_13dg_filing,
)
from sources.sec_common import utcnow_iso
from sources.sec_form144 import (
    Form144Filing,
    Form144Summary,
    parse_form144_filing,
)
from sources.sec_submissions import (
    SecSubmissionFiling,
    build_submissions_inventory,
    fetch_company_submissions,
)
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
        cik=resolver_result.cik_padded,
        lookback_days=lookback_days,
        max_recent=max_recent_filings,
    )

    # Add ticker and company name to inventory
    inventory["ticker"] = ticker
    inventory["company_name"] = resolver_result.company_name

    return inventory


def _get_ownership_filings_from_cik(
    cik: str, lookback_days: int
) -> tuple[list[SecSubmissionFiling], list[SecSubmissionFiling]]:
    """Fetch Form 144 and 13D/G filings for a CIK.

    Args:
        cik: SEC Central Index Key
        lookback_days: Number of days to look back

    Returns:
        Tuple of (form144_filings, ownership_13dg_filings)
    """
    result = fetch_company_submissions(cik)

    if not result["ok"]:
        return ([], [])

    body = result["body"]
    filings_recent = body.get("filings", {}).get("recent", {})

    if not filings_recent:
        return ([], [])

    # Parallel arrays
    accession_numbers = filings_recent.get("accessionNumber", [])
    filing_dates = filings_recent.get("filingDate", [])
    report_dates = filings_recent.get("reportDate", [])
    acceptance_datetimes = filings_recent.get("acceptanceDateTime", [])
    forms = filings_recent.get("form", [])
    primary_documents = filings_recent.get("primaryDocument", [])
    primary_doc_descriptions = filings_recent.get("primaryDocDescription", [])

    # Calculate cutoff date
    now = datetime.now(timezone.utc)
    cutoff_date = (now - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    # Extract CIK without leading zeros
    cik_padded = cik.zfill(10)
    cik_no_leading_zeros = str(int(cik))

    form144_filings = []
    ownership_13dg_filings = []

    for i in range(len(accession_numbers)):
        filing_date = filing_dates[i]

        # Skip filings outside lookback window
        if filing_date < cutoff_date:
            continue

        form = forms[i]
        accession_number = accession_numbers[i]
        accession_no_dashes = accession_number.replace("-", "")

        # Build URLs
        archive_dir_url = (
            f"https://www.sec.gov/cgi-bin/browse-edgar"
            f"?action=getcompany&CIK={cik_padded}"
        )

        primary_document_url = (
            f"https://www.sec.gov/Archives/edgar/data/{cik_no_leading_zeros}/"
            f"{accession_no_dashes}/{primary_documents[i]}"
        )

        source_url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

        filing_obj = SecSubmissionFiling(
            cik=cik_padded,
            cik_no_leading_zeros=cik_no_leading_zeros,
            accession_number=accession_number,
            accession_no_dashes=accession_no_dashes,
            form=form,
            filing_date=filing_date,
            report_date=report_dates[i] if i < len(report_dates) else "",
            acceptance_datetime=(
                acceptance_datetimes[i] if i < len(acceptance_datetimes) else ""
            ),
            primary_document=primary_documents[i],
            primary_doc_description=(
                primary_doc_descriptions[i]
                if i < len(primary_doc_descriptions)
                else ""
            ),
            source_url=source_url,
            archive_directory_url=archive_dir_url,
            primary_document_url=primary_document_url,
        )

        # Classify by form type
        form_upper = form.upper()
        if form_upper == "144":
            form144_filings.append(filing_obj)
        elif "13D" in form_upper or "13G" in form_upper:
            ownership_13dg_filings.append(filing_obj)

    return (form144_filings, ownership_13dg_filings)


def _extract_ticker_ownership_filings(
    ticker: str,
    lookback_days: int,
    output_dir: Path,
) -> dict:
    """Extract Form 144 and 13D/G filings for a single ticker.

    Args:
        ticker: Stock ticker
        lookback_days: Lookback window in days
        output_dir: Output directory for reports

    Returns:
        Ownership extraction result dictionary
    """
    print(f"\nProcessing {ticker}...")

    # Load or create inventory
    inventory = _load_or_create_inventory(ticker, lookback_days, 500)

    if inventory.get("resolver", {}).get("status") == "failed":
        print(f"  ERROR: Ticker resolution failed for {ticker}")
        return {
            "ticker": ticker,
            "status": "failed",
            "error": "Ticker resolution failed",
            "form144": None,
            "ownership_13dg": None,
        }

    cik = inventory["cik"]
    company_name = inventory["company_name"]

    print(f"  Resolved {ticker} -> CIK {cik} ({company_name})")

    # Fetch Form 144 and 13D/G filings
    print(f"  Fetching Form 144 and 13D/G filings...")
    form144_submissions, ownership_13dg_submissions = _get_ownership_filings_from_cik(
        cik, lookback_days
    )

    print(
        f"  Found {len(form144_submissions)} Form 144 filings, "
        f"{len(ownership_13dg_submissions)} 13D/G filings"
    )

    # Parse Form 144 filings
    form144_filings = []
    for submission in form144_submissions:
        print(
            f"    Parsing Form 144: {submission.accession_number} "
            f"({submission.filing_date})"
        )
        filing = parse_form144_filing(submission)
        form144_filings.append(filing)

    # Parse 13D/G filings
    ownership_13dg_filings = []
    for submission in ownership_13dg_submissions:
        print(
            f"    Parsing {submission.form}: {submission.accession_number} "
            f"({submission.filing_date})"
        )
        filing = parse_13dg_filing(submission)
        ownership_13dg_filings.append(filing)

    # Generate summaries
    form144_summary = Form144Summary.from_filings(form144_filings)
    ownership_summary = OwnershipSummary.from_filings(ownership_13dg_filings)

    # Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save Form 144 outputs
    _save_form144_outputs(ticker, form144_filings, form144_summary, output_dir)

    # Save 13D/G outputs
    _save_13dg_outputs(ticker, ownership_13dg_filings, ownership_summary, output_dir)

    # Save combined JSON
    combined_output = {
        "ticker": ticker,
        "issuer_cik": cik,
        "company_name": company_name,
        "lookback_days": lookback_days,
        "form144_summary": form144_summary.to_dict(),
        "ownership_13dg_summary": ownership_summary.to_dict(),
        "report_only": True,
        "alert_enabled": False,
        "openinsider_required": False,
        "generated_at": utcnow_iso(),
    }

    json_path = output_dir / f"{ticker}_ownership_filings.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(combined_output, f, indent=2)

    print(f"  OK Saved combined JSON to {json_path}")

    # Generate Markdown report
    _generate_markdown_report(
        ticker, company_name, form144_summary, ownership_summary, output_dir
    )

    return {
        "ticker": ticker,
        "status": "success",
        "form144_count": len(form144_filings),
        "ownership_13dg_count": len(ownership_13dg_filings),
        "form144_summary": form144_summary.to_dict(),
        "ownership_summary": ownership_summary.to_dict(),
    }


def _save_form144_outputs(
    ticker: str,
    filings: list[Form144Filing],
    summary: Form144Summary,
    output_dir: Path,
):
    """Save Form 144 outputs (CSV)."""
    # Save CSV
    csv_path = output_dir / f"{ticker}_form144_filings.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if filings:
            fieldnames = list(filings[0].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for filing in filings:
                writer.writerow(filing.to_dict())

    print(f"  OK Saved Form 144 CSV to {csv_path}")


def _save_13dg_outputs(
    ticker: str,
    filings: list[Ownership13DG],
    summary: OwnershipSummary,
    output_dir: Path,
):
    """Save 13D/G outputs (CSV)."""
    # Save CSV
    csv_path = output_dir / f"{ticker}_13dg_filings.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if filings:
            fieldnames = list(filings[0].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for filing in filings:
                writer.writerow(filing.to_dict())

    print(f"  OK Saved 13D/G CSV to {csv_path}")


def _generate_markdown_report(
    ticker: str,
    company_name: str,
    form144_summary: Form144Summary,
    ownership_summary: OwnershipSummary,
    output_dir: Path,
):
    """Generate Markdown report for ownership filings."""
    md_path = output_dir / f"{ticker}_ownership_filings.md"

    lines = [
        f"# Ownership Filings Report: {ticker}",
        "",
        f"**Company:** {company_name}",
        f"**Report Generated:** {utcnow_iso()}",
        "",
        "---",
        "",
        "## Form 144 Summary (Notice of Proposed Sale)",
        "",
        f"- **Total Filings:** {form144_summary.total_filings}",
        f"- **Successful Parses:** {form144_summary.successful_parses}",
        f"- **Failed Parses:** {form144_summary.failed_parses}",
        f"- **Partial Parses:** {form144_summary.partial_parses}",
        f"- **Distinct Sellers:** {form144_summary.distinct_sellers}",
        f"- **Earliest Filing:** {form144_summary.earliest_filing_date or 'N/A'}",
        f"- **Latest Filing:** {form144_summary.latest_filing_date or 'N/A'}",
        "",
        "**Note:** Form 144 is a NOTICE of PROPOSED SALE, not an actual sale. "
        "These filings indicate intent to sell restricted securities within 90 days.",
        "",
        "---",
        "",
        "## Schedule 13D/G Summary (Beneficial Ownership)",
        "",
        f"- **Total Filings:** {ownership_summary.total_filings}",
        f"- **Active 13D Filings:** {ownership_summary.active_13d_count}",
        f"- **Passive 13G Filings:** {ownership_summary.passive_13g_count}",
        f"- **Amendment Filings:** {ownership_summary.amendment_count}",
        f"- **Successful Parses:** {ownership_summary.successful_parses}",
        f"- **Failed Parses:** {ownership_summary.failed_parses}",
        f"- **Partial Parses:** {ownership_summary.partial_parses}",
        f"- **Distinct Filers:** {ownership_summary.distinct_filers}",
        f"- **Earliest Filing:** {ownership_summary.earliest_filing_date or 'N/A'}",
        f"- **Latest Filing:** {ownership_summary.latest_filing_date or 'N/A'}",
        "",
        "**Note:** Schedule 13D indicates active beneficial ownership (>5%, intent to influence control). "
        "Schedule 13G indicates passive beneficial ownership (>5%, no intent to influence).",
        "",
        "---",
        "",
        "## Safety Flags",
        "",
        f"- **Report Only:** {form144_summary.report_only}",
        f"- **Alert Enabled:** {form144_summary.alert_enabled}",
        f"- **OpenInsider Required:** {form144_summary.openinsider_required}",
        "",
        "This report is for informational purposes only. It does not constitute investment advice "
        "or a recommendation to buy, sell, or hold any security.",
    ]

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  OK Saved Markdown report to {md_path}")


def _generate_batch_summary(
    ticker_results: list[dict], output_dir: Path
) -> dict:
    """Generate batch summary for multiple tickers."""
    successful = [r for r in ticker_results if r["status"] == "success"]
    failed = [r for r in ticker_results if r["status"] == "failed"]

    batch_summary = {
        "report_type": "ownership_filings_batch_summary",
        "report_only": True,
        "alert_enabled": False,
        "openinsider_required": False,
        "generated_at": utcnow_iso(),
        "tickers_processed": [r["ticker"] for r in ticker_results],
        "total_tickers": len(ticker_results),
        "successful_tickers": len(successful),
        "failed_tickers": len(failed),
        "ticker_summaries": ticker_results,
    }

    # Save batch summary JSON
    json_path = output_dir / "batch_ownership_filings_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(batch_summary, f, indent=2)

    print(f"\nOK Saved batch summary JSON to {json_path}")

    # Save batch summary Markdown
    md_path = output_dir / "batch_ownership_filings_summary.md"
    lines = [
        "# Ownership Filings Batch Summary",
        "",
        f"**Report Generated:** {utcnow_iso()}",
        "",
        "## Overview",
        "",
        f"- **Total Tickers:** {len(ticker_results)}",
        f"- **Successful:** {len(successful)}",
        f"- **Failed:** {len(failed)}",
        "",
        "## Ticker Results",
        "",
    ]

    for result in ticker_results:
        ticker = result["ticker"]
        status = result["status"]
        lines.append(f"### {ticker}")
        lines.append("")
        lines.append(f"- **Status:** {status}")

        if status == "success":
            lines.append(f"- **Form 144 Filings:** {result['form144_count']}")
            lines.append(f"- **13D/G Filings:** {result['ownership_13dg_count']}")
        else:
            lines.append(f"- **Error:** {result.get('error', 'Unknown')}")

        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Safety Flags",
            "",
            "- **Report Only:** True",
            "- **Alert Enabled:** False",
            "- **OpenInsider Required:** False",
            "",
            "This report is for informational purposes only. It does not constitute investment advice "
            "or a recommendation to buy, sell, or hold any security.",
        ]
    )

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"OK Saved batch summary Markdown to {md_path}")

    return batch_summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract Form 144 and Schedule 13D/G ownership filings for one or more tickers"
    )

    # Ticker arguments (mutually exclusive)
    ticker_group = parser.add_mutually_exclusive_group(required=True)
    ticker_group.add_argument("--ticker", help="Single ticker symbol")
    ticker_group.add_argument(
        "--tickers", help="Comma-separated list of ticker symbols (batch mode)"
    )

    # Optional arguments
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=1460,
        help="Number of days to look back (default: 1460 = 4 years)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Output directory for reports",
    )

    args = parser.parse_args()

    # Determine tickers to process
    if args.ticker:
        tickers = [args.ticker.upper()]
    else:
        tickers = [t.strip().upper() for t in args.tickers.split(",")]

    print(f"Extracting ownership filings for {len(tickers)} ticker(s): {', '.join(tickers)}")
    print(f"Lookback period: {args.lookback_days} days")
    print(f"Output directory: {args.output_dir}")

    # Process each ticker
    ticker_results = []
    for ticker in tickers:
        result = _extract_ticker_ownership_filings(
            ticker=ticker,
            lookback_days=args.lookback_days,
            output_dir=args.output_dir / ticker if len(tickers) > 1 else args.output_dir,
        )
        ticker_results.append(result)

    # Generate batch summary if multiple tickers
    if len(tickers) > 1:
        _generate_batch_summary(ticker_results, args.output_dir)

    # Print final summary
    successful_count = sum(1 for r in ticker_results if r["status"] == "success")
    failed_count = sum(1 for r in ticker_results if r["status"] == "failed")

    print("\n" + "=" * 80)
    print(f"SUMMARY: {successful_count}/{len(tickers)} tickers processed successfully")
    if failed_count > 0:
        print(f"  {failed_count} ticker(s) failed:")
        for r in ticker_results:
            if r["status"] == "failed":
                print(f"    - {r['ticker']}: {r.get('error', 'Unknown error')}")

    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
