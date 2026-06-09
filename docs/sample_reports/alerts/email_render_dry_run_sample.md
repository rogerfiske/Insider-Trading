# EMAIL RENDER DRY-RUN — NO EMAIL SENT

**Generated**: 2026-06-09T19:20:47.605028+00:00
**Mode**: Dry-run render test only
**Network**: No SMTP send, no Telegram send

---

## Email Configuration Status

- `ALERT_ENABLE_EMAIL`: **false** (disabled)
- `ALERT_ENABLE_TELEGRAM`: true (but not sending from this script)

---

## Sample Email Alert

**To**: [configured recipient redacted]

**Subject**:
```
[INSIDER] ACTIONABLE BULLISH on MAIA
```

**Body**:
```
SOPHIE CONSENSUS -- BULLISH on MAIA
===================================
Time: 2026-06-09T19:20+00:00

3 of 5 scouts agree:
  - eddie      Recent Form 4 buying by CEO and CFO
  - maggie     Institutional ownership increase in latest 13F
  - frank      Price momentum suggests accumulation

This is informational, not a trade instruction. Ross did not place a trade. The decision is yours.
```

---

## Evidence Context Included

✅ Ticker: MAIA
✅ Direction: BULLISH
✅ Severity: ACTIONABLE
✅ Scout count: 3 scouts agree
✅ Aggregate confidence: 12
✅ Per-scout reasoning included
✅ Timestamp included
✅ Disclaimer included

---

## Safety Confirmations

✅ No email sent
✅ No Telegram sent
✅ Email remains disabled (`ALERT_ENABLE_EMAIL=false`)
✅ No SMTP credentials in output
✅ No Telegram token in output
✅ Informational-only disclaimer present

---

**Rendered sample only. No live alert delivered.**
