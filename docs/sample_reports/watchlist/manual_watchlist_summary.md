# Manual Ticker Watchlist Summary

**Generated**: 2026-06-08T18:33:09.685739+00:00
**Mode**: DRY-RUN — No Telegram or email was sent. This report is for analysis only.

## Configuration

- **Lookback Days**: 1460
- **Max Form 4 Filings**: Unlimited
- **Tickers Requested**: 1
- **Tickers Resolved**: 1
- **Tickers Failed**: 0

## Data Sources

- SEC EDGAR API
- Project connectors (SEC Form 4, SEC 13F)
- **Roger's OpenInsider spreadsheet was not used**

## Ranked Watchlist

Tickers ranked by insider buying evidence strength:

| Rank | Ticker | Company | Eddie Signal | Confidence | Purchases | Purchase Value | Sales | Net Value |
|------|--------|---------|--------------|------------|-----------|----------------|-------|-----------|
| 1 | MAIA | MAIA Biotechnology, Inc. | BULLISH_EVIDENCE | 2 | 134 | $4,921,437.58 | 0 | $4,921,437.58 |

## Per-Ticker Reports

- [MAIA](./watchlist/MAIA_manual_ticker_report.md)

## Ranking Method

Tickers are ranked by:

1. **Eddie Signal**: BULLISH_EVIDENCE > NEUTRAL > BEARISH_EVIDENCE
2. **Net Purchase Value**: Higher insider buying value ranks higher
3. **Purchase Count**: More purchase transactions rank higher
4. **Data Completeness**: More Form 4 filings parsed ranks higher

## Safety Confirmations

- ✅ No Telegram messages sent
- ✅ No email sent
- ✅ Roger's OpenInsider spreadsheet not used
- ✅ Data sourced from SEC EDGAR only

## Disclaimer

**This analysis is informational only and is not trading advice.**

Insider transactions can occur for many reasons unrelated to stock price expectations. This report presents SEC filing data for research purposes only. Do not use this information as the sole basis for investment decisions.
