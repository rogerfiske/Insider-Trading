# Claude Code Handoff Prompt — Insider Trading / Insider Routines Windows 11 Install

You are Claude Code acting as the development team for Roger Fiske. Roger is working in Windsurf IDE on a Windows 11 PC and wants to install, test, and version-control a Windows-compatible implementation of the “Insider Routines” project described in Lewis Jackson’s video “So My AI Agent Does Insider Trading Now.”

Roger’s GitHub repository for this implementation is:

https://github.com/rogerfiske/Insider-Trading

Treat this as a repo-backed implementation project, not a disposable one-shot install. The goal of this first phase is to reproduce the video’s basic project installation and operation on Windows 11, while making the minimum necessary corrections for Windows, Windsurf, Claude Code, GitHub version control, and safe operation.

Do not build future enhancements yet. Future improvements will be planned after Roger runs the basic system and reports feedback.

---

## Operating role

Act as Roger’s implementation team under external PM/technical supervision. Do not silently make major architectural choices. When a phase completes, provide a concise checkpoint report so Roger can paste it back to his senior PM/technical reviewer before continuing.

You must preserve the spirit of the uploaded prompt and video:

- Seven agents: Eddie, Maggie, Frank, Maya, Janet, Sophie, Ross.
- Public-source signal gathering only.
- Local SQLite state store.
- Gmail alerting.
- No automated trades.
- Human decision only.

But you must adapt the implementation for:

- Windows 11.
- Claude Code running inside Windsurf IDE.
- PowerShell-safe commands.
- GitHub repo workflow.
- Secure secrets handling.
- Reproducible install and test reports.

---

## Critical context from Roger

1. The prompt downloaded after the video may include updates made after the video release. Therefore, if the current prompt contains 17 file blocks even though an older instruction says “After all 13 files,” treat 17 blocks as authoritative. Do not “fix” the project back to 13 files.

2. Roger wants the project controlled from the GitHub repository above.

3. Roger wants to get the video project installed and tested first. Future improvements will come later.

4. Roger will send your checkpoint outputs back to his PM/technical reviewer. Make your outputs concrete enough to review.

5. Never ask Roger to paste secrets into chat. Secrets belong only in local `.env` files.

---

## Safety and legal guardrails

This project must remain an informational alerting system only.

Required language in README and startup/status output:

> This project analyzes public information and sends informational alerts only. It does not place trades, recommend that any user trade, or use non-public information. The user is responsible for all investment decisions.

Do not add broker integration, order placement, automated execution, or “recommended trade” language.

Use “signal,” “alert,” “public filing,” “public macro source,” and “informational alert.” Avoid language implying guaranteed returns or illegal insider information.

---

## Repository setup requirements

Preferred local working directory:

```powershell
C:\Users\Minis\CascadeProjects\Insider-Trading
```

If the repo is not already cloned, clone it:

```powershell
git clone https://github.com/rogerfiske/Insider-Trading.git C:\Users\Minis\CascadeProjects\Insider-Trading
```

If the directory already exists, inspect it first. Do not delete existing work.

All project files should live in this repository, not in a loose `C:\Users\<user>\insider-routines` directory, unless Roger explicitly requests a home-directory install later.

The uploaded one-shot prompt uses `$HOME/insider-routines`. For this repo implementation, adapt paths so the project root is the repository root. Use relative-to-file root discovery in Python where practical, for example:

```python
ROOT = Path(__file__).resolve().parents[1]
```

Do not commit `.env`, `.state/`, logs, database files, or local portfolio files that may contain private data.

Create or update `.gitignore` accordingly.

---

## Required repo structure for this phase

Create/adapt the project to this layout:

```text
Insider-Trading/
  README.md
  requirements.txt
  .gitignore
  .env.example
  agents/
    common.py
    eddie.py
    maggie.py
    frank.py
    maya.py
    janet.py
    sophie.py
    ross.py
  config/
    portfolio_target.example.json
    portfolio_current.example.json
  install/
    schedule_windows.ps1
    uninstall_windows.ps1
    smoke_test_windows.ps1
  scripts/
    init_project_windows.ps1
    run_agent.ps1
  docs/
    source/
      original_prompt.md
      video_transcript.txt
    install_notes_windows.md
  .state/
    .gitkeep
```

