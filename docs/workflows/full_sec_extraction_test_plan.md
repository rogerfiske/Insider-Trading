# Full SEC Extraction Test Plan

**Version:** 1.0
**Created:** 2026-06-11
**Checkpoint:** CP24A
**Parent:** [full_sec_extraction_architecture.md](full_sec_extraction_architecture.md)

---

## Overview

This document defines the comprehensive test strategy for the full SEC extraction pipeline. The test plan covers unit tests, integration tests, fixture tests, network-safe tests, degraded-mode tests, security tests, and regression tests.

**Current Test Infrastructure:**
- Total test files: 63
- SEC-focused test files: 15
- Existing test coverage: ~80% for core SEC modules

**Test Philosophy:**
- Write tests first (TDD approach)
- Test behavior, not implementation
- Use real SEC data fixtures where possible
- Mock network calls for unit tests
- Maintain offline test capability
- Verify safety constraints in every test suite

---

## Test Categories

### 1. Unit Tests

**Purpose:** Test individual functions and modules in isolation.

**Characteristics:**
- No network calls (all mocked)
- Fast execution (<100ms per test)
- Focused on single responsibility
- Use minimal synthetic fixtures

**Coverage Targets:**
- Parsing logic: 95%+
- Classification logic: 95%+
- Aggregation logic: 90%+
- Error handling: 90%+

**Example Test Files:**
- `test_sec_form4_details.py` (transaction classification)
- `test_sec_13f_matcher.py` (matching logic)
- `test_form4_aggregator.py` (aggregation calculations)

**Unit Test Pattern:**

```python
def test_classify_transaction_purchase():
    """Test classification of purchase transactions."""
    # Arrange
    transaction_code = "P"
    acquisition_disposition = "A"

    # Act
    result = classify_transaction(transaction_code, acquisition_disposition)

    # Assert
    assert result == "OPEN_MARKET_PURCHASE"


def test_aggregate_form4_transactions_empty_input():
    """Test aggregation with empty transaction list."""
    # Arrange
    transactions = []

    # Act
    result = aggregate_form4_transactions(transactions)

    # Assert
    assert result["open_market_purchases"]["count"] == 0
    assert result["open_market_purchases"]["total_value_usd"] == 0.0
```

---

### 2. Fixture Tests

**Purpose:** Test parsing and extraction with real SEC filing data.

**Characteristics:**
- Use saved SEC filing samples (XML, HTML, JSON)
- No network calls (read from local files)
- Cover edge cases found in production data
- Regression protection for known parsing issues

**Fixture Organization:**

```
tests/fixtures/sec/
├── form4/
│   ├── maia_form4_2024_06_01.xml
│   ├── nvda_form4_2026_05_15.xml
│   ├── malformed_form4_missing_owner.xml
│   └── malformed_form4_missing_price.xml
├── form144/
│   ├── sample_form144_2026_05_01.txt
│   └── malformed_form144_missing_shares.txt
├── 13f/
│   ├── berkshire_13f_infotable_2026_q1.xml
│   ├── bridgewater_13f_infotable_2026_q1.html
│   └── malformed_13f_missing_cusip.xml
├── 10q/
│   ├── nvda_10q_2026_q1_xbrl_instance.xml
│   └── maia_10q_2026_q1_xbrl_instance.xml
└── company_tickers.json (cached SEC reference data)
```

**Fixture Test Pattern:**

```python
def test_parse_form4_xml_with_real_maia_filing():
    """Test parsing with real MAIA Form 4 XML."""
    # Arrange
    fixture_path = "tests/fixtures/sec/form4/maia_form4_2024_06_01.xml"
    with open(fixture_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    # Act
    result = parse_form4_xml(
        xml_content,
        accession_number="0001209191-24-012345",
        primary_document_url="https://example.com/test.xml"
    )

    # Assert
    assert result.parse_status == "success"
    assert len(result.owners) > 0
    assert len(result.transactions) > 0
    assert result.owners[0].owner_name == "Smith John"
    assert result.transactions[0].classification == "OPEN_MARKET_PURCHASE"


def test_parse_form4_xml_with_malformed_missing_owner():
    """Test graceful degradation when owner data is missing."""
    # Arrange
    fixture_path = "tests/fixtures/sec/form4/malformed_form4_missing_owner.xml"
    with open(fixture_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    # Act
    result = parse_form4_xml(xml_content, "0001209191-24-012345", "https://example.com/test.xml")

    # Assert
    assert result.parse_status == "partial"
    assert result.error_type == "MISSING_OWNER"
    assert len(result.transactions) > 0  # Transactions extracted despite missing owner
```

