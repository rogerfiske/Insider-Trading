# Full SEC Extraction JSON Schemas

**Version:** 1.0
**Created:** 2026-06-11
**Checkpoint:** CP24A
**Parent:** [full_sec_extraction_architecture.md](full_sec_extraction_architecture.md)

---

## Overview

This document defines the JSON schemas for all extraction outputs in the full SEC extraction pipeline. Each schema includes required fields, data types, validation rules, and examples.

**Key Principles:**
- All schemas include evidence provenance (source, retrieve_at, source_url)
- All schemas include status tracking (ok, parse_status, error_type)
- All monetary values in USD
- All dates in ISO 8601 format (YYYY-MM-DD)
- All timestamps in ISO 8601 format with timezone (YYYY-MM-DDTHH:MM:SSZ)

---

## 1. Ticker Resolution

### Schema: `TickerCikResult`

```json
{
  "ok": true,
  "ticker": "NVDA",
  "cik": "1045810",
  "cik_padded": "0001045810",
  "company_name": "NVIDIA CORP",
  "error_type": null,
  "error_message": null,
  "retrieve_at": "2026-06-11T18:30:00Z",
  "source_url": "https://www.sec.gov/files/company_tickers.json"
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ok | boolean | Yes | Top-level success indicator |
| ticker | string | Yes | Normalized ticker symbol (uppercase) |
| cik | string | Yes (if ok=true) | CIK as string without leading zeros |
| cik_padded | string | Yes (if ok=true) | 10-digit zero-padded CIK |
| company_name | string | Yes (if ok=true) | Official SEC company name |
| error_type | string \| null | No | Error category: TICKER_NOT_FOUND, NETWORK_ERROR, PARSE_ERROR |
| error_message | string \| null | No | Human-readable error description |
| retrieve_at | string | Yes | ISO 8601 timestamp |
| source_url | string | Yes | SEC data source URL |

**Error Example:**

```json
{
  "ok": false,
  "ticker": "INVALIDTICKER",
  "cik": null,
  "cik_padded": null,
  "company_name": null,
  "error_type": "TICKER_NOT_FOUND",
  "error_message": "Ticker 'INVALIDTICKER' not found in SEC company tickers database",
  "retrieve_at": "2026-06-11T18:30:00Z",
  "source_url": "https://www.sec.gov/files/company_tickers.json"
}
```

---

## 2. SEC Filing Inventory

### Schema: `SecSubmissionFiling`

```json
{
  "accession_number": "0001045810-26-000012",
  "filing_date": "2026-06-01",
  "report_date": "2026-05-31",
  "form": "10-Q",
  "primary_document": "nvda-20260531.htm",
  "archive_directory_url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000012",
  "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000012/nvda-20260531.htm"
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| accession_number | string | Yes | Unique SEC filing identifier (NNNNNNNNNN-NN-NNNNNN) |
| filing_date | string | Yes | Date filing was submitted to SEC (YYYY-MM-DD) |
| report_date | string | No | Report period end date (YYYY-MM-DD) |
| form | string | Yes | Filing type (4, 144, 13D, 13G, 13F-HR, 10-Q, 10-K, etc.) |
| primary_document | string | Yes | Primary document filename |
| archive_directory_url | string | Yes | EDGAR archive directory URL |
| primary_document_url | string | Yes | Full URL to primary document |

**Inventory Response Example:**

```json
{
  "ticker": "NVDA",
  "cik": "0001045810",
  "company_name": "NVIDIA CORP",
  "lookback_days": 1460,
  "total_filings": 142,
  "filings_by_type": {
    "4": 37,
    "10-Q": 16,
    "10-K": 4,
    "8-K": 42,
    "DEF 14A": 4,
    "13F-HR": 0,
    "13D": 0,
    "13G": 5,
    "144": 12,
    "other": 22
  },
  "filings": [
    {
      "accession_number": "0001045810-26-000012",
      "filing_date": "2026-06-01",
      "report_date": "2026-05-31",
      "form": "10-Q",
      "primary_document": "nvda-20260531.htm",
      "archive_directory_url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000012",
      "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000012/nvda-20260531.htm"
    }
  ],
  "retrieve_at": "2026-06-11T18:30:00Z",
  "source_url": "https://data.sec.gov/submissions/CIK0001045810.json"
}
```

---

## 3. Form 4 Transactions

### Schema: `Form4FilingDetails`

```json
{
  "accession_number": "0001209191-26-012345",
  "filing_date": "2026-06-01",
  "issuer_cik": "0001878313",
  "issuer_name": "MAIA Biotechnology, Inc.",
  "issuer_ticker": "MAIA",
  "owners": [
    {
      "owner_cik": "0001234567",
      "owner_name": "Smith John",
      "is_director": true,
      "is_officer": true,
      "is_ten_percent_owner": false,
      "officer_title": "Chief Executive Officer"
    }
  ],
  "transactions": [
    {
      "transaction_date": "2026-05-30",
      "security_title": "Common Stock",
      "transaction_code": "P",
      "acquisition_disposition_code": "A",
      "shares": 10000.0,
      "price_per_share": 5.50,
      "transaction_value_usd": 55000.0,
      "shares_owned_following": 150000.0,
      "ownership_nature": "D",
      "classification": "OPEN_MARKET_PURCHASE"
    }
  ],
  "parse_status": "success",
  "error_type": null,
  "error_message": null,
  "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1878313/000120919126012345/xslF345X03/primary_doc.xml",
  "retrieve_at": "2026-06-11T18:30:00Z"
}
```

**Field Definitions:**

**Top-level:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| accession_number | string | Yes | Filing accession number |
| filing_date | string | Yes | Form 4 filing date (YYYY-MM-DD) |
| issuer_cik | string | Yes | Issuer's 10-digit CIK |
| issuer_name | string | Yes | Issuer company name |
| issuer_ticker | string | No | Issuer ticker symbol |
| owners | array | Yes | Reporting owners |
| transactions | array | Yes | Transaction details |
| parse_status | string | Yes | success \| partial \| failed |
| error_type | string \| null | No | XML_PARSE_ERROR, MISSING_OWNER, MISSING_PRICE |
| error_message | string \| null | No | Human-readable error |
| primary_document_url | string | Yes | XML document URL |
| retrieve_at | string | Yes | ISO 8601 timestamp |

**Owner object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| owner_cik | string | Yes | Reporting owner's CIK |
| owner_name | string | Yes | Owner's full name |
| is_director | boolean | Yes | Director status |
| is_officer | boolean | Yes | Officer status |
| is_ten_percent_owner | boolean | Yes | 10% beneficial owner status |
| officer_title | string \| null | No | Officer title if is_officer=true |

**Transaction object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| transaction_date | string | Yes | Transaction date (YYYY-MM-DD) |
| security_title | string | Yes | Security type (Common Stock, etc.) |
| transaction_code | string | Yes | SEC transaction code (P/S/M/A/F/G/D/etc.) |
| acquisition_disposition_code | string | Yes | A (acquire) or D (dispose) |
| shares | float | Yes | Number of shares |
| price_per_share | float \| null | No | Price per share (null if not reported) |
| transaction_value_usd | float \| null | No | Total value (shares × price) |
| shares_owned_following | float | Yes | Shares owned after transaction |
| ownership_nature | string | Yes | D (direct) or I (indirect) |
| classification | string | Yes | Classified transaction type |

**Transaction Classifications:**
- OPEN_MARKET_PURCHASE
- OPEN_MARKET_SALE
- OPTION_EXERCISE
- OPTION_EXERCISE_WITH_SALE
- GRANT_AWARD
- TAX_WITHHOLDING_OR_DISPOSITION
- OTHER_OR_UNCLASSIFIED

**Aggregated Insider Activity:**

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "lookback_days": 1460,
  "total_form4_filings": 37,
  "open_market_purchases": {
    "count": 134,
    "total_shares": 456789.0,
    "total_value_usd": 4876543.21,
    "distinct_buyers": 12,
    "latest_purchase_date": "2026-06-01"
  },
  "open_market_sales": {
    "count": 8,
    "total_shares": 50000.0,
    "total_value_usd": 325000.0,
    "distinct_sellers": 3,
    "latest_sale_date": "2026-05-15"
  },
  "net_insider_activity": {
    "net_purchase_value_usd": 4551543.21,
    "net_shares": 406789.0,
    "insider_evidence_score": 87.5
  },
  "parse_summary": {
    "success_count": 35,
    "partial_count": 2,
    "failed_count": 0
  },
  "provenance": {
    "source": "SEC EDGAR Form 4 filings",
    "retrieve_at": "2026-06-11T18:30:00Z",
    "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001878313&type=4"
  }
}
```

---

## 4. Form 144 Filings

### Schema: `Form144Filing`

```json
{
  "accession_number": "0001234567-26-000045",
  "filing_date": "2026-06-01",
  "issuer_cik": "0001878313",
  "issuer_name": "MAIA Biotechnology, Inc.",
  "reporting_person_name": "Jones Mary",
  "reporting_person_cik": "0009876543",
  "shares_proposed_for_sale": 25000.0,
  "proposed_sale_date": "2026-06-15",
  "aggregate_market_value_usd": 137500.0,
  "parse_status": "success",
  "error_type": null,
  "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1878313/000123456726000045/form144.txt",
  "retrieve_at": "2026-06-11T18:30:00Z"
}
```

**Note:** Form 144 extraction planned for CP24D. Schema subject to refinement during implementation.

---

## 5. Ownership 13D/G

### Schema: `Ownership13DG`

```json
{
  "accession_number": "0001193125-26-123456",
  "filing_date": "2026-06-01",
  "form_type": "SC 13G/A",
  "issuer_cik": "0001878313",
  "issuer_name": "MAIA Biotechnology, Inc.",
  "filer_name": "BlackRock, Inc.",
  "filer_cik": "0001085364",
  "shares_beneficially_owned": 1250000.0,
  "percent_of_class": 8.5,
  "sole_voting_power": 1200000.0,
  "shared_voting_power": 50000.0,
  "sole_dispositive_power": 1250000.0,
  "shared_dispositive_power": 0.0,
  "parse_status": "success",
  "error_type": null,
  "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1878313/000119312526123456/d123456dsc13ga.htm",
  "retrieve_at": "2026-06-11T18:30:00Z"
}
```

**Note:** 13D/G extraction planned for CP24D. Schema subject to refinement during implementation.

---

## 6. Ownership 13F

### Schema: `HoldingMatchResult`

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "company_name": "MAIA Biotechnology, Inc.",
  "manager_name": "Berkshire Hathaway Inc",
  "manager_cik": "0001067983",
  "filing_accession": "0001193125-26-098765",
  "filing_date": "2026-05-15",
  "report_period": "2026-03-31",
  "value_usd_thousands": 12500,
  "shares": 500000,
  "cusip": "55617Y100",
  "match_confidence": "EXACT_CUSIP",
  "match_method": "CUSIP exact match",
  "issuer_name_in_filing": "MAIA Biotechnology Inc",
  "retrieve_at": "2026-06-11T18:30:00Z",
  "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001067983&type=13F"
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ticker | string | Yes | Resolved ticker symbol |
| cik | string | Yes | Issuer's CIK |
| company_name | string | Yes | Issuer's resolved company name |
| manager_name | string | Yes | Institutional manager name |
| manager_cik | string | Yes | Manager's CIK |
| filing_accession | string | Yes | 13F-HR filing accession number |
| filing_date | string | Yes | Filing date (YYYY-MM-DD) |
| report_period | string | Yes | Report period end date (YYYY-MM-DD) |
| value_usd_thousands | integer | Yes | Holding value in thousands of USD |
| shares | integer | Yes | Number of shares held |
| cusip | string \| null | No | Security CUSIP (9 characters) |
| match_confidence | string | Yes | Match confidence level |
| match_method | string | Yes | How the match was determined |
| issuer_name_in_filing | string | Yes | Issuer name as reported in 13F |
| retrieve_at | string | Yes | ISO 8601 timestamp |
| source_url | string | Yes | SEC source URL |

**Match Confidence Levels:**
- EXACT_CUSIP (highest confidence)
- EXACT_ISSUER_NAME (high confidence)
- NORMALIZED_ISSUER_NAME (medium confidence)
- NO_MATCH (no match found)

**Aggregated 13F Holdings:**

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "company_name": "MAIA Biotechnology, Inc.",
  "managers_checked": 5,
  "managers_with_holdings": 2,
  "total_value_usd_thousands": 25000,
  "total_shares": 1000000,
  "holdings": [
    {
      "manager_name": "Berkshire Hathaway Inc",
      "manager_cik": "0001067983",
      "value_usd_thousands": 12500,
      "shares": 500000,
      "match_confidence": "EXACT_CUSIP"
    },
    {
      "manager_name": "Bridgewater Associates",
      "manager_cik": "0001350694",
      "value_usd_thousands": 12500,
      "shares": 500000,
      "match_confidence": "EXACT_ISSUER_NAME"
    }
  ],
  "provenance": {
    "source": "SEC EDGAR 13F-HR filings",
    "report_period": "2026-03-31",
    "retrieve_at": "2026-06-11T18:30:00Z"
  }
}
```

