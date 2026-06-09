# Production Dual-Channel Pilot Plan

**Date**: 2026-06-09
**Checkpoint**: CP22D
**Status**: PENDING ACTIVATION

## Executive Summary

This plan outlines a conservative production dual-channel pilot for the Insider-Trading alert system, enabling both Telegram and email delivery for high-severity consensus events.

**Pilot Scope**: Limited production deployment with maximum safety constraints
- **Duration**: Pilot phase (ongoing monitoring until CP22E review)
- **Channels**: Telegram (already enabled) + Email (activation pending)
- **Severity**: ACTIONABLE and URGENT only
- **Volume**: Maximum 1 alert per Ross run
- **Deduplication**: 24-hour window
- **Reversibility**: Instant rollback via `.env` change

## Current Status

### Pre-Activation Posture

**Verified Configuration** (via `safe_env_check.py`):

```text
ALERT_ENABLE_EMAIL: False (production email currently disabled)
ALERT_ENABLE_TELEGRAM: True (Telegram enabled and operational)
SMTP credentials: Present
Telegram credentials: Present
Recipient: fiske1945@4securemail.com (Roger's test address)
```

**Scheduled Tasks**: All tasks in "Ready" state (not running)

**System State**:
- Ross dry-run: Disabled (ROSS_DRY_RUN=false)
- Minimum severity: ACTIONABLE
- Max alerts per run: 1
- Dedup window: 24 hours
- Daily guard: Active
- Manual ticker/watchlist workflows: Isolated (no-alert mode)

## Why CP22D Is Approved

### CP22B — Email Delivery Confirmed

- Controlled test email sent successfully at 2026-06-09 20:33:18 UTC
- Roger confirmed receipt at fiske1945@4securemail.com
- Email formatting professional and readable
- SMTP authentication successful (4SecureMail provider)
- No delivery failures

### CP22C — Dual-Channel Verification Complete

- Controlled test completed at 2026-06-09 20:46:43 UTC
- Email delivered successfully ✅
- Telegram delivered successfully ✅
- Roger confirmed receipt of both messages at 1:46 PM local time
- Same timestamp coordination verified
- All CP22C test markers present in both channels
- Script bug identified and fixed (Telegram API returns bool, not dict)
- No retry needed — both channels operational

### Production Readiness Confirmed

✅ Email channel verified operational (CP22B + CP22C)
✅ Telegram channel verified operational (CP16 + CP22C)
✅ Dual-channel coordination verified (CP22C)
✅ Routing policy tested (CP14 + CP15)
✅ Deduplication functional (CP12)
✅ Daily guard active (CP11)
✅ Alert history tracking operational
✅ Ross production execution tested

## Exact Pilot Settings

### What Will Change

```text
ALERT_ENABLE_EMAIL: false → true
```

**Single change only**. No other `.env` values will be modified.

### What Will NOT Change

The following settings remain fixed during the pilot:

| Setting | Value | Purpose |
|---------|-------|---------|
| `ALERT_ENABLE_TELEGRAM` | `true` | Telegram remains enabled |
| `ALERT_MIN_SEVERITY` | `ACTIONABLE` | No low-severity alerts |
| `ALERT_MAX_PER_RUN` | `1` | Conservative volume limit |
| `ALERT_DEDUP_HOURS` | `24` | Prevent duplicate spam |
| `ROSS_DRY_RUN` | `false` | Production execution (already set) |

**Scheduled Tasks**: No modification to task cadence or triggers
**Manual Workflows**: Remain isolated from production alerts
**Watchlist Tracking**: No-alert mode continues

## Activation Steps

### Pre-Activation Checklist

Before making the `.env` change:

- [x] All CP22D precondition files exist
- [x] `.env` and `.state` paths gitignored
- [x] No scheduled tasks actively running
- [x] Routing and Ross behavior reviewed
- [x] Pre-activation safe environment check complete
- [x] Production dual-channel pilot plan created
- [x] CP22D checkpoint report section complete
- [ ] All readiness gates pass (pending)
- [ ] PM approval to proceed (pending)

