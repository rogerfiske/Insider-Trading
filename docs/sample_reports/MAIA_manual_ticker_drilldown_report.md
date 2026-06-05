# MAIA — Manual Ticker Drilldown Diagnostic Report

**Generated**: 2026-06-05T17:04:34.539241+00:00

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

## Ticker Resolution

**Ticker**: MAIA

**CIK**: 0001878313 (1878313)
**Company Name**: MAIA Biotechnology, Inc.
**Resolution Status**: ✅ Success
**Source**: https://www.sec.gov/files/company_tickers.json
**Retrieved**: 2026-06-05T17:04:34.738439+00:00

Ticker `MAIA` successfully resolved to SEC CIK `0001878313` for issuer `MAIA Biotechnology, Inc.`.

---

## Executive Summary

This report exercises the seven-agent insider-trading framework for ticker `MAIA`.

**Ticker Resolution**: ✅ MAIA → CIK 0001878313 (MAIA Biotechnology, Inc.)

**Current Status**: Ticker-to-CIK resolution is now implemented. Eddie can now filter Form 4 filings to this specific issuer CIK.

**Remaining Limitation**: Form 4 transaction detail extraction is limited to metadata. Full XML parsing of individual transactions (share counts, prices, transaction codes) would enhance signal quality.

---

## Agent Applicability Summary

| Agent | Applicability | Evidence Status | Signal | Confidence | Reason |
|-------|--------------|-----------------|--------|------------|--------|
| Eddie | TICKER_RESOLVED_BUT_FORM4_DETAIL_EXTRACTION_LIMITED | CIK 0001878313 resolved | N/A | N/A | CIK resolved; Form 4 detail parsing limited |
| Maggie | BLOCKED_BY_MISSING_CONNECTOR | Cannot filter to MAIA | N/A | N/A | Ticker-to-CUSIP resolution not implemented |
| Frank | PARTIALLY_APPLICABLE | Macro context only | NEUTRAL | 1 | Not ticker-specific |
| Maya | NOT_APPLICABLE | Crypto/on-chain only | N/A | N/A | MAIA is a stock, not crypto |
| Janet | NOT_APPLICABLE | Not in portfolio | N/A | N/A | MAIA not in local portfolio |
| Sophie | APPLICABLE_TO_AGENT_OUTPUTS | Would aggregate signals | N/A | N/A | No ticker-specific signals to aggregate |
| Ross | DRY_RUN_ONLY | Would route if signals exist | N/A | N/A | No actionable signals |

---

## Eddie — SEC Form 4 Insider Transactions

**Applicability**: TICKER_RESOLVED_BUT_FORM4_DETAIL_EXTRACTION_LIMITED

**Ticker Resolution**:
- ✅ MAIA → CIK 0001878313 (MAIA Biotechnology, Inc.)
- Ticker-to-CIK resolution now implemented

**Current Behavior**:
- Eddie fetches all Form 4 filings from the last 24 hours (20 total filings found)
- Filters to CIK 0001878313: 0 filings for MAIA

**MAIA Form 4 Filings**: None found in last 24 hours

**Status**: Ticker resolution works, but no recent Form 4 filings for this issuer

**Evidence Status**: APPLICABLE_NO_RECENT_FILINGS

**Signal**: N/A (transaction detail parsing not yet implemented)

**Confidence**: N/A

**Reason**: CIK resolution successful, but Form 4 detail extraction still limited to metadata

**Source URLs**: N/A (no recent filings)

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
- Total filings retrieved: 20 (last 24 hours)
- MAIA-specific filings: 0 (filtered by CIK 0001878313)

**SEC 13F**:
- Fetch status: Success
- Filings retrieved: 5 (selected managers)
- MAIA holdings: Cannot determine (ticker-to-CUSIP resolution not yet implemented)

---

## Limitations

### Current Connector Limitations

1. **~~Ticker-to-CIK Resolution~~** ✅ RESOLVED:
   - ✅ Ticker-to-CIK mapping now implemented (sources/sec_ticker.py)
   - ✅ Eddie can now filter Form 4 filings by CIK

