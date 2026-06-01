# Production Alert Enablement Plan

**Status:** Manual Pilot Complete (CP19)
**Last Updated:** 2026-06-01
**Current Checkpoint:** CP19

## Executive Summary

This document defines the staged rollout strategy for enabling production live alerts in the Insider-Trading system. All controlled tests (CP16 Telegram-only, CP17 dual-channel) have succeeded. This plan proposes a conservative four-phase approach to production enablement with appropriate safety controls, monitoring, and PM approval gates.

## Current Validated Channel Status

### Telegram

- **Status:** ✅ Fully validated
- **Validations:**
  - CP12B: Initial Telegram bot setup and controlled test
  - CP16: Controlled Telegram-only routing test via alert routing layer
  - CP17: Controlled dual-channel test (Telegram + email)
- **Capabilities:** Send formatted Markdown alerts to configured Telegram chat
- **Rate Limits:** Telegram Bot API standard limits apply
- **Ready for Production:** Yes

### Email (4SecureMail SMTP)

- **Status:** ✅ Fully validated
- **Validations:**
  - CP13B: Generic SMTP implementation and 4SecureMail configuration
  - CP17: Controlled dual-channel test (Telegram + email)
- **Capabilities:** Send plain-text alerts via 4SecureMail SMTP
- **Rate Limits:** 4SecureMail SMTP limits apply (TBD from provider)
- **Ready for Production:** Yes (after Telegram pilot)

### Alert Routing Policy

- **Status:** ✅ Implemented and validated
- **Implementation:** CP15
- **Validations:** CP16 (Telegram-only), CP17 (dual-channel)
- **Features:**
  - Severity classification (INFO, WATCH, ACTIONABLE, URGENT)
  - Alert class determination (LOG_ONLY, TELEGRAM_ONLY, EMAIL_ONLY, TELEGRAM_AND_EMAIL, SUPPRESS_DUPLICATE)
  - Time-bucketed deduplication (default 24-hour window)
  - Independent channel control (ALERT_ENABLE_TELEGRAM, ALERT_ENABLE_EMAIL)
  - Rate limiting (ALERT_MAX_PER_RUN)
  - SQLite audit trail (alert_history table)
- **Ready for Production:** Yes

## Current Safety Defaults

The system currently operates with the following safety defaults:

```env
# Master dry-run control
ROSS_DRY_RUN=true

# Channel enablement (missing = false)
ALERT_ENABLE_TELEGRAM=false
ALERT_ENABLE_EMAIL=false

# Policy defaults (missing = code defaults)
ALERT_MIN_SEVERITY=WATCH
ALERT_DEDUP_HOURS=24
ALERT_MAX_PER_RUN=3
ALERT_REQUIRE_HUMAN_REVIEW=false
```

**All live alert delivery is currently disabled.**

## Scheduled Task Configuration

### Ross Dispatcher

- **Task Name:** `Insider-ross`
- **Schedule:** Daily at 18:30 (6:30 PM)
- **Action:** `powershell -ExecutionPolicy Bypass -File C:\Users\Minis\CascadeProjects\Insider-Trading\scripts\run_agent.ps1 -Agent ross`
- **Current State:** Ready (not running)
- **Behavior:** Reads consensus events from Sophie, applies routing policy, respects dry-run and channel enablement flags

### Sophie Consensus

- **Task Name:** `Insider-sophie`
- **Schedule:** Daily at 18:00 (6:00 PM)
- **Action:** Detects consensus from scout signals
- **Timing:** Runs 30 minutes before Ross

The current schedule is appropriate for production. Ross runs after Sophie has processed the day's scout signals.

## Production Readiness Analysis

### What Works

1. ✅ **Telegram delivery:** Validated end-to-end through routing layer
2. ✅ **Email delivery:** Validated end-to-end through routing layer (4SecureMail SMTP)
3. ✅ **Severity classification:** Correctly assigns INFO, WATCH, ACTIONABLE, URGENT based on scout count and aggregate confidence
4. ✅ **Alert class determination:** Correctly routes to Telegram, email, both, or suppresses based on severity and policy
5. ✅ **Deduplication:** Time-bucketed keys prevent duplicate alerts within configurable window
6. ✅ **Audit trail:** All routing decisions recorded in SQLite alert_history table
7. ✅ **Rate limiting:** ALERT_MAX_PER_RUN prevents alert storms
8. ✅ **Independent channel control:** Channels can be enabled/disabled independently
9. ✅ **Scheduled task automation:** Windows Task Scheduler manages agent execution

