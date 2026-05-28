# CP09 -- Source Connector Implementation Report

**Checkpoint:** CP09
**Date:** 2026-05-28
**Executor:** Claude Code (claude-opus-4-6)
**Instruction file:** `docs/checkpoints/instructions/CP09_source_connectors_implementation_instruction.md`

## 1. Summary of work completed

Implemented deterministic source connectors for all 4 external-facing scout agents (Eddie, Maggie, Frank, Maya). Each agent now fetches live data from its designated public source before prompting Claude, replacing the prior prompt-only prototype approach. Created a typed evidence schema for structured data capture and a file-backed persistence layer for auditability. All connectors handle errors gracefully and comply with SEC fair-access policies. 64 unit tests pass with no live network access required.

## 2. Files created

```text
evidence/__init__.py              Package init, exports schema classes
evidence/schema.py                SourceEvidence, SourceFetchResult, EvidenceBundle dataclasses
evidence/store.py                 File-backed JSON persistence under .state/evidence/

sources/__init__.py               Package init, exports BaseConnector
sources/base.py                   Abstract BaseConnector interface (fetch + format_for_prompt)
sources/sec_common.py             SEC EDGAR shared utilities (User-Agent, rate limiter, cache, HTTP)
sources/sec_form4.py              Form 4 EFTS connector (Eddie)
sources/sec_13f.py                13F-HR submissions connector (Maggie)
sources/fed_speeches.py           Fed speeches HTML scraper (Frank)
sources/onchain_base.py           On-chain utilities (CEX addresses, token decimals, USD estimation)
sources/etherscan.py              Etherscan ERC-20 token transfer connector (Maya)

tests/__init__.py                 Test package init
tests/conftest.py                 Shared fixtures (sys.path setup)
tests/test_evidence_schema.py     10 tests for evidence schema
tests/test_sec_common.py          9 tests for SEC common utilities
tests/test_sec_form4.py           7 tests for Form 4 connector
tests/test_sec_13f.py             6 tests for 13F connector
tests/test_fed_speeches.py        12 tests for Fed speeches connector
tests/test_etherscan.py           20 tests for Etherscan + onchain_base

docs/source_grounding.md          Source connector architecture documentation
```

## 3. Files modified

```text
agents/eddie.py                   Added SecForm4Connector integration, evidence storage, USER_TEMPLATE
agents/maggie.py                  Added Sec13FConnector integration, evidence storage, USER_TEMPLATE
agents/frank.py                   Added FedSpeechesConnector integration, evidence storage, USER_TEMPLATE
agents/maya.py                    Added EtherscanConnector integration, evidence storage, USER_TEMPLATE
requirements.txt                  Added pytest
README.md                         Updated Source Grounding section, Status, Project Structure, Limitations
docs/install_notes_windows.md     Updated Live Data Access section, added CP09 notes
docs/checkpoints/README.md        Added CP09 row to checkpoint history table
```

## 4. Files preserved untouched

```text
agents/common.py                  Shared foundation (no changes needed)
agents/janet.py                   Portfolio drift scout (local data, no connector needed)
agents/sophie.py                  Consensus engine (local SQLite, no connector needed)
agents/ross.py                    Dispatcher (local logic, no connector needed)
.env                              User credentials (gitignored)
.env.example                      Credential template
.gitignore                        Security exclusions
config/                           Portfolio example files
install/                          Windows Task Scheduler scripts
scripts/                          Helper scripts (run_agent, smoke_test, init_project)
docs/source/                      Original prompt, transcript, handoff prompt
docs/checkpoints/CHECKPOINT_PROTOCOL.md
All prior checkpoint instructions and reports
```

## 5. Dependencies added and why

| Package | Version | Reason |
| --- | --- | --- |
| `pytest` | Latest via pip | Unit testing framework for 64 connector and schema tests |

No other dependencies added. All connectors use Python standard library (`urllib.request`, `json`, `html.parser`, `hashlib`, `threading`, `pathlib`, `dataclasses`, `uuid`). The instruction listed `requests` and `beautifulsoup4` as acceptable, but standard-library alternatives were sufficient.

## 6. Evidence schema summary

Three dataclasses in `evidence/schema.py`:

- **`SourceEvidence`**: Individual piece of evidence from a source. Fields: `source_type`, `source_name`, `source_url`, `retrieved_at` (ISO-8601 UTC), `canonical_id`, `raw_excerpt`, `normalized` (dict), `metadata` (dict). Supports `to_dict()`, `to_json()`, `from_dict()`.

- **`SourceFetchResult`**: Result of a connector fetch operation. Fields: `ok` (bool), `source_name`, `evidence` (list of SourceEvidence), `error_type`, `error_message`, `retrieved_at` (auto-populated). Includes `failure()` classmethod for error construction. Supports serialization roundtrips.

- **`EvidenceBundle`**: Wrapper tying an agent name to its fetch result and storage path. Used by `save_evidence()` in `evidence/store.py`.

Storage: JSON files under `.state/evidence/` named `{timestamp}_{agent}_{uuid}.json`. Functions: `save_evidence()`, `load_evidence()`, `list_evidence()`.

## 7. Source connector summary by agent

### Eddie -- SEC Form 4

- **Connector**: `SecForm4Connector` (`sources/sec_form4.py`)
- **Source**: SEC EDGAR Full-Text Search (EFTS) at `efts.sec.gov`
- **Query**: Form 4 filings from the last 24 hours
- **Output**: Filing accession numbers, entity names, filing dates
- **Error handling**: Returns `SourceFetchResult.failure()` on HTTP errors or invalid JSON

### Maggie -- 13F-HR Filings

- **Connector**: `Sec13FConnector` (`sources/sec_13f.py`)
- **Source**: SEC EDGAR submissions API at `data.sec.gov`
- **Default managers**: Berkshire Hathaway (0001067983), Bridgewater (0001350694), Renaissance (0001037389), Citadel (0001423053), Two Sigma (0001179392)
- **Output**: Most recent 13F-HR accession number, filing date, report period per manager
- **Error handling**: Per-manager failures don't block other managers

### Frank -- Federal Reserve Speeches

- **Connector**: `FedSpeechesConnector` (`sources/fed_speeches.py`)
- **Source**: `federalreserve.gov/newsevents/speeches.htm`
- **Lookback**: 7 days (configurable)
- **Output**: Speaker name, date, title, text excerpt (first 2000 chars), hawkish/dovish tone scores
- **Tone analysis**: Keyword heuristic counting hawkish terms (inflation, restrictive, tighten, rate hike) vs dovish terms (patient, accommodative, easing, soft landing)
- **Error handling**: Individual speech fetch failures don't block the listing

### Maya -- On-Chain Whale Moves

- **Connector**: `EtherscanConnector` (`sources/etherscan.py`)
- **Source**: Etherscan API for ERC-20 token transfers
- **Tokens**: WBTC, WETH, USDC, USDT (configurable)
- **Logic**: Classifies transfers as accumulation (CEX -> private) or distribution (private -> CEX) based on 15+ known exchange addresses (Binance, Coinbase, Bitfinex, Kraken, OKX, etc.)
- **Requirement**: `ETHERSCAN_API_KEY` env var
- **Error handling**: Degrades gracefully to config_error without API key

## 8. Agent integration summary

All 4 agents follow the same integration pattern:

1. Import connector class, `EvidenceBundle`, `save_evidence`
2. In `main()`, instantiate connector and call `fetch()`
3. Wrap result in `EvidenceBundle` and persist via `save_evidence()`
4. Call `format_for_prompt(result)` to get plain-text summary
5. Inject summary into `USER_TEMPLATE` with `{source_data}` placeholder
6. Pass formatted prompt to `run_scout()` (unchanged interface in `common.py`)
7. `SYSTEM` prompt updated from "Query SEC EDGAR..." to "Review the LIVE ... data provided below"

The `common.py` module was not modified. The `run_scout()` function accepts any prompt string, so the integration is non-breaking.

## 9. Evidence storage summary

- **Location**: `.state/evidence/`
- **Format**: JSON files, one per agent per fetch
- **Naming**: `{ISO_timestamp}_{agent}_{uuid4_prefix}.json`
- **Content**: Full `EvidenceBundle` serialized via `to_dict()` / `to_json()`
- **Retrieval**: `load_evidence(filepath)` deserializes back to `EvidenceBundle`
- **Listing**: `list_evidence(agent=None)` lists evidence files, optionally filtered by agent
- **Gitignored**: `.state/*` in `.gitignore` excludes all evidence files from version control

