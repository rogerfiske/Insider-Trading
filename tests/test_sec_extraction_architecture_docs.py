"""Tests for SEC Extraction Architecture Documents.

Verifies that all required architecture documents exist and contain required sections.
"""

import sys
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(scope="module")
def docs_dir():
    """Get docs directory path."""
    return Path(__file__).resolve().parents[1] / "docs"


class TestArchitectureDocuments:
    """Test that architecture documents exist and are complete."""

    def test_architecture_document_exists(self, docs_dir):
        """Test that full_sec_extraction_architecture.md exists."""
        arch_doc = docs_dir / "workflows" / "full_sec_extraction_architecture.md"
        assert arch_doc.exists(), "Architecture document must exist"

    def test_implementation_plan_exists(self, docs_dir):
        """Test that full_sec_extraction_implementation_plan.md exists."""
        impl_doc = docs_dir / "workflows" / "full_sec_extraction_implementation_plan.md"
        assert impl_doc.exists(), "Implementation plan must exist"

    def test_schema_document_exists(self, docs_dir):
        """Test that full_sec_extraction_schema.md exists."""
        schema_doc = docs_dir / "workflows" / "full_sec_extraction_schema.md"
        assert schema_doc.exists(), "Schema document must exist"

    def test_test_plan_exists(self, docs_dir):
        """Test that full_sec_extraction_test_plan.md exists."""
        test_plan_doc = docs_dir / "workflows" / "full_sec_extraction_test_plan.md"
        assert test_plan_doc.exists(), "Test plan must exist"

    def test_architecture_document_not_empty(self, docs_dir):
        """Test that architecture document is not empty."""
        arch_doc = docs_dir / "workflows" / "full_sec_extraction_architecture.md"
        content = arch_doc.read_text(encoding="utf-8")
        assert len(content) > 1000, "Architecture document should be substantial"

    def test_implementation_plan_not_empty(self, docs_dir):
        """Test that implementation plan is not empty."""
        impl_doc = docs_dir / "workflows" / "full_sec_extraction_implementation_plan.md"
        content = impl_doc.read_text(encoding="utf-8")
        assert len(content) > 1000, "Implementation plan should be substantial"

    def test_schema_document_not_empty(self, docs_dir):
        """Test that schema document is not empty."""
        schema_doc = docs_dir / "workflows" / "full_sec_extraction_schema.md"
        content = schema_doc.read_text(encoding="utf-8")
        assert len(content) > 5000, "Schema document should be substantial"

    def test_test_plan_not_empty(self, docs_dir):
        """Test that test plan is not empty."""
        test_plan_doc = docs_dir / "workflows" / "full_sec_extraction_test_plan.md"
        content = test_plan_doc.read_text(encoding="utf-8")
        assert len(content) > 5000, "Test plan should be substantial"


class TestArchitectureDocumentContent:
    """Test that architecture document contains required sections."""

    @pytest.fixture
    def arch_content(self, docs_dir):
        """Load architecture document content."""
        arch_doc = docs_dir / "workflows" / "full_sec_extraction_architecture.md"
        return arch_doc.read_text(encoding="utf-8")

    def test_contains_purpose_section(self, arch_content):
        """Test that architecture document contains Purpose section."""
        assert "## 1. Purpose" in arch_content

    def test_contains_source_boundary_section(self, arch_content):
        """Test that architecture document contains Source Boundary section."""
        assert "## 2. Source Boundary" in arch_content

    def test_contains_system_overview_section(self, arch_content):
        """Test that architecture document contains System Overview section."""
        assert "## 3. System Overview" in arch_content

    def test_contains_data_flow_section(self, arch_content):
        """Test that architecture document contains Data Flow section."""
        assert "## 4. Data Flow" in arch_content

    def test_contains_module_design_section(self, arch_content):
        """Test that architecture document contains Module Design section."""
        assert "## 5. Module Design" in arch_content

    def test_contains_error_handling_section(self, arch_content):
        """Test that architecture document contains Error Handling section."""
        assert "## 6. Error Handling" in arch_content

    def test_contains_evidence_provenance_section(self, arch_content):
        """Test that architecture document contains Evidence Provenance section."""
        assert "## 7. Evidence Provenance" in arch_content

    def test_contains_json_schema_section(self, arch_content):
        """Test that architecture document contains JSON Schema section."""
        assert "## 8. JSON Schema Outputs" in arch_content

    def test_contains_test_fixture_section(self, arch_content):
        """Test that architecture document contains Test Fixture section."""
        assert "## 9. Test Fixture Strategy" in arch_content

    def test_contains_security_safety_section(self, arch_content):
        """Test that architecture document contains Security/Safety section."""
        assert "## 10. Security/Safety Model" in arch_content

    def test_contains_no_alert_policy_section(self, arch_content):
        """Test that architecture document contains No-Alert/No-Recommendation Policy section."""
        assert "## 11. No-Alert/No-Recommendation Policy" in arch_content

    def test_contains_known_limitations_section(self, arch_content):
        """Test that architecture document contains Known Limitations section."""
        assert "## 12. Known Limitations" in arch_content

    def test_mentions_approved_sources(self, arch_content):
        """Test that architecture document specifies approved SEC sources."""
        assert "SEC EDGAR" in arch_content
        assert "efts.sec.gov" in arch_content or "sec.gov" in arch_content

    def test_mentions_prohibited_sources(self, arch_content):
        """Test that architecture document lists prohibited sources."""
        assert "Prohibited Sources" in arch_content


