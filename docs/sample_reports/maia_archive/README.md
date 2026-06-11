# MAIA Monitoring Packet Archive

**Ticker:** MAIA
**CIK:** 0001878313
**Company:** MAIA Biotechnology, Inc.
**Archive Generated:** 2026-06-10
**Approved Checkpoints:** CP23D through CP23G

---

## What This Archive Contains

This archive packages the complete approved MAIA research and monitoring artifacts from checkpoints CP23D (Full Synthesis), CP23E (Monitoring Pack), CP23F-Fix (13F Parser Hardening), and CP23G (Market Confirmation Checklist).

**Included artifacts:**

### Research & Synthesis Reports
1. **MAIA Full Synthesis Packet** (CP23D) — Comprehensive insider activity, capital structure, clinical programs, cash runway, and evidence matrix analysis
2. **Weekly Monitoring Checklist** (CP23E) — Structured monitoring workflow for tracking Form 4, Form 144, 13D/G, 13F, clinical updates, financing, and financial filings
3. **13F Institutional Holdings Report** (CP23F-Fix) — InfoTable parsing results with 60% parser success rate; no MAIA institutional matches found
4. **Market Confirmation Checklist** (CP23G) — Manual price/volume monitoring framework relative to $1.50 March 2026 offering price

### Checkpoint Reports
- CP23D_MAIA_full_synthesis_packet_report.md
- CP23E_MAIA_monitoring_pack_report.md
- CP23F_fix_13f_parser_hardening_report.md
- CP23G_MAIA_market_confirmation_checklist_report.md

### JSON Data
- MAIA_full_synthesis_packet.json
- MAIA_monitoring_plan.json
- MAIA_13F_infotable_matching.json
- MAIA_market_confirmation_plan.json

### Manual Templates
- MAIA_market_observation_template.csv — Weekly price/volume observation template

---

## Source Boundary

**Approved sources only:**
- SEC EDGAR filings (Form 4, Form 144, 13D/G, 13F-HR, 10-Q/10-K, S-1/S-3)
- MAIA official investor relations press releases
- MAIA official SEC/XBRL pages
- Project-approved reports: CP21G/H/I/J, CP23A-Fix, CP23B-Fix3A, CP23D, CP23E, CP23F-Fix, CP23G

**NOT permitted:**
- Roger's uploaded MAIA spreadsheet
- OpenInsider data supplied by Roger
- Paid/private/non-project data sources
- Message-board claims or uncited social media

---

## Approved Synthesis Posture

From CP23D Full Synthesis:

> **Strong insider-evidence / high clinical-timing uncertainty profile**

**Insider Activity:**
- **134 open-market purchases**, **0 sales** over 21 months
- **$4,921,437.58** total purchase value
- **10 distinct buyers** (CEO, CFO, CMO, CSO, Directors)
- **Latest purchase:** 2026-06-01
- **Insider score:** 100/100

**Capital Structure:**
- **March 2026 offering price:** $1.50
- **Common shares outstanding (Q1 2026 10-Q):** 60,671,491
- **Approximate fully diluted shares:** ~86.86M
- **13D/G filings:** 0
- **Form 144 filings:** 0

**Cash Runway (Q1 2026 10-Q):**
- **Cash:** $34,413,110 (as of 2026-03-31)
- **Quarterly operating cash burn:** $5,311,328
- **Base runway:** about 19.4 months from 2026-03-31

**Institutional Visibility (CP23F-Fix):**
- **13F parser success rate:** 60% (3 of 5 managers parsed)
- **MAIA matches found:** 0 in Q1 2026 sample
- **Status:** Partial implementation — no reliable institutional holdings detected

**Clinical Programs:**
- **THIO-104:** Phase 3 pivotal trial (advanced NSCLC, second-line+), FDA Fast Track designation
- **Data timing:** **NOT DISCLOSED** (critical unknown)

---

## Report-Only / No Investment Advice Statement

**⚠️ CRITICAL SAFETY NOTICE ⚠️**

