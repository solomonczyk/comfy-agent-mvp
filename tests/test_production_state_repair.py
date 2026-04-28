"""
Tests for production state repair module (RC2-PRODCARDS2K)

Tests for detecting and repairing pre-fix fixture approval mutations
in real project state.
"""

import json
import pytest
from pathlib import Path
from app.production_cards.state_repair import (
    inspect_real_project_decision_state,
    detect_pre_fix_fixture_apply_mutations,
    repair_pre_fix_fixture_apply_mutations
)


class TestProductionStateRepair:
    """Test suite for production state repair functionality."""
    
    def test_detects_artifact_index_retry_gate_open_true_as_unsafe(self):
        """Test that retry_gate_open=true in artifact_index is detected as unsafe."""
        # Create a temporary project with corrupted state
        import tempfile
        import shutil
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "selected_decision": None,
                "production_accepted": False
            }
            workflow_decision = {
                "role": "Workflow TD",
                "decision_status": "pending",
                "selected_decision": None,
                "production_accepted": False
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", 'w') as f:
                json.dump(workflow_decision, f)
            
            # Create corrupted artifact_index with retry_gate_open=true
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True,
                "role_decision_apply": {
                    "status": "applied",
                    "retry_gate_open": True,
                    "next_allowed_action": "retry_generate_frames"
                }
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create episode_ledger
            episode_ledger = {
                "events": []
            }
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Detect mutations
            detection = detect_pre_fix_fixture_apply_mutations(str(project_root))
            
            assert detection["requires_repair"] is True
            assert any(m["type"] == "retry_gate_open" for m in detection["mutations_detected"])
    
    def test_detects_role_decision_apply_status_applied_as_unsafe_when_decisions_pending(self):
        """Test that role_decision_apply.status=applied is unsafe when decisions are pending."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "selected_decision": None,
                "production_accepted": False
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            # Create corrupted artifact_index with role_decision_apply.status=applied
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True,
                "role_decision_apply": {
                    "status": "applied"
                }
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create episode_ledger
            episode_ledger = {"events": []}
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Detect mutations
            detection = detect_pre_fix_fixture_apply_mutations(str(project_root))
            
            assert detection["requires_repair"] is True
            assert any(m["type"] == "artifact_index_role_decision_apply_status" for m in detection["mutations_detected"])
    
    def test_detects_ledger_role_decisions_applied_events_as_historical_contamination(self):
        """Test that role_decisions_applied events in ledger are detected as historical contamination."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "production_accepted": False
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            # Create clean artifact_index
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create episode_ledger with historical contamination
            episode_ledger = {
                "events": [
                    {
                        "event_type": "role_decisions_applied",
                        "timestamp": "2026-04-28T12:09:55Z"
                    }
                ]
            }
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Detect mutations
            detection = detect_pre_fix_fixture_apply_mutations(str(project_root))
            
            assert detection["requires_repair"] is True
            assert any(m["type"] == "ledger_historical_contamination" for m in detection["mutations_detected"])
    
    def test_dry_run_repair_does_not_mutate_project(self):
        """Test that dry-run repair does not mutate project files."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "production_accepted": False
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            # Create corrupted artifact_index
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True,
                "role_decision_apply": {
                    "status": "applied",
                    "retry_gate_open": True
                }
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create episode_ledger
            episode_ledger = {"events": []}
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Get original file modification times
            artifact_index_mtime = (project_root / "output" / "control" / "artifact_index.json").stat().st_mtime
            
            # Run dry-run repair
            result = repair_pre_fix_fixture_apply_mutations(str(project_root), dry_run=True)
            
            # Verify dry-run
            assert result["dry_run"] is True
            assert result["repairs_performed"] == 0
            assert result["status"] == "dry_run_complete"
            
            # Verify files were not mutated
            new_artifact_index_mtime = (project_root / "output" / "control" / "artifact_index.json").stat().st_mtime
            assert artifact_index_mtime == new_artifact_index_mtime
    
    def test_apply_repair_closes_retry_gate(self):
        """Test that apply repair closes the retry gate."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "production_accepted": False
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            # Create corrupted artifact_index with retry gate open
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True,
                "role_decision_apply": {
                    "status": "applied",
                    "retry_gate_open": True,
                    "next_allowed_action": "retry_generate_frames"
                }
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create episode_ledger
            episode_ledger = {"events": []}
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Run apply repair
            result = repair_pre_fix_fixture_apply_mutations(str(project_root), dry_run=False)
            
            # Verify repair
            assert result["dry_run"] is False
            assert result["repairs_performed"] > 0
            assert result["validation"]["retry_gate_closed"] is True
            
            # Verify artifact_index was repaired
            with open(project_root / "output" / "control" / "artifact_index.json", 'r') as f:
                repaired_index = json.load(f)
            
            assert repaired_index.get("retry_gate_open") is False
            assert repaired_index.get("next_allowed_action") == "blocked_by_role_approval"
            assert "role_decision_apply" not in repaired_index
    
    def test_apply_repair_does_not_delete_ledger_history(self):
        """Test that apply repair does not delete historical ledger events."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "production_accepted": False
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            # Create clean artifact_index
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create episode_ledger with historical events
            episode_ledger = {
                "events": [
                    {
                        "event_type": "role_decisions_applied",
                        "timestamp": "2026-04-28T12:09:55Z",
                        "reason": "pre-fix fixture application"
                    }
                ]
            }
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Run apply repair
            result = repair_pre_fix_fixture_apply_mutations(str(project_root), dry_run=False)
            
            # Verify historical events are preserved
            with open(project_root / "output" / "control" / "episode_ledger.json", 'r') as f:
                repaired_ledger = json.load(f)
            
            # Original event should still exist
            historical_events = [e for e in repaired_ledger["events"] if e["event_type"] == "role_decisions_applied"]
            assert len(historical_events) == 1
            assert historical_events[0]["timestamp"] == "2026-04-28T12:09:55Z"
    
    def test_apply_repair_appends_pre_fix_fixture_apply_invalidated_event(self):
        """Test that apply repair appends a corrective invalidation event."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "production_accepted": False
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            # Create corrupted artifact_index with role_decision_apply section
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True,
                "role_decision_apply": {
                    "status": "applied",
                    "retry_gate_open": True,
                    "next_allowed_action": "retry_generate_frames"
                }
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create episode_ledger with historical events
            episode_ledger = {"events": []}
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Run apply repair
            result = repair_pre_fix_fixture_apply_mutations(str(project_root), dry_run=False)
            
            # Verify corrective event was added
            with open(project_root / "output" / "control" / "episode_ledger.json", 'r') as f:
                repaired_ledger = json.load(f)
            
            corrective_events = [e for e in repaired_ledger["events"] if e["event_type"] == "pre_fix_fixture_apply_invalidated"]
            assert len(corrective_events) == 1
            assert corrective_events[0]["reason"] == "fixture approvals were applied before safety hardening"
            assert corrective_events[0]["retry_gate_open"] is False
            assert corrective_events[0]["production_accepted"] is False
            assert corrective_events[0]["downstream_blocked"] is True
    
    def test_apply_repair_keeps_production_accepted_false(self):
        """Test that apply repair keeps production_accepted=false."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "production_accepted": False
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            # Create corrupted artifact_index
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True,
                "role_decision_apply": {
                    "status": "applied",
                    "retry_gate_open": True
                }
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create episode_ledger
            episode_ledger = {"events": []}
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Run apply repair
            result = repair_pre_fix_fixture_apply_mutations(str(project_root), dry_run=False)
            
            # Verify production_accepted remains false
            assert result["validation"]["production_accepted_false"] is True
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'r') as f:
                repaired_index = json.load(f)
            
            assert repaired_index.get("production_accepted") is False
    
    def test_apply_repair_keeps_downstream_blocked_true(self):
        """Test that apply repair keeps downstream_blocked=true."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "production_accepted": False
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            
            # Create corrupted artifact_index
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True,
                "role_decision_apply": {
                    "status": "applied",
                    "retry_gate_open": True
                }
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create episode_ledger
            episode_ledger = {"events": []}
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Run apply repair
            result = repair_pre_fix_fixture_apply_mutations(str(project_root), dry_run=False)
            
            # Verify downstream_blocked remains true
            assert result["validation"]["downstream_blocked"] is True
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'r') as f:
                repaired_index = json.load(f)
            
            assert repaired_index.get("downstream_blocked") is True
    
    def test_final_inspect_returns_safe_for_next_step_true_only_when_project_is_blocked_pending_and_no_retry_gate(self):
        """Test that final inspect returns safe_for_next_step=true only when project is blocked/pending and no retry gate is open."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True)
            
            # Create pending role decisions
            char_decision = {
                "role": "Character Director",
                "decision_status": "pending",
                "selected_decision": None,
                "production_accepted": False,
                "downstream_blocked": True
            }
            workflow_decision = {
                "role": "Workflow TD",
                "decision_status": "pending",
                "selected_decision": None,
                "production_accepted": False,
                "downstream_blocked": True
            }
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision, f)
            with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", 'w') as f:
                json.dump(workflow_decision, f)
            
            # Create clean artifact_index
            artifact_index = {
                "production_accepted": False,
                "downstream_blocked": True,
                "retry_gate_open": False,
                "next_allowed_action": "blocked_by_role_approval"
            }
            
            with open(project_root / "output" / "control" / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            # Create clean episode_ledger
            episode_ledger = {"events": []}
            with open(project_root / "output" / "control" / "episode_ledger.json", 'w') as f:
                json.dump(episode_ledger, f)
            
            # Inspect
            inspection = inspect_real_project_decision_state(str(project_root))
            
            # Should be safe
            assert inspection["safe_for_next_step"] is True
            assert inspection["has_corruption"] is False
    
    def test_no_core_hardcode_for_alya_mir_erdan(self):
        """Test that core module has no hardcoded project-specific names."""
        import app.production_cards.state_repair as state_repair_module
        
        source_code = Path(state_repair_module.__file__).read_text()
        
        # Check for hardcoded project names
        assert "Alya" not in source_code or "character_name" in source_code, "No hardcoded character names in core logic"
        assert "Mir Erdan" not in source_code, "No hardcoded character names in core logic"
        assert "rc2_multishot1_ep01" not in source_code, "No hardcoded project paths in core logic"
