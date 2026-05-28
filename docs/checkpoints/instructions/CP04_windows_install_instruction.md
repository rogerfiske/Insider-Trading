# CP04 — Windows Install / Local Environment Setup Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP03 is approved. This checkpoint installs the local Windows Python environment and performs dependency/import/smoke-test validation.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## Required source/checkpoint files

Confirm these exist before continuing:

```text
docs/checkpoints/CHECKPOINT_PROTOCOL.md
docs/checkpoints/instructions/CP02_project_scaffold_instruction.md
docs/checkpoints/instructions/CP03_agent_port_instruction.md
docs/checkpoints/reports/CP01_implementation_plan_report.md
docs/checkpoints/reports/CP02_project_scaffold_report.md
docs/checkpoints/reports/CP03_agent_port_report.md
docs/source/original_prompt.md
docs/source/Insider_Trading_Windows_Windsurf_Claude_Code_Handoff_Prompt.md
docs/source/video_transcript.txt
```

If any are missing, report the blocker and stop.

## CP04 goal

Create the Windows local Python environment, install dependencies, validate imports, validate safe smoke tests, and prepare the user for manual `.env` creation.

Do not register scheduled tasks, commit, or push.

## PM decisions carried forward

1. Scout agents are currently prototype prompt-based agents and are not yet verified live-source-grounded.
2. Live Anthropic web-search/tool integration is deferred to a later phase.
3. Preserve original model IDs for now, but verify whether scripts fail due to model/API issues during dry-run checks.
4. Use `SOPHIE_*` environment variables.
5. Ross must remain dry-run-safe by default.
6. Do not force-push under any circumstances.
7. Do not print real API keys or secrets.
8. Do not create Windows Task Scheduler tasks in CP04.
9. Do not commit or push in CP04.

## Allowed actions

You may:

1. Create a Python virtual environment at:
   ```text
   .venv/
   ```

2. Upgrade pip inside the virtual environment.

3. Install dependencies from:
   ```text
   requirements.txt
   ```

4. Run safe import and smoke tests.

5. Create local runtime folders that are gitignored:
   ```text
   .state/logs/
   .state/cache/
   ```

6. Create `.env` only if Roger has already created it manually or explicitly approves creation of a placeholder local `.env`.

7. If `.env` does not exist, create a local placeholder `.env` only after confirming it contains no real secrets and is ignored by Git. The preferred approach is:
   - Copy `.env.example` to `.env`
   - Leave placeholder values only
   - Clearly instruct Roger to edit `.env` locally and never upload or commit it

8. Run:
   ```powershell
   scripts/smoke_test_windows.ps1
   ```

9. Optionally run one dry-run local script only if it does not require a real API key and does not send emails/Telegram messages.

10. Save the checkpoint report to:
   ```text
   docs/checkpoints/reports/CP04_windows_install_report.md
   ```

## Prohibited actions

Do not:

1. Register, modify, or delete Windows Task Scheduler tasks.
2. Send real emails.
3. Send real Telegram messages.
4. Place trades or connect to brokerage APIs.
5. Create, edit, or use real portfolio config files:
   ```text
   config/portfolio_target.json
   config/portfolio_current.json
   ```
6. Print or request real API keys in chat/log output.
7. Commit files.
8. Push to GitHub.
9. Force-push.
10. Modify preserved source files in `docs/source/`.
11. Modify CP01/CP02/CP03 checkpoint reports.
12. Implement live web-search tooling in CP04.

## Required commands / checks

Run and report the results of these commands or PowerShell-equivalent checks.

### Environment setup

```powershell
py -3.11 --version
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip list
```

### Git ignore / credential checks

```powershell
git status --short
git check-ignore -v .env
git check-ignore -v .claude/
git check-ignore -v .state/logs/smoke_test_windows.log
git check-ignore -v config/portfolio_target.json
```

If checking a nonexistent ignored file requires a temporary file, create it, verify ignore behavior, then delete it.

### Python compile checks

```powershell
.\.venv\Scripts\python.exe -m py_compile agents/common.py agents/eddie.py agents/maggie.py agents/frank.py agents/maya.py agents/janet.py agents/sophie.py agents/ross.py
```

### Import checks

Run safe import checks that do not execute agent logic or require live API calls. Example:

```powershell
.\.venv\Scripts\python.exe -c "import anthropic, dotenv; print('dependency imports OK')"
.\.venv\Scripts\python.exe -c "import agents.common; print('agents.common import OK')"
```

If importing any agent triggers live calls, stop and report the design issue.

### Smoke test

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_windows.ps1
```

Report pass/fail output.

## `.env` handling

If `.env` does not exist:

1. Confirm `.env` is ignored by Git.
2. Create a placeholder `.env` by copying `.env.example`, only if doing so does not introduce real secrets.
3. Ensure `.env` remains untracked/ignored.
4. Tell Roger that he must edit `.env` locally in Notepad or Windsurf and insert real values himself.
5. Do not ask Roger to paste keys into Claude Code or ChatGPT.

Recommended local command if needed:

```powershell
Copy-Item .env.example .env
```

Then verify:

```powershell
git check-ignore -v .env
git status --short --ignored
```

## Optional dry-run execution

Only after dependency installation and smoke tests pass, you may run one safe dry-run command if it does not require real API keys. Prefer a non-network test mode if available.

If no safe no-key dry-run exists, do not run an agent. Report that runtime agent testing awaits local `.env` credentials and CP05.

## Documentation update allowed

You may update:

```text
README.md
docs/install_notes_windows.md
docs/checkpoints/README.md
```

Only to reflect CP04 environment setup status and next steps.

Do not over-expand documentation.

## CP04 report requirements

Save report to:

```text
docs/checkpoints/reports/CP04_windows_install_report.md
```

The report must include:

1. Summary of work completed.
2. Files created.
3. Files modified.
4. Files preserved untouched.
5. Python version confirmed.
6. Virtual environment creation result.
7. Dependency installation result.
8. `pip list` or dependency summary.
9. Compile check results.
10. Import check results.
11. Smoke test results.
12. `.env` handling result:
    - existed already / placeholder created / not created
    - confirmation that no real secrets were printed
    - confirmation that `.env` is ignored
13. Git status summary.
14. Confirmation that no scheduled tasks were registered.
15. Confirmation that no real email/Telegram messages were sent.
16. Confirmation that no commit or push was performed.
17. Risks/blockers.
18. Proposed next checkpoint: CP05 Safe Runtime Smoke Tests.
19. Awaiting PM Approval section.

## End condition

After saving the report, respond only with:

1. The report path.
2. A short summary.
3. Any blocker requiring PM attention.
4. A statement that you are awaiting PM approval before CP05.
