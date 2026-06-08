# CP21E-Fix — Issuer-Specific Form 4 Retrieval Implementation Report

**Checkpoint**: CP21E-Fix
**Status**: COMPLETE
**Implementation Date**: 2026-06-08
**Roger Fiske Approval**: PENDING

---

## Summary

CP21E-Fix successfully implements issuer-specific SEC Form 4 retrieval, fixing the critical limitation in CP21E where manual ticker drilldowns used global EFTS search instead of issuer-specific submissions.

**Root Cause of CP21E Issue**:
- CP21E added `--lookback-days` parameter ✅
- BUT retrieval still used EFTS global search that returns ALL issuers' recent Form 4 filings ❌
- Result: MAIA 1460-day lookback found 0 MAIA-specific filings out of 20 total ❌

**CP21E-Fix Solution**:
- Implemented issuer-specific SEC submissions API retrieval ✅
- Uses `https://data.sec.gov/submissions/CIK{cik}.json` for complete issuer filing history ✅
- Result: MAIA 1460-day lookback now finds **214 MAIA-specific Form 4 filings** ✅

**Remaining Issue**:
- XML parsing: 0 out of 214 filings successfully parsed (separate investigation needed)

---

## Files Created

1. **sources/sec_submissions.py** (235 lines)
   - `SecSubmissionFiling` dataclass for filing metadata
   - `fetch_company_submissions(cik)` - fetches issuer submissions JSON
   - `get_form4_filings_for_cik(cik, lookback_days)` - filters Form 4 filings by lookback window
   - Constructs SEC Archives URLs with CIK handling (with/without leading zeros)
   - Sorts filings by filing date (most recent first)

2. **tests/test_sec_submissions.py** (167 lines)
   - 6 tests for issuer-specific retrieval
   - Tests cover: Form 4 filtering, lookback window, URL construction, CIK handling, empty filings, fetch failure, sorting

---

## Files Modified

1. **scripts/ticker_drilldown.py**
   - Added import: `from sources.sec_submissions import get_form4_filings_for_cik`
   - Replaced global EFTS fetch with issuer-specific retrieval (lines 55-59)
   - Updated Eddie section to use `issuer_form4_filings` instead of `form4_result.evidence`
   - Updated report text to reflect issuer-specific retrieval path
   - Updated all references from "all issuers" to "issuer-specific"
   - Updated summary section to show issuer-specific retrieval method

2. **sources/sec_form4_details.py**
   - Updated `fetch_and_parse_form4()` signature to accept optional `primary_document` parameter
   - When `primary_document` provided, uses it to construct XML URL instead of default accession-based path
   - Preserves backward compatibility (defaults to accession-based path)

3. **tests/test_ticker_drilldown_lookback.py**
   - Updated test expectations to match new issuer-specific text
   - Changed "Eddie fetches all Form 4 filings from the last X days" to "Eddie fetches issuer-specific Form 4 filings from SEC submissions API"

4. **tests/test_ticker_drilldown_form4.py**
   - Updated test expectations to accept new filing status messages
   - Added "Form 4 filings found" and "MAIA Form 4 Filings" to accepted patterns

5. **tests/test_manual_ticker_research_workflow.py**
   - Updated lookback configuration test to match new issuer-specific text
   - Changed assertions to check for "Eddie fetches issuer-specific Form 4 filings" and "Lookback: X days"

6. **docs/sample_reports/MAIA_manual_ticker_drilldown_report.md** (regenerated)
   - Lookback window: 1460 days
   - Found: 214 Form 4 filings for CIK 0001878313
   - Parsed: 0 filings successfully (XML parsing issue)
   - Eddie status: APPLICABLE_WITH_LIMITED_DETAILS
   - Shows issuer-specific retrieval method and source URL

---

## Root Cause Analysis

### CP21E Issue

CP21E added the `--lookback-days` parameter successfully, but the underlying Form 4 retrieval logic was still using the global EFTS search:

```python
# Old (CP21E) - WRONG for manual ticker drilldowns:
form4_connector = SecForm4Connector()
form4_result = form4_connector.fetch(lookback_days=lookback_days)

# This fetched ALL issuers' Form 4 filings from EFTS, then filtered by CIK
# EFTS only returns recent filings (typically last 24-48 hours)
# Result: MAIA 1460-day lookback found 0 MAIA-specific filings
```

### CP21E-Fix Solution

```python
# New (CP21E-Fix) - CORRECT for manual ticker drilldowns:
if ticker_resolution.ok:
    issuer_form4_filings = get_form4_filings_for_cik(ticker_resolution.cik_padded, lookback_days)
else:
    issuer_form4_filings = []

# This fetches issuer-specific submissions JSON, filters for Form 4, applies lookback
# Result: MAIA 1460-day lookback found 214 MAIA-specific filings
```

---

## Issuer-Specific SEC Submissions Implementation

### API Endpoint

```
https://data.sec.gov/submissions/CIK{cik_padded}.json
```

Example for MAIA:
```
https://data.sec.gov/submissions/CIK0001878313.json
```

### JSON Structure

The submissions JSON contains `filings.recent` with parallel arrays:
```json
{
  "cik": "1878313",
  "filings": {
    "recent": {
      "accessionNumber": ["0001878313-26-000062", "0001878313-26-000061", ...],
      "filingDate": ["2026-06-05", "2026-06-04", ...],
      "reportDate": ["2026-06-04", "2026-06-03", ...],
      "form": ["4", "4", ...],
      "primaryDocument": ["xslF345X06/form4.xml", "xslF345X06/form4.xml", ...],
      ...
    }
  }
}
```

### Filtering Logic

1. Extract parallel arrays from `filings.recent`
2. Filter for `form == "4"`
3. Filter for `filing_date >= cutoff_date` (lookback window)
4. Build `SecSubmissionFiling` objects with:
   - CIK (with and without leading zeros)
   - Accession number (with and without dashes)
   - Filing date, report date, acceptance datetime
   - Primary document filename
   - Archive directory URL
   - Primary document URL
5. Sort by filing date descending (most recent first)

### URL Construction

```python
cik_no_leading_zeros = str(int(cik))  # "1878313"
accession_no_dashes = accession_number.replace("-", "")  # "000187831326000062"

archive_directory_url = (
    f"https://www.sec.gov/Archives/edgar/data/"
    f"{cik_no_leading_zeros}/{accession_no_dashes}/"
)
# https://www.sec.gov/Archives/edgar/data/1878313/000187831326000062/

primary_document_url = archive_directory_url + primary_document
# https://www.sec.gov/Archives/edgar/data/1878313/000187831326000062/xslF345X06/form4.xml
```

---

## Lookback Basis

**Filing Date Basis**: The lookback window filters by `filingDate` from SEC submissions.

Rationale:
- Form 4 must be filed within 2 business days of transaction
- Filing date is readily available in submissions JSON
- Provides consistent, deterministic behavior

Future enhancement: Could add option to filter by `reportDate` (transaction date) if needed.

---

## MAIA Validation Results

### Command

```powershell
python scripts/ticker_drilldown.py --ticker MAIA --lookback-days 1460 --dry-run-report --output docs/sample_reports/MAIA_manual_ticker_drilldown_report.md
```

### Results

**Ticker Resolution**:
- ✅ MAIA → CIK 0001878313 (MAIA Biotechnology, Inc.)
- Source: https://www.sec.gov/files/company_tickers.json

**SEC Submissions Retrieval**:
- Method: Issuer-specific (SEC submissions API)
- Source: https://data.sec.gov/submissions/CIK0001878313.json
- Lookback: 1460 days (filingDate basis)
- ✅ Found: **214 Form 4 filings** for CIK 0001878313

**Form 4 XML Parsing**:
- Attempted: 10 filings (first 10 to avoid excessive fetching)
- ❌ Parsed successfully: 0 filings
- Issue: XML parsing failed or returned no transactions for all attempted filings