### Activation Procedure

1. **Verify current state** with `safe_env_check.py`
   - Confirm `ALERT_ENABLE_EMAIL=false`
   - Confirm all SMTP credentials present

2. **Edit `.env` file locally**
   - Change `ALERT_ENABLE_EMAIL=false` to `ALERT_ENABLE_EMAIL=true`
   - **Do not change any other value**
   - **Do not commit `.env`**

3. **Verify activation** with `safe_env_check.py`
   - Confirm `ALERT_ENABLE_EMAIL=true`
   - Confirm `ALERT_ENABLE_TELEGRAM=true`
   - Confirm both channel credentials present

4. **Document activation** in CP22D checkpoint report

## Validation Steps

### Immediate Post-Activation

Run validation checks (do not send messages or trigger tasks):

```powershell
# Verify environment configuration
.\.venv\Scripts\python.exe .\scripts\safe_env_check.py

# Verify Python modules compile
.\.venv\Scripts\python.exe -m py_compile alerts/routing.py alerts/history.py agents/ross.py

# Run test suite
.\.venv\Scripts\python.exe -m pytest -q

# Secret scan (before any commit)
# Verify no secrets in trackable files
```

### First Production Alert Validation

After the next scheduled Ross run (morning startup):

1. **Check Telegram**
   - Verify message received (if any consensus event triggered)
   - Confirm message formatting correct
   - Confirm timestamp reasonable

2. **Check Email**
   - Verify message received at fiske1945@4securemail.com
   - Confirm same alert as Telegram (dual-channel coordination)
   - Confirm formatting professional
   - Confirm no delivery failures

3. **Verify Deduplication**
   - Subsequent Ross runs should not repeat same alert within 24 hours
   - Alert history database should show correct dedup tracking

4. **Confirm Volume Limit**
   - Maximum 1 alert per Ross run enforced
   - No alert spam

## Monitoring Steps

### Continuous Monitoring

Monitor the following after activation:

**Daily**:
- Check Telegram for any new alerts
- Check email inbox for corresponding alerts
- Verify dual-channel coordination (same alerts on both channels)
- Check for any duplicate alerts
- Monitor alert volume (should be ≤1 per Ross run)

**Weekly**:
- Review alert history database
- Verify deduplication window working correctly
- Check for any SMTP authentication failures
- Review email deliverability metrics

**Stop Conditions** (see below) trigger immediate rollback.

### Alert History Queries

Use `scripts/query_alert_history.py` to inspect routing decisions and sent alerts:

```powershell
# Check recent alerts
.\.venv\Scripts\python.exe .\scripts\query_alert_history.py --recent 7

# Check specific ticker
.\.venv\Scripts\python.exe .\scripts\query_alert_history.py --ticker NVDA
```

## Rollback Steps

### Instant Rollback Procedure

If any stop condition is met, execute immediately:

1. **Disable production email**
   ```text
   Edit .env:
   ALERT_ENABLE_EMAIL=true → ALERT_ENABLE_EMAIL=false
   ```

2. **Verify rollback**
   ```powershell
   .\.venv\Scripts\python.exe .\scripts\safe_env_check.py
   ```
   Confirm: `ALERT_ENABLE_EMAIL enabled: False`

3. **Document rollback** in CP22D-Rollback checkpoint report

4. **Report to PM** with rollback reason and evidence

**Rollback Time**: < 1 minute
**Scheduled Tasks**: No modification needed (rollback is `.env` change only)
**Telegram**: Remains enabled (Telegram-only mode resumes)

## Stop Conditions

Execute rollback immediately if any of the following occur:

### Critical Stop Conditions (Immediate Rollback)

1. **Duplicate Alerts**
   - Same alert sent multiple times within dedup window
   - Deduplication logic failing
   - Alert spam to Roger

