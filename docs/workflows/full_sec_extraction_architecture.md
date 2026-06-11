# Full SEC Extraction Architecture for Arbitrary Tickers

**Version:** 1.0
**Created:** 2026-06-11
**Checkpoint:** CP24A

---

## 1. Purpose

Design a comprehensive, reusable architecture for extracting SEC EDGAR filing data for any manually supplied equity ticker symbol.

This architecture will replace the current validation-mode placeholders (skeleton data) in the generic ticker workflow with live SEC extraction capabilities.

**Goals:**
- Support arbitrary ticker inputs (not just MAIA/NVDA validation)
- Extract Form 4, Form 144, 13D/G, 13F-HR, and 10-Q/10-K data
- Compose complete synthesis, monitoring, market confirmation, and archive packets
- Maintain safety constraints (no alerts, no recommendations)
- Handle degraded modes gracefully
- Provide evidence provenance for all extracted data

**Non-Goals:**
- Real-time streaming (manual batch execution only)
- Automated alert generation
- Investment recommendations or buy/sell/hold language
- Third-party data integration (OpenInsider, Bloomberg, etc.)

---

## 2. Source Boundary

### Approved Sources

**Exclusively SEC EDGAR public data:**
- SEC EDGAR Full-Text Search (EFTS): efts.sec.gov
- SEC Data API: data.sec.gov
- SEC Archives: sec.gov/Archives/edgar/data/
- Official company filings (Form 4, Form 144, 13D/G, 13F-HR, 10-Q, 10-K)

### Prohibited Sources

- Roger's uploaded MAIA spreadsheet
- OpenInsider data files
- Paid/proprietary databases (Bloomberg, FactSet, etc.)
- Social media/message boards
- Third-party financial aggregators
- Non-SEC government sources (unless explicitly approved)

### Data Authority

SEC EDGAR is the single source of truth. All extracted data must have SEC provenance traceable to:
- Filing accession number
- Filing date
- Document URL
- Issuer CIK

---

## 3. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    TICKER INPUT (Manual CLI)                     │
│                     e.g., "NVDA", "AAPL"                         │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TICKER/CIK RESOLUTION                           │
│            (sec_ticker.py → company_tickers.json)                │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              SEC SUBMISSIONS INVENTORY                           │
│          (sec_submissions.py → CIK{cik}.json)                    │
│         Returns: Filing history, accession numbers               │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
         ┌───────────────┴───────────────┐
         ▼                               ▼
┌──────────────────┐           ┌──────────────────┐
│  INSIDER FILINGS │           │  OWNERSHIP/13F   │
│   (Form 4/144)   │           │   (13D/G, 13F)   │
└────────┬─────────┘           └────────┬─────────┘
         ▼                               ▼
┌──────────────────┐           ┌──────────────────┐
│  Form 4 Parser   │           │  13F Matcher     │
│ (sec_form4       │           │ (sec_13f         │
│  _details.py)    │           │  _matcher.py)    │
└────────┬─────────┘           └────────┬─────────┘
         └───────────────┬───────────────┘
                         ▼
         ┌───────────────────────────────┐
         │   FINANCIAL EXTRACTION        │
         │    (10-Q/10-K XBRL)           │
         │  (Planned: CP24E)             │
         └───────────────┬───────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              CAPITAL STRUCTURE / DILUTION                        │
│          (Planned: CP24F - Extract from filings)                 │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            CLINICAL/REGULATORY CLASSIFIER                        │
│      (Planned: Detect biotech from business description)         │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 SYNTHESIS COMPOSER                               │
│          (ticker_synthesis_workflow.py)                          │
│       Merges: insider, ownership, financials, clinical           │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
         ┌───────────────┴───────────────┬───────────────┐
         ▼                               ▼               ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Monitoring Pack │    │ Market Confirm   │    │   Archive    │
