# CP10 — Grounded Runtime Validation / Commit / Push Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP09 is approved. Deterministic source connectors and the evidence layer were implemented and tested, but live grounded runtime validation was intentionally deferred.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP10 goal

Perform controlled live grounded runtime validation for the CP09 connectors and integrated scouts, verify evidence persistence, run final safety/quality gates, commit the CP08/CP09/CP10 work, push to `origin/main`, and report commit hash or hashes.

CP10 may commit and push only after required safety gates pass.

## Required preconditions

Confirm these files/directories exist before continuing:

```text
.venv/
.env
docs/checkpoints/reports/CP09_source_connectors_implementation_report.md
docs/checkpoints/instructions/CP09_source_connectors_implementation_instruction.md
evidence/schema.py
evidence/store.py
sources/sec_common.py
sources/sec_form4.py
sources/sec_13f.py
sources/fed_speeches.py
sources/etherscan.py
agents/eddie.py
agents/maggie.py
agents/frank.py
agents/maya.py
```

Confirm `.env` is ignored without printing contents:

```powershell
git check-ignore -v .env
```

Confirm Windows scheduled tasks exist but do not modify, delete, or manually trigger them:

```powershell
Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Select-Object TaskName, State
```

If any scheduled task is actively running, stop and report before runtime validation.

## Required local `.env` values

Do not print `.env`.

Confirm the presence, but not the values, of:

```text
ANTHROPIC_API_KEY
SEC_USER_AGENT
ROSS_DRY_RUN
```

`ROSS_DRY_RUN` must remain true.

`SEC_USER_AGENT` should be a real descriptive SEC user-agent containing contact information, not the default placeholder.

Optional:

```text
ETHERSCAN_API_KEY
```

If `ETHERSCAN_API_KEY` is absent, Maya may return a graceful config error and CP10 may still pass if this is documented. Do not treat missing Etherscan key as a blocker unless Roger explicitly wants Maya live validation now.

## Critical safety constraints

Do not:

1. Print `.env` contents.
2. Print API keys, passwords, tokens, app passwords, or hidden secrets.
3. Send real email.
4. Send real Telegram messages.
5. Turn off `ROSS_DRY_RUN`.
6. Register, modify, delete, or manually trigger Windows Task Scheduler tasks.
7. Force-push.
8. Modify preserved source files in `docs/source/`.
9. Commit `.env`, `.venv/`, `.claude/`, `.state/` runtime contents except `.state/.gitkeep`, logs, caches, databases, SQLite files, raw data, or private portfolio files.
10. Commit:
    ```text
    config/portfolio_target.json
    config/portfolio_current.json
    ```
11. Store secrets in code, docs, logs, state DB, evidence JSON, or test fixtures.

## Allowed actions

You may:

1. Run controlled direct runtime validation from the command line.
2. Run scout agents directly through `scripts/run_agent.ps1`; do not use Task Scheduler.
3. Inspect `.state/evidence/` metadata and generated filenames without printing secret content.
4. Inspect state DB summaries if needed, without printing secrets.
5. Make narrow code fixes if runtime validation reveals a small local bug.
6. Make narrow documentation updates.
7. Run all final quality gates.
8. Commit and push safe files after all required gates pass.
9. Save CP10 report to:
   ```text
   docs/checkpoints/reports/CP10_grounded_runtime_validation_commit_push_report.md
   ```

## Required quality gates before runtime validation

### Gate 1 — Environment and git status

Run:

```powershell
.\.venv\Scripts\python.exe --version
git branch --show-current
git remote -v
git status --short
```

Expected branch:

```text
main
```

Expected remote:

```text
https://github.com/rogerfiske/Insider-Trading.git
```

If remote differs, stop and report.

### Gate 2 — Ignore safety

Run:

```powershell
git check-ignore -v .env
git check-ignore -v .claude/
git check-ignore -v .venv/
git check-ignore -v .state/logs/smoke_test_windows.log
git check-ignore -v .state/evidence/test.json
git check-ignore -v .state/state.db
git check-ignore -v config/portfolio_target.json
git check-ignore -v config/portfolio_current.json
```

All must be ignored.

Confirm checkpoint reports are not ignored:

```powershell
git check-ignore -v docs/checkpoints/reports/CP09_source_connectors_implementation_report.md
```

Expected: no ignore match / non-zero exit code. Document this as good.

### Gate 3 — Secret pre-scan

Do not scan `.env`.

Run a trackable-file secret marker scan similar to CP07.

Patterns must include:

```text
sk-ant-
ANTHROPIC_API_KEY=sk-
ETHERSCAN_API_KEY=
GMAIL_APP_PASSWORD=
TELEGRAM_BOT_TOKEN=
BEGIN PRIVATE KEY
password=
token=
```

If a real secret appears in a trackable file, stop and report. Placeholder variable names in `.env.example` are acceptable if no real secret value is present.

### Gate 4 — Compile/import/unit tests

Run:

```powershell
.\.venv\Scripts\python.exe -m py_compile agents/common.py agents/eddie.py agents/maggie.py agents/frank.py agents/maya.py agents/janet.py agents/sophie.py agents/ross.py
.\.venv\Scripts\python.exe -m py_compile evidence/schema.py evidence/store.py sources/base.py sources/sec_common.py sources/sec_form4.py sources/sec_13f.py sources/fed_speeches.py sources/onchain_base.py sources/etherscan.py
.\.venv\Scripts\python.exe -m pytest -q
```

### Gate 5 — Smoke test

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_windows.ps1
```

Expected: all checks pass.

## Controlled live runtime validation

Run direct agent commands only. Do not trigger scheduled tasks.

Before running scouts, capture existing evidence count:

```powershell
if (Test-Path .state\evidence) { (Get-ChildItem .state\evidence -Filter *.json | Measure-Object).Count } else { 0 }
```

### Test 1 — Eddie grounded SEC Form 4 runtime

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent eddie
```

Validate:

1. It performs connector retrieval before the Claude prompt.
2. It creates an evidence JSON file or a clear source-failure evidence record.
3. It does not fabricate signals if source retrieval fails.
4. It does not print secrets.
5. It writes or skips signal generation according to source outcome.

SEC source failure due to access/rate-limit should not automatically fail CP10 if handled gracefully and evidence records capture the failure. Report exact category.

### Test 2 — Frank grounded Fed runtime

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent frank
```

Validate:

1. It fetches/parses Federal Reserve source material or fails gracefully.
2. It creates evidence.
3. It does not print secrets.

### Test 3 — Maggie 13F runtime

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent maggie
```

Validate:

1. It attempts deterministic SEC submissions/13F retrieval.
2. It creates evidence or failure evidence.
3. It does not print secrets.
4. Per-manager failures do not crash the entire run unless all fail in a way that should be considered blocking.

### Test 4 — Maya Etherscan runtime

If `ETHERSCAN_API_KEY` exists, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent maya
```

If `ETHERSCAN_API_KEY` does not exist, run Maya only if doing so verifies graceful config-error behavior without API calls.

Validate:

1. It either performs Etherscan retrieval or returns a documented config error.
2. It creates evidence or reports why evidence could not be created.
3. It does not print secrets.

### Test 5 — Sophie after grounded scout runs

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent sophie
```

Validate:

1. It reads current signal history.
2. It handles consensus or no-consensus correctly.
3. It does not print secrets.

### Test 6 — Ross dry-run only

