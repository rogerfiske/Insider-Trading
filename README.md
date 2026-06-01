# Insider Trading -- Public Signal Alerting System

> **This project analyzes public information and sends informational alerts only. It does not place trades, recommend that any user trade, or use non-public information. The user is responsible for all investment decisions.**

## Purpose

A Windows 11 implementation of the "Insider Routines" project described in Lewis Jackson's video "So My AI Agent Does Insider Trading Now." Seven AI agents read public US-government signals (SEC Form 4, 13F filings, Fed speeches, on-chain whale moves, plus portfolio drift) and deliver an email alert (via generic SMTP) when at least three of them agree.

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

**Ross** -- when Sophie fires, Ross applies alert routing policy (severity classification, deduplication, channel routing) and sends alerts via email/Telegram based on policy and channel enablement. Never places trades. Runs daily at 18:30.

Alert routing features:

- **Severity levels**: INFO, WATCH, ACTIONABLE, URGENT (based on scout count and aggregate confidence)
- **Alert classes**: LOG_ONLY, TELEGRAM_ONLY, EMAIL_ONLY, TELEGRAM_AND_EMAIL, SUPPRESS_DUPLICATE
- **Deduplication**: Time-bucketed keys suppress duplicate alerts within configurable window (default 24h)
- **Independent channels**: Telegram and email can be enabled/disabled independently
- **Rate limiting**: Maximum alerts per run (default 3)
- **Audit trail**: All routing decisions recorded in alert_history table

## Source Grounding

Four scout agents now fetch live data from deterministic public sources before sending prompts to Claude. Each agent uses a dedicated connector that returns structured evidence:

| Agent | Connector | Source | Classification |
| --- | --- | --- | --- |
| **Eddie** | `SecForm4Connector` | SEC EDGAR EFTS (Form 4 filings) | A -- deterministic, grounded |
| **Maggie** | `Sec13FConnector` | SEC EDGAR data.sec.gov (13F-HR submissions) | A -- deterministic, grounded |
| **Frank** | `FedSpeechesConnector` | federalreserve.gov (speeches listing + text) | A -- deterministic, grounded |
| **Maya** | `EtherscanConnector` | Etherscan API (ERC-20 token transfers) | A -- deterministic, grounded (requires API key) |
| **Janet** | N/A | Local portfolio JSON files | B -- local deterministic |
| **Sophie** | N/A | Local SQLite signal window | B -- local deterministic |
| **Ross** | N/A | Local consensus events | B -- local deterministic |

All fetched evidence is stored as JSON files under `.state/evidence/` for auditability. See `docs/source_grounding.md` for details.

### SEC Compliance

All SEC EDGAR requests include a valid `User-Agent` header (set via `SEC_USER_AGENT` env var) and a 200ms rate limiter. Responses are cached under `.state/cache/` to reduce repeated hits. The system handles 403/429 errors gracefully.

### Current Limitations

- Maya requires an `ETHERSCAN_API_KEY` in `.env`. Without it, she degrades gracefully to a failure result.
- Fed speech HTML parsing may break if the Federal Reserve website changes its layout.
- SEC EFTS search may return empty results during low-filing periods.
- All signals remain informational and are not trading advice.
- Ross remains in dry-run mode unless explicitly changed.

## Status

**Current checkpoint: CP19 (Manual Production Telegram Pilot) -- Complete.**

All 4 external-facing scout agents (Eddie, Maggie, Frank, Maya) now fetch deterministic live data via source connectors before prompting Claude. Telegram alert delivery validated end-to-end (CP12B). Generic SMTP email delivery supports any SMTP provider (Gmail, 4SecureMail, etc.) via provider-neutral configuration (CP13B). Alert routing policy implemented with severity classification, deduplication, and channel routing (CP15). Controlled Telegram-only test validated routing layer (CP16). Controlled dual-channel test validated full TELEGRAM_AND_EMAIL routing (CP17). Production enablement plan designed with staged rollout (CP18). Manual production Telegram-only pilot executed safely with 0 messages sent (no eligible ACTIONABLE+ alert existed) -- production safety controls validated (CP19). Both channels fully validated. Production live alerts ready for scheduled enablement - awaiting PM approval for CP20 scheduled Telegram pilot.

## Project Structure

```text
Insider-Trading/
  README.md                 This file
  requirements.txt          Python dependencies
  .gitignore                Security exclusions
  .env.example              Credential template (never commit .env)
  agents/
    common.py               Shared foundation (client, state store, delivery)
    eddie.py                SEC Form 4 scout (grounded)
    maggie.py               13F filings scout (grounded)
    frank.py                Fed speeches scout (grounded)
    maya.py                 On-chain whale scout (grounded)
    janet.py                Portfolio drift scout
    sophie.py               Consensus engine
    ross.py                 Dispatcher with alert routing policy (dry-run by default)
  alerts/
    __init__.py             Alert subsystem exports
    smtp_email.py           Generic SMTP email delivery
    routing.py              Severity classification and alert routing
    history.py              Deduplication and audit storage
  evidence/
    schema.py               SourceEvidence, SourceFetchResult, EvidenceBundle
    store.py                File-backed JSON evidence persistence
  sources/
    base.py                 Abstract BaseConnector interface
    sec_common.py           SEC EDGAR shared utilities (rate limit, cache)
    sec_form4.py            Form 4 connector (Eddie)
    sec_13f.py              13F-HR connector (Maggie)
    fed_speeches.py         Fed speeches connector (Frank)
    onchain_base.py         On-chain utilities (CEX addresses, token math)
    etherscan.py            Etherscan ERC-20 connector (Maya)
  tests/                    Unit tests (pytest, 64 tests)
  config/                   Portfolio example files
  install/
    schedule_windows.ps1    Register Windows Task Scheduler tasks
    uninstall_windows.ps1   Remove all Insider scheduled tasks
    cross_platform/         Mac/Linux scripts (preserved, not used)
  scripts/
    run_agent.ps1           Run a named agent manually
    smoke_test_windows.ps1  Pre-flight checks (no API needed)
    init_project_windows.ps1  First-time setup helper
    smtp_test.py            SMTP config check and test email sender
    telegram_setup_check.py Telegram chat ID retrieval helper
  docs/
    source/                 Original prompt, transcript, handoff prompt
    source_grounding.md     Source connector architecture details
    checkpoints/            Checkpoint audit trail
    install_notes_windows.md  Windows-specific notes
  .state/                   Runtime state (gitignored except .gitkeep)
    evidence/               JSON evidence files (auto-created)
    cache/                  SEC response cache (auto-created)
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