│   (ticker_       │    │   Checklist      │    │   Packager   │
│   monitoring     │    │  (ticker_market  │    │  (ticker_    │
│   _pack.py)      │    │  _confirmation)  │    │  archive)    │
└──────────────────┘    └──────────────────┘    └──────────────┘
```

---

## 4. Data Flow

### Phase 1: Ticker Resolution
**Input:** Ticker symbol (string, e.g., "NVDA")
**Process:**
1. Normalize ticker (uppercase, strip whitespace)
2. Fetch SEC company_tickers.json (cached 7 days)
3. Lookup ticker → CIK mapping
4. Validate CIK exists

**Output:** `TickerCikResult` (ok, ticker, cik, cik_padded, company_name, error_type)

**Error Modes:**
- TICKER_NOT_FOUND → Cannot proceed, report to user
- NETWORK_ERROR → Retry with backoff, fail after max retries
- CACHE_MISS → Fetch fresh data

---

### Phase 2: SEC Submissions Inventory
**Input:** CIK (zero-padded 10-digit string)
**Process:**
1. Fetch data.sec.gov/submissions/CIK{cik}.json (cached 24h)
2. Parse parallel arrays (accessionNumber[], filingDate[], form[], etc.)
3. Filter by lookback window (default: 1460 days = 4 years)
4. Construct filing URLs from accession numbers

**Output:** `List[SecSubmissionFiling]` with:
- accession_number (unique filing ID)
- form (4, 144, 13D, 13G, 13F-HR, 10-Q, 10-K, etc.)
- filing_date
- primary_document filename
- archive_directory_url
- primary_document_url

**Error Modes:**
- CIK_NOT_FOUND → Degraded mode: mark all filings as not_available
- NETWORK_ERROR → Retry logic
- PARSE_ERROR → Skip malformed filings, continue with valid ones

---

### Phase 3: Form 4 Extraction (Insider Trading)
**Input:** List of Form 4 accession numbers from submissions inventory
**Process:**
1. For each Form 4 filing:
   a. Fetch primary document (XML embedded in .txt or standalone .xml)
   b. Parse XML to extract reporting owners and transactions
   c. Classify transactions (P/S/M/A/F/G/D codes)
   d. Calculate transaction values (shares × price)
   e. Extract post-transaction holdings

**Output:** `List[Form4FilingDetails]` with:
- owners[] (name, CIK, roles: director/officer/10% owner)
- transactions[] (date, code, shares, price, value, classification)
- parse_status (success/partial/failed)

**Aggregation:**
- Sum open-market purchases (code=P)
- Sum open-market sales (code=S)
- Calculate net purchase value (purchases - sales)
- Count distinct buyers/sellers
- Identify latest purchase/sale dates
- Calculate insider evidence score (0-100)

**Error Modes:**
- XML_PARSE_ERROR → parse_status=failed, continue with other filings
- MISSING_OWNER → Partial success, extract transactions anyway
- MISSING_PRICE → Set value to 0.0, flag as incomplete

---

### Phase 4: Form 144 Extraction (Resale Registration)
**Input:** List of Form 144 accession numbers
**Process:**
1. Fetch filing metadata
2. Extract reporting person, shares proposed for sale, sale date

**Output:** `List[Form144Filing]` with:
- reporting_person
- shares_proposed
- proposed_sale_date

**Note:** Implementation planned for CP24D

---

### Phase 5: 13D/G Extraction (Beneficial Ownership)
**Input:** List of 13D/13G accession numbers
**Process:**
1. Fetch filing text
2. Extract beneficial owner identity, ownership percentage, shares held

**Output:** `List[Ownership13DG]` with:
- filer_name
- filer_cik
- shares_held
- percent_of_class

**Note:** Implementation planned for CP24D

---

### Phase 6: 13F-HR Matching (Institutional Holdings)
**Input:**
- Ticker-resolved company name and CIK
- Holdings data from institutional managers (already extracted via sec_13f.py)

**Process:**
1. For each manager (Berkshire, Bridgewater, Renaissance, etc.):
   a. Fetch latest 13F-HR filing
   b. Parse InfoTable XML/HTML
   c. Extract holdings (CUSIP, issuer name, value, shares)
2. Match ticker to holdings:
   a. CUSIP exact match (if available)
   b. Issuer name exact match
   c. Normalized name match (remove Inc/Corp/Ltd suffixes)

**Output:** `List[HoldingMatchResult]` with:
- manager_name
- value_usd_thousands
- shares
- confidence (EXACT_CUSIP, EXACT_ISSUER_NAME, NORMALIZED_ISSUER_NAME)

**Note:** Integration planned for CP24G

---

### Phase 7: 10-Q/10-K XBRL Financial Extraction
**Input:** List of 10-Q/10-K accession numbers
**Process:**
1. Fetch XBRL instance document
2. Parse financial statements:
   - Cash and cash equivalents
   - Total assets
   - Total liabilities
   - Working capital
   - Revenue
   - Operating cash flow
   - R&D expenses (if applicable)

**Output:** `XBRLFinancials` with:
- report_period
- cash_balance_usd
- total_assets_usd
- working_capital_usd
- quarterly_revenue_usd
- quarterly_operating_cash_flow_usd
- quarterly_rd_expense_usd

**Note:** Implementation planned for CP24E

---

### Phase 8: Capital Structure / Dilution Extraction
**Input:** Latest 10-Q/10-K, DEF 14A proxy statements
**Process:**
1. Extract from financials/notes:
   - Common shares outstanding
   - Stock options outstanding
   - Warrants outstanding
   - Convertible securities
2. Calculate:
   - Approximate fully diluted shares
   - Dilution overhang percentage

**Output:** `CapitalStructure` with:
- common_shares_outstanding
- stock_options
- warrants
- approximate_fully_diluted
- dilution_overhang_percent

**Note:** Implementation planned for CP24F

---

### Phase 9: Clinical/Regulatory Classifier
**Input:** Business description from 10-K, SIC code, company name
**Process:**
1. Detect keywords: "clinical trial", "Phase 1/2/3", "FDA", "biologics", "therapeutics"
2. Check SIC code ranges (2834-2836: Pharmaceutical Preparations)
3. Match company name patterns ("Therapeutics", "Pharma", "Bio", etc.)

**Output:** `ClinicalClassification` with:
- is_biotech (bool)
- confidence (HIGH/MEDIUM/LOW)
- evidence (keywords found, SIC match, name match)

**Note:** Implementation planned after CP24F

---

### Phase 10: Synthesis Composer
**Input:** All extracted modules
**Process:**
1. Merge insider activity, ownership, financials, clinical data
2. Calculate synthesis scores:
   - insider_evidence_score (0-100)
   - dilution_capital_risk_score (0-100)
   - cash_runway_score (months remaining)
   - clinical_progress_score (biotech only)
   - business_progress_score (non-biotech)
   - data_quality_confidence_score (completeness metric)
   - market_confirmation_score (manual tracking readiness)
3. Compose evidence matrix (category, direction, strength, confidence)
4. Generate overall research posture (descriptive, non-recommendation)

**Output:** `SynthesisPacket` (JSON + Markdown)

**Note:** Already implemented (ticker_synthesis_workflow.py), needs live data integration

---

### Phase 11: Monitoring Pack Composer
**Input:** Synthesis packet
**Process:**
1. Establish baseline values from synthesis
2. Define monitoring categories:
   - insider_activity (weekly check for new Form 4s)
   - ownership_13f (quarterly check for 13F holdings changes)
   - financial_health (quarterly check for new 10-Qs)
   - clinical_regulatory (biotech only: monitor trial updates)
3. Define alert triggers (manual, no automation)

**Output:** `MonitoringPlan` (JSON + Markdown)

---

### Phase 12: Market Confirmation Checklist Composer
**Input:** Synthesis packet, latest market price (if available)
**Process:**
1. Identify reference price levels (e.g., recent offering price, 52-week high/low)
2. Generate weekly observation checklist
3. Create CSV template for manual price/volume entry

**Output:** `MarketConfirmationPlan` (JSON + Markdown + CSV)

---

### Phase 13: Archive Packager
**Input:** All synthesis, monitoring, market confirmation outputs
**Process:**
1. Collect all output files
2. Calculate SHA-256 checksums for each artifact
3. Generate manifest with:
   - artifact metadata (name, type, path, purpose, status)
   - checksums
   - safety flags
   - timestamp

**Output:** `ArchiveManifest` (JSON + index Markdown)

---

## 5. Module Design

### 5.1 Ticker Resolver

**Module:** `sources/sec_ticker.py`
**Status:** ✓ Production-ready (100% generic)

**Interface:**
```python
def resolve_ticker_to_cik(ticker: str) -> TickerCikResult:
    """
    Resolve equity ticker to SEC CIK.

    Returns:
        TickerCikResult with ok, ticker, cik, cik_padded, company_name, error_type
    """