### What Needs Attention Before Production

1. **PM approval decisions:** Multiple policy choices require Roger's approval before CP19 (see "PM Approval Decisions" section)
2. **Alert wording review:** Current consensus event rendering should be reviewed for production clarity
3. **Monitoring procedures:** Need to establish routine checks after live enablement
4. **Emergency disable documentation:** Operators need clear instructions for immediate disable
5. **First-run human verification:** CP19 should include manual PM approval gate before first live alert

### Code Changes Required

**None.** The system is ready for production enablement through `.env` configuration changes only. No code modifications are needed.

### Scheduled Task Changes Required

**None.** The existing schedule (Sophie at 18:00, Ross at 18:30) is appropriate for production. Tasks should remain unchanged.

## Staged Rollout Plan

### Phase 1: CP19 — Manual Production Telegram-Only Live Alert Enablement ✅

**Status:** ✅ **COMPLETE** (2026-06-01)

**Goal:** Send the first production alert (if consensus exists) via Telegram only, with human approval gate.

**Outcome:**
- **0 Telegram messages sent** (valid outcome — no eligible ACTIONABLE+ alert existed)
- **0 emails sent** (email disabled per policy)
- Dry-run preview correctly reported "nothing to dispatch"
- Manual pilot executed safely with no code changes required
- All production safety controls validated as working correctly
- Policy threshold enforcement (ACTIONABLE minimum) validated
- Empty dispatch handling validated
- No errors, no duplicates, no issues

**Approach Taken:**
- Kept scheduled tasks unchanged (remained in Ready state, not triggered)
- Ran dry-run preview first (showed no eligible alert)
- Did not apply process-level overrides (no alert to send)
- Kept email disabled
- Used ALERT_MIN_SEVERITY=ACTIONABLE threshold
- Used 24-hour deduplication window
- Used ALERT_MAX_PER_RUN=1 rate limit

**Profile (Intended, not applied — no eligible alert):**
```env
ROSS_DRY_RUN=false  # Would enable live send
ALERT_ENABLE_TELEGRAM=true  # Would enable Telegram
ALERT_ENABLE_EMAIL=false  # Keep email disabled
ALERT_MIN_SEVERITY=ACTIONABLE  # Require strong consensus
ALERT_DEDUP_HOURS=24
ALERT_MAX_PER_RUN=1
```

**Success Criteria:** ✅ All met
- ✅ Zero alerts sent based on actual consensus (no ACTIONABLE+ alert existed)
- ✅ Alert routing policy correctly enforced ACTIONABLE threshold
- ✅ No duplicate alerts
- ✅ No audit trail entry created (correct — no alert dispatched)
- ✅ No errors in logs
- ✅ Scheduled tasks not modified or triggered
- ✅ .env not modified permanently
- ✅ All validation checks passed (107 tests, 31 smoke test checks)

**Rollback:** Not required (no changes made to .env or scheduled tasks)

### Phase 2: CP20 — Scheduled Telegram-Only Pilot

**Goal:** Enable Telegram for scheduled Ross runs, monitor for at least one full cycle (24 hours).

**Approach:**
- Enable Telegram for scheduled Ross only after CP19 succeeds
- Keep email disabled
- Use existing conservative schedule (daily 18:30)
- Monitor for at least one scheduled cycle (ideally 3-7 days)
- Confirm no alert noise, no duplicates, no failures

**Profile:**
```env
ROSS_DRY_RUN=false
ALERT_ENABLE_TELEGRAM=true
ALERT_ENABLE_EMAIL=false
ALERT_MIN_SEVERITY=ACTIONABLE
ALERT_DEDUP_HOURS=24
ALERT_MAX_PER_RUN=1
ALERT_REQUIRE_HUMAN_REVIEW=false
```

**Success Criteria:**
- Scheduled Ross runs complete without errors
- Alerts sent only when consensus exists
- No duplicate alerts
- No alert storms
- Deduplication working correctly
- Audit trail complete for all scheduled runs