---

### 3. Integration Tests

**Purpose:** Test end-to-end workflows with multiple modules.

**Characteristics:**
- Mock only network boundaries (SEC API calls)
- Test module interactions
- Verify data flow through pipeline
- Use realistic data volumes

**Integration Test Pattern:**

```python
@patch('sources.sec_common.sec_fetch')
def test_full_form4_extraction_workflow(mock_sec_fetch):
    """Test complete Form 4 extraction from submissions to aggregation."""
    # Arrange
    mock_sec_fetch.side_effect = [
        load_fixture("company_tickers.json"),           # Ticker resolution
        load_fixture("CIK0001878313_submissions.json"), # Submissions inventory
        load_fixture("maia_form4_2024_06_01.xml"),      # Form 4 XML #1
        load_fixture("maia_form4_2024_05_15.xml"),      # Form 4 XML #2
    ]

    # Act
    # Step 1: Resolve ticker
    ticker_result = resolve_ticker_to_cik("MAIA")
    assert ticker_result.ok

    # Step 2: Get submissions
    submissions = get_form4_filings_for_cik(ticker_result.cik_padded, lookback_days=1460)
    assert len(submissions) > 0

    # Step 3: Extract Form 4s
    form4_details = []
    for filing in submissions[:2]:  # Test first 2
        details = fetch_and_parse_form4(filing.accession_number, ticker_result.cik_padded, filing.primary_document)
        form4_details.append(details)

    # Step 4: Aggregate
    aggregated = aggregate_form4_transactions(form4_details)

    # Assert
    assert aggregated["open_market_purchases"]["count"] > 0
    assert aggregated["insider_evidence_score"] > 0


@patch('sources.sec_common.sec_fetch')
def test_synthesis_composition_with_partial_data(mock_sec_fetch):
    """Test synthesis composition when some modules fail."""
    # Arrange
    mock_sec_fetch.side_effect = [
        load_fixture("company_tickers.json"),
        load_fixture("CIK0001878313_submissions.json"),
        Exception("Network timeout"),  # Form 4 fetch fails
    ]

    # Act
    synthesis = compose_synthesis_packet(
        ticker="MAIA",
        cik="0001878313",
        insider=None,  # Failed to extract
        ownership_13f=[],
        financials=load_fixture("maia_financials.json"),
        capital=load_fixture("maia_capital_structure.json")
    )

    # Assert
    assert synthesis["data_quality_confidence_score"] < 90  # Degraded
    assert "insider_activity" in synthesis["limitations"]
    assert synthesis["safety"]["buy_sell_hold_language_used"] is False
```

---

### 4. Network-Safe Tests

**Purpose:** Ensure tests can run without internet access.

**Characteristics:**
- All external calls mocked or use cached fixtures
- No live SEC API calls
- Repeatable offline
- Fast CI/CD execution

**Network-Safe Test Pattern:**

```python
@patch('sources.sec_common.sec_fetch')
def test_ticker_resolution_uses_cache(mock_sec_fetch):
    """Test ticker resolution uses cached company_tickers.json."""
    # Arrange
    cache_path = Path("tests/fixtures/sec/company_tickers.json")
    assert cache_path.exists(), "Fixture cache must exist for offline tests"

    # Mock should not be called if cache is fresh
    with patch('sources.sec_common.load_from_cache', return_value=load_fixture("company_tickers.json")):
        # Act
        result = resolve_ticker_to_cik("NVDA")

        # Assert
        assert result.ok
        assert result.cik_padded == "0001045810"
        assert mock_sec_fetch.call_count == 0  # No network call


@pytest.mark.offline
def test_form4_parsing_works_offline():
    """Test Form 4 parsing with local fixture only."""
    # Arrange
    fixture_path = "tests/fixtures/sec/form4/nvda_form4_2026_05_15.xml"
    with open(fixture_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    # Act (no network mocks needed)
    result = parse_form4_xml(xml_content, "0001209191-26-012345", "https://example.com/test.xml")

    # Assert
    assert result.parse_status == "success"
    assert len(result.transactions) > 0
```