```

**Caching:** 7 days (company_tickers.json refreshed weekly)

**Error Handling:**
- TICKER_NOT_FOUND → Return ok=False, error_type="TICKER_NOT_FOUND"
- NETWORK_ERROR → Retry with exponential backoff
- PARSE_ERROR → Return ok=False, error_type="PARSE_ERROR"

---

### 5.2 CIK Resolver

**Module:** Same as Ticker Resolver (sec_ticker.py)
**Status:** ✓ Already handles CIK zero-padding

**Note:** CIK is 10-digit zero-padded string (e.g., "0001045810" for NVDA)

---

### 5.3 Submissions Fetcher

**Module:** `sources/sec_submissions.py`
**Status:** ✓ Production-ready (100% generic)

**Interface:**
```python
def get_form4_filings_for_cik(cik: str, lookback_days: int = 1460) -> List[SecSubmissionFiling]:
    """
    Fetch Form 4 filings for CIK within lookback window.

    Returns:
        List of SecSubmissionFiling with accession, filing_date, urls
    """
```

**Caching:** 24 hours (submissions JSON refreshed daily)

**Extensibility:** Add similar functions for Form 144, 13D/G, 10-Q/10-K

---

### 5.4 Form 4 Extractor/Parser

**Modules:**
- `sources/sec_form4.py` (metadata discovery)
- `sources/sec_form4_details.py` (XML parsing)

**Status:** ✓ Production-ready (100% generic)

**Interface:**
```python
def fetch_and_parse_form4(accession_number: str, cik: str, primary_document: str) -> Form4FilingDetails:
    """
    Fetch and parse Form 4 XML to extract owners and transactions.

    Returns:
        Form4FilingDetails with owners[], transactions[], parse_status
    """