This archive is for **research and evidence synthesis purposes only**.

**It is NOT investment advice.**
**It does NOT constitute a buy, sell, or hold recommendation.**
**It does NOT predict future stock performance.**

All reports, checklists, and monitoring frameworks document evidence patterns and identify conditions that warrant PM review. They do NOT direct trading actions.

Users must:
- Conduct independent due diligence
- Consult qualified financial, legal, and tax professionals
- Acknowledge that past insider buying does not guarantee future stock performance
- Understand that MAIA is a clinical-stage biotech with significant risks:
  - Unproven Phase 3 drug (THIO-104)
  - Undisclosed data timing (critical unknown)
  - Cash runway constraints (19.4 months base case from Q1 2026)
  - Dilution risk from future financing

---

## Safety Confirmations

**✅ All safety requirements met:**

1. **Report only:** ✅ This archive generates NO trading signals
2. **No alerts:** ✅ NO Telegram messages or emails sent during archive creation
3. **OpenInsider excluded:** ✅ Roger's OpenInsider spreadsheet was NOT used
4. **No scheduled task modification:** ✅ Windows scheduled tasks were NOT modified or triggered
5. **No .env access:** ✅ `.env` file and secrets were NOT printed or changed
6. **No secrets included:** ✅ Archive contains no API keys, tokens, passwords, or credentials
7. **Source boundary enforced:** ✅ Only SEC EDGAR filings and project-approved reports were used

---

## How to Use the Weekly Monitoring Checklist

**File:** `md/MAIA_weekly_monitoring_checklist.md`

**Purpose:** Structured weekly monitoring workflow to track MAIA-related SEC filings and events.

**Recommended usage:**

1. **Weekly review (minimum):** Every Monday morning, check SEC EDGAR for new MAIA filings from the previous week:
   - New Form 4 (insider purchases/sales)
   - New Form 144 (sale notices)
   - New 13D/G (5%+ beneficial ownership)
   - New 10-Q/10-K (quarterly/annual reports)
   - New S-1/S-3 (financing filings)
   - New 8-K (material events)

2. **Event-driven review:** When any filing is found:
   - Record filing details in monitoring log
   - Assess whether PM review trigger conditions are met (see checklist Section 7)
   - Flag for PM review if trigger conditions are present

3. **Monthly 13F review:** 45 days after each quarter-end:
   - Run 13F InfoTable matching script (if parser coverage improves beyond 60%)
   - Check for new institutional MAIA matches

4. **Clinical update tracking:**
   - Monitor MAIA investor relations page for press releases
   - Check for THIO-104 Phase 3 data timing disclosure (critical unknown)

**PM review triggers (from monitoring checklist):**
- First Form 4 open-market sale (baseline is 0 sales)
- First Form 144 filing (baseline is 0 filings)
- New 13D/G filing (baseline is 0 filings)
- New reliable 13F institutional match (baseline is 0 matches)
- THIO-104 data timing disclosed (resolves critical unknown)
- Cash runway drops below 12 months

---

## How to Use the Market Observation CSV

**File:** `csv/MAIA_market_observation_template.csv`

**Purpose:** Manual weekly price/volume observation template to track whether MAIA's market behavior confirms, ignores, or contradicts the strong insider buying evidence.

**Recommended usage:**

1. **Weekly entry (minimum):** Every Friday after market close, record:
   - Closing price
   - Weekly high/low
   - Weekly volume
   - Days above/below $1.50 (March 2026 offering price)
   - Any major news or SEC filings
   - Price/volume read (confirming / neutral / cautionary / requires_pm_review)

2. **Event-driven entry:** When any PM review trigger event occurs:
   - Record observations on the day of the event
   - Note price reaction to event (up / down / flat)
   - Note volume reaction (spike / average / low)
   - Mark PM review triggered as "Yes" if trigger condition is met

3. **Manual data collection:**
   - If live quote source is integrated: values can be auto-populated
   - If not: manually record price/volume from public quote source (Yahoo Finance, MarketWatch, brokerage platform)