Run Ross only if `ROSS_DRY_RUN=true` is confirmed.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent ross
```

Validate:

1. Ross remains dry-run.
2. No real email is sent.
3. No real Telegram message is sent.
4. Dry-run output/logs are safe.

## Evidence validation

After runtime validation, report:

1. New evidence file count.
2. Evidence filenames generated during CP10.
3. For each new file, summarize:
   - agent
   - source name
   - ok/failure
   - evidence count
   - error type if failed
4. Do not paste lengthy raw excerpts.
5. Do not paste secrets.

## Commit/push authorization

Only commit and push if:

1. Compile checks pass.
2. Unit tests pass.
3. Smoke test passes.
4. Runtime validation either succeeds or fails gracefully in documented non-code-defect ways.
5. No secrets are present in trackable files.
6. No forbidden files are staged.

## Staging rules

Stage safe files carefully.

Recommended:

```powershell
git add requirements.txt
git add README.md
git add docs/
git add agents/eddie.py agents/maggie.py agents/frank.py agents/maya.py
git add evidence/
git add sources/
git add tests/
```

Also stage any narrow safe fixes made during CP10.

Do not stage:

```text
.env
.venv/
.claude/
.state/
*.log
*.db
*.sqlite
*.sqlite3
config/portfolio_target.json
config/portfolio_current.json
```

After staging, run:

```powershell
git status --short
git diff --cached --name-only
```

Verify no forbidden files are staged:

```powershell
git diff --cached --name-only | Select-String -Pattern '^\.env$|^\.venv/|^\.claude/|^\.state/(?!\.gitkeep)|\.log$|\.db$|\.sqlite$|\.sqlite3$|config/portfolio_target\.json|config/portfolio_current\.json'
```

Expected: no matches.

## Commit and push

Commit:

```powershell
git commit -m "Add deterministic source connectors and evidence layer"
```

Capture hash:

```powershell
git rev-parse HEAD
```

Push:

```powershell
git push origin main
```

If rejected due to remote history conflicts, stop and report. Do not force-push.

## CP10 report

Save report to:

```text
docs/checkpoints/reports/CP10_grounded_runtime_validation_commit_push_report.md
```

Because the report must include commit/push results, use either:

### Option A — Two commits

1. Create preliminary CP10 report.
2. Commit source changes.
3. Push.
4. Update CP10 report with commit hash and push result.
5. Commit CP10 report.
6. Push again.

### Option B — One commit with partial report

Only use one commit if the report can accurately include all required details before commit/push. Two commits are acceptable and often clearer.

The report must include:

1. Summary of work completed.
2. Files created.
3. Files modified.
4. Files preserved untouched.
5. Precondition check results.
6. Ignore/secret-safety check results.
7. Secret pre-scan result.
8. Compile/import results.
9. Unit test result.
10. Smoke test result.
11. Eddie grounded runtime result.
12. Frank grounded runtime result.
13. Maggie grounded runtime result.
14. Maya grounded runtime result or graceful no-key result.
15. Sophie result.
16. Ross dry-run result.
17. Evidence validation summary.
18. Confirmation no secrets were printed.
19. Confirmation no real email was sent.
20. Confirmation no real Telegram message was sent.
21. Confirmation no scheduled tasks were changed or triggered.
22. Staged file list.
23. Confirmation no forbidden files were staged.
24. Commit hash or hashes.
25. Push result.
26. Post-push safety verification:
    ```powershell
    git ls-files | Select-String -Pattern '^\.env$|^\.venv/|^\.claude/|^\.state/(?!\.gitkeep)|\.log$|\.db$|\.sqlite$|\.sqlite3$|config/portfolio_target\.json|config/portfolio_current\.json'
    ```
    Expected: no matches.
27. Risks/blockers.
28. Recommended next phase:
    - CP11 Source Connector Hardening / Broader Live Fixtures
    - CP12 Alert Delivery Enablement, if desired
29. Final completion section.

## End condition

After saving the report and completing push verification, respond with:

1. Report path.
2. Commit hash or hashes.
3. Push result.
4. Any blocker requiring PM attention.
5. Confirmation that CP10 is complete or stopped safely.
