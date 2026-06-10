# CP23G — MAIA Market Confirmation Manual Price/Volume Checklist Report

**Checkpoint:** CP23G
**Date:** 2026-06-10
**Status:** ✅ Complete

---

## Summary

CP23G successfully created a comprehensive manual monitoring framework to track whether MAIA's market price and volume behavior confirms, ignores, or contradicts the very strong insider buying evidence documented in the approved MAIA synthesis (CP23D).

**Key deliverables:**
1. Manual market confirmation checklist (markdown)
2. Structured JSON plan with baseline values, PM review triggers, and status labels
3. CSV observation template for weekly manual data entry
4. Baseline status report documenting current state and automation gaps
5. Python validation script
6. Comprehensive test suite (27 tests, all passing)

**Safety confirmation:**
- ✅ Report generation only (NO trading signals)
- ✅ NO Telegram messages sent
- ✅ NO email alerts sent
- ✅ NO scheduled task modification
- ✅ NO .env access
- ✅ NO OpenInsider spreadsheet usage
- ✅ NO buy/sell/hold recommendation language

---

## Files Created

### Documentation Files

1. **docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_checklist.md**
   - Comprehensive 12-section manual checklist
   - Weekly price/volume checks
   - Event-driven checks (Form 4, Form 144, 13D/G, clinical updates, financing, 10-Q/10-K)
   - 18 PM review triggers
   - Manual observation template instructions
   - Automation gap documentation
   - Safety confirmations

2. **docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_plan.json**
   - Structured JSON plan with baseline values
   - 10 weekly checklist items
   - 10 event-driven check definitions
   - 18 PM review triggers with thresholds
   - Manual observation template schema
   - 4 status labels (confirming, neutral, cautionary, requires_pm_review)
   - 9 data quality limitations
   - 8 future automation ideas
   - Safety flags (all correct)

3. **docs/sample_reports/maia_market_confirmation/MAIA_market_observation_template.csv**
   - 17-column CSV template for manual weekly observation entry
   - Example row with placeholder values clearly marked
   - Headers: date, closing_price, weekly_high, weekly_low, weekly_volume, avg_volume_reference, days_above_1_50, days_below_1_50, major_news, sec_filings, form4_activity, form144_activity, clinical_updates, financing_updates, price_volume_read, pm_review_triggered, notes

4. **docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_baseline_status.md**
   - Current approved MAIA research posture (strong insider-evidence / high clinical-timing uncertainty)
   - Market confirmation question framework
   - Known reference price: $1.50 March 2026 offering price
   - What is currently known (insider activity, capital structure, cash runway, 13F visibility, clinical programs)
   - What must be manually observed (price/volume data, event-driven observations, weekly tracking)
   - Top 10 PM review triggers
   - Current automation gaps
   - Confirmation report-only behavior

### Code Files

5. **scripts/maia_market_confirmation_checklist.py**
   - Python validation script (report generation only)
   - MAIAMarketConfirmationChecklist class with validation methods
   - Approved baseline values (134 purchases, 0 sales, $1.50 offering price)
   - 13 PM review triggers
   - 7 validation functions (JSON schema, baseline values, PM triggers, CSV template, no recommendation language, no secrets, safety flags)
   - NO Telegram/email/alert code
   - NO .env access
   - NO OpenInsider spreadsheet access

6. **tests/test_maia_market_confirmation_checklist.py**
   - 27 comprehensive tests covering all CP23G requirements
   - JSON schema validation
   - Baseline value checks (134 purchases, 0 sales, $1.50 offering price)
   - PM review trigger validation
   - CSV template validation
   - No buy/sell/hold recommendation language
   - No secrets
   - Safety flag validation
   - No Telegram/email/alert code validation
   - OpenInsider spreadsheet exclusion validation

---

## Files Modified

**None** — CP23G created new files only; no existing files were modified.

---

## Source Reports Reviewed

**Approved MAIA research baseline (CP21G/H/I/J, CP23A-Fix, CP23B-Fix3A, CP23D, CP23F-Fix):**

1. **docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.json**
   - Insider activity: 134 purchases, 0 sales, $4.92M value, 10 distinct buyers
   - Capital structure: March 2026 offering at $1.50, 60.67M shares outstanding
   - Cash runway: $34.4M cash, $5.31M quarterly burn, 19.4 months base runway
   - Clinical programs: THIO-104 Phase 3 (data timing NOT disclosed)
   - Evidence matrix conclusion: Strong insider-evidence / high clinical-timing uncertainty

2. **docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.md**
   - Verified insider evidence score: 100/100
   - Verified zero sales baseline
   - Verified critical unknown: THIO-104 data timing

