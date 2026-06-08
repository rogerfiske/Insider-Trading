# Manual Ticker Research Workflow

**Last Updated**: 2026-06-08
**Status**: Active

---

## Overview

The Insider-Trading project supports three complementary workflows for analyzing insider trading activity:

1. **Daily Discovery Workflow**: Scheduled agents run automatically and discover whatever they find from their configured universe
2. **Single Manual Ticker Research Workflow**: On-demand, deeper ticker-specific SEC-backed reports with extended lookback windows
3. **Manual Ticker Watchlist Workflow**: Batch processing of multiple tickers with consolidated ranking and summary

This document describes the manual ticker research workflows (single ticker and watchlist modes).

---

## Daily Discovery vs Manual Research

### Daily Discovery Workflow

- **Trigger**: Scheduled Windows tasks (morning/afternoon runs)
- **Scope**: All Form 4 filings filed in the last 24 hours
- **Output**: Telegram alerts for significant insider activity (email disabled by default)
- **Agents**: All seven agents run in production mode
- **Guard**: Ross enforces daily alert limit
- **Purpose**: Real-time monitoring of insider trading across the market

### Single Manual Ticker Research Workflow

- **Trigger**: User runs `scripts/ticker_drilldown.py` with specific ticker
- **Scope**: Configurable lookback window (default 365 days, max 1460 days / 4 years)
- **Output**: Markdown diagnostic report saved to file
- **Agents**: All seven agents run in dry-run mode
- **Guard**: No production guard consumed; no alerts sent
- **Purpose**: Deep historical analysis of specific ticker for research or validation

### Manual Ticker Watchlist Workflow

- **Trigger**: User runs `scripts/ticker_watchlist.py` with multiple tickers
- **Scope**: Configurable lookback window (default 1460 days for watchlist mode)
- **Output**: Per-ticker reports, consolidated summary, and JSON output
- **Agents**: All seven agents run in dry-run mode (via ticker drilldown engine)
- **Guard**: No production guard consumed; no alerts sent
- **Purpose**: Batch analysis and ranking of multiple tickers by insider buying evidence

---

## Running a Manual Ticker Report

### Basic Command

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_drilldown.py --ticker MAIA --dry-run-report
```

This generates a report using the default 365-day lookback window and saves it to:
```
docs/sample_reports/MAIA_manual_ticker_drilldown_report.md
```

### Specifying a Custom Lookback Window

Use the `--lookback-days` option to configure the Form 4 filing lookback period:

```powershell
# 30-day lookback (recent activity only)
.\.venv\Scripts\python.exe .\scripts\ticker_drilldown.py --ticker MAIA --lookback-days 30 --dry-run-report

# 180-day lookback (6 months)
.\.venv\Scripts\python.exe .\scripts\ticker_drilldown.py --ticker MAIA --lookback-days 180 --dry-run-report

# 365-day lookback (1 year, default)
.\.venv\Scripts\python.exe .\scripts\ticker_drilldown.py --ticker MAIA --lookback-days 365 --dry-run-report

# 1460-day lookback (4 years, maximum)
.\.venv\Scripts\python.exe .\scripts\ticker_drilldown.py --ticker MAIA --lookback-days 1460 --dry-run-report
```

### Specifying a Custom Output Path

Use the `--output` option to save the report to a different location:

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_drilldown.py --ticker MAIA --lookback-days 1460 --dry-run-report --output reports/MAIA_4year_report.md
```

---

## Running a Manual Ticker Watchlist

### Purpose

The watchlist workflow allows you to process multiple tickers in a single run and generate:
1. Individual per-ticker reports (same format as single ticker mode)
2. Consolidated summary with ranking by insider buying evidence
3. Machine-readable JSON output for further analysis

### Basic Watchlist Command (Command-Line Tickers)

Process multiple tickers directly from the command line:

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_watchlist.py --tickers MAIA ABCD XYZ --dry-run-report
```

This generates:
- Per-ticker reports: `docs/sample_reports/watchlist/MAIA_manual_ticker_report.md`, etc.
- Consolidated summary: `docs/sample_reports/watchlist/manual_watchlist_summary.md`
- JSON output: `docs/sample_reports/watchlist/manual_watchlist_results.json`

### Watchlist Command (File-Based Tickers)

Process tickers from a file (one ticker per line, # for comments):

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_watchlist.py --tickers-file config/watchlists/manual_tickers.example.txt --dry-run-report
```

Example watchlist file format:

```text
# My research watchlist
# One ticker per line
MAIA
ABCD
XYZ
```

**Note**: User-created watchlist files in `config/watchlists/` (except `*.example.txt`) are automatically gitignored to keep private research private.

