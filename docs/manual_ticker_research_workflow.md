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

### Insider Evidence Scoring

**Added in CP21I** — The watchlist workflow now includes a transparent 0-100 point scoring system to rank tickers by insider buying evidence strength.

#### Scoring Components (7 Total)

Each ticker receives a total score (0-100 points) based on seven weighted components:

| Component | Max Points | Description |
|-----------|-----------|-------------|
| **Net Buying Value** | 25 pts | Purchase value minus sale value |
| **Buy/Sell Imbalance** | 20 pts | Rewards strong buying with little/no selling |
| **Buyer Breadth** | 15 pts | Number of distinct insider buyers |
| **Recency** | 15 pts | How recently insiders purchased |
| **Role Quality** | 10 pts | CEO/CFO/Director purchases weighted higher |
| **Persistence** | 10 pts | Purchases across multiple months |
| **Data Quality** | 5 pts | Form 4 parsing completeness |

#### Net Buying Value (0-25 pts)

| Net Value | Points |
|-----------|--------|
| > $1M | 25 pts |
| $500k - $1M | 20 pts |
| $100k - $500k | 15 pts |
| $25k - $100k | 10 pts |
| $1 - $25k | 5 pts |
| ≤ $0 | 0 pts |

#### Buy/Sell Imbalance (0-20 pts)

| Pattern | Points |
|---------|--------|
| Purchases with no sales | 20 pts |
| ≥ 5:1 purchase-to-sale ratio | 15 pts |
| Net buying but < 5:1 ratio | 10 pts |
| Sales ≥ purchases | 0 pts |

#### Buyer Breadth (0-15 pts)

| Distinct Buyers | Points |
|----------------|--------|
| 5+ | 15 pts |
| 3-4 | 12 pts |
| 2 | 8 pts |
| 1 | 5 pts |
| 0 | 0 pts |

#### Recency (0-15 pts)

| Latest Purchase | Points |
|----------------|--------|
| ≤ 30 days ago | 15 pts |
| 31-90 days ago | 12 pts |
| 91-180 days ago | 8 pts |
| 181-365 days ago | 5 pts |
| > 365 days ago | 0 pts |

#### Role Quality (0-10 pts)

| Buyer Role | Points |
|-----------|--------|
| CEO, CFO, President | 10 pts |
| Director, 10% Owner | 7 pts |
| Other insider | 3 pts |
| No role data | 0 pts |

#### Persistence (0-10 pts)

| Purchase Months | Points |
|----------------|--------|
| 3+ distinct months | 10 pts |
| 2 distinct months | 6 pts |
| 1 month | 3 pts |
| No purchases | 0 pts |

#### Data Quality (0-5 pts)

| Form 4 Parsing Rate | Points |
|--------------------|--------|
| ≥ 95% parsed | 5 pts |
| 80-94% parsed | 3 pts |
| 50-79% parsed | 1 pt |
| < 50% parsed | 0 pts |

#### Rating Labels

Total scores map to five rating tiers:

| Score Range | Rating Label |
|-------------|-------------|
| 80-100 | **Very Strong Insider Buying Evidence** |
| 60-79 | **Strong Insider Buying Evidence** |
| 40-59 | **Moderate Insider Buying Evidence** |
| 20-39 | **Weak Insider Buying Evidence** |
| 0-19 | **Little/No Insider Buying Evidence** |

#### Ranking Method

Tickers in the consolidated summary are ranked by:

1. **Primary**: Insider Evidence Score (0-100 points)
2. **Secondary**: Eddie Signal (BULLISH_EVIDENCE > NEUTRAL > BEARISH_EVIDENCE)
3. **Tertiary**: Net Purchase Value (higher ranks higher)

**Example Ranked Summary with Scoring**:

| Rank | Ticker | Company | Score | Rating | Eddie Signal | Purchase Value | Net Value | Buyers |
|------|--------|---------|-------|--------|--------------|----------------|-----------|--------|
| 1 | MAIA | MAIA Biotechnology, Inc. | 100.0 | Very Strong Insider | BULLISH_EVIDENCE | $4,921,438 | $4,921,438 | 10 |
| 2 | ABCD | Example Corp | 18.0 | Little/No Insider Buy | NEUTRAL | $0 | $0 | 0 |