---

### 5. No-Network Tests

**Purpose:** Explicitly test offline behavior and cache fallbacks.

**Marker:** `@pytest.mark.offline`

**No-Network Test Pattern:**

```python
@pytest.mark.offline
class TestOfflineBehavior:
    """Test suite for offline/no-network scenarios."""

    def test_cached_ticker_resolution_offline(self):
        """Test ticker resolution from cache when network unavailable."""
        # Arrange: Pre-populate cache
        cache_data = load_fixture("company_tickers.json")
        with patch('sources.sec_common.load_from_cache', return_value=cache_data):
            with patch('sources.sec_common.sec_fetch', side_effect=Exception("Network unavailable")):
                # Act
                result = resolve_ticker_to_cik("AAPL")

                # Assert
                assert result.ok
                assert result.cik_padded == "0000320193"

    def test_form4_parsing_requires_no_network(self):
        """Test that Form 4 parsing never makes network calls."""
        with patch('sources.sec_common.sec_fetch', side_effect=AssertionError("Network call should not occur")):
            # Arrange
            xml_content = load_fixture("maia_form4_2024_06_01.xml")

            # Act
            result = parse_form4_xml(xml_content, "test-accession", "https://example.com/test.xml")

            # Assert
            assert result.parse_status == "success"  # No network call made
```

---

### 6. Degraded-Mode Tests

**Purpose:** Test graceful degradation when data is incomplete or modules fail.

**Characteristics:**
- Test partial success scenarios
- Verify error handling at every phase
- Ensure synthesis proceeds with available data
- Validate limitations[] tracking

**Degraded-Mode Test Pattern:**

```python
def test_form4_parsing_with_missing_price():
    """Test Form 4 parsing when price is missing."""
    # Arrange
    xml_content = load_fixture("form4_missing_price.xml")

    # Act
    result = parse_form4_xml(xml_content, "test-accession", "https://example.com/test.xml")

    # Assert
    assert result.parse_status == "partial"
    assert len(result.transactions) > 0
    assert result.transactions[0].price_per_share is None
    assert result.transactions[0].transaction_value_usd == 0.0
    assert "MISSING_PRICE" in result.error_type


def test_synthesis_with_all_modules_failed():
    """Test synthesis composition when all extraction modules fail."""
    # Arrange
    ticker = "INVALIDTICKER"
    cik = "0000000000"

    # Act
    synthesis = compose_synthesis_packet(
        ticker=ticker,
        cik=cik,
        insider=None,
        ownership_13dg=None,
        ownership_13f=None,
        financials=None,
        capital=None,
        clinical=None
    )

    # Assert
    assert synthesis["data_quality_confidence_score"] == 0
    assert len(synthesis["limitations"]) > 5
    assert synthesis["research_posture"] == "Insufficient data for analysis"
    assert synthesis["safety"]["buy_sell_hold_language_used"] is False


def test_synthesis_with_partial_insider_data():
    """Test synthesis when insider data is partial (some Form 4s failed)."""
    # Arrange
    partial_insider_data = {
        "open_market_purchases": {"count": 50, "total_value_usd": 1000000},
        "parse_summary": {"success_count": 20, "partial_count": 5, "failed_count": 3}
    }

    # Act
    synthesis = compose_synthesis_packet(
        ticker="TEST",
        cik="0001234567",
        insider=partial_insider_data,
        ownership_13f=None,
        financials={"cash_balance_usd": 10000000},
        capital=None
    )

    # Assert
    assert 50 < synthesis["data_quality_confidence_score"] < 90  # Partial
    assert "3 Form 4 filings failed to parse" in str(synthesis["limitations"])
```

---

### 7. Secret-Safety Tests

**Purpose:** Ensure no secrets are leaked in output or logs.

**Characteristics:**
- Verify no API keys in JSON output
- Verify no User-Agent email in public artifacts
- Check error messages don't expose secrets
- Validate .env loading works

**Secret-Safety Test Pattern:**

