# Checkpoint Audit Trail

This directory maintains the persistent audit trail for the Insider Trading project implementation.

## Directory Structure

### `instructions/`

Contains PM-approved checkpoint instruction files. These are the directives issued by the PM/technical lead that authorize Claude Code to proceed with specific phases of work. Each file documents what was approved, any constraints, and decisions made.

### `reports/`

Contains Claude Code checkpoint reports. These are the deliverables produced by Claude Code at each checkpoint boundary, summarizing work completed, findings, risks, and items awaiting approval.

## Checkpoint Workflow

1. Claude Code produces a checkpoint report and saves it to `reports/`.
2. Roger passes the report to the PM/technical reviewer.
3. The PM reviews and issues approval (with any corrections) as an instruction file in `instructions/`.
4. Claude Code must NOT proceed beyond a checkpoint until PM approval is received.

## Security and Privacy

The following must NEVER be committed to this repository:

- `.env` files containing real credentials
- API keys, passwords, or tokens
- Log files or runtime outputs
- Database files (`.db`, `.sqlite`, `.sqlite3`)
- Private portfolio files (`config/portfolio_target.json`, `config/portfolio_current.json`)
- Any file containing personally identifiable information

Only `.example` files with placeholder values may be committed.

## Checkpoint History

| Checkpoint | Description                               | Status                         |
| ---------- | ----------------------------------------- | ------------------------------ |
| CP00       | Environment Inspection                    | Complete                       |
| CP01       | Implementation Plan                       | Complete                       |
| CP02       | Project Scaffold                          | Complete                       |
| CP03       | Agent Port                                | Complete                       |
| CP04       | Windows Install / Local Environment Setup | Complete                       |
| CP05       | Safe Runtime Smoke Tests                  | Complete                       |
| CP06       | Task Scheduler Activation                 | Complete                       |
| CP07       | Final Review / Commit / Push              | Complete                       |
