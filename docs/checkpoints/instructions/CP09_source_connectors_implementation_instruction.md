# CP09 — Deterministic Source Connector Implementation Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP08 is approved. CP08 established that Eddie, Maggie, Frank, and Maya are currently prompt-only prototypes and need deterministic source grounding. Janet, Sophie, and Ross are already local deterministic agents.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP09 goal

Implement deterministic public-source connectors and an auditable evidence layer for the four ungrounded scout agents:

```text
Eddie  -> SEC EDGAR Form 4
Maggie -> SEC EDGAR 13F-HR
Frank  -> Federal Reserve speeches / monetary-policy communications
Maya   -> on-chain whale-transfer source strategy, with Etherscan-compatible implementation where possible
```

CP09 should implement code and tests, but it must not commit, push, or modify Windows Task Scheduler tasks.

## Key CP08 findings carried forward

1. Eddie, Maggie, Frank, and Maya are Classification C: prompt-only / not source-grounded.
2. Janet is Classification B: deterministic local portfolio files.
3. Sophie is Classification A: deterministic local SQLite.
4. Ross is Classification A: deterministic local SQLite + dry-run delivery.
5. Grounded scout output must preserve source evidence, not just Claude interpretation.
6. SEC access must use a descriptive user-agent, reasonable rate limiting, local caching, and graceful 403/429 handling.
7. Etherscan free-tier style strategy is acceptable for Maya, but the implementation must degrade gracefully if no API key is present.
8. Federal Reserve speech parsing is high-risk because it is HTML-based; implement conservative parsing and tests.

## Critical safety constraints

Do not:

1. Print `.env` contents.
2. Print API keys, passwords, tokens, or secrets.
3. Send real emails.
4. Send real Telegram messages.
5. Turn off Ross dry-run mode.
6. Register, modify, delete, or manually trigger Windows Task Scheduler tasks.
7. Commit files.
8. Push to GitHub.
9. Force-push.
10. Modify preserved source files in `docs/source/`.
11. Create or modify real private portfolio files:
   ```text
   config/portfolio_target.json
   config/portfolio_current.json
   ```
12. Store secrets in code, test fixtures, logs, state DB, or docs.
13. Use aggressive scraping or high-frequency polling.

## Required preconditions

Confirm these exist before continuing:

```text
docs/checkpoints/reports/CP08_live_source_grounding_plan_report.md
docs/checkpoints/instructions/CP08_live_source_grounding_plan_instruction.md
agents/common.py
agents/eddie.py
agents/maggie.py
agents/frank.py
agents/maya.py
agents/janet.py
agents/sophie.py
agents/ross.py
.venv/
.env
```

Also confirm `.env` is ignored without printing its contents:

```powershell
git check-ignore -v .env
```

Confirm scheduled tasks exist but do not modify or trigger them:

```powershell
Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Select-Object TaskName, State
```

If any scheduled task is actively running, stop and report before editing runtime code.

## Implementation scope

### 1. Evidence schema

Create:

```text
evidence/__init__.py
evidence/schema.py
evidence/store.py
```

Implement typed evidence models using `dataclasses` or lightweight classes.

Required evidence concepts:

```text
SourceEvidence
SourceFetchResult
EvidenceBundle
```

Minimum fields for `SourceEvidence`:

```text
source_type: str
source_name: str
source_url: str
retrieved_at: str
canonical_id: str | None
raw_excerpt: str | None
normalized: dict[str, object]
metadata: dict[str, object]
```

Minimum fields for `SourceFetchResult`:

```text
ok: bool
source_name: str
evidence: list[SourceEvidence]
error_type: str | None
error_message: str | None
retrieved_at: str
```

Requirements:

1. All public functions/classes must have docstrings.
2. All functions must use type hints.
3. JSON serialization helpers must be included.
4. No third-party dependency should be required for the evidence layer.
5. Evidence records must not contain secrets.

### 2. Source connector package

Create:

```text
sources/__init__.py
sources/base.py
sources/sec_common.py
sources/sec_form4.py
sources/sec_13f.py
sources/fed_speeches.py
sources/onchain_base.py
sources/etherscan.py
```

All connector modules must:

