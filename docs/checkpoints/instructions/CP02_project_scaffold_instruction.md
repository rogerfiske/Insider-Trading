# CP02 — Project Scaffold Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

This checkpoint is approved after review of CP01.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## PM decisions from CP01 review

1. CP01 is approved.
2. Defer live Anthropic web-search/tool integration to a later phase. For now, document clearly that scout agents are prototype prompt-based agents and are not live-source-grounded.
3. Preserve the original model IDs from the downloaded prompt for now, but document that they may need verification before real operation.
4. Use `SOPHIE_*` environment variable names where the code actually expects them. Document the original DELPHI/SOPHIE naming mismatch.
5. Do not force-push to GitHub. If remote history conflicts occur, stop and report.
6. Do not request or print real API keys.
7. Do not create `.env` in this checkpoint.
8. Do not install dependencies in this checkpoint.
9. Do not set up Windows Task Scheduler in this checkpoint.
10. Do not implement or port the 17 agent/application files in this checkpoint unless explicitly listed below. CP02 is scaffold-only.

## Goal of this checkpoint

Create the safe project scaffold, repository metadata, documentation shell, security exclusions, and checkpoint audit structure.

Do not port/adapt the executable agent files yet. That will be CP03.

## Source files that must be preserved exactly

Do not delete, rename, overwrite, or edit these files:

```text
docs/source/original_prompt.md
docs/source/Insider_Trading_Windows_Windsurf_Claude_Code_Handoff_Prompt.md
docs/source/video_transcript.txt
docs/checkpoints/CHECKPOINT_PROTOCOL.md
```

## Allowed actions

You may:

1. Create or confirm the checkpoint folders:
   ```text
   docs/checkpoints/instructions/
   docs/checkpoints/reports/
   ```

2. Create or update:
   ```text
   docs/checkpoints/README.md
   ```

3. Initialize Git in the current working directory if `.git` does not exist:
   ```powershell
   git init
   git branch -M main
   ```

4. Add the GitHub remote only if it does not already exist:
   ```powershell
   git remote add origin https://github.com/rogerfiske/Insider-Trading.git
   ```

5. Create or update:
   ```text
   .gitignore
   .env.example
   README.md
   requirements.txt
   docs/install_notes_windows.md
   .state/.gitkeep
   config/portfolio_target.example.json
   config/portfolio_current.example.json
   ```

6. Create empty placeholder package folders/files only:
   ```text
   agents/__init__.py
   scripts/.gitkeep
   install/.gitkeep
   install/cross_platform/.gitkeep
   config/.gitkeep
   ```

7. Save the checkpoint report to:
   ```text
   docs/checkpoints/reports/CP02_project_scaffold_report.md
   ```

8. Run non-destructive verification commands such as:
   ```powershell
   git status --short
   git remote -v
   git branch --show-current
   git check-ignore -v .env
   git check-ignore -v config/portfolio_target.json
   git check-ignore -v .state/logs/smoke_test_windows.log
   ```

## Prohibited actions

Do not:

1. Install dependencies.
2. Create a Python virtual environment.
3. Create `.env`.
4. Request or print real API keys.
5. Port or adapt the executable agent files from the 17 source blocks.
6. Create or modify Task Scheduler tasks.
7. Run agent scripts.
8. Commit files.
9. Push to GitHub.
10. Force-push under any circumstances.
11. Delete, rename, overwrite, or edit source artifacts in `docs/source/`.
12. Modify `docs/checkpoints/CHECKPOINT_PROTOCOL.md` unless there is an obvious typo in a path that blocks this checkpoint.

## Required `.gitignore`

Create or update `.gitignore` so it includes at minimum:

```gitignore
# Secrets
.env
.env.*
!.env.example

# Python environments and caches
.venv/
venv/
env/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Runtime state
.state/*
!.state/.gitkeep

# Local output / generated files
logs/
reports/
data/raw/
data/cache/
*.log
*.db
*.sqlite
*.sqlite3

# Private portfolio/config files
config/portfolio_target.json
config/portfolio_current.json

# IDE / OS
.vscode/
.idea/
.windsurf/
.DS_Store
Thumbs.db
```

