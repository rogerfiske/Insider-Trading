# Full SEC Extraction Implementation Plan

**Version:** 1.0
**Created:** 2026-06-11
**Checkpoint:** CP24A
**Parent Architecture:** [full_sec_extraction_architecture.md](full_sec_extraction_architecture.md)

---

## Overview

This document breaks down the full SEC extraction architecture into **9 implementation checkpoints** (CP24B through CP24J).

Each checkpoint is:
- **Focused**: Single phase or small group of related phases
- **Testable**: Has clear acceptance criteria
- **Safe**: Maintains no-alert/no-recommendation policy
- **Incremental**: Builds on previous checkpoints

**Total estimated checkpoints:** 9
**Estimated duration:** 9-12 development sessions

---

## CP24B — Generic Ticker/CIK Resolver and SEC Submissions Inventory ✓ COMPLETED

**Status:** ✓ Completed (2026-06-11)

### Goal

Implement ticker/CIK resolution and SEC submissions inventory for arbitrary tickers.

### Inputs

- User-provided ticker symbol (string)
- Lookback window in days (default: 1460 = 4 years)
- Max recent filings (default: 100)

### Outputs

- TickerCikResult (ok, ticker, cik, cik_padded, company_name)
- Comprehensive submissions inventory with:
  - Filing counts by form
  - Latest filings for key forms (10-K, 10-Q, 8-K, Form 4, Form 144, 13D/13G, 13F-HR)
  - Recent filings list (up to max_recent)
  - Coverage flags (has_form4, has_form144, has_10q, has_10k, etc.)
  - Downstream readiness assessment
- JSON output: `{ticker}_sec_inventory.json`
- Markdown report: `{ticker}_sec_inventory.md`
- Batch summary for multiple tickers

### Files Created/Modified

**Created:**

- scripts/sec_ticker_inventory.py (CLI tool)
- tests/test_sec_ticker_inventory.py (21 tests)
- docs/sample_reports/sec_inventory/MAIA/ (sample reports)
- docs/sample_reports/sec_inventory/NVDA/ (sample reports)
- docs/sample_reports/sec_inventory/batch_maia_nvda/ (batch sample)

**Modified:**

- sources/sec_submissions.py (added build_submissions_inventory())

**Reused:**

- sources/sec_ticker.py (resolve_ticker_to_cik, TickerCikResult)
- sources/sec_submissions.py (fetch_company_submissions)
- sources/sec_common.py (sec_fetch, utcnow_iso)

### CLI Usage

```powershell
# Single ticker inventory
.\.venv\Scripts\python.exe scripts\sec_ticker_inventory.py --ticker MAIA --output-dir docs/sample_reports/sec_inventory/MAIA

# Multiple tickers (batch mode)
.\.venv\Scripts\python.exe scripts\sec_ticker_inventory.py --tickers MAIA,NVDA --output-dir docs/sample_reports/sec_inventory/batch

# Custom parameters
.\.venv\Scripts\python.exe scripts\sec_ticker_inventory.py --ticker AAPL --output-dir docs/sample_reports/sec_inventory/AAPL --max-recent-filings 200
```

### Safety Constraints

- Read-only SEC access (no writes)
- No alert generation
- No Telegram/email
- No scheduled task modification
- Output JSON/Markdown only (no automated actions)
- User-Agent compliance
- No OpenInsider data required

### Acceptance Criteria

- ✓ Resolves MAIA to CIK 0001878313
- ✓ Resolves NVDA to CIK 0001045810
- ✓ Handles unknown tickers gracefully (error_type=ticker_not_found)
- ✓ Fetches submissions for resolved CIK
- ✓ Builds filing counts by form type
- ✓ Identifies latest filings for key forms (10-K, 10-Q, 8-K, Form 4, Form 144, 13D/13G, 13F-HR)
- ✓ Generates coverage flags for downstream checkpoints
- ✓ Assesses downstream readiness (form4_ready, xbrl_financials_ready, etc.)
- ✓ Handles degraded mode (no filings, unresolved ticker)
- ✓ Generates JSON/Markdown outputs with safety flags
- ✓ Batch mode for multiple tickers
- ✓ No buy/sell/hold language
- ✓ No secrets in outputs
- ✓ 21/21 tests pass
- ✓ Python compilation successful

