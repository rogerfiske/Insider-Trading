# CP08 -- Live Source Grounding Plan Report

**Checkpoint:** CP08 -- Live Source Grounding Plan
**Date:** 2026-05-28
**Executor:** Claude Code (claude-opus-4-6)
**Instruction file:** `docs/checkpoints/instructions/CP08_live_source_grounding_plan_instruction.md`

---

## 1. Summary

CP08 extracts the intended source references from the original prompt (`docs/source/original_prompt.md`), compares them to the current agent implementations, classifies each agent's grounding status, and proposes a deterministic connector architecture for CP09 implementation.

**Key finding:** Four of seven agents (Eddie, Maggie, Frank, Maya) are currently prompt-only prototypes -- they ask Claude to "search" or "query" public data sources, but the Anthropic SDK call in `common.run_scout()` does not attach web search tools. Responses reflect Claude's training knowledge, not verified real-time data. Two agents (Sophie, Ross) are fully deterministic local logic. One agent (Janet) is deterministic local logic but depends on user-supplied config files.

This report proposes a `sources/` module layer with deterministic HTTP connectors for SEC EDGAR, Federal Reserve speeches, and on-chain explorers, plus an `evidence/` schema for auditable provenance. No code was implemented in CP08.

---

## 2. Files Inspected

| # | File | Purpose |
| - | ---- | ------- |
| 1 | `docs/source/original_prompt.md` | Original one-shot prompt with source references |
| 2 | `docs/source/video_transcript.txt` | Lewis Jackson video transcript |
| 3 | `docs/checkpoints/CHECKPOINT_PROTOCOL.md` | Checkpoint workflow rules |
| 4 | `docs/checkpoints/reports/CP07_final_review_commit_push_report.md` | Prior checkpoint report |
| 5 | `agents/common.py` | Shared foundation (run_scout, state store, delivery) |
| 6 | `agents/eddie.py` | SEC Form 4 scout |
| 7 | `agents/maggie.py` | 13F institutional holdings scout |
| 8 | `agents/frank.py` | Fed speeches scout |
| 9 | `agents/maya.py` | On-chain whale watcher scout |
| 10 | `agents/janet.py` | Portfolio drift accountant |
| 11 | `agents/sophie.py` | Consensus engine |
| 12 | `agents/ross.py` | Alert dispatcher |
| 13 | `requirements.txt` | Current dependencies (anthropic, python-dotenv) |
| 14 | `.env.example` | Environment variable template |

---

## 3. Extracted Original Prompt Source Map by Agent

### 3.1 Eddie -- SEC Form 4

**Intended source category:** SEC EDGAR Form 4 insider-trading filings.

**Specific sources referenced in original prompt:**
- URL pattern: `https://efts.sec.gov/LATEST/search-index?forms=4&dateRange=custom`
- Domain: `efts.sec.gov` (EDGAR full-text search system)
- Filing type: Form 4
- Filter criteria: transaction code = P (open-market purchase), total value >= $100,000, filer role = CEO / CFO / President / Chairman / Director

**Specific data fields referenced:**
- Issuer ticker and name
- Filer name and role
- Transaction code
- Share count
- Price per share
- Total value
- Filing date

**Evidence fields for auditability:**
- Accession number
- CIK
- Issuer name/ticker
- Insider name and title
- Transaction date
- Filing date
- Security title
- Transaction code
- Shares traded
- Price per share
- Ownership nature (direct/indirect)
- Source URL (EDGAR filing page)
- Raw filing XML URL

### 3.2 Maggie -- 13F Institutional Holdings

**Intended source category:** SEC EDGAR 13F-HR institutional holdings filings.