2. **Email Deliverability Issues**
   - SMTP authentication failures
   - Email delivery failures
   - Emails marked as spam
   - Email formatting broken

3. **Secret Exposure**
   - Any secret printed to logs
   - Any credential exposed in error messages
   - `.env` accidentally committed

4. **Unexpected Alert Volume**
   - More than 1 alert per Ross run
   - `ALERT_MAX_PER_RUN` not enforced
   - Alert flooding

### High Priority Stop Conditions (Investigate, Consider Rollback)

5. **Channel Coordination Failure**
   - Telegram sent but email not sent (or vice versa) for ACTIONABLE/URGENT
   - Inconsistent message content between channels
   - Timing mismatch suggesting delivery issues

6. **Severity Policy Violation**
   - INFO or WATCH alerts sent via email
   - `ALERT_MIN_SEVERITY` not enforced

7. **Manual Workflow Contamination**
   - Manual ticker research triggering production alerts
   - Watchlist workflow sending alerts

8. **Scheduled Task Issues**
   - Task modification detected
   - Unexpected task triggers
   - Task execution failures

## Roger Confirmation Steps

### After First Production Dual-Channel Alert

Roger must confirm:

1. **Alert Receipt**
   - Received Telegram message? Yes/No
   - Received email message? Yes/No
   - Same alert on both channels? Yes/No

2. **Alert Quality**
   - Telegram formatting acceptable? Yes/No
   - Email formatting acceptable? Yes/No
   - Timestamp reasonable? Yes/No
   - Severity assignment correct? Yes/No

3. **Alert Usefulness**
   - Was the alert actionable? Yes/No
   - Was it a duplicate (within 24 hours)? Yes/No
   - Was the ticker/direction correct? Yes/No

4. **Overall Assessment**
   - Continue pilot? Yes/No/Defer
   - Any issues observed?
   - Recommended adjustments?

Roger's confirmation triggers CP22E checkpoint for pilot monitoring and assessment.

## Safety Guarantees

### Channel Independence

- SMTP failure does NOT block Telegram delivery
- Telegram failure does NOT block email delivery (if configured)
- Routing logic handles channel failures gracefully
- Each channel records delivery status independently

### Deduplication Per Alert

- Dedup key format: `{ticker}:{direction}:{date}`
- 24-hour dedup window enforced
- Alert history database tracks all routing decisions
- Duplicate alerts suppressed with `AlertClass.SUPPRESS_DUPLICATE`

### Manual Workflow Isolation

All manual ticker research and watchlist workflows remain isolated:

- `scripts/manual_ticker_research.py`: Forces dry-run, no alerts
- `scripts/query_watchlist.py`: Forces dry-run, no alerts
- `agents/maia.py`: Not connected to Ross production execution
- Watchlist tracking: No-alert mode enforced

### Scheduled Task Integrity

- No scheduled task modifications during CP22D
- Task cadence unchanged
- Task triggers unchanged
- Ross scheduled execution continues as configured

## Informational-Only Disclaimer

**IMPORTANT**: All Insider-Trading alerts are informational only and do not constitute investment advice.

- Roger must perform independent research before any trade
- Alerts are experimental and may contain errors
- No guarantee of profitability or accuracy
- Roger accepts full responsibility for all trading decisions
- SEC regulations on insider trading remain in effect

## Next Steps After Activation

1. **Wait for next scheduled Ross run** (morning startup)
2. **Monitor Telegram and email** for first production dual-channel alert
3. **Confirm dual-channel coordination** (same alert on both channels)
4. **Report results** to PM
5. **Proceed to CP22E** for production pilot monitoring and assessment

## Revision History

| Date | Version | Change |
|------|---------|--------|
| 2026-06-09 | 1.0 | Initial production dual-channel pilot plan created for CP22D |

---

**Plan Status**: PENDING ACTIVATION
**Awaiting**: All readiness gates pass + PM approval
**Prepared by**: CP22D Implementation Team
**Reviewed by**: Pending PM review
