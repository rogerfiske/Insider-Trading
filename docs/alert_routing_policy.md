# Alert Routing Policy

**Status**: Design proposal (CP14)
**Implementation**: Deferred to CP15+

---

## Purpose

This document defines the alert routing policy for the Insider-Trading project, specifying when and how consensus events should be delivered via Telegram and/or email.

**Critical constraint**: All alerts are informational only. No alerts constitute trading advice or instructions. The human user makes all investment decisions.

---

## Current System Analysis

### Sophie (Consensus Analyst)

- **Input**: 7-day rolling window of scout signals from SQLite database
- **Logic**: Groups signals by (ticker, direction), deduplicates per scout, fires consensus when >= `SOPHIE_MIN_AGREE` scouts agree (default 3)
- **Output**: `ConsensusEvent` records with `dispatched=0` flag
- **No severity classification**: All consensus events treated identically

### Ross (Dispatcher)

- **Input**: All `ConsensusEvent` records where `dispatched=0`
- **Logic**:
  - Respects `ROSS_DRY_RUN` (default true, blocks all delivery)
  - Sends email (always required, fails if SMTP config missing)
  - Sends Telegram (optional, silent failure if not configured)
  - Marks `dispatched=1` only if email succeeds
- **No routing logic**: Cannot selectively route based on event properties
- **No deduplication**: Beyond the binary `dispatched` flag
- **No rate limiting**: Could send many alerts in one run

### Current Gaps

1. **No severity levels**: All consensus events are HIGH priority
2. **No routing flexibility**: Email is always required, Telegram is optional-only
3. **No channel-specific dry-run**: Cannot test Telegram without enabling email
4. **No deduplication across runs**: If Sophie fires same consensus twice, Ross will attempt dispatch twice
5. **No alert history**: No audit trail of when/what was sent
6. **No rate limiting**: No protection against alert spam
7. **Email-centric**: Email failure blocks marking `dispatched`, Telegram failure does not

---

## Proposed Severity Levels

### INFO

**Description**: Informational signals that do not warrant immediate human review.

**Examples**:
- Single low-confidence scout signal
- Source fetch error (e.g., Etherscan NOTOK, SEC 403)
- No-consensus result from Sophie
- Janet portfolio drift below threshold

**Default routing**: LOG_ONLY

### WATCH

**Description**: Potentially interesting signals that warrant passive monitoring but not immediate action.

**Examples**:
- 2 scouts agree on symbol/direction (below consensus threshold)
- Consensus with low aggregate confidence (e.g., all scouts conf=2)
- Janet portfolio drift between 3-5%
- Maya on-chain activity above $5M but below $10M

**Default routing**: TELEGRAM_ONLY

### ACTIONABLE

**Description**: Multi-scout consensus events that warrant human review within 24 hours.

**Examples**:
- 3+ scouts agree (consensus threshold met)
- Aggregate confidence >= 10 (e.g., three scouts at conf=3+)
- Evidence-backed source links available
- No duplicate alert within 24 hours

**Default routing**: TELEGRAM_AND_EMAIL

### URGENT

**Description**: High-confidence consensus with multiple corroborating signals warranting immediate human review.

**Examples**:
- 4+ scouts agree on same direction
- Aggregate confidence >= 15
- Janet portfolio drift >= 7%
- Maya on-chain whale transfer >= $20M
- Repeated corroborating evidence within window

**Default routing**: TELEGRAM_AND_EMAIL (with "URGENT" prefix)

---

## Proposed Alert Classes

### LOG_ONLY

**Behavior**:
- Log event to `.state/logs/ross.log`
- Write to SQLite with alert_delivered=0
- No Telegram message
- No email
- Mark as dispatched immediately

**Use case**: INFO severity, source errors, no-consensus results

### TELEGRAM_ONLY

**Behavior**:
- Send Telegram message (if configured and enabled)
- Log event
- No email
- Mark as dispatched after Telegram send (or immediately if Telegram not configured)

**Use case**: WATCH severity, low-priority signals

