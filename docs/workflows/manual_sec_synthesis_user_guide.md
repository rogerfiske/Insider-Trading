# Manual SEC Synthesis User Guide

**Command:** `scripts/manual_sec_synthesis.py`
**Purpose:** Run manual ticker SEC-only research using the approved CP24 generic SEC pipeline
**Mode:** Report-only (no alerts, Telegram, email, or scheduled tasks)

---

## What This Command Does

The manual SEC synthesis command lets you run SEC-only research for one or more tickers using the approved CP24B-CP24H extraction and synthesis pipeline.

**Key features:**

- **Report-only mode:** Creates comprehensive research outputs without sending alerts or notifications
- **Three operating modes:** Choose between full pipeline, inventory-first, or synthesis-only
- **Structured outputs:** Every run creates a timestamped folder with manifests, summaries, validation matrices, and safety audits
- **Degraded-mode handling:** Gracefully handles missing data and creates explicit degraded-mode records
- **No external spreadsheets:** Uses only public SEC EDGAR data (no OpenInsider or private sources)

---

## Safety Boundaries

This command operates with strict safety controls:

**DOES NOT:**

- Send alerts
- Send Telegram messages
- Send email
- Modify Windows scheduled tasks
- Trigger Windows scheduled tasks
- Access or modify `.env` files
- Use Roger's uploaded MAIA spreadsheet
- Use OpenInsider data
- Require live market data
- Create buy/sell/hold recommendation language

**DOES:**

- Create local research reports
- Use public SEC EDGAR data only
- Generate safety audit files
- Track all module executions
- Handle degraded modes gracefully

---

## Recommended First Command

For your first run, use **synthesis-only mode** with MAIA to verify the command works correctly:

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker MAIA --mode synthesis-only
```

This mode:
- Uses existing local CP24B-CP24G outputs (no network required)
- Completes quickly (typically < 1 minute)
- Creates a clean run folder with all standard outputs
- Demonstrates the output structure

---

## Command Modes

### Synthesis-Only Mode (Default)

Compose synthesis from existing local module outputs. No network required.

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker MAIA --mode synthesis-only
```

**When to use:**
- First time trying the command
- When validating output structure
- When you have existing CP24B-CP24G outputs and want updated synthesis
- When working offline

**What it does:**
- Loads existing CP24B-CP24G JSON outputs from `docs/sample_reports/`
- Runs CP24H generic SEC synthesis composer
- Creates degraded synthesis if required inputs are missing

---

### Inventory-First Mode

Run only the lightweight SEC ticker inventory module. Safe for broad ticker lists.

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --tickers AAPL,MSFT,TSLA --mode inventory-first
```

**When to use:**
- Testing with new tickers you haven't processed before
- Checking if a ticker has sufficient SEC filing activity
- Quickly gathering CIK and submission counts for multiple tickers
- Avoiding rate limits on full extractions

**What it does:**
- Runs CP24B SEC ticker inventory module only
- Resolves ticker → CIK mapping
- Counts submissions by filing type
- Creates readiness summary without full extraction

**Typical runtime:** 5-15 seconds per ticker

---

### Full Mode

Run available CP24B-CP24H modules in sequence for comprehensive extraction.

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker MAIA --mode full
```

**When to use:**
- First-time extraction for a ticker
- When you need fresh data from SEC EDGAR
- When extending coverage to additional tickers

**What it runs (in order):**
1. CP24B: SEC ticker inventory
2. CP24C: Form 4 insider transactions
3. CP24D: Form 144 and 13D/G ownership filings (future)
4. CP24E: XBRL financials (future)
5. CP24F: Capital structure and dilution (future)
6. CP24G: 13F institutional ownership (future)
7. CP24H: Generic SEC synthesis

**Note:** Full mode currently implements inventory, Form 4, and synthesis. Additional modules (CP24D-CP24G) are available as separate scripts and will be integrated in future releases.

**Typical runtime:** 2-5 minutes per ticker (depends on SEC API response times)

---

## Single Ticker Examples

### Basic synthesis-only (default mode)

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker MAIA
```

### Inventory check for new ticker

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker AAPL --mode inventory-first
```

### Full extraction with custom lookback

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker MAIA --mode full --lookback-days 730
```

### Custom run name

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker NVDA --mode synthesis-only --run-name nvda_validation_20260612
```

