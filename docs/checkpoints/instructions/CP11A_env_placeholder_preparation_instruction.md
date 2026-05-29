# CP11A — Etherscan / SEC `.env` Placeholder Preparation Instruction

You are Claude Code acting as the implementation team for Roger Fiske’s `Insider-Trading` project under PM/Technical Lead supervision.

This checkpoint prepares the local environment placeholders needed before CP11 Maya runtime validation.

Do not run Maya yet. Do not run any agent. Do not commit or push.

## Current project path

```text
c:\Users\Minis\CascadeProjects\Insider-Trading
```

## CP11A goal

1. Add safe Etherscan and SEC placeholders to `.env.example`.
2. Add the same missing placeholder keys to the local `.env` file without filling in real values.
3. Preserve any existing real values already present in `.env`.
4. Do not print `.env` contents.
5. Stop and notify Roger exactly which fields he must fill in manually before CP11 runtime testing.

## Important credential policy

Do not store website passwords anywhere.

Do not add placeholders such as:

```text
ETHERSCAN_PASSWORD=
SEC_API_IO_PASSWORD=
PASSWORD=
```

Roger will manage website login credentials in his password manager.

The code should use API keys and SEC user-agent values, not website passwords.

## Required preconditions

Confirm these files exist:

```text
.env
.env.example
sources/etherscan.py
sources/sec_common.py
agents/maya.py
docs/checkpoints/reports/CP10_grounded_runtime_validation_commit_push_report.md
```

Confirm `.env` is ignored without printing contents:

```powershell
git check-ignore -v .env
```

If `.env` does not exist, create it from `.env.example` only after confirming `.env` is ignored by Git.

## Required `.env.example` placeholders

Update `.env.example` so it contains these sections and keys, without real secrets:

```env
# Anthropic
ANTHROPIC_API_KEY=

# SEC EDGAR official access
# Required for SEC.gov fair-access identification.
# Recommended format:
# SEC_USER_AGENT=Insider-Trading Roger Fiske contact-email@example.com
SEC_USER_AGENT=

# Optional third-party SEC API account reference / future integration
# These are not used by SEC.gov EDGAR official connectors unless code is later added.
SEC_API_IO_ACCOUNT_EMAIL=
SEC_API_IO_USERNAME=
SEC_API_IO_API_KEY=

# Etherscan account reference and API access
# Maya uses ETHERSCAN_API_KEY for API calls.
# Etherscan website username/email are optional local reference fields only.
ETHERSCAN_ACCOUNT_EMAIL=
ETHERSCAN_USERNAME=
ETHERSCAN_API_KEY=

# Safety
ROSS_DRY_RUN=true
```

## Required local `.env` update

Update local `.env` so that all keys above exist.

Rules:

1. Do not overwrite existing non-empty values.
2. Add missing keys with blank values.
3. Keep `ROSS_DRY_RUN=true`.
4. Do not print `.env`.
5. Do not stage `.env`.
6. Confirm `.env` remains ignored after editing.

## Required explanation for Roger

At the end of CP11A, clearly tell Roger:

1. `.env` placeholders are ready.
2. He must manually fill in:
   ```text
   ETHERSCAN_API_KEY
   SEC_USER_AGENT
   ```
3. Optional local account-reference fields:
   ```text
   ETHERSCAN_ACCOUNT_EMAIL
   ETHERSCAN_USERNAME
   SEC_API_IO_ACCOUNT_EMAIL
   SEC_API_IO_USERNAME
   SEC_API_IO_API_KEY
   ```
4. Do not enter website passwords into `.env`.
5. For `SEC_USER_AGENT`, use a descriptive value such as:
   ```text
   Insider-Trading Roger Fiske contact-email@example.com
   ```
6. Maya does not need a stock ticker for this checkpoint. Maya monitors on-chain token/wallet/transfer activity. If the current Maya connector requires token or wallet configuration, report exactly what is missing and propose CP11B configuration changes.

## Allowed documentation updates

You may update:

```text
README.md
docs/install_notes_windows.md
docs/source_grounding.md
```

Only to clarify:

1. Etherscan API key usage.
2. SEC user-agent usage.
3. No website passwords in `.env`.
4. Maya is on-chain oriented, not stock-ticker oriented.

## Prohibited actions

Do not:

1. Print `.env` contents.
2. Print real API keys.
3. Ask Roger to paste API keys into Claude Code chat.
4. Add password placeholders.
5. Run Maya or any agent.
6. Send email.
7. Send Telegram messages.
8. Modify scheduled tasks.
9. Commit files.
10. Push to GitHub.
11. Force-push.
12. Modify preserved source files in `docs/source/`.

## Validation commands

Run and report:

```powershell
git status --short
git check-ignore -v .env
git check-ignore -v .claude/
git check-ignore -v .venv/
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m py_compile sources/etherscan.py sources/sec_common.py agents/maya.py
```

Do not print `.env`.

## Required CP11A report

Save the report to:

```text
docs/checkpoints/reports/CP11A_env_placeholder_preparation_report.md
```

The report must include:

1. Summary of work completed.
2. Files created.
3. Files modified.
4. Confirmation `.env.example` was updated.
5. Confirmation local `.env` was updated without printing contents.
6. Confirmation existing `.env` values were not overwritten.
7. Confirmation no password placeholders were added.
8. Confirmation `.env` remains ignored.
9. Exact list of environment variable names Roger must fill in.
10. Explanation of what `SEC_USER_AGENT` should contain.
11. Explanation that Maya does not require a stock ticker for this checkpoint.
12. Any Maya configuration gap discovered.
13. Confirmation no agent was run.
14. Confirmation no scheduled tasks were changed.
15. Confirmation no commit or push was performed.
16. Awaiting PM Approval section.

## End condition

After saving the report, respond with:

1. Report path.
2. Short summary.
3. Exact `.env` keys Roger must fill in manually.
4. Confirmation that you are waiting for Roger to fill in `.env` before CP11 runtime testing.
