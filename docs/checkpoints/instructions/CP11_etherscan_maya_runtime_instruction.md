# CP11 — Etherscan / Maya Runtime Enablement Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP10 is complete. CP11 enables and validates Maya’s Etherscan-backed workflow using Roger’s locally configured Etherscan API key.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP11 goal

1. Add safe Etherscan and SEC-related placeholders/documentation to `.env.example`.
2. Ensure the actual local `.env` can use Roger’s Etherscan API key without printing it.
3. Validate Maya’s workflow using the local `ETHERSCAN_API_KEY`.
4. Keep Ross dry-run and do not send real alerts.
5. Commit and push only safe placeholder/documentation/code changes if all gates pass.

## Important PM guidance

Roger has signed up for the Etherscan free tier and created an API key named:

```text
Insider-Trading
```

Roger also has account/login information for Etherscan and sec-api.io, but website passwords must not be stored in the repository, logs, reports, or `.env.example`.

The `.env.example` may include account-reference placeholders such as email/username fields so Roger can remember which account is used, but it must not include password fields.

## Key technical clarification

Maya should use:

```text
ETHERSCAN_API_KEY
```

It should not need the Etherscan website username or password.

SEC EDGAR official access should use:

```text
SEC_USER_AGENT
```

A third-party sec-api.io key may be documented as optional/future-use only unless code already supports it.

## Required preconditions

Confirm these exist:

```text
.venv/
.env
.env.example
sources/etherscan.py
agents/maya.py
docs/checkpoints/reports/CP10_grounded_runtime_validation_commit_push_report.md
```

Confirm `.env` is ignored without printing contents:

```powershell
git check-ignore -v .env
```

Confirm scheduled tasks exist but do not modify, delete, or manually trigger them:

```powershell
Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Select-Object TaskName, State
```

If any scheduled task is actively running, stop and report before editing runtime code.

## Required local `.env` checks

Do not print `.env`.

Check only presence/absence of:

```text
ETHERSCAN_API_KEY
ANTHROPIC_API_KEY
SEC_USER_AGENT
ROSS_DRY_RUN
```

`ROSS_DRY_RUN` must remain true.

If `ETHERSCAN_API_KEY` is missing, stop and report that Roger must add it locally to `.env`.

## Required `.env.example` updates

Update `.env.example` with safe placeholders only.

Include these groups if not already present:

```env
# Anthropic
ANTHROPIC_API_KEY=

# SEC EDGAR official access
# Use a descriptive value such as: ProjectName ContactName contact@example.com
SEC_USER_AGENT=

# Optional third-party SEC API account reference
# These are for local account tracking / future integration only unless code supports them.
SEC_API_IO_ACCOUNT_EMAIL=
SEC_API_IO_USERNAME=
SEC_API_IO_API_KEY=

# Etherscan account reference and API access
# API calls require ETHERSCAN_API_KEY; website username/email are optional local notes.
ETHERSCAN_ACCOUNT_EMAIL=
ETHERSCAN_USERNAME=
ETHERSCAN_API_KEY=

# Safety
ROSS_DRY_RUN=true
```

Do not add:

```text
ETHERSCAN_PASSWORD
SEC_API_IO_PASSWORD
PASSWORD
```

Do not add any real secrets.

## Documentation updates

Update documentation as needed:

```text
README.md
docs/install_notes_windows.md
docs/source_grounding.md
```

Required documentation points:

1. Etherscan API calls use `ETHERSCAN_API_KEY`.
2. Etherscan website username/password are not needed by the code.
3. Do not store website passwords in `.env` or the repository.
4. SEC official EDGAR connectors use `SEC_USER_AGENT`.
5. sec-api.io is optional/future-use unless code explicitly supports it.
6. `ETHERSCAN_ACCOUNT_EMAIL`, `ETHERSCAN_USERNAME`, `SEC_API_IO_ACCOUNT_EMAIL`, and `SEC_API_IO_USERNAME` are optional local account-reference fields only.
7. Maya is token/on-chain-flow oriented; she does not primarily research stock tickers. If a stock ticker is relevant, a separate mapping from company/ticker to crypto asset/token/wallet/source must be designed later.
8. Ross remains dry-run until explicitly changed in a later checkpoint.

## Maya workflow clarification

Maya’s job is not the same as Eddie/Maggie stock ticker research.

Maya is intended to monitor on-chain activity, such as:

```text
ETH transfers
ERC-20 token transfers
WBTC / WETH / USDC / USDT movement
large-wallet / whale-style flows
```

For CP11, do not require Roger to provide a stock ticker.

Use Maya’s current configured/default token/source behavior. If the connector requires specific token contract addresses or wallet addresses and none are configured, document that limitation and propose a CP11B config enhancement.