---

## 7. XBRL Financials

### Schema: `XBRLFinancials`

```json
{
  "ticker": "NVDA",
  "cik": "0001045810",
  "accession_number": "0001045810-26-000012",
  "filing_date": "2026-06-01",
  "report_period": "2026-05-31",
  "form_type": "10-Q",
  "fiscal_year": 2026,
  "fiscal_period": "Q1",
  "financials": {
    "cash_and_cash_equivalents_usd": 8500000000,
    "total_assets_usd": 45000000000,
    "total_liabilities_usd": 18000000000,
    "current_assets_usd": 22000000000,
    "current_liabilities_usd": 8000000000,
    "working_capital_usd": 14000000000,
    "quarterly_revenue_usd": 12000000000,
    "quarterly_operating_cash_flow_usd": 4500000000,
    "quarterly_rd_expense_usd": 2100000000,
    "quarterly_net_income_usd": 5200000000
  },
  "parse_status": "success",
  "error_type": null,
  "missing_fields": [],
  "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000012/nvda-20260531.htm",
  "retrieve_at": "2026-06-11T18:30:00Z"
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ticker | string | Yes | Ticker symbol |
| cik | string | Yes | Company CIK |
| accession_number | string | Yes | Filing accession number |
| filing_date | string | Yes | Filing date (YYYY-MM-DD) |
| report_period | string | Yes | Report period end date (YYYY-MM-DD) |
| form_type | string | Yes | 10-Q or 10-K |
| fiscal_year | integer | Yes | Fiscal year |
| fiscal_period | string | Yes | Q1/Q2/Q3/Q4 or FY |
| financials | object | Yes | Financial statement data |
| parse_status | string | Yes | success \| partial \| failed |
| error_type | string \| null | No | Error category |
| missing_fields | array | Yes | List of XBRL tags that were not found |
| primary_document_url | string | Yes | SEC filing URL |
| retrieve_at | string | Yes | ISO 8601 timestamp |

**Financials object fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cash_and_cash_equivalents_usd | float \| null | No | Cash balance (us-gaap:CashAndCashEquivalentsAtCarryingValue) |
| total_assets_usd | float \| null | No | Total assets (us-gaap:Assets) |
| total_liabilities_usd | float \| null | No | Total liabilities (us-gaap:Liabilities) |
| current_assets_usd | float \| null | No | Current assets (us-gaap:AssetsCurrent) |
| current_liabilities_usd | float \| null | No | Current liabilities (us-gaap:LiabilitiesCurrent) |
| working_capital_usd | float \| null | No | Working capital (calculated or us-gaap:WorkingCapital) |
| quarterly_revenue_usd | float \| null | No | Quarterly revenue (us-gaap:Revenues) |
| quarterly_operating_cash_flow_usd | float \| null | No | Operating cash flow (us-gaap:NetCashProvidedByUsedInOperatingActivities) |
| quarterly_rd_expense_usd | float \| null | No | R&D expense (us-gaap:ResearchAndDevelopmentExpense) |
| quarterly_net_income_usd | float \| null | No | Net income (us-gaap:NetIncomeLoss) |

**Note:** XBRL extraction planned for CP24E. Schema subject to refinement during implementation.

---

## 8. Capital Structure

### Schema: `CapitalStructure`

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "report_date": "2026-03-31",
  "accession_number": "0001878313-26-000005",
  "common_shares_outstanding": 14750000,
  "stock_options_outstanding": 2100000,
  "warrants_outstanding": 3500000,
  "convertible_securities_equivalent_shares": 0,
  "approximate_fully_diluted_shares": 20350000,
  "dilution_overhang_percent": 27.5,
  "parse_status": "success",
  "error_type": null,
  "data_sources": [
    "10-Q Note 10: Stock-Based Compensation",
    "10-Q Note 8: Warrants"
  ],
  "primary_document_url": "https://www.sec.gov/Archives/edgar/data/1878313/000187831326000005/maia-20260331.htm",
  "retrieve_at": "2026-06-11T18:30:00Z"
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ticker | string | Yes | Ticker symbol |
| cik | string | Yes | Company CIK |
| report_date | string | Yes | Report date (YYYY-MM-DD) |
| accession_number | string | Yes | Source filing accession number |
| common_shares_outstanding | integer \| null | No | Common shares outstanding |
| stock_options_outstanding | integer \| null | No | Stock options outstanding |
| warrants_outstanding | integer \| null | No | Warrants outstanding |
| convertible_securities_equivalent_shares | integer \| null | No | Convertible securities (as-converted shares) |
| approximate_fully_diluted_shares | integer \| null | No | Sum of all dilutive securities |
| dilution_overhang_percent | float \| null | No | (fully_diluted - common) / fully_diluted × 100 |
| parse_status | string | Yes | success \| partial \| failed |
| error_type | string \| null | No | Error category |
| data_sources | array | Yes | List of filing sections used |
| primary_document_url | string | Yes | SEC filing URL |
| retrieve_at | string | Yes | ISO 8601 timestamp |

**Note:** Capital structure extraction planned for CP24F. Schema subject to refinement during implementation.

---

## 9. Clinical/Regulatory Classification

### Schema: `ClinicalClassification`

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "is_biotech": true,
  "confidence": "HIGH",
  "evidence": {
    "sic_code": "2834",
    "sic_description": "Pharmaceutical Preparations",
    "sic_match": true,
    "business_description_keywords": [
      "clinical trial",
      "Phase 2",
      "FDA",
      "therapeutic",
      "THIO-101"
    ],
    "company_name_patterns": [
      "Biotechnology"
    ]
  },
  "clinical_programs": [
    {
      "program_name": "THIO-101",
      "indication": "Advanced solid tumors",
      "phase": "Phase 2",
      "status": "Active",
      "source": "Business Description, 10-K"
    }
  ],
  "parse_status": "success",
  "retrieve_at": "2026-06-11T18:30:00Z"
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ticker | string | Yes | Ticker symbol |
| cik | string | Yes | Company CIK |
| is_biotech | boolean | Yes | Biotech/pharmaceutical classification |
| confidence | string | Yes | HIGH \| MEDIUM \| LOW |
| evidence | object | Yes | Classification evidence |
| clinical_programs | array | No | Detected clinical programs (biotech only) |
| parse_status | string | Yes | success \| partial \| failed |
| retrieve_at | string | Yes | ISO 8601 timestamp |

**Evidence object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sic_code | string \| null | No | SIC code from SEC filings |
| sic_description | string \| null | No | SIC code description |
| sic_match | boolean | Yes | True if SIC code in biotech range (2834-2836) |
| business_description_keywords | array | Yes | Clinical/regulatory keywords found |
| company_name_patterns | array | Yes | Biotech name patterns found |

**Confidence Levels:**
- HIGH: SIC match + keywords + name pattern
- MEDIUM: Any two of three
- LOW: Any one of three

**Note:** Clinical classification planned after CP24F. Schema subject to refinement during implementation.

---

## 10. Synthesis Packet

### Schema: `SynthesisPacket`

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "company_name": "MAIA Biotechnology, Inc.",
  "synthesis_date": "2026-06-11",
  "data_quality_confidence_score": 87.5,
  "scores": {
    "insider_evidence_score": 92.0,
    "dilution_capital_risk_score": 65.0,
    "cash_runway_months": 18.5,
    "clinical_progress_score": 75.0,
    "business_progress_score": null,
    "market_confirmation_score": 0.0
  },
  "evidence_matrix": [
    {
      "category": "Insider Activity",
      "direction": "positive",
      "strength": "strong",
      "confidence": "high",
      "summary": "134 open-market purchases totaling $4.9M over 4 years, 12 distinct buyers"
    },
    {
      "category": "Institutional Ownership",
      "direction": "neutral",
      "strength": "weak",
      "confidence": "medium",
      "summary": "Limited institutional holdings detected, 2 managers with $25M combined"
    },
    {
      "category": "Financial Health",
      "direction": "negative",
      "strength": "moderate",
      "confidence": "high",
      "summary": "$32M cash, 18.5 months runway at current burn rate"
    },
    {
      "category": "Clinical Progress",
      "direction": "positive",
      "strength": "moderate",
      "confidence": "medium",
      "summary": "THIO-101 Phase 2 trial active, preliminary results expected Q3 2026"
    },
    {
      "category": "Capital Structure",
      "direction": "negative",
      "strength": "moderate",
      "confidence": "high",
      "summary": "27.5% dilution overhang from options and warrants"
    }
  ],
  "research_posture": "Strong insider buying signal with moderate clinical progress, offset by limited runway and dilution overhang. No investment recommendation.",
  "limitations": [
    "Form 144 data not yet extracted",
    "Limited institutional 13F holdings detected",
    "Clinical trial data from business description only (no FDA database integration)"
  ],
  "modules": {
    "insider_activity": {
      "status": "success",
      "retrieve_at": "2026-06-11T18:30:00Z"
    },
    "ownership_13dg": {
      "status": "not_implemented",
      "retrieve_at": null
    },
    "ownership_13f": {
      "status": "success",
      "retrieve_at": "2026-06-11T18:30:00Z"
    },
    "financials": {
      "status": "success",
      "retrieve_at": "2026-06-11T18:30:00Z"
    },
    "capital_structure": {
      "status": "success",
      "retrieve_at": "2026-06-11T18:30:00Z"
    },
    "clinical_regulatory": {
      "status": "success",
      "retrieve_at": "2026-06-11T18:30:00Z"
    }
  },
  "safety": {
    "report_only": true,
    "alerts_generated": false,
    "telegram_sent": false,
    "email_sent": false,
    "buy_sell_hold_language_used": false
  },
  "provenance": {
    "source": "SEC EDGAR public filings",
    "retrieve_at": "2026-06-11T18:30:00Z",
    "lookback_days": 1460
  }
}
```

