# CP23B — MAIA Clinical/Regulatory Milestone Calendar and Cash Runway Sensitivity Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP23A-Fix is approved.

Approved CP23A-Fix final state:

```text
Commits:
807c31f — feat: Reconcile MAIA capital structure report
61d1fb0 — docs: Add commit hash to CP23A-Fix checkpoint report

Corrected MAIA capital structure report:
docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution_report.md

Corrected JSON:
docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution.json

Key corrected findings:
- March 2026 public offering: 20,000,000 common shares at $1.50
- Gross proceeds: $30.0M
- Base net proceeds: about $28.0M
- Net proceeds with overallotment: about $32.3M
- No pre-funded warrants in March 2026 public offering
- No common warrants in March 2026 public offering
- Low-case fully diluted estimate: 85,033,854 shares
- High-case fully diluted estimate: 88,033,854 shares
- 13D/G: none found in review period
- Form 144: zero filings found after correction
- 13F: limited; full InfoTable XML matching not yet integrated
```

CP23B is a MAIA-specific research/reporting checkpoint.

It must not alter production alerts, send Telegram/email, modify/trigger scheduled tasks, or use Roger’s uploaded OpenInsider/MAIA spreadsheet.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP23B goal

Produce a SEC/company-source-only MAIA clinical/regulatory milestone calendar and cash runway sensitivity report.

The report should connect MAIA’s:

1. Lead clinical programs.
2. Regulatory status.
3. Expected or implied milestones.
4. Cash position.
5. Quarterly burn.
6. Financing/dilution overhang.
7. Cash runway under low/base/high burn scenarios.
8. Potential next dilution window.
9. Key catalyst monitoring checklist.

This is a research report only.

## Critical data-source boundary

Use only:

```text
SEC EDGAR filings
MAIA official investor relations press releases
MAIA official investor presentation if available from company IR
ClinicalTrials.gov if needed for trial status
FDA public pages only if needed for general Fast Track explanation
Existing project SEC/company-source connectors
```

Do not use Roger’s uploaded MAIA spreadsheet, OpenInsider data supplied by Roger, paid/private/non-project sources, message-board claims, uncited social media, or uncited third-party summaries as source of truth.

## Critical safety constraints

Do not:

1. Send Telegram messages.
2. Send email.
3. Modify Windows scheduled tasks.
4. Trigger Windows scheduled tasks.
5. Change `.env`.
6. Print `.env`.
7. Print SMTP password, Telegram token, Telegram chat ID, API keys, or secrets.
8. Force-push.
9. Modify preserved source files in `docs/source/`.
10. Commit `.env`, `.venv/`, `.claude/`, `.state`, logs, databases, SEC cache files, evidence cache files, private portfolio files, watchlist history database, or Roger’s spreadsheet.
11. Use Roger’s OpenInsider spreadsheet.
12. Present output as investment advice.
13. Connect this report to Ross alerts.
14. Consume Ross daily production guard.
15. Change alert settings such as `ALERT_ENABLE_EMAIL`.

## Required preconditions

Confirm these files exist:

```text
docs/checkpoints/reports/CP23A_fix_MAIA_capital_structure_reconciliation_report.md
docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution_report.md
docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution.json
docs/sample_reports/watchlist/manual_watchlist_results.json
docs/sample_reports/watchlist/manual_watchlist_summary.md
scripts/maia_capital_structure_research.py
scripts/ticker_watchlist.py
scripts/ticker_drilldown.py
sources/sec_common.py
sources/sec_submissions.py
sources/sec_ticker.py
```

Confirm `.env` and `.state` paths are ignored without printing contents:

```powershell
git check-ignore -v .env
git check-ignore -v .state/state.db
git check-ignore -v .state/watchlist_history.db
git check-ignore -v .state/cache
```

Confirm scheduled tasks exist but do not modify or trigger them:

```powershell
Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Select-Object TaskName, State
```

If any scheduled task is actively running, stop and report before proceeding.

## Required research scope

Resolve MAIA:

```text
Ticker: MAIA
CIK: 0001878313
Company: MAIA Biotechnology, Inc.
```

Review source materials covering at least:

```text
2024-01-01 through current date
```

Minimum source types:

```text
10-K
10-Q
8-K
424B / prospectus supplement if financing affects runway
DEF 14A if equity-plan context affects cash/dilution
official press releases
ClinicalTrials.gov records for THIO-101 and THIO-104 if available
FDA public explanation of Fast Track designation if needed
```

## Required clinical/regulatory program mapping

Create a table of MAIA clinical programs with:

```text
Program / asset
Former/current name
Indication
Trial name or identifier
Phase
Line of therapy
Combination partner/drug if applicable
Trial geography/sites if disclosed
Regulatory status
Key endpoints
Enrollment target if disclosed
Current status
Most recent company update
Next expected milestone
Source filing/press release
Confidence level
```

