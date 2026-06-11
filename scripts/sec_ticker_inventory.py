"""SEC Ticker/CIK Resolver and Submissions Inventory CLI.

Resolve ticker symbols to SEC CIK and build comprehensive submissions inventory
for downstream SEC extraction checkpoints (CP24C-CP24H).

This is a report-only foundation layer. It does not generate alerts, send Telegram/email,
modify scheduled tasks, or use Roger's OpenInsider spreadsheet.

Usage:
    python scripts/sec_ticker_inventory.py --ticker MAIA --output-dir docs/sample_reports/sec_inventory/MAIA
    python scripts/sec_ticker_inventory.py --tickers MAIA,NVDA --output-dir docs/sample_reports/sec_inventory/batch
"""

import argparse
import json
import sys
from pathlib import Path

from sources.sec_common import utcnow_iso
from sources.sec_submissions import build_submissions_inventory
from sources.sec_ticker import resolve_ticker_to_cik


def generate_per_ticker_json(
    ticker: str,
    resolver_result,
    submissions_result,
    max_recent_filings: int,
) -> dict:
    """Generate per-ticker JSON output following CP24B schema."""
    # Extract resolver info
    resolved = resolver_result.ok
    cik = resolver_result.cik_padded if resolved else ""
    company_name = resolver_result.company_name if resolved else ""

    resolver_status = "resolved" if resolved else "unresolved"
    resolver_evidence = []
    if resolved:
        resolver_evidence.append(
            {
                "source": "SEC company_tickers.json",
                "url": resolver_result.source_url,
                "retrieved_at": resolver_result.retrieved_at,
            }
        )

    # Extract submissions info
    submissions_status = "failed"
    submissions_data = {
        "recent_filings_count": 0,
        "filing_counts_by_form": {},
        "coverage_flags": {},
        "latest_filings": {},
        "recent_filings": [],
    }

    evidence_provenance = resolver_evidence.copy()

    if resolved and submissions_result["status"] in ("retrieved", "degraded"):
        submissions_status = submissions_result["status"]
        data = submissions_result["data"]

        submissions_data = {
            "recent_filings_count": len(data.get("recent_filings", [])),
            "filing_counts_by_form": data.get("filing_counts_by_form", {}),
            "coverage_flags": data.get("coverage_flags", {}),
            "latest_filings": {
                "latest_10k": data.get("latest_10k"),
                "latest_10q": data.get("latest_10q"),
                "latest_8k": data.get("latest_8k"),
                "latest_form4": data.get("latest_form4"),
                "latest_form144": data.get("latest_form144"),
                "latest_13d_or_13g": data.get("latest_13d_or_13g"),
                "latest_13f_hr": data.get("latest_13f_hr"),
            },
            "recent_filings": data.get("recent_filings", []),
        }

        evidence_provenance.append(
            {
                "source": "SEC submissions API",
                "url": data.get("source_url", ""),
                "retrieved_at": data.get("retrieved_at", ""),
            }
        )

    # Build downstream readiness
    downstream_readiness = {
        "form4_ready": submissions_data["coverage_flags"].get("has_form4", False),
        "form144_ready": submissions_data["coverage_flags"].get("has_form144", False),
        "ownership_13dg_ready": submissions_data["coverage_flags"].get(
            "has_13d_13g", False
        ),
        "xbrl_financials_ready": (
            submissions_data["coverage_flags"].get("has_10q", False)
            or submissions_data["coverage_flags"].get("has_10k", False)
        ),
        "capital_structure_ready": submissions_data["coverage_flags"].get(
            "has_s3_or_offering_filing", False
        ),
        "notes": [],
    }

    # Add readiness notes
    if not downstream_readiness["form4_ready"]:
        downstream_readiness["notes"].append(
            "No Form 4 filings found - insider transaction extraction (CP24C) will not yield data"
        )
    if not downstream_readiness["xbrl_financials_ready"]:
        downstream_readiness["notes"].append(
            "No 10-Q/10-K filings found - XBRL financial extraction (CP24E) will not yield data"
        )

    # Build degraded mode status
    degraded_mode = {"is_degraded": False, "reasons": []}

    if not resolved:
        degraded_mode["is_degraded"] = True
        degraded_mode["reasons"].append(f"Ticker resolution failed: {resolver_result.error_message}")
    elif submissions_status == "failed":
        degraded_mode["is_degraded"] = True
        degraded_mode["reasons"].append(f"Submissions retrieval failed: {submissions_result.get('error', 'Unknown error')}")
    elif submissions_status == "degraded":
        degraded_mode["is_degraded"] = True
        degraded_mode["reasons"].append(
            "Submissions retrieval succeeded but no recent filings found"
        )

    # Build JSON output
    output = {
        "ticker": ticker.upper(),
        "cik": cik,
        "company_name": company_name,
        "generated_at": utcnow_iso(),
        "resolver": {
            "status": resolver_status,
            "source": "SEC",
            "evidence": resolver_evidence,
        },
        "submissions": {
            "status": submissions_status,
            **submissions_data,
        },
        "downstream_readiness": downstream_readiness,
        "degraded_mode": degraded_mode,
        "evidence_provenance": evidence_provenance,
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

    return output


def generate_per_ticker_markdown(ticker_json: dict) -> str:
    """Generate per-ticker Markdown report from JSON data."""
    ticker = ticker_json["ticker"]
    cik = ticker_json["cik"]
    company_name = ticker_json["company_name"]
    generated_at = ticker_json["generated_at"]

    resolver = ticker_json["resolver"]
    submissions = ticker_json["submissions"]
    downstream = ticker_json["downstream_readiness"]
    degraded = ticker_json["degraded_mode"]
    safety = ticker_json["safety"]
    evidence = ticker_json["evidence_provenance"]

    md_lines = [
        f"# SEC Ticker/CIK Submissions Inventory: {ticker}",
        "",
        f"**Generated:** {generated_at}",
        "",
        "## Purpose",
        "",
        "This report provides SEC ticker-to-CIK resolution and submissions inventory for downstream SEC extraction checkpoints (CP24C-CP24H).",
        "",
        "This is a report-only foundation layer. No alerts were generated, no Telegram/email was sent, no scheduled tasks were modified, and OpenInsider data was not used.",
        "",
        "## Source Boundary",
        "",
        "Data sources:",
        "- SEC company_tickers.json (ticker-to-CIK mapping)",
        "- SEC submissions API (filing history)",
        "",
        "No third-party financial data, message boards, social media, or Roger's OpenInsider spreadsheet were used.",
        "",
        "## Resolver Result",
        "",
        f"**Status:** {resolver['status']}",
        "",
    ]

    if resolver["status"] == "resolved":
        md_lines.extend(
            [
                "**Resolution successful.**",
                "",
                f"- Ticker: `{ticker}`",
                f"- CIK: `{cik}`",
                f"- Company: {company_name}",
                "",
            ]
        )
    else:
        md_lines.extend(
            [
                "**Resolution failed.**",
                "",
                "Ticker could not be resolved to a CIK using SEC data.",
                "",
            ]
        )

    md_lines.extend(
        [
            "## SEC Submissions Status",
            "",
            f"**Status:** {submissions['status']}",
            "",
        ]
    )

    if submissions["status"] in ("retrieved", "degraded"):
        md_lines.extend(
            [
                f"**Recent filings count:** {submissions['recent_filings_count']}",
                "",
            ]
        )
    else:
        md_lines.extend(
            [
                "Submissions retrieval failed.",
                "",
            ]
        )

    # Filing counts by form
    md_lines.extend(
        [
            "## Filing Counts by Form",
            "",
        ]
    )

    if submissions["filing_counts_by_form"]:
        md_lines.append("| Form | Count |")
        md_lines.append("|------|-------|")
        for form, count in sorted(
            submissions["filing_counts_by_form"].items(), key=lambda x: -x[1]
        ):
            md_lines.append(f"| {form} | {count} |")
        md_lines.append("")
    else:
        md_lines.extend(
            [
                "No filings found within lookback window.",
                "",
            ]
        )

    # Latest relevant filings
    md_lines.extend(
        [
            "## Latest Relevant Filings",
            "",
        ]
    )

    latest = submissions["latest_filings"]
    for form_type, label in [
        ("latest_10k", "10-K"),
        ("latest_10q", "10-Q"),
        ("latest_8k", "8-K"),
        ("latest_form4", "Form 4"),
        ("latest_form144", "Form 144"),
        ("latest_13d_or_13g", "13D/13G"),
        ("latest_13f_hr", "13F-HR"),
    ]:
        filing = latest.get(form_type)
        if filing:
            md_lines.extend(
                [
                    f"### {label}",
                    "",
                    f"- **Filing Date:** {filing['filing_date']}",
                    f"- **Accession Number:** {filing['accession_number']}",
                    f"- **Primary Document:** {filing['primary_document']}",
                    "",
                ]
            )

    if not any(latest.values()):
        md_lines.extend(
            [
                "No relevant filings found.",
                "",
            ]
        )

    # Downstream readiness
    md_lines.extend(
        [
            "## Downstream Readiness",
            "",
            "| Checkpoint | Ready | Description |",
            "|------------|-------|-------------|",
            f"| CP24C | {'Yes' if downstream['form4_ready'] else 'No'} | Form 4 insider transaction extraction |",
            f"| CP24D | {'Yes' if downstream['form144_ready'] else 'No'} | Form 144 restricted stock sales |",
            f"| CP24E | {'Yes' if downstream['xbrl_financials_ready'] else 'No'} | XBRL financial extraction |",
            f"| CP24F | {'Yes' if downstream['ownership_13dg_ready'] else 'No'} | 13D/13G ownership stakes |",
            f"| CP24G | {'Yes' if downstream['capital_structure_ready'] else 'No'} | Capital structure from S-3/offerings |",
            "",
        ]
    )

    if downstream["notes"]:
        md_lines.extend(
            [
                "**Notes:**",
                "",
            ]
        )
        for note in downstream["notes"]:
            md_lines.append(f"- {note}")
        md_lines.append("")

    # Degraded mode
    md_lines.extend(
        [
            "## Degraded Mode",
            "",
            f"**Is Degraded:** {'Yes' if degraded['is_degraded'] else 'No'}",
            "",
        ]
    )

    if degraded["is_degraded"]:
        md_lines.extend(
            [
                "**Reasons:**",
                "",
            ]
        )
        for reason in degraded["reasons"]:
            md_lines.append(f"- {reason}")
        md_lines.append("")

    # Evidence provenance
    md_lines.extend(
        [
            "## Evidence Provenance",
            "",
        ]
    )

    for ev in evidence:
        md_lines.extend(
            [
                f"### {ev['source']}",
                "",
                f"- **URL:** {ev['url']}",
                f"- **Retrieved:** {ev['retrieved_at']}",
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


def generate_batch_summary_json(ticker_results: list[dict]) -> dict:
    """Generate batch summary JSON for multiple tickers."""
    tickers_requested = [r["ticker"] for r in ticker_results]
    tickers_resolved = [r["ticker"] for r in ticker_results if r["resolver"]["status"] == "resolved"]
    tickers_unresolved = [r["ticker"] for r in ticker_results if r["resolver"]["status"] != "resolved"]

    degraded_count = sum(1 for r in ticker_results if r["degraded_mode"]["is_degraded"])

    summary = {
        "generated_at": utcnow_iso(),
        "tickers_requested": tickers_requested,
        "tickers_resolved": tickers_resolved,
        "tickers_unresolved": tickers_unresolved,
        "results": ticker_results,
        "summary": {
            "resolved_count": len(tickers_resolved),
            "unresolved_count": len(tickers_unresolved),
            "degraded_count": degraded_count,
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

    return summary


def generate_batch_summary_markdown(batch_json: dict) -> str:
    """Generate batch summary Markdown report from JSON data."""
    generated_at = batch_json["generated_at"]
    tickers_requested = batch_json["tickers_requested"]
    tickers_resolved = batch_json["tickers_resolved"]
    tickers_unresolved = batch_json["tickers_unresolved"]
    summary = batch_json["summary"]
    safety = batch_json["safety"]
    results = batch_json["results"]

    md_lines = [
        "# SEC Ticker/CIK Batch Submissions Inventory Summary",
        "",
        f"**Generated:** {generated_at}",
        "",
        "## Requested Tickers",
        "",
    ]

    md_lines.append(", ".join(tickers_requested))
    md_lines.append("")

    md_lines.extend(
        [
            "## Resolved Tickers",
            "",
        ]
    )

    if tickers_resolved:
        md_lines.append(", ".join(tickers_resolved))
    else:
        md_lines.append("None")
    md_lines.append("")

    md_lines.extend(
        [
            "## Unresolved Tickers",
            "",
        ]
    )

    if tickers_unresolved:
        md_lines.append(", ".join(tickers_unresolved))
    else:
        md_lines.append("None")
    md_lines.append("")

    # Per-ticker status table
    md_lines.extend(
        [
            "## Per-Ticker Status",
            "",
            "| Ticker | Resolver | Submissions | Degraded |",
            "|--------|----------|-------------|----------|",
        ]
    )

    for result in results:
        ticker = result["ticker"]
        resolver_status = result["resolver"]["status"]
        submissions_status = result["submissions"]["status"]
        is_degraded = "Yes" if result["degraded_mode"]["is_degraded"] else "No"
        md_lines.append(f"| {ticker} | {resolver_status} | {submissions_status} | {is_degraded} |")

    md_lines.append("")

    # Degraded mode table
    md_lines.extend(
        [
            "## Degraded Mode Details",
            "",
            "| Ticker | Degraded | Reasons |",
            "|--------|----------|---------|",
        ]
    )

    for result in results:
        ticker = result["ticker"]
        degraded = result["degraded_mode"]
        is_degraded = "Yes" if degraded["is_degraded"] else "No"
        reasons = "; ".join(degraded["reasons"]) if degraded["reasons"] else "-"
        md_lines.append(f"| {ticker} | {is_degraded} | {reasons} |")

    md_lines.append("")

    # Summary stats
    md_lines.extend(
        [
            "## Summary Statistics",
            "",
            f"- **Resolved:** {summary['resolved_count']}",
            f"- **Unresolved:** {summary['unresolved_count']}",
            f"- **Degraded:** {summary['degraded_count']}",
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


def process_ticker(ticker: str, max_recent_filings: int) -> dict:
    """Process a single ticker: resolve and build inventory."""
    print(f"Processing ticker: {ticker}")

    # Resolve ticker to CIK
    resolver_result = resolve_ticker_to_cik(ticker)

    # Build submissions inventory if resolved
    submissions_result = {"status": "failed", "data": None, "error": "Ticker not resolved"}

    if resolver_result.ok:
        print(f"  Resolved: {ticker} -> CIK {resolver_result.cik_padded} ({resolver_result.company_name})")
        submissions_result = build_submissions_inventory(
            resolver_result.cik_padded, max_recent=max_recent_filings
        )
        print(f"  Submissions: {submissions_result['status']}")
    else:
        print(f"  Resolution failed: {resolver_result.error_message}")

    # Generate JSON output
    ticker_json = generate_per_ticker_json(
        ticker, resolver_result, submissions_result, max_recent_filings
    )

    return ticker_json


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SEC Ticker/CIK Resolver and Submissions Inventory"
    )
    parser.add_argument("--ticker", help="Single ticker symbol")
    parser.add_argument("--tickers", help="Comma-separated ticker symbols")
    parser.add_argument("--output-dir", required=True, help="Output directory for reports")
    parser.add_argument(
        "--max-recent-filings",
        type=int,
        default=100,
        help="Maximum number of recent filings to include (default: 100)",
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

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process tickers
    ticker_results = []
    for ticker in tickers:
        ticker_json = process_ticker(ticker, args.max_recent_filings)
        ticker_results.append(ticker_json)

        # Write per-ticker outputs
        ticker_upper = ticker.upper()
        json_path = output_dir / f"{ticker_upper}_sec_inventory.json"
        md_path = output_dir / f"{ticker_upper}_sec_inventory.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ticker_json, f, indent=2)
        print(f"  Wrote: {json_path}")

        md_content = generate_per_ticker_markdown(ticker_json)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"  Wrote: {md_path}")

    # Generate batch summary if multiple tickers
    if len(tickers) > 1:
        batch_json = generate_batch_summary_json(ticker_results)
        batch_md = generate_batch_summary_markdown(batch_json)

        batch_json_path = output_dir / "batch_sec_inventory_summary.json"
        batch_md_path = output_dir / "batch_sec_inventory_summary.md"

        with open(batch_json_path, "w", encoding="utf-8") as f:
            json.dump(batch_json, f, indent=2)
        print(f"  Wrote: {batch_json_path}")

        with open(batch_md_path, "w", encoding="utf-8") as f:
            f.write(batch_md)
        print(f"  Wrote: {batch_md_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
