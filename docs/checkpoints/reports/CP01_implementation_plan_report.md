# Checkpoint 1 -- Implementation Plan Report

**Date:** 2026-05-27
**Status:** Awaiting PM approval
**Author:** Claude Code (Opus 4.6)

---

## 1. Proposed Final Project Structure

```text
Insider-Trading/                          (repo root)
  README.md                               NEW -- project readme with legal disclaimer
  requirements.txt                        NEW -- minimal deps
  .gitignore                              NEW -- comprehensive exclusion list
  .env.example                            NEW -- adapted from prompt's config/.env.example
  agents/
    __init__.py                           NEW -- empty, makes agents a package
    common.py                             ADAPTED from prompt block #1
    eddie.py                              ADAPTED from prompt block #2
    maggie.py                             ADAPTED from prompt block #3
    frank.py                              ADAPTED from prompt block #4
    maya.py                               ADAPTED from prompt block #5
    janet.py                              ADAPTED from prompt block #6
    sophie.py                             ADAPTED from prompt block #7
    ross.py                               ADAPTED from prompt block #8
  config/
    portfolio_target.example.json         VERBATIM from prompt block #16
    portfolio_current.example.json        VERBATIM from prompt block #17
  install/
    schedule_windows.ps1                  ADAPTED from prompt block #11 (PS 5.1 safe)
    uninstall_windows.ps1                 ADAPTED from prompt block #14 (PS 5.1 safe)
    smoke_test_windows.ps1                NEW -- per handoff requirements
    cross_platform/
      schedule_mac.sh                     PRESERVED VERBATIM from prompt block #9
      schedule_linux.sh                   PRESERVED VERBATIM from prompt block #10
      uninstall_mac.sh                    PRESERVED VERBATIM from prompt block #12
      uninstall_linux.sh                  PRESERVED VERBATIM from prompt block #13
  scripts/
    init_project_windows.ps1              NEW -- per handoff requirements
    run_agent.ps1                         NEW -- per handoff requirements
  docs/
    source/
      original_prompt.md                  EXISTS -- preserved exactly
      Insider_Trading_Windows_Windsurf_Claude_Code_Handoff_Prompt.md
                                          EXISTS -- preserved exactly
      video_transcript.txt                EXISTS -- preserved exactly
    checkpoints/
      README.md                           NEW -- checkpoint audit trail docs
      instructions/                       PM-approved checkpoint instructions
      reports/                            Claude Code checkpoint reports
    install_notes_windows.md              NEW -- Windows-specific install guide
  .state/
    .gitkeep                              NEW -- placeholder so .state/ is tracked
```

Total: ~30 files (17 from prompt + ~13 new/support files)

---

## 2. Git Initialization and Remote Setup

Commands to execute (in order):

```powershell
git init
git remote add origin https://github.com/rogerfiske/Insider-Trading.git
git branch -M main
```

Verification:

```powershell
git remote -v
git branch --show-current
```

Note: The GitHub repo at rogerfiske/Insider-Trading must already exist (empty or with a compatible history). If it has existing commits, we may need to pull first or force-push. Will verify during implementation.

---

## 3. Windows PowerShell 5.1-Safe Install Plan

The original prompt's schedule_windows.ps1 uses PS 7+ syntax:

```powershell
# ORIGINAL (BROKEN on PS 5.1):
$Python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
```

Fix: Replace with the broadly compatible pattern from the handoff prompt:

```powershell
$PythonCmd = Get-Command py -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command python -ErrorAction SilentlyContinue
}
if (-not $PythonCmd) {
    throw "Python was not found on PATH. Install Python 3.10+ and retry."
}
$Python = $PythonCmd.Source
```

All PS scripts will:

- Use repo root as working directory (not `$HOME\insider-routines`)
- Use `-ErrorAction SilentlyContinue` (not null-conditional)
- Use `Join-Path` for path construction
- Work without admin privileges (Task Scheduler tasks run as current user)

---

## 4. Python Virtual Environment Plan

The `init_project_windows.ps1` script will:

1. Detect Python: `py --version` (fallback: `python --version`)
2. Create venv: `py -m venv .venv`
3. Activate: `.\.venv\Scripts\Activate.ps1`
4. Install deps: `.\.venv\Scripts\pip install -r requirements.txt`
5. Verify: `.\.venv\Scripts\python -c "import anthropic; import dotenv"`

The `run_agent.ps1` and `smoke_test_windows.ps1` scripts will use `.\.venv\Scripts\python.exe` to ensure the venv Python is always used.