Known programs to investigate:

```text
Ateganosine / THIO
THIO-104 pivotal Phase 3 in advanced NSCLC
THIO-101 Phase 2 expansion
```

Search for any other pipeline assets or indications disclosed by MAIA.

## Required clinical/regulatory milestone calendar

Create a forward-looking milestone calendar. For each expected or possible milestone include:

```text
Milestone
Program
Expected timing if disclosed
Timing confidence: disclosed / inferred / unknown
Why it matters
Source
Risk if delayed
```

Look for:

```text
THIO-104 enrollment updates
THIO-104 dosing updates
THIO-104 interim/futility analysis, if disclosed
THIO-104 topline data timing, if disclosed
THIO-101 expansion data updates
Potential accelerated approval path, if disclosed
Regulatory filing plans, if disclosed
FDA interactions, if disclosed
Conference abstracts/presentations, if disclosed by company
Cash runway / financing milestones
```

Do not invent dates. If timing is not disclosed, state “not disclosed” and provide monitoring trigger.

## Required cash runway analysis

Use SEC filing values wherever possible.

Extract from latest 10-Q / 10-K:

```text
cash and cash equivalents
working capital
current liabilities
quarterly R&D expense
quarterly G&A expense
total operating expenses
net loss
net cash used in operating activities if available
cash from financing activities
management going-concern/runway statements
```

Use CP23A-Fix financing data:

```text
March 2026 public offering
20,000,000 common shares at $1.50
$30.0M gross proceeds
about $28.0M base net proceeds
about $32.3M net with overallotment
```

Create low/base/high runway scenarios with:

```text
quarterly burn assumption
monthly burn assumption
cash balance used
estimated runway in months
estimated runway end date
major assumptions
```

If cash balance is reported as of March 31, 2026, project forward carefully and label as estimate.

## Required dilution timing risk

Tie runway to dilution risk. Create a section:

```text
Potential Next Dilution Window
```

Include:

1. Current cash runway estimate.
2. Whether current cash appears sufficient to reach next disclosed milestone.
3. Whether Phase 3 cost escalation could shorten runway.
4. Whether the company may need capital before pivotal data.
5. Existing fully diluted estimate from CP23A-Fix.
6. Existing option/warrant/equity-plan overhang.
7. Monitoring triggers for new financing:
   - S-3/424B filings
   - ATM program activity
   - shelf takedowns
   - private placements
   - warrant exercises
   - going-concern language changes

Do not present the timing as certain.

## Required clinical-risk assessment

Create a balanced clinical-risk section including:

```text
positive clinical/regulatory signals
major clinical execution risks
trial design risks
endpoint risks
safety/tolerability risks
enrollment risks
competitive landscape caveat
regulatory risk
commercialization risk
```

Use only sourced facts and clearly separated inference.

## Required price/volume monitoring tie-in

Do not do a full trading analysis, but include:

```text
Market Confirmation Signals to Watch
```

Include price versus March 2026 offering price of $1.50, volume response to clinical updates, whether rallies are sustained or sold, new Form 4 activity, new Form 144 activity, new 13D/G or 13F visibility, and new financing filings.

No trading recommendations.

## Required outputs

Preferred script:

```text
scripts/maia_clinical_runway_research.py
```

Preferred output directory:

```text
docs/sample_reports/maia_clinical_runway/
```

Required markdown report:

```text
docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway_report.md
```

Required JSON output:

```text
docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway.json
```

Required checkpoint report:

```text
docs/checkpoints/reports/CP23B_MAIA_clinical_regulatory_cash_runway_report.md
```

## Required markdown report format

The markdown report must include:

1. Executive summary.
2. Source boundary.
3. Clinical program map.
4. Clinical/regulatory milestone calendar.
5. Latest financial snapshot.
6. Cash runway sensitivity table.
7. Potential next dilution window.
8. Clinical/regulatory risk assessment.
9. Market confirmation monitoring checklist.
10. Key open questions.
11. Appendix: source filings/press releases reviewed.
12. Confirmation Roger’s OpenInsider spreadsheet was not used.
13. Confirmation no Telegram/email sent.
14. Confirmation no scheduled tasks modified/triggered.

## Required JSON schema

