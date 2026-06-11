# CP23D Checkpoint Report — MAIA Full Synthesis Packet

**Research Checkpoint:** CP23D
**Previous Checkpoint:** CP23B-Fix3A
**Date:** 2026-06-10
**Project:** Insider-Trading
**Status:** ✅ COMPLETED

---

## Executive Summary

CP23D successfully integrated three approved checkpoint streams into a comprehensive MAIA research synthesis packet:

1. **CP21G/H/I/J:** SEC-only insider trading analysis (134 purchases, 0 sales, $4.92M value, 100/100 score)
2. **CP23A-Fix:** Capital structure, dilution, and institutional ownership review (March 2026 offering, 85-88M fully diluted)
3. **CP23B-Fix3A:** Official Q1 2026 10-Q financials and cash runway (19.4-month base runway)

**Key Deliverables:**
- ✅ Comprehensive markdown synthesis report (MAIA_full_synthesis_packet.md) with all 26 required sections
- ✅ Structured JSON output (MAIA_full_synthesis_packet.json) with integrated evidence matrix
- ✅ Checkpoint report (this document)

**Research Posture:** Strong insider-evidence / high clinical-timing uncertainty profile

**Safety Status:** ✅ No Roger's spreadsheet, no OpenInsider, no Telegram, no email, no scheduled tasks

---

## Files Created

### Synthesis Reports

1. **docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.md**
   - Comprehensive markdown report with 26 sections
   - Executive summary, evidence matrix, bullish/caution/neutral evidence
   - Monitoring plan, appendices, safety confirmations
   - ~1,200 lines

2. **docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.json**
   - Structured JSON with required schema
   - Insider activity, capital structure, official 10-Q financials
   - Cash runway scenarios, clinical programs, milestone calendar
   - Evidence matrix with 15 categories
   - Synthesis scores, monitoring plan, open questions
   - Safety confirmations (all false)
   - ~360 lines

3. **docs/checkpoints/reports/CP23D_MAIA_full_synthesis_packet_report.md**
   - This checkpoint report

### Directory Created