If the uploaded prompt only provides some of these, create the missing Windows helper scripts and docs.

Do not create Mac/Linux scheduler scripts unless they are already included in the source prompt and you decide to preserve them under `install/legacy/` or `install/cross_platform/`. This first implementation is Windows-first.

---

## Source material handling

Roger has source materials:

1. The downloaded `prompt.md` from the video instructions.
2. A manually copied transcript of the YouTube video.

First, find these files in the local workspace. They may already be in the repo root, downloads folder, or provided to you in the current Windsurf/Claude context.

Expected names may include:

```text
prompt.md
So my agent does insider trading Now.txt
```

Copy them into:

```text
docs/source/original_prompt.md
docs/source/video_transcript.txt
```

If either is not present, continue with the files you have and report what is missing in the checkpoint. Do not fabricate transcript content.

---

## Mandatory Windows corrections

The original prompt mixes Mac/Linux, CMD, and PowerShell assumptions. Make the implementation PowerShell-safe.

Replace or avoid examples such as:

```text
start "" "$env:USERPROFILE\insider-routines\.env"
start https://console.anthropic.com/settings/keys
cp ~/insider-routines/...
python3 $HOME/insider-routines/agents/eddie.py
```

Use Windows/PowerShell-safe equivalents:

```powershell
Start-Process notepad ".env"
Start-Process "https://console.anthropic.com/settings/keys"
Copy-Item "config\portfolio_target.example.json" "config\portfolio_target.json"
py .\agents\eddie.py
```

Use `py` if available; otherwise use `python`. The scripts must detect this robustly.

Do not rely on PowerShell null-conditional syntax like `?.Source` unless you confirm the PowerShell version supports it. Prefer broadly compatible logic:

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

Task Scheduler scripts must:

- Use the repository root as working directory.
- Write logs to `.state\logs`.
- Register tasks under `\InsiderTrading\` or `\InsiderRoutines\`, but document the exact choice.
- Be idempotent.
- Provide an uninstall script.
- Not require admin privileges unless unavoidable.

---

## Anthropic/web-search issue to inspect and report

The original prompt’s agents ask Claude to “read” SEC, Fed, 13F, and on-chain sources. Inspect whether the generated Python code actually provides real web access or deterministic fetchers.

For this initial install phase, do not overbuild a full data ingestion system unless necessary. However, you must not let the README claim the agents truly scrape/read live sources if the implementation only sends a prompt to Claude without web tools or fetchers.

Perform this audit and report one of these statuses:

1. **Real source access exists** — identify how.
2. **No real source access exists** — the current scouts rely only on LLM prompting and may not retrieve live data.
3. **Partial source access exists** — identify which scouts are grounded and which are not.

If no real source access exists, make only the minimum safe correction for Phase 1:

- Update README and install notes to say “prototype agent prompts are installed; live data grounding requires the next enhancement phase,” OR
- Add Anthropic web search tool support if it is straightforward and compatible with the currently installed Anthropic SDK.

Do not pretend unsupported live research works.

---

## Python code standards

For all Python files you create or materially modify:

- Use Python 3.10+ compatible syntax.
- Add type hints to functions.
- Add docstrings to functions with descriptions and arguments.
- Keep PEP 8 formatting.
- Remove unused imports.
- Use `pathlib.Path` for paths.
- Avoid hardcoded user-specific absolute paths in Python.
- Do not print secrets.

If you preserve upstream code exactly from the prompt for traceability, note any noncompliance in your checkpoint and create a follow-up TODO rather than making broad rewrites.

---

## Environment and dependency requirements

Create `requirements.txt` with the minimal packages actually used.

Initial expected packages:

```text
anthropic
python-dotenv
```

If you add testing or linting tools, include them only if actually used.

Create `.env.example` in repo root. Do not commit `.env`.

Required `.env.example` fields:

```dotenv
ANTHROPIC_API_KEY=
GMAIL_USER=
GMAIL_APP_PASSWORD=
ALERT_TO_EMAIL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

If the code uses different names, normalize or document the difference.

---

## Installation scripts to create

Create `scripts/init_project_windows.ps1` that:

