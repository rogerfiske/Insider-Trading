# CP23A-Fix — Reconcile MAIA Capital Structure / Dilution Report with Manual SEC Extraction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP23A is **not final-approved**.

CP23A created a useful report scaffold and SEC filing inventory, but the output is materially incomplete and contains contradictions that must be fixed before the MAIA dilution/capital-structure report can be trusted.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP23A current commit

```text
Commit: 312d319
```

## Why CP23A is not approved

The report has these material issues:

1. March 2026 financing values appear wrong or unreconciled:
   - Report says gross proceeds: `$30.0 million`
   - Report says net proceeds: `$32.3 million`
   - Net proceeds cannot exceed gross proceeds for the same offering.
2. Report says common shares sold: `1,233,488`, which appears inconsistent with prior MAIA SEC/company data indicating a much larger March 2026 financing.
3. Share price is `TBD`.
4. Pre-funded warrants sold are shown as malformed values:
   ```text
   ,
   ```
5. Common warrants sold are shown as malformed values:
   ```text
   ,
   ```
6. Fully diluted estimate remains `TBD`.
7. 13F review was not integrated; report says it requires 13F matching integration.
8. Form 144 was found but not parsed:
   - seller: TBD
   - shares: TBD
   - relationship: TBD
9. The report relies too much on pattern-based extraction without manual SEC source reconciliation.
10. The checkpoint requirement was to produce a usable capital structure / dilution report, not only a scaffold.

## CP23A-Fix goal

Produce a corrected, SEC-only MAIA capital structure / dilution / hidden-institutional-ownership report with reconciled figures and explicit source filing support.

The goal is to replace `TBD` and contradictory values wherever the SEC filings disclose the information.

## Critical data-source boundary

Use only SEC/project-supported public sources:

```text
SEC EDGAR company submissions
SEC Archives filing documents
10-K / 10-Q / 8-K / 424B / S-1 / S-3 / DEF 14A / Form 144
Schedule 13D / 13G
Form 13F-HR through project-supported matching if available
```

Do not use:

```text
Roger’s uploaded MAIA spreadsheet
OpenInsider data supplied by Roger
paid/private/non-project data sources
uncited third-party summaries as source of truth
manual values from ChatGPT unless verified against SEC filing text
```

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
9. Commit `.env`, `.venv/`, `.claude/`, `.state`, logs, databases, SEC cache files, evidence cache files, private portfolio files, watchlist history database, or Roger’s spreadsheet.
10. Use Roger’s OpenInsider spreadsheet.
11. Present output as investment advice.
12. Connect this report to Ross alerts.
13. Consume Ross daily production guard.
14. Change alert settings.

## Required preconditions

Confirm these files exist:

```text
docs/checkpoints/reports/CP23A_MAIA_capital_structure_dilution_report.md
docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution_report.md
docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution.json
scripts/maia_capital_structure_research.py
tests/test_maia_capital_structure_research.py
```

Confirm `.env` is ignored without printing contents:

```powershell
git check-ignore -v .env
```

Confirm scheduled tasks exist but do not modify or trigger them:

```powershell
Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Select-Object TaskName, State
```

If any scheduled task is actively running, stop and report before continuing.

## Required methodology change

Do not rely only on broad regex pattern extraction.

Use a manual SEC filing reconciliation approach:

1. Download/open the specific MAIA filings.
2. Extract relevant numeric values from the exact filing sections.
3. Record accession numbers and filing dates for every material value.
4. Prefer tables in 10-Q, 10-K, 424B5, 8-K, and DEF 14A over press-release snippets.
5. If a value cannot be found, state exactly which filings were checked and why it remains unresolved.

## Required filings to manually reconcile

At minimum, inspect and reconcile:

```text
2026-03-02 424B5
2026-03-04 424B5
2026-03-04 8-K
2026-03-27 8-K
2026-03-31 8-K
2026-05-11 10-Q
2026-04-07 DEF 14A
2026-01-19 Form 144 or related 144 filing
latest 10-K in review period
latest S-3/S-1 shelf/resale registration if applicable
```

Use accession numbers already found by CP23A.

## Required March 2026 financing reconciliation

Create a clear table that separates each financing event.

Do not combine unrelated March/May offerings.

For each offering event, extract:

```text
filing/accession
date announced
date closed
security type
common shares sold
pre-funded warrants sold
common warrants sold
price per share / pre-funded warrant
warrant exercise price
gross proceeds
net proceeds
underwriter discount/fees if disclosed
over-allotment option if disclosed
use of proceeds
named investors or statement that investors not named
beneficial ownership blockers
```

If there were multiple March 2026 financing documents, reconcile them as separate rows.

If the report says `$30.0M gross` and `$32.3M net`, identify whether:
1. one number belongs to a different offering;
2. the net number is actually cash balance or aggregate financing cash flow;
3. the extraction was wrong.

Correct the report accordingly.

## Required capital structure reconciliation

Update the capital structure table with actual disclosed counts where available:

```text
common shares outstanding
common shares issued in March 2026 financing(s)
pre-funded warrants outstanding or issued
common warrants outstanding or issued
representative/underwriter/placement-agent warrants
stock options outstanding
stock options exercisable
RSUs/restricted stock if any
equity plan shares reserved
convertible debt/notes if any
ATM/shelf capacity if any
```

Every count must have:

```text
source filing
accession
filing date
confidence level
notes
```

## Required fully diluted estimate

Produce a numeric fully diluted estimate or a range.

At minimum:

```text
Basic shares outstanding
+ known pre-funded warrants
+ known common warrants
+ known options/RSUs
+ known other convertibles
= estimated fully diluted shares
```