**Specific sources referenced in original prompt:**
- URL pattern: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={CIK}&type=13F-HR`
- Domain: `sec.gov/cgi-bin/browse-edgar` (EDGAR company search)
- Filing type: 13F-HR

**Specific funds/entities and CIKs:**

| Fund | CIK |
| ---- | --- |
| Berkshire Hathaway | 0001067983 |
| Bridgewater Associates | 0001350694 |
| Renaissance Technologies | 0001037389 |
| Citadel Advisors | 0001423053 |
| Two Sigma Investments | 0001179392 |

**Filter criteria:** position changes >= $50M, classified as NEW POSITION / INCREASED (>=25%) / EXITED.

**Evidence fields for auditability:**
- Manager CIK
- 13F accession number
- Report period (quarter end date)
- Issuer name/ticker
- CUSIP
- Shares held (current quarter)
- Value (current quarter)
- Shares held (prior quarter) for comparison
- Change classification (NEW / INCREASED / EXITED)
- Source URL (filing index page)

### 3.3 Frank -- Federal Reserve Speeches

**Intended source category:** Federal Reserve speeches, FOMC commentary, monetary policy communications.

**Specific sources referenced in original prompt:**
- URL: `https://www.federalreserve.gov/newsevents/speeches.htm`
- Domain: `federalreserve.gov`
- Time window: last 7 days

**Specific data fields referenced:**
- Speaker name
- One-line stance summary
- Classification: hawkish / dovish / neutral
- Supporting quote (<=25 words)
- Net tilt aggregation

**Evidence fields for auditability:**
- Speech URL
- Speaker name
- Speech date
- Speech title
- Policy keywords
- Hawkish/dovish/neutral classification
- Supporting quoted excerpt
- Source URL

### 3.4 Maya -- On-Chain Whale Movements

**Intended source category:** On-chain whale transfer monitoring.

**Specific sources referenced in original prompt:**
- Explorers: Etherscan, blockchain.com, "or similar"
- Tokens: WBTC, WETH, USDC, USDT
- Threshold: transfers >= $5M
- Time window: last 6 hours

**Classification logic:**
- CEX -> private wallet = ACCUMULATION (BULLISH)
- Private wallet -> CEX = DISTRIBUTION (BEARISH)
- WBTC -> BTC ticker, WETH -> ETH ticker, stablecoins -> MACRO

**Evidence fields for auditability:**
- Chain (Ethereum / Bitcoin)
- Token symbol
- Transaction hash
- From address
- To address
- Amount (token units)
- USD estimate
- Timestamp
- Transfer direction (accumulation/distribution)
- Explorer URL

### 3.5 Janet -- Portfolio Drift

**Intended source category:** Local portfolio configuration JSON files.

**Specific sources referenced in original prompt:**
- `config/portfolio_target.json` -- target allocation `{ticker: target_pct}`
- `config/portfolio_current.json` -- current holdings `{ticker: current_value_usd}`
- Drift threshold: 5 percentage points

**Evidence fields for auditability:**
- Symbol
- Target weight (%)
- Current weight (%)
- Delta (percentage points)
- Threshold used
- Source file paths

### 3.6 Sophie -- Consensus Engine

**Intended source category:** Local SQLite state database (signals table).

**Specific sources referenced in original prompt:**
- Rolling 7-day window of scout signals from `state.db`
- Consensus fires when >= 3 scouts agree on same direction + ticker
- Runs after scouts (originally every 30 minutes, now daily 18:00)

**Evidence fields for auditability:**
- Signal IDs contributing to consensus
- Agent names
- Symbols (tickers)
- Directions
- Confidence scores
- Timestamps
- Agreement count
- Consensus rule applied (min_agree, window_days)

### 3.7 Ross -- Alert Dispatcher

**Intended source category:** Local consensus events and alert-dispatch configuration.

**Specific sources referenced in original prompt:**
- Reads pending consensus events from `state.db`
- Dispatches via Gmail SMTP (required) and Telegram (optional)
- Never places trades
- Dry-run gated via `ROSS_DRY_RUN` env var

**Evidence fields for auditability:**
- Consensus event ID
- Dispatch mode (email, telegram, dry-run)
- Dry-run flag value
- Recipient channel
- Timestamp
- Message preview or hash

---

## 4. Current Implementation Gap Analysis by Agent

### 4.1 Eddie (SEC Form 4)

