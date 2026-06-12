# AAPL Validation Summary — CP24I

**Ticker:** AAPL
**CIK:** 0000320193
**Company:** Apple Inc.
**Generated:** 2026-06-12
**Status:** NOT RUN WITH REASON

---

## Validation Status

**Overall:** NOT RUN WITH REASON

**Reason:** Full CP24B-CP24G extraction deferred to avoid expanding SEC collection scope during CP24I validation.

---

## Module Status

| Module | Status | Reason |
|--------|--------|--------|
| sec_inventory | not_run | Deferred |
| form4_transactions | not_run | Deferred |
| ownership_filings | not_run | Deferred |
| xbrl_financials | not_run | Deferred |
| capital_structure | not_run | Deferred |
| institutional_13f | not_run | Deferred |
| generic_synthesis | not_run | Cannot generate without module inputs |

---

## Evidence Matrix

- **Row Count:** 0 (not generated)
- **Synthesis Posture:** "Incomplete evidence"

---

## Degraded Mode

- **Is Degraded:** True
- **Reasons:**
  - Full CP24B-CP24G extraction deferred to avoid expanding SEC collection scope during CP24I validation
  - CP24I validates workflow capability with existing complete datasets (MAIA, NVDA)
  - AAPL data extraction deferred to future checkpoint

---

## Safety Confirmations

| Flag | Value | Status |
|------|-------|--------|
| report_only | True | ✓ |
| alerts_generated | False | ✓ |
| external_spreadsheet_used | False | ✓ |
| telegram_sent | False | ✓ |
| email_sent | False | ✓ |
| scheduled_tasks_modified | False | ✓ |
| env_printed_or_changed | False | ✓ |
| buy_sell_hold_language_used | False | ✓ |

---

## MAIA Leakage Check

- **Status:** ✓ PASS
- **MAIA References Found:** 0

---

## Notes

CP24I validates the multi-ticker batch workflow using existing complete datasets (MAIA and NVDA). AAPL data extraction requires full CP24B-CP24G processing and is deferred to avoid expanding the SEC collection scope during this validation checkpoint. Future checkpoints can extend validation coverage to AAPL after data extraction.