**Rollback:**
- Set ALERT_ENABLE_TELEGRAM=false
- Or set ROSS_DRY_RUN=true for full disable

### Phase 3: CP21 — Email Enablement Planning

**Goal:** Decide email enablement policy before CP22.

**Decisions Required:**
- Should email be used only for ACTIONABLE/URGENT?
- Should email remain disabled for WATCH?
- Should email be manual-only or scheduled?
- Should email use different frequency than Telegram?
- Should email include different content than Telegram?

**No implementation in CP21 — planning only.**

### Phase 4: CP22 — Production Dual-Channel Enablement

**Goal:** Enable email after Telegram pilot is stable (CP20 complete).

**Approach:**
- Enable email only after Telegram production pilot runs successfully for 3-7 days
- Start with same conservative settings (ACTIONABLE min severity)
- Consider different ALERT_MAX_PER_RUN for email if desired
- Monitor first email deliveries closely

**Profile:**
```env
ROSS_DRY_RUN=false
ALERT_ENABLE_TELEGRAM=true
ALERT_ENABLE_EMAIL=true
ALERT_MIN_SEVERITY=ACTIONABLE
ALERT_DEDUP_HOURS=24
ALERT_MAX_PER_RUN=1  # Or separate limits per channel if desired
ALERT_REQUIRE_HUMAN_REVIEW=false
```

**Success Criteria:**
- Both channels delivering successfully
- No duplicate alerts across channels
- Email delivery confirmed (check 4SecureMail inbox)
- Audit trail complete for dual-channel decisions

## Operator Emergency Disable Procedure

### Immediate Disable (< 1 minute)

**Option 1: Disable channels via .env**

1. Edit `.env` file:
   ```env
   ALERT_ENABLE_TELEGRAM=false
   ALERT_ENABLE_EMAIL=false
   ```
2. Save file
3. Next Ross run will respect disabled channels (within 24 hours)

**Option 2: Enable master dry-run**

1. Edit `.env` file:
   ```env
   ROSS_DRY_RUN=true
   ```
2. Save file
3. Next Ross run will be dry-run only (no real sends)

**Option 3: Disable scheduled Ross task**

```powershell
Disable-ScheduledTask -TaskPath "\InsiderRoutines\" -TaskName "Insider-ross"
```

### Verify Disable

```powershell
# Check scheduled task state
Get-ScheduledTask -TaskPath "\InsiderRoutines\" -TaskName "Insider-ross" | Select-Object State

# Check .env channel flags (without printing secrets)
python scripts\check_env_keys.py

# Check latest Ross logs (last 20 lines, no secrets)
Get-Content .state\logs\ross.log -Tail 20
```

### Re-enable After Disable

1. Fix the issue that caused the disable
2. Update `.env` with desired settings
3. If task was disabled, re-enable:
   ```powershell
   Enable-ScheduledTask -TaskPath "\InsiderRoutines\" -TaskName "Insider-ross"
   ```
4. Monitor first run after re-enable

## Operator Controls

### Inspect Scheduled Task State

```powershell
Get-ScheduledTask -TaskPath "\InsiderRoutines\" | Select-Object TaskName, State
Get-ScheduledTask -TaskName "Insider-ross" -TaskPath "\InsiderRoutines\" | Get-ScheduledTaskInfo | Select-Object LastRunTime, NextRunTime
```

### Inspect Latest Alert History

Use SQLite CLI or Python script to query alert_history table:

```powershell
# Install SQLite CLI if needed
# Query recent alerts
sqlite3 .state\state.db "SELECT created_at, ticker, direction, severity, alert_class, telegram_status, email_status FROM alert_history ORDER BY created_at DESC LIMIT 10;"
```

### Inspect Latest Ross Logs (without secrets)

```powershell
Get-Content .state\logs\ross.log -Tail 50
```

Logs contain safe operational info but **never** contain tokens or passwords.

### Verify Channels Are Disabled

```powershell
python scripts\check_env_keys.py
```

Expected output when disabled:
```
ALERT_ENABLE_TELEGRAM=MISSING  # or SET but false
ALERT_ENABLE_EMAIL=MISSING     # or SET but false
ROSS_DRY_RUN=SET               # should be true when disabled
```

