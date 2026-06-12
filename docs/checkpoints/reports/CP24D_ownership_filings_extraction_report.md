# CP24D - Form 144 and Schedule 13D/G Extraction

**Checkpoint:** CP24D
**Date:** 2026-06-12
**Status:** COMPLETED
**Commit:** (pending)

---

## Overview

Successfully implemented generic Form 144 and Schedule 13D/G ownership filing extraction for arbitrary tickers. This checkpoint enables extraction of sale-intent notices (Form 144) and beneficial ownership filings (13D/G) as part of the full SEC extraction architecture (CP24A).

---

## Files Created

### Source Modules

1. **sources/sec_form144.py** (427 lines)
   - Parses Form 144 (Notice of Proposed Sale)
   - Extracts seller information, securities details, proposed sale date
   - Explicitly marks sale_status as "proposed" (NOT actual sale)
   - Preserves parse failures with error provenance

2. **sources/sec_13dg.py** (574 lines)
   - Parses Schedule 13D (active ownership) and 13G (passive ownership)
   - Extracts filer, beneficial owner, ownership percent, shares owned
   - Extracts voting/dispositive power details
   - Distinguishes active vs passive, original vs amendment
   - Preserves parse failures with error provenance

### Scripts

3. **scripts/sec_ownership_filings.py** (577 lines)
   - CLI tool for ownership filings extraction
   - Supports single ticker and batch mode
   - Generates JSON, Markdown, and CSV outputs
   - Integrates with CP24B submissions inventory

### Tests

4. **tests/test_sec_form144_13dg.py** (15 tests)
   - Form 144 parsing (minimal, missing fields, fetch failure)
   - Schedule 13D/G parsing (13D, 13G, amendments)
   - Aggregation and summary generation
   - Safety constraints (no investment language, no secrets)
   - Batch summary schema validation

---

## Implementation Details

### Form 144 Parser

**Key Features:**
- Parses text-based Form 144 documents
- Extracts seller name, relationship, securities to be sold
- Marks all Form 144 as sale_status="proposed" (notice of intent, NOT actual sale)
- Handles missing optional fields gracefully
- Preserves parse failures for debugging

**Sample Output (MAIA):**
- Total Form 144 filings: 1
- Filing date: 2024-01-19
- Parse status: Partial (ticker and seller extracted, some fields missing)

### Schedule 13D/G Parser

**Key Features:**
- Distinguishes 13D (active) vs 13G (passive) based on form type
- Detects amendments (/A suffix)
- Extracts filer identity, ownership percent, share counts
- Extracts voting/dispositive power (sole, shared)
- Purpose of transaction (13D only)

**Sample Output (MAIA):**
- Total 13D/G filings: 11
  - Active 13D: 5
  - Passive 13G: 6
  - Amendments: 3
- Distinct filers: 5
- Filing date range: 2022-08-10 to 2026-05-15

### CLI Tool

**Usage:**
```powershell
# Single ticker
.venv/Scripts/python.exe -m scripts.sec_ownership_filings --ticker MAIA --output-dir docs/sample_reports/ownership_filings/MAIA

# Multiple tickers (batch mode)
.venv/Scripts/python.exe -m scripts.sec_ownership_filings --tickers MAIA,NVDA --output-dir docs/sample_reports/ownership_filings/batch

# Custom lookback
.venv/Scripts/python.exe -m scripts.sec_ownership_filings --ticker NVDA --lookback-days 730 --output-dir docs/sample_reports/ownership_filings/NVDA
```

**Output Files (per ticker):**
- `{TICKER}_ownership_filings.json` (combined JSON)
- `{TICKER}_ownership_filings.md` (Markdown report)
- `{TICKER}_form144_filings.csv` (Form 144 CSV)
- `{TICKER}_13dg_filings.csv` (13D/G CSV)

**Batch Mode Outputs:**
- `batch_ownership_filings_summary.json`
- `batch_ownership_filings_summary.md`

---

## Validation Results

### MAIA (CP24B Reconciliation)

**CP24B Inventory Counts:**
- Form 144: 1
- SC 13D: 3
- SC 13G: 3
- SCHEDULE 13G: 2
- SCHEDULE 13D/A: 1
- SCHEDULE 13G/A: 1
- SC 13D/A: 1
- **Total 13D/G**: 11

**CP24D Extraction Results:**
- Form 144: 1 ✓ (matches CP24B)
- 13D/G filings: 11 ✓ (matches CP24B)
  - Active 13D: 5
  - Passive 13G: 6
  - Amendments: 3

**Reconciliation:** PERFECT MATCH ✓

The extraction correctly identified all 1 Form 144 and all 11 13D/G filings from the CP24B inventory. The breakdown into active (13D) vs passive (13G) and original vs amendment classifications is accurate.

### NVDA Validation

**Extraction Results:**
- Form 144 filings: 241
- 13D/G filings: 14
  - Active 13D: 0
  - Passive 13G: 14
  - Amendments: 9
- Date range: 2023-01-31 to 2026-06-03

**Observations:**
- NVDA has significantly more Form 144 filings than MAIA (241 vs 1)
- All NVDA ownership filings are passive 13G (institutional investors)
- No active 13D filings (no activist investors attempting board control)
- High amendment count (9/14 = 64%) indicates frequent updates from large holders

**No investment language present** ✓

---

## Sample Reports Generated

### Single Ticker Reports

