# CP24 Generic SEC Pipeline Archive

**Created:** 2026-06-12
**Checkpoints:** CP24A through CP24J
**Status:** Complete and Validated

---

## What CP24 Built

The CP24 series of checkpoints established a **generic, SEC-only extraction and synthesis pipeline** for U.S. public company insider trading and ownership research. This pipeline processes publicly available SEC EDGAR filings to generate structured research packets without relying on third-party data providers, paid services, or external financial databases.

**Key Capabilities:**
- Extract insider transactions from Form 4 filings (CP24C)
- Extract ownership disclosures from Form 144 and 13D/G filings (CP24D)
- Extract financial metrics from XBRL data (CP24E)
- Calculate capital structure and dilution estimates (CP24F)
- Integrate institutional ownership from 13F filings (CP24G)
- Synthesize multi-source evidence into unified research packets (CP24H)
- Validate across multiple tickers (CP24I)

---

## Module Overview

### CP24A: Architecture
- **Purpose:** Designed the overall pipeline architecture and data flow
- **Output:** Workflow documents, schema definitions, test plan
- **Status:** ✓ Complete

### CP24B: Ticker/CIK Submissions Inventory
- **Purpose:** Resolve ticker symbols to CIK identifiers and index SEC submissions
- **Input:** Ticker symbol (e.g., "MAIA", "NVDA")
- **Output:** CIK, company name, filing history metadata
- **CLI:** `python scripts/sec_ticker_inventory.py <TICKER>`

### CP24C: Form 4 Transaction Extraction
- **Purpose:** Parse Form 4 XML filings to extract insider transactions
- **Input:** CIK, date range
- **Output:** Structured transaction records (buys, sells, grants, exercises)
- **CLI:** `python scripts/form4_extractor.py <TICKER>`

### CP24D: Ownership Filings Extraction
- **Purpose:** Extract ownership disclosures from Form 144 and 13D/G filings
- **Input:** CIK, date range
- **Output:** Ownership filing metadata and key details
- **CLI:** `python scripts/ownership_filings_extractor.py <TICKER>`

### CP24E: XBRL Financial Extraction
- **Purpose:** Extract financial metrics from SEC companyfacts XBRL API
- **Input:** CIK
- **Output:** Balance sheet and cash flow metrics
- **CLI:** `python scripts/xbrl_financial_extractor.py <TICKER>`

### CP24F: Capital Structure and Dilution
- **Purpose:** Calculate common shares outstanding, dilutive securities, and fully diluted estimates
- **Input:** Form 4 data, XBRL data
- **Output:** Share counts, dilution percentages, estimates
- **CLI:** `python scripts/capital_structure_calculator.py <TICKER>`

### CP24G: 13F Institutional Ownership
- **Purpose:** Identify institutional holders from 13F filings
- **Input:** CIK, CUSIP
- **Output:** Institutional ownership records
- **CLI:** `python scripts/institutional_13f_extractor.py <TICKER>`

### CP24H: Generic SEC Synthesis Composer
- **Purpose:** Integrate CP24B-CP24G outputs into unified evidence-based research packet
- **Input:** All CP24B-CP24G module outputs for a ticker
- **Output:** JSON, Markdown, and CSV synthesis reports
- **CLI:** `python scripts/generic_sec_synthesis.py --ticker <TICKER>`

### CP24I: Multi-Ticker Validation
- **Purpose:** Validate synthesis pipeline across multiple tickers
- **Input:** Ticker list (e.g., "MAIA,NVDA,AAPL,MSFT,TSLA")
- **Output:** Per-ticker validation summaries, batch summary, validation matrix
- **CLI:** `python scripts/generic_sec_synthesis.py --tickers <TICKER1>,<TICKER2>,...`

### CP24J: Documentation and Archive Hardening
- **Purpose:** Create clean, auditable archive of CP24 outputs and documentation
- **Output:** This archive, manifests, checksums, usage guides

---

## Source Boundary: SEC-Only

**What CP24 Uses:**
- SEC EDGAR public filings (Forms 4, 144, 13D/G, 13F)
- SEC companyfacts XBRL API (financial metrics)
- SEC ticker-to-CIK mappings
- Publicly available submission histories

**What CP24 Does NOT Use:**
- Paid data providers (Bloomberg, FactSet, etc.)
- Third-party screeners or aggregators
- Social media or message boards
- Private spreadsheets or proprietary databases
- Live market data or real-time pricing
- Email or messaging alerts from external services

---

## Safety Boundary: Report-Only, No Alerts

**CP24 is report-only mode:**
- ✓ Generates JSON, Markdown, and CSV outputs to `docs/sample_reports/`
- ✓ Prints summary statistics to console
- ✓ Writes checkpoint reports to `docs/checkpoints/reports/`
- ✗ Does NOT send Telegram messages
- ✗ Does NOT send email
- ✗ Does NOT trigger alerts
- ✗ Does NOT modify scheduled tasks
- ✗ Does NOT connect to production alert pipelines
- ✗ Does NOT access .env secrets outside extraction scripts

**No Investment Advice:**
CP24 outputs are research tools only. They do NOT constitute financial advice, investment recommendations, or buy/sell/hold guidance. Users must perform their own due diligence and consult licensed financial professionals before making investment decisions.