```python
def test_no_secrets_in_synthesis_output():
    """Test that synthesis packet contains no secrets."""
    # Arrange
    synthesis = compose_synthesis_packet(
        ticker="TEST",
        cik="0001234567",
        insider={"open_market_purchases": {"count": 10}},
        ownership_13f=None,
        financials=None,
        capital=None
    )

    # Act
    synthesis_json = json.dumps(synthesis, indent=2)

    # Assert
    assert "SEC_USER_AGENT" not in synthesis_json
    assert "@" not in synthesis_json  # No email addresses
    assert "API_KEY" not in synthesis_json
    assert "SECRET" not in synthesis_json


def test_user_agent_not_logged_in_errors():
    """Test that User-Agent is not exposed in error messages."""
    with patch.dict(os.environ, {"SEC_USER_AGENT": "test@example.com"}):
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        # Act
        with pytest.raises(Exception) as exc_info:
            raise Exception(f"SEC request failed: {mock_response.text}")

        # Assert
        error_message = str(exc_info.value)
        assert "test@example.com" not in error_message


def test_env_loading_requires_user_agent():
    """Test that SEC_USER_AGENT is required."""
    with patch.dict(os.environ, {}, clear=True):
        # Act & Assert
        with pytest.raises(ValueError, match="SEC_USER_AGENT"):
            validate_sec_config()
```

---

### 8. No-Alert Tests

**Purpose:** Verify no alerts are generated during extraction.

**Characteristics:**
- Check safety flags in all outputs
- Verify no Telegram/email modules imported
- Validate report-only mode enforced

**No-Alert Test Pattern:**

```python
def test_synthesis_packet_has_correct_safety_flags():
    """Test that synthesis packet safety flags are correct."""
    # Arrange & Act
    synthesis = compose_synthesis_packet(
        ticker="TEST",
        cik="0001234567",
        insider={"open_market_purchases": {"count": 100}},
        ownership_13f=None,
        financials=None,
        capital=None
    )

    # Assert
    assert synthesis["safety"]["report_only"] is True
    assert synthesis["safety"]["alerts_generated"] is False
    assert synthesis["safety"]["telegram_sent"] is False
    assert synthesis["safety"]["email_sent"] is False


def test_no_alert_modules_imported():
    """Test that alert modules are not imported in SEC extraction."""
    import sys

    # Act
    import sources.sec_ticker
    import sources.sec_form4_details
    import scripts.ticker_synthesis_workflow

    # Assert
    assert "connectors.telegram_connector" not in sys.modules
    assert "connectors.email_connector" not in sys.modules


def test_monitoring_plan_has_manual_triggers_only():
    """Test that monitoring plan uses manual triggers only."""
    # Arrange & Act
    plan = generate_monitoring_plan(
        ticker="TEST",
        baseline_synthesis={"insider_evidence_score": 85}
    )

    # Assert
    for category in plan["monitoring_categories"]:
        assert category["alert_trigger"] == "manual"
```

---

### 9. No-Recommendation-Language Tests

**Purpose:** Ensure no investment recommendation language appears in outputs.

**Characteristics:**
- Scan all text output for prohibited terms
- Verify evidence matrix uses neutral language
- Check research posture is descriptive only

**Prohibited Terms:**
- buy, sell, hold
- strong buy, accumulate, reduce, underperform
- recommend, recommendation
- should buy, should sell
- investment advice

**Allowed Descriptive Terms:**
- positive, negative, neutral
- strong, moderate, weak
- high, medium, low (confidence)
- evidence, signal, indication

**No-Recommendation-Language Test Pattern:**

