import pytest
import json
import os
import subprocess
import sys
from pathlib import Path
from app.orchestrator.orchestrator import CombineOrchestrator

class TestCombineOperatorGenerationGate:
    """RC-COMBINE-V2-6 — Operator Generation Authorization Gate tests"""

    @pytest.fixture
    def project_setup(self, tmp_path):
        """Setup a project with required contracts for authorization"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # 1. Asset gate (resolved)
        with open(control_dir / "combine_v2_asset_gate_decision.json", 'w') as f:
            json.dump({"missing_assets": [], "generation_authorized": False}, f)
            
        # 2. Authorization decision (required)
        with open(control_dir / "combine_v2_generation_authorization_decision.json", 'w') as f:
            json.dump({
                "authorization_required": True,
                "generation_authorized": False
            }, f)
        with open(control_dir / "combine_v2_generation_authorization_request.json", 'w') as f:
            json.dump({
                "generation_authorization_ready": True,
                "authorization_required": True
            }, f)
        with open(control_dir / "combine_v2_generation_payload_stub.json", 'w') as f:
            json.dump({
                "payload_type": "generation_contract_v2",
                "retry_context": {
                    "retry_requested": False,
                    "operator_retry_authorized": False,
                    "retry_gate_open": False,
                    "corrective_plan_applied_to_payload": False,
                    "retry_execution_authorized": False
                }
            }, f)
            
        # 3. Other stubs
        with open(control_dir / "combine_v2_workflow_contract.json", 'w') as f:
            json.dump({"workflow_id": "test_wf"}, f)
        with open(control_dir / "combine_v2_prompt_contract.json", 'w') as f:
            json.dump({"prompts": ["test"]}, f)
        with open(control_dir / "combine_v2_preflight_contract.json", 'w') as f:
            json.dump({"preflight_passed": True}, f)
            
        # 4. Mock orchestrator state
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump({"current_state": "generation_authorization_required"}, f)
            
        return tmp_path

    def run_cli(self, args):
        """Run CLI in a subprocess to avoid argparse state issues"""
        cmd = [sys.executable, "-m", "app.cli"] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result

    def test_gate_opens_when_preconditions_met(self, project_setup):
        """Verify that gate opens and artifact is created when preconditions are met"""
        project_root = str(project_setup)
        
        # Run CLI command
        result = self.run_cli(["combine-authorize-generation", "--project-root", project_root, "--json"])
        
        assert result.returncode == 0
        
        # Verify artifact
        auth_file = project_setup / "output" / "control" / "combine_v2_operator_generation_authorization.json"
        assert auth_file.exists()
        
        with open(auth_file, 'r') as f:
            data = json.load(f)
            assert data["generation_gate_open"] is True
            assert data["next_allowed_action"] == "generate_assets"
            
        # Verify orchestrator state
        orchestrator = CombineOrchestrator(project_root)
        status = orchestrator.get_status()
        assert status.current_state == "operator_generation_authorization_required"
        # From operator_generation_authorization_required, only generate_assets is allowed
        assert status.next_allowed_action == "generate_assets"

    def test_gate_blocked_by_missing_assets(self, project_setup):
        """Verify that gate is blocked if assets are missing"""
        project_root = str(project_setup)
        control_dir = project_setup / "output" / "control"
        
        # Mock missing assets
        with open(control_dir / "combine_v2_asset_gate_decision.json", 'w') as f:
            json.dump({"missing_assets": ["hero_v2"], "generation_authorized": False}, f)
            
        # Run CLI command
        result = self.run_cli(["combine-authorize-generation", "--project-root", project_root, "--json"])
        
        assert result.returncode == 1
        
        # Verify rejection artifact
        rejection_file = project_setup / "output" / "control" / "combine_v2_operator_generation_rejection.json"
        assert rejection_file.exists()
        
        with open(rejection_file, 'r') as f:
            data = json.load(f)
            assert data["generation_gate_open"] is False
            assert "missing assets" in data["rejection_reason"].lower()

    def test_gate_blocked_if_authorization_not_required(self, project_setup):
        """Verify that gate is blocked if authorization is not marked as required"""
        project_root = str(project_setup)
        control_dir = project_setup / "output" / "control"
        
        # Mock auth NOT required
        with open(control_dir / "combine_v2_generation_authorization_decision.json", 'w') as f:
            json.dump({
                "authorization_required": False,
                "generation_authorized": False
            }, f)
            
        # Run CLI command
        result = self.run_cli(["combine-authorize-generation", "--project-root", project_root, "--json"])
        
        assert result.returncode == 1
        
        # Verify rejection artifact
        rejection_file = project_setup / "output" / "control" / "combine_v2_operator_generation_rejection.json"
        assert rejection_file.exists()

    def test_opening_gate_does_not_call_comfyui(self, project_setup):
        """Safety check: opening gate must NOT call ComfyUI or perform generation"""
        project_root = str(project_setup)
        
        # Run CLI command
        result = self.run_cli(["combine-authorize-generation", "--project-root", project_root, "--json"])
        
        assert result.returncode == 0
        
        # Verify no generation artifacts (no frames, no images)
        output_dir = project_setup / "output"
        # Only 'control' should exist in 'output'
        items = [p.name for p in output_dir.iterdir()]
        assert items == ["control"]
        
        # Check orchestrator status for safety flags
        orchestrator = CombineOrchestrator(project_root)
        status = orchestrator.get_status()
        assert status.generation_performed is False
        assert status.comfyui_execution is False

    def test_next_allowed_action_is_generate_assets_only_after_auth(self, tmp_path):
        """Verify state machine progression"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        orchestrator = CombineOrchestrator(str(tmp_path))
        
        # Start at generation_authorization_required
        orchestrator._write_stage_result(type('obj', (object,), {
            "stage": "workflow_preflight_required", "success": True, "message": "", "artifacts": [], "metadata": {}, "timestamp": "", "no_generation_performed": True
        }))
        
        # Next action is generation_authorization_required
        status = orchestrator.get_status()
        assert status.next_allowed_action == "generation_authorization_required"
        
        # Mock the contracts for GenerationAgent to recommend operator auth
        with open(control_dir / "combine_v2_asset_gate_decision.json", 'w') as f:
            json.dump({"missing_assets": [], "generation_authorized": False}, f)
        with open(control_dir / "combine_v2_generation_authorization_decision.json", 'w') as f:
            json.dump({"authorization_required": True, "generation_authorized": False}, f)
        with open(control_dir / "combine_v2_generation_authorization_request.json", 'w') as f:
            json.dump({"generation_authorization_ready": True, "authorization_required": True}, f)
        with open(control_dir / "combine_v2_generation_payload_stub.json", 'w') as f:
            json.dump({"payload_type": "generation_contract_v2", "retry_context": {}}, f)
        with open(control_dir / "combine_v2_workflow_contract.json", 'w') as f:
            json.dump({"workflow_id": "test"}, f)
        with open(control_dir / "combine_v2_prompt_contract.json", 'w') as f:
            json.dump({"prompts": []}, f)
        with open(control_dir / "combine_v2_preflight_contract.json", 'w') as f:
            json.dump({"preflight_passed": True}, f)
            
        # Run generation_authorization_required
        orchestrator.run_stage("generation_authorization_required")
        
        # Now next action should be operator_generation_authorization_required (or asset review)
        status = orchestrator.get_status()
        # Alphabetically, controlled_asset_resolution_review_required comes first
        assert "operator_generation_authorization_required" in orchestrator.state_machine.get_allowed_next_states(status.current_state)
        
        # Now run the CLI command to authorize
        result = self.run_cli(["combine-authorize-generation", "--project-root", str(tmp_path), "--json"])
        
        assert result.returncode == 0
        
        # Now current state is operator_generation_authorization_required and next is generate_assets
        status = orchestrator.get_status()
        assert status.current_state == "operator_generation_authorization_required"
        assert status.next_allowed_action == "generate_assets"