3. **docs/sample_reports/maia_monitoring/MAIA_monitoring_plan.json**
   - Institutional visibility: 13F parser 60% success rate, 0 MAIA matches
   - Reviewed monitoring categories and baseline metrics

4. **docs/sample_reports/maia_monitoring/MAIA_monitoring_baseline_status.md**
   - Verified baseline status summary
   - Reviewed monitoring triggers

5. **docs/sample_reports/maia_13f/MAIA_13F_infotable_matching.json**
   - Verified 13F parser diagnostics (3 of 5 managers parsed, 0 MAIA matches)

6. **docs/sample_reports/maia_13f/MAIA_13F_infotable_matching_report.md**
   - Verified 13F matching results and limitations

7. **docs/checkpoints/reports/CP23F_fix_13f_parser_hardening_report.md**
   - Verified 13F parser hardening outcome
   - Parser success rate: 60%
   - Managers parsed: Bridgewater, Citadel, Two Sigma
   - Managers failed: Berkshire Hathaway, Renaissance Technologies (HTML wrappers)

---

## Baseline Values

**Insider Activity (CP21G/H/I/J):**
- Insider score: 100/100
- Open-market purchases: **134**
- Open-market sales: **0**
- Purchase value: **$4,921,437.58**
- Distinct buyers: **10**
- Buyer roles: CEO, CFO, CMO, CSO, Directors
- Latest purchase date: **2026-06-01**
- Purchase months: **21**
- Insider rating: Very Strong Insider Buying Evidence

**Capital Structure (CP23A-Fix, CP23B-Fix3A):**
- March 2026 offering price: **$1.50**
- Common shares outstanding (Q1 2026 10-Q): **60,671,491**
- Approximate fully diluted shares: **~86.86M**
- 13D/G filings: **0**
- Form 144 filings: **0**
- Beneficial ownership blockers: **4.99% or 9.99%**

**Cash Runway (CP23B-Fix3A Q1 2026 10-Q):**
- Cash balance (2026-03-31): **$34,413,110**
- Quarterly operating cash burn: **$5,311,328**
- Base runway: **19.4 months** from 2026-03-31

**Institutional Visibility (CP23F-Fix):**
- 13F parser success rate: **60%** (3 of 5 managers parsed)
- Managers successfully parsed: **3** (Bridgewater, Citadel, Two Sigma)
- Managers failed parsing: **2** (Berkshire Hathaway, Renaissance Technologies)
- Total holdings parsed: **21,128**
- MAIA matches found: **0**
- Status: **Partial implementation** — no reliable institutional holdings detected

**Clinical Programs (CP23B-Fix3A):**
- Primary program: **THIO-104**
- Phase: **Phase 3 pivotal trial**
- Indication: Advanced NSCLC (second-line+)
- FDA status: **Fast Track Designation**
- Data timing: **NOT DISCLOSED** (critical unknown)

**Evidence Matrix Conclusion (CP23D):**
> **Strong insider-evidence / high clinical-timing uncertainty profile**

---

## Market Reference Points

**Primary reference price:**
- **$1.50** — March 2026 public offering price

**Other reference levels (manual entry or integration required):**
- Current price: *(to be manually recorded)*
- 52-week high: *(to be manually recorded)*
- 52-week low: *(to be manually recorded)*
- Average daily volume (30-day): *(to be manually recorded)*
- Recent insider purchase prices: *(review Form 4 filings)*

**Note:** Live market data is **not currently integrated** in the project. Price and volume values are **manual-entry fields** until a verified public quote source is integrated.

---

## Weekly Checklist Summary

**10 weekly price/volume checks:**

1. **WK01:** Closing price relative to $1.50
2. **WK02:** Weekly high/low range
3. **WK03:** Price reaction to MAIA IR updates
4. **WK04:** Price reaction to new SEC filing
5. **WK05:** Sustained move or failed rally
6. **WK06:** Large single-day volume spike
7. **WK07:** Price gap up or gap down
8. **WK08:** Liquidity concern / very low volume
9. **WK09:** Spread concern (manual observation)
10. **WK10:** Weekly volume vs. recent average

**All weekly checks require manual entry** unless verified public quote source is integrated.

---

## Event-Driven Checklist Summary

**10 event-driven checks with confirmation levels:**

1. **EV01:** New Form 4 purchase
   - Confirming: New purchase + price holds above $1.50 on rising volume
   - Cautionary: New purchase + price breaks below $1.50 on heavy volume

2. **EV02:** First Form 4 sale
   - **PM review mandatory** (critical baseline change from 0-sales)

