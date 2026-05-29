# CP13A — Generic SMTP / 4SecureMail Alert Design Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP12B is approved. Telegram alert delivery was validated end-to-end with one controlled test message, and `ROSS_DRY_RUN=true` remains active.

CP13A designs the email alert path for Roger’s 4SecureMail account using generic SMTP. This is a design/planning checkpoint only.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP13A goal

Produce a design plan for replacing or supplementing Gmail-specific email delivery with provider-neutral SMTP delivery suitable for Roger’s 4SecureMail account.

Do not implement SMTP code yet.

Do not send email.

Do not modify scheduled tasks.

Do not commit or push unless the checkpoint report/documentation-only updates are explicitly safe and useful.

## Email provider context

Roger uses:

```text
https://mail.4securemail.com/
```

Target email account:

```text
fiske1945@4securemail.com
```

Likely SMTP host:

```text
mail.4securemail.com
```

Likely SMTP mode:

```text
SMTP over SSL/TLS on port 465
```

Do not assume the password. Roger will manage the email password in his password manager and, later, place the required SMTP password or app password into local `.env` only.

## Important design direction

Move away from Gmail-specific naming:

```text
GMAIL_USER
GMAIL_APP_PASSWORD
GMAIL_TO
```

Toward provider-neutral SMTP naming:

```text
SMTP_HOST
SMTP_PORT
SMTP_USE_SSL
SMTP_USERNAME
SMTP_PASSWORD
ALERT_EMAIL_FROM
ALERT_EMAIL_TO
```

Gmail may remain supported later as one SMTP provider, but the implementation should not be Gmail-only.

## Required preconditions

Confirm these files exist:

```text
.env
.env.example
agents/ross.py
docs/checkpoints/reports/CP12B_telegram_live_test_report.md
README.md
docs/install_notes_windows.md
```

Confirm `.env` is ignored without printing contents:

```powershell
git check-ignore -v .env
```

Confirm scheduled tasks exist but do not modify, delete, or manually trigger them:

```powershell
Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Select-Object TaskName, State
```

## Allowed actions

You may:

1. Inspect current Ross email/alert code.
2. Inspect `.env.example` placeholders without printing local `.env`.
3. Inspect documentation.
4. Create a CP13A design report.
5. Propose `.env.example` changes for CP13B.
6. Propose code changes for CP13B.
7. Update documentation only if the update clearly records planning status and does not contain secrets.
8. Commit/push only documentation/checkpoint report updates if there are no code/runtime changes and all safety checks pass.

## Prohibited actions

Do not:

1. Print `.env`.
2. Print email passwords, SMTP passwords, Telegram tokens, API keys, or other secrets.
3. Add real credentials to `.env.example`.
4. Add password values to docs, reports, tests, code, or logs.
5. Send any email.
6. Send Telegram messages.
7. Turn off `ROSS_DRY_RUN`.
8. Modify scheduled tasks.
9. Trigger scheduled tasks.
10. Implement SMTP code in CP13A.
11. Force-push.
12. Modify preserved source files in `docs/source/`.
13. Commit `.env`, `.venv/`, `.claude/`, `.state/`, logs, databases, raw data, or private portfolio files.

## Required analysis

Analyze the current Ross alert code and report:

1. How email delivery is currently represented.
2. Whether current code is Gmail-specific.
3. Whether current code uses SMTP, Gmail API, or another method.
4. What `.env` keys are currently expected.
5. What changes are needed for provider-neutral SMTP.
6. Whether Telegram and SMTP should be separate delivery channels.
7. How `ROSS_DRY_RUN` should control both Telegram and SMTP.
8. How to perform a future single controlled 4SecureMail test email safely.

## Required proposed `.env.example` design

Propose adding these placeholders in CP13B:

```env
# Generic SMTP alert delivery
SMTP_HOST=
SMTP_PORT=
SMTP_USE_SSL=
SMTP_USERNAME=
SMTP_PASSWORD=
ALERT_EMAIL_FROM=
ALERT_EMAIL_TO=
```

