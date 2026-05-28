# Insider Trading -- Public Signal Alerting System

> **This project analyzes public information and sends informational alerts only. It does not place trades, recommend that any user trade, or use non-public information. The user is responsible for all investment decisions.**

## Purpose

A Windows 11 implementation of the "Insider Routines" project described in Lewis Jackson's video "So My AI Agent Does Insider Trading Now." Seven AI agents read public US-government signals (SEC Form 4, 13F filings, Fed speeches, on-chain whale moves, plus portfolio drift) and deliver a Gmail alert when at least three of them agree.

This is an informational research and alerting prototype. It surfaces public signals for human review. It never places trades.

## Target Environment

- Windows 11
- Windsurf IDE + Claude Code
- PowerShell 5.1
- Python 3.11.9

## The Seven Agents

### Scouts (5)

| Agent | Reads | Schedule |
|-------|-------|----------|
| **Eddie** | SEC Form 4 insider buys >= $100k | Daily 06:00 |
| **Maggie** | 13F filings from major institutional funds | Weekly Sun 19:00 |
| **Frank** | Federal Reserve speeches + FOMC commentary | Weekly Mon 08:00 |
| **Maya** | On-chain whale moves (BTC/ETH/stablecoins) >= $5M | Daily 12:00 |
| **Janet** | Portfolio drift vs target allocation | Daily 17:00 |

### Consensus (1)

**Sophie** -- reads the rolling signal window. Fires a consensus event when enough scouts agree on the same direction + ticker. Runs daily at 18:00.

### Dispatcher (1)

**Ross** -- when Sophie fires, Ross sends a Gmail alert (always) + a Telegram message (if configured). Never places trades. Runs daily at 18:30.

## Current Limitations

**Scout agents are prompt-based prototypes.** Eddie, Maggie, Frank, and Maya send prompts to Claude asking it to research public sources, but the current implementation does not attach web search tools to the Anthropic SDK calls. Responses reflect Claude's training knowledge, not verified real-time data. Live data grounding requires a future enhancement phase.

Janet works from local portfolio JSON files and does not require web access. Sophie and Ross are pure local logic (SQLite + Gmail SMTP).

## Status

**Current checkpoint: CP07 (Final Review / Commit / Push) -- complete.**

Initial commit pushed to `origin/main`. All 7 agents registered in Windows Task Scheduler under `\InsiderRoutines\` with conservative daily schedules. All quality gates pass: compile, import, smoke test, secret scan, ignore checks. Dry-run mode remains active.

## Project Structure

```text
Insider-Trading/
  README.md                 This file
  requirements.txt          Python dependencies
  .gitignore                Security exclusions
  .env.example              Credential template (never commit .env)
  agents/
    common.py               Shared foundation (client, state store, delivery)
    eddie.py                SEC Form 4 scout
    maggie.py               13F filings scout
    frank.py                Fed speeches scout
    maya.py                 On-chain whale scout
    janet.py                Portfolio drift scout
    sophie.py               Consensus engine
    ross.py                 Dispatcher (dry-run by default)
  config/                   Portfolio example files
  install/
    schedule_windows.ps1    Register Windows Task Scheduler tasks
    uninstall_windows.ps1   Remove all Insider scheduled tasks
    cross_platform/         Mac/Linux scripts (preserved, not used)
  scripts/
    run_agent.ps1           Run a named agent manually
    smoke_test_windows.ps1  Pre-flight checks (no API needed)
    init_project_windows.ps1  First-time setup helper
  docs/
    source/                 Original prompt, transcript, handoff prompt
    checkpoints/            Checkpoint audit trail
    install_notes_windows.md  Windows-specific notes
  .state/                   Runtime state (gitignored except .gitkeep)
```

## Environment Variables

This project uses `SOPHIE_*` environment variable names (e.g., `SOPHIE_MIN_AGREE`, `SOPHIE_WINDOW_DAYS`), matching the actual code in `sophie.py`. The original source prompt uses `DELPHI_*` in some comments -- this naming mismatch is documented in `docs/install_notes_windows.md`.

Model IDs are preserved from the original source prompt and may need verification before real operation. See `docs/install_notes_windows.md` for details.

## Credential Safety

- **Never commit `.env`** or any file containing real API keys, passwords, or tokens.
- **Never commit `config/portfolio_target.json`** or `config/portfolio_current.json` (these contain private holdings).
- Only `.example` files with placeholder values are committed.
- See `.gitignore` for the full exclusion list.

## Checkpoint Workflow

This project follows a phased implementation with PM-approved checkpoints. See:

```text
docs/checkpoints/CHECKPOINT_PROTOCOL.md
```

## Legal

This project is for informational and educational purposes only. It does not constitute financial advice, trading recommendations, or an invitation to trade securities. The user bears sole responsibility for all investment decisions. No guarantee of accuracy, timeliness, or completeness of any signal or alert is made or implied.