class TestImplementationPlanContent:
    """Test that implementation plan contains required checkpoint sections."""

    @pytest.fixture
    def impl_content(self, docs_dir):
        """Load implementation plan content."""
        impl_doc = docs_dir / "workflows" / "full_sec_extraction_implementation_plan.md"
        return impl_doc.read_text(encoding="utf-8")

    def test_contains_cp24b_section(self, impl_content):
        """Test that implementation plan contains CP24B section."""
        assert "## CP24B" in impl_content

    def test_contains_cp24c_section(self, impl_content):
        """Test that implementation plan contains CP24C section."""
        assert "## CP24C" in impl_content

    def test_contains_cp24d_section(self, impl_content):
        """Test that implementation plan contains CP24D section."""
        assert "## CP24D" in impl_content

    def test_contains_cp24e_section(self, impl_content):
        """Test that implementation plan contains CP24E section."""
        assert "## CP24E" in impl_content

    def test_contains_cp24f_section(self, impl_content):
        """Test that implementation plan contains CP24F section."""
        assert "## CP24F" in impl_content

    def test_contains_cp24g_section(self, impl_content):
        """Test that implementation plan contains CP24G section."""
        assert "## CP24G" in impl_content

    def test_contains_cp24h_section(self, impl_content):
        """Test that implementation plan contains CP24H section."""
        assert "## CP24H" in impl_content

    def test_contains_cp24i_section(self, impl_content):
        """Test that implementation plan contains CP24I section."""
        assert "## CP24I" in impl_content

    def test_contains_cp24j_section(self, impl_content):
        """Test that implementation plan contains CP24J section."""
        assert "## CP24J" in impl_content

    def test_contains_summary_section(self, impl_content):
        """Test that implementation plan contains Summary section."""
        assert "## Summary" in impl_content

    def test_mentions_acceptance_criteria(self, impl_content):
        """Test that implementation plan includes acceptance criteria."""
        assert "Acceptance Criteria" in impl_content

    def test_mentions_safety_constraints(self, impl_content):
        """Test that implementation plan includes safety constraints."""
        assert "Safety Constraints" in impl_content


