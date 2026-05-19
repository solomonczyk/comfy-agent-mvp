"""Tests for operator reference decision capture.

Tests cover:
- Full folder inventory is used, not only old 24 packet
- Operator decision source is human/operator, not agent-generated
- production_accepted remains false
- Forbidden actions remain false
- State/index/ledger are consistent
- Old 24-packet mismatch/reconciliation
- Human operator decision capture
- No fake decision
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from app.agents.operator_reference_decision_capture import OperatorReferenceDecisionCapture


class TestOperatorReferenceDecisionCapture:
    """Test suite for operator reference decision capture."""
    
    @pytest.fixture
    def project_root(self, tmp_path):
        """Create a temporary project root with canonical references."""
        project_root = tmp_path / "rc2_multishot1_ep01"
        project_root.mkdir()
        
        # Create directory structure
        input_dir = project_root / "input" / "canonical_references"
        input_dir.mkdir(parents=True)
        
        # Create output control directory
        output_dir = project_root / "output" / "control"
        output_dir.mkdir(parents=True)
        
        # Create operator review directory
        operator_review_dir = output_dir / "operator_reference_review"
        operator_review_dir.mkdir(parents=True)
        
        return project_root
    
    @pytest.fixture
    def capture_agent(self, project_root):
        """Create capture agent instance."""
        return OperatorReferenceDecisionCapture(str(project_root))
    
    def test_scan_folder_inventory_creates_full_inventory(self, project_root, capture_agent):
        """Test that full folder inventory is created, not just old packet."""
        # Create test images
        input_dir = project_root / "input" / "canonical_references"
        test_image = input_dir / "test.png"
        
        # Create a minimal PNG file (1x1 pixel)
        test_image.write_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        inventory = capture_agent.scan_folder_inventory()
        
        assert len(inventory) == 1
        assert inventory[0]["filename"] == "test.png"
        assert inventory[0]["extension"] == ".png"
        assert inventory[0]["detected_image_readable"] == True
        assert inventory[0]["width"] == 1
        assert inventory[0]["height"] == 1
        assert inventory[0]["sha256"] is not None
        assert len(inventory[0]["sha256"]) == 64  # SHA256 hex string length
    
    def test_reconciliation_with_matching_packet(self, project_root, capture_agent):
        """Test reconciliation when old packet matches folder inventory."""
        # Create test inventory
        input_dir = project_root / "input" / "canonical_references"
        test_image = input_dir / "test.png"
        test_image.write_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        inventory = capture_agent.scan_folder_inventory()
        
        # Create old packet with matching file
        operator_review_dir = project_root / "output" / "control" / "operator_reference_review"
        old_packet = {
            "reference_summary": {"total_references": 1},
            "reference_slots": [
                {
                    "slot_id": "test_slot",
                    "files": [
                        {
                            "sha256": inventory[0]["sha256"],
                            "filename": "test.png"
                        }
                    ]
                }
            ]
        }
        
        with open(operator_review_dir / "operator_reference_review_packet.json", 'w') as f:
            json.dump(old_packet, f)
        
        reconciliation = capture_agent.reconcile_with_old_packet(inventory)
        
        assert reconciliation["previous_validated_count"] == 1
        assert reconciliation["full_folder_count"] == 1
        assert reconciliation["packet_is_partial"] == False
        assert reconciliation["sha256_matches"] == True
        assert reconciliation["old_packet_found"] == True
        assert "match" in reconciliation["mismatch_details"].lower()
    
    def test_reconciliation_with_mismatched_packet(self, project_root, capture_agent):
        """Test reconciliation when old packet has different count."""
        # Create test inventory with 2 files
        input_dir = project_root / "input" / "canonical_references"
        
        for i in range(2):
            test_image = input_dir / f"test{i}.png"
            test_image.write_bytes(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
                b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
                b'\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
            )
        
        inventory = capture_agent.scan_folder_inventory()
        
        # Create old packet with only 1 file
        operator_review_dir = project_root / "output" / "control" / "operator_reference_review"
        old_packet = {
            "reference_summary": {"total_references": 1},
            "reference_slots": [
                {
                    "slot_id": "test_slot",
                    "files": [
                        {
                            "sha256": inventory[0]["sha256"],
                            "filename": "test0.png"
                        }
                    ]
                }
            ]
        }
        
        with open(operator_review_dir / "operator_reference_review_packet.json", 'w') as f:
            json.dump(old_packet, f)
        
        reconciliation = capture_agent.reconcile_with_old_packet(inventory)
        
        assert reconciliation["previous_validated_count"] == 1
        assert reconciliation["full_folder_count"] == 2
        assert reconciliation["packet_is_partial"] == True
        assert "files" in reconciliation["mismatch_details"]
    
    def test_operator_decision_source_is_human(self, project_root, capture_agent):
        """Test that operator decision source is human, not agent-generated."""
        inventory = []
        reconciliation = {"packet_is_partial": False}
        
        decision = capture_agent.create_operator_decision_artifact(
            operator="Андрей",
            decision_source="human_operator_manual_review",
            decision_text="Я вручную просмотрел все изображения",
            reference_scope="all_images_in_input_canonical_references",
            accepted=True,
            reconciliation=reconciliation,
            inventory=inventory
        )
        
        assert decision["decision_source"] == "human_operator_manual_review"
        assert decision["operator"] == "Андрей"
        assert decision["decision_text"] == "Я вручную просмотрел все изображения"
    
    def test_production_accepted_remains_false(self, project_root, capture_agent):
        """Test that production_accepted remains false after capture."""
        inventory = []
        reconciliation = {"packet_is_partial": False}
        
        decision = capture_agent.create_operator_decision_artifact(
            operator="Андрей",
            decision_source="human_operator_manual_review",
            decision_text="Test decision",
            reference_scope="all_images_in_input_canonical_references",
            accepted=True,
            reconciliation=reconciliation,
            inventory=inventory
        )
        
        assert decision["forbidden_actions"]["production_accepted"] == False
        assert decision["forbidden_actions"]["generation_performed"] == False
        assert decision["forbidden_actions"]["retry_attempted"] == False
        assert decision["forbidden_actions"]["comfyui_submit_executed"] == False
        assert decision["forbidden_actions"]["assembly_executed"] == False
        assert decision["forbidden_actions"]["downstream_executed"] == False
    
    def test_forbidden_actions_not_executed(self, project_root, capture_agent):
        """Test that all forbidden actions remain false."""
        inventory = []
        reconciliation = {"packet_is_partial": False}
        
        decision = capture_agent.create_operator_decision_artifact(
            operator="Андрей",
            decision_source="human_operator_manual_review",
            decision_text="Test decision",
            reference_scope="all_images_in_input_canonical_references",
            accepted=True,
            reconciliation=reconciliation,
            inventory=inventory
        )
        
        forbidden = decision["forbidden_actions"]
        assert all(value == False for value in forbidden.values())
    
    def test_state_transition_updates_correctly(self, project_root, capture_agent):
        """Test that state transition is correct."""
        inventory = []
        reconciliation = {"packet_is_partial": False}
        
        decision = capture_agent.create_operator_decision_artifact(
            operator="Андрей",
            decision_source="human_operator_manual_review",
            decision_text="Test decision",
            reference_scope="all_images_in_input_canonical_references",
            accepted=True,
            reconciliation=reconciliation,
            inventory=inventory
        )
        
        assert decision["state_transition"]["from_state"] == "manual_operator_reference_review"
        assert decision["state_transition"]["to_state"] == "operator_reference_decision_captured"
        assert decision["state_transition"]["next_allowed_action"] == "reference_set_intake_validation"
    
    def test_save_artifacts_creates_files(self, project_root, capture_agent):
        """Test that save_artifacts creates all required files."""
        inventory = [{"reference_id": "test", "sha256": "abc123"}]
        reconciliation = {"packet_is_partial": False}
        decision = {"task_id": "test"}
        
        artifacts = capture_agent.save_artifacts(inventory, reconciliation, decision)
        
        assert "canonical_reference_inventory" in artifacts
        assert "operator_reference_review_reconciliation" in artifacts
        assert "operator_reference_decision" in artifacts
        
        # Verify files exist
        for artifact_path in artifacts.values():
            assert Path(artifact_path).exists()
    
    def test_update_state_files_updates_state_json(self, project_root, capture_agent):
        """Test that update_state_files updates state.json correctly."""
        output_dir = project_root / "output" / "control"
        
        # Create initial state
        state_path = output_dir / "state.json"
        initial_state = {
            "current_state": "manual_operator_reference_review",
            "production_accepted": False
        }
        with open(state_path, 'w') as f:
            json.dump(initial_state, f)
        
        inventory = []
        reconciliation = {"packet_is_partial": False}
        decision = capture_agent.create_operator_decision_artifact(
            operator="Андрей",
            decision_source="human_operator_manual_review",
            decision_text="Test decision",
            reference_scope="all_images_in_input_canonical_references",
            accepted=True,
            reconciliation=reconciliation,
            inventory=inventory
        )
        artifacts = {
            "canonical_reference_inventory": "test_inventory_path",
            "operator_reference_review_reconciliation": "test_reconciliation_path",
            "operator_reference_decision": "test_decision_path"
        }
        
        capture_agent.update_state_files(decision, artifacts, reconciliation)
        
        # Verify state updated
        with open(state_path, 'r', encoding='utf-8') as f:
            updated_state = json.load(f)
        
        assert updated_state["current_state"] == "operator_reference_decision_captured"
        assert updated_state["next_allowed_action"] == "reference_set_intake_validation"
        assert updated_state["production_accepted"] == False
        assert updated_state["operator_reference_decision_captured"] == True
    
    def test_update_state_files_updates_artifact_index(self, project_root, capture_agent):
        """Test that update_state_files updates artifact_index.json correctly."""
        output_dir = project_root / "output" / "control"
        
        # Create initial artifact index
        index_path = output_dir / "artifact_index.json"
        initial_index = {"current_state": "manual_operator_reference_review"}
        with open(index_path, 'w') as f:
            json.dump(initial_index, f)
        
        inventory = []
        reconciliation = {"packet_is_partial": False}
        decision = capture_agent.create_operator_decision_artifact(
            operator="Андрей",
            decision_source="human_operator_manual_review",
            decision_text="Test decision",
            reference_scope="all_images_in_input_canonical_references",
            accepted=True,
            reconciliation=reconciliation,
            inventory=inventory
        )
        artifacts = {
            "canonical_reference_inventory": "test_inventory_path",
            "operator_reference_review_reconciliation": "test_reconciliation_path",
            "operator_reference_decision": "test_decision_path"
        }
        
        capture_agent.update_state_files(decision, artifacts, reconciliation)
        
        # Verify artifact index updated
        with open(index_path, 'r', encoding='utf-8') as f:
            updated_index = json.load(f)
        
        assert updated_index["current_state"] == "operator_reference_decision_captured"
        assert updated_index["operator_reference_decision_captured"] == True
        assert updated_index["canonical_reference_set_accepted"] == True
        assert updated_index["production_accepted"] == False
    
    def test_update_state_files_updates_episode_ledger(self, project_root, capture_agent):
        """Test that update_state_files updates episode_ledger.json correctly."""
        output_dir = project_root / "output" / "control"
        
        # Create initial ledger
        ledger_path = output_dir / "episode_ledger.json"
        initial_ledger = []
        with open(ledger_path, 'w') as f:
            json.dump(initial_ledger, f)
        
        inventory = []
        reconciliation = {"packet_is_partial": False}
        decision = capture_agent.create_operator_decision_artifact(
            operator="Андрей",
            decision_source="human_operator_manual_review",
            decision_text="Test decision",
            reference_scope="all_images_in_input_canonical_references",
            accepted=True,
            reconciliation=reconciliation,
            inventory=inventory
        )
        artifacts = {
            "canonical_reference_inventory": "test_inventory_path",
            "operator_reference_review_reconciliation": "test_reconciliation_path",
            "operator_reference_decision": "test_decision_path"
        }
        
        capture_agent.update_state_files(decision, artifacts, reconciliation)
        
        # Verify ledger updated
        with open(ledger_path, 'r', encoding='utf-8') as f:
            updated_ledger = json.load(f)
        
        assert len(updated_ledger) == 1
        assert updated_ledger[0]["event_type"] == "operator_reference_decision_captured"
        assert updated_ledger[0]["operator"] == "Андрей"
        assert updated_ledger[0]["decision_source"] == "human_operator_manual_review"
        assert updated_ledger[0]["production_accepted"] == False
    
    def test_full_capture_workflow(self, project_root, capture_agent):
        """Test the full capture workflow end-to-end."""
        # Create test images
        input_dir = project_root / "input" / "canonical_references"
        test_image = input_dir / "test.png"
        test_image.write_bytes(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        proof = capture_agent.execute_full_capture(
            operator="Андрей",
            decision_source="human_operator_manual_review",
            decision_text="Я вручную просмотрел все изображения",
            reference_scope="all_images_in_input_canonical_references",
            accepted=True
        )
        
        assert proof["feature_completed"] == True
        assert proof["full_feature_loop_executed"] == True
        assert proof["operator_decision_captured"] == True
        assert proof["operator_decision_source"] == "human_operator_manual_review"
        assert proof["full_canonical_reference_folder_scanned"] == True
        assert proof["canonical_reference_set_accepted"] == True
        assert proof["generation_performed"] == False
        assert proof["production_accepted"] == False
        assert proof["current_state"] == "operator_reference_decision_captured"
        assert proof["next_allowed_action"] == "reference_set_intake_validation"
        assert len(proof["blockers"]) == 0
