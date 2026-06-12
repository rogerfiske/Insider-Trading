# MAIA — Generic SEC Synthesis Packet

**Company:** MAIA Biotechnology, Inc.
**CIK:** 0001878313
**Generated:** 2026-06-12T18:05:39.099654+00:00

---

## Purpose and Source Boundary

This synthesis composes SEC EDGAR public filing data from CP24B-CP24G extraction layers:

- CP24B: Ticker/CIK/submissions inventory
- CP24C: Form 4 insider transactions
- CP24D: Form 144 and 13D/G ownership filings
- CP24E: XBRL financials
- CP24F: Capital structure and dilution
- CP24G: 13F institutional ownership visibility

**This is a research synthesis, not investment advice.**

---

## Input Module Status

| Module | Status |
|--------|--------|
| sec_inventory | success |
| form4_transactions | success |
| ownership_filings | success |
| xbrl_financials | ok |
| capital_structure | success |
| institutional_13f | success |

---

## Executive Research Posture

**Overall Posture:** Strong insider-evidence / high uncertainty profile

**Scoring Components:**

| Component | Score | Comment |
|-----------|-------|---------|
| Insider Evidence | 70/100 | Form 4 activity strength |
| Capital Structure Risk | 45/100 | Lower is less risky |
| Financial Liquidity | 80/100 | Higher is better |
| Ownership Visibility | 30/100 | Institutional coverage |
| Data Quality | 100/100 | Module success rate |

---

## Evidence Matrix (Top 10)

| Category | Evidence | Direction | Strength | Confidence | Source |
|----------|----------|-----------|----------|------------|--------|
| Identity | Ticker MAIA resolved to CIK 0001878313 | positive | high | high | sec_inventory |
| Data Coverage | 0 SEC filings found across multiple form types | positive | high | high | sec_inventory |
| Insider Activity | 141 open-market insider purchases totaling $5,276,429.73 | positive | high | high | form4_transactions |
| Insider Activity | 10 distinct insider(s) made open-market purchases | positive | medium | high | form4_transactions |
| Ownership Filings | 1 Form 144 sale-intent notice(s) filed | neutral | medium | high | ownership_filings |
| Ownership Filings | 11 Schedule 13D/G beneficial ownership filing(s) (5 active 13D, 6 passive 13G) | positive | medium | high | ownership_filings |
| Institutional Ownership | No matches among 3/5 reviewed managers | neutral | not_applicable | medium | institutional_13f |
| Financial Liquidity | Cash and equivalents: $34,413,110 | positive | high | high | xbrl_financials |
| Financial Liquidity | Working capital: $28,992,690 | positive | high | high | xbrl_financials |
| Financial Liquidity | Cash runway: 19.4 months | positive | high | medium | xbrl_financials |

*Showing 10 of 13 evidence rows. See MAIA_evidence_matrix.csv for complete matrix.*

---

## Key Findings

- 141 open-market insider purchases detected totaling $5,276,429.73
- Estimated cash runway: 19.4 months based on trailing burn
- Significant dilution overhang: 45.1% (high estimate)

---

## Critical Unknowns

- Institutional visibility partial: 2 manager(s) failed to parse

---

## Monitoring Triggers

- Monitor for additional insider buying activity (Form 4 filings)

---

## Limitations

- SEC-sourced data only; no live market data
- 13F institutional ownership coverage limited to reviewed managers
- Form 144 indicates proposed sale intent, not actual sale execution
- XBRL financial data reflects most recent filing, not real-time status
- Capital structure estimates include disclosed instruments only
- No clinical/regulatory live catalyst extraction
- This is a research synthesis, not investment advice

---

## Evidence Provenance

| Module | Source | Timestamp |
|--------|--------|-----------|
| sec_inventory | SEC EDGAR public filings | 2026-06-11T19:31:10.670720+00:00 |
| form4_transactions | SEC EDGAR public filings | 2026-06-11T19:52:47.669981+00:00 |
| ownership_filings | SEC EDGAR public filings | 2026-06-12T15:39:37.488312+00:00 |
| xbrl_financials | SEC EDGAR public filings | 2026-06-12T16:07:08.788455+00:00 |
| capital_structure | SEC EDGAR public filings | 2026-06-12T16:32:04.027337+00:00 |
| institutional_13f | SEC EDGAR public filings | 2026-06-12T16:54:07.883189+00:00 |

---

## Safety Confirmations

| Flag | Value |
|------|-------|
| Report only | True |
| Alerts generated | False |
| External spreadsheet used | False |
| Telegram sent | False |
| Email sent | False |
| Scheduled tasks modified | False |
| Env printed or changed | False |
| Buy/sell/hold language used | False |

---

## No-Recommendation Statement

This document is a research synthesis of SEC public filing data.
It does not constitute investment advice, a recommendation to buy or sell securities,
or a price target. All SEC data is presented as-is for research purposes only.