```python
def test_synthesis_packet_contains_no_recommendation_language():
    """Test that synthesis packet uses no buy/sell/hold language."""
    # Arrange & Act
    synthesis = compose_synthesis_packet(
        ticker="TEST",
        cik="0001234567",
        insider={"open_market_purchases": {"count": 100, "total_value_usd": 5000000}},
        ownership_13f=None,
        financials={"cash_balance_usd": 10000000},
        capital=None
    )

    # Act: Convert to JSON and Markdown
    synthesis_json = json.dumps(synthesis, indent=2).lower()
    synthesis_md = generate_synthesis_markdown(synthesis).lower()

    # Assert: Check prohibited terms
    prohibited_terms = [
        "buy", "sell", "hold",
        "strong buy", "accumulate", "reduce",
        "recommend", "should buy", "should sell",
        "investment advice", "underperform", "outperform"
    ]

    for term in prohibited_terms:
        assert term not in synthesis_json, f"Prohibited term '{term}' found in JSON"
        assert term not in synthesis_md, f"Prohibited term '{term}' found in Markdown"


def test_evidence_matrix_uses_neutral_direction_terms():
    """Test that evidence matrix uses neutral direction terms."""
    # Arrange
    evidence_matrix = [
        {"category": "Insider Activity", "direction": "positive", "strength": "strong"},
        {"category": "Financial Health", "direction": "negative", "strength": "moderate"},
        {"category": "Institutional Ownership", "direction": "neutral", "strength": "weak"}
    ]

    # Act
    matrix_json = json.dumps(evidence_matrix).lower()

    # Assert: Allowed terms
    assert "positive" in matrix_json or "negative" in matrix_json or "neutral" in matrix_json
    assert "strong" in matrix_json or "moderate" in matrix_json or "weak" in matrix_json

    # Assert: Prohibited terms
    assert "buy" not in matrix_json
    assert "sell" not in matrix_json
    assert "recommend" not in matrix_json


def test_research_posture_is_descriptive_only():
    """Test that research posture contains no recommendations."""
    # Arrange & Act
    synthesis = compose_synthesis_packet(
        ticker="TEST",
        cik="0001234567",
        insider={"insider_evidence_score": 92},
        ownership_13f=None,
        financials=None,
        capital=None
    )

    posture = synthesis["research_posture"].lower()

    # Assert: Should contain descriptive terms
    descriptive_terms = ["strong", "moderate", "weak", "positive", "negative", "signal", "evidence"]
    assert any(term in posture for term in descriptive_terms)

    # Assert: Should NOT contain recommendation terms
    recommendation_terms = ["buy", "sell", "hold", "recommend", "should"]
    assert not any(term in posture for term in recommendation_terms)
```

---

### 10. Regression Tests

**Purpose:** Preserve known-good baselines for MAIA and NVDA validation.

**Characteristics:**
- Use MAIA as biotech baseline
- Use NVDA as large-cap tech baseline
- Lock in expected values for key metrics
- Detect unintended changes to extraction logic

**Regression Test Pattern:**

```python
@pytest.mark.regression
class TestMAIABaseline:
    """Regression tests for MAIA validation baseline."""

    def test_maia_form4_purchase_count(self):
        """Test MAIA Form 4 purchase count matches approved baseline."""
        # Arrange
        with patch('sources.sec_common.sec_fetch') as mock_fetch:
            mock_fetch.side_effect = load_maia_fixtures()

            # Act
            aggregated = extract_and_aggregate_form4_data("MAIA", "0001878313")

            # Assert
            assert aggregated["open_market_purchases"]["count"] == 134, \
                "MAIA baseline: Expected 134 open-market purchases"

    def test_maia_insider_evidence_score(self):
        """Test MAIA insider evidence score matches baseline."""
        # Arrange
        with patch('sources.sec_common.sec_fetch') as mock_fetch:
            mock_fetch.side_effect = load_maia_fixtures()

            # Act
            aggregated = extract_and_aggregate_form4_data("MAIA", "0001878313")

            # Assert
            assert 85 <= aggregated["insider_evidence_score"] <= 95, \
                "MAIA baseline: Insider evidence score should be in range 85-95"

    def test_maia_clinical_module_is_biotech(self):
        """Test MAIA is correctly classified as biotech."""
        # Arrange
        with patch('sources.sec_common.sec_fetch') as mock_fetch:
            mock_fetch.side_effect = load_maia_fixtures()

            # Act
            classification = classify_biotech_status("MAIA", "0001878313")

            # Assert
            assert classification["is_biotech"] is True
            assert classification["confidence"] == "HIGH"


@pytest.mark.regression
class TestNVDABaseline:
    """Regression tests for NVDA validation baseline."""

    def test_nvda_clinical_module_not_applicable(self):
        """Test NVDA is correctly classified as non-biotech."""
        # Arrange
        with patch('sources.sec_common.sec_fetch') as mock_fetch:
            mock_fetch.side_effect = load_nvda_fixtures()

            # Act
            classification = classify_biotech_status("NVDA", "0001045810")

            # Assert
            assert classification["is_biotech"] is False

    def test_nvda_has_form4_activity(self):
        """Test NVDA Form 4 extraction succeeds."""
        # Arrange
        with patch('sources.sec_common.sec_fetch') as mock_fetch:
            mock_fetch.side_effect = load_nvda_fixtures()

            # Act
            aggregated = extract_and_aggregate_form4_data("NVDA", "0001045810")

            # Assert
            assert aggregated["total_form4_filings"] > 0
            assert "open_market_purchases" in aggregated

    def test_nvda_synthesis_has_no_recommendations(self):
        """Test NVDA synthesis contains no investment recommendations."""
        # Arrange
        with patch('sources.sec_common.sec_fetch') as mock_fetch:
            mock_fetch.side_effect = load_nvda_fixtures()

            # Act
            synthesis = compose_synthesis_packet("NVDA", "0001045810", load_nvda_modules())

            # Assert
            synthesis_text = json.dumps(synthesis).lower()
            assert "buy" not in synthesis_text
            assert "sell" not in synthesis_text
            assert synthesis["safety"]["buy_sell_hold_language_used"] is False
```