### EMAIL_ONLY

**Behavior**:
- Send email (if configured and enabled)
- Log event
- No Telegram message
- Mark as dispatched after email send

**Use case**: Historical audit trail, weekly digests (future)

### TELEGRAM_AND_EMAIL

**Behavior**:
- Send Telegram message (if configured and enabled)
- Send email (if configured and enabled)
- Log event
- Mark as dispatched after both succeed (or after available channels succeed)

**Use case**: ACTIONABLE and URGENT severity

### SUPPRESS_DUPLICATE

**Behavior**:
- Check deduplication cache
- If duplicate detected, log suppression and mark dispatched immediately
- If not duplicate, route according to severity

**Use case**: Prevent repeated alerts for same consensus event

---

## Proposed Routing Policy

```
Severity → Alert Class Mapping:

INFO       → LOG_ONLY
WATCH      → TELEGRAM_ONLY
ACTIONABLE → TELEGRAM_AND_EMAIL (with deduplication)
URGENT     → TELEGRAM_AND_EMAIL (always send, no dedup suppression)
```

### Severity Calculation

Consensus events will be assigned severity based on:

1. **Scout count**:
   - 2 scouts: WATCH
   - 3 scouts: ACTIONABLE
   - 4+ scouts: URGENT

2. **Aggregate confidence** (sum of all agreeing scouts' confidence scores):
   - < 8: INFO
   - 8-11: WATCH
   - 12-14: ACTIONABLE
   - >= 15: URGENT

3. **Override rules**:
   - Janet drift >= 7%: URGENT
   - Maya transfer >= $20M: URGENT
   - Duplicate within 24h: Downgrade one level (unless URGENT)

**Final severity**: Take the maximum of all calculated severities.

---

## Deduplication Strategy

### Deduplication Key

Consensus events are considered duplicates if they match on:

```python
dedup_key = (ticker, direction, time_bucket)
```

Where `time_bucket` = floor(timestamp / DEDUP_HOURS) * DEDUP_HOURS

**Example**: With `DEDUP_HOURS=24`:
- Consensus at 2026-05-29 10:15 UTC → bucket = 2026-05-29 00:00 UTC
- Consensus at 2026-05-29 22:30 UTC → bucket = 2026-05-29 00:00 UTC
- Both have same dedup_key → second is suppressed

### Deduplication Storage

**Option A**: Extend SQLite `consensus` table with dedup fields:

```sql
ALTER TABLE consensus ADD COLUMN dedup_key TEXT;
ALTER TABLE consensus ADD COLUMN alert_severity TEXT;
ALTER TABLE consensus ADD COLUMN alert_channels TEXT;
CREATE INDEX idx_consensus_dedup ON consensus(dedup_key, ts DESC);
```

**Option B**: Separate `alert_history` table:

```sql
CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consensus_id INTEGER NOT NULL,
    dedup_key TEXT NOT NULL,
    severity TEXT NOT NULL,
    channels TEXT NOT NULL,  -- JSON array: ["email", "telegram"]
    delivered_at TEXT NOT NULL,
    FOREIGN KEY (consensus_id) REFERENCES consensus(id)
);
CREATE INDEX idx_alert_history_dedup ON alert_history(dedup_key, delivered_at DESC);
```

**Recommendation**: Option B (separate table) for cleaner separation of concerns and better audit history.

### Deduplication Logic

```python
def is_duplicate(ticker: str, direction: str, timestamp: datetime, dedup_hours: int) -> bool:
    """Check if a similar alert was sent within the dedup window."""
    bucket_seconds = dedup_hours * 3600
    bucket_ts = int(timestamp.timestamp() / bucket_seconds) * bucket_seconds
    bucket_dt = datetime.fromtimestamp(bucket_ts, tz=timezone.utc)
    dedup_key = f"{ticker}:{direction}:{bucket_dt.isoformat()}"

    # Check if we've sent an alert with this dedup_key in the past dedup_hours
    cutoff = timestamp - timedelta(hours=dedup_hours)
    with _conn() as c:
        row = c.execute(
            "SELECT id FROM alert_history "
            "WHERE dedup_key = ? AND delivered_at >= ? "
            "LIMIT 1",
            (dedup_key, cutoff.isoformat())
        ).fetchone()
    return row is not None
```

---

## Channel-Specific Enablement

### Independent Control

Allow Telegram and email to be independently enabled:

```env
ROSS_DRY_RUN=true              # Master kill switch (overrides all channels)
ALERT_ENABLE_TELEGRAM=false    # Telegram-specific enable
ALERT_ENABLE_EMAIL=false       # Email-specific enable
```

**Logic**:

```python
def should_send_telegram(dry_run: bool, telegram_enabled: bool, telegram_configured: bool) -> bool:
    return not dry_run and telegram_enabled and telegram_configured

def should_send_email(dry_run: bool, email_enabled: bool, smtp_configured: bool) -> bool:
    return not dry_run and email_enabled and smtp_configured
```

### Phased Enablement

Recommended transition path:

1. **CP15**: Implement policy and deduplication, keep both channels disabled (`ROSS_DRY_RUN=true`)
2. **CP16**: Enable Telegram only for one controlled test (`ALERT_ENABLE_TELEGRAM=true`, `ALERT_ENABLE_EMAIL=false`)
3. **CP17**: Enable both channels for one controlled test (`ALERT_ENABLE_TELEGRAM=true`, `ALERT_ENABLE_EMAIL=true`)
4. **CP18**: Enable both channels for production (`ROSS_DRY_RUN=false`)

---

## Rate Limiting

### Max Alerts Per Run

Prevent alert spam by limiting alerts per Ross execution:

```env
ALERT_MAX_PER_RUN=3
```

**Logic**:
- Ross processes pending consensus events in order (oldest first)
- Stops after sending `ALERT_MAX_PER_RUN` alerts
- Remaining events stay in pending queue for next run
- URGENT alerts always count toward limit but are never skipped

### Alert Frequency

Minimum time between Ross runs: 30 minutes (current Task Scheduler setting)

**Worst case**: 3 alerts/run * 2 runs/hour = 6 alerts/hour max

---

## Audit and History

### Alert History Table

Track all alert attempts (success or failure):

```sql
CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consensus_id INTEGER NOT NULL,
    dedup_key TEXT NOT NULL,
    severity TEXT NOT NULL,
    channels TEXT NOT NULL,          -- JSON: ["email", "telegram"]
    email_status TEXT,               -- "sent", "failed", "skipped", "disabled"
    telegram_status TEXT,            -- "sent", "failed", "skipped", "disabled"
    error_message TEXT,
    delivered_at TEXT NOT NULL,
    FOREIGN KEY (consensus_id) REFERENCES consensus(id)
);
```

### Log Entries

Ross logs will include:

```
YYYY-MM-DDTHH:MM:SS [ross] CONSENSUS [123] ACTIONABLE AAPL BULLISH (3 scouts)
YYYY-MM-DDTHH:MM:SS [ross] → Email: sent
YYYY-MM-DDTHH:MM:SS [ross] → Telegram: sent
YYYY-MM-DDTHH:MM:SS [ross] → Marked dispatched
```

---

## Configuration Variables

### Proposed .env.example Additions

```env
# -- ALERT ROUTING (CP15+) -----------------------------------------------------

# Master dry-run control. Set to false to enable live alerts.
# Overrides all channel-specific enables.
ROSS_DRY_RUN=true

# Channel-specific enable flags (only active when ROSS_DRY_RUN=false)
ALERT_ENABLE_TELEGRAM=false
ALERT_ENABLE_EMAIL=false

# Minimum severity to dispatch (INFO|WATCH|ACTIONABLE|URGENT)
# Events below this level are logged only.
ALERT_MIN_SEVERITY=ACTIONABLE

# Deduplication window in hours
# Suppress alerts for same ticker+direction within this window.
ALERT_DEDUP_HOURS=24

# Maximum alerts per Ross run (prevent spam)
ALERT_MAX_PER_RUN=3

# Require human review flag (future: pause until acknowledged)
ALERT_REQUIRE_HUMAN_REVIEW=false
```

---

## Implementation Phases

### CP15: Alert Policy Implementation (Dry-Run)

**Scope**:
- Add `alert_history` table to SQLite schema
- Implement severity calculation in Sophie or Ross
- Implement deduplication logic
- Implement routing policy (LOG_ONLY, TELEGRAM_ONLY, etc.)
- Add configuration variables to `.env.example`
- Keep `ROSS_DRY_RUN=true` and both channel enables `false`
- Add unit tests for severity calculation and deduplication

**Validation**:
- Run Sophie/Ross in dry-run mode
- Verify routing policy logic via logs
- Verify deduplication logic via SQLite queries
- No real alerts sent

### CP16: Controlled Telegram-Only Test

**Scope**:
- Keep `ROSS_DRY_RUN=true`
- Set `ALERT_ENABLE_TELEGRAM=true`, `ALERT_ENABLE_EMAIL=false`
- Simulate one ACTIONABLE consensus event (via manual DB insert or controlled scout run)
- Send exactly one Telegram message
- Verify alert_history record created
- Verify deduplication prevents second send

### CP17: Controlled Full Channel Test

**Scope**:
- Keep `ROSS_DRY_RUN=true`
- Set `ALERT_ENABLE_TELEGRAM=true`, `ALERT_ENABLE_EMAIL=true`
- Simulate one ACTIONABLE consensus event
- Send one Telegram message + one email
- Verify alert_history records
- Verify deduplication

### CP18: Live Production Enablement

**Scope**:
- Set `ROSS_DRY_RUN=false`
- Keep both channel enables `true`
- Monitor first 24 hours of live alerts
- Establish rollback procedure (set `ROSS_DRY_RUN=true`)

---

## Neutral Language Guidelines

All alert messages must use informational language, not trading instructions:

**Allowed**:
- "Consensus detected: AAPL BULLISH (3 scouts)"
- "Human review recommended"
- "Portfolio drift observed: +6.5%"
- "On-chain activity observed: $12M transfer"
- "Review candidate: TSLA"

**Prohibited**:
- "BUY AAPL"
- "SELL TSLA"
- "Strong buy signal"
- "Immediate action required"
- "Trade recommendation"

**Current language** (from `render_consensus`):
```
"This is informational, not a trade instruction. Ross did not
place a trade. The decision is yours."
```

This disclaimer should remain in all ACTIONABLE and URGENT alerts.

---

## Risks and Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Alert spam | MEDIUM | Rate limiting (max 3/run), deduplication (24h window) |
| Duplicate alerts | MEDIUM | Deduplication key + alert_history table |
| Missing critical alerts | LOW | URGENT severity bypasses some dedup rules |
| Channel failure blocking dispatch | LOW | Independent channel enables, mark dispatched if any channel succeeds |
| False positives | LOW | Conservative `ALERT_MIN_SEVERITY=ACTIONABLE` default |
| Regulatory misunderstanding | LOW | Prominent "not trading advice" disclaimer in all alerts |

---

## Summary

This policy provides:

1. **Four severity levels** (INFO, WATCH, ACTIONABLE, URGENT) based on scout count and confidence
2. **Five alert classes** (LOG_ONLY, TELEGRAM_ONLY, EMAIL_ONLY, TELEGRAM_AND_EMAIL, SUPPRESS_DUPLICATE) for flexible routing
3. **Deduplication** via time-bucketed keys and alert_history table
4. **Independent channel control** (Telegram and email can be separately enabled)
5. **Rate limiting** (max 3 alerts per run)
6. **Audit trail** (alert_history table tracks all delivery attempts)
7. **Conservative transition path** (CP15 → CP16 → CP17 → CP18)

**Next step**: PM approval, then CP15 implementation (still in dry-run mode).
