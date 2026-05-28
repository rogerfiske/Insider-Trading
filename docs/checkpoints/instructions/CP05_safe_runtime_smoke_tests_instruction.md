# CP05 — Safe Runtime Smoke Tests Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP04 is approved with one required housekeeping correction before runtime tests.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP05 goal

Perform safe runtime smoke tests using Roger’s locally edited `.env`, verify the agents can run without scheduled tasks, confirm outputs/logs/state are created safely, and keep Ross in dry-run mode.

Do not register scheduled tasks, commit, or push.

## Required PM decision from CP04

CP04 showed that `docs/checkpoints/reports/` is ignored by Git because `.gitignore` contains a broad `reports/` pattern.

This must be corrected at the beginning of CP05 because checkpoint reports are part of the project audit trail and should be commit-eligible.

## Required source/checkpoint files

Confirm these exist before continuing:

```text
docs/checkpoints/CHECKPOINT_PROTOCOL.md
docs/checkpoints/instructions/CP02_project_scaffold_instruction.md
docs/checkpoints/instructions/CP03_agent_port_instruction.md
docs/checkpoints/instructions/CP04_windows_install_instruction.md
docs/checkpoints/reports/CP01_implementation_plan_report.md
docs/checkpoints/reports/CP02_project_scaffold_report.md
docs/checkpoints/reports/CP03_agent_port_report.md
docs/checkpoints/reports/CP04_windows_install_report.md
docs/source/original_prompt.md
docs/source/Insider_Trading_Windows_Windsurf_Claude_Code_Handoff_Prompt.md
docs/source/video_transcript.txt
```

If any source or prior checkpoint report is missing, report the blocker and stop.

## Required precondition

Roger must edit the local `.env` file manually before CP05 with at minimum:

```env
ANTHROPIC_API_KEY=<real local key>
ROSS_DRY_RUN=true
```

Optional alert credentials may remain placeholders for CP05 unless explicitly testing email/Telegram dispatch is approved later.

Do not ask Roger to paste secrets into Claude Code or ChatGPT.

Do not print `.env` contents.

## Required housekeeping fix before runtime tests

Update `.gitignore` so checkpoint instructions and checkpoint reports are not ignored.

The project should continue to ignore root/local runtime report folders, but not `docs/checkpoints/reports/`.

Use specific patterns rather than broad patterns if needed.

Required verification:

```powershell
git check-ignore -v docs/checkpoints/reports/CP04_windows_install_report.md
```

Expected result after the fix:

- This command should produce no output and a non-zero exit code, meaning the checkpoint report is not ignored.

Also verify runtime reports/logs still remain ignored if such paths are used:

```powershell
git check-ignore -v .state/logs/smoke_test_windows.log
git check-ignore -v .env
git check-ignore -v .claude/
```

## Allowed actions

You may:

1. Fix `.gitignore` so `docs/checkpoints/reports/` is tracked/trackable.
2. Confirm `.env` exists and is ignored without printing contents.
3. Run safe runtime smoke tests.
4. Run one scout agent, preferably Eddie, using the local `.env` key.
5. Run Sophie only if at least one signal exists.
6. Run Ross only in dry-run mode.
7. Run Janet only against example portfolio files or safe placeholder copies.
8. Inspect generated logs/state metadata without printing secrets.
9. Save the CP05 report to:
   ```text
   docs/checkpoints/reports/CP05_safe_runtime_smoke_tests_report.md
   ```

## Prohibited actions

Do not:

1. Print `.env` contents.
2. Print or request real API keys.
3. Send real emails unless Roger explicitly approved that in writing before this checkpoint. Assume not approved.
4. Send real Telegram messages unless Roger explicitly approved that in writing before this checkpoint. Assume not approved.
5. Place trades or connect to brokerage APIs.
6. Register, modify, or delete Windows Task Scheduler tasks.
7. Create or modify real private portfolio files:
   ```text
   config/portfolio_target.json
   config/portfolio_current.json
   ```
8. Commit files.
9. Push to GitHub.
10. Force-push.
11. Modify preserved source files in `docs/source/`.
12. Implement live web-search/tool integration in CP05.
13. Turn off `ROSS_DRY_RUN`.

## Required verification commands

