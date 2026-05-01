import pytest
import json
import os
import subprocess
import sys
from pathlib import Path
from app.orchestrator.orchestrator import CombineOrchestrator

class TestCombineGenerateAssetsStub:
    """RC-COMBINE-V2-7 — Safe Stub Layer for generate_assets stage tests"""

    @pytest.fixture
    def project_setup(self, tmp_path):
        """Setup a project with required contracts for generation"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # 1. Asset gate (resolved)
        with open(control_dir / "combine_v2_asset_gate_decision.json", 'w') as f:
            json.dump({"inventory": {"hero": "path/to/hero.png"}, "missing_assets": []}, f)
            
        # 2. Authorization decision
        with open(control_dir / "combine_v2_generation_authorization_decision.json", 'w') as f:
            json.dump({
                "authorization_required": True,
                "generation_authorized": True
            }, f)
            
        # 3. Payload stub
        with open(control_dir / "combine_v2_generation_payload_stub.json", 'w') as f:
            json.dump({"is_stub": True}, f)
            
        # 4. Other stubs
        with open(control_dir / "combine_v2_workflow_contract.json", 'w') as f:
            json.dump({"workflow_id": "test_wf"}, f)
        with open(control_dir / "combine_v2_prompt_contract.json", 'w') as f:
            json.dump({"prompts": ["test prompt 1", "test prompt 2"]}, f)
            
        # 5. Operator authorization (closed by default)
        with open(control_dir / "combine_v2_operator_generation_authorization.json", 'w') as f:
            json.dump({"generation_gate_open": False}, f)
            
        # 6. Mock orchestrator state
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump({
                "current_state": "operator_generation_authorization_required",
                "route_family": "portrait_character_identity"
            }, f)
            
        return tmp_path

    def run_cli(self, args):
        """Run CLI in a subprocess to avoid argparse state issues"""
        cmd = [sys.executable, "-m", "app.cli"] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result

    def test_generate_assets_blocked_when_gate_closed(self, project_setup):
        """Verify that generate_assets is blocked if operator gate is closed"""
        project_root = str(project_setup)
        
        # Run CLI command
        result = self.run_cli(["combine-run-stage", "--project-root", project_root, "--stage", "generate_assets", "--json"])
        
        # In this case, success=False because the agent returned status="blocked"
        assert result.returncode == 1
        
        data = json.loads(result.stdout)
        assert data["status"] == "error"
        assert "gate is closed" in data["metadata"]["message"].lower()
        
        # Verify orchestrator state reflects the attempt but stays blocked
        orchestrator = CombineOrchestrator(project_root)
        status = orchestrator.get_status()
        assert status.current_state == "generate_assets"
        assert status.next_allowed_action == "operator_generation_authorization_required"

    def test_generate_assets_creates_execution_plan_when_gate_open(self, project_setup):
        """Verify that generate_assets creates artifacts and transitions when gate is open"""
        project_root = str(project_setup)
        control_dir = project_setup / "output" / "control"
        
        # Open the gate
        with open(control_dir / "combine_v2_operator_generation_authorization.json", 'w') as f:
            json.dump({"generation_gate_open": True}, f)
            
        # Run CLI command
        result = self.run_cli(["combine-run-stage", "--project-root", project_root, "--stage", "generate_assets", "--json"])
        
        assert result.returncode == 0
        
        # Verify artifacts
        plan_file = control_dir / "combine_v2_generation_execution_plan.json"
        result_file = control_dir / "combine_v2_generation_execution_stub_result.json"
        trace_file = control_dir / "combine_v2_generation_trace_stub.json"
        
        assert plan_file.exists()
        assert result_file.exists()
        assert trace_file.exists()
        
        with open(plan_file, 'r') as f:
            plan = json.load(f)
            assert plan["workflow_id"] == "test_wf"
            assert plan["prompt_count"] == 2
            assert plan["execution_strategy"] == "stub_only"
            
        with open(result_file, 'r') as f:
            res = json.load(f)
            assert res["status"] == "stubbed_ready"
            assert res["generation_performed"] is False
            assert res["comfyui_execution"] is False
            assert res["generated_assets"] == []
            assert res["next_allowed_action"] == "visual_qa_required_stub_pending"
            
        with open(trace_file, 'r') as f:
            trace = json.load(f)
            assert "trace_id" in trace
            assert len(trace["events"]) > 0
            
        # Verify orchestrator state
        orchestrator = CombineOrchestrator(project_root)
        status = orchestrator.get_status()
        assert status.current_state == "generate_assets"
        assert status.next_allowed_action == "visual_qa_required_stub_pending"

    def test_safety_boundaries_preserved(self, project_setup):
        """Verify that no real generation or side effects occur"""
        project_root = str(project_setup)
        control_dir = project_setup / "output" / "control"
        
        # Open the gate
        with open(control_dir / "combine_v2_operator_generation_authorization.json", 'w') as f:
            json.dump({"generation_gate_open": True}, f)
            
        # Run CLI command
        result = self.run_cli(["combine-run-stage", "--project-root", project_root, "--stage", "generate_assets", "--json"])
        
        assert result.returncode == 0
        
        # Verify no generation artifacts in output (only control should exist)
        output_dir = project_setup / "output"
        items = [p.name for p in output_dir.iterdir()]
        assert "control" in items
        assert len(items) == 1 # Only 'control' directory
        
        # Verify safety flags in CLI output
        data = json.loads(result.stdout)
        assert data["generation_performed"] is False
        assert data["comfyui_execution"] is False
        
    def test_transition_to_visual_qa_required(self, project_setup):
        """Verify full progression from generate_assets to visual_qa_required"""
        project_root = str(project_setup)
        control_dir = project_setup / "output" / "control"
        
        # Open the gate
        with open(control_dir / "combine_v2_operator_generation_authorization.json", 'w') as f:
            json.dump({"generation_gate_open": True}, f)
            
        orchestrator = CombineOrchestrator(project_root)
        
        # 1. Run generate_assets
        res1 = orchestrator.run_stage("generate_assets")
        assert res1.success
        assert orchestrator.get_status().current_state == "generate_assets"
        assert orchestrator.get_status().next_allowed_action == "visual_qa_required_stub_pending"
        
        # 2. Run visual_qa_required_stub_pending
        res2 = orchestrator.run_stage("visual_qa_required_stub_pending")
        assert res2.success
        assert orchestrator.get_status().current_state == "visual_qa_required_stub_pending"
        assert orchestrator.get_status().next_allowed_action == "visual_qa_required"
        
        # 3. Run visual_qa_required
        res3 = orchestrator.run_stage("visual_qa_required")
        assert res3.success
        assert orchestrator.get_status().current_state == "visual_qa_required"
        # From visual_qa_required, next actions are operator_visual_review or retry
        next_states = orchestrator.state_machine.get_allowed_next_states("visual_qa_required")
        assert "operator_visual_review" in next_states
