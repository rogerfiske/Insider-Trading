# CP12A — Telegram Alert Channel Preparation Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP11 security verification is clean. Git history contains no committed API keys or tokens in `.env.example`, so CP11B key rotation is not required.

CP12A prepares the Telegram alert channel but does not send real alerts yet.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP12A goal

1. Verify Telegram-related placeholders exist in `.env.example`.
2. Verify local `.env` has Telegram placeholder keys, without printing values.
3. Document exactly what Roger must create in Telegram/BotFather.
4. Confirm Ross remains dry-run.
5. Do not send any Telegram messages in CP12A.
6. Do not modify Windows scheduled tasks.
7. Commit and push only safe documentation/checkpoint-report updates if all gates pass.

## Telegram account status

Roger has Telegram Desktop and Telegram Messenger on iPhone installed and linked.

Roger can see prior Telegram traffic on desktop.

## Important Telegram setup concept

The code should not use Roger’s personal Telegram login password.

Telegram alert delivery should use:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

These belong in local `.env` only.

Do not store Telegram account password or phone login credentials anywhere in the repo.

## Required preconditions

Confirm these files exist:

```text
.env
.env.example
agents/ross.py
docs/checkpoints/reports/CP11_etherscan_maya_runtime_report.md
```

Confirm `.env` is ignored without printing contents:

```powershell
git check-ignore -v .env
```

## Required `.env.example` placeholders

Ensure `.env.example` contains empty placeholders only:

```env
# Telegram alert delivery
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Do not add:

```text
TELEGRAM_PASSWORD=
TELEGRAM_PHONE_PASSWORD=
TELEGRAM_2FA_PASSWORD=
```

## Required local `.env` preparation

Update local `.env` only to add missing blank keys.

Rules:

1. Do not overwrite existing non-empty values.
2. Do not print `.env`.
3. Do not stage `.env`.
4. Confirm `.env` remains ignored.
5. Keep `ROSS_DRY_RUN=true`.

Required local keys:

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
ROSS_DRY_RUN
```

Report only SET / BLANK / MISSING, never actual values.

## Manual instructions for Roger

At the end of CP12A, clearly tell Roger:

1. In Telegram, open a chat with `@BotFather`.
2. Create a new bot using `/newbot`.
3. Save the bot token only in local `.env`:
   ```text
   TELEGRAM_BOT_TOKEN=
   ```
4. Start a chat with the new bot and send it a message such as:
   ```text
   hello
   ```
5. Determine `TELEGRAM_CHAT_ID` using the project’s approved method in CP12B, or a safe local helper if already implemented.
6. Do not paste bot token into ChatGPT.
7. Do not store Telegram password in `.env`.

## Allowed documentation updates

You may update:

```text
README.md
docs/install_notes_windows.md
docs/source_grounding.md
```

Only to clarify Telegram alert setup and dry-run safety.

## Prohibited actions

Do not:

1. Print `.env`.
2. Print Telegram bot token.
3. Ask Roger to paste Telegram token into Claude Code chat.
4. Add Telegram password placeholders.
5. Send Telegram messages.
6. Send email.
7. Turn off `ROSS_DRY_RUN`.
8. Modify scheduled tasks.
9. Run Ross in live mode.
10. Force-push.
11. Modify preserved source files in `docs/source/`.
12. Commit `.env`, `.venv/`, `.claude/`, `.state/`, logs, databases, raw data, or private portfolio files.

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
git check-ignore -v docs/checkpoints/reports/CP11_etherscan_maya_runtime_report.md
```

Expected: no ignore match / non-zero exit code.

## Commit/push authorization

If only safe placeholder/documentation/report changes are made and all validation passes, commit and push.

Suggested commit message:

```powershell
git commit -m "Prepare Telegram alert channel configuration"
```

Push:

```powershell
git push origin main
```

If push is rejected, stop and report. Do not force-push.

## Required CP12A report

Save report to:

```text
docs/checkpoints/reports/CP12A_telegram_alert_prep_report.md
```

The report must include:

1. Summary.
2. Files created.
3. Files modified.
4. `.env.example` Telegram placeholder status.
5. Local `.env` Telegram key status without values.
6. Confirmation no Telegram password placeholders were added.
7. Confirmation `.env` was not printed.
8. Confirmation `ROSS_DRY_RUN=true`.
9. Documentation updates.
10. Test results.
11. Smoke test result.
12. Confirmation no Telegram message was sent.
13. Confirmation no email was sent.
14. Confirmation no scheduled tasks were changed.
15. Commit hash, if committed.
16. Push result, if pushed.
17. Exact manual steps Roger must complete before CP12B.
18. Awaiting PM Approval section.

## End condition

After saving the report and completing any approved commit/push, respond with:

1. Report path.
2. Short summary.
3. Commit hash if committed.
4. Push result if pushed.
5. Exact Telegram `.env` keys Roger must fill in manually.
6. Confirmation that CP12A completed successfully or stopped safely.
