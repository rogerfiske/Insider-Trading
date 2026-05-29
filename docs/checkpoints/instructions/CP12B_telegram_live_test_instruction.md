# CP12B — Telegram Bot Token / Chat ID Validation and Controlled Test Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP12A is approved. Telegram placeholders are present in `.env.example` and local `.env`, and Ross remains in dry-run mode.

CP12B validates Telegram alert delivery in a controlled, one-message test while keeping scheduled tasks unchanged and keeping `ROSS_DRY_RUN=true`.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP12B goal

1. Confirm Roger has created a Telegram bot via `@BotFather`.
2. Confirm Roger has added `TELEGRAM_BOT_TOKEN` to local `.env`.
3. Obtain or validate `TELEGRAM_CHAT_ID` without printing the bot token.
4. Add `TELEGRAM_CHAT_ID` to local `.env` if it is missing and can be safely determined.
5. Run a controlled Telegram-only test message.
6. Keep Ross dry-run mode enabled.
7. Do not modify scheduled tasks.
8. Commit and push only safe code/docs/report changes if all gates pass.

## Required manual preconditions for Roger

Before running CP12B, Roger should:

1. Open Telegram.
2. Start a chat with `@BotFather`.
3. Run:
   ```text
   /newbot
   ```
4. Copy the bot token into local `.env` only:
   ```text
   TELEGRAM_BOT_TOKEN=<real token>
   ```
5. Open a chat with the newly created bot.
6. Send the bot a message, such as:
   ```text
   hello
   ```

Do not paste the bot token into Claude Code chat or ChatGPT.

## Important safety policy

Do not print `.env`.

Do not print the Telegram bot token.

Do not print Telegram account passwords or phone-login details.

Do not add password placeholders.

The Telegram integration should use only:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

## Required preconditions

Confirm these files exist:

```text
.env
.env.example
agents/ross.py
docs/checkpoints/reports/CP12A_telegram_alert_prep_report.md
```

Confirm `.env` is ignored without printing contents:

```powershell
git check-ignore -v .env
```

Confirm Windows scheduled tasks exist but do not modify, delete, or manually trigger them:

```powershell
Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Select-Object TaskName, State
```

If any scheduled task is actively running, stop and report before testing alert delivery.

## Local `.env` checks

Do not print `.env`.

Report only SET / BLANK / MISSING for:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
ROSS_DRY_RUN
ANTHROPIC_API_KEY
```

Confirm:

```text
ROSS_DRY_RUN=true
```

If `TELEGRAM_BOT_TOKEN` is missing or blank, stop and tell Roger to add it manually.

## Chat ID discovery

If `TELEGRAM_CHAT_ID` is missing or blank, attempt to determine it using the Telegram Bot API `getUpdates` endpoint.

Requirements:

1. Use the token from `.env` without printing it.
2. Do not write the token to logs, report, or stdout.
3. Call:
   ```text
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
   internally only.
4. Parse the chat ID from the most recent message Roger sent to the bot.
5. Write only the numeric/string chat ID to local `.env`.
6. Do not print the token.
7. It is acceptable to print or report the chat ID if needed, but avoid unnecessary exposure.
8. If no updates are found, stop and instruct Roger to send `hello` to the bot, then rerun CP12B.

If a helper script is needed, it may be created, but it must not store secrets.

Suggested helper path if needed:

```text
scripts/telegram_setup_check.py
```

## Controlled Telegram live test