## 10. SEC compliance implementation details

- **User-Agent header**: All SEC requests include `User-Agent` read from `SEC_USER_AGENT` env var. Default placeholder: `"InsiderRoutines admin@example.com"`. User must set a real value per SEC fair-access policy.
- **Rate limiting**: Module-level `threading.Lock` in `sec_common.py` enforces 200ms minimum between SEC EDGAR requests.
- **Caching**: File-based cache under `.state/cache/`. Cache key is SHA-256 hash of the URL. Default TTL: 300 seconds. Cache stores response body, status code, and timestamp as JSON.
- **Error handling**: HTTP 403 (blocked) and 429 (rate limited) return `SourceFetchResult.failure()` with categorized `error_type` ("http_error") and descriptive `error_message`. No automatic retries to avoid further rate limit violations.
- **Accept header**: SEC JSON endpoints use `Accept: application/json`. EFTS uses default.

## 11. Etherscan/on-chain implementation details

- **API key**: Read from `ETHERSCAN_API_KEY` env var. If missing, connector returns `SourceFetchResult.failure(error_type="config_error")` immediately.
- **Rate limiting**: 250ms between Etherscan API calls (module-level lock).
- **Token contracts**: WBTC, WETH, USDC, USDT addresses defined in `onchain_base.py`.
- **CEX address database**: 15+ known exchange deposit addresses for Binance (3), Coinbase (2), Bitfinex, Kraken, OKX, Gemini, Huobi, KuCoin, Gate.io, Bybit, Crypto.com, FTX (legacy).
- **Transfer classification**: `accumulation` = from CEX to private address (whale buying). `distribution` = from private to CEX address (whale selling).
- **USD estimation**: Stablecoins (USDC, USDT, DAI, BUSD) at 1:1. Other tokens use optional `prices` dict. Unknown tokens estimate at $0.
- **Minimum filter**: Default `min_usd_value=5_000_000` filters out small transfers.

## 12. Tests created

| Test file | Tests | Coverage area |
| --- | --- | --- |
| `tests/test_evidence_schema.py` | 10 | SourceEvidence creation/serialization, SourceFetchResult success/failure/factory/roundtrip, EvidenceBundle |
| `tests/test_sec_common.py` | 9 | User-Agent default/env, cache key/write/read/expired/missing, sec_fetch success/cached/http_error, utcnow_iso |
| `tests/test_sec_form4.py` | 7 | Fetch success/empty/http_error/invalid_json, format_for_prompt success/failure/empty |
| `tests/test_sec_13f.py` | 6 | Fetch single_manager/no_13f/http_error/multiple_managers, format success/failure |
| `tests/test_fed_speeches.py` | 12 | keyword_tone hawkish/dovish/neutral, extract_speaker, extract_speech_text truncation/empty, connector fetch success/listing_failure/filters_old, format success/failure |
| `tests/test_etherscan.py` | 20 | onchain_base classify/is_cex/raw_to_token/usd_estimate, connector no_api_key/success/api_error, format no_key/with_data |
| **Total** | **64** | |

All tests use `unittest.mock` for HTTP mocking. No live network access required. No API keys needed.

## 13. Validation command outputs

### Python version

```
Python 3.11.9
```

### Git status

```
 M README.md
 M agents/eddie.py
 M agents/frank.py
 M agents/maggie.py
 M agents/maya.py
 M docs/checkpoints/README.md
 M docs/install_notes_windows.md
 M requirements.txt
?? docs/checkpoints/instructions/CP08_live_source_grounding_plan_instruction.md
?? docs/checkpoints/instructions/CP09_source_connectors_implementation_instruction.md
?? docs/checkpoints/reports/CP08_live_source_grounding_plan_report.md
?? docs/source_grounding.md
?? evidence/
?? sources/
?? tests/
```

### Gitignore verification

```
.gitignore:2:.env                              .env
.gitignore:38:.claude/                         .claude/
.gitignore:21:logs/                            .state/logs/smoke_test_windows.log
.gitignore:17:.state/*                         .state/evidence/test.json
.gitignore:31:config/portfolio_target.json     config/portfolio_target.json
.gitignore:32:config/portfolio_current.json    config/portfolio_current.json
```

All 6 sensitive paths confirmed gitignored.

### Compile checks