## Required `.env.example`

Create a safe root-level `.env.example`.

It must contain placeholders only and no real secrets.

Include at minimum:

```env
ANTHROPIC_API_KEY=
GMAIL_TO=
GMAIL_USER=
GMAIL_APP_PASSWORD=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

SOPHIE_MIN_AGREE=2
SOPHIE_WINDOW_DAYS=14

JANET_MIN_DELTA_PCT=3
JANET_MIN_POSITION=0.02

ROSS_DRY_RUN=true
```

Do not create `.env`.

## Required `requirements.txt`

For Phase 1, keep this minimal:

```text
anthropic
python-dotenv
```

Do not install these dependencies yet.

## Required README content

Create or update `README.md` with:

1. Project purpose.
2. Windows 11 + Windsurf + Claude Code target environment.
3. Safety disclaimer: informational research/alerting prototype only; not trading advice; does not place trades.
4. Credential warning: never commit `.env` or private portfolio files.
5. Current limitation: scout agents are prompt-based prototypes and do not yet have verified live web/source access.
6. Basic project structure.
7. Checkpoint workflow reference:
   ```text
   docs/checkpoints/CHECKPOINT_PROTOCOL.md
   ```

## Required `docs/checkpoints/README.md`

Create or update it to document:

1. `instructions/` contains PM-approved checkpoint instruction files.
2. `reports/` contains Claude Code checkpoint reports.
3. Claude Code must not proceed beyond a checkpoint until PM approval is received.
4. Credential files, `.env` files, logs, runtime outputs, databases, and private portfolio files must never be committed.

## Required `docs/install_notes_windows.md`

Create or update this as a short Windows-first planning note.

Include:

1. Windows PowerShell 5.1 compatibility requirement.
2. Use `py` / Python 3.11.9.
3. Virtual environment will be created in a later checkpoint.
4. Task Scheduler setup is deferred.
5. Live web/source grounding is deferred to a later enhancement phase.
6. `SOPHIE_*` names are used because the code reads them, even though the source prompt references DELPHI naming in places.

## Required portfolio example files

Create safe example files only:

```text
config/portfolio_target.example.json
config/portfolio_current.example.json
```

Use placeholder/demo symbols only. Do not include real holdings.

## Git initialization rules

If `.git` does not exist:

```powershell
git init
git branch -M main
```

If no remote exists:

```powershell
git remote add origin https://github.com/rogerfiske/Insider-Trading.git
```

If a remote already exists, do not overwrite it. Report it.

Do not commit or push in CP02.

## Required verification

At the end of CP02, run and report:

```powershell
git status --short
git remote -v
git branch --show-current
git check-ignore -v .env
git check-ignore -v config/portfolio_target.json
git check-ignore -v .state/logs/smoke_test_windows.log
```

If any `git check-ignore` command fails because the file does not exist, create a harmless temporary empty file only if necessary, verify ignore behavior, then delete the temporary file before ending the checkpoint.

## CP02 report requirements

Save the report to:

```text
docs/checkpoints/reports/CP02_project_scaffold_report.md
```

The report must include:

1. Summary of work completed.
2. Files created.
3. Files modified.
4. Files explicitly preserved untouched.
5. Git initialization status.
6. Remote status.
7. `.gitignore` verification results.
8. Confirmation that no `.env` was created.
9. Confirmation that no real credentials were requested, printed, or committed.
10. Confirmation that no dependencies were installed.
11. Confirmation that no agent/application porting was performed.
12. Confirmation that no Task Scheduler tasks were created.
13. Risks/blockers.
14. Proposed next checkpoint: CP03 Agent Port.
15. Awaiting PM Approval section.

## End condition

After saving the report, respond only with:

1. The report path.
2. A short summary.
3. Any blocker requiring PM attention.
4. A statement that you are awaiting PM approval before CP03.