1. **docs/sample_reports/ownership_filings/MAIA/**
   - MAIA_ownership_filings.json
   - MAIA_ownership_filings.md
   - MAIA_form144_filings.csv
   - MAIA_13dg_filings.csv

2. **docs/sample_reports/ownership_filings/NVDA/**
   - NVDA_ownership_filings.json
   - NVDA_ownership_filings.md
   - NVDA_form144_filings.csv
   - NVDA_13dg_filings.csv

### Batch Summary

3. **docs/sample_reports/ownership_filings/batch_maia_nvda/**
   - batch_ownership_filings_summary.json
   - batch_ownership_filings_summary.md
   - MAIA/ (per-ticker outputs)
   - NVDA/ (per-ticker outputs)

---

## Test Results

**All 15 tests passing:**

```
tests/test_sec_form144_13dg.py::TestForm144Parsing::test_parse_minimal_form144_fixture PASSED
tests/test_sec_form144_13dg.py::TestForm144Parsing::test_parse_form144_missing_fields PASSED
tests/test_sec_form144_13dg.py::TestForm144Parsing::test_parse_form144_fetch_failure PASSED
tests/test_sec_form144_13dg.py::TestForm144Parsing::test_form144_not_actual_sale PASSED
tests/test_sec_form144_13dg.py::TestSchedule13DGParsing::test_parse_minimal_13d_fixture PASSED
tests/test_sec_form144_13dg.py::TestSchedule13DGParsing::test_parse_minimal_13g_fixture PASSED
tests/test_sec_form144_13dg.py::TestSchedule13DGParsing::test_distinguish_13d_vs_13g PASSED
tests/test_sec_form144_13dg.py::TestSchedule13DGParsing::test_distinguish_original_vs_amendment PASSED
tests/test_sec_form144_13dg.py::TestAggregation::test_form144_summary PASSED
tests/test_sec_form144_13dg.py::TestAggregation::test_ownership_summary PASSED
tests/test_sec_form144_13dg.py::TestSafetyConstraints::test_no_buy_sell_hold_language PASSED
tests/test_sec_form144_13dg.py::TestSafetyConstraints::test_safety_flags_present PASSED
tests/test_sec_form144_13dg.py::TestSafetyConstraints::test_no_secrets_in_outputs PASSED
tests/test_sec_form144_13dg.py::TestBatchSummary::test_batch_summary_schema PASSED
tests/test_sec_form144_13dg.py::TestMAIAValidation::test_maia_inventory_reconciliation PASSED

============================= 15 passed in 0.08s ==============================
```

---

## Safety Constraints Verified

**All safety constraints met:**

✓ Read-only SEC access (no writes)
✓ No alert generation
✓ No Telegram/email
✓ No scheduled task modification
✓ No .env changes
✓ No secrets in outputs
✓ No buy/sell/hold language
✓ No OpenInsider data required
✓ report_only=true, alert_enabled=false in all outputs

---

## Key Findings

### Form 144 Distinction

**CRITICAL:** Form 144 is a NOTICE of PROPOSED SALE, not an actual sale.

- All Form 144 filings have sale_status="proposed"
- Actual sales are reported in Form 4 with transaction code "S"
- Form 144 indicates INTENT to sell restricted securities within 90 days
- Does NOT confirm the sale actually occurred

### Ownership Classifications

**Schedule 13D (Active):**
- Beneficial ownership >5% with intent to influence control
- Requires disclosure of purpose (e.g., "Increase board representation")
- Often filed by activist investors

**Schedule 13G (Passive):**
- Beneficial ownership >5% without intent to influence
- Typically filed by institutional investors (mutual funds, ETFs)
- Simpler disclosure requirements

**Amendments:**
- /A suffix indicates amendment to previous filing
- Common for ownership percent changes
- NVDA has 64% amendment rate (frequent updates from large holders)

---

## Integration with CP24B

The ownership extraction correctly leverages CP24B submissions inventory:

1. Loads existing inventory if available (avoids redundant API calls)
2. Falls back to creating new inventory if not found
3. Extracts Form 144 and 13D/G filings from recent submissions
4. Filters by lookback window (default 1460 days = 4 years)

**Benefits:**
- Consistent CIK resolution across checkpoints
- Reuses cached submissions data
- Maintains audit trail (source URLs preserved)

---

## Next Steps (CP24E)

**CP24E - Generic 10-Q/10-K XBRL Financial Extraction:**
- Extract financial statements from 10-Q and 10-K filings
- Parse XBRL instance documents for key financial facts
- Extract cash, assets, liabilities, revenue, etc.
- Handle missing tags gracefully

**CP24E will complete the financial data layer needed for CP24H synthesis.**

---

## Acceptance Criteria

**All acceptance criteria met:**

✓ Fetches Form 144 and 13D/G filings within lookback window
✓ Parses Form 144 text documents correctly
✓ Parses Schedule 13D/G text documents correctly
✓ Distinguishes 13D (active) vs 13G (passive)
✓ Distinguishes original vs amendment filings
✓ Extracts required fields (filer, ownership, shares)
✓ Handles missing optional fields gracefully
✓ Preserves parse failures with error provenance
✓ Generates JSON/Markdown/CSV outputs
✓ Batch mode for multiple tickers
✓ No buy/sell/hold language in outputs
✓ No secrets in outputs
✓ Safety flags correct (report_only=true, alert_enabled=false)
✓ MAIA baseline reconciled with CP24B (1 Form 144, 11 13D/G)
✓ NVDA extraction successful (241 Form 144, 14 13D/G)
✓ 15/15 tests pass
✓ Python compilation successful

---

## Status

**CP24D: COMPLETED**

Form 144 and Schedule 13D/G extraction implemented, tested, and validated. Ready to proceed to CP24E (XBRL financial extraction).