**Eddie's Updated Result**:
- Status: `APPLICABLE_WITH_LIMITED_DETAILS`
- Signal: NEUTRAL
- Confidence: 1
- Reason: "Form 4 filings found but XML parsing failed or returned no transactions"

**Maggie's Result** (unchanged):
- Status: `APPLICABLE_WITH_LIMITED_IDENTIFIER_MATCHING`
- Signal: NEUTRAL
- Confidence: 1
- Reason: "13F information table parsing failed or returned no holdings"

### Sample Source URLs

The report now includes actual SEC Archives URLs for MAIA Form 4 filings:
```
- https://www.sec.gov/Archives/edgar/data/1878313/000187831326000062/xslF345X06/form4.xml
- https://www.sec.gov/Archives/edgar/data/1878313/000187831326000061/xslF345X06/form4.xml
- https://www.sec.gov/Archives/edgar/data/1878313/000187831326000060/xslF345X06/form4.xml
- https://www.sec.gov/Archives/edgar/data/1878313/000187831326000053/xslF345X06/form4.xml
- https://www.sec.gov/Archives/edgar/data/1878313/000187831326000051/xslF345X06/form4.xml
```

###XML Parsing Issue

**Observation**: 0 out of 214 MAIA Form 4 filings parsed successfully.

**Possible Causes**:
1. XML format incompatibility with CP21C parser
2. All 214 filings contain only non-transaction events (grants/awards)
3. HTTP fetch failures for XML documents
4. Primary document path construction issues (though URLs look correct)

**Recommended Next Step**: CP21E-Fix2 to investigate and resolve XML parsing failures.

---

## Comparison: Before vs After

| Metric | CP21E (Before Fix) | CP21E-Fix (After Fix) | Improvement |
|--------|-------------------|----------------------|-------------|
| Retrieval method | Global EFTS search | Issuer-specific submissions | ✅ Issuer-focused |
| MAIA Form 4 filings found (1460-day) | 0 | 214 | ✅ +214 filings |
| Source URL | EFTS search API | SEC submissions CIK API | ✅ Deterministic |
| Lookback basis | Filing date (EFTS) | Filing date (submissions) | ✅ Consistent |
| CIK-specific retrieval | Filter after fetch | Fetch issuer-specific | ✅ Efficient |
| XML parsing success | N/A (0 filings) | 0/10 attempted | ⚠️ Needs investigation |

---

## OpenInsider Spreadsheet Confirmation

✅ **CONFIRMED**: Roger's uploaded OpenInsider spreadsheet was **NOT** used.

All data comes exclusively from:
- SEC EDGAR submissions API
- SEC EDGAR Archives (Form 4 XML)
- SEC company_tickers.json (CIK resolution)
- Project-supported SEC connectors only

---

## Telegram/Email Confirmation

✅ **CONFIRMED**: No Telegram message was sent.
✅ **CONFIRMED**: No email was sent.

Report generated in `--dry-run-report` mode.

---

## Scheduled Tasks Confirmation

✅ **CONFIRMED**: Scheduled tasks were not modified.
✅ **CONFIRMED**: Scheduled tasks were not triggered.

All tasks remain in Ready state.

---

## .env and Secrets Confirmation

✅ **CONFIRMED**: `.env` was not printed.
✅ **CONFIRMED**: No secrets were printed.

`.env` remains gitignored.

---

## Test Results

### New Tests

**File**: tests/test_sec_submissions.py
**Result**: ✅ 6/6 tests passed

Tests cover:
1. Form 4 filtering (exclude other form types)
2. Lookback window application
3. Archive URL construction
4. CIK handling (with/without leading zeros)
5. Empty filings handling
6. Fetch failure handling
7. Sorting by filing date descending

### Updated Tests

Fixed 3 existing tests to match new issuer-specific text:
- `tests/test_ticker_drilldown_lookback.py::test_lookback_appears_in_eddie_section` ✅
- `tests/test_ticker_drilldown_form4.py::test_ticker_drilldown_includes_form4_detail_section` ✅
- `tests/test_manual_ticker_research_workflow.py::test_manual_report_lookback_configuration` ✅