1. Confirms it is running from the repository root.
2. Detects Python.
3. Creates `.venv` if missing.
4. Installs `requirements.txt` into `.venv`.
5. Creates `.env` from `.env.example` if missing.
6. Creates `.state\logs`.
7. Copies portfolio example JSON files to local editable JSON files if missing.
8. Opens `.env` in Notepad for Roger to fill in.
9. Prints the next command to run after `.env` is filled.

Create `install/smoke_test_windows.ps1` that:

1. Uses the venv Python.
2. Runs import checks.
3. Initializes the database if applicable.
4. Runs `janet.py` first because it can work from local portfolio JSON and should not require live web access.
5. Runs `sophie.py` and `ross.py` in dry-run or safe mode if available.
6. Captures output to `.state\logs\smoke_test_windows.log`.

If dry-run mode does not exist, add it where appropriate, especially for Ross, so a smoke test does not unexpectedly email Roger unless explicitly requested.

Create `scripts/run_agent.ps1` that accepts an agent name:

```powershell
.\scripts\run_agent.ps1 janet
.\scripts\run_agent.ps1 sophie
```

Validate allowed agent names.

---

## Git workflow requirements

Use Git throughout.

At minimum:

1. Confirm remote:

```powershell
git remote -v
```

2. Confirm branch:

```powershell
git branch --show-current
```

3. Make changes.
4. Run quality gates.
5. Commit to `main` only after quality gates pass.
6. Push to `origin/main`.
7. Include the commit hash in your final completion report.

If push fails because authentication is unavailable, commit locally and report the exact failure plus the local commit hash.

Do not commit secrets.

---

## Required quality gates

Before committing, run and report results:

```powershell
git status --short
py -m compileall agents
.\install\smoke_test_windows.ps1
```

If `py` is unavailable, use the detected venv Python.

Also run:

```powershell
git diff --check
```

If there are no formal tests yet, state that explicitly and propose a future test plan, but do not implement a broad test suite in this first install pass unless it is small and directly useful.

---

## Checkpoint reports required

Stop after each checkpoint and provide a concise report. Do not continue to the next checkpoint until Roger approves, unless Roger has already told you to proceed autonomously.

### Checkpoint 0 — Environment and repo inspection

Report:

- Current working directory.
- Whether repo was cloned or already existed.
- Current branch.
- Remote URL.
- Python version and command path.
- PowerShell version.
- Whether source `prompt.md` and transcript were found.
- Whether the prompt contains 17 file blocks.
- Any blockers.

### Checkpoint 1 — Implementation plan

Report:

- Files you will create/modify.
- Whether you will install repo-native rather than `$HOME\insider-routines`.
- Any minimal corrections you need to make to original files.
- Your plan for secrets handling.
- Your plan for smoke testing.

### Checkpoint 2 — Files written/adapted

Report:

- Created files.
- Modified files.
- Any original prompt content preserved exactly.
- Any Windows path corrections made.
- Any known limitation retained.

### Checkpoint 3 — Smoke test results

Report:

- Commands run.
- Pass/fail status.
- Log file paths.
- Whether any email was sent.
- Whether any live web/API access occurred.
- Any errors and proposed fix.

### Checkpoint 4 — Scheduler install readiness

Report:

- Scheduled task names that would be created.
- Schedule times.
- Working directory.
- Log paths.
- Exact command to install tasks.
- Exact command to uninstall tasks.

Do not register scheduled tasks until Roger confirms.

### Checkpoint 5 — Final commit/push report

After Roger approves finalizing:

- Run quality gates.
- Commit.
- Push to `origin/main`.
- Report commit hash.
- Report files changed.
- Report quality gate results.
- Report remaining TODOs.

---

## First task now

Start with Checkpoint 0 only.

Do not modify files yet except for safe inspection if needed.

Return the Checkpoint 0 report in this format:

```text
Checkpoint 0 — Environment and repo inspection

Working directory:
Repository status:
Branch:
Remote:
Python:
PowerShell:
Source prompt found:
Transcript found:
Prompt file-block count:
Windows/Windsurf concerns discovered:
Blockers:
Recommended next step:
```

Additional mandatory .gitignore requirement:

Create or update .gitignore before any commit and include, at minimum:

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

Before committing, explicitly run and report:

git status --short
git check-ignore -v .env
git check-ignore -v config/portfolio_target.json
git check-ignore -v .state/logs/smoke_test_windows.log

Do not commit any local credential, portfolio, log, database, cache, or runtime-output file.
```