```
py_compile agents/common.py agents/eddie.py agents/maggie.py agents/frank.py agents/maya.py agents/janet.py agents/sophie.py agents/ross.py
-- PASS (no output = no errors)

py_compile evidence/schema.py evidence/store.py sources/base.py sources/sec_common.py sources/sec_form4.py sources/sec_13f.py sources/fed_speeches.py sources/onchain_base.py sources/etherscan.py
-- PASS (no output = no errors)
```

All 17 Python files compile cleanly.

## 14. Smoke test result

```
Insider Routines -- Smoke Test
==============================
Results: 31 passed, 0 failed, 0 warnings
Status: ALL CHECKS PASSED
```

Full output includes Python check, 17 required file checks, .env.example check, 3 .gitignore protection checks, 8 py_compile checks, and state directory check.

## 15. Unit test result

```
................................................................         [100%]
64 passed in 0.18s
```

All 64 tests pass. No failures, no warnings, no skips.

## 16. Optional runtime test result

Not performed. The CP09 instruction marks this as optional and recommends it only if the connector implementation is ready and no messages are sent. Since the connectors are fully tested via mocked unit tests and a grounded runtime validation checkpoint (CP10) is recommended, a live runtime test was deferred.

## 17. Confirmation: no secrets were printed

Confirmed. No API keys, passwords, tokens, or credentials were printed to stdout, stderr, or log files during this checkpoint. All test mocks use placeholder values (`"test_key"`, `"test_agent"`). The `SEC_USER_AGENT` default placeholder (`"InsiderRoutines admin@example.com"`) contains no real contact information.

## 18. Confirmation: no real email was sent

Confirmed. Ross was not executed. The `send_email()` function in `common.py` was not called. `ROSS_DRY_RUN` remains `true` in `.env`.

## 19. Confirmation: no real Telegram message was sent

Confirmed. Ross was not executed. The `send_telegram()` function in `common.py` was not called.

## 20. Confirmation: no scheduled tasks were changed or triggered

Confirmed. All 7 `\InsiderRoutines\Insider-*` tasks remain in their original state from CP06. No tasks were created, modified, deleted, or manually triggered during CP09.

## 21. Confirmation: no commit or push was performed

Confirmed. `git status` shows all changes as unstaged modifications and untracked files. No commits were made. No pushes were performed. The last commit remains from CP07.

## 22. Risks/blockers

| Risk | Severity | Mitigation |
| --- | --- | --- |
| SEC EFTS may change API shape or rate-limit more aggressively | Medium | Graceful failure via SourceFetchResult; tests use mocked responses |
| Fed website HTML structure may change | Medium | regex/parser-based extraction; failure returns empty result |
| Etherscan free-tier rate limits (5 req/sec) | Low | 250ms rate limiter; configurable token list |
| SEC_USER_AGENT must be set to real value before production use | Medium | Default placeholder works for testing; documented in README and install_notes |
| Token price estimation is static (no live price feeds) | Low | Documented limitation; prices dict is configurable |
| No live runtime validation yet performed | Medium | Recommend CP10 for grounded runtime validation |

No blocking issues. All connectors degrade gracefully on error.

## 23. Recommendation

**Recommend CP10: Commit/Push + Grounded Runtime Validation.**

Rationale:
- All source connectors are implemented and tested (64/64 unit tests pass).
- Evidence schema and storage are complete.
- All 4 agents are integrated with their connectors.
- Documentation is updated.
- No blocking issues exist.

The CP10 checkpoint should:
1. Commit and push all CP08 + CP09 changes to `origin/main`.
2. Optionally run one or two agents (Eddie, Frank) against live APIs to validate connector behavior with real data.
3. Verify evidence files are created under `.state/evidence/`.
4. Confirm signals are still written to `.state/state.db`.

If PM prefers to validate connectors before committing, a CP09B (Connector Fixes) checkpoint is available as an alternative.

## 24. Awaiting PM Approval

This checkpoint report has been saved. All CP09 deliverables are complete:
- Evidence schema package (3 files)
- Source connector package (8 files)
- Agent integration (4 agents updated)
- Unit tests (64 tests, all passing)
- Documentation (4 files updated/created)
- All validation commands passed

**Awaiting PM approval before proceeding to CP10 (Commit/Push + Grounded Runtime Validation) or CP09B (Connector Fixes).**