#### Score Interpretation Guidelines

**Very Strong (80-100)**: Exceptional insider buying pattern
- Large net buying value (>$1M typical)
- Multiple high-level insiders (CEO/CFO/Directors)
- Recent purchases (within 30-90 days)
- Sustained buying over multiple months
- High data quality (>95% Form 4 parsing success)

**Strong (60-79)**: Compelling insider buying pattern
- Significant net buying value ($500k-$1M+)
- Several insider buyers, including executives
- Purchases within the last quarter
- Some buying persistence

**Moderate (40-59)**: Notable insider buying pattern
- Moderate net buying value ($100k-$500k)
- Some insider buying activity detected
- May lack recency, breadth, or persistence

**Weak (20-39)**: Limited insider buying pattern
- Small net buying value ($25k-$100k)
- Single buyer or sporadic activity
- Older purchases (6+ months ago)

**Little/No (0-19)**: Minimal or no insider buying
- Very low/zero net buying value
- No recent buying activity
- May have insider selling

#### Graceful Degradation

Scoring handles missing data gracefully:
- If a component's data is unavailable, it scores 0 for that component
- Warnings are included in the JSON output
- Partial scores are still computed from available components

**Example**: If only purchase/sale values are available (but no buyer details, dates, or months), the ticker can still score up to 45 points from:
- Net buying value: 0-25 pts
- Buy/sell imbalance: 0-20 pts
- Data quality: 0-5 pts (based on Form 4 parsing rate)

#### Form 4 Transaction Detail Integration

**Added in CP21I-Fix** — The scoring system now automatically populates transaction-level details from SEC Form 4 XML parsing.

**Populated Fields**:
- **Distinct Buyers/Sellers**: Count and names of unique reporting owners from filings with purchases/sales
- **Latest Purchase/Sale Date**: Most recent transaction date (YYYY-MM-DD format)
- **Buyer/Seller Roles**: Officer titles extracted from owner relationship fields (CEO, CFO, Director, etc.)
- **Purchase/Sale Months**: Distinct months (YYYY-MM format) when transactions occurred
- **Form 4 Filings Parsed**: Count of successfully parsed filings vs. total found

**Data Source**: All transaction details come from SEC EDGAR Form 4 XML filings via the project's `sec_form4_details.py` parser. Owner names, officer titles, transaction dates, and transaction codes are extracted directly from SEC submissions.

**Graceful Handling**: If Form 4 parsing fails or transaction details are unavailable, the affected components (buyer breadth, recency, role quality, persistence) gracefully degrade to 0 points while still computing scores from aggregate metrics (net buying value, buy/sell imbalance).

**Data Quality Component**: The data quality score (0-5 pts) now correctly uses the Form 4 parsing success rate (filings parsed / filings found) instead of defaulting to 0.

**Example Impact**: Before CP21I-Fix, a ticker like MAIA with 214 Form 4 filings parsed but no populated transaction details would score ~45/100. After CP21I-Fix, with all transaction details populated (10 distinct buyers, CEO/CFO/CSO/Director roles, 21 months of purchases, latest purchase 8 days ago), the same ticker scores 100/100.

**Important**: Scores are informational only and not investment advice. Insider transactions occur for many reasons unrelated to stock price expectations.

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

## Persistent Watchlist Tracking

The watchlist workflow supports persistent local history tracking, allowing you to build an audit trail of repeated small-cap/penny-stock research over time.

### Purpose

Track how insider buying activity evolves across multiple research runs:
- **Trend Detection**: See if insider purchases are increasing or decreasing
- **New Activity**: Identify when new Form 4 filings appear
- **Signal Changes**: Track changes in Eddie/Maggie signals over time
- **Historical Context**: Build a longitudinal view of research targets

### Database Location

History is stored in a local SQLite database:

```text
.state/watchlist_history.db
```

**Git Safety**: This database is **gitignored** and never committed. It stays local to your machine.

### Saving a Run

Add the `--save-history` flag to save the run to local history:

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_watchlist.py --tickers MAIA ABCD --save-history --dry-run-report
```

**Default Behavior**: History is **not saved** unless you explicitly add `--save-history`. This prevents accidental database growth.

### Comparing with Previous Runs

Add the `--compare-previous` flag to compute deltas against the most recent prior run for each ticker:

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_watchlist.py --tickers MAIA ABCD --save-history --compare-previous --dry-run-report
```

This generates a delta table showing:
- Purchase value change
- Purchase count change
- Sale value change
- Sale count change
- Signal changes
- Confidence changes

### Example: Repeated MAIA Research

**First Run** (establishes baseline):

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_watchlist.py --tickers MAIA --lookback-days 1460 --save-history --dry-run-report
```

Output:
```text
[ticker_watchlist] Run ID: 59e70e5d-3ad5-4509-ab38-e66b703d77bc
[ticker_watchlist]   MAIA: First run - no prior data
```

**Second Run** (compares to first):

```powershell
.\.venv\Scripts\python.exe .\scripts\ticker_watchlist.py --tickers MAIA --lookback-days 1460 --save-history --compare-previous --dry-run-report
```

Output:
```text
[ticker_watchlist] Run ID: 8a74a6e2-5462-426a-afcf-e2da8b0d8611
[ticker_watchlist]   MAIA: No purchase value change
```

If new insider purchases appeared between runs:
```text
[ticker_watchlist]   MAIA: +$50,000.00 purchases; Signal changed: NEUTRAL → BULLISH_EVIDENCE
```

### History Summary Report

When `--save-history` is used, a history summary is generated:

```text
docs/sample_reports/watchlist/manual_watchlist_history_summary.md
```

This report includes:
- Run ID and timestamp
- Current ranked results
- Delta comparison table (if `--compare-previous` was used)
- Safety confirmations

### What Deltas Mean

| Delta | Interpretation |
|-------|----------------|
| **Purchase value increased** | More insider buying detected in this run |
| **Purchase count increased** | More purchase transactions filed |
| **Sale value increased** | Insider selling detected (may indicate reduced confidence) |
| **Signal changed** | Eddie's assessment changed (e.g., NEUTRAL → BULLISH_EVIDENCE) |
| **Zero deltas** | No change since prior run (data stable) |

**Important**: Deltas show changes in **SEC filing data**, not stock price movements. Insider activity can increase while price drops, or vice versa.

### Resetting/Deleting Local History

To reset your research history:

1. **Delete the entire database**:
   ```powershell
   Remove-Item .state/watchlist_history.db
   ```

2. **Or use SQL to delete specific tickers** (advanced):
   ```powershell
   sqlite3 .state/watchlist_history.db
   DELETE FROM watchlist_ticker_results WHERE ticker = 'MAIA';
   DELETE FROM watchlist_ticker_deltas WHERE ticker = 'MAIA';
   ```

The database will be recreated automatically on the next `--save-history` run.

### Safety Boundaries

Persistent watchlist tracking maintains all safety constraints:

- ✅ **Local database only** — never synced or committed to Git
- ✅ **No alerts sent** — dry-run mode enforced
- ✅ **No production guard consumed** — Ross daily limit not affected
- ✅ **SEC data only** — no spreadsheets required
- ✅ **Informational only** — not trading advice

### CLI Options Summary

| Option | Default | Description |
|--------|---------|-------------|
| `--save-history` | Not enabled | Save this run to history database |
| `--no-save-history` | Default | Do not save history (explicit opt-out) |
| `--compare-previous` | Not enabled | Compare each ticker with most recent prior run |
| `--history-db PATH` | `.state/watchlist_history.db` | Custom database path |
| `--history-summary-output PATH` | `docs/sample_reports/watchlist/manual_watchlist_history_summary.md` | Custom history summary path |

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
