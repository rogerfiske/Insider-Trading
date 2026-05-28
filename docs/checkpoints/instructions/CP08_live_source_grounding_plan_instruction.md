# CP08 — Live Source Grounding Plan Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

CP07 is complete. The project is installed, scheduled, committed, and pushed to `origin/main`.

CP08 starts the next phase: converting the original prompt’s intended source references into a real, auditable source-grounding implementation plan.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP08 goal

Produce a source-grounding design plan only.

Do not implement connectors yet.

The original one-shot prompt already describes intended sources for the agents. CP08 must extract those intended sources, compare them to the current implementation, and propose a deterministic connector design for CP09.

## Required preconditions

Confirm these files exist before continuing:

```text
docs/source/original_prompt.md
docs/source/video_transcript.txt
docs/checkpoints/CHECKPOINT_PROTOCOL.md
docs/checkpoints/reports/CP07_final_review_commit_push_report.md
agents/eddie.py
agents/maggie.py
agents/frank.py
agents/maya.py
agents/janet.py
agents/sophie.py
agents/ross.py
agents/common.py
```

If any are missing, stop and report.

## Important context

The current installed system works operationally, but scout agents are still prompt-based prototypes. They may ask Claude to search or reason about public sources, but the code does not yet reliably fetch, parse, cite, and store source evidence.

CP08 must not assume that source grounding exists just because the prompt tells an agent to “search” or “monitor” something.

## Allowed actions

You may:

1. Read `docs/source/original_prompt.md`.
2. Read the current agent files.
3. Read current docs and checkpoint reports.
4. Inspect project structure.
5. Create a CP08 design report.
6. Create a source-grounding plan document if useful.
7. Update documentation only if the update is limited to recording CP08 planning status.

## Prohibited actions

Do not:

1. Implement source connectors.
2. Modify agent runtime behavior.
3. Install dependencies.
4. Create or modify `.env`.
5. Request or print API keys.
6. Send real email.
7. Send real Telegram messages.
8. Register, modify, or delete scheduled tasks.
9. Commit files.
10. Push to GitHub.
11. Force-push.
12. Modify preserved source files in `docs/source/`.

## Required source extraction

Extract the intended source/reference targets from the original prompt for each agent:

```text
Eddie
Maggie
Frank
Maya
Janet
Sophie
Ross
```

For each agent, identify:

1. Intended source category.
2. Specific source URLs, APIs, or domains mentioned in the original prompt.
3. Specific filing types, event types, symbols, funds, or entities mentioned.
4. Whether the current code actually fetches those sources deterministically.
5. Whether the current code relies on Claude prompt-only behavior.
6. Evidence fields that should be stored for auditability.

## Expected initial source map

Do not blindly assume this list is complete. Verify against `docs/source/original_prompt.md`.

Expected source targets likely include:

### Eddie

Likely intended source:

```text
SEC EDGAR Form 4 insider-trading filings
```

Expected domains/APIs to check in source prompt:

```text
sec.gov
efts.sec.gov
data.sec.gov
www.sec.gov/edgar
```

Evidence candidates:

```text
accession number
CIK
issuer
insider name
transaction date
filing date
security title
transaction code
shares
price
ownership nature
source URL
raw filing URL
```

### Maggie

Likely intended source:

```text
SEC EDGAR 13F-HR institutional holdings filings
```

Expected funds/entities may include:

```text
Berkshire Hathaway
Bridgewater
Renaissance Technologies
Citadel
Two Sigma
```

Evidence candidates:

```text
manager CIK
13F accession number
report period
issuer
CUSIP
shares
value
prior-period comparison
source URL
```

### Frank

Likely intended source:

```text
Federal Reserve speeches, FOMC commentary, monetary-policy communications
```

Expected domains:

```text
federalreserve.gov
```

Evidence candidates:

```text
speech URL
speaker
date
title
policy keywords
hawkish/dovish score
quoted excerpt
source URL
```

### Maya

