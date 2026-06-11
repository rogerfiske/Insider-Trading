# Generic Ticker Synthesis Workflow

**Checkpoint:** CP23C
**Status:** Framework skeleton with MAIA validation
**Purpose:** Generalize the MAIA-specific SEC-only synthesis workflow for reuse with any manually supplied ticker

## Overview

The generic ticker synthesis workflow provides a reusable framework for generating comprehensive SEC-only research packets for any ticker. It builds on the approved MAIA workflow (CP23D-CP23H) and generalizes it for broader application.

## Source Boundary

**Approved sources:**
- SEC EDGAR public filings only
- Company official investor relations pages (ticker-specific use only)
- ClinicalTrials.gov/FDA public pages (biotech profile only)
- Project-approved reports as design references

**Prohibited sources:**
- Roger's uploaded MAIA spreadsheet
- OpenInsider data supplied by Roger
- Paid/private/non-project sources
- Message board claims
- Uncited social media
- Third-party financial summaries as source of truth

## Workflow Components

### 1. Synthesis Packet (`ticker_synthesis_workflow.py`)

**Purpose:** Generate comprehensive SEC-only research packet

**Modules:**
- `insider_activity` - Form 4 filings, insider purchases/sales, scoring
- `capital_structure` - Shares outstanding, dilution, recent offerings
- `cash_runway` - 10-Q financials, cash burn scenarios (pre-revenue companies)
- `ownership_13dg` - Form 13D/13G beneficial ownership
- `ownership_13f` - Form 13F institutional holdings (45-day lag, partial visibility)
- `form_144` - Insider sale intent notifications
- `clinical_regulatory` - Clinical programs, milestones (biotech profile only)
- `business_operations` - Revenue, milestones (operating companies only)
- `market_confirmation` - Manual tracking framework (no live data)

**Evidence Matrix:**
- Insider buying strength
- Insider selling absence/presence
- Buyer/seller breadth
- Recency and persistence
- Capital raise / cash position
- Dilution overhang
- Cash runway / liquidity
- 13D/G and 13F ownership
- Form 144 selling intent
- Market confirmation
- Financing risk before catalyst

**Synthesis Scores:**
- Insider evidence score (0-100)
- Dilution/capital risk score
- Cash/liquidity score
- Clinical/business progress score
- Data quality/confidence score
- Market confirmation score
- **Overall research posture** (NO buy/sell/hold language)

**Allowed posture labels:**
- "Strong insider-evidence / high uncertainty profile"
- "Strong insider-evidence / improving confirmation profile"
- "Mixed evidence / moderate uncertainty profile"
- "Weak insider-evidence / incomplete data profile"
- "Incomplete evidence / high uncertainty profile"

**Prohibited language:**
- buy, sell, hold
- price target, expected return
- recommendation, rating (except insider rating)

### 2. Monitoring Plan (`ticker_monitoring_pack.py`)

**Purpose:** Generate ongoing monitoring checklist from synthesis

**Categories:**
- Insider Activity (Form 4) - weekly
- SEC Filings (8-K, 10-Q, 10-K) - as filed
- Press Releases - as issued
- Equity Offerings (S-3, 424B) - as filed
- Clinical Trials - weekly (biotech only)
- Market Price/Volume - daily (manual entry)

### 3. Market Confirmation Checklist (`ticker_market_confirmation_checklist.py`)

**Purpose:** Manual framework for tracking market behavior vs. insider evidence

**Components:**
- Baseline summary from synthesis
- Reference price levels (offering price, 52-week high/low)
- Weekly checklist (price relative to reference, volume patterns, technical signals)
- CSV observation template for manual data entry
- Status labels (confirmation, neutral, contradiction)
- Automation gaps documentation

### 4. Archive Packet (`ticker_archive_packet.py`)

**Purpose:** Create distributable research archive with integrity verification

**Components:**
- Archive manifest with SHA-256 checksums
- Archive index
- README (planned)
- ZIP archive (optional, requires external tool)

## CLI Usage

### Synthesis Workflow

```powershell
# MAIA validation mode (uses existing approved data)
.\.venv\Scripts\python.exe scripts\ticker_synthesis_workflow.py `
    --ticker MAIA `
    --mode validation `
    --profile biotech_clinical `
    --output-dir docs/sample_reports/generic_ticker/MAIA

# Live SEC extraction mode (NOT YET IMPLEMENTED)
.\.venv\Scripts\python.exe scripts\ticker_synthesis_workflow.py `
    --ticker XYZ `
    --cik 0001234567 `
    --lookback-days 1460 `
    --profile small_cap_operating_company `
    --mode live `
    --output-dir docs/sample_reports/generic_ticker/XYZ
```

### Monitoring Pack