If exact current fully diluted count cannot be computed, produce:

```text
Low case
High case
Known excluded/uncertain instruments
```

Do not leave the entire estimate as `TBD`.

## Required 13D/G review

Search MAIA issuer submissions and SEC ownership filings for:

```text
SC 13D
SC 13D/A
SC 13G
SC 13G/A
```

Report either:

```text
none found in review period
```

or a table of holders.

If none are found, explain that this does not prove no hedge fund involvement because 13D/G generally depends on beneficial ownership thresholds and reporting status.

## Required 13F review

Integrate existing 13F issuer matching if possible.

At minimum, run the project’s Maggie/13F matching logic for MAIA again and include:

```text
matching method: CUSIP / issuer name / both
managers found
periods found
shares
market value
confidence level
limitations
```

If the project still cannot reliably match MAIA in 13F, state that clearly and explain why.

But do not leave the section as only “requires integration” if a current project 13F method exists.

## Required Form 144 parsing

Parse the Form 144 found by CP23A:

```text
accession: 0001959173-24-000374
filing date: 2024-01-19
```

Extract if disclosed:

```text
seller
relationship to issuer
shares proposed to be sold
approximate sale date
aggregate market value
broker
securities acquired date
nature of acquisition
```

If the filing is XML/HTML and hard to parse, save a screenshot-free text extraction or narrow parser for the fields. Do not leave all fields as TBD unless the source truly lacks them.

## Required hidden/lagged institutional ownership section

Keep the CP23A hidden ownership section, but tie it to corrected findings.

Specifically discuss:

1. unnamed healthcare-dedicated investors if offering docs use that phrase;
2. beneficial ownership blockers at 4.99% / 9.99%;
3. pre-funded warrants and why they may obscure economic exposure;
4. 13F lag/threshold limits;
5. 13D/G threshold limits;
6. private placement/resale registration visibility;
7. Form 144 as possible sale intent, if applicable.

## Required outputs

Update:

```text
docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution_report.md
docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution.json
```

Create/update checkpoint report:

```text
docs/checkpoints/reports/CP23A_fix_MAIA_capital_structure_reconciliation_report.md
```

## Required JSON corrections

The JSON must not contain malformed placeholder values such as:

```json
"prefunded_warrants_sold": ","
"common_warrants_sold": ","
```

The JSON should use:

```json
null
```

for truly unavailable values, or numeric values when found.

The JSON must include a `reconciliation_status` section:

```json
{
  "reconciliation_status": {
    "gross_net_reconciled": true,
    "fully_diluted_numeric_estimate": true,
    "form_144_parsed": true,
    "thirteen_f_integrated_or_explained": true,
    "remaining_tbd_fields": []
  }
}
```

If any field remains unresolved, include it in `remaining_tbd_fields` with reason and filings checked.

## Required tests

Add or update tests.

Suggested:

```text
tests/test_maia_capital_structure_reconciliation.py
```

Tests should cover:

1. Net proceeds cannot exceed gross proceeds for same financing event unless explicitly explained as different events.
2. Malformed comma placeholders are not allowed in JSON.
3. Fully diluted estimate has numeric low/high or documented unresolved components.
4. Form 144 parser extracts seller/shares if fixture contains them.
5. 13F unavailable path is explicit and not a silent omission.
6. JSON reconciliation status exists.
7. No secrets in report/JSON.
8. No alert/email/Telegram code called.

Use mocked/static fixtures where possible. Live SEC network should not be required for unit tests.

## Required validation commands

Run and report:

```powershell
.\.venv\Scripts\python.exe --version
git branch --show-current
git status --short
git check-ignore -v .env
git check-ignore -v .state/state.db
git check-ignore -v .state/watchlist_history.db
.\.venv\Scripts\python.exe -m py_compile scripts/maia_capital_structure_research.py
.\.venv\Scripts\python.exe -m py_compile sources/sec_common.py sources/sec_submissions.py sources/sec_ticker.py
.\.venv\Scripts\python.exe -m py_compile sources/sec_13f.py sources/sec_13f_parser.py sources/sec_13f_matcher.py
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
git add scripts/maia_capital_structure_research.py
git add docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution_report.md
git add docs/sample_reports/maia_capital_structure/MAIA_capital_structure_dilution.json
git add docs/checkpoints/reports/CP23A_fix_MAIA_capital_structure_reconciliation_report.md
git add tests/test_maia_capital_structure_reconciliation.py
git add tests/test_maia_capital_structure_research.py
```

Only stage files that exist and changed.

Do not stage `.env`, `.state`, logs, databases, evidence cache files, SEC cache files, temporary files, Roger’s private spreadsheet, private watchlist files, private portfolio files, or the watchlist history database.

Commit:

```powershell
git commit -m "Reconcile MAIA capital structure dilution report"
```

Push:

```powershell
git push origin main
```

If push is rejected, stop and report. Do not force-push.

## End condition

Respond with:

1. Checkpoint report path.
2. Corrected MAIA capital structure report path.
3. Corrected JSON path.
4. Short summary.
5. Corrected March 2026 financing findings.
6. Corrected fully diluted estimate.
7. 13D/G findings.
8. 13F findings.
9. Form 144 parsed findings.
10. Hidden/lagged institutional ownership findings.
11. Remaining unresolved fields, if any.
12. Whether Roger’s OpenInsider spreadsheet was excluded.
13. Whether any Telegram/email was sent.
14. Whether scheduled tasks were modified or triggered.
15. Whether `.env` and secrets remained protected.
16. Commit hash if committed.
17. Push result if pushed.
18. Any blocker requiring PM attention.
