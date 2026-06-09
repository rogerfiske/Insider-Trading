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
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# SAFETY: Force dry-run mode for manual ticker research
# This ensures ticker drilldown can never send Telegram/email
os.environ["ROSS_DRY_RUN"] = "true"
os.environ["ALERT_ENABLE_TELEGRAM"] = "false"
os.environ["ALERT_ENABLE_EMAIL"] = "false"

from sources.sec_form4 import SecForm4Connector
from sources.sec_13f import Sec13FConnector
from sources.sec_ticker import SecTickerResolver
from sources.sec_form4_details import fetch_and_parse_form4, summarize_transactions_for_report
from sources.sec_13f_parser import fetch_and_parse_13f_info_table
from sources.sec_13f_matcher import match_ticker_to_13f_holdings, summarize_13f_matches_for_report
from sources.sec_submissions import get_form4_filings_for_cik
from sources.ticker_research_results import EddieTickerResult, MaggieTickerResult, TickerResearchReport
from sources.sec_common import utcnow_iso


def generate_ticker_report(
    ticker: str,
    output_path: Path | None = None,
    lookback_days: int = 365,
    max_form4_filings: int = 0,
) -> str:
    """Generate a comprehensive ticker drilldown report.

    Args:
        ticker: Stock ticker symbol (e.g., "MAIA")
        output_path: Optional path to save report
        lookback_days: Number of days to look back for Form 4 filings (default: 365)
        max_form4_filings: Maximum number of Form 4 filings to parse (0 = unlimited, default: 0)

    Returns:
        Report content as markdown string
    """
    ticker = ticker.upper()
    now = datetime.now(timezone.utc)

    # Resolve ticker to CIK
    ticker_resolver = SecTickerResolver()
    ticker_resolution = ticker_resolver.resolve(ticker)

    # Fetch issuer-specific Form 4 filings if ticker resolution succeeded
    # Uses SEC submissions API: https://data.sec.gov/submissions/CIK{cik}.json
    if ticker_resolution.ok:
        issuer_form4_filings = get_form4_filings_for_cik(ticker_resolution.cik_padded, lookback_days)
    else:
        issuer_form4_filings = []

    # Parse Form 4 filings early to determine Eddie status for summary table
    # This section computes eddie_status, signal, confidence, and signal_reason
    parsed_details = []
    all_purchases = []
    all_sales = []
    all_options = []
    all_grants = []
    all_owners = set()
    eddie_status = "APPLICABLE_NO_RECENT_FILINGS"
    signal = "NEUTRAL"
    confidence = 1
    signal_reason = "No recent Form 4 filings found for this issuer"

    if ticker_resolution.ok and issuer_form4_filings:
        # Apply max_form4_filings limit: 0 means unlimited
        filings_to_parse = issuer_form4_filings if max_form4_filings == 0 else issuer_form4_filings[:max_form4_filings]

        for filing in filings_to_parse:
            accession = filing.accession_number
            primary_doc = filing.primary_document
            if accession:
                details = fetch_and_parse_form4(accession, ticker_resolution.cik_padded, primary_doc)
                if details.parse_status in ("success", "partial"):
                    parsed_details.append(details)
                    summary = summarize_transactions_for_report(details)

                    # Aggregate transactions
                    all_purchases.extend(summary.get("open_market_purchases", {}).get("transactions", []))
                    all_sales.extend(summary.get("open_market_sales", {}).get("transactions", []))
                    all_options.extend(summary.get("option_exercises", {}).get("transactions", []))
                    all_grants.extend(summary.get("grants_awards", {}).get("transactions", []))

                    # Track unique owners
                    for owner in details.owners:
                        owner_desc = f"{owner.name}"
                        if owner.officer_title:
                            owner_desc += f" ({owner.officer_title})"
                        elif owner.is_director:
                            owner_desc += " (Director)"
                        all_owners.add(owner_desc)

        # Calculate total values
        total_purchase_value = sum(txn.transaction_value for txn in all_purchases if txn.transaction_value)
        total_sale_value = sum(txn.transaction_value for txn in all_sales if txn.transaction_value)

        # Determine Eddie's status and signal based on parsed results
        if parsed_details:
            if all_purchases:
                eddie_status = "APPLICABLE_WITH_EVIDENCE"
                # Conservative: only bullish if purchases and no significant sales
                if total_purchase_value > total_sale_value:
                    signal = "BULLISH_EVIDENCE"
                    confidence = 2
                    signal_reason = f"Recent insider purchases detected ({len(all_purchases)} transaction(s), ${total_purchase_value:,.2f} total value)"
                else:
                    signal = "NEUTRAL"
                    confidence = 1
                    signal_reason = "Insider purchases found but offset by sales"
            elif all_sales:
                eddie_status = "APPLICABLE_WITH_EVIDENCE"
                signal = "BEARISH_EVIDENCE"
                confidence = 2
                signal_reason = f"Recent insider sales detected ({len(all_sales)} transaction(s), ${total_sale_value:,.2f} total value)"
            elif all_grants or all_options:
                eddie_status = "APPLICABLE_WITH_EVIDENCE"
                signal = "NEUTRAL"
                confidence = 1
                signal_reason = "Only grants/awards or option exercises found (no open-market transactions)"
            else:
                eddie_status = "APPLICABLE_WITH_LIMITED_DETAILS"
                signal = "NEUTRAL"
                confidence = 1
                signal_reason = "Form 4 filings parsed but no classifiable transactions found"
        else:
            eddie_status = "APPLICABLE_WITH_LIMITED_DETAILS"
            signal = "NEUTRAL"
            confidence = 1
            signal_reason = "Form 4 filings found but XML parsing failed or returned no transactions"

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
        f"**Lookback Window**: {lookback_days} days",
        "",
        "**Purpose**: Diagnostic sample report showing what each agent would contribute for this ticker.",
        "",
        "**Mode**: DRY-RUN — No Telegram or email was sent. This report is for analysis only.",
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
            "**Current Status**: Ticker-to-CIK resolution, Form 4 XML parsing, and 13F issuer matching are now implemented. Eddie can filter and parse Form 4 transaction details. Maggie can parse 13F holdings and match by issuer name.",
            "",
            "**Remaining Limitations**: CUSIP not available from ticker resolution (issuer-name matching used). Historical 13F trend comparison not yet implemented.",
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

    # Eddie row depends on ticker resolution success and uses computed status
    if ticker_resolution.ok:
        # Use computed eddie_status, signal, confidence, signal_reason from Form 4 parsing
        evidence_status = "Form 4 XML parser implemented"
        if parsed_details:
            evidence_status = f"Parsed {len(parsed_details)} Form 4 filing(s) with {len(all_purchases) + len(all_sales) + len(all_grants) + len(all_options)} transaction(s)"
        lines.append(f"| Eddie | {eddie_status} | {evidence_status} | {signal} | {confidence} | {signal_reason} |")
    else:
        lines.append(f"| Eddie | TICKER_RESOLUTION_FAILED | Cannot resolve {ticker} to CIK | N/A | N/A | Ticker not found in SEC mapping |")

    lines.extend([
        f"| Maggie | APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING | 13F parser/matcher implemented | NEUTRAL | 1 | Issuer-name matching used (CUSIP unavailable) |",
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
    # Note: Form 4 parsing already completed earlier to populate eddie_status
    if ticker_resolution.ok:
        lines.extend([
            f"**Applicability**: {eddie_status}",
            "",
            "**Ticker Resolution**:",
            f"- ✅ {ticker} → CIK {ticker_resolution.cik_padded} ({ticker_resolution.company_name})",
            f"- Ticker-to-CIK resolution implemented",
            "",
            "**Current Behavior**:",
            f"- Eddie fetches issuer-specific Form 4 filings from SEC submissions API",
            f"- Source: https://data.sec.gov/submissions/CIK{ticker_resolution.cik_padded}.json",
            f"- Lookback: {lookback_days} days (filingDate basis)",
            f"- Found: {len(issuer_form4_filings)} Form 4 filings for CIK {ticker_resolution.cik_padded}",
            f"- Parsed: {len(parsed_details)} filings successfully",
            "",
        ])

        if parsed_details:
            lines.append(f"**{ticker} Form 4 Transaction Summary**:")
            lines.append(f"- Total filings parsed: {len(parsed_details)}")
            lines.append(f"- Open-market purchases: {len(all_purchases)} transaction(s), ${total_purchase_value:,.2f}")
            lines.append(f"- Open-market sales: {len(all_sales)} transaction(s), ${total_sale_value:,.2f}")
            lines.append(f"- Option exercises: {len(all_options)} transaction(s)")
            lines.append(f"- Grants/awards: {len(all_grants)} transaction(s)")
            if all_owners:
                lines.append(f"- Notable reporting owners: {len(all_owners)}")
                for owner_desc in sorted(all_owners)[:5]:
                    lines.append(f"  - {owner_desc}")
            lines.append("")

            # Show sample transactions
            if all_purchases:
                lines.append("**Sample Open-Market Purchases**:")
                for i, txn in enumerate(all_purchases[:3], 1):
                    value_str = f"${txn.transaction_value:,.2f}" if txn.transaction_value else "N/A"
                    lines.append(f"{i}. {txn.transaction_date}: {txn.shares:,.0f} shares @ ${txn.price_per_share:.2f} = {value_str}")
                lines.append("")

            if all_sales:
                lines.append("**Sample Open-Market Sales**:")
                for i, txn in enumerate(all_sales[:3], 1):
                    value_str = f"${txn.transaction_value:,.2f}" if txn.transaction_value else "N/A"
                    lines.append(f"{i}. {txn.transaction_date}: {txn.shares:,.0f} shares @ ${txn.price_per_share:.2f} = {value_str}")
                lines.append("")

            lines.append("**Evidence Status**: Form 4 XML details parsed successfully")
        elif issuer_form4_filings:
            lines.append(f"**{ticker} Form 4 Filings**: {len(issuer_form4_filings)} found, but XML parsing failed or returned no transactions")
            lines.append("")
            lines.append("**Evidence Status**: CIK-filtered filings found, but detail extraction limited")
        else:
            lines.append(f"**{ticker} Form 4 Filings**: None found in {lookback_days}-day lookback window")
            lines.append("")
            lines.append("**Evidence Status**: No recent filings")

        lines.extend([
            "",
            f"**Signal**: {signal}",
            "",
            f"**Confidence**: {confidence}",
            "",
            f"**Reason**: {signal_reason}",
            "",
            "**Disclaimer**: This analysis is informational only and is not trading advice. Insider transactions can occur for many reasons unrelated to stock price expectations.",
        ])

        if parsed_details:
            lines.append("")
            lines.append("**Source URLs**:")
            for details in parsed_details[:5]:
                lines.append(f"- {details.source_url} (Accession: {details.accession_number})")
        elif issuer_form4_filings:
            lines.append("")
            lines.append("**Source URLs**:")
            for filing in issuer_form4_filings[:5]:
                if filing.primary_document_url:
                    lines.append(f"- {filing.primary_document_url} (Accession: {filing.accession_number})")
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
            f"- Eddie requires valid ticker-to-CIK resolution to fetch issuer-specific Form 4 filings",
            f"- Cannot retrieve {ticker} Form 4 filings without a valid CIK",
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
    ])

    # Maggie section depends on ticker resolution and 13F data
    if ticker_resolution.ok and form13f_result.ok:
        # Parse 13F info tables and match to ticker
        all_holdings_parsed = []
        all_matches = []

        for ev in form13f_result.evidence[:5]:  # Limit to first 5 managers
            manager_name = ev.normalized.get("manager_name", "")
            manager_cik = ev.normalized.get("manager_cik", "")
            accession = ev.normalized.get("accession_number", "")
            filing_date = ev.normalized.get("filing_date", "")
            report_period = ev.normalized.get("report_period", "")
            primary_doc = ev.normalized.get("primary_document", "")

            if accession and manager_cik:
                # Fetch and parse 13F info table
                parse_result = fetch_and_parse_13f_info_table(
                    accession_number=accession,
                    cik=manager_cik,
                    manager_name=manager_name,
                    filing_date=filing_date,
                    report_period=report_period,
                    primary_document=primary_doc,
                )

                if parse_result.parse_status in ("success", "partial") and parse_result.holdings:
                    all_holdings_parsed.append(parse_result)

                    # Match holdings to ticker
                    matches = match_ticker_to_13f_holdings(
                        ticker=ticker,
                        resolved_company_name=ticker_resolution.company_name,
                        resolved_cik=ticker_resolution.cik_padded,
                        holdings=parse_result.holdings,
                        cusip=None,  # CUSIP not available from ticker resolution
                    )
                    all_matches.extend(matches)

        # Determine Maggie's status and signal
        if all_matches:
            maggie_status = "APPLICABLE_WITH_13F_EVIDENCE"
            signal = "NEUTRAL"
            confidence = 2
            signal_reason = f"Found {len(all_matches)} institutional holding(s) for {ticker}, but no historical trend available (static holdings only)"
        elif all_holdings_parsed:
            maggie_status = "APPLICABLE_NO_13F_HOLDINGS_FOUND"
            signal = "NEUTRAL"
            confidence = 1
            signal_reason = f"No {ticker} holdings found among tracked managers (parsed {len(all_holdings_parsed)} 13F filing(s))"
        else:
            maggie_status = "APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING"
            signal = "NEUTRAL"
            confidence = 1
            signal_reason = "13F information table parsing failed or returned no holdings"

        lines.extend([
            f"**Applicability**: {maggie_status}",
            "",
            "**Ticker Resolution**:",
            f"- ✅ {ticker} → CIK {ticker_resolution.cik_padded} ({ticker_resolution.company_name})",
            "- Issuer-name matching implemented (CUSIP not available from ticker resolution)",
            "",
            "**Current Behavior**:",
            f"- Maggie fetches 13F filings for configured institutional managers ({len(form13f_result.evidence)} filings found)",
            f"- Parses 13F information table XML to extract holdings ({len(all_holdings_parsed)} successfully parsed)",
            f"- Matches holdings to {ticker} by issuer name",
            "",
        ])

        if all_matches:
            summary = summarize_13f_matches_for_report(ticker, all_matches)

            lines.append(f"**{ticker} Institutional Holdings Summary**:")
            lines.append(f"- Total matching holdings: {summary['match_count']}")
            lines.append(f"- Total position value: ${summary['total_value_usd']:,.2f}")
            lines.append(f"- Total shares held: {summary['total_shares']:,.0f}")
            lines.append(f"- Managers holding {ticker}: {len(summary['managers'])}")
            lines.append("")

            lines.append("**Holding Details**:")
            for mgr in summary["managers"][:3]:  # Show top 3 managers
                lines.append(f"- **{mgr['name']}** (Report Period: {mgr['report_period']})")
                for match in mgr["holdings"][:2]:  # Show up to 2 holdings per manager
                    h = match.holding
                    lines.append(f"  - {h.shares_or_principal_amount:,.0f} {h.share_type} @ ${h.value_usd:,.2f}")
                    lines.append(f"    CUSIP: {h.cusip}, Class: {h.title_of_class}")
                    lines.append(f"    Match: {match.confidence}")
            lines.append("")

            lines.append("**Evidence Status**: Institutional holdings found")
        elif all_holdings_parsed:
            lines.append(f"**{ticker} Institutional Holdings**: None found in parsed 13F filings")
            lines.append("")
            lines.append("**Evidence Status**: No holdings matched")
        else:
            lines.append("**13F Parsing**: Failed or returned no holdings")
            lines.append("")
            lines.append("**Evidence Status**: Limited data extraction")

        lines.extend([
            "",
            f"**Signal**: {signal}",
            "",
            f"**Confidence**: {confidence}",
            "",
            f"**Reason**: {signal_reason}",
            "",
            "**Limitation**: Historical comparison not yet implemented (static holdings only, no QoQ/YoY trend)",
            "",
            "**Disclaimer**: This analysis is informational only and is not trading advice. Institutional holdings are reported quarterly and may not reflect current positions.",
        ])

        if all_matches:
            lines.append("")
            lines.append("**Source URLs**:")
            managers_shown = set()
            for match in all_matches[:5]:
                if match.holding.manager_name not in managers_shown:
                    if match.holding.source_url:
                        lines.append(f"- {match.holding.source_url} ({match.holding.manager_name})")
                    managers_shown.add(match.holding.manager_name)
        else:
            lines.append("")
            lines.append("**Source URLs**: N/A (no matched holdings)")

    elif ticker_resolution.ok:
        # Ticker resolved but 13F fetch failed
        lines.extend([
            "**Applicability**: FAILED_GRACEFULLY",
            "",
            "**Ticker Resolution**:",
            f"- ✅ {ticker} → CIK {ticker_resolution.cik_padded} ({ticker_resolution.company_name})",
            "",
            "**Current Behavior**:",
            "- 13F connector fetch failed",
            "",
            "**Evidence Status**: Cannot retrieve 13F data",
            "",
            "**Signal**: N/A",
            "",
            "**Confidence**: N/A",
            "",
            "**Reason**: 13F data retrieval failed",
        ])
    else:
        # Ticker resolution failed
        lines.extend([
            "**Applicability**: TICKER_RESOLUTION_FAILED",
            "",
            "**Ticker Resolution**:",
            f"- ❌ {ticker} could not be resolved to CIK",
            f"- Error: {ticker_resolution.error_message}",
            "",
            "**Current Behavior**:",
            "- Cannot match 13F holdings without ticker resolution",
            "",
            "**Evidence Status**: Cannot match without issuer name",
            "",
            "**Signal**: N/A",
            "",
            "**Confidence**: N/A",
            "",
            f"**Reason**: {ticker} not found in SEC company tickers database",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## Frank — Federal Reserve / Macro Context",
        "",
        "**Applicability**: PARTIALLY_APPLICABLE",
        "",
        "**Current Behavior**:",
        "- Frank analyzes Federal Reserve policy and macroeconomic conditions",
        "- Provides market-wide context, not ticker-specific analysis",
        "",
        "**Evidence Status**: Macro context only",
        "",
        "**Signal**: NEUTRAL",
        "",
        "**Confidence**: 1",
        "",
        "**Reason**: Not ticker-specific",
        "",
        "**Disclaimer**: Macro context is informational and not tailored to individual securities.",
        "",
        "---",
        "",
        "## Maya — On-Chain / Whale Movement",
        "",
        "**Applicability**: NOT_APPLICABLE",
        "",
        "**Current Behavior**:",
        "- Maya analyzes cryptocurrency and blockchain data",
        "- Not applicable to traditional equities",
        "",
        "**Evidence Status**: N/A",
        "",
        "**Signal**: N/A",
        "",
        "**Confidence**: N/A",
        "",
        f"**Reason**: {ticker} is a stock, not a cryptocurrency",
        "",
        "**Disclaimer**: Maya only analyzes crypto assets.",
        "",
        "---",
        "",
        "## Janet — Portfolio Drift",
        "",
        "**Applicability**: NOT_APPLICABLE",
        "",
        "**Current Behavior**:",
        "- Janet analyzes positions in Roger's configured portfolio",
        f"- {ticker} is not currently in the tracked portfolio",
        "",
        "**Evidence Status**: N/A",
        "",
        "**Signal**: N/A",
        "",
        "**Confidence**: N/A",
        "",
        f"**Reason**: {ticker} not in local portfolio configuration",
        "",
        "**Disclaimer**: Janet only analyzes configured portfolio holdings.",
        "",
        "---",
        "",
        "## Sophie — Consensus Aggregator",
        "",
        "**Applicability**: APPLICABLE_TO_AGENT_OUTPUTS",
        "",
        "**Current Behavior**:",
        "- Sophie aggregates signals from other agents (Eddie, Maggie, Frank, Maya, Janet)",
        "- Requires ticker-specific signals to aggregate",
        "",
        "**Evidence Status**: No ticker-specific signals to aggregate",
        "",
        "**Signal**: N/A",
        "",
        "**Confidence**: N/A",
        "",
        f"**Reason**: No bullish or bearish signals generated for {ticker}",
        "",
        "**Disclaimer**: Sophie's consensus depends on upstream agent signals.",
        "",
        "---",
        "",
        "## Ross — Routing / Reporting",
        "",
        "**Applicability**: DRY_RUN_ONLY",
        "",
        "**Current Behavior**:",
        "- Ross routes consensus signals to Telegram and/or email",
        "- DRY-RUN mode: no alerts sent",
        "",
        "**Evidence Status**: No actionable signals to route",
        "",
        "**Signal**: N/A",
        "",
        "**Confidence**: N/A",
        "",
        "**Reason**: No consensus signals generated; dry-run mode active",
        "",
        "**Disclaimer**: Ross only routes signals when production mode is enabled and consensus is reached.",
        "",
        "---",
        "",
    ])

    # Report issuer-specific Form 4 filing count
    lines.extend([
        "**SEC Form 4**:",
        f"- Retrieval method: Issuer-specific (SEC submissions API)",
        f"- Lookback: {lookback_days} days (filingDate basis)",
    ])

    if ticker_resolution.ok:
        lines.append(f"- Source: https://data.sec.gov/submissions/CIK{ticker_resolution.cik_padded}.json")
        lines.append(f"- {ticker}-specific filings found: {len(issuer_form4_filings)} (CIK {ticker_resolution.cik_padded})")
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
        "2. **~~Form 4 Transaction Detail Extraction~~** ✅ RESOLVED:",
        "   - ✅ Form 4 XML parser now implemented (sources/sec_form4_details.py)",
        "   - ✅ Eddie can now extract transaction type, share count, price, and value",
        "   - ✅ Eddie generates confidence-weighted signals based on insider transactions",
        "",
        "3. **Ticker-to-CUSIP Resolution** (Still Missing):",
        "   - CUSIP not available from SEC company_tickers.json",
        "   - Issuer-name matching used as conservative alternative",
        "",
        "4. **~~13F Individual Holdings Parsing~~** ✅ RESOLVED:",
        "   - ✅ 13F information table XML parser now implemented (sources/sec_13f_parser.py)",
        "   - ✅ Maggie can now parse holdings with CUSIP, issuer name, value, shares",
        "",
        "5. **Historical Comparison** (Still Missing):",
        "   - Connectors fetch current period only",
        "   - Cannot detect QoQ or YoY changes in holdings",
        "",
        "### Agent-Specific Limitations",
        "",
        "1. **Eddie**: ✅ Can now filter to CIK and parse Form 4 transaction details; generates confidence-weighted signals",
        "2. **Maggie**: ✅ Can now parse 13F holdings and match by issuer name; limited by CUSIP unavailability and no historical trend comparison",
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
            "**Current Capability**: Eddie can filter and parse Form 4 transaction details. Maggie can parse 13F holdings and match by issuer name.",
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
        "2. ✅ COMPLETE: Form 4 transaction detail parsing (Priority 2)",
        "3. ✅ COMPLETE: 13F holdings parsing and issuer-name matching (Priority 3)",
        "4. Implement historical 13F trend comparison (Priority 4)",
        "",
        "**Timeline Estimate**: Priority 4 (historical 13F trend comparison) could be implemented in 1 checkpoint, enabling quarter-over-quarter institutional holdings trend detection.",
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