```

**Fallback Strategies:**
1. Submission text file with embedded XML
2. Primary document URL
3. Accession-based XML path

**Error Handling:**
- XML_PARSE_ERROR → parse_status="failed", error logged
- MISSING_PRICE → Set transaction value to 0.0, flag incomplete
- PARTIAL_SUCCESS → parse_status="partial", return extracted data

---

### 5.5 Form 144 Extractor/Parser

**Module:** `sources/sec_form144.py` (planned)
**Status:** ⚠️ NOT YET IMPLEMENTED (planned for CP24D)

**Planned Interface:**
```python
def fetch_and_parse_form144(accession_number: str, cik: str) -> Form144FilingDetails:
    """
    Fetch and parse Form 144 to extract proposed sale details.

    Returns:
        Form144FilingDetails with reporting_person, shares_proposed, sale_date
    """
```

---

### 5.6 13D/G Extractor/Parser

**Module:** `sources/sec_13dg.py` (planned)
**Status:** ⚠️ NOT YET IMPLEMENTED (planned for CP24D)

**Planned Interface:**
```python
def fetch_and_parse_13dg(accession_number: str, cik: str) -> Ownership13DGDetails:
    """
    Fetch and parse 13D/13G to extract beneficial ownership.

    Returns:
        Ownership13DGDetails with filer_name, shares_held, percent_of_class
    """
```

---

### 5.7 13F InfoTable Matcher

**Modules:**
- `sources/sec_13f.py` (manager filing discovery)
- `sources/sec_13f_parser.py` (InfoTable XML/HTML parsing)
- `sources/sec_13f_matcher.py` (issuer matching)

**Status:** ✓ Production-ready (80% generic, needs manager list config)

**Interface:**
```python
def match_ticker_to_13f_holdings(
    ticker: str,
    resolved_company_name: str,
    resolved_cik: str,
    holdings: List[Form13FHolding],
    cusip: str | None = None
) -> List[HoldingMatchResult]:
    """
    Match ticker-resolved issuer to 13F holdings.

    Returns:
        List of HoldingMatchResult with manager, value, shares, confidence
    """
```

**Matching Priority:**
1. CUSIP exact match (highest confidence)
2. Exact issuer name match
3. Normalized issuer name match (remove Inc/Corp/Ltd)
4. Fuzzy substring match (optional, not used in final results)

---

### 5.8 10-Q/10-K XBRL Financial Extractor

**Module:** `sources/sec_xbrl_financials.py` (planned)
**Status:** ⚠️ NOT YET IMPLEMENTED (planned for CP24E)

**Planned Interface:**
```python
def fetch_and_parse_xbrl_financials(accession_number: str, cik: str) -> XBRLFinancials:
    """
    Fetch and parse XBRL instance document to extract financials.

    Returns:
        XBRLFinancials with cash, assets, liabilities, revenue, cash_flow, etc.
    """