Likely intended source:

```text
on-chain whale transfer monitoring
```

Expected source categories:

```text
Etherscan
Blockchain.com
token transfer APIs
major assets such as WBTC, WETH, USDC, USDT
```

Evidence candidates:

```text
chain
token symbol
transaction hash
from address
to address
amount
USD estimate
timestamp
explorer URL
```

### Janet

Likely source:

```text
local portfolio_target and portfolio_current JSON files
```

Evidence candidates:

```text
symbol
target weight
current weight
delta percentage points
threshold
source file
```

### Sophie

Likely source:

```text
local signal/state database
```

Evidence candidates:

```text
signal IDs
agent names
symbols
directions
confidence
timestamps
agreement count
consensus rule
```

### Ross

Likely source:

```text
local consensus events and alert-dispatch configuration
```

Evidence candidates:

```text
consensus ID
dispatch mode
dry-run flag
recipient channel
timestamp
message hash or preview
```

## Current implementation gap analysis

Compare the extracted source intent to current code.

For each agent, classify current grounding status:

```text
A — deterministic and grounded now
B — local deterministic only
C — prompt-only / not actually source-grounded
D — missing / unclear
```

Explain the classification.

## Required CP09 connector architecture proposal

Propose a CP09 implementation plan that introduces deterministic source connectors while preserving existing agent roles.

The plan should include:

1. Proposed new package/module structure.
2. Connector interfaces.
3. Source-specific connector modules.
4. Evidence schema.
5. State DB changes, if needed.
6. Testing strategy.
7. Dependency changes.
8. Rate-limit and user-agent compliance.
9. Error handling.
10. Fallback behavior when a source is unavailable.
11. How retrieved evidence will be injected into Claude prompts.
12. How source URLs/accession numbers/transaction hashes will be stored.

Suggested possible module structure:

```text
sources/
  __init__.py
  base.py
  sec_common.py
  sec_form4.py
  sec_13f.py
  fed_speeches.py
  onchain_base.py
  etherscan.py
  blockchain_info.py

evidence/
  __init__.py
  schema.py
  store.py

tests/
  test_sec_form4.py
  test_sec_13f.py
  test_fed_speeches.py
  test_evidence_schema.py
```

Do not create these files in CP08 unless the report needs placeholder paths in documentation. CP08 is planning only.

## SEC compliance planning

For SEC-related connectors, the CP08 report must include a plan to comply with SEC access guidance, including:

1. A descriptive user-agent.
2. Reasonable request rate.
3. Local caching.
4. Graceful handling of 403/429/rate-limit responses.
5. No aggressive scraping.

Do not implement yet.

## Evidence quality requirements

The CP08 plan must require future grounded scout outputs to include:

1. Source URL or canonical identifier.
2. Retrieval timestamp.
3. Source type.
4. Raw or normalized evidence record.
5. Agent interpretation.
6. Confidence score.
7. Failure reason if source retrieval failed.

## Required report

Save the CP08 report to:

```text
docs/checkpoints/reports/CP08_live_source_grounding_plan_report.md
```

The report must include:

1. Summary.
2. Files inspected.
3. Extracted original prompt source map by agent.
4. Current implementation gap analysis by agent.
5. Grounding status classification by agent.
6. Proposed CP09 connector architecture.
7. Proposed evidence schema.
8. Proposed state DB/storage changes.
9. Proposed tests.
10. Proposed new dependencies.
11. SEC compliance/access plan.
12. On-chain source/API strategy.
13. Risks/blockers.
14. Recommended CP09 implementation scope.
15. Confirmation that no code implementation was performed.
16. Confirmation that no dependencies were installed.
17. Confirmation that no scheduled tasks were changed.
18. Confirmation that no commit or push was performed.
19. Awaiting PM Approval section.

## End condition

After saving the report, respond only with:

1. The report path.
2. A short summary.
3. Any blocker requiring PM attention.
4. A statement that you are awaiting PM approval before CP09.
