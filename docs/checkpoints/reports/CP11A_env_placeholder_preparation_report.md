# CP11A -- Etherscan / SEC `.env` Placeholder Preparation Report

**Checkpoint:** CP11A
**Date:** 2026-05-29
**Executor:** Claude Code (claude-opus-4-6)
**Instruction file:** `docs/checkpoints/instructions/CP11A_env_placeholder_preparation_instruction.md`

## 1. Summary of work completed

Added SEC EDGAR and Etherscan placeholder keys to `.env.example` and the local `.env` file. No existing values were overwritten. No password placeholders were added. No agents were run. No commits or pushes were performed. The environment is now ready for Roger to manually fill in `SEC_USER_AGENT` and `ETHERSCAN_API_KEY` before CP11 runtime testing.

## 2. Files created

```text
docs/checkpoints/reports/CP11A_env_placeholder_preparation_report.md   (this file)
```

## 3. Files modified

```text
.env.example   Added SEC_USER_AGENT, SEC_API_IO_*, ETHERSCAN_* placeholder sections
.env           Added 7 missing placeholder keys (SEC_USER_AGENT, SEC_API_IO_*, ETHERSCAN_*)
```

## 4. Confirmation: `.env.example` was updated

Updated. The following sections and keys were added:

```text
# SEC EDGAR
SEC_USER_AGENT=
SEC_API_IO_ACCOUNT_EMAIL=
SEC_API_IO_USERNAME=
SEC_API_IO_API_KEY=

# Etherscan
ETHERSCAN_ACCOUNT_EMAIL=
ETHERSCAN_USERNAME=
ETHERSCAN_API_KEY=
```

All keys have empty values (no secrets). Comments explain each key's purpose. The existing sections (Anthropic, Gmail, Telegram, Tuning, Advanced) were preserved.

## 5. Confirmation: local `.env` was updated without printing contents

Confirmed. A PowerShell script added 7 missing keys to `.env` with empty values. The script output showed key names and set/empty status only -- no values were printed.

## 6. Confirmation: existing `.env` values were not overwritten

Confirmed. The following pre-existing keys retained their original values:

- `ANTHROPIC_API_KEY` -- SET (length 108)
- `ROSS_DRY_RUN` -- SET (length 4, confirmed `true`)
- `SOPHIE_MIN_AGREE` -- SET
- `SOPHIE_WINDOW_DAYS` -- SET
- `JANET_MIN_DELTA_PCT` -- SET
- `JANET_MIN_POSITION` -- SET

All other pre-existing keys (GMAIL_*, TELEGRAM_*) were also preserved.

## 7. Confirmation: no password placeholders were added

Confirmed. No keys containing `PASSWORD` were added. The instruction explicitly prohibits password placeholders (`ETHERSCAN_PASSWORD`, `SEC_API_IO_PASSWORD`, `PASSWORD`). None were created.

## 8. Confirmation: `.env` remains ignored

```
.gitignore:2:.env    .env
```

`.env` does not appear in `git status --short`. Confirmed gitignored.

## 9. Exact list of environment variable names Roger must fill in

### Required (must fill before CP11 runtime testing)

| Key | Purpose |
| --- | --- |
| `ETHERSCAN_API_KEY` | API key for Maya's on-chain token transfer monitoring. Get a free key at https://etherscan.io/apis |
| `SEC_USER_AGENT` | SEC EDGAR fair-access identification header. Required for Eddie and Maggie's SEC data fetching |

### Optional (local account reference fields, not used by code)

| Key | Purpose |
| --- | --- |
| `ETHERSCAN_ACCOUNT_EMAIL` | Local reference: Etherscan account email |
| `ETHERSCAN_USERNAME` | Local reference: Etherscan username |
| `SEC_API_IO_ACCOUNT_EMAIL` | Local reference: sec-api.io account email |
| `SEC_API_IO_USERNAME` | Local reference: sec-api.io username |
| `SEC_API_IO_API_KEY` | Future integration: sec-api.io API key (not currently used by connectors) |

## 10. Explanation: what `SEC_USER_AGENT` should contain

SEC EDGAR requires a descriptive `User-Agent` header for fair-access compliance. The value should identify the application and provide contact information. Recommended format:

```text
Insider-Trading Roger Fiske your-real-email@example.com
```

Replace `your-real-email@example.com` with a real contact email address. This is sent as an HTTP header to SEC servers, not published anywhere.

## 11. Explanation: Maya does not require a stock ticker

Maya monitors on-chain ERC-20 token transfers (WBTC, WETH, USDC, USDT) on Ethereum mainnet. She classifies large transfers between known CEX addresses and private wallets as accumulation or distribution signals. Maya does not track stock tickers -- she is an on-chain whale-watcher, not a stock market scanner.

## 12. Maya configuration gap discovered

No configuration gap. Maya's `EtherscanConnector` reads only `ETHERSCAN_API_KEY` from the environment. The token list (WBTC, WETH, USDC, USDT), minimum USD threshold ($5M), and CEX address database are all hardcoded defaults in `sources/onchain_base.py` and `sources/etherscan.py`. No additional configuration is needed beyond the API key.

## 13. Confirmation: no agent was run

Confirmed. No agents were executed during CP11A.

## 14. Confirmation: no scheduled tasks were changed

Confirmed. All 7 `\InsiderRoutines\Insider-*` tasks remain in their original Ready state.

## 15. Confirmation: no commit or push was performed

Confirmed. `git status --short` shows uncommitted changes only:

```
 M .env.example
?? docs/checkpoints/instructions/CP11A_env_placeholder_preparation_instruction.md
?? docs/checkpoints/reports/CP10_grounded_runtime_validation_commit_push_report.zip
```

No commits or pushes were made.

## 16. Awaiting PM Approval

CP11A placeholder preparation is complete. Awaiting:

1. Roger to manually fill in `ETHERSCAN_API_KEY` and `SEC_USER_AGENT` in `.env`.
2. PM approval before proceeding to CP11 runtime testing.
