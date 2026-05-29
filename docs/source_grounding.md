# Source Grounding Architecture

> Implemented in CP09. This document explains how scout agents fetch deterministic live data from public sources.

## Overview

Before CP09, scout agents (Eddie, Maggie, Frank, Maya) sent prompts to Claude asking it to research public sources. Claude responded based on training knowledge, not live data. CP09 adds deterministic source connectors that fetch real data before each Claude call.

## Architecture

```text
Agent (e.g. eddie.py)
  |
  +-- Connector.fetch() --> SourceFetchResult (ok/fail + evidence list)
  |     |
  |     +-- HTTP request to public API/site
  |     +-- Parse response into SourceEvidence objects
  |     +-- Return structured result
  |
  +-- EvidenceBundle --> save_evidence() --> .state/evidence/{timestamp}_{agent}_{uuid}.json
  |
  +-- Connector.format_for_prompt(result) --> plain-text summary
  |
  +-- Claude API call with injected source data
  |
  +-- Signal stored in SQLite (.state/state.db)
```

## Connectors by Agent

### Eddie -- SEC Form 4

- **Connector**: `SecForm4Connector` (`sources/sec_form4.py`)
- **Source**: SEC EDGAR Full-Text Search (EFTS) at `efts.sec.gov`
- **Query**: Form 4 filings from the last 24 hours
- **Output**: Filing accession numbers, entity names, filing dates
- **Requirements**: `SEC_USER_AGENT` env var (SEC fair-access policy)

### Maggie -- 13F-HR Filings

- **Connector**: `Sec13FConnector` (`sources/sec_13f.py`)
- **Source**: SEC EDGAR submissions API at `data.sec.gov`
- **Query**: Most recent 13F-HR filing for each tracked manager
- **Default managers**: Berkshire Hathaway, Bridgewater, Renaissance, Citadel, Two Sigma
- **Output**: Accession numbers, filing dates, report periods
- **Requirements**: `SEC_USER_AGENT` env var

### Frank -- Federal Reserve Speeches

- **Connector**: `FedSpeechesConnector` (`sources/fed_speeches.py`)
- **Source**: Federal Reserve website at `federalreserve.gov/newsevents/speeches.htm`
- **Query**: Speeches from the last 7 days (configurable via `lookback_days`)
- **Output**: Speaker name, speech date, title, text excerpt, hawkish/dovish tone score
- **Tone analysis**: Simple keyword heuristic counting hawkish terms (inflation, restrictive, tighten) vs dovish terms (patient, accommodative, easing)
- **Requirements**: None (public HTML)

### Maya -- On-Chain Whale Moves

- **Connector**: `EtherscanConnector` (`sources/etherscan.py`)
- **Source**: Etherscan API for ERC-20 token transfers
- **Tokens tracked**: WBTC, WETH, USDC, USDT (configurable)
- **Logic**: Classifies transfers as accumulation (CEX -> private) or distribution (private -> CEX) based on 15+ known exchange addresses
- **Requirements**: `ETHERSCAN_API_KEY` env var (degrades gracefully without it)

## Evidence Schema

All connectors return `SourceFetchResult` objects containing:

- `ok`: Whether the fetch succeeded
- `source_name`: Identifier for the data source
- `evidence`: List of `SourceEvidence` objects
- `error_type` / `error_message`: On failure, categorized error info

Each `SourceEvidence` contains:

- `source_type`: Category (e.g., "sec_form4", "etherscan")
- `source_url`: URL of the source data
- `retrieved_at`: ISO-8601 UTC timestamp
- `canonical_id`: Unique identifier (e.g., accession number, tx hash)
- `normalized`: Connector-specific structured data (dict)

## Evidence Storage

Evidence is persisted as JSON files under `.state/evidence/`:

```text
.state/evidence/20260128T060000Z_eddie_a1b2c3d4.json
.state/evidence/20260202T190000Z_maggie_e5f6g7h8.json
```

Files are named `{timestamp}_{agent}_{uuid}.json`. The `.state/` directory is gitignored.

## SEC Compliance

- **User-Agent**: All SEC requests include a `User-Agent` header read from `SEC_USER_AGENT` env var. Format: `CompanyName admin@example.com` per SEC fair-access policy.
- **Rate limiting**: 200ms minimum between SEC EDGAR requests (module-level lock).
- **Caching**: Responses cached under `.state/cache/` with configurable TTL (default 300s for SEC). Cache key is a SHA-256 hash of the URL.
- **Error handling**: 403 (blocked) and 429 (rate limited) responses return `SourceFetchResult.failure()` with categorized errors. No retries to avoid further rate limit hits.

## Credential and Account Policy

- **Etherscan API calls** use only `ETHERSCAN_API_KEY`. The code does not need or use Etherscan website username or password.
- **SEC EDGAR official connectors** use only `SEC_USER_AGENT` for fair-access identification. No SEC.gov login is required.
- **sec-api.io** keys (`SEC_API_IO_API_KEY`) are documented as optional/future-use. No current connector uses them.
- **Do not store website passwords** in `.env`, `.env.example`, or anywhere in the repository. Manage website login credentials in a password manager.
- **Account-reference fields** (`ETHERSCAN_ACCOUNT_EMAIL`, `ETHERSCAN_USERNAME`, `SEC_API_IO_ACCOUNT_EMAIL`, `SEC_API_IO_USERNAME`) are optional local notes so you can remember which account is associated. They are not read by any connector code.
- **Maya is on-chain oriented**, monitoring ERC-20 token transfers (WBTC, WETH, USDC, USDT) and classifying whale wallet flows. She does not research stock tickers. If company-to-token mapping is needed, that requires a separate design.
- **Ross remains dry-run** until explicitly changed in a future checkpoint.

## Remaining Limitations

1. SEC EFTS may return empty results during low-filing periods (weekends, holidays).
2. Fed speech HTML parsing depends on the current website structure. Layout changes may break extraction.
3. Etherscan free-tier API has rate limits (5 calls/sec). The connector uses 250ms spacing.
4. Token price estimation uses a simple lookup dict, not live price feeds.
5. On-chain analysis is limited to Ethereum mainnet ERC-20 transfers.
6. All signals remain informational. This system does not place trades or provide trading advice.
7. Ross remains in dry-run mode unless `ROSS_DRY_RUN` is explicitly set to `false`.
