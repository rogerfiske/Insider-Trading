# CP24 Generic SEC Pipeline - Archive Manifest

**Archive:** cp24_generic_sec_pipeline
**Created:** 2026-06-12
**Version:** 1.0.0
**Description:** Complete archive of CP24 generic SEC-only extraction and synthesis pipeline

---

## Checkpoints

- CP24A: Architecture
- CP24B: Ticker/CIK Inventory
- CP24C: Form 4 Extraction
- CP24D: Ownership Filings Extraction
- CP24E: XBRL Financial Extraction
- CP24F: Capital Structure and Dilution
- CP24G: 13F Institutional Ownership
- CP24H: Generic SEC Synthesis Composer
- CP24H-Fix: Evidence Mapping Fix
- CP24I: Multi-Ticker Validation
- CP24I-Fix: Five-Ticker Coverage Completion
- CP24J: Documentation and Archive Hardening

---

## Checkpoint Reports (10 files)

| Path | Checkpoint | Size | SHA256 | Notes |
|------|-----------|------|--------|-------|
| docs/checkpoints/reports/CP24A_full_sec_extraction_architecture_report.md | CP24A | 25539 | b29f3ba831... | Pipeline architecture and design |
| docs/checkpoints/reports/CP24B_ticker_cik_submissions_inventory_report.md | CP24B | 17770 | 179ba5b431... | Ticker/CIK resolution and submissions inventory |
| docs/checkpoints/reports/CP24C_form4_extraction_report.md | CP24C | 13249 | 80475ac5fd... | Form 4 insider transaction extraction |
| docs/checkpoints/reports/CP24D_ownership_filings_extraction_report.md | CP24D | 9957 | 0d6bb5f722... | Form 144 and 13D/G ownership filings |
| docs/checkpoints/reports/CP24E_xbrl_financial_extraction_report.md | CP24E | 17583 | 102b245725... | XBRL financial metrics extraction |
| docs/checkpoints/reports/CP24F_capital_structure_dilution_report.md | CP24F | 15033 | f0d2de5ab9... | Capital structure and dilution calculations |
| docs/checkpoints/reports/CP24G_13f_institutional_ownership_integration_report.md | CP24G | 14892 | 135f65912a... | 13F institutional ownership integration |
| docs/checkpoints/reports/CP24H_generic_sec_synthesis_report.md | CP24H | 13314 | 8949811f5d... | Generic SEC synthesis composer |
| docs/checkpoints/reports/CP24H_fix_evidence_mapping_report.md | CP24H-Fix | 13688 | c5866c170f... | Evidence mapping fix for CP24H |
| docs/checkpoints/reports/CP24I_multi_ticker_validation_report.md | CP24I | 16371 | c3c0cf59ee... | Multi-ticker validation including CP24I-Fix |

---

## Workflow Documentation (5 files)

| Path | Notes |
|------|-------|
| docs/workflows/full_sec_extraction_architecture.md | Pipeline architecture documentation |
| docs/workflows/full_sec_extraction_implementation_plan.md | Implementation plan and roadmap |
| docs/workflows/full_sec_extraction_schema.md | Data schema definitions |
| docs/workflows/full_sec_extraction_test_plan.md | Test plan and validation strategy |
| docs/workflows/generic_ticker_synthesis_workflow.md | Synthesis workflow guide |

---

## Core Scripts (7 files)

| Path | Module | Size | SHA256 | Notes |
|------|--------|------|--------|-------|
| scripts/generic_sec_synthesis.py | CP24H | 4803 | 23842fdce8... | Main synthesis script |
| scripts/sec_ticker_inventory.py | CP24B | - | - | Ticker/CIK inventory script |
| scripts/form4_extractor.py | CP24C | - | - | Form 4 extraction script |
| scripts/ownership_filings_extractor.py | CP24D | - | - | Ownership filings extraction script |
| scripts/xbrl_financial_extractor.py | CP24E | - | - | XBRL financial extraction script |
| scripts/capital_structure_calculator.py | CP24F | - | - | Capital structure calculation script |
| scripts/institutional_13f_extractor.py | CP24G | - | - | 13F institutional ownership script |