---

## CP24C — Generic Form 4 Extraction and Insider Transaction Normalization ✓ COMPLETED

**Status:** ✓ Completed (2026-06-11)

### Goal

Extract and normalize Form 4 insider transactions for arbitrary tickers.

### Inputs

- Ticker (from CP24B)
- CIK and company name (from CP24B)
- All Form 4 filings from SEC submissions API (not limited by inventory cap)

### Outputs

- List[CanonicalTransaction] (normalized transaction records)
- Aggregated insider statistics (purchase count, sale count, net value, distinct buyers/sellers)
- JSON output: `{ticker}_form4_transactions.json`
- CSV output: `{ticker}_form4_transactions.csv`
- Markdown report: `{ticker}_form4_transactions.md`
- Batch summary for multiple tickers

### Files Created/Modified

**Created:**

- sources/form4_aggregator.py (transaction normalization and aggregation)
- scripts/sec_form4_transactions.py (CLI tool)
- tests/test_sec_form4_transactions.py (22 tests)
- docs/sample_reports/form4_transactions/MAIA/ (sample reports)
- docs/sample_reports/form4_transactions/NVDA/ (sample reports)
- docs/sample_reports/form4_transactions/batch_maia_nvda/ (batch sample)

**Reused:**

- sources/sec_form4_details.py (Form 4 XML parsing)
- sources/sec_submissions.py (fetch_company_submissions)

### CLI Usage

```powershell
# Single ticker extraction
.\.venv\Scripts\python.exe -m scripts.sec_form4_transactions --ticker MAIA --output-dir docs/sample_reports/form4_transactions/MAIA

# Multiple tickers (batch mode)
.\.venv\Scripts\python.exe -m scripts.sec_form4_transactions --tickers MAIA,NVDA --output-dir docs/sample_reports/form4_transactions/batch

# Custom lookback period
.\.venv\Scripts\python.exe -m scripts.sec_form4_transactions --ticker NVDA --lookback-days 730 --output-dir docs/sample_reports/form4_transactions/NVDA
```

### Safety Constraints

- Read-only SEC access (no writes)
- No alert generation
- No Telegram/email
- No scheduled task modification
- Output JSON/Markdown/CSV only
- User-Agent compliance
- Parse failures logged but don't halt extraction
- Partial success acceptable

### Acceptance Criteria

- ✓ Fetches ALL Form 4 filings within lookback window (not limited by inventory cap)
- ✓ Parses Form 4 XML (handles embedded XML, standalone XML)
- ✓ Classifies transactions correctly (P/S vs A/M/F/G/J)
- ✓ Aggregates open-market purchases/sales only (excludes grants/exercises)
- ✓ Calculates distinct buyers/sellers
- ✓ Handles parse failures gracefully (parse_status=failed)
- ✓ Generates JSON/Markdown/CSV outputs with safety flags
- ✓ Batch mode for multiple tickers
- ✓ No buy/sell/hold language
- ✓ No secrets in outputs
- ✓ 22/22 tests pass
- ✓ Python compilation successful
- ✓ MAIA baseline reconciled (141 purchases vs 134 baseline, explainable variance)
- ✓ NVDA extraction successful (392 filings, 1 purchase, 1501 sales)

---

## CP24D — Generic Form 144 and 13D/G Extraction ✓ COMPLETED

**Status:** ✓ Completed (2026-06-12)

### Goal

Extract Form 144 (notice of proposed sale) and Schedule 13D/G (beneficial ownership) filings.

### Inputs

- Ticker (from CP24B)
- CIK and company name (from CP24B)
- All Form 144 and 13D/G filings from SEC submissions API

### Outputs

- List[Form144Filing] (seller, securities, proposed sale date, sale_status="proposed")
- List[Ownership13DG] (filer, ownership percent, shares owned, active/passive classification)
- JSON output: `{ticker}_ownership_filings.json`
- Markdown report: `{ticker}_ownership_filings.md`
- CSV outputs: `{ticker}_form144_filings.csv`, `{ticker}_13dg_filings.csv`
- Batch summary for multiple tickers