---

## Test Organization by Checkpoint

### CP24B: Ticker/CIK Resolver and Submissions Inventory

**Test Files:**
- `test_ticker_submissions_inventory.py`

**Test Cases:**
- ✓ Resolve known tickers (AAPL, MSFT, NVDA)
- ✓ Handle unknown tickers (TICKER_NOT_FOUND)
- ✓ Fetch submissions for CIK
- ✓ Filter filings by form type
- ✓ Filter filings by date range
- ✓ Cache company_tickers.json (7-day TTL)
- ✓ Cache submissions JSON (24-hour TTL)
- ✓ Handle network errors gracefully
- ✓ Offline operation with cached data
- ✓ Provenance tracking (retrieve_at, source_url)

**Acceptance:** 10/10 tests pass

---

### CP24C: Form 4 Extraction and Insider Transaction Normalization

**Test Files:**
- `test_form4_aggregator.py`
- `test_ticker_form4_extractor.py`

**Test Cases:**
- ✓ Parse Form 4 XML (embedded and standalone)
- ✓ Extract reporting owners
- ✓ Extract transactions
- ✓ Classify transactions (P/S/M/A/F/G/D)
- ✓ Aggregate open-market purchases
- ✓ Aggregate open-market sales
- ✓ Calculate net insider activity
- ✓ Calculate insider evidence score
- ✓ Handle missing price (set to None, value = 0.0)
- ✓ Handle missing owner (partial success)
- ✓ Handle malformed XML (parse_status=failed)
- ✓ Count distinct buyers/sellers
- ✓ Track latest purchase/sale dates
- ✓ Offline operation with fixtures
- ✓ MAIA regression: 134 purchases

**Acceptance:** 15/15 tests pass

---

### CP24D: Form 144 and 13D/G Extraction

**Test Files:**
- `test_sec_form144.py`
- `test_sec_13dg.py`
- `test_ticker_form144_extractor.py`
- `test_ticker_13dg_extractor.py`

**Test Cases:**
- ✓ Parse Form 144 text file
- ✓ Extract reporting person, shares proposed, sale date
- ✓ Parse 13D/G text file
- ✓ Extract filer identity, shares held, ownership percent
- ✓ Handle missing optional fields
- ✓ Handle parse errors gracefully
- ✓ Offline operation with fixtures
- ✓ No recommendation language
- ✓ Safety flags correct
- ✓ Provenance tracking

**Acceptance:** 10/10 tests pass per form type (20 total)

---

### CP24E: XBRL Financial Extraction

**Test Files:**
- `test_sec_xbrl_financials.py`
- `test_ticker_xbrl_extractor.py`

**Test Cases:**
- ✓ Fetch XBRL instance document
- ✓ Parse XML namespaces (us-gaap, dei)
- ✓ Extract cash balance
- ✓ Extract total assets/liabilities
- ✓ Extract working capital (or calculate)
- ✓ Extract revenue
- ✓ Extract operating cash flow
- ✓ Extract R&D expense
- ✓ Handle missing XBRL tags (set to None)
- ✓ Filter by context ID (most recent period)
- ✓ Handle 10-Q and 10-K formats
- ✓ Offline operation with fixtures

**Acceptance:** 12/12 tests pass

---

### CP24F: Capital Structure Extraction

**Test Files:**
- `test_sec_capital_structure.py`
- `test_ticker_capital_structure_extractor.py`

**Test Cases:**
- ✓ Extract shares outstanding from XBRL
- ✓ Extract stock options from notes
- ✓ Extract warrants from notes
- ✓ Extract convertible securities
- ✓ Calculate fully diluted shares
- ✓ Calculate dilution overhang percent
- ✓ Handle missing data fields
- ✓ MAIA regression: ~27.5% dilution