---

## Multi-Ticker Examples

### Synthesis-only for MAIA and NVDA

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --tickers MAIA,NVDA --mode synthesis-only
```

### Inventory check for megacap tickers

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --tickers AAPL,MSFT,TSLA,GOOGL,AMZN --mode inventory-first
```

### Full extraction for small batch

```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --tickers MAIA,NVDA --mode full
```

---

## Command-Line Options

### Required (one of)

| Option | Description | Example |
|--------|-------------|---------|
| `--ticker` | Single ticker symbol | `--ticker MAIA` |
| `--tickers` | Comma-separated tickers | `--tickers MAIA,NVDA,AAPL` |

### Mode

| Option | Description | Default |
|--------|-------------|---------|
| `--mode` | Run mode: `full`, `inventory-first`, or `synthesis-only` | `synthesis-only` |

### Output

| Option | Description | Default |
|--------|-------------|---------|
| `--output-root` | Output root directory | `docs/sample_reports/manual_sec_synthesis_runs` |
| `--run-name` | Custom run name for folder | (auto-generated timestamp) |

### Module Parameters

| Option | Description | Default |
|--------|-------------|---------|
| `--lookback-days` | Form 4 lookback period in days | `1460` (4 years) |
| `--max-form4-filings` | Optional max Form 4 filings to process | (no limit) |
| `--skip-13f` | Skip 13F institutional ownership module | `false` |

### Execution

| Option | Description | Default |
|--------|-------------|---------|
| `--reuse-existing` | Reuse existing module outputs | `false` |
| `--no-network` | Offline mode (synthesis-only only) | `false` |
| `--fail-fast` | Stop on first module failure | `false` |

---

## How to Read Outputs

Each run creates a timestamped folder:

```
docs/sample_reports/manual_sec_synthesis_runs/
└── 20260612_143022_MAIA_NVDA/
    ├── run_manifest.json          # Complete run metadata
    ├── run_summary.json            # Structured results
    ├── run_summary.md              # Human-readable summary
    ├── validation_matrix.csv       # Per-ticker validation matrix
    ├── safety_audit.json           # Safety audit log
    ├── MAIA/
    │   ├── module_outputs/         # CP24B-CP24G outputs
    │   ├── synthesis/              # CP24H synthesis outputs
    │   │   ├── MAIA_generic_sec_synthesis.json
    │   │   ├── MAIA_generic_sec_synthesis.md
    │   │   └── MAIA_evidence_matrix.csv
    │   └── MAIA_manual_summary.json
    └── NVDA/
        └── ... (same structure)
```

### Key Files

**run_summary.md**
- Human-readable summary of the run
- Per-ticker completion status
- Degraded-mode notes
- Safety confirmations
- Disclaimer

**run_manifest.json**
- Complete run metadata
- File paths for all outputs
- Degraded/failed ticker lists
- Safety flags

**validation_matrix.csv**
- One row per ticker
- Module status columns
- Evidence row counts
- Posture summaries
- Degraded flags

**safety_audit.json**
- Timestamp and mode
- All safety confirmations
- No-alert/Telegram/email flags
- Notes

**<TICKER>_generic_sec_synthesis.json**
- Complete synthesis packet
- Evidence matrix with 12+ rows
- Scoring framework
- Insider/ownership/financial data
- Posture label

---

## Interpreting Degraded-Mode Results

Degraded mode means the synthesis was created with missing or incomplete inputs.

**Common degraded scenarios:**

1. **Missing SEC submissions:** Ticker has no Form 4 filings or limited activity
2. **XBRL gaps:** Pre-revenue companies may have incomplete financial data
3. **13F coverage:** Small-cap tickers may not appear in institutional 13F filings
4. **Extraction errors:** SEC API rate limits or network issues

**How to identify degraded mode:**

- `validation_matrix.csv`: Check `degraded` column
- `run_summary.md`: Look for "Degraded: Yes" per ticker
- `run_manifest.json`: Check `degraded_tickers` list
- Synthesis JSON: Check `degraded_mode.is_degraded` field

**What to do:**

- Review `degraded_reasons` to understand what's missing
- If it's a temporary SEC API issue, re-run in `full` mode
- If it's fundamental (no filings exist), accept the degraded synthesis
- For XBRL gaps, this is expected for pre-revenue companies