### Watchlist with Custom Lookback Window

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_watchlist.py --tickers MAIA ABCD --lookback-days 1460 --dry-run-report
```

Default for watchlist mode is 1460 days (4 years) to provide comprehensive historical analysis for small-cap/penny-stock research.

### Output Files Explained

| File | Description |
|------|-------------|
| `docs/sample_reports/watchlist/{TICKER}_manual_ticker_report.md` | Individual ticker report (same format as single ticker mode) |
| `docs/sample_reports/watchlist/manual_watchlist_summary.md` | Consolidated summary with ranked tickers and insider buying evidence |
| `docs/sample_reports/watchlist/manual_watchlist_results.json` | Machine-readable JSON with all ticker metrics for further analysis |

### Ranking Method

Tickers in the consolidated summary are ranked by insider buying evidence strength:

1. **Eddie Signal**: BULLISH_EVIDENCE > NEUTRAL > BEARISH_EVIDENCE
2. **Net Purchase Value**: Higher insider buying value ranks higher
3. **Purchase Count**: More purchase transactions rank higher
4. **Data Completeness**: More Form 4 filings parsed ranks higher

**Example Ranked Summary**:

| Rank | Ticker | Company | Eddie Signal | Confidence | Purchases | Purchase Value | Net Value |
|------|--------|---------|--------------|------------|-----------|----------------|-----------|
| 1 | MAIA | MAIA Biotechnology, Inc. | BULLISH_EVIDENCE | 2 | 134 | $4,921,437.58 | $4,921,437.58 |
| 2 | ABCD | Example Corp | NEUTRAL | 1 | 0 | $0.00 | $0.00 |

### Single Ticker vs Watchlist Mode

| Feature | Single Ticker | Watchlist |
|---------|---------------|-----------|
| **Command** | `ticker_drilldown.py` | `ticker_watchlist.py` |
| **Input** | One ticker | Multiple tickers |
| **Default Lookback** | 365 days | 1460 days |
| **Per-Ticker Report** | ✅ | ✅ |
| **Consolidated Summary** | ❌ | ✅ |
| **JSON Output** | ❌ | ✅ |
| **Ranking** | ❌ | ✅ |
| **Use Case** | Deep-dive on specific ticker | Compare multiple small-cap tickers |

### Safety Boundaries

Both single ticker and watchlist modes enforce strict safety boundaries:

- ✅ **No Telegram messages sent** (dry-run mode enforced)
- ✅ **No email sent** (dry-run mode enforced)
- ✅ **No uploaded spreadsheets used** (SEC EDGAR only)
- ✅ **No private data committed** (private watchlist files gitignored)
- ✅ **Not trading advice** (informational only)

---

## Recommended Lookback Windows

| Use Case | Lookback Days | Rationale |
|----------|---------------|-----------|
| **Recent activity check** | 30-90 days | Quick scan for recent insider moves |
| **Quarterly trend** | 180 days | Capture last two reporting quarters |
| **Annual pattern** | 365 days | Full year of insider activity (default) |
| **Long-term pattern** | 730 days (2 years) | Multi-year trend analysis |
| **Historical deep-dive** | 1460 days (4 years) | Maximum available lookback for comprehensive analysis |

**Why 1460 days?**
- SEC Form 4 filings are available indefinitely, but extended lookbacks trade performance for completeness
- 1460 days (4 years) approximates the maximum practical lookback for pattern analysis:
  - Captures multiple market cycles
  - Includes sufficient data for executive stock option vesting schedules (typically 4 years)
  - Balances API load against data utility

---

## Why Not Use OpenInsider or Private Spreadsheets?

**Security and Data Integrity**:
- This project relies exclusively on SEC EDGAR data
- Manual spreadsheets and third-party aggregators are not version-controlled
- Spreadsheet data cannot be reliably cached or reproduced
- SEC data is the authoritative source and legally filed

**Claude Code Best Practices**:
- Do not commit private spreadsheets to the repository
- Do not upload sensitive portfolio data to Claude Code sessions
- Do not give Claude Code access to Roger's private research files

The manual ticker workflow is specifically designed to generate SEC-backed reports that can be cross-checked against private data **outside** the Claude Code session, maintaining a clean separation between authoritative public data and private research.

---

## Expected Agent Behavior

When running a manual ticker report, each agent behaves as follows:

### Eddie — SEC Form 4 Insider Transactions

- **Behavior**: Fetches all Form 4 filings within the specified lookback window
- **Filtering**: Filters to the ticker's CIK (requires successful ticker-to-CIK resolution)
- **Parsing**: Parses Form 4 XML to extract transaction details (type, shares, price, value)
- **Output**: Transaction summary with purchases, sales, options, grants
- **Status**: `APPLICABLE_NO_RECENT_FILINGS` if no filings found in window

### Maggie — SEC 13F Institutional Holdings

- **Behavior**: Fetches latest 13F-HR filings for configured institutional managers
- **Matching**: Matches holdings to ticker by issuer name (CUSIP not available from ticker resolution)
- **Output**: Holdings summary grouped by manager
- **Status**: `APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING` (issuer-name matching used)
- **Limitation**: Historical 13F trend comparison not yet implemented (static holdings only)

### Frank — Federal Reserve / Macro Context

- **Behavior**: Provides market-wide macro context
- **Output**: Not ticker-specific
- **Status**: `PARTIALLY_APPLICABLE`

### Maya — On-Chain / Whale Movement

- **Behavior**: Analyzes cryptocurrency and blockchain data
- **Output**: N/A for traditional equities
- **Status**: `NOT_APPLICABLE` (MAIA is a stock, not crypto)

### Janet — Portfolio Drift

- **Behavior**: Analyzes positions in Roger's configured portfolio
- **Output**: N/A if ticker not in portfolio
- **Status**: `NOT_APPLICABLE` if ticker not tracked

### Sophie — Consensus Aggregator

- **Behavior**: Aggregates signals from other agents
- **Output**: Consensus signal if upstream agents produce signals
- **Status**: `APPLICABLE_TO_AGENT_OUTPUTS`

### Ross — Routing / Reporting

- **Behavior**: Would route consensus signals to Telegram/email in production
- **Output**: Dry-run mode active; no alerts sent
- **Status**: `DRY_RUN_ONLY`

---

## Current Limitations

### Form 4 Lookback Limitation

The `--lookback-days` parameter controls the **filing date window** used to query SEC EDGAR. The current implementation:
- ✅ Filters Form 4 filings by filing date within the lookback window
- ✅ Parses transaction details from Form 4 XML
- ❌ Does not filter by transaction date vs filing date (all transactions in a filing are included, even if transaction occurred before the lookback window)

For most use cases, this is acceptable because Form 4 filings must be filed within 2 business days of the transaction, so filing date closely approximates transaction date.

### 13F Lookback Limitation

The current implementation:
- ✅ Fetches and parses 13F-HR information tables for configured managers
- ✅ Matches holdings to ticker by issuer name
- ❌ Does not support configurable 13F lookback (always fetches latest filings)
- ❌ Does not support historical 13F trend comparison (static holdings only, no QoQ/YoY change detection)

### CUSIP Availability

- CUSIP identifiers are not available from SEC `company_tickers.json` ticker-to-CIK resolution
- Maggie uses conservative issuer-name matching as an alternative
- CUSIP-based matching would be more reliable for 13F analysis but requires additional data source

---

## Safety and Compliance

### No Alerts Sent

Manual ticker research mode runs in `--dry-run-report` mode:
- ✅ No Telegram messages sent
- ✅ No email alerts sent
- ✅ Ross daily alert guard not consumed
- ✅ Scheduled tasks not modified or triggered

### Not Trading Advice

All manual ticker reports include the following disclaimer:

> **Safety Disclaimer**: This report is informational only and is not trading advice. No buy/sell/trade instructions are provided.

Insider trading analysis is provided for research purposes only. All investment decisions should be made with professional financial advice.

---

## Example: MAIA 4-Year Deep-Dive

To generate a comprehensive 4-year historical analysis for MAIA:

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_drilldown.py --ticker MAIA --lookback-days 1460 --dry-run-report --output docs/sample_reports/MAIA_4year_report.md
```