**Acceptance:** 8/8 tests pass

---

### CP24G: 13F InfoTable Integration

**Test Files:**
- `test_ticker_13f_matcher.py`
- `test_ticker_13f_integration.py`

**Test Cases:**
- ✓ Fetch 13F-HR filings for managers
- ✓ Parse InfoTable XML
- ✓ Parse InfoTable HTML fallback
- ✓ Match by CUSIP (exact)
- ✓ Match by issuer name (exact)
- ✓ Match by normalized issuer name
- ✓ Handle no matches (empty result, not error)
- ✓ Aggregate holdings across managers
- ✓ Offline operation with fixtures

**Acceptance:** 10/10 tests pass

---

### CP24H: Full Synthesis Composition

**Test Files:**
- `test_synthesis_composer.py`
- `test_ticker_synthesis_workflow.py`

**Test Cases:**
- ✓ Compose synthesis from all modules
- ✓ Calculate insider evidence score
- ✓ Calculate dilution capital risk score
- ✓ Calculate cash runway months
- ✓ Calculate clinical progress score (biotech)
- ✓ Calculate business progress score (non-biotech)
- ✓ Generate evidence matrix
- ✓ Generate research posture (descriptive only)
- ✓ Handle partial data (some modules failed)
- ✓ Handle minimal data (only ticker/CIK)
- ✓ Track limitations correctly
- ✓ Safety flags correct
- ✓ No recommendation language
- ✓ Provenance tracking
- ✓ Data quality confidence score accurate
- ✓ MAIA regression: baseline preserved
- ✓ NVDA regression: non-biotech classification
- ✓ Offline operation
- ✓ Degraded mode scoring correct
- ✓ Archive manifest generation

**Acceptance:** 20/20 tests pass

---

### CP24I: Multi-Ticker Validation Batch

**Test Files:**
- `test_multi_ticker_validation.py`
- `test_ticker_batch_validator.py`

**Test Cases:**
- ✓ Batch process 5-10 tickers
- ✓ MAIA baseline preserved (134 purchases, biotech classification)
- ✓ NVDA baseline preserved (non-biotech, large-cap)
- ✓ AAPL extraction succeeds
- ✓ MSFT extraction succeeds
- ✓ REGN extraction succeeds (biotech, revenue-positive)
- ✓ JPM extraction succeeds (financial services)
- ✓ XOM extraction succeeds (energy)
- ✓ All tickers have no recommendation language
- ✓ All tickers have correct safety flags
- ✓ All tickers have provenance tracking
- ✓ Batch summary report accurate
- ✓ Degraded modes handled correctly
- ✓ Offline operation with cached fixtures
- ✓ No network calls during test execution

**Acceptance:** 30/30 regression tests pass

---

### CP24J: Documentation/Archive Hardening

**Test Files:**
- `test_archive_manifest.py`
- `test_documentation_completeness.py`

**Test Cases:**
- ✓ Archive manifest includes all artifacts
- ✓ SHA-256 checksums calculated correctly
- ✓ Safety flags verified in manifest
- ✓ Data completeness score calculated
- ✓ Documentation examples work
- ✓ Troubleshooting guide covers common errors
- ✓ Test coverage ≥ 80% for all SEC modules

**Acceptance:** 7/7 tests pass

---

## Test Execution Commands

### Run All Tests

```powershell
# Run full test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=sources --cov=scripts --cov-report=html --cov-report=term

# Open coverage report
start htmlcov/index.html
```

### Run Specific Test Categories

```powershell
# Run only unit tests (fast, no network)
pytest tests/ -v -m "not integration and not regression"

# Run only offline tests
pytest tests/ -v -m offline

# Run only regression tests
pytest tests/ -v -m regression

# Run only SEC-focused tests
pytest tests/test_sec*.py -v

# Run only Form 4 tests
pytest tests/test*form4*.py -v
```

### Run Tests by Checkpoint