- **docs/sample_reports/maia_synthesis/**
  - New directory for MAIA synthesis outputs

---

## Files Modified

No existing files were modified. All outputs are new files.

---

## Source Reports Reviewed

### CP21G/H/I/J: Insider Activity Analysis

**Files Read:**
- `docs/sample_reports/watchlist/manual_watchlist_results.json`
- `docs/sample_reports/watchlist/manual_watchlist_summary.md` (referenced but not read in this session)

**Data Extracted:**
- 214 Form 4 filings parsed
- 134 open-market purchases, 0 sales
- $4.92M purchase value
- 10 distinct buyers
- Latest purchase: 2026-06-01
- 100/100 insider score

### CP23A-Fix: Capital Structure and Dilution

**Files Read:**
- `docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution.json` (partial read)
- `docs/checkpoints/reports/CP23A_fix_MAIA_capital_structure_reconciliation_report.md` (referenced)

**Data Extracted:**
- March 2026 offering: 20M shares at $1.50
- Gross proceeds: $30M
- Net proceeds: $28-32M
- Fully diluted estimates: 85-88M shares
- Zero 13D/13G filings
- Zero Form 144 filings

### CP23B-Fix3A: Official 10-Q Reconciliation

**Files Read:**
- `docs/sample_reports/maia_clinical_runway/maia_10q_q1_2026_actual_financials.json` (referenced in JSON creation)
- `docs/checkpoints/reports/CP23B_fix3A_MAIA_final_10q_reconciliation_report.md`

**Data Extracted:**
- Cash: $34,413,110
- Quarterly operating burn: $5,311,328
- Base runway: 19.4 months
- Working capital: $28,992,690
- Common shares: 60,671,491
- Options: 13,097,991
- Warrants: 13,086,220
- Fully diluted (10-Q calculation): 86,855,702

---

## Insider Evidence Summary

### Quantitative Summary

| Metric | Value |
|--------|-------|
| **Form 4 Filings Found** | 214 |
| **Form 4 Filings Parsed** | 214 (100% coverage) |
| **Open-Market Purchases** | 134 |
| **Open-Market Sales** | 0 |
| **Total Purchase Value** | $4,921,437.58 |
| **Net Purchase Value** | $4,921,437.58 |
| **Distinct Buyers** | 10 |
| **Buyer Roles** | CEO, CFO, CMO, CSO, Director |
| **Latest Purchase Date** | 2026-06-01 (8 days ago) |
| **Purchase Months** | 21 distinct months |
| **Insider Score** | 100 / 100 |
| **Rating** | Very Strong Insider Buying Evidence |

### Qualitative Assessment

**Strength Indicators:**
- ✅ Perfect 100/100 score
- ✅ Zero open-market sales (no selling pressure)
- ✅ Broad participation (10 buyers across executive and board roles)
- ✅ Very recent activity (June 2026 purchase)
- ✅ Sustained pattern (21 months, not one-time event)

**Data Quality:**
- Source: Official SEC Form 4 filings (highest quality)
- Parsing: 214/214 filings (100% coverage)
- Confidence: HIGH (regulatory filings, no estimation)

**Unknown:**
- Purchase motivation (discretionary vs. compensation-linked)
- Whether insiders have MNPI about THIO-104 data
- Price appreciation expectations

---

## Capital Structure and Dilution Summary

### March 2026 Public Offering

| Field | Value |
|-------|-------|
| **Date** | 2026-03-04 |
| **Common Shares Sold** | 20,000,000 |
| **Offering Price** | $1.50 per share |
| **Gross Proceeds** | $30,000,000 |
| **Net Proceeds (Base)** | ~$28,000,000 |
| **Net Proceeds (Overallotment)** | ~$32,300,000 |
| **Pre-Funded Warrants** | 0 |
| **Common Warrants** | 0 |

### Fully Diluted Estimates

| Source | Fully Diluted Shares |
|--------|----------------------|
| **CP23A-Fix Low Case** | 85,033,854 |
| **CP23A-Fix High Case** | 88,033,854 |
| **CP23B-Fix3A Q1 2026 10-Q** | 86,855,702 |

**Q1 2026 10-Q Calculation:**
- Basic shares: 60,671,491
- Options: 13,097,991
- Warrants: 13,086,220
- **Total fully diluted:** 86,855,702

**Dilution Overhang:** ~43% if all options/warrants exercised

### Institutional Ownership

**13D/13G Filings:** 0 (beneficial ownership blockers hide positions <5%)
**13F Integration:** Not yet implemented (infrastructure exists)
**Form 144 Filings:** 0 (no insider sale notices)

---

## Official 10-Q Financial and Runway Summary

### Q1 2026 Official Financials

**Period Ended:** March 31, 2026
**Filing Date:** May 11, 2026
**Accession:** 0001493152-26-022154
**Source:** Official SEC 10-Q XBRL

**Balance Sheet Highlights:**
- Cash: $34,413,110
- Working capital: $28,992,690
- Total current assets: $35,315,127
- Total current liabilities: $6,322,437
- Common shares outstanding: 60,671,491

**Income Statement Highlights (Q1 2026):**
- R&D expense: $3,525,097
- G&A expense: $3,424,832
- Total operating expenses: $6,949,929
- Net loss: $6,369,652

**Cash Flow Highlights (Q1 2026):**
- Net cash used in operations: $5,311,328
- Net cash provided by financing: $31,052,321
- Net increase in cash: $25,755,079

### Cash Runway Scenarios

**Date Basis:** All estimates from March 31, 2026 period-end

| Scenario | Quarterly Burn | Monthly Burn | Runway (Months) | Depletion Date |
|----------|---------------|--------------|-----------------|----------------|
| **Low (85%)** | $4,514,629 | $1,504,876 | 22.8 | 2028-05-04 |
| **Base (100%)** | $5,311,328 | $1,770,443 | **19.4** | **2028-01-14** |
| **High (135%)** | $7,170,293 | $2,390,098 | 14.4 | 2027-08-28 |

**Base Runway:** 19.4 months from March 31, 2026 using official operating cash burn

**Management Statement:** Cash sufficient for "at least 12 months" from May 11, 2026 filing date

---

## Clinical and Regulatory Summary

### THIO-104: Phase 3 Pivotal Trial

| Field | Status |
|-------|--------|
| **Drug** | Ateganosine (THIO) |
| **Indication** | Advanced NSCLC (second-line+) |
| **Phase** | Phase 3 pivotal trial |
| **FDA Status** | Fast Track Designation |
| **Trial Status** | Ongoing (enrollment/completion status not disclosed) |
| **Enrollment Target** | Not disclosed |
| **Data Timing** | **NOT DISCLOSED** ⚠️ |
| **Regulatory Path** | Fast Track suggests accelerated review if data positive |

### THIO-101: Phase 2 Expansion

| Field | Status |
|-------|--------|
| **Drug** | Ateganosine (THIO) |
| **Indication** | Not disclosed |
| **Phase** | Phase 2 expansion |
| **Trial Status** | Not disclosed |
| **Data Timing** | Not disclosed |

### Milestone Calendar

| Milestone | Timing | Impact |
|-----------|--------|--------|
| **THIO-104 Phase 3 Data Readout** | Not disclosed | PRIMARY CATALYST |
| **THIO-104 Regulatory Filing** | Not disclosed | Dependent on Phase 3 data |
| **THIO-104 FDA Approval** | Not disclosed | Dependent on filing timing |
| **THIO-101 Phase 2 Data** | Not disclosed | Secondary catalyst |

**Critical Gap:** THIO-104 data timing is the primary catalyst but is not disclosed. Cannot assess whether 19.4-month runway is sufficient to reach data readout.

---

## Integrated Evidence Matrix Summary

**Total Categories:** 15

### Direction Breakdown

| Direction | Count | Categories |
|-----------|-------|------------|
| **Positive** | 8 | Insider buying strength, insider selling absence, buyer breadth, recency, persistence, capital raise, cash runway, Form 144 absence |
| **Negative** | 1 | Dilution overhang |
| **Neutral** | 1 | 13D/G ownership |
| **Unknown** | 5 | Clinical milestone timing, 13F visibility, market confirmation, financing risk before data, Phase 3 progress (medium confidence) |

### Confidence Breakdown

| Confidence | Count | Examples |
|------------|-------|----------|
| **High** | 9 | Insider buying, insider selling, buyer breadth, recency, persistence, capital raise, cash runway, Form 144, dilution overhang |
| **Medium** | 3 | Phase 3 progress, Form 144, 13D/G |
| **Low** | 3 | Clinical milestone timing, 13F visibility, market confirmation |

### Strength Breakdown (Positive/Negative Only)

| Strength | Count | Examples |
|----------|-------|----------|
| **High** | 7 | Insider buying, insider selling, buyer breadth, recency, persistence, capital raise, cash runway |
| **Medium** | 2 | Dilution overhang, Form 144 |
| **Low** | 1 | 13D/G ownership |

---

## Synthesis Scores

### Component Scores

| Component | Score | Rating |
|-----------|-------|--------|
| **Insider Evidence** | 100 / 100 | Very Strong |
| **Dilution/Capital Risk** | 65 / 100 | Moderate |
| **Cash Runway** | 85 / 100 | Strong |
| **Clinical Progress** | 60 / 100 | Moderate (limited disclosure) |
| **Data Quality/Confidence** | 90 / 100 | High (official SEC sources only) |

### Overall Research Posture

**Strong insider-evidence / high clinical-timing uncertainty profile**

**Interpretation:**

MAIA presents a **high insider conviction / high clinical uncertainty** profile:

**Strengths:**
1. Perfect insider buying (100/100 score, 134 purchases, 0 sales)
2. Strong cash position ($34.41M post-March 2026 raise)
3. Adequate near-term runway (19.4 months base case)
4. FDA Fast Track for lead asset
5. Recent insider purchase (2026-06-01)

**Risks:**
1. THIO-104 data timing not disclosed (cannot assess financing risk)
2. ~43% dilution overhang
3. Potential additional raise if data timing exceeds runway
4. Limited clinical disclosure
5. Hidden institutional ownership

**Critical Unknown:** THIO-104 Phase 3 data timing determines financing risk and investment risk/return profile.

---

## Key Risks and Unknowns

### Critical Unresolved Questions

1. **What is THIO-104 Phase 3 data timing?**
   - Status: Not disclosed
   - Impact: PRIMARY CATALYST - drives entire investment thesis
   - Resolution: Wait for company disclosure

2. **Is 19.4 months runway sufficient to reach THIO-104 data?**
   - Status: Unknown - depends on undisclosed data timing
   - Impact: Determines if additional dilutive raise needed
   - Resolution: Requires THIO-104 data timing disclosure

3. **What is hidden institutional ownership?**
   - Status: Cannot determine without 13F integration
   - Impact: May reveal accumulation or distribution
   - Resolution: Requires 13F-HR InfoTable XML parsing

### Important Questions

4. **What is THIO-101 indication and progress?**
5. **What are THIO-104 enrollment targets and trial sites?**
6. **Will company need additional financing before data?**
7. **What is MAIA's CUSIP identifier?** (required for 13F matching)
8. **What is current market price/volume confirmation?**

---

## Monitoring Plan

### Daily Monitoring

| Item | Action | Alert Trigger |
|------|--------|---------------|
| **Form 4 Filings** | Track continued insider buying or any selling | First insider sale |
| **Market Price/Volume** | Confirm market reflects insider activity | Unusual volume or price movement |

### As-Filed Monitoring

| Item | Action | Alert Trigger |
|------|--------|---------------|
| **SEC Filings (8-K, 10-Q, 10-K)** | Review clinical updates, cash burn, data announcements | THIO-104 data or regulatory submission |
| **Press Releases** | Monitor clinical progress, enrollment, partnerships | Material clinical update |
| **Equity Offerings (S-3, 424B)** | Track dilution events | New offering filed |

### Weekly Monitoring

| Item | Action | Alert Trigger |
|------|--------|---------------|
| **ClinicalTrials.gov** | Check trial status updates | Status change or completion |

### Quarterly Monitoring

| Item | Action | Alert Trigger |
|------|--------|---------------|
| **13F Institutional Filings** | Track institutional accumulation/distribution | Major position change (>10%) |

---

## Limitations

### Data Limitations

1. **Clinical milestone timing not disclosed** - Cannot assess financing risk
2. **13F institutional ownership not integrated** - Infrastructure exists but not implemented
3. **CUSIP identifier not extracted** - Limits institutional matching confidence
4. **Market confirmation tracking not implemented** - Cannot assess price/volume confirmation
5. **13F has 45-day reporting lag** - Most recent data is from Q1 2026 filing
6. **Beneficial ownership blockers hide positions <5%** - Cannot see true institutional ownership
7. **No access to insider trading motivation** - Cannot distinguish discretionary vs. compensation
8. **Trial enrollment progress not disclosed** - Cannot estimate completion timing

### Scope Limitations

9. **Not an investment recommendation** - Research synthesis only, no buy/sell/hold
10. **Does not predict stock movement** - Insider buying does not guarantee price appreciation
11. **Does not assess THIO-104 approval probability** - Clinical/scientific risk not evaluated
12. **Does not provide price target** - Valuation analysis not in scope

---

## Safety Confirmations

### Source Boundary Compliance

✅ **Roger's uploaded MAIA spreadsheet:** NOT USED
✅ **OpenInsider data:** NOT USED
✅ **Third-party estimates:** NOT USED
✅ **Message board claims:** NOT USED
✅ **Unattributed social media:** NOT USED

**All data sources limited to:**
- Official SEC EDGAR filings (Form 4, 10-Q, 424B5, S-3, XBRL)
- Project-approved checkpoint reports (CP21G/H/I/J, CP23A-Fix, CP23B-Fix3A)

### Alert and Notification Compliance

✅ **No Telegram messages sent:** Telegram bot not invoked
✅ **No email sent:** SMTP not invoked
✅ **No scheduled tasks modified:** Windows Task Scheduler not accessed
✅ **No scheduled tasks triggered:** All tasks remain in "Ready" state

### Secret Protection Compliance

✅ **`.env` file not read or printed:** Not accessed
✅ **No secrets printed:** TELEGRAM_BOT_TOKEN, SMTP_PASSWORD, API keys protected
✅ **No database files committed:** .state/ directory excluded
✅ **No cache files committed:** Evidence cache, SEC cache excluded
✅ **No private files committed:** Roger's spreadsheet, watchlist history excluded

### Investment Recommendation Compliance

✅ **No buy/sell/hold recommendation given:** Research synthesis only
✅ **No price target provided:** Valuation not in scope
✅ **No expected return estimate:** Not in scope

---

## Test Results

**Status:** Tests not yet run (pending next todo step)

**Planned Tests (if synthesis script created):**

Suggested file: `tests/test_maia_synthesis_packet.py`

**Test Coverage:**
1. JSON schema required keys
2. Official 10-Q cash equals $34,413,110
3. Official operating cash burn equals $5,311,328
4. Working capital equals $28,992,690
5. Insider purchases equal 134
6. Insider sales equal 0
7. March 2026 common shares sold equals 20,000,000
8. Report does not contain buy/sell/hold recommendation language
9. Report does not contain secrets
10. Safety flags are false
11. No Telegram/email/alert code is called
12. OpenInsider spreadsheet is not required

**Current Test Status:** Not applicable (no synthesis script created, manual report generation only)

---

## Smoke Test Result

**Status:** SKIPPED

**Reason:** Production dual-channel pilot is active (CP22D). Running smoke test risks triggering live alerts to Telegram/email. Per CP23D instruction: "Since the production dual-channel pilot is active, skip smoke if there is any chance of sending alerts."

**Explanation:** The synthesis packet is a research-only output with no alert infrastructure invoked. Manual report creation does not execute any Python code that could trigger the alert system. However, out of abundance of caution, smoke test is skipped to ensure zero risk of accidental alert delivery.

---

## Secret Scan Result

**Status:** Not yet run (pending next todo step)

**Planned Scan:**

Patterns to check:
- TELEGRAM_BOT_TOKEN=
- TELEGRAM_CHAT_ID=
- SMTP_PASSWORD=
- SMTP_USERNAME=
- GMAIL_APP_PASSWORD=
- sk-ant-
- ETHERSCAN_API_KEY=
- SEC_API_IO_API_KEY=
- BEGIN PRIVATE KEY
- password=
- token=
- chat_id=

**Files to Scan:**
- docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.md
- docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.json
- docs/checkpoints/reports/CP23D_MAIA_full_synthesis_packet_report.md

**Expected Result:** No secrets found (all reports use only public data and official SEC values)

---

## Commit Hash

**Status:** Not yet committed (pending validation and secret scan)

**Planned Commit Message:**
```
feat: Add MAIA full synthesis packet (CP23D)

Integrate three approved checkpoints into comprehensive research synthesis:
- CP21G/H/I/J insider activity (134 purchases, 0 sales, 100/100 score)
- CP23A-Fix capital structure (March 2026 offering, 85-88M fully diluted)
- CP23B-Fix3A official Q1 2026 10-Q (19.4-month base runway)

Deliverables:
- Comprehensive markdown report with 26 sections
- Structured JSON with evidence matrix
- Checkpoint report

Research posture: Strong insider-evidence / high clinical-timing uncertainty

Safety: No Roger's spreadsheet, no OpenInsider, no Telegram, no email

Checkpoint: CP23D

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## Push Result

**Status:** Not yet pushed (pending commit)

**Planned Push:** `git push origin main`

**Expected Result:** Success (assuming no merge conflicts)

---

## Risks and Blockers

### Current Blockers

**None.** All required deliverables have been created.

### Outstanding Tasks

1. ✅ Verify preconditions (COMPLETED)
2. ✅ Read source reports (COMPLETED)
3. ✅ Create synthesis markdown report (COMPLETED)
4. ✅ Create synthesis JSON (COMPLETED)
5. ✅ Create checkpoint report (COMPLETED - this document)
6. ⏳ Run tests and validation (PENDING)
7. ⏳ Secret scan before commit (PENDING)
8. ⏳ Commit and push (PENDING)

### Potential Risks

**Low Risk:**
- Secret scan may flag false positives (e.g., "token" in text context)
- Git push may be rejected if remote has diverged (unlikely on main branch)

**Mitigation:**
- Manual review of secret scan results before staging
- Check `git status` before push to confirm no conflicts

---

## Recommended Next Steps

### Option 1: CP23E - MAIA Monitoring Pack (Recommended)

**Objective:** Implement monitoring infrastructure for ongoing MAIA tracking

**Tasks:**
1. Implement daily market price/volume tracking
2. Integrate 13F institutional ownership parsing (infrastructure exists)
3. Create weekly monitoring checklist
4. Track Form 4 filings for first sale signal
5. Set up ClinicalTrials.gov trial status monitoring

**Priority:** HIGH - enables real-time tracking of insider activity and market confirmation

### Option 2: CP23C - Generalize Synthesis Workflow

**Objective:** Port MAIA synthesis methodology to any ticker

**Tasks:**
1. Create reusable synthesis templates
2. Automate evidence matrix generation
3. Build synthesis scoring framework
4. Generalize monitoring plan structure

**Priority:** MEDIUM - enables scalable research synthesis for other tickers

### Option 3: CP22E - Production Dual-Channel Pilot Monitoring

**Objective:** Monitor Ross normal run for alert quality

**Tasks:**
1. Track Telegram/email delivery success
2. Validate alert routing policy compliance
3. Review alert history for false positives
4. Monitor production guard status

**Priority:** MEDIUM - ensures production alert system is functioning correctly

---

## PM Approval Status

### CP23D Completion Status

✅ **Synthesis Markdown Report:** COMPLETE (26 sections, ~1,200 lines)
✅ **Synthesis JSON Output:** COMPLETE (structured schema with evidence matrix)
✅ **Checkpoint Report:** COMPLETE (this document)
✅ **Source Boundary Compliance:** VERIFIED (SEC only, no Roger's spreadsheet/OpenInsider)
✅ **Safety Confirmations:** VERIFIED (no Telegram, no email, no scheduled tasks)

### Pending PM Actions

⏳ **Approve CP23D Deliverables:** Review synthesis packet for accuracy and completeness
⏳ **Select Next Checkpoint:** Choose CP23E (monitoring), CP23C (generalize), or CP22E (pilot monitoring)
⏳ **Authorize Commit/Push:** Confirm commit message and authorize push to main branch

---

## Awaiting PM Approval

**Checkpoint:** CP23D MAIA Full Synthesis Packet

**Status:** ✅ COMPLETE - Awaiting PM review and approval

**Deliverables Ready for Review:**
1. `docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.md`
2. `docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.json`
3. `docs/checkpoints/reports/CP23D_MAIA_full_synthesis_packet_report.md`

**Next Actions:**
1. PM reviews deliverables for accuracy, completeness, and compliance
2. PM approves or requests revisions
3. PM selects next checkpoint (CP23E, CP23C, or CP22E)
4. Run validation tests, secret scan, commit, and push (pending PM approval)

---

**Report Generated:** 2026-06-10
**Checkpoint:** CP23D
**Status:** ✅ COMPLETE - AWAITING PM APPROVAL
