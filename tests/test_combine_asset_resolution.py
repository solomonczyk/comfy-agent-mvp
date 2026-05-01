import pytest
import json
from pathlib import Path
from app.orchestrator.orchestrator import CombineOrchestrator
from app.agents.asset_resolver_agent import AssetResolverAgent
from app.orchestrator.contracts import CombineRunContext

class TestAssetResolutionLayer:
    """Tests for the controlled asset resolution layer"""

    def test_asset_resolver_agent_reads_requirements(self, tmp_path):
        """Test that AssetResolverAgent reads requirements from the contract file"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        requirements_file = control_dir / "combine_v2_asset_requirements_contract.json"
        requirements_data = {
            "agent": "CreativeDirectorAgent",
            "stage": "production_plan_review",
            "asset_requirements": {
                "characters": ["hero_v2"],
                "environments": ["mars_base"],
                "audio": ["ambient_wind", "special_music"]
            }
        }
        with open(requirements_file, 'w') as f:
            json.dump(requirements_data, f)
            
        agent = AssetResolverAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="asset_resolution_required",
            stage="asset_resolution_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context)
        
        # Verify result contains the expected assets from the file
        inventory = result.metadata.get("combine_v2_asset_inventory_contract", {})
        available = inventory.get("inventory", {}).get("available_assets", {})
        
        assert "hero_v2" in available.get("characters", [])
        assert "mars_base" in available.get("environments", [])
        
    def test_asset_resolution_artifacts_creation(self, tmp_path):
        """Test that all 3 required artifacts are created"""
        orchestrator = CombineOrchestrator(str(tmp_path))
        
        # Setup prerequisite states
        orchestrator.run_stage("brief_intake_required")
        orchestrator.run_stage("route_classification_required")
        orchestrator.run_stage("production_plan_required")
        orchestrator.run_stage("production_plan_review")
        
        # Run asset resolution
        result = orchestrator.run_stage("asset_resolution_required")
        
        assert result.success
        assert "combine_v2_asset_inventory_contract.json" in result.artifacts
        assert "combine_v2_asset_resolution_result.json" in result.artifacts
        assert "combine_v2_asset_gate_decision.json" in result.artifacts
        
        # Check files exist in output/control
        control_dir = tmp_path / "output" / "control"
        assert (control_dir / "combine_v2_asset_inventory_contract.json").exists()
        assert (control_dir / "combine_v2_asset_resolution_result.json").exists()
        assert (control_dir / "combine_v2_asset_gate_decision.json").exists()

    def test_missing_assets_trigger_review_state(self, tmp_path):
        """Test that missing assets lead to controlled_asset_resolution_review_required"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create requirements with something that will be "missing" (background_music in our stub)
        requirements_file = control_dir / "combine_v2_asset_requirements_contract.json"
        with open(requirements_file, 'w') as f:
            json.dump({
                "asset_requirements": {"audio": ["background_music"]}
            }, f)
            
        orchestrator = CombineOrchestrator(str(tmp_path))
        # Mock state to allow asset_resolution_required
        orchestrator._write_stage_result(type('obj', (object,), {
            "stage": "production_plan_review", "success": True, "message": "", "artifacts": [], "metadata": {}, "timestamp": "", "no_generation_performed": True
        }))
        
        result = orchestrator.run_stage("asset_resolution_required")
        
        assert result.metadata["next_recommended_stage"] == "controlled_asset_resolution_review_required"
        
        # Verify resolution result records missing assets
        res_result = result.metadata["combine_v2_asset_resolution_result"]
        assert "background_music" in res_result["missing"]
        assert res_result["manual_review_required"] is True

    def test_no_silent_substitution_and_authorization_flags(self, tmp_path):
        """Verify safety flags are correctly set to False"""
        agent = AssetResolverAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            current_state="asset_resolution_required",
            stage="asset_resolution_required",
            route_family="custom",
            dry_run=True
        )
        
        result = agent.run(context)
        
        # Check AgentResult flags
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        
        # Check metadata flags
        meta = result.metadata
        assert meta["download_authorized"] is False
        assert meta["install_authorized"] is False
        assert meta["silent_substitution"] is False
        
        # Check gate decision
        gate = meta["combine_v2_asset_gate_decision"]
        assert gate["download_authorized"] is False
        assert gate["install_authorized"] is False
        assert gate["generation_authorized"] is False

    def test_artifacts_only_in_output_control(self, tmp_path):
        """Verify no artifacts are created outside output/control"""
        orchestrator = CombineOrchestrator(str(tmp_path))
        orchestrator._write_stage_result(type('obj', (object,), {
            "stage": "production_plan_review", "success": True, "message": "", "artifacts": [], "metadata": {}, "timestamp": "", "no_generation_performed": True
        }))
        
        orchestrator.run_stage("asset_resolution_required")
        
        # List all files in tmp_path recursively
        files = [str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file()]
        
        for f in files:
            # All files should be in output/control
            assert f.startswith("output\\control") or f.startswith("output/control"), f"File {f} is outside output/control"
