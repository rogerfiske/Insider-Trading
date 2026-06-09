# Manual Ticker Watchlist History Summary

**Generated**: 2026-06-09T18:12:06.694923+00:00
**Run ID**: `94f61b6f-424c-464d-b013-f4f8a2a5221d`
**Mode**: DRY-RUN — No Telegram or email was sent. This is research history only.

## Configuration

- **History Database**: `.state\watchlist_history.db`
- **Lookback Days**: 1460
- **Max Form 4 Filings**: 100
- **Tickers Requested**: 4
- **Tickers Resolved**: 4
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
| 1 | MAIA | MAIA Biotechnology, Inc. | BULLISH_EVIDENCE | 2 | 37 | $2,191,477.60 | 0 | $2,191,477.60 |
| 2 | TSLA | Tesla, Inc. | BULLISH_EVIDENCE | 2 | 26 | $1,000,984,274.37 | 367 | $116,684,896.83 |
| 3 | AAPL | Apple Inc. | BEARISH_EVIDENCE | 2 | 0 | $0.00 | 82 | $-546,654,179.81 |
| 4 | ZZZINVALID123 | Unknown | N/A | 0 | 0 | $0.00 | 0 | $0.00 |

## Comparison with Prior Runs

Changes since most recent prior run for each ticker:

| Ticker | Prior Run Date | Purchase Value Δ | Purchase Count Δ | Sale Value Δ | Sale Count Δ | Signal Changed | Note |
|--------|----------------|------------------|------------------|--------------|--------------|----------------|------|
| MAIA | 2026-06-09 | $0.00 | 0 | $0.00 | 0 | No | No purchase value change |
| TSLA | 2026-06-09 | $0.00 | 0 | $0.00 | 0 | No | No purchase value change |
| AAPL | 2026-06-09 | $0.00 | 0 | $0.00 | 0 | No | No purchase value change |
| ZZZINVALID123 | 2026-06-09 | $0.00 | 0 | $0.00 | 0 | No | No purchase value change |

## Per-Ticker Reports

- [MAIA](./MAIA_manual_ticker_report.md)
- [TSLA](./TSLA_manual_ticker_report.md)
- [AAPL](./AAPL_manual_ticker_report.md)
- [ZZZINVALID123](./ZZZINVALID123_manual_ticker_report.md)

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