```powershell
.\.venv\Scripts\python.exe scripts\ticker_monitoring_pack.py `
    --ticker MAIA `
    --mode validation `
    --input-dir docs/sample_reports/generic_ticker/MAIA `
    --output-dir docs/sample_reports/generic_ticker/MAIA
```

### Market Confirmation

```powershell
.\.venv\Scripts\python.exe scripts\ticker_market_confirmation_checklist.py `
    --ticker MAIA `
    --mode validation `
    --input-dir docs/sample_reports/generic_ticker/MAIA `
    --output-dir docs/sample_reports/generic_ticker/MAIA
```

### Archive Packet

```powershell
.\.venv\Scripts\python.exe scripts\ticker_archive_packet.py `
    --ticker MAIA `
    --cik 0001878313 `
    --mode validation `
    --input-dir docs/sample_reports/generic_ticker/MAIA `
    --output-dir docs/sample_reports/generic_ticker/MAIA/archive
```

## Output Structure

For ticker `<TICKER>`, outputs are organized as:

```
docs/sample_reports/generic_ticker/<TICKER>/
├── synthesis/
│   ├── <TICKER>_synthesis_packet.json
│   └── <TICKER>_synthesis_packet.md
├── monitoring/
│   ├── <TICKER>_monitoring_plan.json
│   └── <TICKER>_monitoring_plan.md
├── market_confirmation/
│   ├── <TICKER>_market_confirmation_plan.json
│   ├── <TICKER>_market_confirmation_checklist.md
│   └── <TICKER>_market_observation_template.csv
└── archive/
    ├── <TICKER>_archive_manifest.json
    └── <TICKER>_archive_index.md
```

## JSON Schemas

Schema definitions located in `schemas/`:
- `ticker_synthesis_schema.json` - Synthesis packet structure
- `ticker_monitoring_schema.json` - Monitoring plan structure
- `ticker_market_confirmation_schema.json` - Market confirmation structure

## Ticker Profile Types

| Profile | Clinical Module | Business Module | Cash Runway Focus |
|---------|----------------|-----------------|-------------------|
| `biotech_clinical` | Required | N/A | Critical (pre-revenue) |
| `small_cap_operating_company` | N/A | Required | Liquidity/going concern |
| `pre_revenue_company` | N/A | Required | Critical |
| `unknown_profile` | Optional | Optional | Conditional |

## Scoring Framework

### Insider Evidence Score (0-100)

- **100:** Purchases > 0, sales = 0
- **85:** Purchases > 3× sales, value > 3× sale value
- **70:** Purchases > sales, value > sale value
- **50:** Balanced activity
- **<30:** Sales dominate

### Risk Scores

Dilution, cash runway, and progress scores use domain-specific criteria.

### Overall Posture

Combines insider score, cash runway, catalyst timing to produce descriptive (not prescriptive) label.

## MAIA Validation

MAIA serves as the validation ticker because it has approved baseline values.

**Preserved MAIA values:**
- Insider purchases: 134
- Insider sales: 0
- Purchase value: $4,921,437.58
- Distinct buyers: 10
- Latest purchase date: 2026-06-01
- Cash balance: $34,413,110
- Working capital: $28,992,690
- Operating cash burn (quarterly): $5,311,328
- Base runway: 19.4 months
- Offering reference price: $1.50
- Common shares outstanding: 60,671,491
- Approximate fully diluted shares: ~86.86M
- 13F visibility: partial; no MAIA matches among parsed filings
- Critical unknown: THIO-104 Phase 3 timing not disclosed

**Validation command:**
```powershell
.\.venv\Scripts\python.exe scripts\ticker_synthesis_workflow.py `
    --ticker MAIA --mode validation --profile biotech_clinical `
    --output-dir docs/sample_reports/generic_ticker/MAIA
```

The script validates that all baseline values are preserved.

## NVDA Second Validation (CP23I)

NVDA serves as the second validation ticker to verify the generic framework handles non-biotech companies correctly.

**Purpose:**
- Confirm framework works for non-biotech ticker profiles
- Verify clinical/regulatory module correctly set to `not_applicable`
- Confirm MAIA-specific values do not leak into NVDA outputs
- Validate safety flags, no buy/sell/hold language
- Demonstrate market confirmation and archive outputs for non-biotech ticker

**NVDA validation characteristics:**
- Ticker: NVDA
- Profile: `unknown_profile` (not biotech)
- Clinical/regulatory module: `not_applicable`
- All insider/financial data: `not_available` (skeleton mode)
- No MAIA-specific values: No $1.50, no 134 purchases, no THIO references
- Not an investment analysis: Framework validation only

**Validation commands:**
```powershell
# Synthesis
python scripts/ticker_synthesis_workflow.py `
    --ticker NVDA --mode validation --profile unknown_profile `
    --output-dir docs/sample_reports/generic_ticker/NVDA

