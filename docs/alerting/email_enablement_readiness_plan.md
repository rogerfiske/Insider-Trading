# Email Enablement Readiness Plan

**Created**: 2026-06-09
**Checkpoint**: CP22
**Status**: READINESS REVIEW — Email remains disabled

---

## 1. Current Status

### Alerting Infrastructure

**Completed and Validated**:
- ✅ Generic SMTP implementation (CP13B) supporting any SMTP provider including 4SecureMail
- ✅ Alert routing policy (CP14/CP15) with severity levels and channel routing
- ✅ Telegram-only production pilot (CP19/CP20) running successfully on scheduled tasks
- ✅ Dual-channel test validation (CP17) confirmed both Telegram and email delivery work
- ✅ Deduplication system (24-hour time-bucketed)
- ✅ Rate limiting (ALERT_MAX_PER_RUN)
- ✅ Minimum severity filtering (ALERT_MIN_SEVERITY)
- ✅ Dry-run mode enforcement
- ✅ Audit history storage

**Current Production Pilot Posture** (as of CP20/CP20D):
```env
ROSS_DRY_RUN=false                  # Live Telegram delivery enabled
ALERT_ENABLE_TELEGRAM=true          # Telegram channel enabled
ALERT_ENABLE_EMAIL=false            # Email channel DISABLED
ALERT_MIN_SEVERITY=ACTIONABLE       # Only actionable/urgent alerts
ALERT_MAX_PER_RUN=1                 # Maximum 1 alert per run
ALERT_DEDUP_HOURS=24                # 24-hour deduplication window
```

### What Remains Disabled

- ❌ **Email delivery**: `ALERT_ENABLE_EMAIL=false` in production `.env`
- ❌ **Dual-channel routing**: Only Telegram is active
- ❌ **Manual watchlist alerting**: Manual ticker research is isolated from live alerts (dry-run forced)

---

## 2. What Has Already Been Validated

### SMTP Implementation (CP13B)
- Generic SMTP email delivery works with 4SecureMail (mail.4securemail.com)
- Secrets are read from `.env` only, never logged or printed
- Password redaction in error messages works
- Email body format includes ticker, direction, scout count, confidence
- Email subject format is clear: "ROSS Alert: {TICKER} {DIRECTION}"
- SMTP failures degrade gracefully (return error without crashing)
- Controlled test email successfully delivered to fiske1945@4securemail.com

### Alert Routing (CP14/CP15)
- Severity calculation works correctly (INFO, WATCH, ACTIONABLE, URGENT)
- Alert class routing works:
  - INFO → LOG_ONLY
  - WATCH → TELEGRAM_ONLY (if enabled)
  - ACTIONABLE → TELEGRAM_AND_EMAIL (if enabled)
  - URGENT → TELEGRAM_AND_EMAIL (if enabled)
- Duplicate suppression works (24-hour deduplication window)
- Rate limiting works (ALERT_MAX_PER_RUN)
- Minimum severity filtering works
- Channel enablement flags work independently:
  - `ALERT_ENABLE_TELEGRAM` can be true while `ALERT_ENABLE_EMAIL` is false
  - `ALERT_ENABLE_EMAIL` can be true while `ALERT_ENABLE_TELEGRAM` is false
  - Both can be true (dual-channel)
  - Both can be false (log-only)

### Dual-Channel Test (CP17)
- Controlled test confirmed both Telegram and email can send for same event
- ACTIONABLE consensus event sent one Telegram message and one email
- Both messages contained same evidence (ticker, direction, scout count, confidence)
- No duplicate alert suppression between channels (correct behavior — one event = one Telegram + one email)

### Telegram Production Pilot (CP19/CP20/CP20D)
- Scheduled tasks run 7x daily (agents: eddie, maggie, frank, maya, janet, sophie, ross)
- Morning startup schedule (6:30 AM user logon trigger) validated
- Ross daily production guard prevents excessive alerts
- Telegram-only alerts working reliably
- No false positives or spam
- Deduplication and rate limiting working correctly

### Manual Watchlist Isolation (CP21G-CP21J)
- Manual ticker research workflow (`ticker_watchlist.py`) explicitly sets:
  ```python
  os.environ["ROSS_DRY_RUN"] = "true"
  os.environ["ALERT_ENABLE_TELEGRAM"] = "false"
  os.environ["ALERT_ENABLE_EMAIL"] = "false"
  ```