3. **EV03:** New Form 144 filing
   - **PM review mandatory** (first filing after 0-filings baseline)

4. **EV04:** New 13D/G filing
   - **PM review mandatory** (5%+ beneficial ownership disclosure)

5. **EV05:** New 13F match
   - **PM review mandatory** (first institutional match after 0-matches baseline)

6. **EV06:** New clinical update
   - Confirming: Positive update + price up on heavy volume
   - Cautionary: Negative update + price down on heavy volume

7. **EV07:** THIO-104 data timing disclosed
   - **PM review mandatory** (resolves critical unknown)

8. **EV08:** New financing filing
   - Confirming: Price holds above offering price on stable/rising volume
   - Cautionary: Price drops on heavy volume after financing filing

9. **EV09:** New 10-Q/10-K filing
   - Confirming: Strong cash, stable burn, no going-concern issues
   - Cautionary: Going-concern language added, burn accelerating, runway dropping

10. **EV10:** Cash runway drops below 12 months
    - **PM review mandatory** (financing need imminent)

---

## PM Review Triggers

**18 PM review triggers defined:**

### Price Triggers (6)

1. Price closes below $1.50 for 5 consecutive trading days
2. Price reclaims $1.50 and holds for 5 consecutive trading days on elevated volume
3. Price declines >25% in one week without company explanation
4. Price declines >50% from $1.50 offering price (reaches $0.75 or below)
5. Price surges >50% in one week on heavy volume

### Volume Triggers (2)

6. Single-day volume spike >3x recent average
7. Volume consistently <50% of recent average for 5+ days

### Insider Activity Triggers (3)

8. First Form 4 open-market sale
9. First Form 144 filing
10. Insider purchases stop for >90 days

### Institutional Triggers (2)

11. New 13D/G filing
12. New reliable 13F institutional match

### Clinical Triggers (3)

13. THIO-104 data timing disclosed
14. THIO-104 topline data released
15. Clinical trial update (enrollment complete, enrollment halted, etc.)

### Financial Triggers (3)

16. New financing filing
17. Cash runway drops below 12 months
18. Going-concern language change in 10-Q/10-K

---

## Manual Observation Template

**CSV template path:**
`docs/sample_reports/maia_market_confirmation/MAIA_market_observation_template.csv`

**17 columns:**
1. date
2. closing_price
3. weekly_high
4. weekly_low
5. weekly_volume
6. avg_volume_reference
7. days_above_1_50
8. days_below_1_50
9. major_news
10. sec_filings
11. form4_activity
12. form144_activity
13. clinical_updates
14. financing_updates
15. price_volume_read (confirming / neutral / cautionary / requires_pm_review)
16. pm_review_triggered (Yes / No)
17. notes

**Usage instructions:**
- **Weekly entry (minimum):** Record observations at least weekly (e.g., every Friday after market close)
- **Event-driven entry:** Record observations on the day of any PM review trigger event
- **Manual data collection:** If live quote source is integrated, values can be auto-populated. If not, manually record from public quote source.
- **Price/volume read:** Manually assess overall picture as confirming, neutral, cautionary, or requires_pm_review
- **PM review triggered:** Mark "Yes" if any PM review trigger condition is met; add trigger details in notes

---

## Automation Gaps

**CP23G provides manual monitoring only. 8 automation gaps identified:**

1. **Price/volume data integration**
   - Gap: No live quote source integrated
   - Manual workaround: Record weekly from public quote source
   - Future automation: Integrate Alpha Vantage, Yahoo Finance, or IEX Cloud API

2. **PM review trigger detection**
   - Gap: No automated calculation of 5-day trends, volume ratios, trigger conditions
   - Manual workaround: Calculate manually using CSV
   - Future automation: Script to detect triggers and flag for PM review

3. **Alert generation**
   - Gap: No Telegram/email alerts when PM review trigger is met
   - Manual workaround: PM manually reviews CSV weekly
   - Future automation: Alert generation (only if PM approves)

4. **Form 4 price correlation**
   - Gap: No automated matching of Form 4 transaction prices to market closing prices
   - Manual workaround: Manually review Form 4 filings
   - Future automation: Parse Form 4 and correlate transaction prices to daily closing prices

5. **13F institutional tracking**
   - Gap: 13F parser success rate is 60%; 2 of 5 large managers could not be parsed
   - Manual workaround: Quarterly manual review of unparsed manager filings
   - Future automation: Investigate non-standard InfoTable formats (HTML wrappers) and expand parser coverage

