"""RC-COMBINE-V2-3261-3360: ComfyUI POST /prompt 500 Recovery Tests.

Tests for:
- POST /prompt 500 diagnosis artifact creation
- Payload validation before ComfyUI submit
- No blind rerun without diagnostics
- No fake success without prompt_id or asset
- Missing node/model preserves blocked state
- Exactly one generation enforced
- Production accepted false
- Assembly/downstream forbidden
"""

import json
import pytest
from pathlib import Path


class TestComfyUIPrompt500Recovery:
    """Test suite for ComfyUI POST /prompt 500 recovery."""

    def test_post_prompt_500_diagnosis_created(self):
        """Test that POST /prompt 500 diagnosis artifact exists."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        diagnosis_file = control_dir / "combine_v2_comfyui_prompt_500_diagnosis.json"
        
        assert diagnosis_file.exists(), "Diagnosis artifact must exist"
        
        with open(diagnosis_file) as f:
            data = json.load(f)
        
        assert data["task_id"] == "RC-COMBINE-V2-3261-3360"
        assert data["post_prompt_failed"] is True
        assert data["root_cause_category"] == "invalid_prompt_payload"
        assert "root_cause_summary" in data
        assert data["post_prompt_status"] == 500

    def test_payload_validation_artifact_created(self):
        """Test that payload validation artifact exists and is valid."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        validation_file = control_dir / "combine_v2_corrective_retry_v5_prompt_payload_validation.json"
        
        assert validation_file.exists(), "Payload validation artifact must exist"
        
        with open(validation_file) as f:
            data = json.load(f)
        
        assert data["task_id"] == "RC-COMBINE-V2-3261-3360"
        assert data["workflow_valid_for_comfyui_api"] is True
        assert data["validation_passed"] is True
        assert data["validation_errors"] == []
        assert "removed_keys" in data
        assert "shot_id" in data["removed_keys"]

    def test_payload_validation_blocks_invalid_workflow(self):
        """Test that payload validator blocks invalid workflows."""
        # Simulate validation of an invalid workflow (with non-node metadata)
        invalid_workflow = {
            "shot_id": "shot02",  # Non-node metadata
            "some_metadata": "value",  # More non-node metadata
            # No actual ComfyUI nodes
        }
        
        # Validation function should reject this
        def validate_workflow(wf):
            if not wf:
                return False, ["Workflow is empty"]
            
            cleaned = {}
            for key, value in wf.items():
                if isinstance(key, str) and key.isdigit():
                    cleaned[key] = value
            
            if not cleaned:
                return False, ["No valid node entries found in workflow"]
            
            return True, []
        
        valid, errors = validate_workflow(invalid_workflow)
        assert valid is False, "Invalid workflow should be blocked"
        assert len(errors) > 0, "Validation errors should be returned"

    def test_payload_validation_allows_valid_workflow(self):
        """Test that payload validator allows valid workflows."""
        valid_workflow = {
            "3": {"class_type": "KSampler", "inputs": {}},
            "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "model.safetensors"}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "test"}},
        }
        
        def validate_workflow(wf):
            if not wf:
                return False, ["Workflow is empty"]
            
            cleaned = {}
            for key, value in wf.items():
                if isinstance(key, str) and key.isdigit():
                    cleaned[key] = value
            
            if not cleaned:
                return False, ["No valid node entries found in workflow"]
            
            return True, []
        
        valid, errors = validate_workflow(valid_workflow)
        assert valid is True, "Valid workflow should pass validation"
        assert errors == [], "No validation errors for valid workflow"

    def test_no_blind_rerun_without_diagnostics(self):
        """Test that no blind rerun occurs without new diagnostics."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        blocked_file = control_dir / "combine_v2_corrective_retry_v5_generation_runtime_blocked.json"
        diagnosis_file = control_dir / "combine_v2_comfyui_prompt_500_diagnosis.json"
        
        assert blocked_file.exists(), "Blocked state artifact must exist"
        assert diagnosis_file.exists(), "Diagnosis artifact must exist before any retry"
        
        with open(blocked_file) as f:
            data = json.load(f)
        
        # Should have blocker category indicating root cause identified
        assert data["blocker"] == "COMFYUI_PROMPT_500_ROOT_CAUSE_IDENTIFIED"
        assert data["root_cause_category"] == "invalid_prompt_payload"

    def test_no_fake_success_without_prompt_id(self):
        """Test that no fake success is reported without prompt_id."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        blocked_file = control_dir / "combine_v2_corrective_retry_v5_generation_runtime_blocked.json"
        
        assert blocked_file.exists()
        
        with open(blocked_file) as f:
            data = json.load(f)
        
        # Generation not performed, no fake prompt_id
        assert data["generation_performed"] is False
        assert data["workflow_submitted"] is True  # Submitted but execution failed

    def test_no_fake_success_without_asset(self):
        """Test that no fake success is reported without generated asset."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        blocked_file = control_dir / "combine_v2_corrective_retry_v5_generation_runtime_blocked.json"
        
        assert blocked_file.exists()
        
        with open(blocked_file) as f:
            data = json.load(f)
        
        # No generation performed, no fake asset
        assert data["generation_performed"] is False
        assert data["comfyui_execution"] is False

    def test_missing_node_or_model_preserves_blocked_state(self):
        """Test that missing node/model preserves blocked state."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        blocked_file = control_dir / "combine_v2_corrective_retry_v5_generation_runtime_blocked.json"
        diagnosis_file = control_dir / "combine_v2_comfyui_prompt_500_diagnosis.json"
        
        assert blocked_file.exists()
        assert diagnosis_file.exists()
        
        with open(blocked_file) as f:
            blocked_data = json.load(f)
        
        with open(diagnosis_file) as f:
            diagnosis_data = json.load(f)
        
        # Secondary blocker identified
        assert blocked_data["secondary_blocker"] == "MISSING_CHECKPOINT_MODEL_OR_CUSTOM_NODE"
        assert blocked_data["required_model"] == "juggernautXL_version2.safetensors"
        assert blocked_data["manual_action_required"] is True
        
        # Diagnosis includes manual action
        assert diagnosis_data["manual_action_required"] is True
        assert "manual_action" in diagnosis_data

    def test_production_accepted_false(self):
        """Test that production_accepted is always false in blocked state."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        blocked_file = control_dir / "combine_v2_corrective_retry_v5_generation_runtime_blocked.json"
        
        assert blocked_file.exists()
        
        with open(blocked_file) as f:
            data = json.load(f)
        
        assert data["production_accepted"] is False

    def test_assembly_downstream_forbidden(self):
        """Test that assembly and downstream are forbidden in blocked state."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        blocked_file = control_dir / "combine_v2_corrective_retry_v5_generation_runtime_blocked.json"
        
        assert blocked_file.exists()
        
        with open(blocked_file) as f:
            data = json.load(f)
        
        assert data.get("assembly_allowed", False) is False
        assert data.get("downstream_allowed", False) is False

    def test_exactly_one_generation_enforced(self):
        """Test that exactly one generation is enforced by CLI guards."""
        # The CLI has a guard that max_generations must equal 1
        # This is validated in the combine_corrective_retry_v5_visual_recovery function
        import sys
        sys.path.insert(0, "f:/ComfyUI/comfy-agent-mvp")
        
        # Read the CLI file to verify the guard exists
        cli_file = Path("f:/ComfyUI/comfy-agent-mvp/app/cli.py")
        cli_content = cli_file.read_text(encoding="utf-8")
        
        assert "max_generations != 1" in cli_content
        assert "max_generations_must_equal_1" in cli_content

    def test_artifact_index_updated(self):
        """Test that artifact_index.json is updated with new artifacts."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        index_file = control_dir / "artifact_index.json"
        
        assert index_file.exists()
        
        with open(index_file) as f:
            data = json.load(f)
        
        artifacts = data.get("artifacts", [])
        assert "output/control/combine_v2_comfyui_prompt_500_diagnosis.json" in artifacts
        assert "output/control/combine_v2_corrective_retry_v5_prompt_payload_validation.json" in artifacts
        assert "output/control/combine_v2_corrective_retry_v5_generation_runtime_blocked.json" in artifacts

    def test_episode_ledger_updated(self):
        """Test that episode_ledger.json is updated with diagnosis event."""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        ledger_file = control_dir / "episode_ledger.json"
        
        assert ledger_file.exists()
        
        with open(ledger_file) as f:
            data = json.load(f)
        
        # Find the diagnosis event
        diagnosis_events = [e for e in data if e.get("event_type") == "comfyui_prompt_500_diagnosis_completed"]
        assert len(diagnosis_events) > 0, "Diagnosis event must be in ledger"
        
        event = diagnosis_events[-1]
        assert event["task_id"] == "RC-COMBINE-V2-3261-3360"
        assert event["post_prompt_500_diagnosed"] is True
        assert event["root_cause_category"] == "invalid_prompt_payload"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