Recommended local 4SecureMail values for Roger to fill in later:

```env
SMTP_HOST=mail.4securemail.com
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USERNAME=fiske1945@4securemail.com
SMTP_PASSWORD=<local password or app password only>
ALERT_EMAIL_FROM=fiske1945@4securemail.com
ALERT_EMAIL_TO=fiske1945@4securemail.com
```

Do not write real `SMTP_PASSWORD` anywhere.

## Required CP13B implementation plan

The CP13A report must propose a CP13B implementation plan covering:

1. Provider-neutral SMTP helper module or Ross refactor.
2. Safe `.env.example` placeholder update.
3. Tests using mocked SMTP only.
4. Validation that no SMTP password is printed.
5. Validation that no real email is sent during dry-run.
6. One controlled real email test only after explicit PM approval.
7. Continued Telegram support.
8. Documentation updates.
9. Commit/push plan.
10. Rollback/safety plan if SMTP fails.

## Suggested future module structure

Evaluate whether this structure is appropriate:

```text
alerts/
  __init__.py
  telegram.py
  smtp_email.py
  common.py

tests/
  test_alerts_smtp_email.py
  test_alerts_telegram.py
```

Do not create these files in CP13A unless only documenting the proposal.

## Validation commands

Run and report:

```powershell
.\.venv\Scripts\python.exe --version
git branch --show-current
git remote -v
git status --short
git check-ignore -v .env
git check-ignore -v .claude/
git check-ignore -v .venv/
.\.venv\Scripts\python.exe -m py_compile agents/ross.py
.\.venv\Scripts\python.exe -m pytest -q
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_windows.ps1
```

Confirm checkpoint reports are not ignored:

```powershell
git check-ignore -v docs/checkpoints/reports/CP12B_telegram_live_test_report.md
```

Expected: no ignore match / non-zero exit code.

## Secret scan

If committing any documentation/report update, run a safe trackable-file secret scan excluding `.env`.

Patterns must include:

```text
SMTP_PASSWORD=
GMAIL_APP_PASSWORD=
TELEGRAM_BOT_TOKEN=
sk-ant-
ETHERSCAN_API_KEY=
SEC_API_IO_API_KEY=
BEGIN PRIVATE KEY
password=
token=
```

Empty placeholders in `.env.example` are allowed. Real values are not allowed.

## Required CP13A report

Save the report to:

```text
docs/checkpoints/reports/CP13A_smtp_4securemail_design_report.md
```

The report must include:

1. Summary.
2. Files inspected.
3. Current Ross email/alert implementation analysis.
4. Current Gmail-specific assumptions, if any.
5. Proposed provider-neutral SMTP `.env` design.
6. 4SecureMail recommended local values, without password.
7. Proposed alert module/refactor design.
8. Proposed tests.
9. Proposed CP13B implementation steps.
10. Safety and dry-run plan.
11. Single controlled email test plan for CP13B or CP13C.
12. Validation command results.
13. Confirmation no `.env` contents were printed.
14. Confirmation no email was sent.
15. Confirmation no Telegram message was sent.
16. Confirmation no scheduled tasks were changed or triggered.
17. Commit hash, if committed.
18. Push result, if pushed.
19. Risks/blockers.
20. Recommendation: proceed to CP13B implementation or revise design.
21. Awaiting PM Approval section.

## Commit/push authorization

CP13A is planning-only. Prefer no commit unless documentation/report updates are useful.

If committing, use:

```powershell
git commit -m "Plan generic SMTP alert delivery"
git push origin main
```

If push is rejected, stop and report. Do not force-push.

## End condition

After saving the report and completing any approved commit/push, respond with:

1. Report path.
2. Short summary.
3. Commit hash if committed.
4. Push result if pushed.
5. Any blocker requiring PM attention.
6. Recommendation: proceed to CP13B or revise design.
