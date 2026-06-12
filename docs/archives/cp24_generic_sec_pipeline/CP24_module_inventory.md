# CP24 Module Inventory

**Archive:** cp24_generic_sec_pipeline v1.0.0
**Generated:** 2026-06-12

---

## Scripts

| Script | Purpose | Inputs | Outputs | CLI Usage | Safety |
|--------|---------|--------|---------|-----------|--------|
| `scripts/sec_ticker_inventory.py` | Resolve ticker to CIK and index SEC submissions | Ticker symbol | SEC inventory JSON/MD | `python scripts/sec_ticker_inventory.py <TICKER>` | Report-only, no alerts |
| `scripts/form4_extractor.py` | Extract insider transactions from Form 4 filings | Ticker/CIK, date range | Form 4 transactions JSON/MD | `python scripts/form4_extractor.py <TICKER>` | Report-only, no alerts |
| `scripts/ownership_filings_extractor.py` | Extract Form 144 and 13D/G ownership filings | Ticker/CIK, date range | Ownership filings JSON/MD | `python scripts/ownership_filings_extractor.py <TICKER>` | Report-only, no alerts |
| `scripts/xbrl_financial_extractor.py` | Extract financial metrics from SEC XBRL API | CIK | XBRL financials JSON/MD | `python scripts/xbrl_financial_extractor.py <TICKER>` | Report-only, no alerts |
| `scripts/capital_structure_calculator.py` | Calculate capital structure and dilution | Form 4 + XBRL data | Capital structure JSON/MD | `python scripts/capital_structure_calculator.py <TICKER>` | Report-only, no alerts |
| `scripts/institutional_13f_extractor.py` | Extract 13F institutional ownership | CIK, CUSIP | 13F holdings JSON/MD | `python scripts/institutional_13f_extractor.py <TICKER>` | Report-only, no alerts |
| `scripts/generic_sec_synthesis.py` | Synthesize CP24B-CP24G outputs into unified packet | CP24B-CP24G outputs | Synthesis JSON/MD/CSV | `python scripts/generic_sec_synthesis.py --ticker <TICKER>` | Report-only, no alerts |

---

## Source Modules

| Module | Purpose | Inputs | Outputs | Safety Considerations |
|--------|---------|--------|---------|----------------------|
| `sources/sec_inventory_builder.py` | Build SEC submissions inventory | Ticker, SEC API data | Inventory dict | No network calls outside SEC EDGAR |
| `sources/form4_parser.py` | Parse Form 4 XML filings | Form 4 XML | Transaction records | Handles non-standard XML structures |
| `sources/ownership_filings_parser.py` | Parse Form 144 and 13D/G filings | Filing HTML/XML | Ownership records | May have sparse coverage |
| `sources/xbrl_extractor.py` | Extract XBRL financial metrics | SEC companyfacts JSON | Financial metrics | API can lag or be unavailable |
| `sources/capital_structure_analyzer.py` | Analyze capital structure and dilution | Form 4, XBRL data | Capital metrics | Conservative estimates |
| `sources/institutional_13f_parser.py` | Parse 13F institutional filings | 13F XML/HTML | Institutional holdings | Partial manager universe |
| `sources/generic_synthesis_composer.py` | Compose generic synthesis from modules | All module outputs | Synthesis packet | Requires >= 12 evidence rows |

---

## Test Files

| Test File | Purpose | Tests | Coverage | Safety Checks |
|-----------|---------|-------|----------|---------------|
| `tests/test_generic_sec_synthesis.py` | Validate generic synthesis logic | 32 | CP24H synthesis | Schema, safety flags, evidence rows, no secrets, no recommendation language |
| `tests/test_multi_ticker_validation.py` | Validate multi-ticker batch | 15 | CP24I validation | Batch summary, validation matrix, degraded mode, all tickers present |
| `tests/test_cp24_archive.py` | Validate CP24J archive integrity | 20 | CP24J archive | Archive files exist, checksums match, no secrets in archive docs |

---

## Sample Output Roots