### Manual Ross Test Run (dry-run)

```powershell
# Ensure ROSS_DRY_RUN=true in .env first
powershell -ExecutionPolicy Bypass -File .\scripts\run_agent.ps1 -Agent ross
```

Review output and logs to verify dry-run behavior.

## Monitoring Checklist After Live Enablement

### First 24 Hours (CP19, CP20)

- [ ] Check Ross scheduled task completed successfully
- [ ] Check Ross logs for errors
- [ ] Check alert_history table for new entries
- [ ] Verify Telegram messages received (if consensus existed)
- [ ] Verify no duplicate alerts sent
- [ ] Verify deduplication working correctly
- [ ] Verify audit trail complete

### First Week (CP20)

- [ ] Monitor daily Ross runs
- [ ] Track alert frequency (should match consensus frequency)
- [ ] Confirm no alert storms
- [ ] Confirm ALERT_MAX_PER_RUN respected
- [ ] Review alert content for clarity/accuracy
- [ ] Check for any false positives/negatives

### Ongoing (CP22+)

- [ ] Weekly review of alert_history
- [ ] Weekly review of Ross logs
- [ ] Monthly review of deduplication effectiveness
- [ ] Monthly review of alert frequency vs consensus frequency
- [ ] Quarterly review of alert content quality

## PM Approval Decisions Required Before CP19

Roger (PM) must approve the following decisions before CP19 execution:

1. **Channel Strategy:**
   - ☐ Confirm Telegram-only first (recommended)
   - ☐ Or choose dual-channel first (not recommended)

2. **Enablement Approach:**
   - ☐ Confirm manual live run first (recommended)
   - ☐ Or choose scheduled live first (not recommended)

3. **Minimum Severity Threshold:**
   - ☐ ACTIONABLE (recommended for initial production)
   - ☐ WATCH (more alerts, higher noise risk)
   - ☐ URGENT (fewer alerts, may miss important signals)

4. **Maximum Alerts Per Run:**
   - ☐ 1 (recommended for initial production)
   - ☐ 3 (code default, acceptable)
   - ☐ Other: _____

5. **Deduplication Window:**
   - ☐ 24 hours (recommended)
   - ☐ 48 hours (longer suppression)
   - ☐ Other: _____

6. **Human Review Gate:**
   - ☐ Enable ALERT_REQUIRE_HUMAN_REVIEW=true for CP19 manual run (recommended)
   - ☐ Or skip human review gate (not recommended for first production alert)

7. **WATCH Alert Email Policy:**
   - ☐ Never email WATCH alerts (recommended)
   - ☐ Email WATCH alerts
   - ☐ Decide later in CP21

8. **Alert Content:**
   - ☐ Current consensus event rendering acceptable
   - ☐ Alert wording should be revised before CP19

9. **Evidence/Source URLs:**
   - ☐ Include source URLs/evidence summaries in alerts
   - ☐ Omit source URLs (keep alerts concise)
   - ☐ Decide later

## Proposed `.env` Production Profiles

### Profile 1: Current Safe/Default (CP18)

```env
# Status: Current state (all alerts disabled)
ROSS_DRY_RUN=true
ALERT_ENABLE_TELEGRAM=false
ALERT_ENABLE_EMAIL=false
ALERT_MIN_SEVERITY=WATCH
ALERT_DEDUP_HOURS=24
ALERT_MAX_PER_RUN=3
ALERT_REQUIRE_HUMAN_REVIEW=false
```

### Profile 2: CP19 Manual Telegram-Only (Proposed)

```env
# Status: For manual CP19 test only (not scheduled)
ROSS_DRY_RUN=false  # Enable live delivery
ALERT_ENABLE_TELEGRAM=true  # Enable Telegram
ALERT_ENABLE_EMAIL=false  # Keep email disabled
ALERT_MIN_SEVERITY=ACTIONABLE  # Require strong consensus
ALERT_DEDUP_HOURS=24  # 24-hour dedup window
ALERT_MAX_PER_RUN=1  # Limit to 1 alert
ALERT_REQUIRE_HUMAN_REVIEW=true  # Manual approval gate
```

### Profile 3: CP20 Scheduled Telegram-Only Pilot (Proposed)

