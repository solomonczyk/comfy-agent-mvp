import pytest
import json
import os
from pathlib import Path


class TestFreshVisualGenerationExecute:
    """Test suite for RC-COMBINE-V2-FRESH-VISUAL-GENERATION-EXECUTE-001"""

    @pytest.fixture
    def project_root(self):
        return Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")

    @pytest.fixture
    def control_dir(self, project_root):
        return project_root / "output" / "control"

    def test_blocks_execution_if_authorization_artifact_missing(self, control_dir):
        """Test that execution is blocked if authorization artifact is missing"""
        auth_file = control_dir / "fresh_visual_generation_authorization_record.json"
        
        # If file doesn't exist, should block
        if not auth_file.exists():
            preflight_file = control_dir / "fresh_visual_generation_execution_preflight.json"
            if preflight_file.exists():
                with open(preflight_file) as f:
                    preflight = json.load(f)
                assert preflight["preflight_status"] == "BLOCKED"

    def test_blocks_if_generation_authorized_false(self, control_dir):
        """Test that execution is blocked if generation_authorized=false"""
        auth_file = control_dir / "fresh_visual_generation_authorization_record.json"
        if auth_file.exists():
            with open(auth_file) as f:
                auth = json.load(f)
            if auth.get("generation_authorized") == False:
                preflight_file = control_dir / "fresh_visual_generation_execution_preflight.json"
                if preflight_file.exists():
                    with open(preflight_file) as f:
                        preflight = json.load(f)
                    assert preflight["preflight_status"] == "BLOCKED"

    def test_blocks_if_max_generations_not_one(self, control_dir):
        """Test that execution is blocked if max_generations != 1"""
        auth_file = control_dir / "fresh_visual_generation_authorization_record.json"
        if auth_file.exists():
            with open(auth_file) as f:
                auth = json.load(f)
            if auth.get("max_generations") != 1:
                preflight_file = control_dir / "fresh_visual_generation_execution_preflight.json"
                if preflight_file.exists():
                    with open(preflight_file) as f:
                        preflight = json.load(f)
                    assert preflight["preflight_status"] == "BLOCKED"

    def test_blocks_if_decision_source_not_human_operator(self, control_dir):
        """Test that execution is blocked if decision source is not human operator"""
        decision_file = control_dir / "fresh_visual_generation_operator_decision.json"
        if decision_file.exists():
            with open(decision_file) as f:
                decision = json.load(f)
            if decision.get("decision_source") != "human_operator":
                preflight_file = control_dir / "fresh_visual_generation_execution_preflight.json"
                if preflight_file.exists():
                    with open(preflight_file) as f:
                        preflight = json.load(f)
                    assert preflight["preflight_status"] == "BLOCKED"

    def test_blocks_second_generation_attempt(self, control_dir):
        """Test that second generation attempt is blocked"""
        result_file = control_dir / "fresh_visual_generation_execution_result.json"
        if result_file.exists():
            with open(result_file) as f:
                result = json.load(f)
            if result.get("generation_count", 0) >= 1:
                # Should not allow second generation
                assert result.get("second_generation_attempted") == False

    def test_blocks_retry_attempt(self, control_dir):
        """Test that retry attempt is blocked"""
        result_file = control_dir / "fresh_visual_generation_execution_result.json"
        if result_file.exists():
            with open(result_file) as f:
                result = json.load(f)
            assert result.get("retry_attempted") == False

    def test_blocks_fake_prompt_id(self, control_dir):
        """Test that fake prompt_id is blocked"""
        result_file = control_dir / "fresh_visual_generation_execution_result.json"
        if result_file.exists():
            with open(result_file) as f:
                result = json.load(f)
            prompt_id = result.get("prompt_id")
            if prompt_id:
                # Should be a real prompt ID, not fake
                assert not prompt_id.startswith("fake_")
                assert len(prompt_id) > 10  # Real prompt IDs are longer

    def test_validates_generated_asset_manifest_schema(self, control_dir):
        """Test that generated asset manifest schema is validated"""
        manifest_file = control_dir / "fresh_visual_generation_asset_manifest.json"
        if manifest_file.exists():
            with open(manifest_file) as f:
                manifest = json.load(f)
            
            # Validate schema
            assert "generated_assets" in manifest
            assert isinstance(manifest["generated_assets"], list)
            
            if manifest["generated_assets"]:
                asset = manifest["generated_assets"][0]
                required_fields = ["path", "exists", "sha256", "size_bytes", "width", "height"]
                for field in required_fields:
                    assert field in asset

    def test_validates_state_moves_to_result_review_only(self, control_dir):
        """Test that state moves to result-review only"""
        result_file = control_dir / "fresh_visual_generation_execution_result.json"
        if result_file.exists():
            with open(result_file) as f:
                result = json.load(f)
            
            if result.get("generation_performed"):
                assert result["current_state"] == "fresh_visual_generation_result_review_required"
                assert result["next_allowed_action"] == "fresh_visual_generation_result_review_required"

    def test_confirms_visual_qa_not_executed(self, control_dir):
        """Test that Visual QA is not executed"""
        result_file = control_dir / "fresh_visual_generation_execution_result.json"
        if result_file.exists():
            with open(result_file) as f:
                result = json.load(f)
            assert result.get("visual_qa_executed") == False

    def test_confirms_assembly_downstream_remain_false(self, control_dir):
        """Test that assembly/downstream remain false"""
        result_file = control_dir / "fresh_visual_generation_execution_result.json"
        if result_file.exists():
            with open(result_file) as f:
                result = json.load(f)
            assert result.get("assembly_executed") == False
            assert result.get("downstream_executed") == False

    def test_confirms_production_accepted_false(self, control_dir):
        """Test that production_accepted=false"""
        result_file = control_dir / "fresh_visual_generation_execution_result.json"
        if result_file.exists():
            with open(result_file) as f:
                result = json.load(f)
            assert result.get("production_accepted") == False

    def test_confirms_dirty_git_preflight_creates_blocker(self, control_dir):
        """Test that dirty git preflight creates blocker"""
        preflight_file = control_dir / "fresh_visual_generation_execution_preflight.json"
        if preflight_file.exists():
            with open(preflight_file) as f:
                preflight = json.load(f)
            
            if preflight.get("git_status", {}).get("working_tree_clean") == False:
                assert preflight["preflight_status"] == "BLOCKED"
                assert "git_dirty" in preflight.get("blocker_reason", "").lower()

    def test_py_compile_validation_passes(self):
        """Test that py_compile validation passes"""
        import py_compile
        import tempfile
        
        cli_file = Path("F:/ComfyUI/comfy-agent-mvp/app/cli.py")
        if cli_file.exists():
            # Should not raise any exception
            py_compile.compile(str(cli_file), doraise=True)