| Output Root | Module | Purpose | Typical Contents |
|-------------|--------|---------|------------------|
| `docs/sample_reports/sec_inventory/<TICKER>/` | CP24B | SEC submissions inventory | `<TICKER>_sec_inventory.json`, `<TICKER>_sec_inventory.md` |
| `docs/sample_reports/form4_transactions/<TICKER>/` | CP24C | Form 4 insider transactions | `<TICKER>_form4_transactions.json`, `<TICKER>_form4_summary.md` |
| `docs/sample_reports/ownership_filings/<TICKER>/` | CP24D | Ownership filings | `<TICKER>_ownership_filings.json`, `<TICKER>_ownership_summary.md` |
| `docs/sample_reports/xbrl_financials/<TICKER>/` | CP24E | XBRL financial metrics | `<TICKER>_xbrl_financials.json`, `<TICKER>_financials_summary.md` |
| `docs/sample_reports/capital_structure/<TICKER>/` | CP24F | Capital structure and dilution | `<TICKER>_capital_structure.json`, `<TICKER>_dilution_summary.md` |
| `docs/sample_reports/13f_institutional_ownership/<TICKER>/` | CP24G | 13F institutional ownership | `<TICKER>_13f_holdings.json`, `<TICKER>_13f_summary.md` |
| `docs/sample_reports/generic_synthesis/<TICKER>/` | CP24H | Generic SEC synthesis | `<TICKER>_generic_sec_synthesis.json`, `<TICKER>_generic_sec_synthesis.md`, `<TICKER>_evidence_matrix.csv` |
| `docs/sample_reports/cp24i_validation/` | CP24I | Multi-ticker validation | `batch_generic_sec_synthesis_summary.json`, `validation_matrix.csv`, per-ticker validation summaries |

---

## Checkpoint Reports

| Report | Checkpoint | Purpose | Key Sections |
|--------|-----------|---------|--------------|
| `docs/checkpoints/reports/CP24A_full_sec_extraction_architecture_report.md` | CP24A | Pipeline architecture | Design decisions, data flow, module boundaries |
| `docs/checkpoints/reports/CP24B_ticker_cik_submissions_inventory_report.md` | CP24B | Ticker/CIK inventory | Implementation, validation, sample outputs |
| `docs/checkpoints/reports/CP24C_form4_extraction_report.md` | CP24C | Form 4 extraction | XML parsing, transaction normalization, validation |
| `docs/checkpoints/reports/CP24D_ownership_filings_extraction_report.md` | CP24D | Ownership filings | Form 144 and 13D/G parsing, metadata extraction |
| `docs/checkpoints/reports/CP24E_xbrl_financial_extraction_report.md` | CP24E | XBRL financials | companyfacts API integration, metric extraction |
| `docs/checkpoints/reports/CP24F_capital_structure_dilution_report.md` | CP24F | Capital structure | Share count calculations, dilution estimates |
| `docs/checkpoints/reports/CP24G_13f_institutional_ownership_integration_report.md` | CP24G | 13F ownership | CUSIP matching, institutional holder identification |
| `docs/checkpoints/reports/CP24H_generic_sec_synthesis_report.md` | CP24H | Generic synthesis | Evidence matrix, synthesis scores, framing logic |
| `docs/checkpoints/reports/CP24H_fix_evidence_mapping_report.md` | CP24H-Fix | Evidence fix | NVDA evidence row addition, test updates |
| `docs/checkpoints/reports/CP24I_multi_ticker_validation_report.md` | CP24I | Multi-ticker validation | Batch validation, five-ticker coverage, MAIA leakage check |
| `docs/checkpoints/reports/CP24J_documentation_archive_hardening_report.md` | CP24J | Archive hardening | Manifest, checksums, usage guides, validation summary |

---

## Workflow Documentation

| Document | Purpose | Key Sections |
|----------|---------|--------------|
| `docs/workflows/full_sec_extraction_architecture.md` | Pipeline architecture overview | Module design, data flow diagrams, integration points |
| `docs/workflows/full_sec_extraction_implementation_plan.md` | Implementation roadmap | Checkpoint sequence, dependencies, milestones |
| `docs/workflows/full_sec_extraction_schema.md` | Data schema definitions | JSON schemas for each module output |
| `docs/workflows/full_sec_extraction_test_plan.md` | Testing strategy | Unit tests, integration tests, validation criteria |
| `docs/workflows/generic_ticker_synthesis_workflow.md` | Synthesis workflow guide | Module integration, evidence matrix construction, synthesis logic |

---

## Archive Documentation

