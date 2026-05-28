# CP06 — Windows Task Scheduler Setup Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP05 is approved. Runtime smoke tests passed after Anthropic API credits were added.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP06 goal

Install and validate Windows Task Scheduler tasks for the local `Insider-Trading` agent system.

The scheduled setup should use the repo-local `.venv`, repo-relative paths, safe logging under `.state/logs/`, and Ross dry-run mode.

Do not commit or push in CP06.

## Required preconditions

Confirm these before continuing:

1. `.venv/` exists.
2. `.env` exists and is ignored by Git.
3. `.env` contains an Anthropic API key without printing the value.
4. `ROSS_DRY_RUN=true` is present or Ross otherwise defaults to dry-run mode.
5. CP05 report exists:
   ```text
   docs/checkpoints/reports/CP05_safe_runtime_smoke_tests_report.md
   ```
6. Smoke test still passes:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_windows.ps1
   ```

If any precondition fails, stop and report the blocker.

## Important safety constraints

1. Ross must remain in dry-run mode.
2. Do not send real email.
3. Do not send real Telegram messages.
4. Do not place trades or connect to brokerage APIs.
5. Do not print `.env` contents.
6. Do not print API keys.
7. Do not commit files.
8. Do not push to GitHub.
9. Do not force-push.
10. Do not modify preserved source files in `docs/source/`.

## Expected scheduler scope

Create scheduled tasks for the Windows-first local install.

Recommended tasks:

```text
InsiderTrading_Eddie
InsiderTrading_Maggie
InsiderTrading_Frank
InsiderTrading_Maya
InsiderTrading_Sophie
InsiderTrading_Ross
InsiderTrading_Janet
```

Use the actual task names defined by `install/schedule_windows.ps1` if they differ, but report the final names.

Tasks should execute through the repo-local environment and scripts, preferably via:

```powershell
scripts\run_agent.ps1
```

or directly through:

```text
.venv\Scripts\python.exe
```

Task actions must use the repo as the working directory where possible.

## Scheduling expectations

Use the schedule already encoded in `install/schedule_windows.ps1` if it exists and is reasonable.

If the script does not encode timing clearly, use this conservative default for initial install:

```text
Scouts: Eddie/Maggie/Frank/Maya — once daily, staggered
Sophie: after scouts, once daily
Ross: after Sophie, once daily, dry-run only
Janet: once daily
```

Avoid creating high-frequency tasks in CP06.

## Allowed actions

You may:

1. Review `install/schedule_windows.ps1`.
2. Make narrow fixes to `install/schedule_windows.ps1` if needed for:
   - PowerShell 5.1 compatibility
   - correct repo path handling
   - correct `.venv` path handling
   - safe `.state/logs/` logging
   - dry-run safety
3. Run the scheduler install script:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install\schedule_windows.ps1
   ```
   Use any required safe parameters documented in the script.
4. Query created tasks using PowerShell / Task Scheduler commands.
5. Optionally run **one** manual scheduled task trigger for validation, preferably Eddie or Sophie, only if it does not send alerts.
6. Run Ross only if dry-run is confirmed.
7. Save the CP06 report to:
   ```text
   docs/checkpoints/reports/CP06_scheduler_setup_report.md
   ```

## Prohibited actions

Do not:

1. Send real email.
2. Send real Telegram messages.
3. Turn off Ross dry-run mode.
4. Create or modify real private portfolio files:
   ```text
   config/portfolio_target.json
   config/portfolio_current.json
   ```
5. Commit files.
6. Push to GitHub.
7. Force-push.
8. Modify preserved source files in `docs/source/`.
9. Implement live web-search/tool integration.
10. Increase schedule frequency beyond conservative defaults.
11. Store secrets in scheduled task arguments.
12. Store API keys in Task Scheduler actions.

## Required checks before scheduler setup

Run and report:

```powershell
.\.venv\Scripts\python.exe --version
git status --short
Test-Path .env
git check-ignore -v .env
git check-ignore -v .claude/
git check-ignore -v .state/logs/smoke_test_windows.log
git check-ignore -v docs/checkpoints/reports/CP05_safe_runtime_smoke_tests_report.md
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_windows.ps1
```

For the checkpoint report ignore check, expected result is **not ignored**. Document this clearly.

## Required scheduler setup

Run the Windows scheduler setup script:

```powershell
powershell -ExecutionPolicy Bypass -File .\install\schedule_windows.ps1
```

If the script requires parameters, inspect it and use the safest documented form.

After running, list created tasks:

```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like "InsiderTrading*" } | Select-Object TaskName, State
```

Also inspect actions/triggers without exposing secrets:

```powershell
Get-ScheduledTask | Where-Object { $_.TaskName -like "InsiderTrading*" } | ForEach-Object {
    [PSCustomObject]@{
        TaskName = $_.TaskName
        State = $_.State
        Actions = ($_.Actions | ForEach-Object { $_.Execute + " " + $_.Arguments }) -join " | "
        Triggers = ($_.Triggers | ForEach-Object { $_.StartBoundary }) -join " | "
    }
}
```

If task names use a different prefix, report the actual prefix and query accordingly.

## Optional manual validation

After tasks are created, optionally trigger one safe task manually:

```powershell
Start-ScheduledTask -TaskName "InsiderTrading_Eddie"
Start-Sleep -Seconds 20
Get-ScheduledTaskInfo -TaskName "InsiderTrading_Eddie"
```

Only trigger Ross if `ROSS_DRY_RUN=true` is confirmed.

If task execution creates logs, inspect only summaries and timestamps. Do not print secrets.

## Uninstall script check

Do not uninstall the tasks.

But inspect whether this file exists and appears available for later cleanup:

```text
install/uninstall_windows.ps1
```

Report its presence and readiness.

## Documentation updates allowed

You may update:

```text
README.md
docs/install_notes_windows.md
docs/checkpoints/README.md
```

Only to reflect CP06 scheduler setup status, task names, and safety notes.

## Required CP06 report

Save report to:

```text
docs/checkpoints/reports/CP06_scheduler_setup_report.md
```

The report must include:

1. Summary of work completed.
2. Files created.
3. Files modified.
4. Files preserved untouched.
5. Precondition checks.
6. Smoke test result.
7. Scheduler script command used.
8. Scheduled tasks created:
   - task name
   - state
   - action summary
   - trigger summary
9. Confirmation no secrets are stored in task arguments.
10. Confirmation `.env` remains local and ignored.
11. Confirmation Ross remains dry-run.
12. Optional manual task validation result, if performed.
13. Log/state file summary, if generated.
14. Confirmation no real email was sent.
15. Confirmation no real Telegram message was sent.
16. Confirmation no commit or push was performed.
17. Uninstall script availability.
18. Risks/blockers.
19. Proposed next checkpoint:
    - CP07 Final Review / Commit / Push if scheduler setup passes
    - or CP06B Scheduler Fixes if scheduler setup reveals issues
20. Awaiting PM Approval section.

## End condition

After saving the report, respond only with:

1. The report path.
2. A short summary.
3. Any blocker requiring PM attention.
4. A statement that you are awaiting PM approval before CP07 or CP06B.