---

## Source Modules (7 files)

| Path | Module | Size | SHA256 | Notes |
|------|--------|------|--------|-------|
| sources/generic_synthesis_composer.py | CP24H | 51374 | 06044accc9... | Synthesis composer module |
| sources/sec_inventory_builder.py | CP24B | - | - | SEC inventory builder module |
| sources/form4_parser.py | CP24C | - | - | Form 4 parser module |
| sources/ownership_filings_parser.py | CP24D | - | - | Ownership filings parser module |
| sources/xbrl_extractor.py | CP24E | - | - | XBRL extractor module |
| sources/capital_structure_analyzer.py | CP24F | - | - | Capital structure analyzer module |
| sources/institutional_13f_parser.py | CP24G | - | - | 13F parser module |

---

## Test Files (2 files)

| Path | Tests | Size | SHA256 | Notes |
|------|-------|------|--------|-------|
| tests/test_generic_sec_synthesis.py | 32 | 22977 | d7ca3162e0... | Generic synthesis tests (CP24H) |
| tests/test_multi_ticker_validation.py | 15 | 8880 | 5b02eb0b0a... | Multi-ticker validation tests (CP24I) |

**Total Tests:** 47
**Pass Rate:** 100%

---

## MAIA Sample Outputs

| Path | Module | Size | SHA256 | Notes |
|------|--------|------|--------|-------|
| docs/sample_reports/sec_inventory/MAIA/ | CP24B | - | - | Ticker/CIK inventory outputs |
| docs/sample_reports/form4_transactions/MAIA/ | CP24C | - | - | Form 4 transaction outputs |
| docs/sample_reports/ownership_filings/MAIA/ | CP24D | - | - | Ownership filings outputs |
| docs/sample_reports/xbrl_financials/MAIA/ | CP24E | - | - | XBRL financial outputs |
| docs/sample_reports/capital_structure/MAIA/ | CP24F | - | - | Capital structure outputs |
| docs/sample_reports/13f_institutional_ownership/MAIA/ | CP24G | - | - | 13F institutional ownership outputs |
| docs/sample_reports/generic_synthesis/MAIA/MAIA_generic_sec_synthesis.json | CP24H | 8182 | b07f697b7b... | Generic synthesis JSON output |
| docs/sample_reports/generic_synthesis/MAIA/MAIA_generic_sec_synthesis.md | CP24H | - | - | Generic synthesis Markdown output |
| docs/sample_reports/generic_synthesis/MAIA/MAIA_evidence_matrix.csv | CP24H | - | - | Evidence matrix CSV (13 rows) |

---

## NVDA Sample Outputs

| Path | Module | Size | SHA256 | Notes |
|------|--------|------|--------|-------|
| docs/sample_reports/sec_inventory/NVDA/ | CP24B | - | - | Ticker/CIK inventory outputs |
| docs/sample_reports/form4_transactions/NVDA/ | CP24C | - | - | Form 4 transaction outputs |
| docs/sample_reports/ownership_filings/NVDA/ | CP24D | - | - | Ownership filings outputs |
| docs/sample_reports/xbrl_financials/NVDA/ | CP24E | - | - | XBRL financial outputs |
| docs/sample_reports/capital_structure/NVDA/ | CP24F | - | - | Capital structure outputs |
| docs/sample_reports/13f_institutional_ownership/NVDA/ | CP24G | - | - | 13F institutional ownership outputs |
| docs/sample_reports/generic_synthesis/NVDA/NVDA_generic_sec_synthesis.json | CP24H | 7794 | 649599470a... | Generic synthesis JSON output |
| docs/sample_reports/generic_synthesis/NVDA/NVDA_generic_sec_synthesis.md | CP24H | - | - | Generic synthesis Markdown output |
| docs/sample_reports/generic_synthesis/NVDA/NVDA_evidence_matrix.csv | CP24H | - | - | Evidence matrix CSV (12 rows) |