---

## How to Run the Pipeline Manually

### Step 1: Ticker Inventory
```bash
python scripts/sec_ticker_inventory.py MAIA
```
**Output:** `docs/sample_reports/sec_inventory/MAIA/`

### Step 2: Form 4 Extraction
```bash
python scripts/form4_extractor.py MAIA
```
**Output:** `docs/sample_reports/form4_transactions/MAIA/`

### Step 3: Ownership Filings
```bash
python scripts/ownership_filings_extractor.py MAIA
```
**Output:** `docs/sample_reports/ownership_filings/MAIA/`

### Step 4: XBRL Financials
```bash
python scripts/xbrl_financial_extractor.py MAIA
```
**Output:** `docs/sample_reports/xbrl_financials/MAIA/`

### Step 5: Capital Structure
```bash
python scripts/capital_structure_calculator.py MAIA
```
**Output:** `docs/sample_reports/capital_structure/MAIA/`

### Step 6: 13F Institutional Ownership
```bash
python scripts/institutional_13f_extractor.py MAIA
```
**Output:** `docs/sample_reports/13f_institutional_ownership/MAIA/`

### Step 7: Generic Synthesis
```bash
python scripts/generic_sec_synthesis.py --ticker MAIA
```
**Output:** `docs/sample_reports/generic_synthesis/MAIA/`

### Step 8: Multi-Ticker Batch (Optional)
```bash
python scripts/generic_sec_synthesis.py --tickers MAIA,NVDA
```
**Output:** `docs/sample_reports/cp24i_validation/` (or custom output directory)

---

## Validation Statuses

### completed
Module ran successfully, outputs generated, data quality acceptable.

### degraded
Module ran but encountered warnings, missing fields, or partial data. Outputs still usable but flagged for review.

### failed
Module encountered critical errors and could not complete. No valid output generated.

### not_run_with_reason
Module was intentionally skipped (e.g., missing prerequisite data, out of scope for validation).

---

## Known Limitations

1. **AAPL/MSFT/TSLA Coverage:** In CP24I validation, AAPL, MSFT, and TSLA are represented as `not_run_with_reason` because full CP24B-CP24G extraction was deferred to avoid expanding the SEC collection scope during validation. These tickers can be processed by running CP24B-CP24G extraction first.

2. **13F Manager Universe:** CP24G institutional ownership extraction relies on a partial universe of 13F filers. Some institutional holders may not appear in results.

3. **SEC Data Lag:** SEC companyfacts XBRL API can lag behind actual filings by days or weeks. Some classifications may be missing or incomplete.

4. **No Live Market Data:** CP24 does not access real-time stock prices, volume, or market cap. All analysis is based on historical SEC filings.

5. **Evidence Row Threshold:** CP24H synthesis requires >= 12 evidence rows for complete validation. Tickers with sparse SEC activity may not meet this threshold.

6. **Framing Variations:** CP24 uses different framing for large-cap profitable companies vs. pre-revenue biotech. Users should review outputs for appropriateness.

7. **No Buy/Sell/Hold Language:** CP24 outputs deliberately avoid recommendation language. Users must make their own investment decisions.

---

## Next Recommended Checkpoint

After CP24J, the recommended next steps are:

**Option 1: CP25 - Production-Ready Manual Ticker SEC Synthesis Command**
- Create a single production-ready command for on-demand ticker synthesis
- Integrate CP24B-CP24H into a unified, idempotent workflow
- Add validation gates and safety checks

**Option 2: CP22E - Production Dual-Channel Pilot Monitoring**
- Monitor the next scheduled Ross alert run
- Verify dual-channel (Telegram + Email) pilot is working correctly
- Review alert content and timing

**Option 3: Manual Archive Review**
- Pause and review the CP24 archive manually
- Validate manifests, checksums, and documentation
- Plan integration with existing alert pipelines

---

## Archive Maintenance

**Manifest Files:**
- `MANIFEST.json` - Machine-readable artifact inventory
- `MANIFEST.md` - Human-readable artifact inventory
- `CHECKSUMS.sha256` - SHA-256 checksums for key files

**Status Reports:**
- `CP24_pipeline_status.md` - Checkpoint-by-checkpoint status
- `CP24_validation_summary.md` - Test results and validation metrics

**Usage Guides:**
- `CP24_safe_usage_guide.md` - Detailed CLI examples and safety rules
- `CP24_module_inventory.md` - Complete module and script inventory

---

## Safety Reminder

**Before running any CP24 script:**
1. Verify `.env` contains required API keys (if applicable)
2. Confirm report-only mode (no alerts)
3. Check output directories exist and are writable
4. Review degraded-mode handling in synthesis composer
5. Never commit `.env`, `.state`, databases, or private files

**No Buy/Sell/Hold Wording:**
CP24 outputs are strictly informational. Do not interpret them as investment advice, price targets, or recommendations.

---

## Contact

For questions, issues, or enhancement requests related to the CP24 pipeline, refer to:
- Checkpoint reports: `docs/checkpoints/reports/CP24*.md`
- Workflow docs: `docs/workflows/full_sec_extraction_*.md`
- Test files: `tests/test_*.py`

---

**This is not investment advice. Perform your own due diligence.**
