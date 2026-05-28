# Insider-Trading Project Checkpoint Protocol

## Purpose

This document defines the checkpoint workflow for coordinating between:

- Roger / PM
- ChatGPT as senior project manager and technical reviewer
- Claude Code as the implementation team inside Windsurf IDE

The goal is to reduce chat context usage, preserve a permanent project audit trail, and make each Claude Code step reviewable before implementation continues.

---

## Recommended Repository Folder Structure

Create this folder structure inside the repo:

```text
docs/
  source/
    original_prompt.md
    Insider_Trading_Windows_Windsurf_Claude_Code_Handoff_Prompt.md
    video_transcript.txt

  checkpoints/
    instructions/
      CP00_environment_inspection_instruction.md
      CP01_implementation_plan_instruction.md
      CP02_project_scaffold_instruction.md
      CP03_agent_port_instruction.md
      CP04_windows_install_instruction.md
      CP05_smoke_tests_instruction.md
      CP06_scheduler_setup_instruction.md
      CP07_final_review_commit_push_instruction.md

    reports/
      CP00_environment_inspection_report.md
      CP01_implementation_plan_report.md
      CP02_project_scaffold_report.md
      CP03_agent_port_report.md
      CP04_windows_install_report.md
      CP05_smoke_tests_report.md
      CP06_scheduler_setup_report.md
      CP07_final_review_commit_push_report.md
```

---

## Workflow

### Step 1 — ChatGPT creates a checkpoint instruction

ChatGPT provides Roger a downloadable Markdown checkpoint instruction file.

Roger saves the file into:

```text
docs/checkpoints/instructions/
```

### Step 2 — Roger gives Claude Code a short pointer prompt

Instead of pasting the full instruction, Roger tells Claude Code:

```text
Read and execute the checkpoint instruction at:

docs/checkpoints/instructions/CP01_implementation_plan_instruction.md

Follow it exactly. Save your checkpoint report to:

docs/checkpoints/reports/CP01_implementation_plan_report.md

Do not proceed beyond the checkpoint. End by stating that the checkpoint report has been saved and that you are awaiting PM approval.
```

### Step 3 — Claude Code executes the checkpoint

Claude Code reads the instruction file, performs only the allowed work, then writes the checkpoint report.

### Step 4 — Roger uploads Claude’s checkpoint report to ChatGPT

Roger uploads the generated report file to ChatGPT for review.

ChatGPT reviews the report and creates the next checkpoint instruction.

---

## Rules for Claude Code

Claude Code must follow these rules for every checkpoint:

1. Read the checkpoint instruction file before acting.
2. Do only the work authorized in that checkpoint.
3. Do not skip ahead.
4. Do not print, request, or commit real credentials.
5. Do not commit files unless the checkpoint explicitly authorizes it.
6. Do not push to GitHub unless the checkpoint explicitly authorizes it.
7. Save a Markdown report in `docs/checkpoints/reports/`.
8. Include exact commands run, files created, files modified, tests run, test results, risks, and blockers.
9. End every report with an `Awaiting PM Approval` section.

---

## Git Policy

Checkpoint instruction files and checkpoint reports should generally be committed to the repo because they are part of the project audit trail.

Never commit:

```text
.env
.env.*
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
```

The safe template `.env.example` may be committed.

---

## Recommended Checkpoint Sequence

### CP00 — Environment Inspection

Status: already completed in chat.

Purpose:

- Confirm working directory
- Confirm Python version
- Confirm PowerShell version
- Confirm Git status
- Confirm source files exist
- Confirm prompt block count
- Identify Windows/Windsurf issues

### CP01 — Implementation Plan

Purpose:

- No file modifications except possibly creating the report
- Plan repo structure
- Plan Git initialization
- Plan Windows-safe install
- Plan credential handling
- Plan smoke tests
- Plan scheduled task setup

### CP02 — Project Scaffold

Purpose:

- Initialize Git
- Add remote
- Create folder structure
- Add `.gitignore`
- Add `.env.example`
- Preserve source files
- Create initial project documentation
- No real credentials

### CP03 — Agent Port

Purpose:

- Extract/adapt the 17 original prompt file blocks
- Convert paths to repo-relative Windows-safe paths
- Make PowerShell 5.1-safe script changes
- Preserve Mac/Linux scripts but mark Windows-first flow

### CP04 — Windows Install

Purpose:

- Create virtual environment
- Install dependencies
- Create local `.env` from `.env.example` without real key values committed
- Confirm import-level readiness

### CP05 — Smoke Tests

Purpose:

- Run safe, non-scheduled tests
- Validate Python scripts start correctly
- Validate config loading
- Validate no secrets are printed
- Validate logs/output paths

### CP06 — Scheduler Setup

Purpose:

- Configure Windows Task Scheduler only after smoke tests pass
- Verify tasks exist
- Confirm scheduled jobs write logs safely

### CP07 — Final Review, Commit, Push

Purpose:

- Run final checks
- Confirm `.env` and private files are ignored
- Commit approved changes
- Push to `origin/main`
- Report commit hash and test summary

---

# CP01 Instruction File

Save the following as:

```text
docs/checkpoints/instructions/CP01_implementation_plan_instruction.md
```

---

## CP01 — Implementation Plan Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

### Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

### Source files expected

```text
docs/source/original_prompt.md
docs/source/Insider_Trading_Windows_Windsurf_Claude_Code_Handoff_Prompt.md
docs/source/video_transcript.txt
```

### Goal of this checkpoint

Produce an implementation plan only.

Do not implement the project yet.

### Allowed actions

You may:

1. Read files.
2. Inspect the repo and environment.
3. Run read-only diagnostic commands.
4. Create the checkpoint report file:

```text
docs/checkpoints/reports/CP01_implementation_plan_report.md
```

If the `docs/checkpoints/reports/` directory does not exist yet, you may create only the minimum required folders to save the report.

### Prohibited actions

Do not:

1. Initialize Git yet.
2. Add the GitHub remote yet.
3. Install dependencies.
4. Create or modify application source files.
5. Create `.env`.
6. Request or print real API keys.
7. Create scheduled tasks.
8. Commit files.
9. Push to GitHub.
10. Delete, overwrite, or rename source files.

### CP01 report requirements

Write a Markdown report to:

```text
docs/checkpoints/reports/CP01_implementation_plan_report.md
```

The report must include:

1. Environment summary
2. Confirmed current source files
3. Proposed final project structure
4. Git initialization plan
5. GitHub remote plan
6. Windows PowerShell 5.1-safe install plan
7. Python 3.11.9 virtual environment plan using `py`
8. Dependency plan
9. Credential-protection plan
10. `.gitignore` plan
11. `.env` and `.env.example` plan
12. Plan for adapting the 17 original prompt file blocks
13. Plan for preserving Mac/Linux files while keeping Windows-first execution
14. Proposed smoke-test plan before Task Scheduler setup
15. Proposed Task Scheduler plan
16. Proposed checkpoint sequence after CP01
17. Risks, blockers, and assumptions
18. Exact commands proposed for CP02, but do not run them yet
19. Awaiting PM Approval section

### Credential and repository safety requirements

The plan must ensure that the following are never committed:

```text
.env
.env.*
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
```

The plan may commit:

```text
.env.example
config/portfolio_target.example.json
config/portfolio_current.example.json
docs/checkpoints/
docs/source/
```

### End condition

After saving the report, respond only with:

1. The report path.
2. A short summary.
3. A statement that you are awaiting PM approval before implementation.