Create:

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "generated_at": "...",
  "data_sources": ["SEC EDGAR", "MAIA IR", "ClinicalTrials.gov if used"],
  "clinical_programs": [],
  "milestone_calendar": [],
  "financial_snapshot": {},
  "cash_runway_scenarios": [],
  "dilution_timing_risk": {},
  "clinical_risk_assessment": {},
  "market_confirmation_watchlist": [],
  "limitations": [],
  "safety": {
    "openinsider_spreadsheet_used": false,
    "telegram_sent": false,
    "email_sent": false,
    "scheduled_tasks_modified": false
  }
}
```

No secrets.

## Required tests

Add tests if new parser/runway logic is introduced.

Suggested tests:

```text
tests/test_maia_clinical_runway_research.py
tests/test_cash_runway_sensitivity.py
```

Tests should cover:

1. Runway calculation from cash and quarterly burn.
2. Low/base/high scenario ordering.
3. Unknown milestone timing handled as not disclosed.
4. JSON schema contains required keys.
5. Report does not contain secrets.
6. No alert/email/Telegram code called.
7. No OpenInsider spreadsheet required.

Use mocked/static fixtures where possible. Live network should not be required for unit tests.

## Required validation commands

Run and report:

```powershell
.\.venv\Scripts\python.exe --version
git branch --show-current
git status --short
git check-ignore -v .env
git check-ignore -v .state/state.db
git check-ignore -v .state/watchlist_history.db
.\.venv\Scripts\python.exe -m py_compile scripts/maia_clinical_runway_research.py
.\.venv\Scripts\python.exe -m py_compile sources/sec_common.py sources/sec_submissions.py sources/sec_ticker.py
```

Run tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Run smoke test only if safe and not alert-triggering. Since the production dual-channel pilot is active, skip smoke if there is any chance of sending alerts and explain why.

## Secret scan before commit

Before staging, run a safe trackable-file secret scan excluding `.env`.

Patterns must include:

```text
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SMTP_PASSWORD=
SMTP_USERNAME=
GMAIL_APP_PASSWORD=
sk-ant-
ETHERSCAN_API_KEY=
SEC_API_IO_API_KEY=
BEGIN PRIVATE KEY
password=
token=
chat_id=
```

Verify no database/private files are staged:

```powershell
git diff --cached --name-only | Select-String -Pattern '^\.env$|^\.venv/|^\.claude/|^\.state/|\.log$|\.db$|\.sqlite$|\.sqlite3$|MAIA\.xlsx|OpenInsider|openinsider|config/watchlists/(?!.*\.example\.txt)'
```

Expected: no matches.

## Commit/push authorization

If validation passes and only safe files changed, commit and push.

Suggested staging:

```powershell
git add scripts/maia_clinical_runway_research.py
git add docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway_report.md
git add docs/sample_reports/maia_clinical_runway/MAIA_clinical_regulatory_cash_runway.json
git add docs/checkpoints/reports/CP23B_MAIA_clinical_regulatory_cash_runway_report.md
git add tests/test_maia_clinical_runway_research.py
git add tests/test_cash_runway_sensitivity.py
git add README.md
```

Only stage files that exist and changed. Do not stage `.env`, `.state`, logs, databases, evidence cache files, SEC cache files, temporary files, Roger’s private spreadsheet, private watchlist files, private portfolio files, or the watchlist history database.

Commit:

```powershell
git commit -m "Add MAIA clinical runway research"
```

Push:

```powershell
git push origin main
```

If push is rejected, stop and report. Do not force-push.

## Required checkpoint report

Save:

```text
docs/checkpoints/reports/CP23B_MAIA_clinical_regulatory_cash_runway_report.md
```

The checkpoint report must include:

1. Summary.
2. Files created.
3. Files modified.
4. Sources reviewed.
5. Clinical program map summary.
6. Milestone calendar summary.
7. Financial snapshot.
8. Cash runway scenarios.
9. Potential dilution timing risk.
10. Clinical/regulatory risks.
11. Market confirmation monitoring checklist.
12. Limitations.
13. Confirmation Roger’s OpenInsider spreadsheet was not used.
14. Confirmation no Telegram message was sent.
15. Confirmation no email was sent.
16. Confirmation scheduled tasks were not modified or triggered.
17. Confirmation `.env` was not printed or changed.
18. Confirmation no secrets were printed.
19. Test results.
20. Smoke test result or reason skipped.
21. Secret scan result.
22. Commit hash if committed.
23. Push result if pushed.
24. Risks/blockers.
25. Recommended next step:
    - CP23C Generalize capital-structure/runway research to any ticker.
    - CP23D MAIA full synthesis packet combining insider, dilution, clinical, and runway.
    - CP22E production dual-channel pilot monitoring after next normal Ross run.
26. Awaiting PM Approval section.

## End condition

Respond with:

1. Checkpoint report path.
2. MAIA clinical/runway report path.
3. MAIA clinical/runway JSON path.
4. Short summary.
5. Clinical program/milestone findings.
6. Cash runway scenarios.
7. Potential dilution timing risk.
8. Clinical/regulatory risks.
9. Market confirmation monitoring checklist.
10. Whether Roger’s OpenInsider spreadsheet was excluded.
11. Whether any Telegram/email was sent.
12. Whether scheduled tasks were modified or triggered.
13. Whether `.env` and secrets remained protected.
14. Commit hash if committed.
15. Push result if pushed.
16. Any blocker requiring PM attention.
