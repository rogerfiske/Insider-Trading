# CP24 Safe Usage Guide

**Archive:** cp24_generic_sec_pipeline v1.0.0
**Generated:** 2026-06-12

---

## Table of Contents

1. [Manual Command Examples](#manual-command-examples)
2. [Recommended Sequence for New Ticker](#recommended-sequence-for-new-ticker)
3. [Report-Only Validation Mode](#report-only-validation-mode)
4. [How to Avoid Alerts](#how-to-avoid-alerts)
5. [Environment and Secret Safety](#environment-and-secret-safety)
6. [Degraded Output Handling](#degraded-output-handling)
7. [No Buy/Sell/Hold Wording Policy](#no-buysellhold-wording-policy)
8. [Large-Cap vs Small-Cap Framing](#large-cap-vs-small-cap-framing)
9. [Extending from MAIA/NVDA to Other Tickers](#extending-from-maianvda-to-other-tickers)

---

## Manual Command Examples

### CP24B: Ticker/CIK Inventory

```bash
# Extract ticker/CIK mapping and submissions inventory
python scripts/sec_ticker_inventory.py MAIA
```

**Output:** `docs/sample_reports/sec_inventory/MAIA/`

**What it does:**
- Resolves ticker symbol to CIK identifier
- Downloads SEC submissions metadata
- Creates JSON and Markdown reports

---

### CP24C: Form 4 Transaction Extraction

```bash
# Extract insider transactions from Form 4 filings
python scripts/form4_extractor.py MAIA
```

**Output:** `docs/sample_reports/form4_transactions/MAIA/`

**What it does:**
- Parses Form 4 XML filings
- Extracts buys, sells, grants, exercises
- Generates transaction summary reports

---

### CP24D: Ownership Filings Extraction

```bash
# Extract ownership disclosure filings (Form 144, 13D/G)
python scripts/ownership_filings_extractor.py MAIA
```

**Output:** `docs/sample_reports/ownership_filings/MAIA/`

**What it does:**
- Identifies Form 144 and 13D/G filings
- Extracts ownership disclosure metadata
- Creates ownership filing reports

---

### CP24E: XBRL Financial Extraction

```bash
# Extract financial metrics from SEC companyfacts API
python scripts/xbrl_financial_extractor.py MAIA
```

**Output:** `docs/sample_reports/xbrl_financials/MAIA/`

**What it does:**
- Fetches XBRL data from SEC companyfacts API
- Extracts balance sheet and cash flow metrics
- Generates financial metrics reports

---

### CP24F: Capital Structure Calculation

```bash
# Calculate capital structure and dilution estimates
python scripts/capital_structure_calculator.py MAIA
```

**Output:** `docs/sample_reports/capital_structure/MAIA/`

**What it does:**
- Combines Form 4 and XBRL data
- Calculates common shares outstanding
- Estimates fully diluted share count
- Computes dilution percentages

---

### CP24G: 13F Institutional Ownership

```bash
# Extract institutional ownership from 13F filings
python scripts/institutional_13f_extractor.py MAIA
```

**Output:** `docs/sample_reports/13f_institutional_ownership/MAIA/`

**What it does:**
- Identifies 13F filers holding the ticker
- Extracts institutional ownership records
- Generates 13F holder reports

---

### CP24H: Generic SEC Synthesis

```bash
# Synthesize all CP24B-CP24G outputs into unified research packet
python scripts/generic_sec_synthesis.py --ticker MAIA

# Or for multiple tickers (batch mode)
python scripts/generic_sec_synthesis.py --tickers MAIA,NVDA
```

**Output:** `docs/sample_reports/generic_synthesis/MAIA/`

**What it does:**
- Loads all CP24B-CP24G module outputs
- Builds evidence matrix (>= 12 rows required)
- Computes synthesis scores
- Generates JSON, Markdown, and CSV reports

---

## Recommended Sequence for New Ticker

To process a new ticker (e.g., "AAPL"), run CP24B-CP24H in order:

```bash
# Step 1: Ticker/CIK inventory
python scripts/sec_ticker_inventory.py AAPL

# Step 2: Form 4 extraction
python scripts/form4_extractor.py AAPL

# Step 3: Ownership filings
python scripts/ownership_filings_extractor.py AAPL

# Step 4: XBRL financials
python scripts/xbrl_financial_extractor.py AAPL

# Step 5: Capital structure
python scripts/capital_structure_calculator.py AAPL

# Step 6: 13F institutional ownership
python scripts/institutional_13f_extractor.py AAPL

# Step 7: Generic synthesis
python scripts/generic_sec_synthesis.py --ticker AAPL
```

**Important:**
- Each step depends on the previous step's outputs
- If a step fails, fix the issue before proceeding
- Check for degraded mode flags in synthesis output

---

## Report-Only Validation Mode

All CP24 scripts are **report-only by default**. They:

- ✓ Write outputs to `docs/sample_reports/`
- ✓ Print summary statistics to console
- ✗ Do NOT send Telegram messages
- ✗ Do NOT send email
- ✗ Do NOT trigger alerts
- ✗ Do NOT modify scheduled tasks

**To verify report-only mode:**
1. Check that scripts do not import `telegram`, `smtplib`, or alert modules
2. Review safety flags in synthesis JSON output
3. Confirm no scheduled tasks are triggered

---

## How to Avoid Alerts

**Critical Rules:**

1. **Never modify `.env` settings** that control alert channels
2. **Never import alert modules** in CP24 scripts
3. **Never call alert functions** from synthesis scripts
4. **Use `--report-only` flag** if available in future script versions
5. **Review safety flags** in synthesis JSON output before sharing

**Safety Checks:**

```json
"safety": {
  "report_only": true,
  "alerts_generated": false,
  "telegram_sent": false,
  "email_sent": false,
  "scheduled_tasks_modified": false
}
```

If any of these flags are `false` (except `report_only`), **STOP** and review the code.

---

## Environment and Secret Safety

**Required `.env` Variables:**

(None required for CP24 SEC-only extraction - SEC APIs are public)

**Optional `.env` Variables:**

- `SEC_API_IO_API_KEY` (if using sec-api.io for enhanced SEC access)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (for alerts - NOT USED in CP24)
- `SMTP_*` (for email alerts - NOT USED in CP24)

**Safety Rules:**

1. **Never commit `.env`** to version control
2. **Never print `.env` contents** to console or logs
3. **Never expose secrets** in checkpoint reports or documentation
4. **Verify `.env` is gitignored:**

```bash
git check-ignore -v .env
# Expected output: .gitignore:2:.env	.env
```

5. **Scan for secrets before commit:**

```bash
# Search staged files for common secret patterns
git diff --cached --name-only | xargs grep -i -E "api.key|secret|password|token|credential"
```

---

## Degraded Output Handling

**Degraded Mode** indicates that a module ran but encountered warnings, missing fields, or partial data.

**Degraded Status in Synthesis Output:**

```json
"module_status": {
  "sec_inventory": "success",
  "form4_transactions": "success",
  "xbrl_financials": "ok",  // "ok" indicates some limitations
  "capital_structure": "degraded",  // "degraded" indicates warnings
  "institutional_13f": "success"
}
```

**Handling Degraded Outputs:**

1. **Review the module's JSON output** for `warnings` or `notes` fields
2. **Check for missing fields** or `null` values in key metrics
3. **Determine if degraded data is acceptable** for your use case
4. **Consider re-running the module** or manually reviewing SEC filings
5. **Document degraded status** in validation summaries

**Example: XBRL "ok" vs "degraded":**
- `"ok"`: Some XBRL metrics missing (common for pre-revenue companies)
- `"degraded"`: XBRL API unavailable or data quality issues

---

## No Buy/Sell/Hold Wording Policy

**Prohibited Language:**

- ✗ "Buy", "Sell", "Hold"
- ✗ "Strong buy", "Weak sell"
- ✗ "Outperform", "Underperform"
- ✗ "Accumulate", "Distribute"
- ✗ "Price target: $X"
- ✗ "Fair value: $X"
- ✗ "Recommended allocation: X%"

**Allowed Language:**

- ✓ "Strong insider-evidence profile"
- ✓ "High uncertainty profile"
- ✓ "Large operating company profile"
- ✓ "Institutional visibility"
- ✓ "Evidence of insider buying"
- ✓ "Evidence of insider selling"

**Rationale:**

CP24 outputs are **research tools**, not investment advice. Recommendation language creates legal risk and misrepresents the purpose of the pipeline.

**Enforcement:**

- Automated tests scan for recommendation language
- Manual review of all synthesis outputs
- Checkpoint reports verify compliance

---

## Large-Cap vs Small-Cap Framing

**Framing Logic:**

CP24 synthesis uses different framing for large-cap profitable companies vs. pre-revenue small-cap companies.

**Large-Cap/Profitable (e.g., NVDA):**
- "Large operating company / institutional visibility profile"
- Focus on insider activity patterns relative to company scale
- Emphasis on institutional ownership and liquidity

**Small-Cap/Pre-Revenue (e.g., MAIA):**
- "Strong insider-evidence / high uncertainty profile"
- Focus on clinical/regulatory milestones and cash runway
- Emphasis on dilution risk and insider buying confidence

**Framing Determination:**

1. **Check XBRL financials:** Presence of revenue, profitability
2. **Check market cap:** Typically large-cap if > $10B
3. **Check insider activity:** High insider buying may indicate small-cap

**Manual Override:**

If framing is incorrect, review `sources/generic_synthesis_composer.py` logic and adjust as needed.

---

## Extending from MAIA/NVDA to Other Tickers

**Current Coverage:**

- **MAIA:** Complete CP24B-CP24H extraction + validation
- **NVDA:** Complete CP24B-CP24H extraction + validation
- **AAPL/MSFT/TSLA:** Documented in CP24I as `not_run_with_reason`

**To Extend to AAPL:**

1. Run CP24B-CP24G extraction for AAPL (see [Recommended Sequence](#recommended-sequence-for-new-ticker))
2. Run CP24H synthesis for AAPL
3. Re-run CP24I validation with AAPL included:

```bash
python scripts/generic_sec_synthesis.py --tickers MAIA,NVDA,AAPL
```

4. Update validation matrix and batch summary
5. Verify MAIA leakage check still passes
6. Run full test suite

**To Extend to Other Tickers:**

Follow the same process as AAPL. Key considerations:

- **International companies with ADRs:** May have different filing patterns
- **Pre-revenue biotech:** May have limited XBRL coverage
- **Recently IPO'd companies:** May have sparse filing history
- **Low-volume tickers:** May have sparse 13F coverage

---

## Troubleshooting

### "Module Not Found" Error

**Cause:** Python virtual environment not activated or dependencies not installed

**Solution:**
```bash
# Activate virtual environment
.\.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

---

### "Ticker Not Found" Error

**Cause:** Ticker symbol not recognized by SEC or typo in ticker

**Solution:**
1. Verify ticker symbol is correct
2. Check SEC EDGAR for ticker: https://www.sec.gov/cgi-bin/browse-edgar?company=&CIK={TICKER}&type=&dateb=&owner=exclude&count=40
3. Try CIK directly instead of ticker

---

### "Evidence Row Count < 12" Warning

**Cause:** Synthesis requires >= 12 evidence rows; ticker has sparse SEC activity

**Solution:**
1. Review individual module outputs for missing data
2. Check if ticker is pre-revenue (limited XBRL coverage)
3. Manually review SEC filings for additional evidence
4. Accept degraded mode if data is sufficient for analysis

---

### "XBRL API Unavailable" Error

**Cause:** SEC companyfacts API is down or rate-limited

**Solution:**
1. Wait 5-10 minutes and retry
2. Check SEC EDGAR status page
3. Use cached XBRL data if available
4. Manually download companyfacts JSON from SEC website

---

## Safety Checklist Before Running

Before running any CP24 script:

- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file exists (if using sec-api.io) OR not required for public SEC APIs
- [ ] Report-only mode confirmed (no alert modules imported)
- [ ] Output directory exists and is writable
- [ ] No active scheduled tasks that might interfere
- [ ] Sufficient disk space for SEC cache files

---

## Contact and Support

For questions, issues, or enhancement requests:

- **Checkpoint Reports:** `docs/checkpoints/reports/CP24*.md`
- **Workflow Docs:** `docs/workflows/full_sec_extraction_*.md`
- **Test Files:** `tests/test_*.py`
- **Archive Manifest:** `docs/archives/cp24_generic_sec_pipeline/MANIFEST.md`

---

**This is not investment advice. Perform your own due diligence.**
