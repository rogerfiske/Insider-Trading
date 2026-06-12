"""CLI script for SEC XBRL financial extraction.

Extracts financial metrics from SEC companyfacts for specified tickers.

Usage:
    python scripts/sec_xbrl_financials.py --ticker MAIA --output-dir docs/sample_reports/xbrl_financials/MAIA
    python scripts/sec_xbrl_financials.py --tickers MAIA,NVDA --output-dir docs/sample_reports/xbrl_financials/batch

Safety constraints:
    - No alerts
    - No Telegram/email
    - No scheduled tasks modified
    - No secrets in outputs
    - No buy/sell/hold language
"""

import argparse
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from sources.sec_ticker import resolve_ticker_to_cik
from sources.sec_companyfacts import fetch_companyfacts, parse_companyfacts
from sources.sec_xbrl_financials import (
    extract_financial_metrics,
    select_latest_quarter,
    select_latest_annual,
    calculate_derived_metrics,
    reconcile_with_targets,
)


# MAIA CP23B-Fix3A official reconciliation targets
MAIA_RECONCILIATION_TARGETS = {
    "cash_and_cash_equivalents": 34413110,
    "current_assets": 36103913,
    "current_liabilities": 6322437,
    "total_liabilities": 15872969,
    "common_shares_outstanding": 60671491,
    "accumulated_deficit": -116000657,
    "research_and_development_expense": 3525097,
    "general_and_administrative_expense": 3424832,
    "operating_expenses": 6949929,
    "operating_loss": -6949929,
    "net_loss": -6369652,
    "weighted_average_shares_basic": 57748419,
    "net_cash_used_in_operating_activities": -5311328,
}


def extract_ticker_xbrl_financials(ticker: str, output_dir: Path) -> dict:
    """Extract XBRL financials for a single ticker.

    Args:
        ticker: Stock ticker symbol
        output_dir: Output directory for reports

    Returns:
        dict with extraction results and status
    """
    print(f"\n=== Extracting XBRL financials for {ticker} ===")

    # Resolve ticker to CIK
    cik_result = resolve_ticker_to_cik(ticker)
    if not cik_result.ok:
        print(f"ERROR: Failed to resolve ticker {ticker}: {cik_result.error_type}")
        return {
            "ticker": ticker,
            "status": "failed",
            "error": cik_result.error_type,
        }

    cik = cik_result.cik_padded
    company_name = cik_result.company_name

    print(f"Resolved {ticker} to CIK {cik} ({company_name})")

    # Fetch companyfacts
    cf_result = fetch_companyfacts(cik)
    if not cf_result["ok"]:
        print(f"ERROR: Failed to fetch companyfacts: {cf_result['error']}")
        return {
            "ticker": ticker,
            "cik": cik,
            "company_name": company_name,
            "status": "companyfacts_failed",
            "error": cf_result["error"],
        }

    print(f"Fetched companyfacts (from_cache={cf_result.get('from_cache', False)})")

    # Parse companyfacts
    parsed = parse_companyfacts(cf_result["body"])
    if not parsed["ok"]:
        print(f"ERROR: Failed to parse companyfacts: {parsed['error']}")
        return {
            "ticker": ticker,
            "cik": cik,
            "company_name": company_name,
            "status": "parse_failed",
            "error": parsed["error"],
        }

    us_gaap_facts = parsed["facts"].get("us-gaap", {})
    if not us_gaap_facts:
        print(f"ERROR: No US-GAAP facts found")
        return {
            "ticker": ticker,
            "cik": cik,
            "company_name": company_name,
            "status": "no_us_gaap_facts",
        }

    # Select latest periods
    latest_q = select_latest_quarter(us_gaap_facts)
    latest_annual = select_latest_annual(us_gaap_facts)

    if not latest_q and not latest_annual:
        print(f"ERROR: No quarterly or annual periods found")
        return {
            "ticker": ticker,
            "cik": cik,
            "company_name": company_name,
            "status": "no_periods_found",
        }

    # Extract metrics for latest quarter
    quarterly_metrics = {}
    if latest_q:
        print(f"Latest quarter: {latest_q['period_end']} (FY{latest_q['fiscal_year']} {latest_q['fiscal_period']})")
        quarterly_metrics = extract_financial_metrics(us_gaap_facts, period_end=latest_q["period_end"])

    # Extract metrics for latest annual
    annual_metrics = {}
    if latest_annual:
        print(f"Latest annual: {latest_annual['period_end']} (FY{latest_annual['fiscal_year']} {latest_annual['fiscal_period']})")
        annual_metrics = extract_financial_metrics(us_gaap_facts, period_end=latest_annual["period_end"])

    # Calculate derived metrics (use quarterly if available, else annual)
    primary_metrics = quarterly_metrics if quarterly_metrics else annual_metrics
    derived = calculate_derived_metrics(primary_metrics)

    # Reconciliation (MAIA only)
    reconciliation = None
    if ticker.upper() == "MAIA" and quarterly_metrics:
        print("Reconciling against CP23B-Fix3A official targets...")
        reconciliation = reconcile_with_targets(quarterly_metrics, MAIA_RECONCILIATION_TARGETS)
        print(f"Reconciliation status: {reconciliation['status']}")
        print(f"Matched: {reconciliation['matched_count']}/{reconciliation['total_targets']}")

        if reconciliation['differences']:
            print(f"Differences found: {len(reconciliation['differences'])}")
            for diff in reconciliation['differences'][:5]:  # Show first 5
                if diff.get('status') == 'not_available':
                    print(f"  - {diff['metric']}: not available (expected {diff['expected']})")
                else:
                    print(f"  - {diff['metric']}: {diff['actual']} vs {diff['expected']} (diff: {diff['difference']})")

    # Build result
    result = {
        "ticker": ticker,
        "cik": cik,
        "company_name": company_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "companyfacts_status": "retrieved",
        "latest_quarter": latest_q,
        "latest_annual": latest_annual,
        "quarterly_metrics": quarterly_metrics,
        "annual_metrics": annual_metrics,
        "derived_metrics": derived,
        "reconciliation": reconciliation if reconciliation else {"has_reconciliation_target": False},
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
        "status": "ok",
    }

    # Write outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON output
    json_path = output_dir / f"{ticker}_xbrl_financials.json"
    with open(json_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"Wrote {json_path}")

    # Markdown report
    md_path = output_dir / f"{ticker}_xbrl_financials.md"
    write_markdown_report(result, md_path)
    print(f"Wrote {md_path}")

    # CSV output
    csv_path = output_dir / f"{ticker}_xbrl_financials.csv"
    write_csv_report(result, csv_path)
    print(f"Wrote {csv_path}")

    print(f"[OK] {ticker} extraction complete")

    return result


