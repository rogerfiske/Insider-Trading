# MAIA — Manual Ticker Drilldown Diagnostic Report

**Generated**: 2026-06-05T16:30:50.662101+00:00

**Ticker**: MAIA

**Purpose**: Diagnostic sample report showing what each agent would contribute for this ticker.

**Safety Disclaimer**: This report is informational only and is not trading advice. No buy/sell/trade instructions are provided.

---

## Data Source Boundary

**Sources Used**:
- Project connectors only (SEC Form 4, SEC 13F, etc.)
- Current project state/database
- Agent logic as implemented

**Sources NOT Used**:
- Roger's uploaded OpenInsider spreadsheet
- Manual insider-trade data from chat
- External data not supported by existing connectors

---

## Executive Summary

This report exercises the seven-agent insider-trading framework for ticker `MAIA`. Due to current connector limitations, most agents cannot filter to ticker-specific data and instead analyze all recent data or report not applicable.

**Key Finding**: Current connectors fetch all recent filings (e.g., all Form 4s from last 24 hours) but do not support ticker-specific filtering. To generate a true ticker-level report, ticker-to-CIK resolution and ticker-specific filtering would need to be implemented.

---

## Agent Applicability Summary

| Agent | Applicability | Evidence Status | Signal | Confidence | Reason |
|-------|--------------|-----------------|--------|------------|--------|
| Eddie | BLOCKED_BY_MISSING_CONNECTOR | Cannot filter to MAIA | N/A | N/A | Ticker-to-CIK resolution not implemented |
| Maggie | BLOCKED_BY_MISSING_CONNECTOR | Cannot filter to MAIA | N/A | N/A | Ticker-to-CUSIP resolution not implemented |
| Frank | PARTIALLY_APPLICABLE | Macro context only | NEUTRAL | 1 | Not ticker-specific |
| Maya | NOT_APPLICABLE | Crypto/on-chain only | N/A | N/A | Stock ticker not applicable |
| Janet | NOT_APPLICABLE | Not in portfolio | N/A | N/A | MAIA not in local portfolio |
| Sophie | APPLICABLE_TO_AGENT_OUTPUTS | Would aggregate signals | N/A | N/A | No ticker-specific signals to aggregate |
| Ross | DRY_RUN_ONLY | Would route if signals exist | N/A | N/A | No actionable signals |

---

## Eddie — SEC Form 4 Insider Transactions

**Applicability**: BLOCKED_BY_MISSING_CONNECTOR

**Current Behavior**:
- Eddie fetches all Form 4 filings from the last 24 hours (20 filings found)
- Current connector does NOT support ticker-specific filtering
- Cannot determine if any of the 20 filings are for MAIA

**Limitation**: Ticker-to-CIK resolution not implemented

**What Would Be Needed**:
1. Implement ticker-to-CIK lookup (e.g., via SEC company tickers JSON)
2. Filter Form 4 results to CIK for MAIA
3. Analyze MAIA-specific insider transactions
4. Generate ticker-specific signal

**Evidence Status**: Cannot filter to MAIA with current connector

**Signal**: N/A (cannot generate ticker-specific signal)

**Confidence**: N/A

**Reason**: Ticker-specific filtering not supported by current Form 4 connector

**Source URLs**: N/A (no MAIA-specific filings identified)

---

## Maggie — SEC 13F Institutional Holdings

**Applicability**: BLOCKED_BY_MISSING_CONNECTOR

**Current Behavior**:
- Maggie fetches 13F filings for configured institutional managers (5 filings found)
- Current connector is manager-focused, not ticker/CUSIP-focused
- Cannot determine if selected managers hold MAIA

**Limitation**: Ticker-to-CUSIP resolution and holding-level filtering not implemented

**What Would Be Needed**:
1. Implement ticker-to-CUSIP lookup
2. Parse 13F XML to extract individual holdings
3. Filter to MAIA holdings across all managers
4. Detect position changes (additions, increases, decreases, exits)
5. Generate ticker-specific signal

**Evidence Status**: Cannot filter to MAIA with current connector

**Signal**: N/A (cannot generate ticker-specific signal)

**Confidence**: N/A

**Reason**: Ticker-specific 13F filtering not supported

---

## Frank — Federal Reserve / Macro Context

**Applicability**: PARTIALLY_APPLICABLE (macro context only)

**Current Behavior**:
- Frank monitors Federal Reserve speeches and policy signals
- Frank is intentionally macro-focused, not ticker-specific
- Frank would NOT form a ticker-specific view on MAIA

**What Frank Would Provide**:
- Overall market sentiment (dovish/hawkish Fed)
- Interest rate trajectory context
- Macro risk factors

**Signal**: NEUTRAL

**Confidence**: 1 (macro background only)

**Reason**: Frank does not analyze individual tickers like MAIA; provides macro context only

---

## Maya — On-Chain / Whale Movement

**Applicability**: NOT_APPLICABLE

**Current Behavior**:
- Maya monitors crypto/blockchain wallet activity
- MAIA is a stock ticker, not a crypto asset
- Maya has no visibility into stock transactions

**Why Not Applicable**: MAIA is not a cryptocurrency or blockchain-related asset

**Signal**: N/A

**Confidence**: N/A

**Reason**: Maya only analyzes crypto assets; MAIA is a stock

---

## Janet — Portfolio Drift

**Applicability**: NOT_APPLICABLE (not in portfolio)

**Current Behavior**:
- Janet compares current portfolio holdings to target allocation
- Janet reads `config/portfolio_current.json` and `config/portfolio_target.json`
- MAIA is not present in local portfolio files

**Evidence Status**: Not in portfolio

**Signal**: N/A (no drift to report)

**Confidence**: N/A

**Reason**: MAIA not present in local portfolio configuration