**Field Definitions:**

See existing `schemas/ticker_synthesis_schema.json` for complete schema definition.

---

## 11. Monitoring Plan

### Schema: `MonitoringPlan`

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "plan_date": "2026-06-11",
  "baseline_synthesis_date": "2026-06-11",
  "monitoring_categories": [
    {
      "category": "insider_activity",
      "frequency": "weekly",
      "check_type": "new_form4_filings",
      "baseline_value": 134,
      "alert_trigger": "manual",
      "description": "Monitor for new Form 4 filings indicating open-market purchases or sales"
    },
    {
      "category": "ownership_13f",
      "frequency": "quarterly",
      "check_type": "13f_holdings_change",
      "baseline_value": 1000000,
      "alert_trigger": "manual",
      "description": "Check for changes in institutional holdings after 13F-HR filing deadlines"
    },
    {
      "category": "financial_health",
      "frequency": "quarterly",
      "check_type": "new_10q_filing",
      "baseline_value": 32000000,
      "alert_trigger": "manual",
      "description": "Review quarterly 10-Q for cash balance and burn rate changes"
    },
    {
      "category": "clinical_regulatory",
      "frequency": "monthly",
      "check_type": "trial_updates",
      "baseline_value": "Phase 2 active",
      "alert_trigger": "manual",
      "description": "Monitor for clinical trial updates in 8-K filings or press releases"
    }
  ],
  "safety": {
    "report_only": true,
    "alerts_generated": false
  },
  "provenance": {
    "source": "Synthesis packet baseline",
    "retrieve_at": "2026-06-11T18:30:00Z"
  }
}
```

**Field Definitions:**

See existing `schemas/ticker_monitoring_schema.json` for complete schema definition.

---

## 12. Market Confirmation Checklist

### Schema: `MarketConfirmationPlan`

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "plan_date": "2026-06-11",
  "reference_price_levels": [
    {
      "level_name": "Recent Offering Price",
      "price_usd": 5.00,
      "date": "2025-12-15",
      "source": "8-K filing: Public offering"
    },
    {
      "level_name": "52-Week High",
      "price_usd": 7.25,
      "date": "2025-08-10",
      "source": "Manual observation"
    },
    {
      "level_name": "52-Week Low",
      "price_usd": 3.50,
      "date": "2026-02-20",
      "source": "Manual observation"
    }
  ],
  "observation_template_csv": "date,close_price,volume,notes\n2026-06-11,,,''\n2026-06-18,,,''\n2026-06-25,,,''",
  "weekly_checklist": [
    "Record closing price",
    "Record daily volume",
    "Note any unusual price movements",
    "Check for new SEC filings (8-K, Form 4)",
    "Review news/press releases"
  ],
  "safety": {
    "report_only": true,
    "no_trading_recommendations": true
  },
  "provenance": {
    "source": "SEC filings and manual observation",
    "retrieve_at": "2026-06-11T18:30:00Z"
  }
}
```

