# CP07 — Final Review / Commit / Push Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP06 is approved. Windows Task Scheduler setup passed with all 7 tasks registered under `\InsiderRoutines\`, Sophie manually validated, Ross dry-run preserved, and no real messages sent.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP07 goal

Perform the final local safety review, run quality gates, stage only safe project files, create the initial commit, push to `origin/main`, and verify that no secrets/private runtime artifacts were committed.

This checkpoint may commit and push only after all required quality gates pass.

## Required preconditions

Confirm these exist before continuing:

```text
docs/checkpoints/CHECKPOINT_PROTOCOL.md
docs/checkpoints/instructions/CP02_project_scaffold_instruction.md
docs/checkpoints/instructions/CP03_agent_port_instruction.md
docs/checkpoints/instructions/CP04_windows_install_instruction.md
docs/checkpoints/instructions/CP05_safe_runtime_smoke_tests_instruction.md
docs/checkpoints/instructions/CP05B_runtime_retest_instruction.md
docs/checkpoints/instructions/CP06_scheduler_setup_instruction.md
docs/checkpoints/reports/CP01_implementation_plan_report.md
docs/checkpoints/reports/CP02_project_scaffold_report.md
docs/checkpoints/reports/CP03_agent_port_report.md
docs/checkpoints/reports/CP04_windows_install_report.md
docs/checkpoints/reports/CP05_safe_runtime_smoke_tests_report.md
docs/checkpoints/reports/CP06_scheduler_setup_report.md
docs/source/original_prompt.md
docs/source/Insider_Trading_Windows_Windsurf_Claude_Code_Handoff_Prompt.md
docs/source/video_transcript.txt
```

If any are missing, stop and report the blocker.

## Important safety constraints

1. Do not print `.env` contents.
2. Do not print API keys, passwords, tokens, or secrets.
3. Do not commit `.env`.
4. Do not commit `.venv/`.
5. Do not commit `.claude/`.
6. Do not commit `.state/` runtime contents except `.state/.gitkeep`.
7. Do not commit logs, caches, databases, SQLite files, raw data, or private portfolio files.
8. Do not commit:
   ```text
   config/portfolio_target.json
   config/portfolio_current.json
   ```
9. Do not force-push under any circumstances.
10. Do not turn off `ROSS_DRY_RUN`.
11. Do not send real email.
12. Do not send real Telegram messages.
13. Do not register new scheduled tasks in CP07.
14. Do not modify preserved source files in `docs/source/`.
15. Do not implement live web-search/tool integration in CP07.

## Allowed actions

You may:

1. Run final safety checks.
2. Run final compile/import/smoke checks.
3. Create/update `docs/checkpoints/reports/CP07_final_review_commit_push_report.md`.
4. Make narrow documentation corrections if required for accuracy.
5. Make narrow `.gitignore` corrections if required to protect secrets/runtime artifacts.
6. Stage safe project files.
7. Commit safe project files only after all quality gates pass.
8. Push to `origin/main`.
9. Verify the pushed commit hash.
10. Verify no ignored/private files were committed.

## Required final quality gates

### Gate 1 — Git and remote status

Run:

```powershell
git branch --show-current
git remote -v
git status --short
```

Expected:

- Branch is `main`.
- Remote `origin` points to:
  ```text
  https://github.com/rogerfiske/Insider-Trading.git
  ```

If remote is different, stop and report.

### Gate 2 — Ignore and secret-safety checks

Run and report:

```powershell
git check-ignore -v .env
git check-ignore -v .claude/
git check-ignore -v .venv/
git check-ignore -v .state/logs/smoke_test_windows.log
git check-ignore -v .state/state.db
git check-ignore -v config/portfolio_target.json
git check-ignore -v config/portfolio_current.json
```

All should be ignored.

Confirm checkpoint reports are **not** ignored:

```powershell
git check-ignore -v docs/checkpoints/reports/CP06_scheduler_setup_report.md
```

Expected: no ignore match / non-zero exit code. Document this as good.

### Gate 3 — Pre-stage secret scan

Before staging, run commands that list candidate files and inspect for obvious secret leakage without printing secret values.

Use:

```powershell
git status --short
git ls-files --others --exclude-standard
```

Then run a safe search for likely secret markers in trackable files only. Do not search or print `.env`.

Suggested PowerShell approach:

```powershell
$patterns = @(
    'sk-ant-',
    'ANTHROPIC_API_KEY=sk-',
    'GMAIL_APP_PASSWORD=',
    'TELEGRAM_BOT_TOKEN=',
    'BEGIN PRIVATE KEY',
    'password=',
    'token='
)

$files = git ls-files --others --exclude-standard
$files += git ls-files

$files = $files | Where-Object {
    $_ -and
    $_ -notmatch '^\.env$' -and
    $_ -notmatch '^\.venv/' -and
    $_ -notmatch '^\.claude/' -and
    $_ -notmatch '^\.state/' -and
    $_ -notmatch '\.zip$'
}

foreach ($pattern in $patterns) {
    $matches = Select-String -Path $files -Pattern $pattern -SimpleMatch -ErrorAction SilentlyContinue
    if ($matches) {
        Write-Host "Potential secret marker found for pattern: $pattern"
        $matches | ForEach-Object { Write-Host ("  " + $_.Path + ":" + $_.LineNumber) }
    }
}
```