---

## CP24I Validation Outputs

| Path | Module | Ticker | Size | SHA256 | Notes |
|------|--------|--------|------|--------|-------|
| docs/sample_reports/cp24i_validation/batch_generic_sec_synthesis_summary.json | CP24I | All | 2444 | 18e1c398d1... | Batch summary JSON (5 tickers) |
| docs/sample_reports/cp24i_validation/batch_generic_sec_synthesis_summary.md | CP24I | All | - | - | Batch summary Markdown |
| docs/sample_reports/cp24i_validation/validation_matrix.csv | CP24I | All | 1461 | 5a629ac4bb... | Validation matrix (5 tickers, 23 columns) |
| docs/sample_reports/cp24i_validation/MAIA/ | CP24I | MAIA | - | - | MAIA validation summary (status: completed) |
| docs/sample_reports/cp24i_validation/NVDA/ | CP24I | NVDA | - | - | NVDA validation summary (status: completed) |
| docs/sample_reports/cp24i_validation/AAPL/ | CP24I-Fix | AAPL | - | - | AAPL validation summary (status: not_run_with_reason) |
| docs/sample_reports/cp24i_validation/MSFT/ | CP24I-Fix | MSFT | - | - | MSFT validation summary (status: not_run_with_reason) |
| docs/sample_reports/cp24i_validation/TSLA/ | CP24I-Fix | TSLA | - | - | TSLA validation summary (status: not_run_with_reason) |

---

## Excluded Files

The following file types are explicitly excluded from this archive:

- `.env` (environment variables and secrets)
- `.state/` (runtime state databases)
- `*.db`, `*.sqlite`, `*.sqlite3` (databases)
- `*.log` (log files)
- `.venv/` (Python virtual environment)
- `.claude/` (Claude configuration)
- `MAIA.xlsx` (Roger's private spreadsheet)
- `OpenInsider data` (external third-party data)
- `config/watchlists/` (except `*.example.txt`)
- `SEC cache files` (cached SEC filings)
- `Evidence cache files` (cached evidence data)
- `Private portfolio files`
- `Temporary files`

---

## Safety Confirmations

| Safety Check | Status |
|--------------|--------|
| Report-only mode | ✓ True |
| No alerts generated | ✓ True |
| No Telegram messages | ✓ True |
| No email sent | ✓ True |
| No scheduled tasks modified | ✓ True |
| No .env exposed | ✓ True |
| No secrets in archive | ✓ True |
| No buy/sell/hold language | ✓ True |

---

## Validation Metrics

| Metric | Value |
|--------|-------|
| Checkpoint Reports | 10 |
| Workflow Docs | 5 |
| Core Scripts | 7 |
| Source Modules | 7 |
| Test Files | 2 |
| Total Tests | 47 |
| Test Pass Rate | 100% |
| Tickers Validated (completed) | MAIA, NVDA |
| Tickers Documented (all statuses) | MAIA, NVDA, AAPL, MSFT, TSLA |
| Evidence Rows (MAIA) | 13 |
| Evidence Rows (NVDA) | 12 |
| MAIA Leakage Check | PASS |

---

## Archive Contents Summary

- **Total Checkpoint Reports:** 10
- **Total Workflow Docs:** 5
- **Total Core Scripts:** 7
- **Total Source Modules:** 7
- **Total Test Files:** 2
- **Total Tickers Validated:** 2 (completed)
- **Total Tickers Documented:** 5 (all statuses)
- **Test Coverage:** 47 tests, 100% passing

---

**This manifest documents the complete CP24 generic SEC pipeline archive as of 2026-06-12.**