---

## How to Avoid Alerts

This command does NOT trigger alerts. It operates in strict report-only mode.

**Built-in safeguards:**

- No alert code paths in manual synthesis runner
- No Telegram/email modules loaded
- No scheduled task access
- Safety audit confirms all protections

**Verification:**

Every run creates `safety_audit.json` confirming:
- `no_alerts_confirmed: true`
- `no_telegram_confirmed: true`
- `no_email_confirmed: true`
- `scheduled_tasks_unchanged_or_not_touched: true`

---

## Known Limitations

### 1. Full Mode Module Coverage

Current full mode implements:
- ✓ CP24B: Ticker inventory
- ✓ CP24C: Form 4 transactions
- ✓ CP24H: Generic synthesis

Future integration:
- CP24D: Ownership filings (Form 144, 13D/G)
- CP24E: XBRL financials
- CP24F: Capital structure
- CP24G: 13F institutional ownership

**Workaround:** Run these modules separately using individual scripts (e.g., `scripts/sec_xbrl_financials.py`), then use `--mode synthesis-only` to compose synthesis.

### 2. SEC API Rate Limits

SEC EDGAR enforces a 10 requests/second limit. Large ticker batches in `full` or `inventory-first` mode may encounter rate limits.

**Workaround:** Process tickers in smaller batches (5-10 at a time).

### 3. No Live Market Data

This command uses only SEC filing data. It does not access:
- Real-time stock prices
- Trading volumes
- Market cap
- Analyst estimates

**Workaround:** Combine SEC synthesis outputs with external market data sources if needed for your analysis.

### 4. 13F Coverage Gaps

13F institutional ownership relies on a partial universe of 13F filers. Some institutional holders may not appear.

**Workaround:** Manually review 13F filings on SEC EDGAR for comprehensive coverage.

### 5. Evidence Row Threshold

Synthesis requires >= 12 evidence rows for complete validation. Tickers with sparse SEC activity may not meet this threshold.

**Workaround:** Accept degraded mode for low-activity tickers or manually supplement evidence.

---

## Troubleshooting

### Command not found

**Error:** `python: command not found` or `The system cannot find the path specified`

**Fix:** Use the virtual environment Python:
```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker MAIA
```

### Module not found errors

**Error:** `ModuleNotFoundError: No module named 'sources'`

**Fix:** Make sure you're running from the project root directory:
```powershell
cd c:\Users\Minis\CascadeProjects\Insider-Trading
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker MAIA
```

### No existing outputs for synthesis-only mode

**Error:** Synthesis fails with "Missing required inputs"

**Fix:** Run in `full` or `inventory-first` mode first to generate base data:
```powershell
.\.venv\Scripts\python.exe scripts/manual_sec_synthesis.py --ticker MAIA --mode full
```

### SEC API rate limit errors

**Error:** "429 Too Many Requests" or timeouts

**Fix 1:** Reduce batch size (process fewer tickers per run)
**Fix 2:** Add delays between runs
**Fix 3:** Use `inventory-first` mode instead of `full` for lightweight checks

### Synthesis degraded mode

**Issue:** `validation_matrix.csv` shows `degraded=true`

**Normal scenarios:**
- Pre-revenue companies (limited XBRL data)
- Small-cap tickers (no 13F matches)
- New tickers (limited filing history)

**Investigation:**
- Check `degraded_reasons` in `run_summary.md`
- Review individual module outputs in `<TICKER>/module_outputs/`
- Verify ticker has SEC filings on EDGAR

---

## Disclaimer

**This is not investment advice.**

The manual SEC synthesis command produces research outputs based solely on public SEC filings. These outputs:

- Do NOT constitute investment recommendations
- Do NOT include buy/sell/hold guidance
- Do NOT predict future stock performance
- Do NOT constitute financial advice

Perform your own due diligence and consult licensed financial professionals before making investment decisions.

---

## Support

For issues or questions:

1. Check this user guide
2. Review `docs/archives/cp24_generic_sec_pipeline/README.md`
3. Check checkpoint reports in `docs/checkpoints/reports/`
4. Review safety audit files in run outputs

---

**Version:** CP25
**Last Updated:** 2026-06-12
**Approved Pipeline:** CP24B-CP24H (SEC-only extraction and synthesis)

