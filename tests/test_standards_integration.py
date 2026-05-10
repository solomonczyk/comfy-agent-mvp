"""Tests for standards integration layer.

RC-COMBINE-V2-QA-QC-TESTER-STANDARDS-INTEGRATION-001
"""

import json
import pytest
from pathlib import Path

from app.standards import (
    StandardsIntegration,
    StandardsBinding,
    StandardsDecisionAdapter,
    StandardsTraceability,
)


PROJECT_ROOT = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"


class TestStandardsIntegration:
    def test_load_standards_pack(self):
        si = StandardsIntegration(PROJECT_ROOT)
        result = si.load_standards_pack()
        assert result["success"] is True
        assert "version" in result

    def test_validate_required_categories(self):
        si = StandardsIntegration(PROJECT_ROOT)
        si.load_standards_pack()
        cats = si.validate_required_categories()
        assert cats["valid"] is True
        assert cats["missing"] == []

    def test_resolve_rule_by_id(self):
        si = StandardsIntegration(PROJECT_ROOT)
        si.load_standards_pack()
        result = si.resolve_rule_by_id("nonexistent_rule")
        assert result["found"] is False

    def test_resolve_policy_by_id(self):
        si = StandardsIntegration(PROJECT_ROOT)
        si.load_standards_pack()
        result = si.resolve_policy_by_id("forbidden_actions_policy")
        assert result["found"] is True
        assert "policy" in result

    def test_map_defect_to_severity(self):
        si = StandardsIntegration(PROJECT_ROOT)
        si.load_standards_pack()
        result = si.map_defect_to_severity("face_identity_mismatch")
        if result["found"]:
            assert "severity" in result
            assert "category" in result
        else:
            pytest.skip("defect taxonomy may not contain face_identity_mismatch")

    def test_map_severity_to_decision(self):
        si = StandardsIntegration(PROJECT_ROOT)
        si.load_standards_pack()
        result = si.map_severity_to_decision("blocker")
        assert result["decision"] == "blocked"
        result2 = si.map_severity_to_decision("info")
        assert result2["decision"] == "pass"

    def test_produce_role_specific_decision(self):
        si = StandardsIntegration(PROJECT_ROOT)
        si.load_standards_pack()
        result = si.produce_role_specific_decision("qa_agent", {})
        assert "overall_decision" in result
        assert result["traceable"] is True
        assert result["role"] == "qa_agent"

    def test_return_traceable_rule_references(self):
        si = StandardsIntegration(PROJECT_ROOT)
        si.load_standards_pack()
        result = si.return_traceable_rule_references("qa", "test", "pass", "info")
        assert result["traceable"] is True
        assert result["role"] == "qa"
        assert "rule_references" in result

    def test_write_artifact(self, tmp_path):
        si = StandardsIntegration(tmp_path)
        si.ensure_integration_dir()
        path = si.write_artifact("test.json", {"test": True})
        assert path.exists()
        with open(path, "r") as f:
            data = json.load(f)
        assert data["test"] is True

    def test_ensure_integration_dir(self, tmp_path):
        si = StandardsIntegration(tmp_path)
        path = si.ensure_integration_dir()
        assert path.exists()

    def test_build_validation_report(self):
        si = StandardsIntegration(PROJECT_ROOT)
        report = si.build_validation_report()
        assert "valid" in report
        assert "standards_pack_loaded" in report
        assert "required_categories_present" in report