**Note**: If Roger wants Janet to track MAIA, he would need to add it to portfolio configuration files

---

## Sophie — Consensus Aggregator

**Applicability**: APPLICABLE_TO_AGENT_OUTPUTS

**Current Behavior**:
- Sophie reads recent scout signals from all agents
- Sophie groups signals by ticker and direction
- Sophie applies consensus threshold (default: 2+ agents agreeing)

**For MAIA**:
- **Signals collected**: 0 ticker-specific signals
- **Consensus met**: No (threshold not reached)
- **Result**: No consensus event generated

**Reason**: No agents produced ticker-specific signals due to connector limitations

**What Would Happen If Signals Existed**:
- If 2+ agents signaled BULLISH on MAIA, Sophie would generate a consensus event
- Sophie would aggregate confidence scores
- Sophie would mark consensus for Ross to route

---

## Ross — Routing / Reporting

**Applicability**: DRY_RUN_ONLY

**Current Behavior**:
- Ross reads pending consensus events
- Ross applies alert routing policy (severity, deduplication, channel routing)
- **DRY-RUN MODE**: No alerts actually sent

**For MAIA**:
- **Pending consensus**: None (no signals from scouts)
- **Routing decision**: N/A (nothing to route)

**What Would Happen If Consensus Existed**:
1. **Severity calculation**: Based on signal count, confidence, and historical patterns
2. **Alert class determination**:
   - ACTIONABLE (if meets ACTIONABLE threshold)
   - WATCH (if interesting but below threshold)
   - LOG_ONLY (if duplicate or low confidence)
3. **Channel routing**:
   - Telegram: Yes (if ACTIONABLE in production mode)
   - Email: No (email disabled in current pilot)
4. **Deduplication**: Check 24-hour window for duplicate MAIA signals
5. **Rate limiting**: Max 1 alert per run (current pilot configuration)

**Confirmation**: No Telegram or email was sent during this diagnostic run

---

## Source / Evidence References

**SEC Form 4**:
- Fetch status: Success
- Filings retrieved: 20 (last 24 hours)
- MAIA-specific filings: Cannot determine (ticker filtering not implemented)

**SEC 13F**:
- Fetch status: Success
- Filings retrieved: 5 (selected managers)
- MAIA holdings: Cannot determine (ticker/CUSIP filtering not implemented)

---

## Limitations

### Current Connector Limitations

1. **No Ticker-to-CIK Resolution**:
   - Form 4 connector cannot map MAIA ticker to SEC CIK
   - Cannot filter Form 4 filings to MAIA issuer

2. **No Ticker-to-CUSIP Resolution**:
   - 13F connector cannot map MAIA ticker to CUSIP
   - Cannot filter institutional holdings to MAIA

3. **No Individual Holdings Parsing**:
   - 13F connector fetches manager-level filings
   - Does not parse XML to extract individual security holdings

4. **No Historical Comparison**:
   - Connectors fetch current period only
   - Cannot detect QoQ or YoY changes in holdings

### Agent-Specific Limitations

1. **Eddie**: Cannot generate ticker-specific signals without ticker-to-CIK resolution
2. **Maggie**: Cannot analyze ticker-specific institutional interest without holding-level data
3. **Frank**: Intentionally macro-focused; not a limitation
4. **Maya**: Intentionally crypto-focused; not applicable to stocks
5. **Janet**: Requires manual portfolio configuration; not automatic

---

## Recommended Implementation Improvements

### Priority 1: Ticker-to-CIK/CUSIP Resolution

**Implementation**:
1. Download SEC company tickers JSON: https://www.sec.gov/files/company_tickers.json
2. Create ticker lookup cache in .state/
3. Implement ticker_to_cik(ticker: str) -> str | None
4. Implement ticker_to_cusip(ticker: str) -> str | None

**Benefit**: Enables Eddie and Maggie to filter to ticker-specific data

### Priority 2: Form 4 Ticker Filtering

**Implementation**:
1. After fetching all Form 4 filings, filter by CIK
2. Update SecForm4Connector.fetch() to accept optional ticker/CIK parameter
3. Update Eddie to request ticker-specific Form 4 data

**Benefit**: Eddie can generate true ticker-specific insider-trading signals

### Priority 3: 13F Holdings Parsing

**Implementation**:
1. Parse 13F XML to extract individual holdings table
2. Filter holdings by CUSIP
3. Compare quarter-over-quarter position changes

**Benefit**: Maggie can detect institutional interest changes for specific tickers

### Priority 4: Ticker Drilldown CLI Enhancement

**Implementation**:
1. Add --ticker parameter to all scout agents
2. Implement dry-run mode that doesn't consume production guard
3. Add diagnostic output mode for development/testing

**Benefit**: Enables Roger to query any ticker on-demand without waiting for scheduled runs

---

## Conclusion

This diagnostic report demonstrates the current insider-trading framework's structure and agent roles for ticker `MAIA`. While the framework is operational, current connectors do not support ticker-specific filtering.

**Next Steps**:
1. Implement ticker-to-CIK/CUSIP resolution (Priority 1)
2. Add ticker filtering to Form 4 connector (Priority 2)
3. Parse 13F holdings for ticker-specific analysis (Priority 3)
4. Rerun this diagnostic after improvements to see MAIA-specific signals

**Timeline Estimate**: Priority 1-2 improvements could be implemented in 1-2 checkpoints, enabling true ticker-specific insider-trading reports.

---

**Report Generated**: 2026-06-05T16:30:50.662101+00:00

**Generated By**: scripts/ticker_drilldown.py

**Disclaimer**: This report is informational only and is not trading advice. All analysis is based on publicly available SEC filings and current project connector capabilities. No buy/sell/trade instructions are provided.