### Basic environment checks

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip list
git status --short
```

### Credential-safety checks

Do not print `.env`.

Run:

```powershell
Test-Path .env
git check-ignore -v .env
git check-ignore -v .claude/
```

Confirm `.env` exists and is ignored.

### Checkpoint report ignore fix

Run:

```powershell
git check-ignore -v docs/checkpoints/reports/CP04_windows_install_report.md
```

After fixing `.gitignore`, this should indicate the report is not ignored.

If PowerShell reports a non-zero exit code, that is expected when a file is not ignored. Document this clearly.

### Compile/import smoke checks

```powershell
.\.venv\Scripts\python.exe -m py_compile agents/common.py agents/eddie.py agents/maggie.py agents/frank.py agents/maya.py agents/janet.py agents/sophie.py agents/ross.py
.\.venv\Scripts\python.exe -c "import agents.common; print('agents.common import OK')"
```

### Script smoke test

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_windows.ps1
```

## Runtime test plan

Use the helper script where possible.

### Test 1 — Eddie scout runtime test

Run Eddie through the helper script, or directly if the helper script is not suitable.

Preferred:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent eddie
```

If the parameter name differs, inspect the script and use the correct form.

Requirements:

1. Use `.env` without printing it.
2. Confirm whether the Anthropic API call succeeds.
3. Capture stdout/stderr summary in the report.
4. Do not paste full model output if it is lengthy.
5. Confirm whether a signal/state/log entry was created.

If the API fails because the model ID is invalid or unavailable, do not treat that as a project failure. Report it as a model-ID verification blocker for CP05/CP06.

### Test 2 — Sophie consensus smoke test

Run Sophie only after Eddie creates at least one signal/state record.

Preferred:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent sophie
```

Requirements:

1. Confirm Sophie starts.
2. Confirm it reads available signal/state data.
3. Confirm no secret output.
4. Confirm whether consensus is produced or appropriately reports insufficient data.

### Test 3 — Ross dry-run dispatch test

Run Ross only in dry-run mode.

Preferred:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent ross
```

Requirements:

1. Confirm `ROSS_DRY_RUN=true`.
2. Confirm no real email was sent.
3. Confirm no real Telegram message was sent.
4. Confirm dry-run output/log formatting.

### Optional Test 4 — Janet portfolio test

Only run Janet if it can use safe example portfolio files, not real holdings.

Do not create or use:

```text
config/portfolio_target.json
config/portfolio_current.json
```

unless they contain fake/demo data and remain gitignored.

## Handling expected failures

If runtime tests fail due to:

1. Missing/placeholder `ANTHROPIC_API_KEY`
2. Invalid model ID
3. Anthropic API permission/rate issue
4. Scout limitations caused by no live web-search tooling

Then stop runtime escalation and document the exact failure category without printing secrets.

Do not attempt broad rewrites in CP05.

If a small bug prevents the helper script from running but the fix is clearly local and safe, you may fix it and report exactly what changed.

## Documentation updates allowed

You may update:

```text
README.md
docs/install_notes_windows.md
docs/checkpoints/README.md
```

Only to reflect CP05 runtime smoke-test status, known limitations, and the `.gitignore` checkpoint report fix.

## Required CP05 report

Save report to:

```text
docs/checkpoints/reports/CP05_safe_runtime_smoke_tests_report.md
```

The report must include:

1. Summary of work completed.
2. Files created.
3. Files modified.
4. Files preserved untouched.
5. `.gitignore` checkpoint-report fix details.
6. Confirmation that checkpoint reports are no longer ignored.
7. Confirmation that `.env`, `.claude/`, `.venv/`, and runtime logs remain ignored.
8. Confirmation that `.env` exists without printing contents.
9. Python/environment verification.
10. Compile/import verification.
11. Script smoke-test results.
12. Eddie runtime test result.
13. Sophie runtime test result, if run.
14. Ross dry-run result, if run.
15. Janet optional test result, if run.
16. Confirmation that no real email was sent.
17. Confirmation that no real Telegram message was sent.
18. Confirmation that no scheduled tasks were registered.
19. Confirmation that no commit or push was performed.
20. Risks/blockers.
21. Proposed next checkpoint:
    - CP06 Scheduler Setup if runtime tests pass
    - or CP05B Runtime Fixes if runtime tests reveal blockers
22. Awaiting PM Approval section.

## End condition

After saving the report, respond only with:

1. The report path.
2. A short summary.
3. Any blocker requiring PM attention.
4. A statement that you are awaiting PM approval before CP06 or CP05B.