6. **Clinical milestone calendar**
   - Gap: No automated parsing of MAIA press releases or 10-Q/10-K for clinical milestone updates
   - Manual workaround: Manually review MAIA investor relations page and SEC filings
   - Future automation: Parse press releases and 10-Q/10-K for milestone disclosure updates

7. **Cash runway auto-update**
   - Gap: No automated parsing of latest 10-Q/10-K to update cash balance and burn rate
   - Manual workaround: Manually update from each new 10-Q/10-K
   - Future automation: Parse 10-Q/10-K XBRL data and auto-calculate runway

8. **Event-driven report generation**
   - Gap: No automated PDF summary when PM review trigger is met
   - Manual workaround: PM manually reviews CSV and creates summary
   - Future automation: Generate PDF summary with price charts and event timeline

---

## Safety Confirmations

**✅ All safety requirements met:**

1. **Report only:** ✅ This checklist generates NO trading signals
2. **No alerts:** ✅ This checklist sends NO Telegram messages or emails
3. **OpenInsider excluded:** ✅ Roger's OpenInsider spreadsheet was NOT used
4. **No scheduled task modification:** ✅ Windows scheduled tasks were NOT modified or triggered
5. **No .env access:** ✅ `.env` file and secrets were NOT printed or changed
6. **No recommendation language:** ✅ This checklist contains NO buy/sell/hold recommendations
7. **Source boundary enforced:** ✅ Only SEC EDGAR filings and project-approved reports were used
8. **Manual entry acknowledged:** ✅ Price/volume values are manual-entry fields unless verified public quote source is integrated

**Safety flags in JSON (all correct):**
```json
{
  "report_only": true,
  "alerts_generated": false,
  "openinsider_spreadsheet_used": false,
  "telegram_sent": false,
  "email_sent": false,
  "scheduled_tasks_modified": false,
  "env_printed_or_changed": false,
  "buy_sell_hold_language_used": false
}
```

---

## Test Results

**Test suite:** `tests/test_maia_market_confirmation_checklist.py`

**Tests created:** 27 tests

**Test coverage:**
1. ✅ JSON schema required keys
2. ✅ Baseline insider purchases equal 134
3. ✅ Baseline insider sales equal 0
4. ✅ Baseline offering price equals 1.50
5. ✅ PM review triggers include "below $1.50 for 5 days"
6. ✅ PM review triggers include "reclaims $1.50 for 5 days"
7. ✅ PM review triggers include ">3x volume"
8. ✅ PM review triggers include "first Form 4 sale"
9. ✅ PM review triggers include "Form 144"
10. ✅ PM review triggers include "new financing"
11. ✅ PM review triggers include "THIO-104 timing"
12. ✅ CSV template has required columns
13. ✅ No buy/sell/hold recommendation language
14. ✅ No secrets
15. ✅ Safety flags correct
16. ✅ No Telegram/email/alert code
17. ✅ OpenInsider spreadsheet not required
18. ✅ Status labels defined
19. ✅ Baseline 13F parser success rate (60%)
20. ✅ Baseline 13F MAIA matches found (0)
21. ✅ Baseline Form 13D/G filings (0)
22. ✅ Baseline Form 144 filings (0)
23. ✅ Baseline THIO-104 data timing ("Not disclosed")
24. ✅ Weekly checklist has manual_entry_required flags
25. ✅ Event-driven checks have confirmation_levels
26. ✅ Limitations include manual entry note
27. ✅ Future automation includes quote API integration idea

**Test result:**
```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.0.3, pluggy-1.6.0
27 passed in 0.06s
```

**All 27 tests passed** ✅

---

## Smoke Test

**Skipped** — CP23G is a manual monitoring tool only. No smoke test required because:
1. No live price/volume data integration (manual entry only)
2. No alert generation
3. No scheduled task modification
4. No Telegram/email
5. Production dual-channel pilot is active (CP22D) — skipping smoke test to avoid any chance of triggering alerts

The validation script can be run manually:
```powershell
.venv/Scripts/python.exe scripts/maia_market_confirmation_checklist.py --validate
```

---

## Secret Scan Result

**Secret scan executed:** ✅ Passed

**Patterns scanned:**
- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- SMTP_PASSWORD
- SMTP_USERNAME
- GMAIL_APP_PASSWORD
- sk-ant-
- ETHERSCAN_API_KEY
- SEC_API_IO_API_KEY
- BEGIN PRIVATE KEY
- password=
- token=
- chat_id=

**Result:** No secrets detected in CP23G files

