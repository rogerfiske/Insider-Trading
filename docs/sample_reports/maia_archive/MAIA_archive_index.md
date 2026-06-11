# MAIA Monitoring Packet Archive Index

**Archive Generated:** 2026-06-10
**Approved Checkpoints:** CP23D through CP23G

---

## Artifact Index

| Artifact | Type | Original Path | Archive Path | Purpose | Status |
|----------|------|---------------|--------------|---------|--------|
| **MAIA Full Synthesis Packet** | markdown | docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.md | md/MAIA_full_synthesis_packet.md | Comprehensive insider activity, capital structure, clinical programs, cash runway, and evidence matrix analysis (CP23D) | approved |
| **MAIA Full Synthesis Packet (JSON)** | json | docs/sample_reports/maia_synthesis/MAIA_full_synthesis_packet.json | json/MAIA_full_synthesis_packet.json | Machine-readable synthesis data (CP23D) | approved |
| **MAIA Weekly Monitoring Checklist** | markdown | docs/sample_reports/maia_monitoring/MAIA_weekly_monitoring_checklist.md | md/MAIA_weekly_monitoring_checklist.md | Structured monitoring workflow for tracking Form 4, Form 144, 13D/G, 13F, clinical updates, financing, and financial filings (CP23E) | approved |
| **MAIA Monitoring Plan (JSON)** | json | docs/sample_reports/maia_monitoring/MAIA_monitoring_plan.json | json/MAIA_monitoring_plan.json | Machine-readable monitoring plan data (CP23E) | approved |
| **MAIA Monitoring Baseline Status** | markdown | docs/sample_reports/maia_monitoring/MAIA_monitoring_baseline_status.md | md/MAIA_monitoring_baseline_status.md | Current monitoring baseline and approval status (CP23E) | approved |
| **MAIA 13F InfoTable Matching Report** | markdown | docs/sample_reports/maia_13f/MAIA_13F_infotable_matching_report.md | md/MAIA_13F_infotable_matching_report.md | 13F institutional holdings parsing results with 60% parser success rate; no MAIA matches found (CP23F-Fix) | approved with limitation |
| **MAIA 13F InfoTable Matching (JSON)** | json | docs/sample_reports/maia_13f/MAIA_13F_infotable_matching.json | json/MAIA_13F_infotable_matching.json | Machine-readable 13F matching data and parser diagnostics (CP23F-Fix) | approved with limitation |
| **MAIA Market Confirmation Checklist** | markdown | docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_checklist.md | md/MAIA_market_confirmation_checklist.md | Manual price/volume monitoring framework relative to $1.50 March 2026 offering price (CP23G) | approved |
| **MAIA Market Confirmation Plan (JSON)** | json | docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_plan.json | json/MAIA_market_confirmation_plan.json | Machine-readable market confirmation plan with baseline, triggers, status labels (CP23G) | approved |
| **MAIA Market Observation Template** | csv | docs/sample_reports/maia_market_confirmation/MAIA_market_observation_template.csv | csv/MAIA_market_observation_template.csv | Weekly price/volume manual observation template with 17 columns (CP23G) | manual template |
| **MAIA Market Confirmation Baseline Status** | markdown | docs/sample_reports/maia_market_confirmation/MAIA_market_confirmation_baseline_status.md | md/MAIA_market_confirmation_baseline_status.md | Current market confirmation baseline and automation gaps (CP23G) | approved |
| **CP23D Checkpoint Report** | markdown | docs/checkpoints/reports/CP23D_MAIA_full_synthesis_packet_report.md | md/CP23D_MAIA_full_synthesis_packet_report.md | CP23D checkpoint execution report (Full Synthesis) | checkpoint report |
| **CP23E Checkpoint Report** | markdown | docs/checkpoints/reports/CP23E_MAIA_monitoring_pack_report.md | md/CP23E_MAIA_monitoring_pack_report.md | CP23E checkpoint execution report (Monitoring Pack) | checkpoint report |
| **CP23F-Fix Checkpoint Report** | markdown | docs/checkpoints/reports/CP23F_fix_13f_parser_hardening_report.md | md/CP23F_fix_13f_parser_hardening_report.md | CP23F-Fix checkpoint execution report (13F Parser Hardening) | checkpoint report |
| **CP23G Checkpoint Report** | markdown | docs/checkpoints/reports/CP23G_MAIA_market_confirmation_checklist_report.md | md/CP23G_MAIA_market_confirmation_checklist_report.md | CP23G checkpoint execution report (Market Confirmation Checklist) | checkpoint report |

---

## Status Legend

- **approved:** Artifact is approved for use without modification
- **approved with limitation:** Artifact is approved with documented limitations (e.g., 13F parser 60% success rate, partial institutional visibility)
- **manual template:** Artifact is a template for manual data entry (e.g., weekly price/volume observation CSV)
- **checkpoint report:** Artifact is a checkpoint execution report documenting the implementation process

---

## Limitations Summary

### 13F Institutional Visibility (approved with limitation)

**Limitation:** 13F parser success rate is 60%; no-match conclusion is scoped to successfully parsed filings only.

**Details:**
- **Managers successfully parsed:** 3 (Bridgewater Associates, Citadel Advisors, Two Sigma Investments)
- **Managers failed parsing:** 2 (Berkshire Hathaway, Renaissance Technologies — non-standard InfoTable format)
- **Total holdings parsed:** 21,128 positions
- **MAIA matches found:** 0
- **Conclusion:** No MAIA institutional matches found **among successfully parsed large managers** (3 of 5)

**Recommendation:** Quarterly 13F monitoring should continue; first institutional match (if/when found) is a PM review trigger.

### Market Confirmation Data (manual template)

**Limitation:** Price/volume data is manual-entry only; no live market quote source is integrated.

**Details:**
- Weekly price/volume observations require manual recording from public quote source (Yahoo Finance, MarketWatch, brokerage platform)
- PM review trigger detection is manual calculation (no automated calculation of 5-day trends, volume ratios, or trigger conditions)
- No Telegram/email alerts when PM review trigger is met (manual PM review only)

**Recommendation:** Integrate public quote API (Alpha Vantage, Yahoo Finance, IEX Cloud) to auto-populate price/volume data and enable automated PM review trigger detection.

### THIO-104 Data Timing (critical unknown)

**Limitation:** THIO-104 Phase 3 data timing is NOT disclosed.

**Details:**
- Trial status: Ongoing (not disclosed)
- Enrollment: Not disclosed
- Expected data readout: Not disclosed
- **PM review trigger:** THIO-104 data timing disclosure resolves this critical unknown

**Recommendation:** Monitor MAIA investor relations page and SEC filings (8-K, 10-Q/10-K) for THIO-104 Phase 3 data timing disclosure.

---

## Archive Verification

- **Total artifacts:** 15 (10 markdown, 4 JSON, 1 CSV)
- **PDF exports:** 0 (PDF tools not available; see README.md for manual export instructions)
- **Checksums:** See `MAIA_archive_manifest.json` for SHA-256 checksums of all archived files
- **Secrets:** None included (archive verified free of API keys, tokens, passwords, credentials)
- **OpenInsider data:** Not used (Roger's OpenInsider spreadsheet excluded)

---

**END OF INDEX**