After `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are both present:

Send exactly one controlled Telegram test message.

Message should be clearly non-trading and non-sensitive, such as:

```text
Insider-Trading CP12B Telegram test: delivery channel verified. Ross remains in dry-run mode.
```

Requirements:

1. Send only one message.
2. Do not include any ticker, signal, recommendation, or financial instruction.
3. Do not turn off `ROSS_DRY_RUN`.
4. Do not run scheduled tasks.
5. Do not send email.
6. Do not send actual trading alerts.
7. Report whether Telegram returned success/failure without printing the bot token.

## Ross integration boundary

Ross must remain dry-run for normal alert dispatch.

CP12B may implement or use a Telegram test helper that sends one explicit test message without changing global Ross behavior.

Do not change scheduled Ross task behavior.

If changing `agents/ross.py` is necessary, keep the change narrow:

1. Provider-neutral alert-channel helper is acceptable.
2. Token redaction is required.
3. Dry-run behavior must remain default.
4. Existing tests must pass.

## Allowed code/documentation changes

You may create or update:

```text
scripts/telegram_setup_check.py
tests/test_telegram_alerts.py
README.md
docs/install_notes_windows.md
```

You may update `agents/ross.py` only if needed for safe Telegram integration/testing.

You may update `.env.example` only to ensure placeholders exist and remain blank.

## Prohibited actions

Do not:

1. Print `.env`.
2. Print Telegram bot token.
3. Ask Roger to paste the token into Claude Code chat.
4. Add Telegram password placeholders.
5. Send more than one Telegram test message.
6. Send email.
7. Turn off `ROSS_DRY_RUN`.
8. Modify scheduled tasks.
9. Trigger scheduled tasks.
10. Force-push.
11. Modify preserved source files in `docs/source/`.
12. Commit `.env`, `.venv/`, `.claude/`, `.state/`, logs, databases, raw data, or private portfolio files.
13. Put token values in docs, reports, tests, logs, evidence JSON, or code.

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
git check-ignore -v docs/checkpoints/reports/CP12A_telegram_alert_prep_report.md
```

Expected: no ignore match / non-zero exit code.

## Secret scan before commit

Before staging, run a safe trackable-file secret scan excluding `.env`.

Patterns must include:

```text
TELEGRAM_BOT_TOKEN=
bot
sk-ant-
ETHERSCAN_API_KEY=
SEC_API_IO_API_KEY=
GMAIL_APP_PASSWORD=
SMTP_PASSWORD=
BEGIN PRIVATE KEY
```

Important:

- Empty placeholders in `.env.example` are allowed.
- Real token-like values in tracked files are not allowed.
- Do not scan or print `.env`.

If a real token appears in any trackable file, stop and report.

## Commit/push authorization

If all validation passes and only safe files changed, commit and push safe changes.

Suggested staging:

```powershell
git add .env.example
git add README.md
git add docs/install_notes_windows.md
git add scripts/telegram_setup_check.py
git add tests/test_telegram_alerts.py
git add agents/ross.py
git add docs/checkpoints/reports/CP12B_telegram_live_test_report.md
```

Only stage files that actually exist and changed.

Verify no forbidden files are staged:

```powershell
git diff --cached --name-only | Select-String -Pattern '^\.env$|^\.venv/|^\.claude/|^\.state/(?!\.gitkeep)|\.log$|\.db$|\.sqlite$|\.sqlite3$|config/portfolio_target\.json|config/portfolio_current\.json'
```

Expected: no matches.

Commit:

```powershell
git commit -m "Validate Telegram alert delivery"
```

Push:

```powershell
git push origin main
```

If push is rejected, stop and report. Do not force-push.

## Required CP12B report

Save report to:

```text
docs/checkpoints/reports/CP12B_telegram_live_test_report.md
```

The report must include:

1. Summary.
2. Files created.
3. Files modified.
4. `.env.example` Telegram placeholder status.
5. Local `.env` Telegram key status without values.
6. Chat ID discovery result.
7. Confirmation no Telegram password placeholders were added.
8. Confirmation `.env` was not printed.
9. Confirmation bot token was not printed.
10. Confirmation `ROSS_DRY_RUN=true`.
11. Test results.
12. Smoke test result.
13. Controlled Telegram test result.
14. Confirmation only one Telegram test message was sent.
15. Confirmation no email was sent.
16. Confirmation scheduled tasks were not changed or triggered.
17. Secret scan result.
18. Staged file list.
19. Confirmation no forbidden files were staged.
20. Commit hash, if committed.
21. Push result, if pushed.
22. Risks/blockers.
23. Recommended next phase:
    - CP13A Generic SMTP / 4SecureMail design
    - or CP12C Telegram hardening if the test failed
24. Awaiting PM Approval section.

## End condition

After saving the report and completing any approved commit/push, respond with:

1. Report path.
2. Short summary.
3. Whether Telegram test message was delivered.
4. Commit hash if committed.
5. Push result if pushed.
6. Any blocker requiring PM attention.
7. Recommendation: proceed to CP13A or CP12C.