1. Use type hints.
2. Include docstrings for all public functions/classes.
3. Avoid live network calls at import time.
4. Provide safe timeout handling.
5. Provide clear error categories.
6. Support test injection/mocking where practical.
7. Return `SourceFetchResult` / `SourceEvidence` objects.
8. Use descriptive user-agent logic where required.
9. Use local cache under `.state/cache/` where practical.
10. Never print secrets.

### 3. SEC common connector

`source/sec_common.py` should provide reusable SEC helpers.

Required behavior:

1. Read a descriptive SEC user-agent from environment, e.g.:
   ```text
   SEC_USER_AGENT
   ```
2. If `SEC_USER_AGENT` is missing, use a safe placeholder that clearly instructs the user to configure it, but do not fail imports.
3. Use reasonable timeouts.
4. Include basic request helper with:
   - user-agent header
   - accept encoding/header where appropriate
   - rate-limit pause
   - cache support where practical
   - graceful 403/429 handling
5. Do not make requests faster than a conservative default rate.
6. Do not perform aggressive crawling.

### 4. Eddie Form 4 connector

`source/sec_form4.py` should implement deterministic retrieval/parsing for recent Form 4 evidence.

Implementation should support at least one safe path:

1. SEC submissions/companyfacts style endpoints when CIKs are supplied, or
2. EDGAR search endpoint if already used in the original prompt, or
3. a conservative connector scaffold with tested parsing helpers and a documented retrieval limitation.

The connector should produce evidence fields such as:

```text
accession_number
cik
issuer_name
insider_name
filing_date
transaction_date
transaction_code
security_title
shares
price
ownership_nature
source_url
```

If full live recent Form 4 search is too large for CP09, implement a reliable narrowly scoped connector and document the limitation.

### 5. Maggie 13F connector

`source/sec_13f.py` should implement deterministic retrieval/parsing for selected 13F-HR managers.

It should support configured manager CIKs for at least the entities identified in CP08, such as:

```text
Berkshire Hathaway
Bridgewater
Renaissance Technologies
Citadel
Two Sigma
```

If exact CIKs are already in the original prompt, use them. If not, create a config mapping with TODO notes and no fabricated claims.

Evidence fields should include:

```text
manager_name
manager_cik
accession_number
report_period
issuer_name
cusip
shares
value
source_url
```

Avoid pretending to perform prior-period comparison unless the code actually retrieves two periods.

### 6. Frank Federal Reserve connector

`source/fed_speeches.py` should implement conservative retrieval/parsing for Federal Reserve speeches or policy communications.

Required behavior:

1. Fetch or parse from `federalreserve.gov` source pages identified in CP08/original prompt.
2. Extract:
   ```text
   title
   speaker
   date
   url
   excerpt
   keywords
   ```
3. Provide a simple keyword-based policy-tone helper only as a first-pass signal, clearly labeled heuristic.
4. Store source URL and retrieved timestamp.
5. Gracefully handle HTML layout changes.

### 7. Maya on-chain connector

`source/etherscan.py` should implement an Etherscan-compatible connector with graceful no-key behavior.

Required behavior:

1. Read:
   ```text
   ETHERSCAN_API_KEY
   ```
   from environment if present.
2. Do not require `ETHERSCAN_API_KEY` for imports or tests.
3. If no key is present, return a clear `SourceFetchResult` error or limited no-key behavior.
4. Support token-transfer evidence shape:
   ```text
   chain
   token_symbol
   transaction_hash
   from_address
   to_address
   amount
   timestamp
   explorer_url
   ```
5. Do not log or print the API key.

### 8. Agent integration

Update the four scout agents only:

```text
agents/eddie.py
agents/maggie.py
agents/frank.py
agents/maya.py
```

They should:

1. Call their deterministic source connector before calling Claude.
2. Pass summarized source evidence into the Claude prompt.
3. Store source/evidence metadata with the generated signal if current state schema supports it.
4. If the current state schema does not support full evidence storage, write a minimal safe evidence record to `.state/evidence/` or propose schema migration.
5. When source retrieval fails, report the failure clearly and avoid fabricating signals.
6. Preserve existing dry-run and no-secrets behavior.
7. Keep imports safe.
8. Avoid live calls at import time.

Do not change Janet, Sophie, or Ross unless a narrow compatibility change is required.

### 9. State/evidence storage

If the existing SQLite schema cannot store evidence, implement a safe file-backed evidence store under:

```text
.state/evidence/
```