- Manual watchlist scores (0-100 insider evidence scoring) are report-only
- No code path connects manual watchlist to live alerting
- Dry-run mode is forced for all manual ticker research

---

## 3. Recommended Staged Rollout

### CP22 (Current) — Readiness Review Only
**Status**: COMPLETED
**Actions**: Document current state, create readiness plan, no live changes
**Outcome**: This document

### CP22A — Email Render Dry-Run Test (Recommended Next)
**Goal**: Validate email body rendering without sending live email
**Actions**:
- Create a helper script that renders email body for a mock ACTIONABLE event
- Verify evidence context is complete (ticker, direction, scouts, confidence, reasons)
- Verify subject line format
- Verify body format is clear and actionable
- No live email send (render to console/file only)

**Success Criteria**:
- Email body contains all necessary evidence
- Subject line is clear and not spammy
- Body format is readable and concise
- No secrets in rendered output
- Dry-run mode enforced

### CP22B — Controlled Single Live Email Test (Roger Only)
**Goal**: Send one controlled live email to Roger only, validate delivery
**Actions**:
- Temporarily set `ALERT_ENABLE_EMAIL=true` in a test script (not `.env`)
- Create a mock ACTIONABLE consensus event (e.g., NVDA BULLISH with 3 scouts)
- Send one email to `ALERT_EMAIL_TO` (Roger's 4SecureMail address)
- Verify email delivered successfully
- Verify email body contains expected evidence
- Verify no Telegram sent (Telegram disabled for this test)
- Restore `ALERT_ENABLE_EMAIL=false` after test

**Success Criteria**:
- Email delivered to Roger's inbox
- Email not marked as spam
- Email body is clear and actionable
- Subject line is professional
- No errors or exceptions
- Test is reversible (no production impact)

### CP22C — Controlled Dual-Channel Test (Roger Only)
**Goal**: Validate Telegram + email dual-channel for same event
**Actions**:
- Temporarily set both `ALERT_ENABLE_TELEGRAM=true` and `ALERT_ENABLE_EMAIL=true` in a test script
- Create a mock ACTIONABLE consensus event
- Send one Telegram and one email for the same event
- Verify both delivered
- Verify no duplicate suppression between channels (correct behavior)
- Restore production settings after test

**Success Criteria**:
- Both Telegram and email delivered for same event
- No cross-channel duplicate suppression
- Both messages contain same evidence
- Test is reversible

### CP22D — Production Dual-Channel Pilot (1 Alert/Run Max)
**Goal**: Enable email in production with maximum safety constraints
**Actions**:
- Update production `.env`:
  ```env
  ALERT_ENABLE_EMAIL=true          # Enable email channel
  ALERT_ENABLE_TELEGRAM=true       # Keep Telegram enabled
  ALERT_MIN_SEVERITY=ACTIONABLE    # Only actionable/urgent
  ALERT_MAX_PER_RUN=1              # Maximum 1 alert per run
  ALERT_DEDUP_HOURS=24             # 24-hour dedup
  ```
- Monitor for 7 days (1 week pilot)
- Track:
  - Total email sent
  - Email deliverability
  - Duplicate notifications
  - User feedback (Roger)
  - SMTP errors or failures

**Success Criteria**:
- Email deliverability ≥ 95%
- No duplicate notifications within 24-hour window
- No spam complaints
- No SMTP auth failures
- User feedback is positive (actionable alerts, not noisy)

### CP22E — Production Decision / Rollback Criteria
**Goal**: Decide whether to keep email enabled or roll back
**Actions**:
- Review 7-day pilot metrics
- Decide: keep email enabled, adjust settings, or roll back to Telegram-only

**Keep Email Enabled If**:
- Email deliverability ≥ 95%
- No duplicate notification issues
- User feedback positive
- No SMTP reliability issues

**Roll Back to Telegram-Only If**:
- Email deliverability < 90%
- Duplicate notifications occur
- User reports email is too noisy
- SMTP reliability issues
- User prefers Telegram-only

**Rollback Procedure**:
- Update production `.env`: `ALERT_ENABLE_EMAIL=false`
- Restart scheduled tasks (or wait for next scheduled run)
- Email delivery stops immediately
- Telegram delivery continues

---

## 4. Preconditions for Enabling Email

Before enabling `ALERT_ENABLE_EMAIL=true` in production `.env`:

1. ✅ **SMTP credentials configured** in `.env`:
   - SMTP_HOST=mail.4securemail.com
   - SMTP_PORT=465
   - SMTP_USE_SSL=true
   - SMTP_USERNAME=fiske1945@4securemail.com
   - SMTP_PASSWORD=[configured, not printed]
   - ALERT_EMAIL_FROM=fiske1945@4securemail.com
   - ALERT_EMAIL_TO=fiske1945@4securemail.com

2. ✅ **Alert routing policy validated**:
   - ALERT_MIN_SEVERITY=ACTIONABLE (only actionable/urgent alerts)
   - ALERT_MAX_PER_RUN=1 (rate limiting)
   - ALERT_DEDUP_HOURS=24 (duplicate suppression)

3. ✅ **Email implementation validated** (CP13B/CP17):
   - Generic SMTP works
   - Email body contains evidence
   - Secrets never logged
   - SMTP failures degrade gracefully

4. ✅ **Telegram pilot stable** (CP19/CP20):
   - Scheduled tasks running reliably
   - Ross daily production guard working
   - No false positives or spam

5. ✅ **Manual watchlist isolated** (CP21G-CP21J):
   - Manual ticker research forces dry-run mode
   - No connection to live alerting

6. ✅ **Rollback path known**:
   - Set `ALERT_ENABLE_EMAIL=false`
   - Restart tasks or wait for next run
   - Email stops, Telegram continues

7. ⚠️ **Pending**: Controlled email render dry-run (CP22A)
8. ⚠️ **Pending**: Controlled single live email test (CP22B)
9. ⚠️ **Pending**: Controlled dual-channel test (CP22C)

---

## 5. Safety Constraints

### Never Enable Email For
- ❌ Manual ticker research (`ticker_watchlist.py` forces dry-run)
- ❌ Ticker drilldown (`ticker_drilldown.py` is read-only research)
- ❌ Test scripts (use dry-run mode or temporary flag)

### Always Enforce
- ✅ ALERT_MIN_SEVERITY=ACTIONABLE (minimum)
- ✅ ALERT_MAX_PER_RUN=1 (during pilot)
- ✅ ALERT_DEDUP_HOURS=24 (minimum)
- ✅ Ross daily production guard active
- ✅ Secrets read from `.env` only, never logged

### Email-Specific Safety
- ✅ SMTP failures degrade gracefully (do not block Telegram)
- ✅ Email body contains evidence, not just ticker symbol
- ✅ Subject line is professional, not spammy
- ✅ Password redaction in error messages

---

## 6. Rollback Procedure

If email delivery must be disabled:

1. **Immediate Rollback**:
   ```powershell
   # Edit .env
   ALERT_ENABLE_EMAIL=false
   ```

2. **Restart Scheduled Tasks** (optional — tasks pick up new .env on next run):
   ```powershell
   Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Restart-ScheduledTask
   ```

3. **Verify Email Stopped**:
   - Check alert history database
   - Confirm no new email send attempts
   - Telegram continues working

4. **Root Cause Analysis**:
   - Review alert history for failed email sends
   - Check SMTP error messages
   - Review user feedback
   - Document reason for rollback

5. **Re-enablement Criteria**:
   - Root cause identified and fixed
   - User approval to re-enable
   - New controlled test (CP22B or CP22C)

---

## 7. Evidence Included in Email

Email body format (from CP13B/CP17 validation):

```
Subject: ROSS Alert: {TICKER} {DIRECTION}

Body:
ROSS Alert: Insider consensus detected

Ticker: {TICKER}
Direction: {DIRECTION}
Severity: {SEVERITY}
Scout Count: {N} scouts agree
Aggregate Confidence: {CONFIDENCE}

Agreeing Scouts:
- {SCOUT_NAME}: {REASON}
- {SCOUT_NAME}: {REASON}
...

This is an automated alert for informational purposes only.
Not financial advice.

Timestamp: {ISO_TIMESTAMP}
```

**Evidence Context** (confirmed present in CP17 test):
- Ticker symbol
- Direction (BULLISH/BEARISH/NEUTRAL)
- Severity level (WATCH/ACTIONABLE/URGENT)
- Scout count (how many scouts agree)
- Aggregate confidence (sum of scout confidence scores)
- Per-scout reasoning
- Timestamp

**Evidence Quality**: Sufficient for actionable decision. User can review scout reasoning and assess consensus strength.

---

## 8. Known Risks

### Risk 1: Duplicate Notifications
**Scenario**: User receives both Telegram and email for same event
**Mitigation**: This is expected behavior for dual-channel routing. ACTIONABLE/URGENT events should send to both channels.
**Severity**: LOW — Working as designed
**Monitoring**: Track user feedback on notification volume

### Risk 2: Email Deliverability
**Scenario**: Email marked as spam or not delivered
**Mitigation**:
- Use professional subject line (no "URGENT!!!" or excessive caps)
- 4SecureMail is a paid email service (better reputation than free providers)
- Rate limiting (ALERT_MAX_PER_RUN=1) prevents spam-like volume
**Severity**: MEDIUM
**Monitoring**: Track email delivery success rate in alert history

### Risk 3: SMTP Auth Issues
**Scenario**: SMTP credentials expire or become invalid
**Mitigation**:
- SMTP failures degrade gracefully (return error, do not crash)
- Telegram continues working (independent channel)
- Monitor alert history for SMTP errors
**Severity**: MEDIUM
**Monitoring**: Check alert history database for failed email sends

### Risk 4: Overly Noisy Alerts
**Scenario**: Too many emails sent, user overwhelmed
**Mitigation**:
- ALERT_MIN_SEVERITY=ACTIONABLE (filters out INFO/WATCH)
- ALERT_MAX_PER_RUN=1 (rate limiting)
- ALERT_DEDUP_HOURS=24 (suppresses duplicates)
- Ross daily production guard (additional safeguard)
**Severity**: LOW — Multiple safeguards in place
**Monitoring**: Track total email sent per day, user feedback

### Risk 5: Mixing Manual Research with Live Alerts
**Scenario**: Manual ticker watchlist triggers live email
**Mitigation**:
- `ticker_watchlist.py` explicitly forces dry-run mode
- `ticker_drilldown.py` is read-only research (no alert code path)
- Manual watchlist scoring is report-only (isolated from alerting)
**Severity**: NONE — Code enforces isolation
**Validation**: Confirmed in CP21G-CP21J

### Risk 6: Email Contains Secrets
**Scenario**: Email body accidentally includes SMTP password or API keys
**Mitigation**:
- Email body is generated from consensus event data only (ticker, direction, scouts)
- No code path includes `.env` values in email body
- Password redaction implemented for error messages
**Severity**: NONE — Code design prevents this
**Validation**: Confirmed in CP13B/CP17 tests

---

## 9. Clear Recommendation for Next Checkpoint

**Recommended**: **CP22A — Email Render Dry-Run Test**

**Why**:
- Email delivery is the only major component not yet enabled in production
- All prerequisites are met (SMTP validated, routing validated, Telegram pilot stable)
- Staged rollout minimizes risk (render → single test → dual-channel → pilot → production)
- Email adds redundancy (if Telegram fails, email continues working)

**Rationale**:
- CP22A is low-risk (render only, no live send)
- Validates email body format before any live test
- Allows PM to review rendered email output
- Non-blocking (can roll back immediately if format is wrong)

**Alternative**: **CP20E — Morning Pilot Monitoring** (if scheduled task monitoring is due)

---

## 10. Summary

### Current State
- ✅ SMTP implementation complete and validated (CP13B)
- ✅ Alert routing complete and validated (CP14/CP15)
- ✅ Telegram-only production pilot running successfully (CP19/CP20/CP20D)
- ✅ Dual-channel test validated (CP17)
- ✅ Manual watchlist isolated from live alerts (CP21G-CP21J)
- ❌ Email delivery remains disabled (`ALERT_ENABLE_EMAIL=false`)

### Readiness Assessment
**Email is READY for controlled enablement** with staged rollout:
1. CP22A: Render dry-run (no send)
2. CP22B: Single live email test
3. CP22C: Dual-channel test
4. CP22D: Production pilot (1 alert/run, 7-day monitoring)
5. CP22E: Production decision or rollback

### Next Step
**CP22A** — Email render dry-run test to validate email body format before any live send.

---

**Document Status**: APPROVED FOR REFERENCE — Email remains disabled until explicit checkpoint enables it.