**Note:** The patterns "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "SMTP_PASSWORD", "sk-ant-", and "ETHERSCAN_API_KEY" appear in the validation code (`scripts/maia_market_confirmation_checklist.py` and `tests/test_maia_market_confirmation_checklist.py`) as **pattern checks**, not actual secrets. These are the patterns the validation code **searches for** to ensure no secrets are present in reports. This is expected and safe.

---

## Validation Commands

**Python version:**
```
Python 3.11.9
```

**Git branch:**
```
main
```

**Git status before staging:**
```
?? docs/sample_reports/maia_market_confirmation/
?? scripts/maia_market_confirmation_checklist.py
?? tests/test_maia_market_confirmation_checklist.py
```

**Python compilation:**
```powershell
.venv/Scripts/python.exe -m py_compile scripts/maia_market_confirmation_checklist.py
```
✅ Compiled successfully (no errors)

**Pytest:**
```powershell
.venv/Scripts/python.exe -m pytest tests/test_maia_market_confirmation_checklist.py -v
```
✅ 27 tests passed

---

## Commit Hash

**Commit hash:** `fb2075f`

**Commit message:**
```
Add MAIA market confirmation checklist (CP23G)
```

**Files committed:**
- scripts/maia_market_confirmation_checklist.py
- docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_checklist.md
- docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_plan.json
- docs/sample_reports/maia_market_confirmation/MAIA_market_observation_template.csv
- docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_baseline_status.md
- tests/test_maia_market_confirmation_checklist.py

**Total:** 6 files created, 2,077 insertions

---

## Push Result

**Push result:** ✅ Successfully pushed to origin main

**Push output:**
```
To https://github.com/rogerfiske/Insider-Trading.git
   b2c0ade..fb2075f  main -> main
```

**Previous commit:** b2c0ade (CP23F-Fix — Harden 13F InfoTable parsing)
**Current commit:** fb2075f (CP23G — Add MAIA market confirmation checklist)

---

## Risks / Blockers

**No blockers.** CP23G completed successfully.

**Identified risks (informational only):**

1. **Manual data entry dependency**
   - Risk: Price/volume observations depend on manual weekly entry; prone to human error, delay, or gaps
   - Mitigation: Integrate verified public quote source (Alpha Vantage, Yahoo Finance, IEX Cloud) to auto-populate price/volume data

2. **PM review trigger detection is manual**
   - Risk: PM must manually calculate 5-day price trends, volume ratios, and trigger conditions; risk of missing triggers
   - Mitigation: Create automated trigger detection script to flag PM review conditions

3. **13F parser coverage is 60%**
   - Risk: 2 of 5 large managers (Berkshire Hathaway, Renaissance Technologies) could not be parsed due to non-standard InfoTable formats (HTML wrappers); institutional visibility remains partial
   - Mitigation: Investigate HTML table extraction methods to expand parser coverage beyond 60%

4. **THIO-104 data timing remains undisclosed**
   - Risk: Critical clinical catalyst timing is unknown; market confirmation analysis operates in a high-uncertainty environment
   - Mitigation: No technical mitigation available; this is a disclosure-dependent unknown; PM review trigger defined for when data timing is disclosed

5. **No institutional holdings detected**
   - Risk: 0 MAIA matches found in Q1 2026 13F sample among 3 successfully parsed large managers; institutional visibility is minimal
   - Mitigation: Quarterly 13F tracking; PM review trigger defined for first institutional match

---

## Recommended Next Step

**Recommended next checkpoint:** CP23H — MAIA monitoring packet PDF export and archive

**Alternative checkpoints:**
- CP23C — Generalize MAIA synthesis workflow to any ticker
- CP22E — Production dual-channel pilot monitoring after next normal Ross run

**PM discretion:** Choose next checkpoint based on priorities.

---

## Awaiting PM Approval

**CP23G is complete and ready for PM review.**

**Deliverables ready:**
1. ✅ Manual market confirmation checklist
2. ✅ Structured JSON plan
3. ✅ CSV observation template
4. ✅ Baseline status report
5. ✅ Python validation script
6. ✅ Test suite (27 tests, all passing)

**PM review questions:**
1. Is the PM review trigger list comprehensive, or should additional triggers be added?
2. Is the CSV observation template format suitable for weekly manual entry, or should it be adjusted?
3. Should a public quote API (Alpha Vantage, Yahoo Finance, IEX Cloud) be integrated to auto-populate price/volume data, or should manual entry continue?
4. Should automated PM review trigger detection be implemented as a priority, or should manual calculation continue?
5. Should the MAIA market confirmation checklist be incorporated into the MAIA monitoring pack (CP23E), or should it remain a standalone manual tool?

**Awaiting PM approval to proceed to next checkpoint.**

---

**END OF CP23G REPORT**