```

**XBRL Tags to Extract:**
```
us-gaap:CashAndCashEquivalentsAtCarryingValue
us-gaap:Assets
us-gaap:Liabilities
us-gaap:WorkingCapital
us-gaap:Revenues
us-gaap:NetCashProvidedByUsedInOperatingActivities
us-gaap:ResearchAndDevelopmentExpense
```

---

### 5.9 Capital Structure/Dilution Extractor

**Module:** `sources/sec_capital_structure.py` (planned)
**Status:** ⚠️ NOT YET IMPLEMENTED (planned for CP24F)

**Planned Interface:**
```python
def extract_capital_structure(accession_10q: str, cik: str) -> CapitalStructure:
    """
    Extract capital structure from 10-Q/10-K notes.

    Returns:
        CapitalStructure with shares_outstanding, options, warrants, dilution
    """
```

**Sources:**
- 10-Q/10-K: Note on shares outstanding, equity compensation plan table
- DEF 14A: Proxy statement equity compensation disclosures

---

### 5.10 Clinical/Regulatory Classifier

**Module:** `sources/sec_clinical_classifier.py` (planned)
**Status:** ⚠️ NOT YET IMPLEMENTED (planned after CP24F)

**Planned Interface:**
```python
def classify_biotech_status(
    business_description: str,
    sic_code: str,
    company_name: str
) -> ClinicalClassification:
    """
    Detect if company is biotech/pharmaceutical.

    Returns:
        ClinicalClassification with is_biotech, confidence, evidence
    """
```

**Detection Rules:**
1. SIC codes 2834-2836 → HIGH confidence biotech
2. Keywords in business description → MEDIUM confidence
3. Company name patterns → LOW confidence
4. All three → HIGH confidence

---

### 5.11 Synthesis Composer

**Module:** `scripts/ticker_synthesis_workflow.py`
**Status:** ✓ Skeleton implemented, needs live data integration (CP24H)

**Current State:**
- Validation mode: MAIA/NVDA skeleton data
- Live mode: Placeholder (raises NotImplementedError)

**CP24H Goal:**
Replace `extract_sec_data()` placeholder with:
```python
def extract_sec_data(ticker: str, cik: str) -> dict:
    # Phase 1: Ticker/CIK resolution (already have CIK)
    # Phase 2: Submissions inventory
    submissions = get_all_filings_for_cik(cik, lookback_days=1460)

    # Phase 3-6: Extract filings
    form4_data = extract_form4_data(submissions.form4_filings)
    form144_data = extract_form144_data(submissions.form144_filings)
    ownership_13dg = extract_13dg_data(submissions.dg_filings)
    ownership_13f = match_ticker_to_13f(ticker, cik)
    xbrl_financials = extract_xbrl_data(submissions.tenq_filings)
    capital_structure = extract_capital_structure(submissions.tenq_filings)

    # Phase 7: Clinical classification
    clinical = classify_biotech(xbrl_financials.business_description)

    # Phase 8: Compose synthesis packet
    return compose_synthesis(
        ticker=ticker,
        cik=cik,
        insider=form4_data,
        ownership_13dg=ownership_13dg,
        ownership_13f=ownership_13f,
        financials=xbrl_financials,
        capital=capital_structure,
        clinical=clinical
    )
