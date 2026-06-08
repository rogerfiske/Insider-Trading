# Manual Ticker Watchlist History Summary

**Generated**: 2026-06-08T18:33:09.729652+00:00
**Run ID**: `8a74a6e2-5462-426a-afcf-e2da8b0d8611`
**Mode**: DRY-RUN — No Telegram or email was sent. This is research history only.

## Configuration

- **History Database**: `.state\watchlist_history.db`
- **Lookback Days**: 1460
- **Max Form 4 Filings**: Unlimited
- **Tickers Requested**: 1
- **Tickers Resolved**: 1
- **Tickers Failed**: 0
- **Compared with Prior Runs**: Yes

## Data Sources

- SEC EDGAR API
- Project connectors (SEC Form 4, SEC 13F)
- **Roger's OpenInsider spreadsheet was not used**

## Current Run Results

Tickers ranked by insider buying evidence strength:

| Rank | Ticker | Company | Eddie Signal | Confidence | Purchases | Purchase Value | Sales | Net Value |
|------|--------|---------|--------------|------------|-----------|----------------|-------|-----------
| 1 | MAIA | MAIA Biotechnology, Inc. | BULLISH_EVIDENCE | 2 | 134 | $4,921,437.58 | 0 | $4,921,437.58 |

## Comparison with Prior Runs

Changes since most recent prior run for each ticker:

| Ticker | Prior Run Date | Purchase Value Δ | Purchase Count Δ | Sale Value Δ | Sale Count Δ | Signal Changed | Note |
|--------|----------------|------------------|------------------|--------------|--------------|----------------|------|
| MAIA | 2026-06-08 | $0.00 | 0 | $0.00 | 0 | No | No purchase value change |

## Per-Ticker Reports

- [MAIA](./MAIA_manual_ticker_report.md)

## Limitations

- This is manual research history only, not trading advice
- Deltas show changes in SEC filing data, not price movements
- Insider transactions can occur for many reasons unrelated to expectations
- Historical comparison requires multiple saved runs over time

## Safety Confirmations

- ✅ No Telegram messages sent
- ✅ No email sent
- ✅ Roger's OpenInsider spreadsheet not used
- ✅ Data sourced from SEC EDGAR only
- ✅ History database is local and gitignored

## Disclaimer

**This analysis is informational only and is not trading advice.**

Insider transactions can occur for many reasons unrelated to stock price expectations. This report presents SEC filing data for research purposes only. Do not use this information as the sole basis for investment decisions.
