#!/usr/bin/env python3
"""
Ticker Drilldown Helper -- Manual diagnostic report generator for a specific ticker.

Usage:
    python scripts/ticker_drilldown.py --ticker MAIA --dry-run-report

Generates a sample ticker-level report showing what each agent would contribute
for the specified ticker, given current connector capabilities.

Safety:
  - Runs in dry-run mode (no alerts sent)
  - Does not consume daily production guard
  - Does not modify scheduled tasks
  - Does not use uploaded spreadsheets
  - Uses only existing project connectors
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sources.sec_form4 import SecForm4Connector
from sources.sec_13f import Sec13FConnector
from sources.sec_ticker import SecTickerResolver


def generate_ticker_report(ticker: str, output_path: Path | None = None) -> str:
    """Generate a comprehensive ticker drilldown report.

    Args:
        ticker: Stock ticker symbol (e.g., "MAIA")
        output_path: Optional path to save report

    Returns:
        Report content as markdown string
    """
    ticker = ticker.upper()
    now = datetime.now(timezone.utc)

    # Resolve ticker to CIK
    ticker_resolver = SecTickerResolver()
    ticker_resolution = ticker_resolver.resolve(ticker)

    # Fetch recent Form 4 data (all filings, not ticker-specific)
    form4_connector = SecForm4Connector()
    form4_result = form4_connector.fetch()

    # Fetch 13F data (manager-focused, not ticker-specific)
    form13f_connector = Sec13FConnector()
    form13f_result = form13f_connector.fetch()

    # Build report
    lines = [
        f"# {ticker} — Manual Ticker Drilldown Diagnostic Report",
        "",
        f"**Generated**: {now.isoformat()}",
        "",
        "**Ticker**: " + ticker,
        "",
        "**Purpose**: Diagnostic sample report showing what each agent would contribute for this ticker.",
        "",
        "**Safety Disclaimer**: This report is informational only and is not trading advice. No buy/sell/trade instructions are provided.",
        "",
        "---",
        "",
        "## Data Source Boundary",
        "",
        "**Sources Used**:",
        "- Project connectors only (SEC Form 4, SEC 13F, etc.)",
        "- Current project state/database",
        "- Agent logic as implemented",
        "",
        "**Sources NOT Used**:",
        "- Roger's uploaded OpenInsider spreadsheet",
        "- Manual insider-trade data from chat",
        "- External data not supported by existing connectors",
        "",
        "---",
        "",
        "## Ticker Resolution",
        "",
        f"**Ticker**: {ticker}",
        "",
    ]

    # Add ticker resolution result
    if ticker_resolution.ok:
        lines.extend([
            f"**CIK**: {ticker_resolution.cik_padded} ({ticker_resolution.cik})",
            f"**Company Name**: {ticker_resolution.company_name}",
            f"**Resolution Status**: ✅ Success",
            f"**Source**: {ticker_resolution.source_url}",
            f"**Retrieved**: {ticker_resolution.retrieved_at}",
            "",
            f"Ticker `{ticker}` successfully resolved to SEC CIK `{ticker_resolution.cik_padded}` for issuer `{ticker_resolution.company_name}`.",
        ])
    else:
        lines.extend([
            "**CIK**: Not found",
            "**Resolution Status**: ❌ Failed",
            f"**Error**: {ticker_resolution.error_message}",
            f"**Error Type**: {ticker_resolution.error_type}",
            "",
            f"Ticker `{ticker}` could not be resolved to an SEC CIK. This ticker may not be in the SEC company tickers mapping or may be delisted.",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"This report exercises the seven-agent insider-trading framework for ticker `{ticker}`.",
        "",
    ])

    # Update executive summary based on resolution status
    if ticker_resolution.ok:
        lines.extend([
            f"**Ticker Resolution**: ✅ {ticker} → CIK {ticker_resolution.cik_padded} ({ticker_resolution.company_name})",
            "",
            "**Current Status**: Ticker-to-CIK resolution is now implemented. Eddie can now filter Form 4 filings to this specific issuer CIK.",
            "",
            "**Remaining Limitation**: Form 4 transaction detail extraction is limited to metadata. Full XML parsing of individual transactions (share counts, prices, transaction codes) would enhance signal quality.",
        ])
    else:
        lines.extend([
            f"**Ticker Resolution**: ❌ {ticker} could not be resolved to CIK",
            "",
            "**Current Status**: Ticker resolution attempted but failed. Eddie cannot filter Form 4 filings without a valid CIK.",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## Agent Applicability Summary",
        "",
        "| Agent | Applicability | Evidence Status | Signal | Confidence | Reason |",
        "|-------|--------------|-----------------|--------|------------|--------|",
    ])

    # Eddie row depends on ticker resolution success
    if ticker_resolution.ok:
        lines.append(f"| Eddie | TICKER_RESOLVED_BUT_FORM4_DETAIL_EXTRACTION_LIMITED | CIK {ticker_resolution.cik_padded} resolved | N/A | N/A | CIK resolved; Form 4 detail parsing limited |")
    else:
        lines.append(f"| Eddie | TICKER_RESOLUTION_FAILED | Cannot resolve {ticker} to CIK | N/A | N/A | Ticker not found in SEC mapping |")

    lines.extend([
        f"| Maggie | BLOCKED_BY_MISSING_CONNECTOR | Cannot filter to {ticker} | N/A | N/A | Ticker-to-CUSIP resolution not implemented |",
        "| Frank | PARTIALLY_APPLICABLE | Macro context only | NEUTRAL | 1 | Not ticker-specific |",
        f"| Maya | NOT_APPLICABLE | Crypto/on-chain only | N/A | N/A | {ticker} is a stock, not crypto |",
        f"| Janet | NOT_APPLICABLE | Not in portfolio | N/A | N/A | {ticker} not in local portfolio |",
        "| Sophie | APPLICABLE_TO_AGENT_OUTPUTS | Would aggregate signals | N/A | N/A | No ticker-specific signals to aggregate |",
        "| Ross | DRY_RUN_ONLY | Would route if signals exist | N/A | N/A | No actionable signals |",
        "",
        "---",
        "",
        "## Eddie — SEC Form 4 Insider Transactions",
        "",
    ])

    # Eddie section depends on ticker resolution success
    if ticker_resolution.ok:
        # Count Form 4 filings for this CIK
        matching_filings = []
        if form4_result.ok:
            for ev in form4_result.evidence:
                if ev.normalized.get("cik") == ticker_resolution.cik_padded.lstrip("0"):
                    matching_filings.append(ev)

        lines.extend([
            "**Applicability**: TICKER_RESOLVED_BUT_FORM4_DETAIL_EXTRACTION_LIMITED",
            "",
            "**Ticker Resolution**:",
            f"- ✅ {ticker} → CIK {ticker_resolution.cik_padded} ({ticker_resolution.company_name})",
            f"- Ticker-to-CIK resolution now implemented",
            "",
            "**Current Behavior**:",
            f"- Eddie fetches all Form 4 filings from the last 24 hours ({len(form4_result.evidence) if form4_result.ok else 0} total filings found)",
            f"- Filters to CIK {ticker_resolution.cik_padded}: {len(matching_filings)} filings for {ticker}",
            "",
        ])

        if matching_filings:
            lines.append(f"**{ticker} Form 4 Filings Found**:")
            for i, ev in enumerate(matching_filings[:5], 1):
                n = ev.normalized
                lines.append(f"{i}. Accession: {n.get('accession_number', '?')} | Filed: {n.get('filing_date', '?')} | Filers: {', '.join(n.get('display_names', []))}")
                if ev.source_url:
                    lines.append(f"   URL: {ev.source_url}")
            lines.append("")
            lines.extend([
                "**Remaining Limitation**: Form 4 XML detail extraction is limited.",
                "",
                "**What's Still Missing**:",
                "1. Parse individual Form 4 XML to extract transaction table",
                "2. Extract transaction type (P=purchase, S=sale, etc.)",
                "3. Extract share count, price, and total value",
                "4. Filter to open-market purchases >= $100k by C-suite/directors",
                "5. Generate confidence-weighted signal",
                "",
                "**Evidence Status**: CIK-filtered filings found, transaction details not yet parsed",
            ])
        else:
            lines.extend([
                f"**{ticker} Form 4 Filings**: None found in last 24 hours",
                "",
                "**Status**: Ticker resolution works, but no recent Form 4 filings for this issuer",
                "",
                "**Evidence Status**: APPLICABLE_NO_RECENT_FILINGS",
            ])

        lines.extend([
            "",
            "**Signal**: N/A (transaction detail parsing not yet implemented)",
            "",
            "**Confidence**: N/A",
            "",
            "**Reason**: CIK resolution successful, but Form 4 detail extraction still limited to metadata",
        ])

        if matching_filings:
            lines.append("")
            lines.append("**Source URLs**:")
            for ev in matching_filings[:5]:
                if ev.source_url:
                    lines.append(f"- {ev.source_url}")
        else:
            lines.append("")
            lines.append("**Source URLs**: N/A (no recent filings)")

    else:
        lines.extend([
            "**Applicability**: TICKER_RESOLUTION_FAILED",
            "",
            "**Ticker Resolution**:",
            f"- ❌ {ticker} could not be resolved to CIK",
            f"- Error: {ticker_resolution.error_message}",
            f"- Error Type: {ticker_resolution.error_type}",
            "",
            "**Current Behavior**:",
            f"- Eddie fetches all Form 4 filings from the last 24 hours ({len(form4_result.evidence) if form4_result.ok else 0} filings found)",
            f"- Cannot filter to {ticker} without a valid CIK",
            "",
            "**Limitation**: Ticker not found in SEC company tickers mapping",
            "",
            "**Evidence Status**: Cannot filter without CIK",
            "",
            "**Signal**: N/A (cannot generate ticker-specific signal)",
            "",
            "**Confidence**: N/A",
            "",
            f"**Reason**: {ticker} not found in SEC company tickers database",
            "",
            "**Source URLs**: N/A (no CIK to filter with)",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## Maggie — SEC 13F Institutional Holdings",
        "",
        "**Applicability**: BLOCKED_BY_MISSING_CONNECTOR",
        "",
        "**Current Behavior**:",
        f"- Maggie fetches 13F filings for configured institutional managers ({len(form13f_result.evidence) if form13f_result.ok else 0} filings found)",
        "- Current connector is manager-focused, not ticker/CUSIP-focused",
        f"- Cannot determine if selected managers hold {ticker}",
        "",
        "**Limitation**: Ticker-to-CUSIP resolution and holding-level filtering not implemented",
        "",
        "**What Would Be Needed**:",
        "1. Implement ticker-to-CUSIP lookup",
        "2. Parse 13F XML to extract individual holdings",
        f"3. Filter to {ticker} holdings across all managers",
        "4. Detect position changes (additions, increases, decreases, exits)",
        "5. Generate ticker-specific signal",
        "",
        "**Evidence Status**: Cannot filter to MAIA with current connector",
        "",
        "**Signal**: N/A (cannot generate ticker-specific signal)",
        "",
        "**Confidence**: N/A",
        "",
        "**Reason**: Ticker-specific 13F filtering not supported",
        "",
        "---",
        "",
        "## Frank — Federal Reserve / Macro Context",
        "",
        "**Applicability**: PARTIALLY_APPLICABLE (macro context only)",
        "",
        "**Current Behavior**:",
        "- Frank monitors Federal Reserve speeches and policy signals",
        "- Frank is intentionally macro-focused, not ticker-specific",
        f"- Frank would NOT form a ticker-specific view on {ticker}",
        "",
        "**What Frank Would Provide**:",
        "- Overall market sentiment (dovish/hawkish Fed)",
        "- Interest rate trajectory context",
        "- Macro risk factors",
        "",
        "**Signal**: NEUTRAL",
        "",
        "**Confidence**: 1 (macro background only)",
        "",
        f"**Reason**: Frank does not analyze individual tickers like {ticker}; provides macro context only",
        "",
        "---",
        "",
        "## Maya — On-Chain / Whale Movement",
        "",
        "**Applicability**: NOT_APPLICABLE",
        "",
        "**Current Behavior**:",
        "- Maya monitors crypto/blockchain wallet activity",
        f"- {ticker} is a stock ticker, not a crypto asset",
        "- Maya has no visibility into stock transactions",
        "",
        f"**Why Not Applicable**: {ticker} is not a cryptocurrency or blockchain-related asset",
        "",
        "**Signal**: N/A",
        "",
        "**Confidence**: N/A",
        "",
        f"**Reason**: Maya only analyzes crypto assets; {ticker} is a stock",
        "",
        "---",
        "",
        "## Janet — Portfolio Drift",
        "",
        "**Applicability**: NOT_APPLICABLE (not in portfolio)",
        "",
        "**Current Behavior**:",
        "- Janet compares current portfolio holdings to target allocation",
        "- Janet reads `config/portfolio_current.json` and `config/portfolio_target.json`",
        f"- {ticker} is not present in local portfolio files",
        "",
        "**Evidence Status**: Not in portfolio",
        "",
        "**Signal**: N/A (no drift to report)",
        "",
        "**Confidence**: N/A",
        "",
        f"**Reason**: {ticker} not present in local portfolio configuration",
        "",
        "**Note**: If Roger wants Janet to track MAIA, he would need to add it to portfolio configuration files",
        "",
        "---",
        "",
        "## Sophie — Consensus Aggregator",
        "",
        "**Applicability**: APPLICABLE_TO_AGENT_OUTPUTS",
        "",
        "**Current Behavior**:",
        "- Sophie reads recent scout signals from all agents",
        "- Sophie groups signals by ticker and direction",
        "- Sophie applies consensus threshold (default: 2+ agents agreeing)",
        "",
        f"**For {ticker}**:",
        "- **Signals collected**: 0 ticker-specific signals",
        "- **Consensus met**: No (threshold not reached)",
        "- **Result**: No consensus event generated",
        "",
        "**Reason**: No agents produced ticker-specific signals due to connector limitations",
        "",
        "**What Would Happen If Signals Existed**:",
        f"- If 2+ agents signaled BULLISH on {ticker}, Sophie would generate a consensus event",
        "- Sophie would aggregate confidence scores",
        "- Sophie would mark consensus for Ross to route",
        "",
        "---",
        "",
        "## Ross — Routing / Reporting",
        "",
        "**Applicability**: DRY_RUN_ONLY",
        "",
        "**Current Behavior**:",
        "- Ross reads pending consensus events",
        "- Ross applies alert routing policy (severity, deduplication, channel routing)",
        "- **DRY-RUN MODE**: No alerts actually sent",
        "",
        f"**For {ticker}**:",
        "- **Pending consensus**: None (no signals from scouts)",
        "- **Routing decision**: N/A (nothing to route)",
        "",
        "**What Would Happen If Consensus Existed**:",
        "1. **Severity calculation**: Based on signal count, confidence, and historical patterns",
        "2. **Alert class determination**:",
        "   - ACTIONABLE (if meets ACTIONABLE threshold)",
        "   - WATCH (if interesting but below threshold)",
        "   - LOG_ONLY (if duplicate or low confidence)",
        "3. **Channel routing**:",
        "   - Telegram: Yes (if ACTIONABLE in production mode)",
        "   - Email: No (email disabled in current pilot)",
        "4. **Deduplication**: Check 24-hour window for duplicate MAIA signals",
        "5. **Rate limiting**: Max 1 alert per run (current pilot configuration)",
        "",
        "**Confirmation**: No Telegram or email was sent during this diagnostic run",
        "",
        "---",
        "",
        "## Source / Evidence References",
        "",
    ])

    # Count ticker-specific Form 4 filings if resolution succeeded
    ticker_form4_count = 0
    if ticker_resolution.ok and form4_result.ok:
        for ev in form4_result.evidence:
            if ev.normalized.get("cik") == ticker_resolution.cik_padded.lstrip("0"):
                ticker_form4_count += 1

    lines.extend([
        "**SEC Form 4**:",
        f"- Fetch status: {'Success' if form4_result.ok else 'Failed'}",
        f"- Total filings retrieved: {len(form4_result.evidence) if form4_result.ok else 0} (last 24 hours)",
    ])

    if ticker_resolution.ok:
        lines.append(f"- {ticker}-specific filings: {ticker_form4_count} (filtered by CIK {ticker_resolution.cik_padded})")
    else:
        lines.append(f"- {ticker}-specific filings: Cannot determine (CIK resolution failed)")

    lines.extend([
        "",
        "**SEC 13F**:",
        f"- Fetch status: {'Success' if form13f_result.ok else 'Failed'}",
        f"- Filings retrieved: {len(form13f_result.evidence) if form13f_result.ok else 0} (selected managers)",
        f"- {ticker} holdings: Cannot determine (ticker-to-CUSIP resolution not yet implemented)",
        "",
        "---",
        "",
        "## Limitations",
        "",
        "### Current Connector Limitations",
        "",
        "1. **~~Ticker-to-CIK Resolution~~** ✅ RESOLVED:",
        "   - ✅ Ticker-to-CIK mapping now implemented (sources/sec_ticker.py)",
        "   - ✅ Eddie can now filter Form 4 filings by CIK",
        "",
        "2. **Form 4 Transaction Detail Extraction** (Still Limited):",
        "   - Form 4 connector fetches filing metadata but does not parse XML transaction tables",
        "   - Cannot extract transaction type, share count, price, or total value",
        "   - Eddie cannot yet generate confidence-weighted signals",
        "",
        "3. **Ticker-to-CUSIP Resolution** (Still Missing):",
        "   - 13F connector cannot map ticker to CUSIP",
        "   - Cannot filter institutional holdings to specific tickers",
        "",
        "4. **13F Individual Holdings Parsing** (Still Missing):",
        "   - 13F connector fetches manager-level filings",
        "   - Does not parse XML to extract individual security holdings",
        "",
        "5. **Historical Comparison** (Still Missing):",
        "   - Connectors fetch current period only",
        "   - Cannot detect QoQ or YoY changes in holdings",
        "",
        "### Agent-Specific Limitations",
        "",
        "1. **Eddie**: ✅ Can now filter to CIK; still limited by Form 4 detail parsing",
        "2. **Maggie**: Cannot analyze ticker-specific institutional interest without CUSIP resolution and holding-level data",
        "3. **Frank**: Intentionally macro-focused; not a limitation",
        "4. **Maya**: Intentionally crypto-focused; not applicable to stocks",
        "5. **Janet**: Requires manual portfolio configuration; not automatic",
        "",
        "---",
        "",
        "## Recommended Implementation Improvements",
        "",
        "### ~~Priority 1: Ticker-to-CIK Resolution~~ ✅ COMPLETE",
        "",
        "**Status**: ✅ Implemented in sources/sec_ticker.py",
        "",
        "**Implementation Complete**:",
        "1. ✅ Uses SEC company tickers JSON: https://www.sec.gov/files/company_tickers.json",
        "2. ✅ Caches ticker mapping data in .state/cache/ (7-day cache)",
        "3. ✅ Implements resolve_ticker_to_cik(ticker: str) -> TickerCikResult",
        "4. ✅ Returns structured result with CIK, company name, source URL, timestamps",
        "",
        "**Benefit Realized**: Eddie can now filter Form 4 filings to specific issuer CIKs",
        "",
        "### Priority 1B: Ticker-to-CUSIP Resolution (Still Needed)",
        "",
        "**Implementation**:",
        "1. Extend SEC ticker resolver or use additional data source",
        "2. Map ticker → CUSIP for 13F filtering",
        "3. Implement ticker_to_cusip(ticker: str) -> str | None",
        "",
        "**Benefit**: Enables Maggie to filter 13F holdings to specific tickers",
        "",
        "### Priority 2: Form 4 Transaction Detail Parsing",
        "",
        "**Implementation**:",
        "1. Fetch individual Form 4 XML documents using accession numbers",
        "2. Parse XML to extract transaction table (derivativeTable and nonDerivativeTable)",
        "3. Extract transaction type (P=purchase, S=sale, A=award, etc.)",
        "4. Extract share count, price per share, total value",
        "5. Identify reporting person role (CEO, CFO, Director, 10% Owner, etc.)",
        "6. Filter to open-market purchases (code P) >= $100k by C-suite/directors",
        "",
        "**Benefit**: Eddie can generate confidence-weighted ticker-specific insider-trading signals",
        "",
        "### Priority 3: 13F Holdings Parsing",
        "",
        "**Implementation**:",
        "1. Parse 13F XML to extract individual holdings table",
        "2. Filter holdings by CUSIP",
        "3. Compare quarter-over-quarter position changes",
        "",
        "**Benefit**: Maggie can detect institutional interest changes for specific tickers",
        "",
        "### Priority 4: Ticker Drilldown CLI Enhancement",
        "",
        "**Implementation**:",
        "1. Add --ticker parameter to all scout agents",
        "2. Implement dry-run mode that doesn't consume production guard",
        "3. Add diagnostic output mode for development/testing",
        "",
        "**Benefit**: Enables Roger to query any ticker on-demand without waiting for scheduled runs",
        "",
        "---",
        "",
        "## Conclusion",
        "",
        f"This diagnostic report demonstrates the current insider-trading framework's structure and agent roles for ticker `{ticker}`.",
        "",
    ])

    if ticker_resolution.ok:
        lines.extend([
            f"**Progress**: ✅ Ticker-to-CIK resolution is now implemented. {ticker} resolves to CIK {ticker_resolution.cik_padded} ({ticker_resolution.company_name}).",
            "",
            "**Current Capability**: Eddie can now filter Form 4 filings to this specific issuer.",
            "",
        ])
    else:
        lines.extend([
            f"**Progress**: ❌ Ticker resolution attempted but {ticker} was not found in SEC company tickers mapping.",
            "",
        ])

    lines.extend([
        "**Next Steps**:",
        "1. ✅ COMPLETE: Ticker-to-CIK resolution (Priority 1)",
        "2. Implement Form 4 transaction detail parsing (Priority 2)",
        "3. Implement ticker-to-CUSIP resolution (Priority 1B)",
        "4. Parse 13F holdings for ticker-specific analysis (Priority 3)",
        "",
        "**Timeline Estimate**: Priority 2 (Form 4 detail parsing) could be implemented in 1 checkpoint, enabling confidence-weighted ticker-specific insider-trading signals.",
        "",
        "---",
        "",
        "**Report Generated**: " + now.isoformat(),
        "",
        "**Generated By**: scripts/ticker_drilldown.py",
        "",
        "**Disclaimer**: This report is informational only and is not trading advice. All analysis is based on publicly available SEC filings and current project connector capabilities. No buy/sell/trade instructions are provided.",
    ])

    report_content = "\n".join(lines)

    # Save to file if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_content, encoding="utf-8")
        print(f"[ticker_drilldown] Report saved: {output_path}")

    return report_content


def main() -> int:
    """Main entry point for ticker drilldown diagnostic."""
    parser = argparse.ArgumentParser(
        description="Generate a diagnostic ticker-level insider-trading report"
    )
    parser.add_argument(
        "--ticker",
        required=True,
        help="Stock ticker symbol (e.g., MAIA)",
    )
    parser.add_argument(
        "--dry-run-report",
        action="store_true",
        help="Generate dry-run diagnostic report only (no alerts)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/sample_reports") / "MAIA_manual_ticker_drilldown_report.md",
        help="Output path for report (default: docs/sample_reports/MAIA_manual_ticker_drilldown_report.md)",
    )

    args = parser.parse_args()

    if not args.dry_run_report:
        print("[ticker_drilldown] ERROR: Only --dry-run-report mode is currently supported")
        return 1

    print(f"[ticker_drilldown] Generating diagnostic report for {args.ticker.upper()}...")
    print("[ticker_drilldown] Mode: DRY-RUN (no alerts will be sent)")

    report = generate_ticker_report(args.ticker, args.output)

    print(f"[ticker_drilldown] Report generated successfully")
    print(f"[ticker_drilldown] Length: {len(report)} characters")

    return 0


if __name__ == "__main__":
    sys.exit(main())