def write_markdown_report(result: dict, output_path: Path):
    """Write Markdown report for ticker financials."""
    ticker = result["ticker"]
    company_name = result["company_name"]
    cik = result["cik"]

    lines = []
    lines.append(f"# {ticker} XBRL Financial Extraction Report")
    lines.append("")
    lines.append(f"**Company:** {company_name}")
    lines.append(f"**CIK:** {cik}")
    lines.append(f"**Generated:** {result['generated_at']}")
    lines.append("")

    lines.append("## Purpose")
    lines.append("")
    lines.append("This report extracts standardized financial metrics from SEC companyfacts data.")
    lines.append("Source: SEC EDGAR companyfacts API (https://data.sec.gov/api/xbrl/companyfacts/)")
    lines.append("")

    lines.append("## Latest Quarter Financial Snapshot")
    lines.append("")
    if result.get("latest_quarter"):
        q = result["latest_quarter"]
        lines.append(f"**Period:** {q['period_end']} (FY{q['fiscal_year']} {q['fiscal_period']})")
        lines.append(f"**Form:** {q['form']}")
        lines.append(f"**Filed:** {q['filed']}")
        lines.append("")

        metrics = result.get("quarterly_metrics", {})
        if metrics:
            lines.append("| Metric | Value | Unit |")
            lines.append("|--------|-------|------|")
            for name, data in sorted(metrics.items()):
                if data.get("status") == "ok" and data.get("value") is not None:
                    val = data["value"]
                    unit = data.get("unit", "")
                    lines.append(f"| {name.replace('_', ' ').title()} | {val:,.0f} | {unit} |")
        lines.append("")
    else:
        lines.append("No quarterly data available.")
        lines.append("")

    lines.append("## Derived Metrics")
    lines.append("")
    derived = result.get("derived_metrics", {})
    if derived:
        lines.append("| Metric | Value | Unit | Status |")
        lines.append("|--------|-------|------|--------|")
        for name, data in sorted(derived.items()):
            val = data.get("value", "N/A")
            unit = data.get("unit", "")
            status = data.get("status", "ok")
            if val != "N/A" and isinstance(val, (int, float)):
                val_str = f"{val:,.2f}"
            else:
                val_str = str(val)
            lines.append(f"| {name.replace('_', ' ').title()} | {val_str} | {unit} | {status} |")
        lines.append("")
    else:
        lines.append("No derived metrics calculated.")
        lines.append("")

    # MAIA reconciliation section
    if result.get("reconciliation", {}).get("has_reconciliation_target") is not False:
        lines.append("## MAIA Reconciliation (CP23B-Fix3A)")
        lines.append("")
        recon = result["reconciliation"]
        lines.append(f"**Status:** {recon['status']}")
        lines.append(f"**Matched:** {recon['matched_count']} / {recon['total_targets']}")
        lines.append("")

        if recon.get("differences"):
            lines.append("### Differences")
            lines.append("")
            lines.append("| Metric | Expected | Actual | Difference |")
            lines.append("|--------|----------|--------|------------|")
            for diff in recon["differences"]:
                metric = diff["metric"].replace("_", " ").title()
                expected = diff.get("expected", "N/A")
                actual = diff.get("actual", "N/A")
                if diff.get("status") == "not_available":
                    lines.append(f"| {metric} | {expected} | Not Available | - |")
                else:
                    delta = diff.get("difference", 0)
                    lines.append(f"| {metric} | {expected:,.0f} | {actual:,.0f} | {delta:,.0f} |")
            lines.append("")

    lines.append("## Safety Confirmations")
    lines.append("")
    safety = result.get("safety", {})
    lines.append(f"- Report only: {safety.get('report_only', True)}")
    lines.append(f"- Alerts generated: {safety.get('alerts_generated', False)}")
    lines.append(f"- OpenInsider spreadsheet used: {safety.get('openinsider_spreadsheet_used', False)}")
    lines.append(f"- Telegram sent: {safety.get('telegram_sent', False)}")
    lines.append(f"- Email sent: {safety.get('email_sent', False)}")
    lines.append(f"- Scheduled tasks modified: {safety.get('scheduled_tasks_modified', False)}")
    lines.append("")

    lines.append("## No-Recommendation Statement")
    lines.append("")
    lines.append("This report is for informational purposes only. It does not constitute investment advice.")
    lines.append("No buy, sell, or hold recommendations are provided.")
    lines.append("")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def write_csv_report(result: dict, output_path: Path):
    """Write CSV report with all metrics."""
    ticker = result["ticker"]
    cik = result["cik"]

    rows = []

    # Add quarterly metrics
    metrics = result.get("quarterly_metrics", {})
    for metric_name, metric_data in metrics.items():
        if metric_data.get("status") == "ok":
            rows.append({
                "ticker": ticker,
                "cik": cik,
                "metric": metric_name,
                "value": metric_data.get("value"),
                "unit": metric_data.get("unit"),
                "period_start": metric_data.get("period_start", ""),
                "period_end": metric_data.get("period_end"),
                "fiscal_year": metric_data.get("fiscal_year"),
                "fiscal_period": metric_data.get("fiscal_period"),
                "form": metric_data.get("form"),
                "filed": metric_data.get("filed"),
                "concept": metric_data.get("concept"),
                "source": metric_data.get("source"),
                "status": metric_data.get("status"),
            })

    with open(output_path, 'w', newline='') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)


