# NVDA — Generic SEC Synthesis Packet

**Company:** NVIDIA CORP
**CIK:** 0001045810
**Generated:** 2026-06-12T17:52:02.393445+00:00

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

**Overall Posture:** Large operating company / institutional visibility profile

**Scoring Components:**

| Component | Score | Comment |
|-----------|-------|---------|
| Insider Evidence | 0/100 | Form 4 activity strength |
| Capital Structure Risk | N/A | Data unavailable |
| Financial Liquidity | 100/100 | Higher is better |
| Ownership Visibility | 80/100 | Institutional coverage |
| Data Quality | 100/100 | Module success rate |

---

## Evidence Matrix (Top 10)

| Category | Evidence | Direction | Strength | Confidence | Source |
|----------|----------|-----------|----------|------------|--------|
| Identity | Ticker NVDA resolved to CIK 0001045810 | positive | high | high | sec_inventory |
| Data Coverage | 0 SEC filings found across multiple form types | positive | high | high | sec_inventory |
| Insider Activity | 1 open-market insider purchases totaling $250,000.00 | positive | high | high | form4_transactions |
| Insider Activity | 1501 open-market insider sales totaling $5,218,282,389.93 | negative | medium | high | form4_transactions |
| Insider Activity | 1 distinct insider(s) made open-market purchases | positive | medium | high | form4_transactions |
| Ownership Filings | 241 Form 144 sale-intent notice(s) filed | neutral | medium | high | ownership_filings |
| Ownership Filings | 14 Schedule 13D/G beneficial ownership filing(s) (0 active 13D, 14 passive 13G) | positive | medium | high | ownership_filings |
| Institutional Ownership | 10 institutional holdings matched ($26,855,805,249,000 total value) | positive | medium | medium | institutional_13f |
| Financial Liquidity | Cash and equivalents: $13,237,000,000 | positive | high | high | xbrl_financials |
| Financial Liquidity | Working capital: $107,111,000,000 | positive | high | high | xbrl_financials |

*Showing 10 of 12 evidence rows. See NVDA_evidence_matrix.csv for complete matrix.*

---

## Key Findings

- 1 open-market insider purchases detected totaling $250,000.00

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
| sec_inventory | SEC EDGAR public filings | 2026-06-11T19:31:24.313924+00:00 |
| form4_transactions | SEC EDGAR public filings | 2026-06-11T19:54:54.126737+00:00 |
| ownership_filings | SEC EDGAR public filings | 2026-06-12T15:40:34.062743+00:00 |
| xbrl_financials | SEC EDGAR public filings | 2026-06-12T16:07:52.744640+00:00 |
| capital_structure | SEC EDGAR public filings | 2026-06-12T16:31:35.273597+00:00 |
| institutional_13f | SEC EDGAR public filings | 2026-06-12T16:54:16.645766+00:00 |

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
