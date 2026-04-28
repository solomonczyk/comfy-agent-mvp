"""
Tests for production role decision apply safety (RC2-PRODCARDS2J)
"""

import json
import os
import pytest
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from app.production_cards.decision_apply import (
    validate_decision_source,
    apply_role_decisions
)


class TestProductionRoleDecisionApplySafety:
    """Test suite for role decision apply safety hardening."""
    
    def test_real_project_apply_rejects_fixture_only_decisions(self):
        """Real project apply rejects fixture_only decisions."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        result = apply_role_decisions(str(real_project_root), str(fixture_root), dry_run=False)
        
        assert result["status"] == "rejected", f"Expected rejected, got {result['status']}"
        assert result["reason"] == "fixture_decisions_cannot_be_applied_to_real_project"
        assert result["applied_decisions"] == 0
        assert result["real_project_mutated"] is False
        assert result["production_accepted"] is False
    
    def test_rejection_does_not_mutate_real_project(self):
        """Rejection does not mutate real project."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        artifact_index_path = real_project_root / "output" / "control" / "artifact_index.json"
        before = None
        if artifact_index_path.exists():
            with open(artifact_index_path, 'r') as f:
                before = json.load(f)
        
        result = apply_role_decisions(str(real_project_root), str(fixture_root), dry_run=False)
        
        assert result["real_project_mutated"] is False
        
        after = None
        if artifact_index_path.exists():
            with open(artifact_index_path, 'r') as f:
                after = json.load(f)
        
        assert before == after, "Real project artifact_index should be unchanged after rejection"
    
    def test_dry_run_still_accepts_fixture_approvals_for_contract_proof(self):
        """Dry-run still accepts fixture approvals for contract proof."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        result = apply_role_decisions(str(real_project_root), str(fixture_root), dry_run=True)
        
        assert result["status"] == "valid"
        assert result["dry_run"] is True
        assert result["would_apply_decisions"] == 2
        assert result["real_project_mutated"] is False
    
    def test_real_apply_rejects_missing_decision_source(self):
        """Real apply rejects missing decision_source."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_decisions = Path(temp_dir) / "decisions"
            temp_decisions.mkdir()
            
            # Copy fixture but remove fixture_only and decision_source
            fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
            
            char_fixture = fixture_root / "character_director_identity_decision.approved.json"
            with open(char_fixture, 'r') as f:
                char_decision = json.load(f)
            del char_decision["fixture_only"]
            if "decision_source" in char_decision:
                del char_decision["decision_source"]
            char_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            char_decision["approved_for_shot"] = "shot01"
            char_decision["approved_by_role"] = "Character Director"
            
            with open(temp_decisions / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            workflow_fixture = fixture_root / "workflow_td_identity_workflow_decision.approved.json"
            with open(workflow_fixture, 'r') as f:
                workflow_decision = json.load(f)
            del workflow_decision["fixture_only"]
            if "decision_source" in workflow_decision:
                del workflow_decision["decision_source"]
            workflow_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            workflow_decision["approved_for_shot"] = "shot01"
            workflow_decision["approved_by_role"] = "Workflow TD / ComfyUI Technical Director"
            
            with open(temp_decisions / "workflow_td_identity_workflow_decision.json", 'w') as f:
                json.dump(workflow_decision, f)
            
            result = apply_role_decisions(str(real_project_root), str(temp_decisions), dry_run=False)
            
            assert result["status"] == "blocked"
            assert any("missing decision_source" in err for err in result["validation_errors"])
    
    def test_real_apply_rejects_wrong_decision_source(self):
        """Real apply rejects decision_source != real_role_decision."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_decisions = Path(temp_dir) / "decisions"
            temp_decisions.mkdir()
            
            fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
            
            char_fixture = fixture_root / "character_director_identity_decision.approved.json"
            with open(char_fixture, 'r') as f:
                char_decision = json.load(f)
            del char_decision["fixture_only"]
            char_decision["decision_source"] = "fixture_approval"
            char_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            char_decision["approved_for_shot"] = "shot01"
            char_decision["approved_by_role"] = "Character Director"
            
            with open(temp_decisions / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            workflow_fixture = fixture_root / "workflow_td_identity_workflow_decision.approved.json"
            with open(workflow_fixture, 'r') as f:
                workflow_decision = json.load(f)
            del workflow_decision["fixture_only"]
            workflow_decision["decision_source"] = "fixture_approval"
            workflow_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            workflow_decision["approved_for_shot"] = "shot01"
            workflow_decision["approved_by_role"] = "Workflow TD / ComfyUI Technical Director"
            
            with open(temp_decisions / "workflow_td_identity_workflow_decision.json", 'w') as f:
                json.dump(workflow_decision, f)
            
            result = apply_role_decisions(str(real_project_root), str(temp_decisions), dry_run=False)
            
            assert result["status"] == "blocked"
            assert any("real_role_decision'" in err for err in result["validation_errors"])
    
    def test_real_apply_rejects_mismatched_approved_for_project_id(self):
        """Real apply rejects mismatched approved_for_project_id."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_decisions = Path(temp_dir) / "decisions"
            temp_decisions.mkdir()
            
            fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
            
            char_fixture = fixture_root / "character_director_identity_decision.approved.json"
            with open(char_fixture, 'r') as f:
                char_decision = json.load(f)
            del char_decision["fixture_only"]
            char_decision["decision_source"] = "real_role_decision"
            char_decision["approved_for_project_id"] = "wrong_project"
            char_decision["approved_for_shot"] = "shot01"
            char_decision["approved_by_role"] = "Character Director"
            
            with open(temp_decisions / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            workflow_fixture = fixture_root / "workflow_td_identity_workflow_decision.approved.json"
            with open(workflow_fixture, 'r') as f:
                workflow_decision = json.load(f)
            del workflow_decision["fixture_only"]
            workflow_decision["decision_source"] = "real_role_decision"
            workflow_decision["approved_for_project_id"] = "wrong_project"
            workflow_decision["approved_for_shot"] = "shot01"
            workflow_decision["approved_by_role"] = "Workflow TD / ComfyUI Technical Director"
            
            with open(temp_decisions / "workflow_td_identity_workflow_decision.json", 'w') as f:
                json.dump(workflow_decision, f)
            
            result = apply_role_decisions(str(real_project_root), str(temp_decisions), dry_run=False)
            
            assert result["status"] == "blocked"
            assert any("approved_for_project_id" in err for err in result["validation_errors"])
    
    def test_real_apply_rejects_mismatched_approved_for_shot(self):
        """Real apply rejects mismatched approved_for_shot."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_decisions = Path(temp_dir) / "decisions"
            temp_decisions.mkdir()
            
            fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
            
            char_fixture = fixture_root / "character_director_identity_decision.approved.json"
            with open(char_fixture, 'r') as f:
                char_decision = json.load(f)
            del char_decision["fixture_only"]
            char_decision["decision_source"] = "real_role_decision"
            char_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            char_decision["approved_for_shot"] = "shot99"
            char_decision["approved_by_role"] = "Character Director"
            
            with open(temp_decisions / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            workflow_fixture = fixture_root / "workflow_td_identity_workflow_decision.approved.json"
            with open(workflow_fixture, 'r') as f:
                workflow_decision = json.load(f)
            del workflow_decision["fixture_only"]
            workflow_decision["decision_source"] = "real_role_decision"
            workflow_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            workflow_decision["approved_for_shot"] = "shot99"
            workflow_decision["approved_by_role"] = "Workflow TD / ComfyUI Technical Director"
            
            with open(temp_decisions / "workflow_td_identity_workflow_decision.json", 'w') as f:
                json.dump(workflow_decision, f)
            
            result = apply_role_decisions(str(real_project_root), str(temp_decisions), dry_run=False)
            
            assert result["status"] == "blocked"
            assert any("approved_for_shot" in err for err in result["validation_errors"])
    
    def test_real_apply_rejects_production_accepted_true_in_decision_file(self):
        """Real apply rejects production_accepted=true inside decision file."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_decisions = Path(temp_dir) / "decisions"
            temp_decisions.mkdir()
            
            fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
            
            char_fixture = fixture_root / "character_director_identity_decision.approved.json"
            with open(char_fixture, 'r') as f:
                char_decision = json.load(f)
            del char_decision["fixture_only"]
            char_decision["decision_source"] = "real_role_decision"
            char_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            char_decision["approved_for_shot"] = "shot01"
            char_decision["approved_by_role"] = "Character Director"
            char_decision["production_accepted"] = True
            
            with open(temp_decisions / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            workflow_fixture = fixture_root / "workflow_td_identity_workflow_decision.approved.json"
            with open(workflow_fixture, 'r') as f:
                workflow_decision = json.load(f)
            del workflow_decision["fixture_only"]
            workflow_decision["decision_source"] = "real_role_decision"
            workflow_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            workflow_decision["approved_for_shot"] = "shot01"
            workflow_decision["approved_by_role"] = "Workflow TD / ComfyUI Technical Director"
            workflow_decision["production_accepted"] = True
            
            with open(temp_decisions / "workflow_td_identity_workflow_decision.json", 'w') as f:
                json.dump(workflow_decision, f)
            
            result = apply_role_decisions(str(real_project_root), str(temp_decisions), dry_run=False)
            
            assert result["status"] == "blocked"
            assert any("production_accepted=true" in err for err in result["validation_errors"])
    
    def test_temp_fixture_apply_tests_from_2i_still_pass(self):
        """Temp fixture apply tests from 2I still pass."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            
            os.environ["COMFY_AGENT_TEMP_APPLY"] = "1"
            try:
                result = apply_role_decisions(str(temp_project), str(fixture_root), dry_run=False)
            finally:
                os.environ.pop("COMFY_AGENT_TEMP_APPLY", None)
            
            assert result["status"] == "applied"
            assert result["applied_decisions"] == 2
            assert result["production_accepted"] is False
    
    def test_no_core_hardcode_for_alya_mir_erdan(self):
        """Core module has no hardcoded project-specific names."""
        import app.production_cards.decision_apply as decision_apply_module
        
        source_code = Path(decision_apply_module.__file__).read_text()
        
        assert "Alya" not in source_code or "character_name" in source_code
        assert "Mir Erdan" not in source_code
        assert "rc2_multishot1_ep01" not in source_code
    
    def test_validate_decision_source_fixture_only_short_circuits(self):
        """validate_decision_source returns immediately on fixture_only=true."""
        decision = {"fixture_only": True}
        errors = validate_decision_source(decision, "Character Director", "/some/project", "shot01")
        assert len(errors) == 1
        assert "fixture_only=true" in errors[0]