def write_batch_summary(results: list[dict], output_dir: Path):
    """Write batch summary JSON and Markdown."""
    print("\n=== Writing batch summary ===")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tickers_requested": [r["ticker"] for r in results],
        "tickers_succeeded": [r["ticker"] for r in results if r.get("status") == "ok"],
        "tickers_failed": [r["ticker"] for r in results if r.get("status") != "ok"],
        "results": results,
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

    # JSON
    json_path = output_dir / "batch_xbrl_financials_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote {json_path}")

    # Markdown
    md_path = output_dir / "batch_xbrl_financials_summary.md"
    lines = []
    lines.append("# Batch XBRL Financial Extraction Summary")
    lines.append("")
    lines.append(f"**Generated:** {summary['generated_at']}")
    lines.append(f"**Tickers Requested:** {', '.join(summary['tickers_requested'])}")
    lines.append(f"**Succeeded:** {len(summary['tickers_succeeded'])}")
    lines.append(f"**Failed:** {len(summary['tickers_failed'])}")
    lines.append("")

    lines.append("## Per-Ticker Status")
    lines.append("")
    lines.append("| Ticker | CIK | Company | Status |")
    lines.append("|--------|-----|---------|--------|")
    for r in results:
        ticker = r.get("ticker", "")
        cik = r.get("cik", "N/A")
        company = r.get("company_name", "N/A")
        status = r.get("status", "unknown")
        lines.append(f"| {ticker} | {cik} | {company} | {status} |")
    lines.append("")

    lines.append("## Safety Confirmations")
    lines.append("")
    safety = summary["safety"]
    for key, val in safety.items():
        lines.append(f"- {key}: {val}")
    lines.append("")

    with open(md_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"Wrote {md_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract XBRL financials from SEC companyfacts"
    )
    parser.add_argument("--ticker", help="Single ticker to extract")
    parser.add_argument("--tickers", help="Comma-separated tickers for batch mode")
    parser.add_argument("--output-dir", required=True, help="Output directory")

    args = parser.parse_args()

    if not args.ticker and not args.tickers:
        parser.error("Must specify --ticker or --tickers")

    output_dir = Path(args.output_dir)

    if args.ticker:
        # Single ticker mode
        result = extract_ticker_xbrl_financials(args.ticker.upper(), output_dir)
        if result.get("status") == "ok":
            print("\n[OK] Extraction successful")
        else:
            print(f"\n[FAIL] Extraction failed: {result.get('error', 'unknown')}")
            return 1

    elif args.tickers:
        # Batch mode
        tickers = [t.strip().upper() for t in args.tickers.split(",")]
        results = []

        for ticker in tickers:
            ticker_dir = output_dir / ticker
            result = extract_ticker_xbrl_financials(ticker, ticker_dir)
            results.append(result)

        # Write batch summary
        write_batch_summary(results, output_dir)

        succeeded = sum(1 for r in results if r.get("status") == "ok")
        print(f"\n[OK] Batch extraction complete: {succeeded}/{len(tickers)} succeeded")

    return 0


if __name__ == "__main__":
    exit(main())