### Files Created/Modified

**Created:**

- sources/sec_form144.py (Form 144 parser, 427 lines)
- sources/sec_13dg.py (13D/G parser, 574 lines)
- scripts/sec_ownership_filings.py (CLI tool, 577 lines)
- tests/test_sec_form144_13dg.py (15 tests)
- docs/sample_reports/ownership_filings/MAIA/ (sample reports)
- docs/sample_reports/ownership_filings/NVDA/ (sample reports)
- docs/sample_reports/ownership_filings/batch_maia_nvda/ (batch sample)
- docs/checkpoints/reports/CP24D_ownership_filings_extraction_report.md

**Reused:**

- sources/sec_submissions.py (fetch_company_submissions)
- sources/sec_ticker.py (resolve_ticker_to_cik)
- sources/sec_common.py (sec_fetch, utcnow_iso)

### CLI Usage

```powershell
# Single ticker extraction
.venv/Scripts/python.exe -m scripts.sec_ownership_filings --ticker MAIA --output-dir docs/sample_reports/ownership_filings/MAIA

# Multiple tickers (batch mode)
.venv/Scripts/python.exe -m scripts.sec_ownership_filings --tickers MAIA,NVDA --output-dir docs/sample_reports/ownership_filings/batch

# Custom lookback period
.venv/Scripts/python.exe -m scripts.sec_ownership_filings --ticker NVDA --lookback-days 730 --output-dir docs/sample_reports/ownership_filings/NVDA
```

### Safety Constraints

- Read-only SEC access (no writes)
- No alert generation
- No Telegram/email
- No scheduled task modification
- Output JSON/Markdown/CSV only
- User-Agent compliance
- Parse failures logged but don't halt extraction
- Partial success acceptable

### Acceptance Criteria

- ✓ Fetches Form 144 and 13D/G filings within lookback window
- ✓ Parses Form 144 text documents (sale_status="proposed")
- ✓ Parses Schedule 13D/G text documents
- ✓ Distinguishes 13D (active) vs 13G (passive)
- ✓ Distinguishes original vs amendment filings
- ✓ Extracts required fields (filer, ownership, shares)
- ✓ Handles missing optional fields gracefully
- ✓ Preserves parse failures with error provenance
- ✓ Generates JSON/Markdown/CSV outputs with safety flags
- ✓ Batch mode for multiple tickers
- ✓ No buy/sell/hold language
- ✓ No secrets in outputs
- ✓ 15/15 tests pass
- ✓ Python compilation successful
- ✓ MAIA baseline reconciled with CP24B (1 Form 144, 11 13D/G)
- ✓ NVDA extraction successful (241 Form 144, 14 13D/G)

---

## CP24E — Generic 10-Q/10-K XBRL Financial Extraction

### Goal

Extract financial statements from 10-Q and 10-K XBRL filings.

### Inputs

- Ticker
- List[SecSubmissionFiling] for 10-Q, 10-K

### Outputs

- XBRLFinancials (cash, assets, liabilities, revenue, etc.)
- JSON output: `{ticker}_xbrl_financials.json`

### Files Likely Changed

**New:**
- sources/sec_xbrl_financials.py (XBRL parser)
- scripts/ticker_xbrl_extractor.py (CLI tool)
- tests/test_sec_xbrl_financials.py

### Implementation Steps

1. Create XBRL parser:
   - Fetch XBRL instance document (.xml from FilingSummary.xml)
   - Parse XML namespaces (us-gaap, dei)
   - Extract financial facts:
     - us-gaap:CashAndCashEquivalentsAtCarryingValue
     - us-gaap:Assets
     - us-gaap:Liabilities
     - us-gaap:WorkingCapital (or calculate: current assets - current liabilities)
     - us-gaap:Revenues
     - us-gaap:NetCashProvidedByUsedInOperatingActivities
     - us-gaap:ResearchAndDevelopmentExpense
   - Handle context IDs (report period vs instant)

2. Create CLI tool for XBRL extraction

3. Add tests:
   - XBRL tag extraction
   - Context ID filtering (most recent period)
   - Missing tag handling (set to None)

### Validation Commands