def extract_structured_transaction_metrics(
    ticker: str,
    lookback_days: int = 365,
    max_form4_filings: int = 0,
) -> dict[str, Any]:
    """Extract structured transaction metrics for scoring inputs.

    This function extracts the same Form 4 data as generate_ticker_report but returns
    it in a structured format suitable for populating insider evidence scoring inputs.

    Args:
        ticker: Stock ticker symbol (e.g., "MAIA")
        lookback_days: Number of days to look back for Form 4 filings
        max_form4_filings: Maximum number of Form 4 filings to parse (0 = unlimited)

    Returns:
        Dictionary with structured transaction metrics including:
        - distinct_buyers: Count of unique reporting owners in filings with purchases
        - distinct_buyer_names: List of buyer names with titles
        - distinct_sellers: Count of unique reporting owners in filings with sales
        - distinct_seller_names: List of seller names with titles
        - latest_purchase_date: Most recent purchase date (YYYY-MM-DD) or None
        - latest_sale_date: Most recent sale date (YYYY-MM-DD) or None
        - buyer_roles: List of officer titles from owners in purchase filings
        - seller_roles: List of officer titles from owners in sale filings
        - purchase_months: List of unique YYYY-MM from purchase transactions
        - sale_months: List of unique YYYY-MM from sale transactions
        - form4_filings_found: Count of Form 4 filings found
        - form4_filings_parsed: Count of Form 4 filings successfully parsed
        - transactions_extracted: Total count of transactions extracted
        - purchase_count: Count of purchase transactions
        - purchase_value: Total purchase value
        - sale_count: Count of sale transactions
        - sale_value: Total sale value
    """
    ticker = ticker.upper()

    # Resolve ticker to CIK
    ticker_resolver = SecTickerResolver()
    ticker_resolution = ticker_resolver.resolve(ticker)

    # Initialize metrics
    metrics = {
        "distinct_buyers": 0,
        "distinct_buyer_names": [],
        "distinct_sellers": 0,
        "distinct_seller_names": [],
        "latest_purchase_date": None,
        "latest_sale_date": None,
        "buyer_roles": [],
        "seller_roles": [],
        "purchase_months": [],
        "sale_months": [],
        "form4_filings_found": 0,
        "form4_filings_parsed": 0,
        "transactions_extracted": 0,
        "purchase_count": 0,
        "purchase_value": 0.0,
        "sale_count": 0,
        "sale_value": 0.0,
    }

    # Return empty metrics if ticker resolution failed
    if not ticker_resolution.ok:
        return metrics

    # Fetch issuer-specific Form 4 filings
    issuer_form4_filings = get_form4_filings_for_cik(ticker_resolution.cik_padded, lookback_days)
    metrics["form4_filings_found"] = len(issuer_form4_filings)

    if not issuer_form4_filings:
        return metrics

    # Parse Form 4 filings
    filings_to_parse = issuer_form4_filings if max_form4_filings == 0 else issuer_form4_filings[:max_form4_filings]

    parsed_details = []
    all_purchases = []
    all_sales = []
    purchase_filing_owners = set()  # Owners from filings with purchases
    sale_filing_owners = set()      # Owners from filings with sales

    for filing in filings_to_parse:
        accession = filing.accession_number
        primary_doc = filing.primary_document
        if accession:
            details = fetch_and_parse_form4(accession, ticker_resolution.cik_padded, primary_doc)
            if details.parse_status in ("success", "partial"):
                parsed_details.append(details)
                summary = summarize_transactions_for_report(details)

                # Get transactions
                purchases = summary.get("open_market_purchases", {}).get("transactions", [])
                sales = summary.get("open_market_sales", {}).get("transactions", [])

                all_purchases.extend(purchases)
                all_sales.extend(sales)

                # Track owners from filings with purchases
                if purchases:
                    for owner in details.owners:
                        purchase_filing_owners.add((owner.name, owner.officer_title, owner.is_director))

                # Track owners from filings with sales
                if sales:
                    for owner in details.owners:
                        sale_filing_owners.add((owner.name, owner.officer_title, owner.is_director))

    metrics["form4_filings_parsed"] = len(parsed_details)
    metrics["transactions_extracted"] = len(all_purchases) + len(all_sales)

    # Process purchase metrics
    if all_purchases:
        metrics["purchase_count"] = len(all_purchases)
        metrics["purchase_value"] = sum(txn.transaction_value for txn in all_purchases if txn.transaction_value)

        # Extract purchase dates
        purchase_dates = [txn.transaction_date for txn in all_purchases if txn.transaction_date]
        if purchase_dates:
            metrics["latest_purchase_date"] = max(purchase_dates)

            # Extract unique purchase months
            purchase_months = set()
            for date_str in purchase_dates:
                if len(date_str) >= 7:  # YYYY-MM-DD format
                    purchase_months.add(date_str[:7])  # YYYY-MM
            metrics["purchase_months"] = sorted(list(purchase_months))

    # Process sale metrics
    if all_sales:
        metrics["sale_count"] = len(all_sales)
        metrics["sale_value"] = sum(txn.transaction_value for txn in all_sales if txn.transaction_value)

        # Extract sale dates
        sale_dates = [txn.transaction_date for txn in all_sales if txn.transaction_date]
        if sale_dates:
            metrics["latest_sale_date"] = max(sale_dates)

            # Extract unique sale months
            sale_months = set()
            for date_str in sale_dates:
                if len(date_str) >= 7:
                    sale_months.add(date_str[:7])
            metrics["sale_months"] = sorted(list(sale_months))

    # Process buyer information
    if purchase_filing_owners:
        buyer_names = []
        buyer_roles = []

        for name, title, is_director in purchase_filing_owners:
            # Build name with title
            name_with_title = name
            if title:
                name_with_title += f" ({title})"
            elif is_director:
                name_with_title += " (Director)"
            buyer_names.append(name_with_title)

            # Extract role for scoring
            if title:
                buyer_roles.append(title)
            elif is_director:
                buyer_roles.append("Director")

        metrics["distinct_buyers"] = len(purchase_filing_owners)
        metrics["distinct_buyer_names"] = sorted(buyer_names)
        metrics["buyer_roles"] = sorted(list(set(buyer_roles)))  # Deduplicate roles

    # Process seller information
    if sale_filing_owners:
        seller_names = []
        seller_roles = []

        for name, title, is_director in sale_filing_owners:
            # Build name with title
            name_with_title = name
            if title:
                name_with_title += f" ({title})"
            elif is_director:
                name_with_title += " (Director)"
            seller_names.append(name_with_title)

            # Extract role
            if title:
                seller_roles.append(title)
            elif is_director:
                seller_roles.append("Director")

        metrics["distinct_sellers"] = len(sale_filing_owners)
        metrics["distinct_seller_names"] = sorted(seller_names)
        metrics["seller_roles"] = sorted(list(set(seller_roles)))

    return metrics


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
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=365,
        help="Number of days to look back for Form 4 filings (default: 365, max: 1460)",
    )
    parser.add_argument(
        "--max-form4-filings",
        type=int,
        default=0,
        help="Maximum number of Form 4 filings to parse (0 = unlimited, default: 0)",
    )

    args = parser.parse_args()

    # Validate lookback-days
    if args.lookback_days <= 0:
        print(f"[ticker_drilldown] ERROR: --lookback-days must be positive (got {args.lookback_days})")
        return 1
    if args.lookback_days > 1460:
        print(f"[ticker_drilldown] ERROR: --lookback-days cannot exceed 1460 days / 4 years (got {args.lookback_days})")
        return 1

    # Validate max-form4-filings
    if args.max_form4_filings < 0:
        print(f"[ticker_drilldown] ERROR: --max-form4-filings must be non-negative (got {args.max_form4_filings})")
        return 1

    if not args.dry_run_report:
        print("[ticker_drilldown] ERROR: Only --dry-run-report mode is currently supported")
        return 1

    print(f"[ticker_drilldown] Generating diagnostic report for {args.ticker.upper()}...")
    print(f"[ticker_drilldown] Lookback window: {args.lookback_days} days")
    if args.max_form4_filings == 0:
        print("[ticker_drilldown] Form 4 parsing limit: unlimited")
    else:
        print(f"[ticker_drilldown] Form 4 parsing limit: {args.max_form4_filings} filings")
    print("[ticker_drilldown] Mode: DRY-RUN (no alerts will be sent)")

    report = generate_ticker_report(
        args.ticker,
        args.output,
        lookback_days=args.lookback_days,
        max_form4_filings=args.max_form4_filings,
    )

    print(f"[ticker_drilldown] Report generated successfully")
    print(f"[ticker_drilldown] Length: {len(report)} characters")

    return 0


if __name__ == "__main__":
    sys.exit(main())