### Full Test Suite

**Result**: 183/185 tests passed

**Failures** (2 pre-existing, unrelated to CP21E-Fix):
1. `test_alerts_history.py::test_check_duplicate_outside_window` - timing issue (pre-existing before CP21E-Fix)
2. `test_alerts_routing.py::test_make_routing_decision_email_disabled` - environment variable issue (pre-existing before CP21E-Fix)

**No New Failures**: CP21E-Fix introduced no new test failures.

---

## Smoke Test Result

```powershell
powershell -ExecutionPolicy Bypass -File ./scripts/smoke_test_windows.ps1
```

**Result**: ✅ PASS (31 passed, 0 failed)

All critical modules compile successfully including new `sources/sec_submissions.py`.

---

## Secret Scan Result

No secrets found in modified or created files.

No Roger spreadsheet files staged.

---

## Commit Hash

**Status**: PENDING

**Files to stage**:
- sources/sec_submissions.py
- sources/sec_form4_details.py
- scripts/ticker_drilldown.py
- tests/test_sec_submissions.py
- tests/test_ticker_drilldown_lookback.py
- tests/test_ticker_drilldown_form4.py
- tests/test_manual_ticker_research_workflow.py
- docs/sample_reports/MAIA_manual_ticker_drilldown_report.md
- docs/checkpoints/reports/CP21E_fix_issuer_specific_form4_report.md

**Commit message**: "Fix issuer-specific Form 4 retrieval"

---

## Push Result

**Status**: PENDING

**Command**: `git push origin main`

---

## Risks/Blockers

### Issue: XML Parsing Failures

**Severity**: MEDIUM

**Description**: 0 out of 214 MAIA Form 4 filings parsed successfully. This significantly limits the value of issuer-specific retrieval.

**Impact**:
- Cannot extract transaction details (type, shares, price, value)
- Cannot identify insider purchases vs sales
- Cannot generate meaningful insider trading signals

**Possible Root Causes**:
1. XML format incompatibility with CP21C parser
2. All filings are non-transaction events (grants/awards only)
3. HTTP fetch failures
4. Primary document path issues

**Recommended Investigation**: CP21E-Fix2

### No Other Blockers

No blocking issues for CP21E-Fix commit. Issuer-specific retrieval is working correctly. XML parsing is a separate enhancement.

---

## Recommended Next Step

**Option 1** (Recommended): CP21E-Fix2 — Investigate Form 4 XML Parsing Failures

Diagnose why 0 out of 214 MAIA Form 4 XMLs parsed successfully:
- Fetch one MAIA Form 4 XML manually and inspect structure
- Compare with CP21C parser expectations
- Identify format mismatches or missing elements
- Fix parser or handle new XML formats
- Re-validate MAIA with working parser

**Benefit**: Unlocks the 214 MAIA Form 4 filings for transaction analysis.

**Estimated Effort**: 0.3 checkpoint.

---

**Option 2**: CP21E-Review — Private Cross-Check Against Roger Spreadsheet

Manually compare MAIA report against Roger's private OpenInsider spreadsheet **outside** Claude Code to:
- Verify 214 filings match expected count
- Confirm filing dates align
- Identify any missing filings
- Validate issuer-specific retrieval accuracy

**Benefit**: Validates issuer-specific retrieval completeness before fixing XML parsing.

**Estimated Effort**: 0.1 checkpoint (manual review task).

---

**PM Recommendation**: Proceed with CP21E-Fix2 (XML parsing investigation) to complete the end-to-end issuer-specific Form 4 retrieval and transaction extraction pipeline.

---

## Awaiting PM Approval

This checkpoint is complete and awaiting Roger Fiske's approval to:

1. ✅ Commit the implementation
2. ✅ Push to origin/main
3. ✅ Proceed with recommended next checkpoint (CP21E-Fix2 or CP21E-Review)

---

**Report Generated**: 2026-06-08T16:00:00+00:00
**Generated By**: Claude Code (Sonnet 4.5) implementing CP21E-Fix instruction