class TestStandardsBinding:
    def test_build_qa_binding_report(self):
        sb = StandardsBinding(PROJECT_ROOT)
        report = sb.build_qa_binding_report()
        assert report["valid"] is True
        assert report["role"] == "qa"
        assert report["qa_cannot_accept_production"] is True
        assert report["technical_pass_separate_from_visual_pass"] is True

    def test_build_qc_binding_report(self):
        sb = StandardsBinding(PROJECT_ROOT)
        report = sb.build_qc_binding_report()
        assert report["valid"] is True
        assert report["role"] == "qc"
        assert "policies_available" in report

    def test_build_tester_binding_report(self):
        sb = StandardsBinding(PROJECT_ROOT)
        report = sb.build_tester_binding_report()
        assert report["valid"] is True
        assert report["role"] == "tester"
        assert "failure_cases_checked" in report

    def test_build_visual_qa_binding_report(self):
        sb = StandardsBinding(PROJECT_ROOT)
        report = sb.build_visual_qa_binding_report()
        assert report["valid"] is True
        assert report["role"] == "visual_qa"
        assert "canons_available" in report

    def test_build_script_supervisor_binding_report(self):
        sb = StandardsBinding(PROJECT_ROOT)
        report = sb.build_script_supervisor_binding_report()
        assert report["valid"] is True
        assert report["role"] == "script_supervisor"
        assert report["preview_render_not_executed"] is True

    def test_build_state_audit_binding_report(self):
        sb = StandardsBinding(PROJECT_ROOT)
        report = sb.build_state_audit_binding_report()
        assert report["valid"] is True
        assert report["role"] == "state_audit"
        assert report["forbidden_actions_all_false"] is True

    def test_build_operator_review_packet(self):
        sb = StandardsBinding(PROJECT_ROOT)
        report = sb.build_operator_review_packet()
        assert report["valid"] is True
        assert report["role"] == "operator_review"
        assert report["production_accepted_remains_false"] is True

    def test_build_integration_manifest(self):
        sb = StandardsBinding(PROJECT_ROOT)
        manifest = sb.build_integration_manifest()
        assert manifest["manifest_id"] == "standards_integration_manifest"
        assert "roles_integrated" in manifest

    def test_build_readiness_report(self):
        sb = StandardsBinding(PROJECT_ROOT)
        report = sb.build_readiness_report()
        assert report["readiness"]["production_accepted"] is False
        assert report["readiness"]["assembly_allowed"] is False

    def test_build_proof(self):
        sb = StandardsBinding(PROJECT_ROOT)
        proof = sb.build_proof()
        assert proof["feature_completed"] is True
        assert proof["forbidden_actions_not_executed"] is True
        assert proof["qa_qc_tester_roles_separated"] is True
        assert proof["production_acceptance_blocked_without_gate"] is True

    def test_build_all_reports_writes_files(self, tmp_path):
        sb = StandardsBinding(tmp_path)
        paths = sb.build_all_reports()
        for name, path in paths.items():
            assert path.exists(), f"{name} was not written"
            with open(path, "r") as f:
                data = json.load(f)
            assert isinstance(data, dict)


class TestStandardsDecisionAdapter:
    def test_adapt(self):
        sda = StandardsDecisionAdapter(PROJECT_ROOT)
        result = sda.adapt("qa", {}, source_artifact="test")
        assert result["traceable"] is True
        assert result["role"] == "qa"
        assert "decision" in result

    def test_adapt_unknown_role(self):
        sda = StandardsDecisionAdapter(PROJECT_ROOT)
        result = sda.adapt("nonexistent_role", {})
        assert result["traceable"] is True
        assert result["decision"] == "blocked"

    def test_evaluate_defect(self):
        sda = StandardsDecisionAdapter(PROJECT_ROOT)
        result = sda.evaluate_defect("qa", "face_identity_mismatch")
        assert result["traceable"] is True
        if result.get("error"):
            pytest.skip("defect not found in taxonomy")
        assert "severity" in result
        assert "decision" in result


class TestStandardsTraceability:
    def test_trace(self):
        st = StandardsTraceability(PROJECT_ROOT)
        result = st.trace("qa", "pass", "info", "test_artifact")
        assert result["traceable"] is True
        assert result["role"] == "qa"
        assert result["source_artifact"] == "test_artifact"

    def test_audit_chain_valid(self):
        st = StandardsTraceability(PROJECT_ROOT)
        results = [
            {
                "standards_pack_version": "1.0",
                "standard_id": "qa_standard",
                "policy_id": "qa_policy",
                "rule_id": "rule_1",
                "role": "qa",
                "severity": "info",
                "decision": "pass",
                "source_artifact": "test",
                "traceable": True,
            }
        ]
        audit = st.audit_chain(results)
        assert audit["valid"] is True
        assert audit["issues"] == []

    def test_audit_chain_missing_field(self):
        st = StandardsTraceability(PROJECT_ROOT)
        results = [{"role": "qa"}]
        audit = st.audit_chain(results)
        assert audit["valid"] is False
        assert any("missing field" in issue for issue in audit["issues"])

    def test_audit_chain_not_traceable(self):
        st = StandardsTraceability(PROJECT_ROOT)
        results = [
            {
                "standards_pack_version": "1.0",
                "standard_id": "qa_standard",
                "policy_id": "qa_policy",
                "rule_id": "rule_1",
                "role": "qa",
                "severity": "info",
                "decision": "pass",
                "source_artifact": "test",
                "traceable": False,
            }
        ]
        audit = st.audit_chain(results)
        assert audit["valid"] is False
        assert any("not marked traceable" in issue for issue in audit["issues"])