| Document | Purpose | Key Sections |
|----------|---------|--------------|
| `docs/archives/cp24_generic_sec_pipeline/README.md` | Archive overview | What CP24 built, module summaries, usage instructions |
| `docs/archives/cp24_generic_sec_pipeline/MANIFEST.json` | Machine-readable manifest | Artifact inventory with sizes and checksums |
| `docs/archives/cp24_generic_sec_pipeline/MANIFEST.md` | Human-readable manifest | Organized artifact listings by category |
| `docs/archives/cp24_generic_sec_pipeline/CHECKSUMS.sha256` | SHA-256 checksums | File integrity verification |
| `docs/archives/cp24_generic_sec_pipeline/CP24_pipeline_status.md` | Checkpoint status | Per-checkpoint status, commits, limitations |
| `docs/archives/cp24_generic_sec_pipeline/CP24_safe_usage_guide.md` | Safe usage guide | CLI examples, safety rules, troubleshooting |
| `docs/archives/cp24_generic_sec_pipeline/CP24_module_inventory.md` | Module inventory | This file - complete module catalog |
| `docs/archives/cp24_generic_sec_pipeline/CP24_validation_summary.md` | Validation summary | Test results, metrics, safety confirmations |

---

## Module Dependencies

### CP24B (Ticker Inventory)
**Dependencies:** None (entry point)
**Dependents:** CP24C, CP24D, CP24E, CP24F, CP24G

### CP24C (Form 4 Extraction)
**Dependencies:** CP24B (CIK)
**Dependents:** CP24F (capital structure), CP24H (synthesis)

### CP24D (Ownership Filings)
**Dependencies:** CP24B (CIK)
**Dependents:** CP24H (synthesis)

### CP24E (XBRL Financials)
**Dependencies:** CP24B (CIK)
**Dependents:** CP24F (capital structure), CP24H (synthesis)

### CP24F (Capital Structure)
**Dependencies:** CP24C (Form 4), CP24E (XBRL)
**Dependents:** CP24H (synthesis)

### CP24G (13F Ownership)
**Dependencies:** CP24B (CIK, CUSIP)
**Dependents:** CP24H (synthesis)

### CP24H (Generic Synthesis)
**Dependencies:** CP24B, CP24C, CP24D, CP24E, CP24F, CP24G (all modules)
**Dependents:** CP24I (validation)

### CP24I (Multi-Ticker Validation)
**Dependencies:** CP24H (synthesis for multiple tickers)
**Dependents:** None (terminal node)

---

## Safety Guidelines per Module

### All Modules
- ✓ Report-only mode (no alerts, no Telegram, no email)
- ✓ No `.env` secrets exposed in outputs
- ✓ No buy/sell/hold recommendation language
- ✓ No hardcoded credentials
- ✓ Safe error handling (no stack traces with sensitive data)

### CP24B (Ticker Inventory)
- ✓ Public SEC API only (no authentication)
- ✓ Rate limiting respect (1 req/sec default)
- ✓ Cached responses to minimize SEC load

### CP24C (Form 4 Extraction)
- ✓ XML parsing with error handling (malformed filings)
- ✓ Transaction normalization (handles derivative transactions)

### CP24E (XBRL Financials)
- ✓ companyfacts API error handling (API downtime)
- ✓ Graceful degradation if metrics missing

### CP24F (Capital Structure)
- ✓ Conservative dilution estimates (not financial advice)
- ✓ Clear notes on estimation methodology

### CP24G (13F Ownership)
- ✓ Partial manager universe documented
- ✓ CUSIP matching failures handled gracefully

### CP24H (Generic Synthesis)
- ✓ Evidence row count threshold (>= 12 rows)
- ✓ Degraded mode handling (module failures)
- ✓ Posture label allowlist (no recommendation language)
- ✓ Safety flag validation in tests

---

## Module Maintenance

### Adding a New Module

1. Create script in `scripts/`
2. Create source module in `sources/`
3. Create test file in `tests/`
4. Create sample output root in `docs/sample_reports/`
5. Create checkpoint report in `docs/checkpoints/reports/`
6. Update workflow docs
7. Add to manifest and inventory
8. Run full test suite

### Updating an Existing Module

1. Create fix branch (e.g., `CP24C-Fix`)
2. Modify script and/or source module
3. Update tests (add new tests if needed)
4. Regenerate sample outputs
5. Create fix checkpoint report
6. Update manifests and checksums
7. Run full test suite
8. Commit and push

---

**This module inventory is current as of 2026-06-12.**