```

---

### 5.12 Monitoring Pack Composer

**Module:** `scripts/ticker_monitoring_pack.py`
**Status:** ✓ Skeleton implemented, needs live baseline integration

**CP24H Goal:**
Replace `generate_monitoring_plan()` to consume live synthesis data instead of validation-mode baselines.

---

### 5.13 Market Confirmation Checklist Composer

**Module:** `scripts/ticker_market_confirmation_checklist.py`
**Status:** ✓ Skeleton implemented, needs reference price integration

**CP24H Goal:**
Derive reference price levels from:
- Recent offering price (if available in filings)
- 52-week high/low (manual entry or external API if approved)
- Current market price (manual entry)

---

### 5.14 Archive Packager

**Module:** `scripts/ticker_archive_packet.py`
**Status:** ✓ Production-ready (100% generic)

**Note:** Already calculates SHA-256 checksums, no changes needed.

---

## 6. Error Handling and Degraded-Mode Behavior

### Graceful Degradation Principles

1. **Partial success is acceptable**: If Form 4 parsing succeeds but 13F matching fails, synthesis packet includes Form 4 data with 13F marked "not_available"
2. **Evidence provenance required**: Every data point must trace to a specific SEC filing
3. **Explicit error types**: Use structured error_type fields (NETWORK_ERROR, PARSE_ERROR, NOT_FOUND, TIMEOUT)
4. **No silent failures**: All errors logged and surfaced in synthesis limitations[]

### Error Modes by Phase

| Phase | Error Type | Degraded Behavior |
|-------|------------|-------------------|
| Ticker resolution | TICKER_NOT_FOUND | STOP: Cannot proceed without CIK |
| Submissions fetch | NETWORK_ERROR | Retry 3 times, then fail |
| Form 4 parse | XML_PARSE_ERROR | Mark parse_status=failed, continue |
| 13F match | NO_MATCHES | Set ownership_13f=[] (empty, not error) |
| XBRL parse | MISSING_TAG | Set field to None, flag incomplete |
| Capital structure | PARSE_ERROR | Set all fields to None, note unavailable |

### Status Tracking

Every module returns a status indicator:
```python
ok: bool                           # Top-level success/failure
parse_status: str | None           # success | partial | failed
error_type: str | None             # Category for debugging
error_message: str | None          # Human-readable description
retrieve_at: str                   # ISO 8601 timestamp
```

### Synthesis Packet Degraded Modes

**Best case:** All modules succeed, data_quality_confidence_score = 90-100
**Partial:** Some modules fail, data_quality_confidence_score = 50-89
**Minimal:** Only ticker/CIK resolution succeeds, data_quality_confidence_score = 10-49
**Failure:** Cannot resolve ticker, data_quality_confidence_score = 0

---

## 7. Evidence Provenance Model

Every data point in the synthesis packet must include provenance:

```json
{
  "data_point": "open_market_purchases",
  "value": 134,
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

**Required Fields:**
- source (human-readable description)
- retrieve_at (ISO 8601 timestamp)
- source_url (SEC EDGAR link)

**Optional but Recommended:**
- accession_number (unique filing ID)
- filing_date
- filing_count (if aggregated)
- lookback_days

---

## 8. JSON Schema Outputs

All outputs conform to JSON schemas defined in `schemas/`:

1. **ticker_resolution** → `TickerCikResult`
2. **sec_filing_inventory** → `List[SecSubmissionFiling]`
3. **form4_transactions** → `List[Form4FilingDetails]`
4. **form144_filings** → `List[Form144Filing]` (planned)
5. **ownership_13dg** → `List[Ownership13DG]` (planned)
6. **ownership_13f** → `List[HoldingMatchResult]`
7. **xbrl_financials** → `XBRLFinancials` (planned)
8. **capital_structure** → `CapitalStructure` (planned)
9. **clinical_regulatory** → `ClinicalClassification` (planned)
10. **synthesis_packet** → Defined in `schemas/ticker_synthesis_schema.json`
11. **monitoring_plan** → Defined in `schemas/ticker_monitoring_schema.json`
12. **market_confirmation** → Defined in `schemas/ticker_market_confirmation_schema.json`
13. **archive_manifest** → Custom schema with SHA-256 checksums

---

## 9. Test Fixture Strategy

### Unit Tests

Use **synthetic minimal fixtures** for parsing logic:
```python
# Example: Form 4 XML with single transaction
MINIMAL_FORM4_XML = """<ownershipDocument>
  <reportingOwner>...</reportingOwner>
  <nonDerivativeTransaction>...</nonDerivativeTransaction>
</ownershipDocument>"""
```

### Integration Tests

Use **real SEC filing samples** (saved locally):
```python
# Example: Actual MAIA Form 4 XML from accession 0001209191-24-012345
REAL_MAIA_FORM4_PATH = "tests/fixtures/sec/maia_form4_2024_06_01.xml"
```

### Regression Tests

Use **MAIA and NVDA as validation baselines**:
- MAIA: Biotech, clinical trials, pre-revenue
- NVDA: Large cap, operating company, revenue-positive

**Regression criteria:**
- MAIA Form 4 aggregation should match approved baseline (134 purchases, $4.9M)
- NVDA clinical module should be "not_applicable"

### Network-Safe Tests

**Use mocking for HTTP calls:**
```python
@patch('sources.sec_common.sec_fetch')
def test_ticker_resolution_network_error(mock_fetch):
    mock_fetch.side_effect = Exception("Network timeout")
    result = resolve_ticker_to_cik("TEST")
    assert result.ok is False
    assert result.error_type == "NETWORK_ERROR"
```

### No-Network Tests

**Use cached fixtures:**
```python
def test_form4_parse_offline():
    with open("tests/fixtures/form4.xml") as f:
        xml = f.read()
    result = parse_form4_xml(xml, "0001209191-24-012345", "test_url")
    assert result.parse_status == "success"
```

---

## 10. Security/Safety Model

### No Alert Generation

- All scripts operate in **report-only mode**
- No Telegram/email sending capabilities in SEC extraction modules
- Safety flags enforced: `alerts_generated: false`

### No Investment Recommendations

- Synthesis packet contains **descriptive analysis only**
- Prohibited language: buy, sell, hold, strong buy, accumulate, reduce
- Evidence matrix uses neutral terms: direction (positive/negative/neutral), strength (strong/moderate/weak)
- Overall posture is descriptive: "Strong insider buying" (not "Recommended buy")

### Secret Management

- SEC_USER_AGENT required (email-based User-Agent string)
- No API keys embedded in code
- .env loading via python-dotenv
- Secrets never logged or printed

### Rate Limiting Compliance

- Minimum 200ms between SEC requests (max 5 req/sec)
- Exponential backoff on retries
- Respect SEC fair-access policy

### Caching for Efficiency

- Cache frequently accessed data (company_tickers.json, submissions)
- Cache key: SHA256(url)
- TTL: Conservative defaults (7d tickers, 24h submissions, 1h Form 4)

---

## 11. No-Alert/No-Recommendation Policy

### Enforcement Mechanisms

1. **Safety flags in every output:**
```json
{
  "safety": {
    "report_only": true,
    "alerts_generated": false,
    "telegram_sent": false,
    "email_sent": false,
    "buy_sell_hold_language_used": false
  }
}
```

2. **Automated tests:**
```python
def test_no_recommendation_language():
    synthesis = generate_synthesis_packet("NVDA")
    text = json.dumps(synthesis).lower()
    assert "buy" not in text or "should buy" not in text
    assert "sell" not in text or "should sell" not in text
```

3. **Code review checklist:**
- No alert connectors imported
- No Telegram/email modules imported
- No buy/sell/hold terms in output strings

---

## 12. Known Limitations

### Current Limitations (CP24A - Design Phase)

1. **No live SEC extraction yet**: Full extraction planned for CP24B-H
2. **XBRL parsing not implemented**: 10-Q/10-K financials planned for CP24E
3. **Capital structure extraction manual**: Planned for CP24F
4. **Clinical classifier basic**: Keyword-based only, no NLP
5. **13F manager list hardcoded**: Berkshire, Bridgewater, Renaissance, Citadel, Two Sigma
6. **No real-time market data**: Manual price/volume entry required
7. **CIK lookup requires exact ticker match**: No fuzzy matching
8. **Form 144 and 13D/G not yet implemented**: Planned for CP24D

### Permanent Limitations (By Design)

1. **Manual ticker input only**: No automated ticker discovery
2. **No alerting/automation**: Report-only mode
3. **No third-party data**: SEC EDGAR only
4. **No investment advice**: Descriptive analysis only
5. **No real-time updates**: Batch execution, manual triggering
6. **No historical trend analysis**: Point-in-time snapshots only

### Future Enhancements (Out of Scope for CP24)

1. Automated ticker watchlist monitoring
2. Historical trending (multi-period comparison)
3. Peer company benchmarking
4. Real-time market data integration
5. Advanced NLP for business classification
6. Sentiment analysis from MD&A sections

---

## Summary

This architecture provides a **comprehensive, modular, and extensible foundation** for extracting SEC EDGAR data for arbitrary tickers.

**Key Strengths:**
- Reuses 100% of existing SEC modules (2357 lines of production-ready code)
- Graceful degradation at every phase
- Evidence provenance for all data points
- Safety-first design (no alerts, no recommendations)
- Test-driven with fixtures and regression baselines

**Implementation Path:**
CP24A → CP24B → CP24C → CP24D → CP24E → CP24F → CP24G → CP24H → CP24I → CP24J

**Estimated Complexity:**
- CP24B-D: Medium (extend existing modules)
- CP24E-F: High (new XBRL/capital structure parsing)
- CP24G-H: Low (integration of existing components)
- CP24I-J: Low (validation and documentation)

**Ready for PM approval to proceed with CP24B.**