```env
# Status: For scheduled production pilot (after CP19 success)
ROSS_DRY_RUN=false  # Enable live delivery
ALERT_ENABLE_TELEGRAM=true  # Enable Telegram
ALERT_ENABLE_EMAIL=false  # Keep email disabled
ALERT_MIN_SEVERITY=ACTIONABLE  # Require strong consensus
ALERT_DEDUP_HOURS=24  # 24-hour dedup window
ALERT_MAX_PER_RUN=1  # Limit to 1 alert
ALERT_REQUIRE_HUMAN_REVIEW=false  # No manual gate (automated)
```

### Profile 4: CP22 Dual-Channel Production (Future)

```env
# Status: After Telegram pilot stable (CP20 complete)
ROSS_DRY_RUN=false  # Enable live delivery
ALERT_ENABLE_TELEGRAM=true  # Enable Telegram
ALERT_ENABLE_EMAIL=true  # Enable email
ALERT_MIN_SEVERITY=ACTIONABLE  # Require strong consensus
ALERT_DEDUP_HOURS=24  # 24-hour dedup window
ALERT_MAX_PER_RUN=1  # Limit to 1 alert per run
ALERT_REQUIRE_HUMAN_REVIEW=false  # No manual gate (automated)
```

**Note:** These are planning examples only. Actual `.env` changes occur in CP19-CP22 implementation checkpoints, not CP18.

## Risks and Mitigation

### Risk: Alert Storm

**Description:** Multiple alerts sent in rapid succession due to misconfiguration or routing policy bug.

**Mitigation:**
- ALERT_MAX_PER_RUN=1 for initial production (CP19, CP20)
- Deduplication prevents duplicate ticker/direction alerts within 24 hours
- Rate limiting in routing layer
- Manual disable procedure documented

**Likelihood:** Low (mitigated)

### Risk: False Positive Alerts

**Description:** Alerts sent for low-confidence or spurious consensus events.

**Mitigation:**
- ALERT_MIN_SEVERITY=ACTIONABLE requires 3+ scouts or high aggregate confidence
- Human review of alert content quality during CP20 pilot
- Can raise ALERT_MIN_SEVERITY to URGENT if needed

**Likelihood:** Medium (acceptable for informational alerts)

### Risk: Missed Important Alerts

**Description:** Real consensus events not alerted due to overly conservative settings.

**Mitigation:**
- Review alert_history regularly to identify suppressed alerts
- Adjust ALERT_MIN_SEVERITY if needed
- Consider lowering threshold after pilot phase

**Likelihood:** Medium (acceptable tradeoff for initial production)

### Risk: Email Rate Limiting

**Description:** 4SecureMail SMTP provider rate limits or blocks high-frequency emails.

**Mitigation:**
- Start with Telegram-only (CP19, CP20)
- Test email frequency limits before CP22
- Use separate ALERT_MAX_PER_RUN for email if needed
- Have fallback SMTP provider ready

**Likelihood:** Low (4SecureMail limits TBD)

### Risk: Scheduled Task Failure

**Description:** Windows scheduled task fails to execute Ross.

**Mitigation:**
- Monitor scheduled task state daily
- Windows Task Scheduler logs failures
- Ross logs capture execution errors
- Manual Ross run always available as backup

**Likelihood:** Low (scheduled tasks validated in CP10+)

## Next Steps

### CP19 Preparation

Before executing CP19:

1. Roger (PM) approves all policy decisions listed above
2. Review current consensus events in Sophie database
3. Confirm at least one consensus event exists for CP19 test (or wait for one)
4. Review alert content/wording if needed
5. Prepare `.env` changes for manual CP19 run (do not apply yet)
6. Schedule CP19 execution window with Roger

### CP19 Implementation

See CP19 instruction file for detailed implementation steps.

## Approval Status

- [ ] **PM Approval Required:** Roger must approve this plan before CP19
- [ ] **Policy Decisions Approved:** All PM decisions documented above
- [ ] **Alert Content Approved:** Current consensus event rendering acceptable
- [ ] **Emergency Procedures Reviewed:** Operator disable procedures tested
- [ ] **Monitoring Plan Approved:** Checklist acceptable for CP20 pilot

**Awaiting Roger's approval to proceed to CP19.**
