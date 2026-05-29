# Windows Installation Notes

Planning notes for the Windows-first implementation of Insider Routines.

## Environment

- **PowerShell version:** 5.1 (Windows PowerShell, not PowerShell Core)
  - All scripts must avoid PS 7+ syntax such as null-conditional (`?.`) operators.
  - Use `Get-Command ... -ErrorAction SilentlyContinue` and explicit `if` checks instead.
- **Python:** 3.11.9 via `py` launcher (`C:\Windows\py.exe`)
- **Git:** Available at `C:\Program Files\Git\cmd\git.exe`

## Virtual Environment

The `.venv` virtual environment was created in CP04:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Installed packages (CP04): anthropic 0.104.1, python-dotenv 1.2.2, pip 26.1.1, plus transitive dependencies (pydantic, httpx, anyio, etc.).

## Task Scheduler

Windows Task Scheduler tasks registered in CP06 under `\InsiderRoutines\`:

| Task Name | Schedule | Notes |
| --------- | -------- | ----- |
| Insider-eddie | Daily 06:00 | SEC Form 4 scout |
| Insider-maggie | Weekly Sunday 19:00 | 13F filings scout |
| Insider-frank | Weekly Monday 08:00 | Fed speeches scout |
| Insider-maya | Daily 12:00 | On-chain whale scout (reduced from every 6h) |
| Insider-janet | Daily 17:00 | Portfolio drift scout |
| Insider-sophie | Daily 18:00 | Consensus engine (reduced from every 30min) |
| Insider-ross | Daily 18:30 | Dispatcher (reduced from every 30min) |

All tasks use the venv Python executable (`.venv\Scripts\python.exe`) and the repo root as working directory. Sophie was manually triggered via Task Scheduler in CP06 and confirmed working (exit code 0).

To uninstall: `powershell -File install\uninstall_windows.ps1`

## Live Data Access (Updated CP09)

Scout agents (Eddie, Maggie, Frank, Maya) now fetch deterministic live data via source connectors before prompting Claude. Each connector fetches from a specific public API or website, returning structured `SourceFetchResult` objects. The fetched data is injected into the Claude prompt so the model analyzes real evidence rather than training knowledge.

| Agent | Connector | Source | Requires |
| --- | --- | --- | --- |
| Eddie | `SecForm4Connector` | SEC EDGAR EFTS | `SEC_USER_AGENT` env var |
| Maggie | `Sec13FConnector` | SEC data.sec.gov | `SEC_USER_AGENT` env var |
| Frank | `FedSpeechesConnector` | federalreserve.gov | Nothing (public HTML) |
| Maya | `EtherscanConnector` | Etherscan API | `ETHERSCAN_API_KEY` env var |

All evidence is persisted as JSON under `.state/evidence/` for auditability.

### SEC EDGAR Compliance

- All SEC requests include a `User-Agent` header read from `SEC_USER_AGENT` env var.
- A 200ms rate limiter prevents hitting SEC rate limits.
- Responses are cached under `.state/cache/` with configurable TTL.
- 403/429 errors are caught and returned as `SourceFetchResult.failure()`.

### Etherscan API

- Maya requires `ETHERSCAN_API_KEY` in `.env` for on-chain data.
- Without the key, Maya degrades gracefully (returns a clear config_error).
- A 250ms rate limiter prevents hitting Etherscan rate limits.

## Environment Variable Naming

The original downloaded prompt (`docs/source/original_prompt.md`) uses `DELPHI_MIN_AGREE` and `DELPHI_WINDOW_DAYS` in the `.env.example` comments. However, the actual code in `sophie.py` reads `SOPHIE_MIN_AGREE` and `SOPHIE_WINDOW_DAYS`.

This project uses `SOPHIE_*` names in `.env.example` and all scripts, matching the code. The naming mismatch in the original prompt is documented here for traceability.

Similarly, the original prompt refers to "Mercury" in some `.env.example` comments. The agent's actual name is Ross. This project uses Ross consistently.

## Model IDs

The original prompt references these Claude model IDs:

- `claude-sonnet-4-5-20250929` (default scout model)
- `claude-haiku-4-5-20250630` (fast model for Maya)
- `claude-opus-4-7-20251020` (deep model, unused in Phase 1)

These IDs are preserved as-is from the source prompt. Before real operation, verify that these model IDs are current and available in the Anthropic API. The Anthropic console lists available models at: https://console.anthropic.com/

## CP03 Agent Porting Notes

All 17 file blocks from `docs/source/original_prompt.md` have been extracted and adapted:

- **8 Python agent files** (`agents/common.py` + 7 agents) -- ported with repo-relative paths, dry-run safety, and prototype limitation notes.
- **2 Windows install scripts** (`install/schedule_windows.ps1`, `install/uninstall_windows.ps1`) -- rewritten for PS 5.1 compatibility with explicit `Get-Command` checks instead of `?.Source`.
- **4 Mac/Linux scripts** -- preserved verbatim under `install/cross_platform/`.
- **3 helper scripts** (`scripts/run_agent.ps1`, `scripts/smoke_test_windows.ps1`, `scripts/init_project_windows.ps1`) -- new, PS 5.1 compatible.

### Key Adaptations

1. **Repo-relative paths**: All agents use `Path(__file__).resolve().parents[1]` instead of `Path.home() / "insider-routines"`.
2. **Dry-run default**: Ross checks `ROSS_DRY_RUN` env var (defaults to `true`). `send_email()` and `send_telegram()` in `common.py` respect dry-run mode.
3. **No live web access**: Scout prompts are sent to Claude without web search tools attached. Outputs reflect training knowledge only.
4. **PS 5.1 safety**: All PowerShell scripts avoid null-conditional `?.` syntax and use `Get-Command ... -ErrorAction SilentlyContinue` with explicit `if` checks.
5. **`.claude/` ignored**: Added to `.gitignore` to prevent IDE/tooling config from being tracked.

### Deferred Items

- **Live source grounding**: Implemented in CP09 for Eddie, Maggie, Frank, Maya.
- **Dependency installation**: Completed in CP04. pytest added in CP09.
- **Task Scheduler registration**: CP06.
- **Real `.env` creation**: User must edit `.env` locally with real credentials.
- **Grounded runtime validation**: CP10 candidate (test connectors against live APIs).

## CP04 Environment Setup Notes

- Virtual environment created at `.venv/` using Python 3.11.9.
- pip upgraded to 26.1.1.
- All dependencies installed from `requirements.txt`.
- All 8 agent files pass `py_compile` and import successfully.
- Smoke test (`scripts/smoke_test_windows.ps1`) passes 31/31 checks.
- Placeholder `.env` created from `.env.example` (no real secrets).
- `.env` is confirmed gitignored.

## CP05 Runtime Smoke Test Notes

- `.gitignore` fixed: changed `reports/` to `/reports/` so `docs/checkpoints/reports/` is trackable while root `reports/` remains ignored.
- All 4 tested agents pass runtime smoke tests:
  - **Eddie**: API call succeeded, produced signal `LSAQ BULLISH conf=5`.
  - **Sophie**: Read signal window, correctly found no consensus (need >= 2 agreeing scouts).
  - **Ross**: Ran in dry-run mode, no emails/Telegram sent, correctly found nothing to dispatch.
  - **Janet**: Detected NVDA drift +6.5pp above target, produced signal `NVDA BEARISH conf=2`.
- State store (`.state/state.db`) holds 2 signals and 0 consensus events.
- Log files created for all 4 agents: `.state/logs/{eddie,sophie,ross,janet}.log`.
- Note: Initial run hit an API billing blocker (insufficient credits). After Roger added credits, all tests passed.

## CP06 Scheduler Setup Notes

- `install/schedule_windows.ps1` modified for conservative schedules: Maya reduced from every 6h to daily 12:00, Sophie from every 30min to daily 18:00, Ross from every 30min to daily 18:30.
- All 7 tasks registered under `\InsiderRoutines\` in Windows Task Scheduler, all in "Ready" state.
- Each task uses `.venv\Scripts\python.exe` as the executable, the agent script as the argument, and the repo root as the working directory.
- Sophie manually triggered via `Start-ScheduledTask`: completed with exit code 0, log entry confirmed at `.state/logs/sophie.log`.
- Uninstall script verified: `install/uninstall_windows.ps1` correctly targets all 7 `Insider-*` tasks.
- Dry-run mode remains active (`ROSS_DRY_RUN=true`). No real emails or Telegram messages were sent.

## CP09 Source Connector Implementation Notes

- Created `evidence/` package: `schema.py` (SourceEvidence, SourceFetchResult, EvidenceBundle dataclasses) and `store.py` (JSON file persistence under `.state/evidence/`).
- Created `sources/` package: `base.py` (abstract BaseConnector), `sec_common.py` (SEC rate limiter, cache, User-Agent), `sec_form4.py` (Eddie), `sec_13f.py` (Maggie), `fed_speeches.py` (Frank), `onchain_base.py` (CEX addresses, token math), `etherscan.py` (Maya).
- Updated 4 scout agents to import and use their connectors. Each agent fetches data, stores evidence, then injects formatted text into the Claude prompt.
- Added `pytest` to `requirements.txt`. 64 unit tests across 6 test files, all passing. No live network access required.
- All 17 source + evidence + agent files pass `py_compile`.
- Smoke test passes 31/31 checks.
- No scheduled tasks were changed or triggered.
- No secrets were printed, no emails sent, no Telegram messages sent.

## CP11 Etherscan / Maya Runtime Notes

- `ETHERSCAN_API_KEY` configured and validated. Maya now fetches live on-chain data from Etherscan.
- `SEC_USER_AGENT` configured with real contact information for SEC fair-access compliance.
- `.env.example` updated with SEC and Etherscan placeholder sections. No real values in `.env.example`.
- Maya monitors ERC-20 token transfers (WBTC, WETH, USDC, USDT) on Ethereum mainnet. She is on-chain oriented, not stock-ticker oriented.
- Website passwords must not be stored in `.env`. Only API keys and user-agent strings are used by the code.
- `ETHERSCAN_ACCOUNT_EMAIL`, `ETHERSCAN_USERNAME`, `SEC_API_IO_*` fields are optional local account-reference notes only.
- Ross remains in dry-run mode (`ROSS_DRY_RUN=true`).

## CP12A Telegram Alert Preparation Notes

- `.env.example` already contains empty Telegram placeholders: `TELEGRAM_BOT_TOKEN=` and `TELEGRAM_CHAT_ID=`.
- Local `.env` has these keys present (currently blank).
- Ross remains in dry-run mode. No Telegram messages are sent until CP12B.
- Telegram setup requires creating a bot via `@BotFather` in Telegram and obtaining:
  1. Bot token from `/newbot` command.
  2. Chat ID from the Telegram API after sending a test message to the bot.
- Do not store your personal Telegram login password in `.env` -- only the bot token and chat ID are used.
- No Telegram password placeholders (`TELEGRAM_PASSWORD`, `TELEGRAM_2FA_PASSWORD`) are added to the repo.