**Field Definitions:**

See existing `schemas/ticker_market_confirmation_schema.json` for complete schema definition.

---

## 13. Archive Manifest

### Schema: `ArchiveManifest`

```json
{
  "ticker": "MAIA",
  "cik": "0001878313",
  "archive_date": "2026-06-11T18:30:00Z",
  "extraction_mode": "live",
  "artifacts": [
    {
      "artifact_type": "ticker_resolution",
      "file_name": "MAIA_ticker_resolution.json",
      "file_path": "outputs/generic_ticker/MAIA/ticker_resolution/MAIA_ticker_resolution.json",
      "purpose": "Ticker to CIK resolution",
      "status": "success",
      "sha256": "a1b2c3d4e5f6...",
      "size_bytes": 512,
      "created_at": "2026-06-11T18:25:00Z"
    },
    {
      "artifact_type": "submissions_inventory",
      "file_name": "MAIA_submissions_inventory.json",
      "file_path": "outputs/generic_ticker/MAIA/submissions/MAIA_submissions_inventory.json",
      "purpose": "SEC filing inventory",
      "status": "success",
      "sha256": "b2c3d4e5f6a1...",
      "size_bytes": 45678,
      "created_at": "2026-06-11T18:26:00Z"
    },
    {
      "artifact_type": "form4_insider_activity",
      "file_name": "MAIA_form4_insider_activity.json",
      "file_path": "outputs/generic_ticker/MAIA/insider_activity/MAIA_form4_insider_activity.json",
      "purpose": "Form 4 insider transaction aggregation",
      "status": "success",
      "sha256": "c3d4e5f6a1b2...",
      "size_bytes": 12345,
      "created_at": "2026-06-11T18:27:00Z"
    },
    {
      "artifact_type": "synthesis_packet_json",
      "file_name": "MAIA_synthesis_packet.json",
      "file_path": "outputs/generic_ticker/MAIA/synthesis/MAIA_synthesis_packet.json",
      "purpose": "Complete synthesis packet",
      "status": "success",
      "sha256": "d4e5f6a1b2c3...",
      "size_bytes": 23456,
      "created_at": "2026-06-11T18:29:00Z"
    },
    {
      "artifact_type": "synthesis_packet_markdown",
      "file_name": "MAIA_synthesis_packet.md",
      "file_path": "outputs/generic_ticker/MAIA/synthesis/MAIA_synthesis_packet.md",
      "purpose": "Human-readable synthesis report",
      "status": "success",
      "sha256": "e5f6a1b2c3d4...",
      "size_bytes": 34567,
      "created_at": "2026-06-11T18:29:30Z"
    }
  ],
  "safety_flags": {
    "alerts_generated": false,
    "telegram_sent": false,
    "email_sent": false,
    "buy_sell_hold_language_detected": false
  },
  "data_completeness_score": 87.5,
  "total_artifacts": 12,
  "successful_artifacts": 11,
  "failed_artifacts": 1
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ticker | string | Yes | Ticker symbol |
| cik | string | Yes | Company CIK |
| archive_date | string | Yes | Archive creation timestamp (ISO 8601) |
| extraction_mode | string | Yes | validation \| live |
| artifacts | array | Yes | List of archived artifacts |
| safety_flags | object | Yes | Safety verification flags |
| data_completeness_score | float | Yes | 0-100 completeness metric |
| total_artifacts | integer | Yes | Total artifact count |
| successful_artifacts | integer | Yes | Successful artifact count |
| failed_artifacts | integer | Yes | Failed artifact count |

**Artifact object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| artifact_type | string | Yes | Type identifier |
| file_name | string | Yes | File name |
| file_path | string | Yes | Relative or absolute path |
| purpose | string | Yes | Human-readable description |
| status | string | Yes | success \| partial \| failed \| not_available |
| sha256 | string | Yes | SHA-256 checksum (hex) |
| size_bytes | integer | Yes | File size in bytes |
| created_at | string | Yes | Creation timestamp (ISO 8601) |

---

## 14. Evidence Provenance

### Schema: `EvidenceProvenance`

Embedded in all data structures:

```json
{
  "provenance": {
    "source": "SEC EDGAR Form 4 filings",
    "filing_count": 37,
    "lookback_days": 1460,
    "latest_accession": "0001209191-26-123456",
    "latest_filing_date": "2026-06-01",
    "retrieve_at": "2026-06-11T18:30:00Z",
    "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001878313&type=4"
  }
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| source | string | Yes | Human-readable source description |
| filing_count | integer | No | Number of filings processed (if aggregated) |
| lookback_days | integer | No | Lookback window in days |
| latest_accession | string | No | Most recent accession number |
| latest_filing_date | string | No | Most recent filing date (YYYY-MM-DD) |
| retrieve_at | string | Yes | Extraction timestamp (ISO 8601) |
| source_url | string | Yes | SEC EDGAR source URL |

---

## 15. Error/Degraded-Mode Status

### Schema: `DegradedModeStatus`

Embedded in all module outputs:

```json
{
  "ok": false,
  "parse_status": "partial",
  "error_type": "XML_PARSE_ERROR",
  "error_message": "Failed to parse 3 of 37 Form 4 XML documents due to malformed XML structure",
  "successful_items": 34,
  "failed_items": 3,
  "degraded_fields": ["transactions[12].price_per_share", "transactions[15].price_per_share"],
  "retrieve_at": "2026-06-11T18:30:00Z"
}
```

**Field Definitions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ok | boolean | Yes | Top-level success indicator |
| parse_status | string | Yes | success \| partial \| failed |
| error_type | string \| null | No | Structured error category |
| error_message | string \| null | No | Human-readable error description |
| successful_items | integer | No | Count of successful items |
| failed_items | integer | No | Count of failed items |
| degraded_fields | array | No | List of fields with missing/incomplete data |
| retrieve_at | string | Yes | ISO 8601 timestamp |

**Error Types:**
- TICKER_NOT_FOUND
- CIK_NOT_FOUND
- NETWORK_ERROR
- TIMEOUT
- PARSE_ERROR
- XML_PARSE_ERROR
- MISSING_TAG
- MISSING_OWNER
- MISSING_PRICE
- RATE_LIMIT_EXCEEDED

---

## Summary

This schema document defines **15 comprehensive JSON schemas** covering all extraction outputs in the full SEC extraction pipeline:

1. ✓ Ticker resolution
2. ✓ SEC filing inventory
3. ✓ Form 4 transactions
4. ⚠️ Form 144 filings (planned CP24D)
5. ⚠️ Ownership 13D/G (planned CP24D)
6. ✓ Ownership 13F
7. ⚠️ XBRL financials (planned CP24E)
8. ⚠️ Capital structure (planned CP24F)
9. ⚠️ Clinical/regulatory classification (planned after CP24F)
10. ✓ Synthesis packet
11. ✓ Monitoring plan
12. ✓ Market confirmation checklist
13. ✓ Archive manifest
14. ✓ Evidence provenance
15. ✓ Error/degraded-mode status

**Key Design Principles:**
- All schemas include evidence provenance (source, retrieve_at, source_url)
- All schemas include error handling (ok, parse_status, error_type)
- All monetary values in USD with explicit units
- All dates/timestamps in ISO 8601 format
- Graceful degradation with explicit status tracking

**Status Legend:**
- ✓ Production-ready (existing or well-defined)
- ⚠️ Planned (schema subject to refinement during implementation)