class TestSchemaDocumentContent:
    """Test that schema document contains required schema definitions."""

    @pytest.fixture
    def schema_content(self, docs_dir):
        """Load schema document content."""
        schema_doc = docs_dir / "workflows" / "full_sec_extraction_schema.md"
        return schema_doc.read_text(encoding="utf-8")

    def test_contains_ticker_resolution_schema(self, schema_content):
        """Test that schema document contains Ticker Resolution schema."""
        assert "Ticker Resolution" in schema_content
        assert "TickerCikResult" in schema_content

    def test_contains_sec_filing_inventory_schema(self, schema_content):
        """Test that schema document contains SEC Filing Inventory schema."""
        assert "SEC Filing Inventory" in schema_content
        assert "SecSubmissionFiling" in schema_content

    def test_contains_form4_transactions_schema(self, schema_content):
        """Test that schema document contains Form 4 Transactions schema."""
        assert "Form 4 Transactions" in schema_content
        assert "Form4FilingDetails" in schema_content

    def test_contains_form144_schema(self, schema_content):
        """Test that schema document contains Form 144 schema."""
        assert "Form 144" in schema_content
        assert "Form144Filing" in schema_content

    def test_contains_ownership_13dg_schema(self, schema_content):
        """Test that schema document contains Ownership 13D/G schema."""
        assert "Ownership 13D/G" in schema_content
        assert "Ownership13DG" in schema_content

    def test_contains_ownership_13f_schema(self, schema_content):
        """Test that schema document contains Ownership 13F schema."""
        assert "Ownership 13F" in schema_content
        assert "HoldingMatchResult" in schema_content

    def test_contains_xbrl_financials_schema(self, schema_content):
        """Test that schema document contains XBRL Financials schema."""
        assert "XBRL Financials" in schema_content
        assert "XBRLFinancials" in schema_content

    def test_contains_capital_structure_schema(self, schema_content):
        """Test that schema document contains Capital Structure schema."""
        assert "Capital Structure" in schema_content
        assert "CapitalStructure" in schema_content

    def test_contains_clinical_regulatory_schema(self, schema_content):
        """Test that schema document contains Clinical/Regulatory schema."""
        assert "Clinical" in schema_content or "Regulatory" in schema_content
        assert "ClinicalClassification" in schema_content

    def test_contains_synthesis_packet_schema(self, schema_content):
        """Test that schema document contains Synthesis Packet schema."""
        assert "Synthesis Packet" in schema_content
        assert "SynthesisPacket" in schema_content

    def test_contains_monitoring_plan_schema(self, schema_content):
        """Test that schema document contains Monitoring Plan schema."""
        assert "Monitoring Plan" in schema_content
        assert "MonitoringPlan" in schema_content

    def test_contains_market_confirmation_schema(self, schema_content):
        """Test that schema document contains Market Confirmation schema."""
        assert "Market Confirmation" in schema_content
        assert "MarketConfirmationPlan" in schema_content

    def test_contains_archive_manifest_schema(self, schema_content):
        """Test that schema document contains Archive Manifest schema."""
        assert "Archive Manifest" in schema_content
        assert "ArchiveManifest" in schema_content

    def test_contains_evidence_provenance_schema(self, schema_content):
        """Test that schema document contains Evidence Provenance schema."""
        assert "Evidence Provenance" in schema_content
        assert "EvidenceProvenance" in schema_content

    def test_contains_error_degraded_mode_schema(self, schema_content):
        """Test that schema document contains Error/Degraded-Mode schema."""
        assert "Degraded" in schema_content or "Error" in schema_content
        assert "DegradedModeStatus" in schema_content or "error_type" in schema_content

    def test_contains_json_examples(self, schema_content):
        """Test that schema document contains JSON examples."""
        assert "```json" in schema_content
        # Should have multiple JSON examples
        assert schema_content.count("```json") >= 10

    def test_contains_field_definitions(self, schema_content):
        """Test that schema document contains field definition tables."""
        assert "Field Definitions" in schema_content or "| Field |" in schema_content


class TestTestPlanContent:
    """Test that test plan contains required test categories."""

    @pytest.fixture
    def test_plan_content(self, docs_dir):
        """Load test plan content."""
        test_plan_doc = docs_dir / "workflows" / "full_sec_extraction_test_plan.md"
        return test_plan_doc.read_text(encoding="utf-8")

    def test_contains_unit_tests_section(self, test_plan_content):
        """Test that test plan contains Unit Tests section."""
        assert "Unit Tests" in test_plan_content

    def test_contains_fixture_tests_section(self, test_plan_content):
        """Test that test plan contains Fixture Tests section."""
        assert "Fixture Tests" in test_plan_content

    def test_contains_integration_tests_section(self, test_plan_content):
        """Test that test plan contains Integration Tests section."""
        assert "Integration Tests" in test_plan_content

    def test_contains_network_safe_tests_section(self, test_plan_content):
        """Test that test plan contains Network-Safe Tests section."""
        assert "Network-Safe" in test_plan_content or "Network Safe" in test_plan_content

    def test_contains_no_network_tests_section(self, test_plan_content):
        """Test that test plan contains No-Network Tests section."""
        assert "No-Network" in test_plan_content or "No Network" in test_plan_content

    def test_contains_degraded_mode_tests_section(self, test_plan_content):
        """Test that test plan contains Degraded-Mode Tests section."""
        assert "Degraded" in test_plan_content or "degraded" in test_plan_content

    def test_contains_secret_safety_tests_section(self, test_plan_content):
        """Test that test plan contains Secret-Safety Tests section."""
        assert "Secret" in test_plan_content or "secret" in test_plan_content

    def test_contains_no_alert_tests_section(self, test_plan_content):
        """Test that test plan contains No-Alert Tests section."""
        assert "No-Alert" in test_plan_content or "No Alert" in test_plan_content

    def test_contains_no_recommendation_tests_section(self, test_plan_content):
        """Test that test plan contains No-Recommendation-Language Tests section."""
        assert "No-Recommendation" in test_plan_content or "No Recommendation" in test_plan_content

    def test_contains_regression_tests_section(self, test_plan_content):
        """Test that test plan contains Regression Tests section."""
        assert "Regression" in test_plan_content

    def test_mentions_maia_baseline(self, test_plan_content):
        """Test that test plan mentions MAIA regression baseline."""
        assert "MAIA" in test_plan_content
        assert "134" in test_plan_content  # MAIA purchase count baseline

    def test_mentions_nvda_baseline(self, test_plan_content):
        """Test that test plan mentions NVDA regression baseline."""
        assert "NVDA" in test_plan_content

    def test_mentions_test_coverage_targets(self, test_plan_content):
        """Test that test plan mentions test coverage targets."""
        assert "80%" in test_plan_content or "coverage" in test_plan_content.lower()

    def test_contains_test_execution_commands(self, test_plan_content):
        """Test that test plan contains test execution commands."""
        assert "pytest" in test_plan_content


