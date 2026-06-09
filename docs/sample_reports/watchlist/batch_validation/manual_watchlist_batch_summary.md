# Manual Ticker Watchlist Summary

**Generated**: 2026-06-09T18:12:06.620172+00:00
**Mode**: DRY-RUN — No Telegram or email was sent. This report is for analysis only.

## Configuration

- **Lookback Days**: 1460
- **Max Form 4 Filings**: 100
- **Tickers Requested**: 4
- **Tickers Resolved**: 4
- **Tickers Failed**: 0

## Data Sources

- SEC EDGAR API
- Project connectors (SEC Form 4, SEC 13F)
- **Roger's OpenInsider spreadsheet was not used**

## Ranked Watchlist

Tickers ranked by insider buying evidence strength (score 0-100):

| Rank | Ticker | Company | Score | Rating | Eddie Signal | Purchase Value | Net Value | Buyers |
|------|--------|---------|-------|--------|--------------|----------------|-----------|--------|
| 1 | MAIA | MAIA Biotechnology, Inc. | 95.0 | Very Strong Insider  | BULLISH_EVIDENCE | $2,191,478 | $2,191,478 | 7 |
| 2 | TSLA | Tesla, Inc. | 65.0 | Strong Insider Buyin | BULLISH_EVIDENCE | $1,000,984,274 | $116,684,897 | 2 |
| 3 | AAPL | Apple Inc. | 1.0 | Little/No Insider Bu | BEARISH_EVIDENCE | $0 | $-546,654,180 | 0 |
| 4 | ZZZINVALID123 | Unknown | 0.0 | Little/No Insider Bu | N/A | $0 | $0 | 0 |

## Per-Ticker Reports

- [MAIA](./watchlist/MAIA_manual_ticker_report.md)
- [TSLA](./watchlist/TSLA_manual_ticker_report.md)
- [AAPL](./watchlist/AAPL_manual_ticker_report.md)
- [ZZZINVALID123](./watchlist/ZZZINVALID123_manual_ticker_report.md)

## Ranking Method

Tickers are ranked by **Insider Evidence Score** (0-100 points):

### Scoring Components

1. **Net Insider Buying Value** (0-25 pts): Purchase value minus sale value
2. **Buy/Sell Imbalance** (0-20 pts): Reward strong buying with little/no selling
3. **Distinct Buyer Breadth** (0-15 pts): More distinct insider buyers
4. **Recency** (0-15 pts): How recently insiders purchased
5. **Role Quality** (0-10 pts): CEO/CFO/Director purchases weighted higher
6. **Persistence** (0-10 pts): Purchases across multiple months
7. **Data Quality** (0-5 pts): Form 4 parsing completeness

### Rating Labels

- **80-100**: Very Strong Insider Buying Evidence
- **60-79**: Strong Insider Buying Evidence
- **40-59**: Moderate Insider Buying Evidence
- **20-39**: Weak Insider Buying Evidence
- **0-19**: Little/No Insider Buying Evidence

**Note**: Scores are for ranking/research only. Not trading recommendations.

## Safety Confirmations

- ✅ No Telegram messages sent
- ✅ No email sent
- ✅ Roger's OpenInsider spreadsheet not used
- ✅ Data sourced from SEC EDGAR only

## Disclaimer

**This analysis is informational only and is not trading advice.**

Insider transactions can occur for many reasons unrelated to stock price expectations. This report presents SEC filing data for research purposes only. Do not use this information as the sole basis for investment decisions.