4. **Interpretation:**
   - **Confirming:** Price holding above $1.50 on stable or rising volume
   - **Neutral:** Price stable around $1.50, no major volume change
   - **Cautionary:** Price trending below $1.50 on heavy volume, or very low liquidity
   - **Requires PM review:** Significant divergence from expected pattern or any PM review trigger condition met

**PM review triggers (from market confirmation checklist):**
- Price closes below $1.50 for 5 consecutive trading days
- Price declines >25% in one week without company explanation
- Price declines >50% from $1.50 (reaches $0.75 or below)
- Single-day volume spike >3x recent average
- First Form 4 open-market sale
- First Form 144 filing
- New financing filing
- Cash runway drops below 12 months

See `md/MAIA_market_confirmation_checklist.md` for full list of 18 PM review triggers.

---

## How to Interpret the 13F Partial-Visibility Limitation

**File:** `md/MAIA_13F_infotable_matching_report.md`

**Parser status (CP23F-Fix):**
- **Parser success rate:** 60% (3 of 5 large managers parsed successfully)
- **Managers successfully parsed:** Bridgewater Associates, Citadel Advisors, Two Sigma Investments
- **Managers failed parsing:** Berkshire Hathaway, Renaissance Technologies (non-standard InfoTable format — HTML wrappers)
- **Total holdings parsed:** 21,128 positions from 3 managers
- **MAIA matches found:** 0

**Interpretation:**

1. **No-match conclusion is scoped to successfully parsed filings only.**
   - The conclusion "no MAIA institutional matches found" applies to the 3 managers successfully parsed (Bridgewater, Citadel, Two Sigma).
   - It does NOT cover the 2 managers that failed parsing (Berkshire, Renaissance).

2. **60% parser success rate is a known limitation.**
   - Berkshire Hathaway and Renaissance Technologies use non-standard InfoTable formats (HTML wrappers instead of XML).
   - The parser currently handles standard XML InfoTables only.
   - Future parser improvements may expand coverage beyond 60%.

3. **13F-HR filings have inherent limitations regardless of parser success:**
   - 45-day lag from quarter-end (holdings data is stale)
   - Only reports long positions >$200k or >10k shares threshold
   - Derivatives, shorts, and synthetic positions not fully visible
   - Managers can file amendments after initial deadline

4. **Quarterly 13F monitoring is still valuable:**
   - If parser coverage improves, more managers can be scanned
   - First institutional match (if/when found) is a PM review trigger
   - Institutional entry can signal market confidence in MAIA

**Recommended action:**
- Continue quarterly 13F monitoring (45 days post quarter-end)
- Manually review unparsed manager filings (Berkshire, Renaissance) if resources permit
- Flag first MAIA institutional match as PM review trigger

---

## File List

### Markdown Reports (md/)
- MAIA_full_synthesis_packet.md
- MAIA_weekly_monitoring_checklist.md
- MAIA_monitoring_baseline_status.md
- MAIA_13F_infotable_matching_report.md
- MAIA_market_confirmation_checklist.md
- MAIA_market_confirmation_baseline_status.md
- CP23D_MAIA_full_synthesis_packet_report.md
- CP23E_MAIA_monitoring_pack_report.md
- CP23F_fix_13f_parser_hardening_report.md
- CP23G_MAIA_market_confirmation_checklist_report.md

### JSON Data (json/)
- MAIA_full_synthesis_packet.json
- MAIA_monitoring_plan.json
- MAIA_13F_infotable_matching.json
- MAIA_market_confirmation_plan.json

### CSV Templates (csv/)
- MAIA_market_observation_template.csv

### PDF Reports (pdf/)
**PDF export unavailable** — local markdown-to-PDF tools (pandoc, wkhtmltopdf) not installed.

**Manual PDF export instructions:**

If you need PDF versions of the markdown reports, you can export them manually using one of these methods:

1. **Using pandoc (recommended):**
   ```bash
   # Install pandoc first: https://pandoc.org/installing.html
   pandoc md/MAIA_full_synthesis_packet.md -o pdf/MAIA_full_synthesis_packet.pdf --pdf-engine=xelatex
   pandoc md/MAIA_weekly_monitoring_checklist.md -o pdf/MAIA_weekly_monitoring_checklist.pdf --pdf-engine=xelatex
   pandoc md/MAIA_monitoring_baseline_status.md -o pdf/MAIA_monitoring_baseline_status.pdf --pdf-engine=xelatex
   pandoc md/MAIA_13F_infotable_matching_report.md -o pdf/MAIA_13F_infotable_matching_report.pdf --pdf-engine=xelatex
   pandoc md/MAIA_market_confirmation_checklist.md -o pdf/MAIA_market_confirmation_checklist.pdf --pdf-engine=xelatex
   pandoc md/MAIA_market_confirmation_baseline_status.md -o pdf/MAIA_market_confirmation_baseline_status.pdf --pdf-engine=xelatex
   pandoc md/CP23D_MAIA_full_synthesis_packet_report.md -o pdf/CP23D_MAIA_full_synthesis_packet_report.pdf --pdf-engine=xelatex
   pandoc md/CP23E_MAIA_monitoring_pack_report.md -o pdf/CP23E_MAIA_monitoring_pack_report.pdf --pdf-engine=xelatex
   pandoc md/CP23F_fix_13f_parser_hardening_report.md -o pdf/CP23F_fix_13f_parser_hardening_report.pdf --pdf-engine=xelatex
   pandoc md/CP23G_MAIA_market_confirmation_checklist_report.md -o pdf/CP23G_MAIA_market_confirmation_checklist_report.pdf --pdf-engine=xelatex
   ```

2. **Using Markdown editors with PDF export:**
   - Typora, Marked 2 (macOS), or Visual Studio Code with Markdown PDF extension

3. **Using browser print-to-PDF:**
   - Open markdown files in VS Code or GitHub
   - Use browser print function and select "Save as PDF"

---

## Archive Structure

```text
maia_archive/
├── README.md (this file)
├── MAIA_archive_manifest.json (artifact manifest with checksums)
├── MAIA_archive_index.md (PM-readable artifact index)
├── md/ (markdown reports)
│   ├── MAIA_full_synthesis_packet.md
│   ├── MAIA_weekly_monitoring_checklist.md
│   ├── MAIA_monitoring_baseline_status.md
│   ├── MAIA_13F_infotable_matching_report.md
│   ├── MAIA_market_confirmation_checklist.md
│   ├── MAIA_market_confirmation_baseline_status.md
│   ├── CP23D_MAIA_full_synthesis_packet_report.md
│   ├── CP23E_MAIA_monitoring_pack_report.md
│   ├── CP23F_fix_13f_parser_hardening_report.md
│   └── CP23G_MAIA_market_confirmation_checklist_report.md
├── json/ (JSON data)
│   ├── MAIA_full_synthesis_packet.json
│   ├── MAIA_monitoring_plan.json
│   ├── MAIA_13F_infotable_matching.json
│   └── MAIA_market_confirmation_plan.json
├── csv/ (manual templates)
│   └── MAIA_market_observation_template.csv
└── pdf/ (empty — PDF tools not available; see manual export instructions above)
```

---

## Date Generated

**Archive Created:** 2026-06-10
**Checkpoints Covered:** CP23D (2026-06-09), CP23E (2026-06-09), CP23F-Fix (2026-06-10), CP23G (2026-06-10)
**Approved Commits:** (see MAIA_archive_manifest.json for commit hashes)

---

## Questions or Issues

For questions about this archive or MAIA research methodology, review:
1. Checkpoint reports in `md/` directory (CP23D, CP23E, CP23F-Fix, CP23G)
2. Archive manifest: `MAIA_archive_manifest.json`
3. Archive index: `MAIA_archive_index.md`

---

**END OF README**