# Monitoring
python scripts/ticker_monitoring_pack.py `
    --ticker NVDA --mode validation `
    --input-dir docs/sample_reports/generic_ticker/NVDA `
    --output-dir docs/sample_reports/generic_ticker/NVDA

# Market confirmation
python scripts/ticker_market_confirmation_checklist.py `
    --ticker NVDA --mode validation `
    --input-dir docs/sample_reports/generic_ticker/NVDA `
    --output-dir docs/sample_reports/generic_ticker/NVDA

# Archive
python scripts/ticker_archive_packet.py `
    --ticker NVDA --mode validation `
    --input-dir docs/sample_reports/generic_ticker/NVDA `
    --output-dir docs/sample_reports/generic_ticker/NVDA/archive
```

**Expected outputs:**
- `docs/sample_reports/generic_ticker/NVDA/synthesis/NVDA_synthesis_packet.json`
- `docs/sample_reports/generic_ticker/NVDA/synthesis/NVDA_synthesis_packet.md`
- `docs/sample_reports/generic_ticker/NVDA/monitoring/NVDA_monitoring_plan.json`
- `docs/sample_reports/generic_ticker/NVDA/monitoring/NVDA_monitoring_plan.md`
- `docs/sample_reports/generic_ticker/NVDA/market_confirmation/NVDA_market_confirmation_plan.json`
- `docs/sample_reports/generic_ticker/NVDA/market_confirmation/NVDA_market_confirmation_checklist.md`
- `docs/sample_reports/generic_ticker/NVDA/market_confirmation/NVDA_market_observation_template.csv`
- `docs/sample_reports/generic_ticker/NVDA/archive/NVDA_archive_manifest.json`
- `docs/sample_reports/generic_ticker/NVDA/archive/NVDA_archive_index.md`

**Validation tests:**
```powershell
pytest tests/test_generic_ticker_second_validation.py -v
```

**Known limitations:**
- Skeleton validation mode - no live SEC data extraction
- All financial/insider data marked `not_available`
- Not an NVDA investment analysis or research report
- Demonstrates framework structure, not actual analysis

## Safety Constraints

**All scripts enforce:**
- `report_only: true`
- `alerts_generated: false`
- `openinsider_spreadsheet_used: false`
- `telegram_sent: false`
- `email_sent: false`
- `scheduled_tasks_modified: false`
- `env_printed_or_changed: false`
- `buy_sell_hold_language_used: false`

**Prohibited actions:**
- Send Telegram messages
- Send email
- Modify or trigger scheduled tasks
- Change or print .env contents
- Use Roger's OpenInsider spreadsheet
- Create buy/sell/hold recommendation language
- Connect to Ross alert system
- Force-push to git

## Limitations

**Current implementation:**
1. Full SEC extraction for arbitrary tickers not yet implemented
2. Validation mode uses existing MAIA data reformatted to generic schema
3. Markdown templates simplified (full templates planned)
4. CIK lookup automation not implemented
5. 10-Q/10-K XBRL parsing not generalized
6. Form 4 aggregation not generalized
7. Clinical trial data extraction not automated

**13F limitations:**
- 45-day reporting lag
- Parser success rate: 60% (based on MAIA validation)
- Beneficial ownership blockers hide positions <5%
- CUSIP identifier not always extracted

**Market confirmation limitations:**
- Manual entry only
- No live quote integration
- No automated volume/price analysis

## Implementation Roadmap

**CP23C (current):**
- [x] JSON schemas
- [x] CLI design
- [x] MAIA validation mode
- [x] Safety flag validation
- [x] Baseline value preservation
- [x] Documentation

**Future checkpoints (not in scope for CP23C):**
- [ ] Automatic CIK lookup from ticker
- [ ] Generic Form 4 extraction
- [ ] Generic 10-Q/10-K XBRL parsing
- [ ] Clinical trial data extraction (biotech profile)
- [ ] Full markdown templates with Jinja2
- [ ] Live SEC extraction mode
- [ ] Multi-ticker batch processing

## Testing

See `tests/test_ticker_synthesis_workflow.py` and related test files.

**Required validations:**
- MAIA baseline values preserved
- Safety flags correct
- No recommendation language
- Schema compliance
- Checksum integrity

## References

- CP23D: MAIA Full Synthesis Packet
- CP23E: MAIA Monitoring Pack
- CP23F-Fix: 13F Parser Hardening
- CP23G: MAIA Market Confirmation Checklist
- CP23H: MAIA Archive Packet

---

**Checkpoint:** CP23C
**Status:** Framework skeleton complete; MAIA validation passing; full SEC extraction planned for future checkpoint