The `schedule_windows.ps1` will also use the venv Python path (not the system `py`) for Task Scheduler actions.

---

## 5. Dependency Plan

`requirements.txt` contents:

```text
anthropic
python-dotenv
```

No pinned versions for Phase 1. No test/lint tools added unless requested.

---

## 6. Credential-Protection Plan

- `.env` lives in repo root (never committed)
- `.env.example` lives in repo root (committed, no real values)
- `.gitignore` blocks `.env`, `.env.*`, but allows `!.env.example`
- `config/portfolio_target.json` and `portfolio_current.json` are gitignored (only `.example.json` versions are committed)
- `.state/` contents gitignored (except `.gitkeep`)
- No secrets printed to console by any script
- No secrets requested in chat -- Roger fills `.env` via Notepad
- Pre-commit verification: `git check-ignore -v .env`

---

## 7. .gitignore Plan

Will use the exact list from the handoff prompt:

```text
.env
.env.*
!.env.example
.venv/
venv/
env/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.state/*
!.state/.gitkeep
logs/
reports/
data/raw/
data/cache/
*.log
*.db
*.sqlite
*.sqlite3
config/portfolio_target.json
config/portfolio_current.json
.vscode/
.idea/
.windsurf/
.DS_Store
Thumbs.db
```

---

## 8. .env / .env.example Plan

The original prompt places `.env.example` in `config/.env.example`. The handoff requires `.env.example` in repo root.

Adaptations needed:

- The original uses "Mercury" (old name for Ross) in comments -- normalize to "Ross"
- The original uses `DELPHI_MIN_AGREE` / `DELPHI_WINDOW_DAYS` in comments, but the actual code (`sophie.py`) reads `SOPHIE_MIN_AGREE` / `SOPHIE_WINDOW_DAYS` -- this is a naming mismatch in the original prompt. Plan: Use the names the CODE actually reads (`SOPHIE_*`), note the discrepancy in `install_notes_windows.md`
- The handoff requires `ALERT_TO_EMAIL=` but the code reads `GMAIL_TO`. Plan: Use `GMAIL_TO` (matching the code) and document the mapping.
- Model names in `.env.example` comments reference future model versions. Will document that users should verify model availability.

---

## 9. How the 17 Original Prompt File Blocks Will Be Adapted

| Block | File | Treatment |
|-------|------|-----------|
| 1 | agents/common.py | ADAPT: Change ROOT from `Path.home()/"insider-routines"` to `Path(__file__).resolve().parents[1]` (repo root). Change ENV_PATH, error messages. Add `--dry-run` support for smoke testing. |
| 2 | agents/eddie.py | MINIMAL ADAPT: sys.path preserved. Content/prompts verbatim. |
| 3 | agents/maggie.py | Same as eddie. |
| 4 | agents/frank.py | Same as eddie. |
| 5 | agents/maya.py | Same as eddie. |
| 6 | agents/janet.py | ADAPT: Change CONFIG path from `Path.home()/"insider-routines"/"config"` to `Path(__file__).resolve().parents[1] / "config"`. Logic preserved. |
| 7 | agents/sophie.py | MINIMAL -- no path refs beyond common import. |
| 8 | agents/ross.py | ADAPT: Add `--dry-run` flag so smoke test doesn't send email. Logic preserved. |
| 9 | install/schedule_mac.sh | PRESERVE VERBATIM in `install/cross_platform/` |
| 10 | install/schedule_linux.sh | PRESERVE VERBATIM in `install/cross_platform/` |
| 11 | install/schedule_windows.ps1 | ADAPT: Fix PS 5.1 compat. Change paths to repo root. Use venv Python. |
| 12 | install/uninstall_mac.sh | PRESERVE VERBATIM in `install/cross_platform/` |
| 13 | install/uninstall_linux.sh | PRESERVE VERBATIM in `install/cross_platform/` |
| 14 | install/uninstall_windows.ps1 | ADAPT: Fix paths to repo root. Fix PS 5.1 issues. |
| 15 | config/.env.example | ADAPT to repo root `.env.example`. Fix DELPHI/SOPHIE naming. Fix Mercury/Ross naming. |
| 16 | config/portfolio_target.example.json | VERBATIM. |
| 17 | config/portfolio_current.example.json | VERBATIM. |

---

## 10. Files Preserved as Original Source Artifacts

These three files are preserved exactly as they exist now:

- `docs/source/original_prompt.md`
- `docs/source/Insider_Trading_Windows_Windsurf_Claude_Code_Handoff_Prompt.md`
- `docs/source/video_transcript.txt`

They are documentation artifacts, not executable code.

---

## 11. Mac/Linux Files -- Preserved but Not Used

Four files moved to `install/cross_platform/`:

- `install/cross_platform/schedule_mac.sh` (from block #9)
- `install/cross_platform/schedule_linux.sh` (from block #10)
- `install/cross_platform/uninstall_mac.sh` (from block #12)
- `install/cross_platform/uninstall_linux.sh` (from block #13)

Preserved verbatim for traceability. They still reference `$HOME/insider-routines` and would need adaptation for Mac/Linux use. NOT in scope for Phase 1.

---

## 12. Web Access / Data Source Audit

**CRITICAL FINDING: No real source access exists.**

| Agent | Data Method | Real Web Access? |
|-------|-------------|-----------------|
| Eddie | Claude prompt asking to "query SEC EDGAR" | NO -- no web tool attached to SDK call |
| Maggie | Claude prompt asking to "pull 13F-HR filings" | NO -- no web tool attached |
| Frank | Claude prompt asking to "pull Fed speeches" | NO -- no web tool attached |
| Maya | Claude prompt asking to "query on-chain explorer" | NO -- no web tool attached |
| Janet | Reads local JSON files | YES -- deterministic local data |
| Sophie | Reads local SQLite DB | YES -- deterministic local logic |
| Ross | Sends Gmail SMTP / Telegram | YES -- real delivery |

**Assessment: STATUS 2** -- No real source access exists for eddie/maggie/frank/maya.

**Phase 1 correction plan** (per handoff -- minimum safe correction):

- Update README to state: "Prototype agent prompts are installed. Scouts eddie/maggie/frank/maya send prompts to Claude but do NOT have live web access. Responses reflect Claude's training knowledge, not real-time data. Live data grounding requires the next enhancement phase."
- Do NOT attempt to add web search tools in Phase 1 unless PM explicitly requests it.

---

## 13. Proposed Smoke Tests

`install/smoke_test_windows.ps1` will:

1. Verify `.venv` exists and Python works
2. Run import checks (`import anthropic; import dotenv`)
3. Initialize the database (import common triggers table creation)
4. Run `janet.py` (works from local JSON, no API key needed)
5. Run `sophie.py` (reads DB, no API key needed)
6. Run `ross.py --dry-run` (no email sent, no API key needed)
7. Capture all output to `.state\logs\smoke_test_windows.log`

Tests NOT run in smoke test: eddie/maggie/frank/maya (require valid `ANTHROPIC_API_KEY` and make paid API calls).

---

## 14. Proposed Checkpoint Sequence After Checkpoint 1

| Checkpoint | Description |
|------------|-------------|
| CP02 | Files written/adapted. Report: files created, modifications, known limitations. |
| CP03 | Smoke test results. After Roger fills .env: run init, install deps, run smoke test. |
| CP04 | Scheduler install readiness. Present Task Scheduler config. DO NOT register tasks. |
| CP05 | Final commit/push report. Quality gates, commit, push, report hash and TODOs. |

---

## 15. Risks and Blockers Requiring PM Approval

### RISK 1 -- GitHub push authentication (MEDIUM)

gh CLI is not installed. Push will rely on git credential manager. If it fails, we commit locally and report.

### RISK 2 -- Model names may not exist yet (LOW)

The `.env.example` references model IDs that may not be current. Leave as defaults and document.

**PM decision needed:** Preserve original model IDs or update to current?

### RISK 3 -- DELPHI vs SOPHIE env var naming (LOW)

Original prompt uses DELPHI_* but code reads SOPHIE_*. Plan: Use SOPHIE_* (matching code).

### RISK 4 -- No live data access for scouts (HIGH -- functional gap)

See section 12. Eddie/Maggie/Frank/Maya cannot fetch live data.

**PM decision needed:** Add Anthropic web_search tool support in Phase 1 or defer to Phase 2?

### RISK 5 -- GitHub repo may have existing commits (LOW)

If remote has commits, push may fail. Plan: attempt merge first, report if blocked.

**PM decision needed:** Merge or force-push if conflict?

---

## Default Recommendations (if PM says "proceed at your discretion")

1. Preserve original model IDs, document in install notes.
2. Defer web search to Phase 2.
3. Attempt merge first; if conflict, commit locally and report.

---

**AWAITING PM APPROVAL BEFORE IMPLEMENTATION**
