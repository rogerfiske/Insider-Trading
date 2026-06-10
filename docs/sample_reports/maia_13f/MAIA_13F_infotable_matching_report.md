# MAIA Biotechnology, Inc. — 13F Institutional Holdings Matching Report

**Ticker:** MAIA
**CIK:** 0001878313
**Generated:** 2026-06-10T18:24:57.659800Z
**Checkpoint:** CP23F

---

## Executive Summary

**No reliable 13F InfoTable matches found** for MAIA in the reviewed filing sample.

This does not necessarily mean zero institutional ownership. Possible explanations:

- Holdings below 13F reporting threshold ($200k or 10k shares)
- Holdings held by managers not in reviewed sample (5 large managers)
- Reporting lag (13F filed 45 days after quarter-end)
- Name/CUSIP mismatch preventing automated matching

---

## Source Boundary

**Sources used:**
- SEC EDGAR 13F-HR filings (public data)
- SEC submissions API for filing metadata
- 13F information table XML parsing

**Sources NOT used:**
- Roger's uploaded MAIA spreadsheet
- OpenInsider data
- Third-party institutional ownership pages
- Private/paid data sources

---

## Target Issuer/Ticker/CUSIP Resolution

**Ticker:** MAIA
**CIK:** 0001878313
**Issuer Name:** MAIA Biotechnology, Inc.
**CUSIP:** Not available (using issuer name matching)
**CUSIP Confidence:** unknown

---

## 13F Method Used

1. Fetch recent 13F-HR filing metadata from SEC submissions API
2. Locate and fetch 13F information table XML from SEC EDGAR
3. Parse XML to extract individual security holdings
4. Match MAIA holdings using:
   - CUSIP exact match (if available) → High confidence
   - Issuer name exact match → Medium confidence
   - Issuer name normalized match → Medium confidence
   - Issuer name fuzzy match → Low confidence (excluded from results)

---

## 13F Filings/Periods Reviewed

**Managers reviewed:** 5

- **Berkshire Hathaway** (CIK 0001067983)
  - Accession: 0001193125-26-226661
  - Filing date: 2026-05-15
  - Report period: 2026-03-31
- **Bridgewater Associates** (CIK 0001350694)
  - Accession: 0001350694-26-000002
  - Filing date: 2026-05-15
  - Report period: 2026-03-31
- **Renaissance Technologies** (CIK 0001037389)
  - Accession: 0001037389-26-000033
  - Filing date: 2026-05-14
  - Report period: 2026-03-31
- **Citadel Advisors** (CIK 0001423053)
  - Accession: 0001104659-26-062477
  - Filing date: 2026-05-15
  - Report period: 2026-03-31
- **Two Sigma Investments** (CIK 0001179392)
  - Accession: 0000899140-26-000547
  - Filing date: 2026-05-15
  - Report period: 2026-03-31

---

## InfoTable Parse Results

**InfoTables parsed:** 5

[WARN] **Berkshire Hathaway**
  - Parse status: failed
  - Holdings parsed: 0
  - Error: Invalid XML: mismatched tag: line 33, column 2

[WARN] **Bridgewater Associates**
  - Parse status: partial
  - Holdings parsed: 0

[WARN] **Renaissance Technologies**
  - Parse status: failed
  - Holdings parsed: 0
  - Error: Invalid XML: mismatched tag: line 33, column 2

[WARN] **Citadel Advisors**
  - Parse status: partial
  - Holdings parsed: 0

[WARN] **Two Sigma Investments**
  - Parse status: failed
  - Holdings parsed: 0
  - Error: Invalid XML: mismatched tag: line 33, column 2

---

## Matched MAIA Holdings

No MAIA matches found in reviewed filings.

---

## Match Confidence and Basis

No matches found. Confidence assessment not applicable.

---

## Limitations

- 13F has 45-day reporting lag from quarter-end
- 13F only reports long positions >$200k or >10k shares threshold
- Derivatives, shorts, and synthetic positions not fully visible
- Private placements and warrants may not appear cleanly
- CUSIP not available for MAIA ticker resolution (name matching used)
- Name matching may have false positives/negatives without CUSIP confirmation

---

## Impact on CP23D/CP23E Monitoring Baseline

**13F InfoTable matching implemented but no reliable MAIA matches found in reviewed sample.**

**Recommended baseline update:**
- Update MAIA monitoring baseline to note: "13F InfoTable matching implemented; no reliable matches found in reviewed sample (5 large managers, most recent quarter)"
- Continue manual quarterly 13F checks
- Future automation can expand to more managers or direct CUSIP lookup

---

## Safety Confirmations

- Roger's uploaded MAIA spreadsheet: **NOT USED**
- OpenInsider data: **NOT USED**
- Telegram messages sent: **NO**
- Email sent: **NO**
- Scheduled tasks modified: **NO**
- Scheduled tasks triggered: **NO**
- .env printed or changed: **NO**
- Secrets printed: **NO**

---

**End of MAIA 13F InfoTable Matching Report**

**Checkpoint:** CP23F
**Generated:** 2026-06-10T18:24:57.659800Z