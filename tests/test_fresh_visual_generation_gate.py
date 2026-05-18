import json
import pytest
from pathlib import Path


class TestFreshVisualGenerationGate:
    """Test suite for RC-COMBINE-V2-FRESH-VISUAL-GENERATION-GATE-001"""

    @pytest.fixture
    def gate_dir(self):
        """Path to the fresh visual generation gate directory"""
        return Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control/fresh_visual_generation_gate")

    @pytest.fixture
    def gate_package(self, gate_dir):
        """Load the gate package JSON"""
        with open(gate_dir / "fresh_visual_generation_gate_package.json", "r") as f:
            return json.load(f)

    @pytest.fixture
    def pre_authorization_checks(self, gate_dir):
        """Load the pre-authorization checks JSON"""
        with open(gate_dir / "fresh_visual_generation_pre_authorization_checks.json", "r") as f:
            return json.load(f)

    @pytest.fixture
    def operator_authorization_packet(self, gate_dir):
        """Load the operator authorization packet JSON"""
        with open(gate_dir / "fresh_visual_generation_operator_authorization_packet.json", "r") as f:
            return json.load(f)

    def test_generation_gate_package_is_prepared_not_authorized(self, gate_package):
        """Test that generation gate package is prepared but not authorized"""
        assert gate_package["gate_type"] == "controlled_fresh_visual_generation_gate"
        assert gate_package["gate_status"] == "prepared_waiting_for_operator_authorization"
        assert gate_package["generation_authorized"] is False
        assert gate_package["operator_authorization_required"] is True

    def test_generation_gate_requires_operator_authorization(self, gate_package, operator_authorization_packet):
        """Test that generation gate requires operator authorization"""
        assert gate_package["operator_authorization_required"] is True
        assert operator_authorization_packet["authorization_decision_status"] == "pending"
        assert operator_authorization_packet["operator_action_required"] == "approve_or_reject_one_fresh_visual_generation"

    def test_generation_gate_allows_max_one_future_generation(self, gate_package, operator_authorization_packet):
        """Test that generation gate allows maximum one future generation"""
        assert gate_package["max_generations"] == 1
        assert gate_package["blind_retry_allowed"] is False
        assert operator_authorization_packet["if_approved"]["max_generations"] == 1
        assert operator_authorization_packet["if_approved"]["blind_retry_allowed"] is False

    def test_generation_gate_blocks_blind_retry(self, gate_package):
        """Test that generation gate blocks blind retry"""
        assert gate_package["blind_retry_allowed"] is False

    def test_generation_gate_uses_quality_reference_as_calibration_only(self, gate_package):
        """Test that generation gate uses quality reference as calibration only"""
        assert gate_package["quality_reference_id"] == "quality_ref_eye_closeup_001"
        assert gate_package["quality_reference_usage"] == "quality_calibration_only"

    def test_generation_gate_does_not_submit_comfyui(self, gate_package):
        """Test that generation gate does not submit ComfyUI"""
        assert gate_package["generation_authorized"] is False
        assert "comfyui_submit_authorized" not in gate_package or gate_package.get("comfyui_submit_authorized", False) is False

    def test_generation_gate_does_not_create_prompt_id(self, pre_authorization_checks):
        """Test that generation gate does not create prompt ID"""
        checks = pre_authorization_checks["individual_checks"]
        assert checks["operator_authorization_present"]["status"] is False
        assert checks["comfyui_submit_authorized"]["status"] is False
        assert checks["runtime_execution_allowed_now"]["status"] is False

    def test_generation_gate_blocks_visual_qa_assembly_downstream(self, gate_package):
        """Test that generation gate blocks visual QA, assembly, and downstream"""
        assert gate_package["visual_qa_allowed_after_generation"] is False
        assert gate_package["assembly_allowed_after_generation"] is False
        assert gate_package["downstream_allowed_after_generation"] is False
        assert gate_package["production_acceptance_allowed_after_generation"] is False

    def test_generation_gate_keeps_production_accepted_false(self, gate_package):
        """Test that generation gate keeps production_accepted as false"""
        assert gate_package["production_acceptance_allowed_after_generation"] is False

    def test_generation_gate_updates_artifact_index_and_ledger(self):
        """Test that generation gate updates artifact index and ledger"""
        # Check artifact index
        artifact_index_path = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control/artifact_index.json")
        with open(artifact_index_path, "r") as f:
            artifact_index = json.load(f)
        
        assert artifact_index["current_state"] == "fresh_visual_generation_gate_prepared"
        assert artifact_index["next_allowed_action"] == "operator_generation_authorization_required"
        assert artifact_index["fresh_visual_generation_gate_created"] is True
        assert "fresh_visual_generation_gate_package" in artifact_index
        
        # Check episode ledger
        episode_ledger_path = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control/episode_ledger.json")
        with open(episode_ledger_path, "r") as f:
            episode_ledger = json.load(f)
        
        # First event should be our gate preparation
        first_event = episode_ledger[0]
        assert first_event["event_type"] == "fresh_visual_generation_gate_prepared"
        assert first_event["task_id"] == "RC-COMBINE-V2-FRESH-VISUAL-GENERATION-GATE-001"
        assert first_event["generation_performed"] is False
        assert first_event["gate_package_created"] is True

    def test_generation_gate_preserves_dirty_carryover_scope(self, pre_authorization_checks):
        """Test that generation gate preserves dirty carryover scope"""
        assert pre_authorization_checks["overall_status"] == "ready_for_operator_authorization_review"
        assert pre_authorization_checks["summary"]["ready_for_operator"] is True
        assert pre_authorization_checks["summary"]["failed_checks"] == 0

    def test_all_required_gate_artifacts_exist(self, gate_dir):
        """Test that all required gate artifacts exist"""
        required_files = [
            "fresh_visual_generation_gate_package.json",
            "fresh_visual_generation_pre_authorization_checks.json",
            "fresh_visual_generation_operator_authorization_packet.json",
            "fresh_visual_generation_execution_contract.json",
            "fresh_visual_generation_stop_policy.json",
            "fresh_visual_generation_gate_report.json"
        ]
        
        for filename in required_files:
            file_path = gate_dir / filename
            assert file_path.exists(), f"Required file {filename} does not exist"
            assert file_path.stat().st_size > 0, f"Required file {filename} is empty"

    def test_execution_contract_is_preparation_only(self, gate_dir):
        """Test that execution contract is preparation only"""
        with open(gate_dir / "fresh_visual_generation_execution_contract.json", "r") as f:
            contract = json.load(f)
        
        assert contract["execution_allowed_in_this_task"] is False
        assert contract["future_task_id_recommendation"] == "RC-COMBINE-V2-FRESH-VISUAL-GENERATION-EXECUTE-ONCE-001"
        assert contract["pre_execution_requirements"]["must_verify_operator_authorization_before_execution"] is True

    def test_stop_policy_enforces_post_generation_limits(self, gate_dir):
        """Test that stop policy enforces post-generation limits"""
        with open(gate_dir / "fresh_visual_generation_stop_policy.json", "r") as f:
            stop_policy = json.load(f)
        
        assert stop_policy["stop_after_generation"] is True
        assert stop_policy["stop_conditions"]["block_visual_qa_automation"]["condition"] is True
        assert stop_policy["stop_conditions"]["block_assembly_automation"]["condition"] is True
        assert stop_policy["stop_conditions"]["block_downstream_automation"]["condition"] is True
        assert stop_policy["stop_conditions"]["block_production_acceptance"]["condition"] is True
