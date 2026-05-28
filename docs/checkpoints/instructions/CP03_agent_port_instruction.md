# CP03 — Agent Port Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP02 is approved with two required housekeeping fixes at the beginning of CP03.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## Required source files

These source files must be preserved exactly and must not be edited:

```text
docs/source/original_prompt.md
docs/source/Insider_Trading_Windows_Windsurf_Claude_Code_Handoff_Prompt.md
docs/source/video_transcript.txt
docs/checkpoints/CHECKPOINT_PROTOCOL.md
docs/checkpoints/instructions/CP02_project_scaffold_instruction.md
docs/checkpoints/reports/CP01_implementation_plan_report.md
docs/checkpoints/reports/CP02_project_scaffold_report.md
```

If `docs/checkpoints/CHECKPOINT_PROTOCOL.md` is missing, stop and report that blocker. Do not continue CP03 until it exists.

## CP03 goal

Port/adapt the 17 original prompt file blocks from `docs/source/original_prompt.md` into the scaffolded repository, with Windows 11 + PowerShell 5.1 + Windsurf + Claude Code compatibility.

Do not install dependencies, create `.env`, register scheduled tasks, commit, or push.

## PM decisions carried forward

1. Defer live Anthropic web-search/tool integration to a later phase.
2. Scout agents may remain prototype prompt-based agents, but code/docs must clearly state that they are not yet verified live-source-grounded.
3. Preserve the original model IDs for now, but document that they may need verification before real operation.
4. Use `SOPHIE_*` environment variable names where the code expects them.
5. Document the original DELPHI/SOPHIE naming mismatch.
6. Do not force-push under any circumstances.
7. Do not request or print real API keys.
8. Do not create `.env`.
9. Do not create Windows Task Scheduler tasks.
10. Do not run live agent operations requiring API access.

## Required housekeeping fixes before porting

1. Confirm `docs/checkpoints/CHECKPOINT_PROTOCOL.md` exists.
2. Add `.claude/` to `.gitignore` if it is not already ignored.
3. Verify `.claude/` is ignored with:
   ```powershell
   git check-ignore -v .claude/
   ```

## File port/adaptation requirements

Extract and adapt the 17 file blocks from `docs/source/original_prompt.md`.

### Python agent files

Create or update:

```text
agents/common.py
agents/eddie.py
agents/maggie.py
agents/frank.py
agents/maya.py
agents/janet.py
agents/sophie.py
agents/ross.py
```

Requirements:

1. Preserve the functional intent of the original prompt.
2. Use repo-relative paths instead of `$HOME/insider-routines`.
3. Load environment values from a root `.env` file when present, but do not require `.env` during import.
4. Do not print secrets.
5. Add or preserve type hints.
6. Add or preserve docstrings for functions.
7. Make imports clean and remove unused imports where practical.
8. Keep Python 3.11-compatible code.
9. Avoid hard-coded absolute user-specific paths.
10. Add `main()` entry points guarded by:
    ```python
    if __name__ == "__main__":
        main()
    ```
11. Do not perform live API calls on import.
12. Do not run agent logic unless executed directly.
13. Include safe error handling for missing API keys/config.
14. Make Ross dry-run-safe by default unless environment/config explicitly allows non-dry-run behavior.

### Prototype live-source limitation

Because true source-grounded web/API retrieval is deferred, add clear comments and README/install-note documentation that scout outputs depend on the current prompt/API setup and are not yet independently verified live-source-grounded.

Do not implement Anthropic web search in CP03 unless it is already present in the original source blocks and requires no dependency or credential change. If it is absent, document it as a CP08+ enhancement candidate.

## Install script requirements

Create or update:

```text
install/schedule_windows.ps1
install/uninstall_windows.ps1
```

Requirements:

1. PowerShell 5.1 compatible.
2. No null-conditional syntax such as `?.`.
3. Use repo-root-relative paths.
4. Do not require administrator privileges unless absolutely necessary.
5. Do not run during CP03.
6. Include safe logging paths under `.state/logs/`.
7. Use `py` or repo virtual environment paths in a way suitable for later CP04/CP06 activation.
8. Do not register tasks in CP03.

## Cross-platform preservation requirements

Preserve Mac/Linux scripts from the original 17 blocks under:

```text
install/cross_platform/schedule_mac.sh
install/cross_platform/schedule_linux.sh
install/cross_platform/uninstall_mac.sh
install/cross_platform/uninstall_linux.sh
```

These may be copied verbatim or minimally annotated as preserved upstream scripts, but they are not the Windows-first execution path.

## Helper script requirements

Create these helper scripts:

```text
scripts/run_agent.ps1
scripts/smoke_test_windows.ps1
scripts/init_project_windows.ps1
```

Requirements:

1. PowerShell 5.1 compatible.
2. Use repo-root-relative paths.
3. `run_agent.ps1` should run a named agent script without requiring scheduled tasks.
4. `smoke_test_windows.ps1` should perform safe checks only:
   - Python version
   - expected files exist
   - imports compile or import safely
   - `.env.example` exists
   - `.gitignore` protects `.env`
   - no live API calls required
5. `init_project_windows.ps1` should prepare local folders and give user instructions, but must not create real `.env` with secrets.
6. Do not execute helper scripts in CP03 unless the command is safe and does not require dependencies/API keys.

## Documentation updates

Update these files as needed:

```text
README.md
docs/install_notes_windows.md
docs/checkpoints/README.md
```

Required documentation additions:

1. CP03 added agent source porting.
2. Windows-first workflow remains non-operational until CP04 installs dependencies and local `.env` is created by the user.
3. Scout agents are not yet verified live-source-grounded.
4. `.claude/` is ignored.
5. Model IDs are preserved from the source prompt and may need verification.
6. `SOPHIE_*` is used consistently, with note on DELPHI/SOPHIE source mismatch.

## Prohibited actions

Do not:

1. Install dependencies.
2. Create a virtual environment.
3. Create `.env`.
4. Request or print real API keys.
5. Register, modify, or delete Windows Task Scheduler tasks.
6. Run live agents requiring API access.
7. Commit files.
8. Push to GitHub.
9. Force-push.
10. Delete source artifacts.
11. Modify portfolio real config files.
12. Create `config/portfolio_target.json` or `config/portfolio_current.json`.

## Allowed verification

You may run:

```powershell
git status --short
git check-ignore -v .env
git check-ignore -v .claude/
py -3.11 --version
py -3.11 -m py_compile agents/common.py agents/eddie.py agents/maggie.py agents/frank.py agents/maya.py agents/janet.py agents/sophie.py agents/ross.py
```

If `python-dotenv` or `anthropic` is missing, do not install dependencies. Instead, report that full import/runtime smoke tests are deferred to CP04.

## Required CP03 report

Save report to:

```text
docs/checkpoints/reports/CP03_agent_port_report.md
```

The report must include:

1. Summary of work completed.
2. Housekeeping fixes completed.
3. Files created.
4. Files modified.
5. Files preserved untouched.
6. Mapping of all 17 source blocks to final repo paths.
7. Windows compatibility changes made.
8. PowerShell 5.1 compatibility changes made.
9. Credential-safety measures confirmed.
10. Prototype/live-source limitations documented.
11. Validation commands run and outputs.
12. Confirmation that no dependencies were installed.
13. Confirmation that no `.env` was created.
14. Confirmation that no scheduled tasks were registered.
15. Confirmation that no commit or push was performed.
16. Risks/blockers.
17. Proposed next checkpoint: CP04 Windows Install / Local Environment Setup.
18. Awaiting PM Approval section.

## End condition

After saving the report, respond only with:

1. The report path.
2. A short summary.
3. Any blocker requiring PM attention.
4. A statement that you are awaiting PM approval before CP04.