class TestCrossReferenceIntegrity:
    """Test that documents correctly cross-reference each other."""

    @pytest.fixture
    def all_docs(self, docs_dir):
        """Load all architecture documents."""
        return {
            "architecture": (docs_dir / "workflows" / "full_sec_extraction_architecture.md").read_text(encoding="utf-8"),
            "implementation": (docs_dir / "workflows" / "full_sec_extraction_implementation_plan.md").read_text(encoding="utf-8"),
            "schema": (docs_dir / "workflows" / "full_sec_extraction_schema.md").read_text(encoding="utf-8"),
            "test_plan": (docs_dir / "workflows" / "full_sec_extraction_test_plan.md").read_text(encoding="utf-8"),
        }

    def test_schema_references_architecture(self, all_docs):
        """Test that schema document references architecture document."""
        assert "full_sec_extraction_architecture.md" in all_docs["schema"]

    def test_test_plan_references_architecture(self, all_docs):
        """Test that test plan references architecture document."""
        assert "full_sec_extraction_architecture.md" in all_docs["test_plan"]

    def test_implementation_references_architecture(self, all_docs):
        """Test that implementation plan references architecture document."""
        assert "full_sec_extraction_architecture.md" in all_docs["implementation"]

    def test_all_docs_mention_cp24a(self, all_docs):
        """Test that all documents mention CP24A."""
        for doc_name, content in all_docs.items():
            assert "CP24A" in content, f"{doc_name} should mention CP24A"


class TestSafetyConstraintsCoverage:
    """Test that safety constraints are documented across all documents."""

    @pytest.fixture
    def all_docs(self, docs_dir):
        """Load all architecture documents."""
        return {
            "architecture": (docs_dir / "workflows" / "full_sec_extraction_architecture.md").read_text(encoding="utf-8"),
            "implementation": (docs_dir / "workflows" / "full_sec_extraction_implementation_plan.md").read_text(encoding="utf-8"),
            "schema": (docs_dir / "workflows" / "full_sec_extraction_schema.md").read_text(encoding="utf-8"),
            "test_plan": (docs_dir / "workflows" / "full_sec_extraction_test_plan.md").read_text(encoding="utf-8"),
        }

    def test_all_docs_mention_no_alerts(self, all_docs):
        """Test that all documents mention no-alert policy."""
        for doc_name, content in all_docs.items():
            content_lower = content.lower()
            assert "alert" in content_lower, f"{doc_name} should mention alerts"

    def test_all_docs_mention_no_recommendations(self, all_docs):
        """Test that all documents mention no-recommendation policy."""
        for doc_name, content in all_docs.items():
            content_lower = content.lower()
            assert "recommendation" in content_lower or "buy" in content_lower or "sell" in content_lower, \
                f"{doc_name} should mention recommendation policy"

    def test_all_docs_mention_safety_flags(self, all_docs):
        """Test that all documents mention safety flags."""
        for doc_name, content in all_docs.items():
            content_lower = content.lower()
            assert "safety" in content_lower, f"{doc_name} should mention safety"

    def test_schema_defines_safety_flags(self, all_docs):
        """Test that schema document defines safety flag structure."""
        assert '"safety"' in all_docs["schema"]
        assert "alerts_generated" in all_docs["schema"]

    def test_test_plan_covers_safety_testing(self, all_docs):
        """Test that test plan covers safety constraint testing."""
        assert "No-Alert" in all_docs["test_plan"]
        assert "No-Recommendation" in all_docs["test_plan"]
        assert "Secret" in all_docs["test_plan"] or "secret" in all_docs["test_plan"]