```powershell
# CP24B: Ticker/CIK resolver
pytest tests/test_ticker_submissions_inventory.py -v

# CP24C: Form 4 extraction
pytest tests/test_form4_aggregator.py tests/test_ticker_form4_extractor.py -v

# CP24D: Form 144 and 13D/G
pytest tests/test_sec_form144.py tests/test_sec_13dg.py -v

# CP24E: XBRL financials
pytest tests/test_sec_xbrl_financials.py -v

# CP24F: Capital structure
pytest tests/test_sec_capital_structure.py -v

# CP24G: 13F integration
pytest tests/test_ticker_13f_matcher.py -v

# CP24H: Full synthesis
pytest tests/test_synthesis_composer.py tests/test_ticker_synthesis_workflow.py -v

# CP24I: Multi-ticker validation
pytest tests/test_multi_ticker_validation.py -v
```

---

## Test Coverage Goals

### Module-Level Coverage Targets

| Module | Target | Current | Notes |
|--------|--------|---------|-------|
| sources/sec_ticker.py | 95% | ~90% | Ticker resolution |
| sources/sec_submissions.py | 95% | ~85% | Submissions inventory |
| sources/sec_form4_details.py | 95% | ~92% | Form 4 parsing |
| sources/sec_form144.py | 90% | 0% | Not yet implemented |
| sources/sec_13dg.py | 90% | 0% | Not yet implemented |
| sources/sec_13f_matcher.py | 95% | ~88% | 13F matching |
| sources/sec_xbrl_financials.py | 85% | 0% | Not yet implemented |
| sources/sec_capital_structure.py | 85% | 0% | Not yet implemented |
| sources/synthesis_composer.py | 90% | 0% | Not yet implemented |
| scripts/ticker_synthesis_workflow.py | 80% | ~70% | Integration script |

### Overall Coverage Target

**Target:** ≥80% coverage for all SEC extraction modules

**Current:** ~75% (existing modules)

**Gap:** +5% coverage needed, primarily in:
- Error handling paths
- Degraded-mode scenarios
- Edge case fixtures

---

## Test Maintenance Strategy

### Fixture Updates

**When to update fixtures:**
- SEC changes XML/HTML format
- New XBRL tags discovered
- Parsing failures in production
- Regression test failures

**Fixture update process:**
1. Save real SEC filing causing issue
2. Add to `tests/fixtures/sec/`
3. Create failing test case
4. Fix parsing logic
5. Verify test passes
6. Document edge case

### Regression Baseline Updates

**MAIA baseline (locked):**
- Form 4 purchase count: 134
- Insider evidence score: 85-95
- Clinical classification: biotech
- Dilution overhang: ~27.5%

**NVDA baseline (locked):**
- Clinical classification: non-biotech
- Form 4 activity: present
- 13F holdings: detected

**Update process:**
- Require PM approval to change baselines
- Document reason for baseline change
- Update test expectations
- Re-run full regression suite

### CI/CD Integration

**Pre-commit checks:**
- Run offline tests only
- Verify no recommendation language
- Verify safety flags
- Fast execution (<30 seconds)

**Pull request checks:**
- Run full test suite
- Coverage report
- Regression tests
- Linting/formatting

**Scheduled checks:**
- Weekly: Live SEC data smoke tests (optional)
- Monthly: Fixture freshness validation

---

## Summary

This test plan defines **comprehensive test coverage** for the full SEC extraction pipeline:

**Test Categories:**
1. ✓ Unit tests (fast, isolated, mocked)
2. ✓ Fixture tests (real SEC data, offline)
3. ✓ Integration tests (multi-module workflows)
4. ✓ Network-safe tests (no live API calls)
5. ✓ No-network tests (explicit offline mode)
6. ✓ Degraded-mode tests (partial success scenarios)
7. ✓ Secret-safety tests (no leaked credentials)
8. ✓ No-alert tests (report-only mode enforced)
9. ✓ No-recommendation-language tests (descriptive only)
10. ✓ Regression tests (MAIA/NVDA baselines)

**Estimated Test Count by Checkpoint:**
- CP24B: 10 tests
- CP24C: 15 tests
- CP24D: 20 tests (10 per form type)
- CP24E: 12 tests
- CP24F: 8 tests
- CP24G: 10 tests
- CP24H: 20 tests
- CP24I: 30 regression tests
- CP24J: 7 tests
- **Total: ~132 new tests**

**Current Infrastructure:**
- 63 existing test files
- 15 SEC-focused test files
- ~80% coverage for core modules

**Target:**
- ~195 total test files after CP24J
- ≥80% overall coverage
- 100% safety flag verification
- 0 recommendation language violations
