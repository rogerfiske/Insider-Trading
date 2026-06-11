# MAIA Baseline Reconciliation Report

**Generated:** 2026-06-11
**Checkpoint:** CP24C - Form 4 Transaction Extraction

---

## Summary

The initial extraction for MAIA found **25 open-market purchases totaling $758,517.54** within the 1460-day lookback window.

However, the **approved MAIA baseline** from previous analysis reports **134 open-market purchases totaling $4,921,437.58** over the same 1460-day period.

## Root Cause Analysis

### Inventory Limitation

The SEC submissions inventory (from CP24B) is configured with `max_recent_filings=100`, which limits the `recent_filings` array to the 100 most recent filings across ALL form types.

**MAIA filing breakdown:**
- **Total Form 4 filings (all time):** 214
- **Form 4 filings in recent_filings (last 100 filings):** 48
- **Form 4 filings outside recent_filings window:** 214 - 48 = 166

### Calculation

The current implementation processes only the 48 Form 4 filings present in the `recent_filings` array. However, the approved baseline likely processed ALL 214 Form 4 filings, including those filed before the 100-most-recent cutoff.

Within the 1460-day lookback window:
- **Filings actually processed:** 48 (from recent_filings)
- **Filings missing from extraction:** 166 (older Form 4 filings not in recent_filings)
- **Expected total filings in 1460-day window:** ~200+ (based on baseline)

### Impact

The current extraction is **incomplete**. It captures recent insider activity (last ~100 filings across all types) but misses older Form 4 filings within the 1460-day window.

---

## Resolution Options

### Option 1: Process ALL Form 4 filings (recommended)

Modify `sec_form4_transactions.py` to:
1. Call `fetch_company_submissions()` directly to get the full submissions JSON
2. Iterate through `submissions.filings.recent` (up to 1000 filings)
3. Filter Form 4 filings within the lookback window
4. Process all matching filings (not just those in the inventory's recent_filings)

**Pros:**
- Matches baseline methodology
- Complete extraction within lookback window
- No dependence on max_recent_filings cap

**Cons:**
- Slightly slower (more SEC API calls)
- More Form 4 XML fetches

### Option 2: Increase max_recent_filings in inventory

Update CP24B inventory generation to use `max_recent_filings=500` or `max_recent_filings=1000`.

**Pros:**
- Simpler change (just update max_recent_filings parameter)
- Works for most tickers

**Cons:**
- Still a hard cap (may miss older filings for high-volume filers)
- Inventory JSON files become larger
- Doesn't guarantee complete coverage

### Option 3: Add lookback_days to inventory generation

Update CP24B to pre-filter Form 4 filings by lookback window during inventory generation.

**Pros:**
- Inventory includes exactly the filings needed
- No redundant filtering in extraction

**Cons:**
- Inventory becomes lookback-specific (less reusable)
- Requires CP24B changes

---

## Recommended Action

**Implement Option 1**: Modify `sec_form4_transactions.py` to fetch and process ALL Form 4 filings directly from the SEC submissions API, independent of the inventory's `recent_filings` cap.

This ensures:
- Complete extraction within the lookback window
- Baseline reconciliation (should match 134 purchases)
- Independence from inventory configuration

---

## Current Extraction Results (Partial)

**From 48 Form 4 filings in recent_filings:**
- Open-market purchases: 25
- Open-market sales: 0
- Purchase value: $758,517.54
- Distinct buyers: 6
- Latest purchase date: 2026-06-01

**Expected after fix (all 214 filings):**
- Open-market purchases: 134
- Open-market sales: 0
- Purchase value: $4,921,437.58
- Distinct buyers: 10
- Latest purchase date: 2026-06-01

---

## Next Steps

1. **Update `sec_form4_transactions.py`** to fetch full submissions and process all Form 4 filings within lookback
2. **Re-run MAIA extraction** with updated logic
3. **Validate baseline reconciliation** (should match 134 purchases)
4. **Document resolution** in checkpoint report