Requirements:

1. Directory is gitignored.
2. Evidence files are JSON.
3. Filename should include timestamp, agent name, and a safe unique suffix.
4. Evidence records must not contain secrets.
5. Agent signal should reference the evidence file path or evidence ID if feasible.

Do not break existing Sophie/Ross behavior.

### 10. Tests

Create a tests folder if needed:

```text
tests/
```

Required tests:

```text
tests/test_evidence_schema.py
tests/test_sec_common.py
tests/test_sec_form4.py
tests/test_sec_13f.py
tests/test_fed_speeches.py
tests/test_etherscan.py
```

Tests must not require live API keys or live network access.

Use static fixtures or mocked responses.

If pytest is added, update `requirements.txt` or a separate dev requirements file. Prefer:

```text
pytest
```

If using HTTP mocking, either use standard-library mocking or add a justified dependency.

### 11. Dependency policy

Prefer standard library where reasonable.

If dependencies are needed, update `requirements.txt` and install them in `.venv`.

Likely acceptable additions:

```text
pytest
requests
beautifulsoup4
```

Only add dependencies actually used.

After updating requirements, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 12. Documentation updates

Update:

```text
README.md
docs/install_notes_windows.md
```

Create if useful:

```text
docs/source_grounding.md
```

Documentation must explain:

1. Which agents are now source-grounded.
2. Which sources each connector uses.
3. Evidence storage approach.
4. SEC user-agent requirement.
5. Etherscan API key optionality/requirement.
6. Remaining limitations.
7. That signals remain informational and not trading advice.
8. Ross remains dry-run unless explicitly changed later.

## Required validation commands

Run and report:

```powershell
.\.venv\Scripts\python.exe --version
git status --short
git check-ignore -v .env
git check-ignore -v .claude/
git check-ignore -v .state/logs/smoke_test_windows.log
git check-ignore -v .state/evidence/test.json
git check-ignore -v config/portfolio_target.json
git check-ignore -v config/portfolio_current.json
```

Compile checks:

```powershell
.\.venv\Scripts\python.exe -m py_compile agents/common.py agents/eddie.py agents/maggie.py agents/frank.py agents/maya.py agents/janet.py agents/sophie.py agents/ross.py
.\.venv\Scripts\python.exe -m py_compile evidence/schema.py evidence/store.py sources/base.py sources/sec_common.py sources/sec_form4.py sources/sec_13f.py sources/fed_speeches.py sources/onchain_base.py sources/etherscan.py
```

Smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test_windows.ps1
```

Unit tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

If pytest is not used, document the alternative test command.

Optional direct safe runtime test:

Run at most one scout in controlled mode if the connector implementation is ready and no messages are sent. Prefer Eddie or Frank. Do not manually trigger scheduled tasks.

## Expected failure handling

If a live public source blocks access, rate limits, or changes HTML/API shape:

1. Do not fake data.
2. Return a `SourceFetchResult` with `ok=False`.
3. Log/report the error category.
4. Keep tests based on mocked fixtures passing.
5. Document the source limitation.

## Required CP09 report

Save the report to:

```text
docs/checkpoints/reports/CP09_source_connectors_implementation_report.md
```

The report must include:

1. Summary of work completed.
2. Files created.
3. Files modified.
4. Files preserved untouched.
5. Dependencies added and why.
6. Evidence schema summary.
7. Source connector summary by agent.
8. Agent integration summary.
9. Evidence storage summary.
10. SEC compliance implementation details.
11. Etherscan/on-chain implementation details.
12. Tests created.
13. Validation command outputs.
14. Smoke test result.
15. Unit test result.
16. Optional runtime test result, if performed.
17. Confirmation no secrets were printed.
18. Confirmation no real email was sent.
19. Confirmation no real Telegram message was sent.
20. Confirmation no scheduled tasks were changed or triggered.
21. Confirmation no commit or push was performed.
22. Risks/blockers.
23. Recommendation:
    - CP10 Grounded Runtime Validation, or
    - CP09B Connector Fixes, or
    - CP10 Commit/Push if everything is stable
24. Awaiting PM Approval section.

## End condition

After saving the report, respond only with:

1. The report path.
2. A short summary.
3. Any blocker requiring PM attention.
4. A statement that you are awaiting PM approval before CP10 or CP09B.
