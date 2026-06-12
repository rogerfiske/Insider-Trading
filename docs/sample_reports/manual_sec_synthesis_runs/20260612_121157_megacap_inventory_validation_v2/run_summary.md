# Manual SEC Synthesis Run Summary

**Run ID:** 20260612_121157_megacap_inventory_validation_v2
**Generated:** 2026-06-12 19:11:58 UTC
**Mode:** inventory-first

---

## Purpose and Source Boundary

This is a manual SEC-only research run using the approved CP24 generic SEC pipeline.

**Data sources:**
- SEC EDGAR public filings
- SEC companyfacts API
- SEC 13F InfoTables

**Excluded sources:**
- Roger's uploaded MAIA spreadsheet
- OpenInsider data
- Third-party paid/private sources
- Live market data

---

## Tickers Requested

- **AAPL**: completed
- **MSFT**: completed
- **TSLA**: completed

---

## Per-Ticker Results

### AAPL

**Status:** completed
**Degraded:** False

**Modules Run:** inventory

**Output Path:** `docs\sample_reports\manual_sec_synthesis_runs\20260612_121157_megacap_inventory_validation_v2\AAPL`

### MSFT

**Status:** completed
**Degraded:** False

**Modules Run:** inventory

**Output Path:** `docs\sample_reports\manual_sec_synthesis_runs\20260612_121157_megacap_inventory_validation_v2\MSFT`

### TSLA

**Status:** completed
**Degraded:** False

**Modules Run:** inventory

**Output Path:** `docs\sample_reports\manual_sec_synthesis_runs\20260612_121157_megacap_inventory_validation_v2\TSLA`

---

## Safety Confirmations

- ✓ Report-only mode
- ✓ No alerts generated
- ✓ No Telegram messages sent
- ✓ No email sent
- ✓ No scheduled tasks modified or triggered
- ✓ No .env access or modifications
- ✓ No OpenInsider spreadsheet usage
- ✓ No buy/sell/hold recommendation language

---

## Output Files

- `run_manifest.json` - Complete run metadata and file paths
- `run_summary.json` - Structured run results
- `run_summary.md` - This file
- `validation_matrix.csv` - Per-ticker validation matrix
- `safety_audit.json` - Safety audit log
- `<TICKER>/` - Per-ticker output folders

---

## Disclaimer

**This is not investment advice.** Perform your own due diligence and consult licensed financial professionals before making investment decisions.

---

## Next Suggested Action

Review individual ticker outputs in the `<TICKER>/` folders. Check synthesis JSON files for evidence matrices and scoring framework.