2. **Form 4 Transaction Detail Extraction** (Still Limited):
   - Form 4 connector fetches filing metadata but does not parse XML transaction tables
   - Cannot extract transaction type, share count, price, or total value
   - Eddie cannot yet generate confidence-weighted signals

3. **Ticker-to-CUSIP Resolution** (Still Missing):
   - 13F connector cannot map ticker to CUSIP
   - Cannot filter institutional holdings to specific tickers

4. **13F Individual Holdings Parsing** (Still Missing):
   - 13F connector fetches manager-level filings
   - Does not parse XML to extract individual security holdings

5. **Historical Comparison** (Still Missing):
   - Connectors fetch current period only
   - Cannot detect QoQ or YoY changes in holdings

### Agent-Specific Limitations

1. **Eddie**: ✅ Can now filter to CIK; still limited by Form 4 detail parsing
2. **Maggie**: Cannot analyze ticker-specific institutional interest without CUSIP resolution and holding-level data
3. **Frank**: Intentionally macro-focused; not a limitation
4. **Maya**: Intentionally crypto-focused; not applicable to stocks
5. **Janet**: Requires manual portfolio configuration; not automatic

---

## Recommended Implementation Improvements

### ~~Priority 1: Ticker-to-CIK Resolution~~ ✅ COMPLETE

**Status**: ✅ Implemented in sources/sec_ticker.py

**Implementation Complete**:
1. ✅ Uses SEC company tickers JSON: https://www.sec.gov/files/company_tickers.json
2. ✅ Caches ticker mapping data in .state/cache/ (7-day cache)
3. ✅ Implements resolve_ticker_to_cik(ticker: str) -> TickerCikResult
4. ✅ Returns structured result with CIK, company name, source URL, timestamps

**Benefit Realized**: Eddie can now filter Form 4 filings to specific issuer CIKs

### Priority 1B: Ticker-to-CUSIP Resolution (Still Needed)

**Implementation**:
1. Extend SEC ticker resolver or use additional data source
2. Map ticker → CUSIP for 13F filtering
3. Implement ticker_to_cusip(ticker: str) -> str | None

**Benefit**: Enables Maggie to filter 13F holdings to specific tickers

### Priority 2: Form 4 Transaction Detail Parsing

**Implementation**:
1. Fetch individual Form 4 XML documents using accession numbers
2. Parse XML to extract transaction table (derivativeTable and nonDerivativeTable)
3. Extract transaction type (P=purchase, S=sale, A=award, etc.)
4. Extract share count, price per share, total value
5. Identify reporting person role (CEO, CFO, Director, 10% Owner, etc.)
6. Filter to open-market purchases (code P) >= $100k by C-suite/directors

**Benefit**: Eddie can generate confidence-weighted ticker-specific insider-trading signals

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

This diagnostic report demonstrates the current insider-trading framework's structure and agent roles for ticker `MAIA`.

**Progress**: ✅ Ticker-to-CIK resolution is now implemented. MAIA resolves to CIK 0001878313 (MAIA Biotechnology, Inc.).

**Current Capability**: Eddie can now filter Form 4 filings to this specific issuer.

**Next Steps**:
1. ✅ COMPLETE: Ticker-to-CIK resolution (Priority 1)
2. Implement Form 4 transaction detail parsing (Priority 2)
3. Implement ticker-to-CUSIP resolution (Priority 1B)
4. Parse 13F holdings for ticker-specific analysis (Priority 3)

**Timeline Estimate**: Priority 2 (Form 4 detail parsing) could be implemented in 1 checkpoint, enabling confidence-weighted ticker-specific insider-trading signals.

---

**Report Generated**: 2026-06-05T17:04:34.539241+00:00

**Generated By**: scripts/ticker_drilldown.py

**Disclaimer**: This report is informational only and is not trading advice. All analysis is based on publicly available SEC filings and current project connector capabilities. No buy/sell/trade instructions are provided.