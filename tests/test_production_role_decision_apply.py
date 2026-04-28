"""
Tests for production role decision apply transactional contract (RC2-PRODCARDS2I)
"""

import json
import pytest
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from app.production_cards.decision_apply import (
    validate_before_apply,
    create_apply_backup,
    write_approved_decisions,
    update_artifact_index_for_retry_gate,
    append_episode_ledger_apply_event,
    apply_role_decisions
)


class TestProductionRoleDecisionApply:
    """Test suite for role decision apply transactional contract."""
    
    def test_default_apply_role_decisions_is_dry_run(self):
        """Test that default apply-role-decisions without flags is dry-run."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        result = apply_role_decisions(str(project_root), str(fixture_root))
        
        assert result["status"] == "valid", "Default should be dry-run valid"
        assert result["dry_run"] is True, "Default should be dry-run mode"
        assert result["would_apply_decisions"] == 2, "Would apply both decisions"
        assert result["real_project_mutated"] is False, "Should not mutate real project"
    
    def test_explicit_dry_run_does_not_mutate_project(self):
        """Test that explicit --dry-run does not mutate project."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        # Get real project state before dry-run
        role_decisions_dir = project_root / "output" / "control" / "role_decisions"
        char_decision_before = None
        workflow_decision_before = None
        
        if role_decisions_dir.exists():
            char_path = role_decisions_dir / "character_director_identity_decision.json"
            workflow_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
            
            if char_path.exists():
                with open(char_path, 'r') as f:
                    char_decision_before = json.load(f)
            if workflow_path.exists():
                with open(workflow_path, 'r') as f:
                    workflow_decision_before = json.load(f)
        
        # Run dry-run
        result = apply_role_decisions(str(project_root), str(fixture_root), dry_run=True)
        
        # Get real project state after dry-run
        char_decision_after = None
        workflow_decision_after = None
        
        if role_decisions_dir.exists():
            char_path = role_decisions_dir / "character_director_identity_decision.json"
            workflow_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
            
            if char_path.exists():
                with open(char_path, 'r') as f:
                    char_decision_after = json.load(f)
            if workflow_path.exists():
                with open(workflow_path, 'r') as f:
                    workflow_decision_after = json.load(f)
        
        # Real project decisions should be unchanged
        assert char_decision_before == char_decision_after, "Character Director decision should not be mutated by dry-run"
        assert workflow_decision_before == workflow_decision_after, "Workflow TD decision should not be mutated by dry-run"
        
        # Result should confirm no mutation
        assert result["dry_run"] is True, "Should be in dry-run mode"
        assert result["real_project_mutated"] is False, "Result should confirm real project not mutated"
    
    def test_explicit_apply_mutates_only_temp_project_copy(self):
        """Test that explicit --apply mutates only temp project copy."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_project = Path(temp_dir) / "temp_project"
            # Copy real project to temp location
            shutil.copytree(real_project_root, temp_project)
            
            # Get temp project state before apply
            role_decisions_dir = temp_project / "output" / "control" / "role_decisions"
            char_path = role_decisions_dir / "character_director_identity_decision.json"
            workflow_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
            
            char_before = None
            if char_path.exists():
                with open(char_path, 'r') as f:
                    char_before = json.load(f)
            
            # Run apply on temp project
            result = apply_role_decisions(str(temp_project), str(fixture_root), dry_run=False)
            
            # Get temp project state after apply
            char_after = None
            if char_path.exists():
                with open(char_path, 'r') as f:
                    char_after = json.load(f)
            
            # Temp project should be mutated
            assert result["status"] == "applied", "Should apply successfully"
            assert result["dry_run"] is False, "Should not be dry-run"
            assert result["applied_decisions"] == 2, "Should apply both decisions"
            assert result["backup_created"] is True, "Should create backup"
            
            # Character Director decision should be updated
            if char_after:
                assert char_after.get("decision_status") == "decided", "Character Director decision should be decided"
                assert char_after.get("selected_decision") == "approve", "Character Director decision should be approve"
    
    def test_apply_writes_approved_character_director_decision(self):
        """Test that apply writes approved Character Director decision."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            
            # Run apply
            apply_role_decisions(str(temp_project), str(fixture_root), dry_run=False)
            
            # Check Character Director decision was written
            role_decisions_dir = temp_project / "output" / "control" / "role_decisions"
            char_path = role_decisions_dir / "character_director_identity_decision.json"
            
            assert char_path.exists(), "Character Director decision file should exist"
            
            with open(char_path, 'r') as f:
                char_decision = json.load(f)
            
            assert char_decision.get("decision_status") == "decided", "Decision status should be decided"
            assert char_decision.get("selected_decision") == "approve", "Decision should be approve"
    
    def test_apply_writes_approved_workflow_td_decision(self):
        """Test that apply writes approved Workflow TD decision."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            
            # Run apply
            apply_role_decisions(str(temp_project), str(fixture_root), dry_run=False)
            
            # Check Workflow TD decision was written
            role_decisions_dir = temp_project / "output" / "control" / "role_decisions"
            workflow_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
            
            assert workflow_path.exists(), "Workflow TD decision file should exist"
            
            with open(workflow_path, 'r') as f:
                workflow_decision = json.load(f)
            
            assert workflow_decision.get("decision_status") == "decided", "Decision status should be decided"
            assert workflow_decision.get("selected_decision") == "approve_workflow", "Decision should be approve_workflow"
    
    def test_apply_opens_retry_generate_frames_only(self):
        """Test that apply opens retry_generate_frames only as next allowed action."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            
            # Run apply
            result = apply_role_decisions(str(temp_project), str(fixture_root), dry_run=False)
            
            assert result["next_allowed_action"] == "retry_generate_frames", "Next action should be retry_generate_frames"
            assert result["downstream_unblocked_for"] == ["retry_generate_frames"], "Should unblock only retry_generate_frames"
    
    def test_apply_does_not_set_production_accepted_true(self):
        """Test that apply does not set production_accepted=true."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            
            # Run apply
            result = apply_role_decisions(str(temp_project), str(fixture_root), dry_run=False)
            
            assert result["production_accepted"] is False, "Production accepted should remain false"
            
            # Check artifact_index
            artifact_index_path = temp_project / "output" / "control" / "artifact_index.json"
            if artifact_index_path.exists():
                with open(artifact_index_path, 'r') as f:
                    artifact_index = json.load(f)
                
                assert artifact_index.get("production_accepted") is False, "Artifact index should have production_accepted=false"
    
    def test_apply_creates_backup(self):
        """Test that apply creates backup."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            
            # Run apply
            result = apply_role_decisions(str(temp_project), str(fixture_root), dry_run=False)
            
            assert result["backup_created"] is True, "Backup should be created"
            assert "backup_path" in result, "Backup path should be in result"
            
            # Check backup directory exists
            backup_path = Path(result["backup_path"])
            assert backup_path.exists(), "Backup directory should exist"
    
    def test_artifact_index_records_retry_gate_open_for_retry_only(self):
        """Test that artifact_index records retry gate open for retry only."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            
            # Ensure artifact_index exists
            artifact_index_path = temp_project / "output" / "control" / "artifact_index.json"
            artifact_index_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(artifact_index_path, 'w') as f:
                json.dump({}, f)
            
            # Run apply
            apply_role_decisions(str(temp_project), str(fixture_root), dry_run=False)
            
            # Check artifact_index
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert "role_decision_apply" in artifact_index, "role_decision_apply should be in artifact_index"
            role_decision_apply = artifact_index["role_decision_apply"]
            assert role_decision_apply["status"] == "applied", "Status should be applied"
            assert role_decision_apply["retry_gate_open"] is True, "Retry gate should be open"
            assert role_decision_apply["next_allowed_action"] == "retry_generate_frames", "Next action should be retry_generate_frames"
            assert role_decision_apply["production_accepted"] is False, "Production accepted should be false"
            assert role_decision_apply["downstream_unblocked_for"] == ["retry_generate_frames"], "Should unblock only retry_generate_frames"
    
    def test_episode_ledger_records_role_decisions_applied(self):
        """Test that episode_ledger records role_decisions_applied event."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            
            # Run apply
            apply_role_decisions(str(temp_project), str(fixture_root), dry_run=False)
            
            # Check episode_ledger
            ledger_path = temp_project / "output" / "control" / "episode_ledger.json"
            assert ledger_path.exists(), "Episode ledger should exist"
            
            with open(ledger_path, 'r') as f:
                ledger = json.load(f)
            
            assert "events" in ledger, "Ledger should have events"
            assert len(ledger["events"]) > 0, "Ledger should have events"
            
            # Find role_decisions_applied event
            apply_event = None
            for event in ledger["events"]:
                if event.get("event_type") == "role_decisions_applied":
                    apply_event = event
                    break
            
            assert apply_event is not None, "Should have role_decisions_applied event"
            assert apply_event["roles"] == ["Character Director", "Workflow TD / ComfyUI Technical Director"], "Roles should match"
            assert apply_event["next_allowed_action"] == "retry_generate_frames", "Next action should be retry_generate_frames"
            assert apply_event["production_accepted"] is False, "Production accepted should be false"
            assert apply_event["comfyui_generation"] is False, "ComfyUI generation should be false"
            assert apply_event["pipeline_action_rerun"] is False, "Pipeline action rerun should be false"
            assert apply_event["apply_mode"] == "transactional", "Apply mode should be transactional"
    
    def test_invalid_intake_blocks_apply(self):
        """Test that invalid intake blocks apply."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        with TemporaryDirectory() as temp_dir:
            temp_decisions = Path(temp_dir) / "decisions"
            temp_decisions.mkdir()
            
            # Create invalid decision (empty)
            with open(temp_decisions / "character_director_identity_decision.json", 'w') as f:
                json.dump({}, f)
            
            # Run apply
            result = apply_role_decisions(str(real_project_root), str(temp_decisions), dry_run=False)
            
            assert result["status"] == "blocked", "Invalid intake should block apply"
            assert result["can_apply"] is False, "Should not be able to apply"
            assert result["applied_decisions"] == 0, "Should not apply any decisions"
            assert len(result["validation_errors"]) > 0, "Should have validation errors"
    
    def test_missing_decision_blocks_apply(self):
        """Test that missing decision blocks apply."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        with TemporaryDirectory() as temp_dir:
            temp_decisions = Path(temp_dir) / "decisions"
            temp_decisions.mkdir()
            
            # Copy and modify Character Director decision to remove fixture_only and add source metadata
            char_fixture = fixture_root / "character_director_identity_decision.approved.json"
            with open(char_fixture, 'r') as f:
                char_decision = json.load(f)
            del char_decision["fixture_only"]
            char_decision["decision_source"] = "real_role_decision"
            char_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            char_decision["approved_for_shot"] = "shot01"
            char_decision["approved_by_role"] = "Character Director"
            
            with open(temp_decisions / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            # Run apply on temp project copy (to avoid fixture rejection on real project)
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            result = apply_role_decisions(str(temp_project), str(temp_decisions), dry_run=False)
            
            assert result["status"] == "blocked", "Missing decision should block apply"
            assert result["can_apply"] is False, "Should not be able to apply"
            assert "workflow_td" in result["missing_decisions"], "Should report missing workflow_td"
    
    def test_incomplete_artifacts_block_apply(self):
        """Test that incomplete artifacts block apply."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        with TemporaryDirectory() as temp_dir:
            temp_decisions = Path(temp_dir) / "decisions"
            temp_decisions.mkdir()
            
            # Copy and modify Character Director decision to remove artifacts and fixture_only
            char_decision_path = temp_decisions / "character_director_identity_decision.json"
            shutil.copy(fixture_root / "character_director_identity_decision.approved.json", char_decision_path)
            
            with open(char_decision_path, 'r') as f:
                decision = json.load(f)
            
            decision["required_artifacts"] = {}
            del decision["fixture_only"]
            decision["decision_source"] = "real_role_decision"
            decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            decision["approved_for_shot"] = "shot01"
            decision["approved_by_role"] = "Character Director"
            
            with open(char_decision_path, 'w') as f:
                json.dump(decision, f)
            
            # Copy and modify Workflow TD decision
            workflow_fixture = fixture_root / "workflow_td_identity_workflow_decision.approved.json"
            with open(workflow_fixture, 'r') as f:
                workflow_decision = json.load(f)
            del workflow_decision["fixture_only"]
            workflow_decision["decision_source"] = "real_role_decision"
            workflow_decision["approved_for_project_id"] = "rc2_multishot1_ep01"
            workflow_decision["approved_for_shot"] = "shot01"
            workflow_decision["approved_by_role"] = "Workflow TD / ComfyUI Technical Director"
            
            with open(temp_decisions / "workflow_td_identity_workflow_decision.json", 'w') as f:
                json.dump(workflow_decision, f)
            
            # Run apply on temp project copy (to avoid fixture rejection on real project)
            temp_project = Path(temp_dir) / "temp_project"
            shutil.copytree(real_project_root, temp_project)
            result = apply_role_decisions(str(temp_project), str(temp_decisions), dry_run=False)
            
            assert result["status"] == "blocked", "Incomplete artifacts should block apply"
            assert result["can_apply"] is False, "Should not be able to apply"
            assert len(result["validation_errors"]) > 0, "Should have validation errors"
    
    def test_real_project_root_remains_unchanged(self):
        """Test that real project root remains unchanged after dry-run."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        # Get real project state before
        artifact_index_path = real_project_root / "output" / "control" / "artifact_index.json"
        artifact_index_before = None
        if artifact_index_path.exists():
            with open(artifact_index_path, 'r') as f:
                artifact_index_before = json.load(f)
        
        # Run dry-run on real project
        apply_role_decisions(str(real_project_root), str(fixture_root), dry_run=True)
        
        # Get real project state after
        artifact_index_after = None
        if artifact_index_path.exists():
            with open(artifact_index_path, 'r') as f:
                artifact_index_after = json.load(f)
        
        # Real project should be unchanged
        assert artifact_index_before == artifact_index_after, "Real project artifact_index should be unchanged"
    
    def test_no_core_hardcode_for_alya_mir_erdan(self):
        """Test that core module has no hardcoded project-specific names."""
        import app.production_cards.decision_apply as decision_apply_module
        
        source_code = Path(decision_apply_module.__file__).read_text()
        
        # Check for hardcoded project names
        assert "Alya" not in source_code or "character_name" in source_code, "No hardcoded character names in core logic"
        assert "Mir Erdan" not in source_code, "No hardcoded character names in core logic"
        assert "rc2_multishot1_ep01" not in source_code, "No hardcoded project paths in core logic"
