# SEC Ticker/CIK Submissions Inventory: AAPL

**Generated:** 2026-06-12T19:11:57.507094+00:00

## Purpose

This report provides SEC ticker-to-CIK resolution and submissions inventory for downstream SEC extraction checkpoints (CP24C-CP24H).

This is a report-only foundation layer. No alerts were generated, no Telegram/email was sent, no scheduled tasks were modified, and OpenInsider data was not used.

## Source Boundary

Data sources:
- SEC company_tickers.json (ticker-to-CIK mapping)
- SEC submissions API (filing history)

No third-party financial data, message boards, social media, or Roger's OpenInsider spreadsheet were used.

## Resolver Result

**Status:** resolved

**Resolution successful.**

- Ticker: `AAPL`
- CIK: `0000320193`
- Company: Apple Inc.

## SEC Submissions Status

**Status:** retrieved

**Recent filings count:** 100

## Filing Counts by Form

| Form | Count |
|------|-------|
| 4 | 167 |
| 144 | 44 |
| 8-K | 35 |
| PX14A6G | 17 |
| 10-Q | 12 |
| 424B2 | 6 |
| SC 13G/A | 6 |
| 3 | 5 |
| DEFA14A | 5 |
| SD | 4 |
| DEF 14A | 4 |
| 25-NSE | 4 |
| 10-K | 4 |
| FWP | 3 |
| UPLOAD | 3 |
| CORRESP | 3 |
| SCHEDULE 13G/A | 2 |
| S-8 | 2 |
| SCHEDULE 13G | 1 |
| 144/A | 1 |
| S-3ASR | 1 |
| 5 | 1 |
| 4/A | 1 |

## Latest Relevant Filings

### 10-K

- **Filing Date:** 2025-10-31
- **Accession Number:** 0000320193-25-000079
- **Primary Document:** aapl-20250927.htm

### 10-Q

- **Filing Date:** 2026-05-01
- **Accession Number:** 0000320193-26-000013
- **Primary Document:** aapl-20260328.htm

### 8-K

- **Filing Date:** 2026-04-30
- **Accession Number:** 0000320193-26-000011
- **Primary Document:** aapl-20260430.htm

### Form 4

- **Filing Date:** 2026-05-29
- **Accession Number:** 0001140361-26-023363
- **Primary Document:** xslF345X06/form4.xml

### Form 144

- **Filing Date:** 2026-05-27
- **Accession Number:** 0001921094-26-000555
- **Primary Document:** xsl144X01/primary_doc.xml

### 13D/13G

- **Filing Date:** 2024-02-14
- **Accession Number:** 0001193125-24-036431
- **Primary Document:** d751537dsc13ga.htm

## Downstream Readiness

| Checkpoint | Ready | Description |
|------------|-------|-------------|
| CP24C | Yes | Form 4 insider transaction extraction |
| CP24D | Yes | Form 144 restricted stock sales |
| CP24E | Yes | XBRL financial extraction |
| CP24F | Yes | 13D/13G ownership stakes |
| CP24G | Yes | Capital structure from S-3/offerings |

## Degraded Mode

**Is Degraded:** No

## Evidence Provenance

### SEC company_tickers.json

- **URL:** https://www.sec.gov/files/company_tickers.json
- **Retrieved:** 2026-06-12T19:11:57.505094+00:00

### SEC submissions API

- **URL:** https://data.sec.gov/submissions/CIK0000320193.json
- **Retrieved:** 2026-06-12T19:11:57.507094+00:00

## Safety Confirmations

- **Report Only:** True
- **Alerts Generated:** False
- **OpenInsider Spreadsheet Used:** False
- **Telegram Sent:** False
- **Email Sent:** False
- **Scheduled Tasks Modified:** False
- **Env Printed or Changed:** False
- **Buy/Sell/Hold Language Used:** False