## Allowed code changes

You may make narrow code changes only if needed to:

1. Improve Maya’s handling of a configured `ETHERSCAN_API_KEY`.
2. Add safe no-secret presence checks.
3. Improve error messages for missing token/wallet configuration.
4. Ensure evidence is persisted for successful or gracefully failed Maya runs.
5. Add/update tests for Etherscan env/key handling.

Do not redesign Maya broadly in CP11.

## Prohibited actions

Do not:

1. Print `.env` contents.
2. Print Etherscan API key.
3. Print Anthropic API key.
4. Store website passwords anywhere.
5. Send real email.
6. Send real Telegram messages.
7. Turn off `ROSS_DRY_RUN`.
8. Register, modify, delete, or manually trigger Windows Task Scheduler tasks.
9. Force-push.
10. Modify preserved source files in `docs/source/`.
11. Store secrets in docs, code, logs, state DB, evidence JSON, reports, or tests.
12. Create or modify real private portfolio files.

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
git check-ignore -v .state/evidence/test.json
```

Confirm checkpoint reports are not ignored:

```powershell
git check-ignore -v docs/checkpoints/reports/CP10_grounded_runtime_validation_commit_push_report.md
```

Expected: no ignore match / non-zero exit code.

Run compile/tests:

```powershell
.\.venv\Scripts\python.exe -m py_compile agents/maya.py sources/etherscan.py evidence/schema.py evidence/store.py
.\.venv\Scripts\python.exe -m pytest -q
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_windows.ps1
```

## Runtime validation

Before running Maya, count evidence files:

```powershell
if (Test-Path .state\evidence) { (Get-ChildItem .state\evidence -Filter *.json | Measure-Object).Count } else { 0 }
```

Run Maya directly, not through Task Scheduler:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent maya
```

Validate:

1. Maya detects `ETHERSCAN_API_KEY` without printing it.
2. Maya attempts Etherscan-backed retrieval.
3. Maya either produces source evidence or produces a clear non-secret configuration/source failure.
4. Any evidence JSON created contains no secrets.
5. No real alerts are sent.
6. No scheduled tasks are changed or triggered.

After running Maya, count evidence files again and summarize new evidence files by filename, source name, ok/failure status, and error type if any. Do not paste raw secret-like content.

## Commit/push authorization

If all safety gates pass, commit and push safe changes.

Stage only safe files, likely:

```powershell
git add .env.example
git add README.md
git add docs/install_notes_windows.md
git add docs/source_grounding.md
git add agents/maya.py
git add sources/etherscan.py
git add tests/
git add docs/checkpoints/reports/CP11_etherscan_maya_runtime_report.md
```

Only stage files that actually changed.

Verify no forbidden files are staged:

```powershell
git diff --cached --name-only | Select-String -Pattern '^\.env$|^\.venv/|^\.claude/|^\.state/(?!\.gitkeep)|\.log$|\.db$|\.sqlite$|\.sqlite3$|config/portfolio_target\.json|config/portfolio_current\.json'
```

Expected: no matches.

Commit:

```powershell
git commit -m "Enable Etherscan configuration for Maya"
```

Push:

```powershell
git push origin main
```

If push is rejected, stop and report. Do not force-push.

## Required CP11 report

Save report to:

```text
docs/checkpoints/reports/CP11_etherscan_maya_runtime_report.md
```

The report must include:

1. Summary of work completed.
2. Files created.
3. Files modified.
4. Files preserved untouched.
5. `.env.example` placeholder changes.
6. Confirmation that no password placeholders were added.
7. Confirmation that `.env` was not printed.
8. Confirmation that `ETHERSCAN_API_KEY` presence was detected without printing value.
9. Documentation updates.
10. Test results.
11. Smoke test result.
12. Maya runtime result.
13. Evidence validation summary.
14. Confirmation no secrets were stored in evidence files.
15. Confirmation no real email was sent.
16. Confirmation no real Telegram message was sent.
17. Confirmation no scheduled tasks were changed or triggered.
18. Staged file list.
19. Confirmation no forbidden files were staged.
20. Commit hash, if committed.
21. Push result, if pushed.
22. Risks/blockers.
23. Recommended next phase:
    - CP11B Maya token/wallet configuration, if current Maya still needs explicit token/wallet scope
    - or CP12 alert-delivery dry-run-to-live planning
24. Awaiting PM Approval section.

## End condition

After saving the report and completing any approved commit/push, respond with:

1. Report path.
2. Short summary.
3. Commit hash if committed.
4. Push result if pushed.
5. Any blocker requiring PM attention.
6. Confirmation that CP11 completed successfully or stopped safely.