If a real secret appears in a trackable file, stop and report. Do not commit.

Placeholder values in `.env.example` are acceptable if they do not contain real secret strings.

### Gate 4 — Python compile/import checks

Run:

```powershell
.\.venv\Scripts\python.exe -m py_compile agents/common.py agents/eddie.py agents/maggie.py agents/frank.py agents/maya.py agents/janet.py agents/sophie.py agents/ross.py
.\.venv\Scripts\python.exe -c "import agents.common; print('agents.common import OK')"
```

### Gate 5 — Final smoke test

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_windows.ps1
```

Expected: all checks pass.

### Gate 6 — Scheduler state check

Do not create new scheduled tasks. Only verify existing tasks:

```powershell
Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Select-Object TaskName, State
```

Report all tasks found.

### Gate 7 — Stage safe files only

Stage files carefully.

Recommended:

```powershell
git add .gitignore
git add .env.example
git add README.md
git add requirements.txt
git add agents/
git add scripts/
git add install/
git add config/
git add docs/
git add .state/.gitkeep
```

Do not `git add .` unless you first verify ignored/private files cannot be staged.

After staging, run:

```powershell
git status --short
git diff --cached --name-only
```

Then verify no forbidden files are staged:

```powershell
git diff --cached --name-only | Select-String -Pattern '^\.env$|^\.venv/|^\.claude/|^\.state/(?!\.gitkeep)|\.log$|\.db$|\.sqlite$|\.sqlite3$|config/portfolio_target\.json|config/portfolio_current\.json'
```

Expected: no matches.

If forbidden files are staged, unstage them immediately and report.

### Gate 8 — Commit

Only if all prior gates pass, commit:

```powershell
git commit -m "Initial Windows Insider Trading agent scaffold"
```

Then capture the commit hash:

```powershell
git rev-parse HEAD
```

### Gate 9 — Push

Push to `origin/main`:

```powershell
git push -u origin main
```

If authentication is required, use the normal Git Credential Manager/browser workflow. Do not paste tokens into Claude Code.

If the push is rejected due to remote history conflict, stop and report. Do not force-push.

### Gate 10 — Post-push verification

After push succeeds, run:

```powershell
git status --short
git log --oneline -1
git ls-files
```

Verify no forbidden files are tracked:

```powershell
git ls-files | Select-String -Pattern '^\.env$|^\.venv/|^\.claude/|^\.state/(?!\.gitkeep)|\.log$|\.db$|\.sqlite$|\.sqlite3$|config/portfolio_target\.json|config/portfolio_current\.json'
```

Expected: no matches.

## Documentation updates allowed

You may update:

```text
README.md
docs/install_notes_windows.md
docs/checkpoints/README.md
```

Only to reflect CP07 final commit/push status and the pushed commit hash.

If documentation is updated after the initial commit, include it in the same commit before pushing. Do not create multiple commits unless necessary.

## Required CP07 report

Save the report to:

```text
docs/checkpoints/reports/CP07_final_review_commit_push_report.md
```

Important: the CP07 report itself should be included in the commit if possible. To do that:

1. Write the report with all pre-commit gate results first.
2. Stage it.
3. Commit.
4. Push.
5. After push, append the commit hash and push verification to the report.
6. If appending changes the report after commit, create a second small commit:
   ```powershell
   git add docs/checkpoints/reports/CP07_final_review_commit_push_report.md
   git commit -m "Add CP07 completion report"
   git push
   ```
7. Report both commit hashes if two commits are needed.

The report must include:

1. Summary of work completed.
2. Files created.
3. Files modified.
4. Files preserved untouched.
5. Git branch and remote verification.
6. Ignore/secret-safety check results.
7. Pre-stage secret scan result.
8. Compile/import check results.
9. Final smoke-test result.
10. Scheduler task state check.
11. Files staged.
12. Final committed file list or summary.
13. Confirmation no forbidden files were staged.
14. Commit hash or hashes.
15. Push result.
16. Post-push tracked-file safety verification.
17. Confirmation `.env` was not committed.
18. Confirmation `.venv/`, `.claude/`, logs, state DB, and private portfolio files were not committed.
19. Confirmation no real email was sent.
20. Confirmation no real Telegram message was sent.
21. Confirmation no scheduled tasks were changed.
22. Risks/blockers.
23. Recommended next phase:
    - CP08 Live Source Grounding / Anthropic Web Search or deterministic public-data APIs
    - CP09 Alert Delivery Enablement, if desired
24. Final completion section.

## End condition

After saving the report and completing push verification, respond with:

1. The report path.
2. Commit hash or hashes.
3. Push result.
4. Any blocker requiring PM attention.
5. Confirmation that CP07 is complete.