```powershell
# Extract NVDA financials
python scripts/ticker_xbrl_extractor.py --ticker NVDA --input-dir docs/sample_reports/generic_ticker/NVDA/submissions --output-dir docs/sample_reports/generic_ticker/NVDA
```

### Safety Constraints

- Read-only access
- Parse failures → None values
- No financial analysis (just extraction)

### Acceptance Criteria

- ✓ Fetches latest 10-Q or 10-K
- ✓ Parses XBRL instance document
- ✓ Extracts key financial facts
- ✓ Handles missing tags (set to None)
- ✓ Returns report period date
- ✓ 12/12 tests pass

---

## CP24F — Generic Capital Structure/Dilution Extraction

### Goal

Extract capital structure and calculate dilution metrics.

### Inputs

- Ticker
- Latest 10-Q/10-K XBRL (from CP24E)
- Latest DEF 14A proxy (if available)

### Outputs

- CapitalStructure (shares_outstanding, options, warrants, dilution_percent)
- JSON output: `{ticker}_capital_structure.json`

### Files Likely Changed

**New:**
- sources/sec_capital_structure.py (capital structure extractor)
- scripts/ticker_capital_structure_extractor.py (CLI tool)
- tests/test_sec_capital_structure.py

### Implementation Steps

1. Create capital structure extractor:
   - Extract from 10-Q/10-K XBRL:
     - us-gaap:CommonStockSharesOutstanding
     - us-gaap:ShareBasedCompensationArrangementByShareBasedPaymentAwardOptionsOutstandingNumber
   - Extract from notes/tables:
     - Warrants outstanding
     - Convertible securities
   - Calculate:
     - Approximate fully diluted shares = common + options + warrants + convertibles
     - Dilution overhang = (fully_diluted - common) / fully_diluted * 100

2. Create CLI tool

3. Add tests

### Validation Commands

```powershell
# Extract NVDA capital structure
python scripts/ticker_capital_structure_extractor.py --ticker NVDA --input-dir docs/sample_reports/generic_ticker/NVDA --output-dir docs/sample_reports/generic_ticker/NVDA
```

### Safety Constraints

- Read-only access
- Graceful failure if data unavailable

### Acceptance Criteria

- ✓ Extracts shares outstanding
- ✓ Extracts stock options outstanding
- ✓ Calculates dilution overhang
- ✓ Handles missing data (set to None)
- ✓ 8/8 tests pass

---

## CP24G — Integrate 13F InfoTable Matching into Generic Ticker Workflow

### Goal

Integrate existing 13F InfoTable matching into the generic ticker workflow.

### Inputs

- Ticker (from CP24B)
- CIK and company name (from CP24B)
- Holdings from institutional managers (from sec_13f.py)

### Outputs

- List[HoldingMatchResult] (matched holdings with confidence)
- JSON output: `{ticker}_ownership_13f.json`

### Files Likely Changed

**Existing (Reuse):**
- sources/sec_13f.py (already implemented)
- sources/sec_13f_parser.py (already implemented)
- sources/sec_13f_matcher.py (already implemented)

**New/Modified:**
- scripts/ticker_13f_matcher.py (new CLI tool)
- tests/test_ticker_13f_matching.py (integration tests)

### Implementation Steps

1. Create CLI tool `scripts/ticker_13f_matcher.py`:
   - Load ticker/CIK from CP24B output
   - Fetch latest 13F-HR filings for default managers
   - Parse InfoTable XML/HTML
   - Match ticker to holdings
   - Save to JSON

2. Add integration tests:
   - End-to-end matching for known tickers (AAPL, MSFT)
   - CUSIP exact match
   - Issuer name match
   - No matches scenario

### Validation Commands

```powershell
# Match NVDA to 13F holdings
python scripts/ticker_13f_matcher.py --ticker NVDA --input-dir docs/sample_reports/generic_ticker/NVDA --output-dir docs/sample_reports/generic_ticker/NVDA
```

### Safety Constraints

- Read-only access
- No alerts
- Manager list configurable (not hardcoded)

### Acceptance Criteria