**Current behavior:** `eddie.py` constructs a system prompt instructing Claude to "query the SEC EDGAR full-text search for Form 4 filings" and provides the URL pattern `efts.sec.gov/LATEST/search-index?forms=4&dateRange=custom`. It calls `common.run_scout()` which invokes `client.messages.create()` with NO web search tools attached ([common.py:271](agents/common.py#L271)). Claude responds from training knowledge.

**Gap:** No HTTP request to SEC EDGAR is made. No real filing data is fetched. No accession numbers or filing XML is parsed. The response is entirely based on Claude's parametric memory, which cannot reflect filings published in the last 24 hours.

### 4.2 Maggie (13F Institutional Holdings)

**Current behavior:** `maggie.py` lists 5 funds with CIKs and constructs a prompt asking Claude to "pull the latest 13F-HR filings from these funds." It provides the EDGAR browse URL pattern. Calls `run_scout()` with no web search tools.

**Gap:** No HTTP request to SEC EDGAR is made. No 13F filing data is fetched. No CUSIP or holdings comparison is performed. Claude cannot know the latest quarterly filings.

### 4.3 Frank (Fed Speeches)

**Current behavior:** `frank.py` prompts Claude to "pull speeches + testimony from federalreserve.gov/newsevents/speeches.htm published in the last 7 days." Calls `run_scout()` with no web search tools.

**Gap:** No HTTP request to federalreserve.gov is made. No speech text is fetched or parsed. Claude cannot know which speeches were published in the last 7 days.

### 4.4 Maya (On-Chain Whales)

**Current behavior:** `maya.py` prompts Claude to "query a free on-chain explorer (Etherscan, blockchain.com, or similar) for large transfers in the last 6 hours." Calls `run_scout()` with HAIKU_MODEL and no web search tools.

**Gap:** No HTTP request to any blockchain explorer is made. No transaction data is fetched. Claude (especially Haiku) has no knowledge of on-chain transactions from the last 6 hours.

### 4.5 Janet (Portfolio Drift)

**Current behavior:** `janet.py` reads `config/portfolio_target.json` and `config/portfolio_current.json` directly from disk. Performs drift calculation in pure Python. Does NOT call Claude.

**Gap:** Minimal. The logic is deterministic and correctly grounded in local files. The only gap is that `portfolio_current.json` must be manually maintained by the user -- there is no automated price feed or brokerage API connection. This is by design per the original prompt.

### 4.6 Sophie (Consensus Engine)

**Current behavior:** `sophie.py` reads the signals table from SQLite via `common.read_window()`. Groups by (ticker, direction), deduplicates per scout, applies consensus threshold (MIN_AGREE=3, WINDOW_DAYS=7). Pure local logic, no Claude call.

**Gap:** None. Sophie is fully deterministic and correctly grounded in the local state store.

### 4.7 Ross (Alert Dispatcher)

**Current behavior:** `ross.py` reads pending consensus events from SQLite via `common.pending_consensus()`. Sends email via `common.send_email()` and optional Telegram via `common.send_telegram()`. Gated by `is_dry_run()`. Pure local logic.

**Gap:** None. Ross is fully deterministic and correctly grounded in local state. Delivery channels (Gmail, Telegram) are properly implemented and gated.

---

## 5. Grounding Status Classification by Agent

| Agent | Classification | Explanation |
| ----- | -------------- | ----------- |
| **Eddie** | **C** -- prompt-only, not source-grounded | Asks Claude to search SEC EDGAR but no HTTP fetch occurs. Output is training-knowledge hallucination. |
| **Maggie** | **C** -- prompt-only, not source-grounded | Asks Claude to pull 13F filings but no HTTP fetch occurs. Output is training-knowledge hallucination. |
| **Frank** | **C** -- prompt-only, not source-grounded | Asks Claude to read Fed speeches but no HTTP fetch occurs. Output is training-knowledge hallucination. |
| **Maya** | **C** -- prompt-only, not source-grounded | Asks Claude to query on-chain explorers but no HTTP fetch occurs. Output is training-knowledge hallucination. |
| **Janet** | **B** -- local deterministic only | Reads local JSON files. Drift logic is correct and deterministic. No external data source needed (user maintains files manually). |
| **Sophie** | **A** -- deterministic and grounded now | Reads local SQLite. Consensus logic is correct and deterministic. |
| **Ross** | **A** -- deterministic and grounded now | Reads local SQLite. Delivery logic is correct and deterministic. |

**Summary:** 4 of 7 agents require source grounding (Eddie, Maggie, Frank, Maya). 3 are already grounded (Janet=B, Sophie=A, Ross=A).

---

## 6. Proposed CP09 Connector Architecture

### 6.1 Design Principles

1. **Deterministic fetch first.** Each connector makes real HTTP requests to authoritative sources and returns structured data.
2. **Claude interprets, not fetches.** The fetched data is injected into the Claude prompt as context. Claude's role shifts from "search the web" to "analyze this data."
3. **Evidence provenance.** Every piece of fetched data carries a source URL, retrieval timestamp, and raw record for audit.
4. **Graceful degradation.** If a source is unavailable (403, 429, timeout), the connector returns a failure record with reason. The agent still runs but emits a NEUTRAL signal with low confidence and the failure reason.
5. **No new agent behavior.** Existing agent roles, signal schema, and consensus logic are preserved. Only the data injection layer changes.

### 6.2 Proposed Module Structure

```text
sources/
  __init__.py           # Package init, exports connector factory
  base.py               # Abstract BaseConnector class
  sec_common.py         # Shared SEC EDGAR utilities (rate limiter, user-agent, caching)
  sec_form4.py          # Eddie's Form 4 connector
  sec_13f.py            # Maggie's 13F-HR connector
  fed_speeches.py       # Frank's Fed speech connector
  onchain_base.py       # Shared on-chain utilities
  etherscan.py          # Maya's Etherscan connector

evidence/
  __init__.py           # Package init
  schema.py             # EvidenceRecord dataclass and serialization
  store.py              # Evidence persistence (SQLite evidence table)

tests/
  test_sec_form4.py     # Unit tests for Form 4 connector
  test_sec_13f.py       # Unit tests for 13F connector
  test_fed_speeches.py  # Unit tests for Fed speech connector
  test_etherscan.py     # Unit tests for Etherscan connector
  test_evidence_schema.py  # Unit tests for evidence schema
  test_evidence_store.py   # Unit tests for evidence persistence
```

### 6.3 Connector Interface

```python
# sources/base.py (conceptual -- NOT implemented in CP08)

from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class FetchResult:
    """Result of a deterministic source fetch."""
    success: bool
    source_type: str          # e.g. "sec_form4", "sec_13f", "fed_speech", "etherscan"
    source_url: str           # canonical URL fetched
    retrieved_at: datetime    # UTC timestamp of retrieval
    records: list[dict]       # normalized evidence records
    raw_response: str         # raw HTTP response body (truncated if needed)
    failure_reason: str | None  # None if success, else error description

class BaseConnector:
    """Abstract base for all source connectors."""

    def fetch(self) -> FetchResult:
        """Fetch data from the source. Must be implemented by subclass."""
        raise NotImplementedError

    def format_for_prompt(self, result: FetchResult) -> str:
        """Format fetched data as context for Claude's prompt."""
        raise NotImplementedError
```

### 6.4 Source-Specific Connector Summaries

#### 6.4.1 SEC Form 4 Connector (`sec_form4.py`)

**API endpoint:** `https://efts.sec.gov/LATEST/search-index?q=%22&forms=4&dateRange=custom&startdt={yesterday}&enddt={today}`

**Fetch strategy:**
1. Query EFTS for Form 4 filings from the last 24 hours.
2. Parse the JSON response to extract accession numbers and filing metadata.
3. For each filing, fetch the XML from `https://www.sec.gov/Archives/edgar/data/{CIK}/{accession}/{primary_doc}`.
4. Parse XML for transaction details: issuer, insider, transaction code, shares, price, value.
5. Filter to open-market purchases (code P) >= $100k by C-suite/directors.
6. Return structured `FetchResult` with filtered records.

**Rate limit:** Max 10 requests/second to SEC. Implement 150ms delay between requests.

#### 6.4.2 SEC 13F-HR Connector (`sec_13f.py`)

**API endpoint:** `https://data.sec.gov/submissions/CIK{cik}.json` (for latest filing index) and the 13F XML/CSV for holdings.

**Fetch strategy:**
1. For each of the 5 fund CIKs, fetch the submissions index from `data.sec.gov`.
2. Find the most recent 13F-HR filing accession number.
3. Fetch the holdings table (InfoTable XML or CSV).
4. Parse holdings: issuer, CUSIP, shares, value.
5. Compare against locally cached prior-quarter holdings (stored in `.state/`).
6. Classify changes: NEW POSITION, INCREASED (>=25%), EXITED.
7. Filter to changes >= $50M.
8. Return structured `FetchResult`.

**Rate limit:** Same SEC rate limits. Cache prior-quarter data locally in `.state/13f_cache/`.

#### 6.4.3 Fed Speeches Connector (`fed_speeches.py`)

**API endpoint:** None (no JSON API exists). Must scrape HTML.

**Fetch strategy:**
1. Fetch `https://www.federalreserve.gov/newsevents/speeches.htm` via HTTP GET.
2. Parse the HTML table/list of recent speeches.
3. Filter to speeches published in the last 7 days.
4. For each speech, fetch the individual speech page.
5. Extract: speaker, date, title, and the first ~2000 characters of speech text.
6. Return structured `FetchResult` with speech excerpts.

**Note:** Claude will analyze the speech text for hawkish/dovish classification. The connector's job is to fetch and deliver the raw text, not classify.

**Rate limit:** Polite 1 request/second to federalreserve.gov. Cache speech pages for 24 hours.

#### 6.4.4 Etherscan Connector (`etherscan.py`)

**API endpoint:** `https://api.etherscan.io/api` (free tier, API key required).

**Fetch strategy:**
1. Use Etherscan API to query recent token transfers for WBTC, WETH, USDC, USDT.
2. Endpoint: `module=account&action=tokentx` for ERC-20 token transfers.
3. Filter to transfers >= $5M (estimate USD value using token decimals and a price lookup).
4. Classify transfers by matching from/to addresses against known CEX address lists.
5. Return structured `FetchResult` with qualifying transfers.

**Alternative approach:** Use Etherscan's "Large Transactions" pages or Alchemy webhooks for push-based monitoring.

**Rate limit:** Free tier allows 5 calls/second. Implement 250ms delay between requests.

**API key:** Requires `ETHERSCAN_API_KEY` in `.env`. Free tier available at etherscan.io.

### 6.5 How Retrieved Evidence Will Be Injected into Claude Prompts

The current `run_scout()` function signature remains unchanged. The change occurs in each agent's `main()` function:

```python
# Conceptual pattern for CP09 (NOT implemented in CP08)

def main() -> int:
    # 1. Fetch deterministic data
    connector = SecForm4Connector()
    result = connector.fetch()

    # 2. Format as prompt context
    context = connector.format_for_prompt(result)

    # 3. Inject into user prompt
    grounded_prompt = f"{USER}\n\n--- LIVE EDGAR DATA ---\n{context}"

    # 4. Run scout with grounded prompt
    sig = run_scout("eddie", SYSTEM, grounded_prompt)

    # 5. Store evidence
    store_evidence(result)

    return 0
```

This approach:
- Preserves the existing `run_scout()` interface.
- Does not require changes to `common.py` for basic grounding.
- Allows Claude to focus on analysis/interpretation rather than data fetching.
- Stores evidence independently of the signal for audit.

### 6.6 How Source URLs / Accession Numbers / Transaction Hashes Will Be Stored

Two storage mechanisms:

1. **Evidence table in `state.db`:** New SQLite table for structured evidence records linked to signals.
2. **Raw field in signals table:** The existing `raw` column in the `signals` table will naturally contain the grounded prompt output, which includes source references.

---

## 7. Proposed Evidence Schema

```python
# evidence/schema.py (conceptual -- NOT implemented in CP08)

@dataclass
class EvidenceRecord:
    """A single piece of auditable evidence from a source connector."""
    id: int | None           # auto-incremented
    source_type: str         # "sec_form4", "sec_13f", "fed_speech", "etherscan"
    source_url: str          # canonical URL or API endpoint
    canonical_id: str        # accession number, speech URL, tx hash
    retrieved_at: str        # ISO 8601 UTC timestamp
    agent: str               # "eddie", "maggie", "frank", "maya"
    signal_id: int | None    # FK to signals.id (linked after signal is recorded)
    raw_data: str            # JSON-serialized raw fetched data
    normalized_data: str     # JSON-serialized normalized/filtered data
    interpretation: str      # agent's interpretation (from Claude response)
    confidence: int          # 1-5
    failure_reason: str | None  # None if fetch succeeded
```

**SQLite DDL (conceptual):**

```sql
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    canonical_id TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    agent TEXT NOT NULL,
    signal_id INTEGER,
    raw_data TEXT NOT NULL,
    normalized_data TEXT NOT NULL,
    interpretation TEXT DEFAULT '',
    confidence INTEGER DEFAULT 1,
    failure_reason TEXT,
    FOREIGN KEY (signal_id) REFERENCES signals(id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_agent ON evidence(agent);
CREATE INDEX IF NOT EXISTS idx_evidence_ts ON evidence(retrieved_at);
CREATE INDEX IF NOT EXISTS idx_evidence_canonical ON evidence(canonical_id);
```

---

## 8. Proposed State DB / Storage Changes

### 8.1 New `evidence` Table

Add the `evidence` table described in section 7 to `state.db`. Managed by `evidence/store.py`.

### 8.2 New `.state/13f_cache/` Directory

Store prior-quarter 13F holdings data for Maggie's quarter-over-quarter comparison. Files named `{CIK}_{quarter}.json`.

### 8.3 New `.state/cache/` Directory

General HTTP response cache directory for SEC and Fed speech pages. Files named by URL hash with TTL metadata.

### 8.4 No Changes to Existing Tables

The `signals` and `consensus` tables remain unchanged. The existing `raw` column in `signals` will naturally contain more useful data once prompts include real source material.

### 8.5 `.gitignore` Updates

Add to `.gitignore`:
```text
.state/13f_cache/
.state/cache/
```

These directories contain fetched data that should not be committed.

---

## 9. Proposed Tests

| Test File | Tests |
| --------- | ----- |
| `tests/test_sec_form4.py` | Mock EFTS JSON response parsing; XML filing parsing; filter logic (code P, >= $100k, C-suite); rate limiter behavior; 403/429 handling |
| `tests/test_sec_13f.py` | Mock submissions index parsing; holdings table parsing; quarter comparison logic; NEW/INCREASED/EXITED classification; $50M filter |
| `tests/test_fed_speeches.py` | Mock HTML page parsing; speech extraction; date filtering; truncation |
| `tests/test_etherscan.py` | Mock API response parsing; transfer filtering; USD estimation; CEX address matching; API key handling |
| `tests/test_evidence_schema.py` | EvidenceRecord creation; JSON serialization/deserialization; validation |
| `tests/test_evidence_store.py` | SQLite table creation; insert/query/link operations; index verification |

**Testing strategy:**
- All HTTP calls mocked using `unittest.mock.patch` on `urllib.request.urlopen`.
- No real network calls in tests.
- Tests use deterministic sample data (real filing formats from SEC).
- Each connector tested independently.
- Integration test: connector -> evidence store -> prompt injection -> signal verification.

---

## 10. Proposed New Dependencies

| Package | Purpose | License |
| ------- | ------- | ------- |
| `requests` | HTTP client for source connectors (preferred over raw urllib for robustness) | Apache 2.0 |

**Optional / deferred:**
| Package | Purpose | Notes |
| ------- | ------- | ----- |
| `beautifulsoup4` + `lxml` | HTML parsing for Fed speeches | Only if regex-based parsing proves insufficient |
| `defusedxml` | Safe XML parsing for SEC filings | If processing untrusted XML |

**Rationale:** The current project uses only `anthropic` and `python-dotenv`. Adding `requests` provides connection pooling, retry logic, and cleaner API. `beautifulsoup4` is deferred -- initial Fed speech parsing may work with regex or `html.parser` from stdlib.

**Minimal approach:** If dependency count must stay low, all connectors can use `urllib.request` (already in stdlib, already used by `send_telegram()` in `common.py`). This avoids adding any new packages.

---

## 11. SEC Compliance / Access Plan

### 11.1 User-Agent Header

All requests to SEC domains must include a descriptive `User-Agent` header per SEC guidance:

```text
User-Agent: InsiderRoutines/1.0 (contact@example.com)
```

The contact email should be configurable via `.env`:

```text
SEC_USER_AGENT=InsiderRoutines/1.0 (roger@example.com)
```

### 11.2 Request Rate

- Maximum 10 requests per second to SEC domains (per SEC fair-access guidance).
- Implementation: enforce minimum 150ms between requests via a shared rate limiter in `sec_common.py`.
- Eddie (daily): ~5-20 requests per run (EFTS search + a few filing XML fetches). Well within limits.
- Maggie (weekly): ~10-15 requests per run (5 CIK submissions + 5 holdings files + 5 prior-quarter). Well within limits.

### 11.3 Local Caching

- Cache EFTS search results for 1 hour (Eddie runs daily, no intra-day re-fetches needed).
- Cache 13F holdings files for 24 hours (Maggie runs weekly).
- Cache filing XML for 7 days (filings do not change after initial posting, except amendments).
- Cache stored in `.state/cache/` with TTL metadata files.

### 11.4 HTTP Error Handling

| Status Code | Behavior |
| ----------- | -------- |
| 200 | Process normally |
| 301/302 | Follow redirect (max 3 hops) |
| 403 | Log "access denied," return failure FetchResult, agent emits NEUTRAL |
| 429 | Log "rate limited," wait 60 seconds, retry once. If still 429, return failure. |
| 500/502/503 | Log server error, retry once after 10 seconds. If still failing, return failure. |
| Timeout (30s) | Log timeout, return failure FetchResult. |

### 11.5 No Aggressive Scraping

- No parallel requests to SEC domains.
- No recursive crawling of filing indexes.
- No bulk downloading of all Form 4 filings (only filtered results).
- Respect `robots.txt` (SEC EDGAR allows programmatic access per their developer guidance).

---

## 12. On-Chain Source / API Strategy

### 12.1 Primary: Etherscan API

**Endpoint:** `https://api.etherscan.io/api`

**Modules used:**
- `module=account&action=tokentx` -- ERC-20 token transfers for specific contract addresses (WBTC, WETH, USDC, USDT).
- `module=proxy&action=eth_blockNumber` -- current block for time windowing.

**Rate limit:** Free tier = 5 calls/second. Implement 250ms delay.

**API key:** Required. Free at etherscan.io. Stored as `ETHERSCAN_API_KEY` in `.env`.

**Token contract addresses (Ethereum mainnet):**

| Token | Contract |
| ----- | -------- |
| WBTC | `0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599` |
| WETH | `0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2` |
| USDC | `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48` |
| USDT | `0xdAC17F958D2ee523a2206206994597C13D831ec7` |

### 12.2 USD Value Estimation

For transfer value estimation:
- WBTC/WETH: Use CoinGecko free API (`api.coingecko.com/api/v3/simple/price`) for approximate USD price. No API key needed for free tier (10-30 calls/min).
- USDC/USDT: Assume 1:1 USD peg.

### 12.3 CEX Address Classification

Maintain a local JSON file of known CEX deposit/withdrawal addresses:
- Source: public Etherscan label data or community-maintained lists.
- Store as `config/cex_addresses.json` (gitignored if it contains large datasets, or committed if small).
- Fallback: if address not in list, classify as "unknown" and do not flag as accumulation/distribution.

### 12.4 Alternatives Evaluated

| Source | Status | Notes |
| ------ | ------ | ----- |
| **Whale Alert API** | **Rejected** | Paid only, no free tier. |
| **Alchemy Webhooks** | **Deferred** | Push-based (good for real-time), but requires webhook endpoint. Not suitable for batch polling from a local Windows machine. |
| **Blockchain.com API** | **Deferred** | Limited to BTC/BCH. Does not cover ERC-20 tokens. |
| **Etherscan** | **Selected** | Free tier, covers all 4 target tokens, well-documented JSON API. |

### 12.5 Bitcoin (Native BTC) Strategy

The original prompt mentions WBTC (an ERC-20 token on Ethereum), not native BTC. WBTC whale moves are trackable via Etherscan. If native BTC tracking is desired later, blockchain.com or mempool.space APIs can be added as a separate connector.

---

## 13. Risks / Blockers

| # | Risk | Severity | Mitigation |
| - | ---- | -------- | ---------- |
| 1 | SEC EDGAR EFTS API may change endpoints or response format | MEDIUM | Pin to known endpoint; add response validation; monitor for 404s |
| 2 | Fed speeches page has no JSON API -- HTML scraping is fragile | HIGH | Use robust parsing with fallback patterns; validate extracted data; cache aggressively |
| 3 | Etherscan free tier rate limits (5/sec) may be insufficient for large token transfer scans | MEDIUM | Optimize queries (paginate, use block ranges); cache results; upgrade to paid tier if needed |
| 4 | Etherscan API key required -- Roger must register | LOW | Free registration at etherscan.io; add `ETHERSCAN_API_KEY` to `.env.example` |
| 5 | SEC filing XML format varies across filing types | MEDIUM | Validate XML structure defensively; log and skip malformed filings |
| 6 | CEX address lists become stale | LOW | Periodically refresh from public sources; treat unknown addresses conservatively |
| 7 | 13F quarter-over-quarter comparison requires historical cache | LOW | First run has no prior data -- emit informational NEUTRAL signal; cache builds over time |
| 8 | Model IDs may deprecate during CP09 | MEDIUM | Model IDs are env-configurable; update when new models are available |
| 9 | `requests` dependency adds supply-chain surface | LOW | Can use stdlib `urllib.request` instead if preferred |
| 10 | Fed speeches may include PDFs or non-HTML formats | LOW | Skip non-HTML speeches on first pass; add PDF support later if needed |

**No blocking issues identified.** All risks have feasible mitigations.

---

## 14. Recommended CP09 Implementation Scope

### Phase 1 (CP09 Core -- recommended)

1. Implement `sources/base.py` -- abstract connector and FetchResult.
2. Implement `sources/sec_common.py` -- rate limiter, user-agent, caching.
3. Implement `sources/sec_form4.py` -- Eddie's Form 4 connector.
4. Implement `evidence/schema.py` and `evidence/store.py`.
5. Modify `agents/eddie.py` to use the connector.
6. Write tests for Form 4 connector and evidence store.
7. Validate Eddie produces grounded signals from real SEC data.

### Phase 2 (CP09 Extended -- if time permits)

8. Implement `sources/sec_13f.py` -- Maggie's 13F connector.
9. Implement `sources/fed_speeches.py` -- Frank's Fed speech connector.
10. Modify `agents/maggie.py` and `agents/frank.py` to use connectors.
11. Write tests for 13F and Fed speech connectors.

### Phase 3 (CP10 or later -- on-chain)

12. Implement `sources/etherscan.py` -- Maya's Etherscan connector.
13. Implement `sources/onchain_base.py` -- shared on-chain utilities.
14. Modify `agents/maya.py` to use the connector.
15. Write tests for Etherscan connector.

### Rationale for Phasing

- Eddie (SEC Form 4) is the flagship agent and the simplest connector to validate end-to-end.
- SEC connectors share infrastructure (`sec_common.py`), so building Eddie first creates reusable foundations.
- Fed speeches require HTML scraping, which is more fragile and benefits from the patterns established by SEC connectors.
- On-chain requires an external API key and has different error/rate-limit characteristics.

### Agents NOT Requiring CP09 Changes

- **Janet:** Already grounded (local files). No connector needed.
- **Sophie:** Already grounded (local SQLite). No connector needed.
- **Ross:** Already grounded (local SQLite + delivery). No connector needed.

---

## 15. Confirmation: No Code Implementation Was Performed

No source connectors, evidence modules, or agent modifications were implemented in CP08. All code snippets in this report are conceptual illustrations only.

---

## 16. Confirmation: No Dependencies Were Installed

No `pip install` or `requirements.txt` changes were made in CP08.

---

## 17. Confirmation: No Scheduled Tasks Were Changed

No Windows Task Scheduler tasks were created, modified, or deleted in CP08. All 7 tasks remain in their CP06 configuration.

---

## 18. Confirmation: No Commit or Push Was Performed

No `git commit` or `git push` commands were executed in CP08.

---

## 19. Awaiting PM Approval

CP08 (Live Source Grounding Plan) is complete. The report identifies 4 agents requiring deterministic source connectors (Eddie, Maggie, Frank, Maya) and 3 agents already grounded (Janet, Sophie, Ross). A connector architecture with evidence schema, SEC compliance plan, on-chain API strategy, testing approach, and phased implementation scope has been proposed.

**Awaiting PM approval before proceeding to CP09 (Source Connector Implementation).**