**Expected Output**:
- Ticker: MAIA
- CIK: 0001878313 (MAIA Biotechnology, Inc.)
- Lookback window: 1460 days
- Form 4 filings: All filings from the last 4 years
- Transactions: Detailed purchase/sale/grant/option summary
- Insiders: Top reporting owners with transaction counts
- 13F holdings: Current institutional holdings (if available)

The resulting report can be manually cross-checked against Roger's private OpenInsider spreadsheet **outside** Claude Code to validate SEC data accuracy and completeness.

---

## Next Steps

Potential enhancements for the manual ticker research workflow:

1. **Historical 13F Trend Comparison**: Track QoQ/YoY changes in institutional holdings
2. **Transaction Date Filtering**: Filter Form 4 transactions by transaction date (not just filing date)
3. **CUSIP Resolution**: Add ticker-to-CUSIP mapping for more reliable 13F matching
4. **Insider Sentiment Scoring**: Weighted scoring based on reporting owner role, transaction size, and timing
5. **CSV Export**: Export watchlist data in CSV format for spreadsheet analysis
6. **Watchlist Persistence**: Track watchlist results over time for trend analysis

---

**For Questions or Issues**:
- See checkpoint reports in `docs/checkpoints/reports/`
- Check sample reports in `docs/sample_reports/`
- Review test coverage in `tests/test_ticker_drilldown*.py` and `tests/test_ticker_watchlist*.py`

**Last Checkpoint**: CP21G — Manual Ticker Watchlist / Small-Cap Workflow