- ✓ Fetches 13F-HR filings for managers
- ✓ Parses InfoTable (XML/HTML fallback)
- ✓ Matches ticker to holdings
- ✓ Returns confidence levels
- ✓ Handles no matches gracefully
- ✓ 10/10 tests pass

---

## CP24H — Compose Full Generic SEC-Only Synthesis Packet

### Goal

Replace validation-mode placeholders with live SEC extraction data.

### Inputs

- All extraction outputs from CP24B-G

### Outputs

- Complete synthesis packet (JSON + Markdown)
- `{ticker}_synthesis_packet.json`
- `{ticker}_synthesis_packet.md`

### Files Likely Changed

**Modified:**
- scripts/ticker_synthesis_workflow.py (replace extract_sec_data placeholder)

**New:**
- sources/synthesis_composer.py (aggregation logic)
- tests/test_synthesis_composer.py

### Implementation Steps

1. Create `sources/synthesis_composer.py`:
   - compose_synthesis_packet() → Merge all module outputs
   - calculate_synthesis_scores() → Compute scores from extracted data
   - generate_evidence_matrix() → Build evidence table

2. Update `ticker_synthesis_workflow.py`:
   - Replace extract_sec_data() placeholder with live extraction:
     ```python
     def extract_sec_data(ticker: str, cik: str) -> dict:
         # Load all extraction outputs
         submissions = load_submissions_inventory(ticker)
         form4 = load_form4_data(ticker)
         form144 = load_form144_data(ticker)
         ownership_13dg = load_13dg_data(ticker)
         ownership_13f = load_13f_data(ticker)
         financials = load_xbrl_data(ticker)
         capital = load_capital_structure(ticker)

         # Compose synthesis
         return compose_synthesis_packet(
             ticker=ticker,
             cik=cik,
             insider=form4,
             ownership_13dg=ownership_13dg,
             ownership_13f=ownership_13f,
             financials=financials,
             capital=capital
         )
     ```

3. Add tests:
   - Full synthesis composition
   - Score calculations
   - Evidence matrix generation
   - Partial data handling

### Validation Commands

```powershell
# Generate full NVDA synthesis (live mode)
python scripts/ticker_synthesis_workflow.py --ticker NVDA --mode live --output-dir docs/sample_reports/generic_ticker/NVDA
```

### Safety Constraints

- No alerts
- No recommendations
- Descriptive analysis only

### Acceptance Criteria

- ✓ Composes synthesis from all extraction modules
- ✓ Calculates synthesis scores correctly
- ✓ Generates evidence matrix
- ✓ Handles partial data (some modules failed)
- ✓ No recommendation language
- ✓ Safety flags correct
- ✓ 20/20 tests pass

---

## CP24I — Multi-Ticker Validation Batch

### Goal

Validate full extraction pipeline on 5-10 diverse tickers.

### Inputs

- List of validation tickers (suggested):
  - AAPL (large cap, tech)
  - MSFT (large cap, tech)
  - NVDA (large cap, semiconductors)
  - MAIA (small cap, biotech, pre-revenue) - regression baseline
  - REGN (mid cap, biotech, revenue-positive)
  - JPM (large cap, financial services)
  - XOM (large cap, energy)

### Outputs

- Synthesis packets for all validation tickers
- Validation report comparing results
- Regression test confirmation (MAIA baseline preserved)

### Files Likely Changed

**New:**
- scripts/ticker_batch_validator.py (batch processing tool)
- tests/test_multi_ticker_validation.py (regression tests)
- docs/checkpoints/reports/CP24I_multi_ticker_validation_report.md

### Implementation Steps

1. Create batch validator:
   - Accept list of tickers
   - Run full extraction pipeline for each
   - Generate synthesis packets
   - Compare to expected baselines (MAIA)

2. Add regression tests:
   - MAIA Form 4 count matches baseline (134 purchases)
   - NVDA clinical module is not_applicable
   - All tickers have no recommendation language
   - All tickers have correct safety flags

### Validation Commands

```powershell
# Run batch validation
python scripts/ticker_batch_validator.py --tickers AAPL,MSFT,NVDA,MAIA,REGN,JPM,XOM --output-dir docs/sample_reports/generic_ticker/batch_validation
```

### Safety Constraints

- No alerts
- Batch processing read-only
- No automated actions

### Acceptance Criteria

- ✓ All validation tickers complete successfully
- ✓ MAIA regression baseline preserved
- ✓ NVDA clinical module not_applicable
- ✓ No recommendation language in any output
- ✓ Safety flags correct for all tickers
- ✓ 30/30 regression tests pass

---

## CP24J — Documentation/Archive Hardening

### Goal

Complete documentation, update archive packaging, finalize test coverage.

### Inputs

- All extraction outputs from CP24B-I

### Outputs

- Updated documentation
- Enhanced archive manifests
- Test coverage report
- Final checkpoint report

### Files Likely Changed

**Modified:**
- docs/workflows/generic_ticker_synthesis_workflow.md (add live extraction docs)
- scripts/ticker_archive_packet.py (enhance manifest metadata)

**New:**
- docs/workflows/sec_extraction_troubleshooting.md
- docs/workflows/sec_extraction_best_practices.md

### Implementation Steps

1. Update documentation:
   - Add live extraction examples to generic_ticker_synthesis_workflow.md
   - Create troubleshooting guide for common SEC extraction errors
   - Create best practices guide (caching, rate limiting, error handling)

2. Enhance archive packaging:
   - Add extraction_mode field to manifest
   - Add data_completeness_score
   - Add extraction_timestamp per module

3. Test coverage audit:
   - Run coverage report
   - Ensure 80%+ coverage for all SEC modules
   - Add missing tests

### Validation Commands

```powershell
# Generate coverage report
pytest --cov=sources --cov=scripts --cov-report=html

# Open coverage report
start htmlcov/index.html
```

### Safety Constraints

- Documentation updates only
- No code changes to extraction logic

### Acceptance Criteria

- ✓ Documentation updated for live extraction
- ✓ Troubleshooting guide created
- ✓ Archive manifest enhanced
- ✓ Test coverage ≥ 80%
- ✓ All documentation reviewed

---

## Summary

### Checkpoint Sequence

1. **CP24B** - Ticker/CIK resolver + submissions inventory (foundation)
2. **CP24C** - Form 4 extraction (insider trading)
3. **CP24D** - Form 144 + 13D/G extraction (ownership)
4. **CP24E** - XBRL financial extraction (10-Q/10-K)
5. **CP24F** - Capital structure extraction
6. **CP24G** - 13F InfoTable integration
7. **CP24H** - Full synthesis composition (replace validation mode)
8. **CP24I** - Multi-ticker validation batch
9. **CP24J** - Documentation hardening

### Estimated Effort

| Checkpoint | Complexity | Estimated Duration |
|------------|------------|-------------------|
| CP24B | Low | 1 session (reuse existing) |
| CP24C | Medium | 1-2 sessions |
| CP24D | Medium | 1-2 sessions (2 parsers) |
| CP24E | High | 2 sessions (XBRL complexity) |
| CP24F | Medium | 1 session |
| CP24G | Low | 1 session (reuse existing) |
| CP24H | Medium | 1-2 sessions |
| CP24I | Low | 1 session |
| CP24J | Low | 1 session |
| **Total** | | **9-12 sessions** |

### Dependencies

```
CP24B (foundation)
  ├── CP24C (Form 4)
  ├── CP24D (Form 144, 13D/G)
  ├── CP24E (XBRL)
  │    └── CP24F (Capital structure)
  └── CP24G (13F integration)
       └── CP24H (Full synthesis)
            └── CP24I (Validation)
                 └── CP24J (Documentation)
```

### Risk Mitigation

1. **XBRL complexity**: Start with simple tags, add advanced features later
2. **Rate limiting**: Use conservative caching, respect SEC limits
3. **Parse failures**: Graceful degradation at every phase
4. **Test coverage**: Write tests before implementation (TDD)
5. **Regression**: Preserve MAIA baseline throughout

### Success Criteria

- All 9 checkpoints complete
- 108+ tests passing (current) + ~100 new tests
- MAIA and NVDA regression baselines preserved
- No alert generation
- No recommendation language
- Full documentation
- Test coverage ≥ 80%

---

**Ready for PM approval to proceed with CP24B (Ticker/CIK resolver and submissions inventory).**
