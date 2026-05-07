import pytest
import json
import os
from pathlib import Path
from app.orchestrator.orchestrator import CombineOrchestrator
from app.orchestrator.state_machine import CombineStateMachine
from app.agents.visual_qa_agent import VisualQAAgent
from app.orchestrator.contracts import CombineRunContext


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True)
    
    # Initialize with a state that can transition to real_visual_qa_preflight_required
    # Must be real_generation_result_collected since we blocked generate_assets -> real_visual_qa_preflight_required
    artifact_index = {
        "current_state": "real_generation_result_collected",
        "route_family": "portrait_character_identity"
    }
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump(artifact_index, f)
    
    # Initialize empty ledger to prevent stale state inference
    with open(control_dir / "episode_ledger.json", "w") as f:
        json.dump([], f)
        
    return project_root


def test_real_visual_qa_state_machine_validity():
    """Verify state machine transitions for Real Visual QA."""
    sm = CombineStateMachine()
    
    assert sm.is_valid_state("real_visual_qa_preflight_required")
    assert sm.is_valid_state("real_visual_qa_required")
    
    # Verify forbidden transition is blocked: generate_assets cannot bypass result review
    assert not sm.can_transition("generate_assets", "real_visual_qa_preflight_required")
    # Correct chain: real_generation_result_collected -> real_visual_qa_preflight_required
    assert sm.can_transition("real_generation_result_collected", "real_visual_qa_preflight_required")
    assert sm.can_transition("real_visual_qa_preflight_required", "real_visual_qa_required")
    assert sm.can_transition("real_visual_qa_required", "operator_visual_review")


def test_real_visual_qa_agent_preflight(temp_project):
    """Verify VisualQAAgent behavior in real_visual_qa_preflight_required stage."""
    orchestrator = CombineOrchestrator(str(temp_project))
    
    # Execute real_visual_qa_preflight_required
    result = orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    
    assert result.success
    assert result.stage == "real_visual_qa_preflight_required"
    assert result.metadata["next_recommended_stage"] == "real_visual_qa_required"
    assert result.metadata["real_image_analysis"] is True


def test_real_visual_qa_agent_required_logic(temp_project):
    """Verify VisualQAAgent creates required artifacts in real_visual_qa_required stage."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"

    # Seed generation artifacts consumed by VisualQAAgent
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only", "stage": "generate_assets"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready", "generated_assets": []}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001", "events": []}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True, "operator_generation_authorized": True}, f)
    
    # Set state to real_visual_qa_preflight_required first to allow transition
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    
    # Execute real_visual_qa_required
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    assert result.success
    assert "combine_v2_real_visual_qa_preflight_report.json" in result.artifacts
    assert "combine_v2_real_visual_qa_report.json" in result.artifacts
    assert "combine_v2_real_visual_qa_technical_packet.json" in result.artifacts
    assert "combine_v2_operator_visual_review_packet.json" in result.artifacts
    
    # Check artifacts on disk
    preflight_report_path = control_dir / "combine_v2_real_visual_qa_preflight_report.json"
    technical_packet_path = control_dir / "combine_v2_real_visual_qa_technical_packet.json"
    
    assert preflight_report_path.exists()
    assert technical_packet_path.exists()
    
    with open(preflight_report_path, 'r') as f:
        report = json.load(f)
        assert report["stage"] == "real_visual_qa_required"
        assert report["status"] == "real_analysis_required"
        assert report["real_image_analysis"] is True
        # technical_asset_valid may be False if no actual asset exists in test
        assert isinstance(report["technical_asset_valid"], bool)
        assert report["visual_quality_passed"] is False
        assert report["operator_review_required"] is True
        assert report["recommended_operator_decision"] == "reject"
        assert report["next_allowed_action"] == "operator_visual_review"
        assert report["retry_attempted"] is False
        assert report["assembly_executed"] is False
        assert report["downstream_executed"] is False
        assert report["production_accepted"] is False
        
        # Verify checks are present (new structure uses "checks" instead of "visual_quality_checks")
        assert "checks" in report
        # Verify manual checks are included
        expected_manual_checks = [
            "anatomy_distortion",
            "hand_distortion",
            "body_pose_instability",
            "clothing_artifacts",
            "face_identity_unreliable",
            "production_quality_failed"
        ]
        for check in expected_manual_checks:
            assert check in report["checks"]
            assert report["checks"][check]["status"] == "manual_review_required"
        
    with open(technical_packet_path, 'r') as f:
        packet = json.load(f)
        assert packet["stage"] == "real_visual_qa_required"
        assert packet["source_stage"] == "real_visual_qa_preflight_required"
        # technical_asset_valid may be False if no actual asset exists in test
        assert isinstance(packet["technical_asset_valid"], bool)
        assert packet["visual_quality_passed"] is False
        assert packet["operator_review_required"] is True
        assert packet["recommended_operator_decision"] == "reject"
        assert packet["next_allowed_action"] == "operator_visual_review"
        assert packet["retry_attempted"] is False
        assert packet["assembly_executed"] is False
        assert packet["downstream_executed"] is False
        assert packet["production_accepted"] is False
        
        # Verify quality metrics are defined (actual technical checks, not pending)
        expected_metrics = [
            "asset_exists",
            "asset_readable",
            "width_height_valid",
            "sha256_present",
            "size_bytes_valid",
            "resolution_policy_check",
            "blur_or_softness_basic",
            "brightness_basic",
            "contrast_basic"
        ]
        for metric in expected_metrics:
            assert metric in packet["quality_metrics"]
            # Technical checks should have actual status (passed/warn/failed), not pending
            assert packet["quality_metrics"][metric] in ["passed", "warn", "failed"]
        
        # Verify operator review packet
        assert packet["operator_review_packet"]["review_required"] is True
        assert packet["operator_review_packet"]["real_image_analysis"] is True
        assert "accept_visuals" in packet["operator_review_packet"]["operator_actions"]
        assert "reject_visuals" in packet["operator_review_packet"]["operator_actions"]
        assert "request_retry_correction" in packet["operator_review_packet"]["operator_actions"]


def test_real_visual_qa_output_structure_match(temp_project):
    """Verify that the output structure matches the expected format exactly."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"

    # Seed generation artifacts
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001"}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True}, f)
    
    # Execute stages
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    # Verify result structure
    assert result.stage == "real_visual_qa_required"
    assert result.success is True
    
    # Verify metadata structure matches expected format
    expected_metadata_fields = [
        "technical_asset_valid",
        "visual_quality_passed",
        "operator_review_required",
        "recommended_operator_decision",
        "next_allowed_action",
        "retry_attempted",
        "assembly_executed",
        "downstream_executed",
        "production_accepted"
    ]
    
    for field in expected_metadata_fields:
        assert field in result.metadata
    
    assert isinstance(result.metadata["technical_asset_valid"], bool)
    assert result.metadata["visual_quality_passed"] is False
    assert result.metadata["operator_review_required"] is True
    assert result.metadata["recommended_operator_decision"] == "reject"
    assert result.metadata["next_allowed_action"] == "operator_visual_review"
    assert result.metadata["retry_attempted"] is False
    assert result.metadata["assembly_executed"] is False
    assert result.metadata["downstream_executed"] is False
    assert result.metadata["production_accepted"] is False


def test_real_visual_qa_safety_boundaries(temp_project):
    """Verify that VisualQAAgent enforces safety boundaries for real visual QA."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"

    # Seed generation artifacts
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001"}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True}, f)
    
    # Transition to real_visual_qa_required
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    # Verify safety boundaries: No Retry / No Assembly / No Downstream
    assert result.metadata.get("retry_attempted", False) is False
    assert result.metadata.get("assembly_executed", False) is False
    assert result.metadata.get("downstream_executed", False) is False
    assert result.metadata.get("real_image_analysis", True) is True
    
    # Verify artifacts don't include generation or assembly artifacts
    assert "combine_v2_real_visual_qa_preflight_report.json" in result.artifacts
    assert "combine_v2_real_visual_qa_report.json" in result.artifacts
    assert "combine_v2_real_visual_qa_technical_packet.json" in result.artifacts
    assert "combine_v2_operator_visual_review_packet.json" in result.artifacts
    # Should NOT include generation or assembly artifacts
    assert "generated_frame" not in str(result.artifacts)
    assert "assembly" not in str(result.artifacts)


def test_real_visual_qa_no_image_acceptance(temp_project):
    """Verify that the layer does not accept images directly."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"

    # Seed generation artifacts
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001"}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True}, f)
    
    # Execute real visual QA
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    # Verify the layer doesn't accept images - it only analyzes existing assets
    assert result.metadata.get("real_image_analysis", True) is True
    # The layer should not have image input parameters
    assert "image_input" not in result.metadata
    assert "uploaded_image" not in result.metadata


def test_real_visual_qa_no_retry_launch(temp_project):
    """Verify that the layer does not launch retry."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"

    # Seed generation artifacts
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001"}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True}, f)
    
    # Execute real visual QA
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    # Verify retry is not launched
    assert result.metadata.get("retry_attempted", False) is False
    assert result.metadata["next_recommended_stage"] == "operator_visual_review"
    # Should not recommend retry stage
    assert result.metadata["next_recommended_stage"] != "retry_correction_required"


def test_real_visual_qa_preflight_creates_artifact(temp_project):
    """Test 1: real_visual_qa_preflight_required creates preflight report artifact."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"
    
    result = orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    
    assert result.success
    assert "combine_v2_real_visual_qa_preflight_report.json" in result.artifacts
    
    preflight_path = control_dir / "combine_v2_real_visual_qa_preflight_report.json"
    assert preflight_path.exists()
    
    with open(preflight_path, 'r') as f:
        report = json.load(f)
        assert report["stage"] == "real_visual_qa_preflight_required"
        assert report["status"] == "preflight_cleared"
        assert report["next_allowed_action"] == "real_visual_qa_required"


def test_real_generation_cannot_bypass_result_review():
    """Test 2: real generation cannot bypass result review."""
    sm = CombineStateMachine()
    
    # Direct transition from generate_assets to real_visual_qa_preflight must be blocked
    assert not sm.can_transition("generate_assets", "real_visual_qa_preflight_required")
    
    # Correct path requires going through result collection and review
    assert sm.can_transition("real_generate_assets", "real_generation_result_collected")
    assert sm.can_transition("real_generation_result_collected", "real_generation_result_review_required")
    assert sm.can_transition("real_generation_result_collected", "real_visual_qa_preflight_required")


def test_technical_checks_execute_on_asset(temp_project):
    """Test 3-5: Technical checks execute on asset from manifest (exists, readable, dimensions)."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"
    
    # Create a test asset
    assets_dir = temp_project / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a simple test image
    from PIL import Image
    test_img = Image.new('RGB', (512, 512), color='red')
    test_img.save(assets_dir / "test_asset.png")
    
    # Create manifest
    manifest = {
        "generated_assets": [
            {
                "path": str(assets_dir / "test_asset.png"),
                "width": 512,
                "height": 512
            }
        ]
    }
    with open(control_dir / "combine_v2_generation_manifest.json", "w") as f:
        json.dump(manifest, f)
    
    # Seed other required artifacts
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001"}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True}, f)
    
    # Execute real visual QA
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    # Check technical packet
    technical_packet_path = control_dir / "combine_v2_real_visual_qa_technical_packet.json"
    with open(technical_packet_path, 'r') as f:
        packet = json.load(f)
        
        # Test 3: asset from manifest is readable
        assert packet["quality_metrics"]["asset_exists"] in ["passed", "warn"]
        assert packet["quality_metrics"]["asset_readable"] in ["passed", "warn"]
        
        # Test 4: width/height are checked
        assert packet["quality_metrics"]["width_height_valid"] in ["passed", "warn"]
        
        # Test 5: sha256 is checked
        assert packet["quality_metrics"]["sha256_present"] in ["passed", "warn"]


def test_resolution_mismatch_gives_warn_not_pass(temp_project):
    """Test 6: resolution mismatch gives warn/fail, not pass."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"
    
    # Create a test asset with different resolution than expected
    assets_dir = temp_project / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    from PIL import Image
    test_img = Image.new('RGB', (512, 512), color='red')
    test_img.save(assets_dir / "test_asset.png")
    
    # Create manifest with mismatched expected resolution
    manifest = {
        "generated_assets": [
            {
                "path": str(assets_dir / "test_asset.png"),
                "width": 1024,  # Expected different from actual
                "height": 1024
            }
        ]
    }
    with open(control_dir / "combine_v2_generation_manifest.json", "w") as f:
        json.dump(manifest, f)
    
    # Seed other required artifacts
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001"}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True}, f)
    
    # Execute real visual QA
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    # Check technical packet
    technical_packet_path = control_dir / "combine_v2_real_visual_qa_technical_packet.json"
    with open(technical_packet_path, 'r') as f:
        packet = json.load(f)
        
        # Resolution mismatch should give warn, not pass
        resolution_status = packet["quality_metrics"]["resolution_policy_check"]
        assert resolution_status in ["warn", "failed"]
        assert resolution_status != "passed"


def test_manual_checks_require_human_review(temp_project):
    """Test 7: manual visual checks don't get passed without real judge/operator."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"
    
    # Seed required artifacts
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001"}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True}, f)
    
    # Execute real visual QA
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    # Check QA report
    qa_report_path = control_dir / "combine_v2_real_visual_qa_report.json"
    with open(qa_report_path, 'r') as f:
        report = json.load(f)
        
        # Manual checks should be manual_review_required, not passed
        manual_checks = [
            "anatomy_distortion",
            "hand_distortion",
            "body_pose_instability",
            "clothing_artifacts",
            "face_identity_unreliable",
            "production_quality_failed"
        ]
        
        for check in manual_checks:
            assert check in report["checks"]
            assert report["checks"][check]["status"] == "manual_review_required"
            assert report["checks"][check]["status"] != "passed"


def test_visual_qa_required_verdicts(temp_project):
    """Test 8-10: visual_quality_passed=false, recommended_operator_decision=reject, next_allowed_action=operator_visual_review."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"
    
    # Seed required artifacts
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001"}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True}, f)
    
    # Execute real visual QA
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    # Test 8: visual_quality_passed=false
    assert result.metadata.get("visual_quality_passed", False) is False
    
    # Test 9: recommended_operator_decision=reject
    assert result.metadata.get("recommended_operator_decision", "reject") == "reject"
    
    # Test 10: next_allowed_action=operator_visual_review
    assert result.metadata.get("next_allowed_action", "operator_visual_review") == "operator_visual_review"
    assert result.metadata["next_recommended_stage"] == "operator_visual_review"


def test_no_retry_assembly_downstream_production_acceptance(temp_project):
    """Test 11-14: retry_attempted=false, assembly_executed=false, downstream_executed=false, production_accepted=false."""
    orchestrator = CombineOrchestrator(str(temp_project))
    control_dir = temp_project / "output" / "control"
    
    # Seed required artifacts
    with open(control_dir / "combine_v2_generation_execution_plan.json", "w") as f:
        json.dump({"execution_strategy": "stub_only"}, f)
    with open(control_dir / "combine_v2_generation_execution_stub_result.json", "w") as f:
        json.dump({"status": "stubbed_ready"}, f)
    with open(control_dir / "combine_v2_generation_trace_stub.json", "w") as f:
        json.dump({"trace_id": "trace_test_001"}, f)
    with open(control_dir / "combine_v2_operator_generation_authorization.json", "w") as f:
        json.dump({"generation_gate_open": True}, f)
    
    # Execute real visual QA
    orchestrator.run_stage("real_visual_qa_preflight_required", dry_run=True)
    result = orchestrator.run_stage("real_visual_qa_required", dry_run=True)
    
    # Test 11: retry_attempted=false
    assert result.metadata.get("retry_attempted", False) is False
    
    # Test 12: assembly_executed=false
    assert result.metadata.get("assembly_executed", False) is False
    
    # Test 13: downstream_executed=false
    assert result.metadata.get("downstream_executed", False) is False
    
    # Test 14: production_accepted=false
    assert result.metadata.get("production_accepted", False) is False


# ── RC-COMBINE-V2-2481-2540: V4 Visual QA Gate Tests ──────────────────────────

def test_v4_visual_qa_preflight_state_machine_validity():
    """V4 visual QA states are valid in state machine."""
    sm = CombineStateMachine()
    assert sm.is_valid_state("corrective_retry_v4_visual_qa_preflight_required")
    assert sm.is_valid_state("corrective_retry_v4_visual_qa_required")


def test_v4_visual_qa_preflight_state_transition():
    """State machine allows correct V4 visual QA transitions."""
    sm = CombineStateMachine()
    assert sm.can_transition(
        "corrective_retry_v4_visual_qa_preflight_required",
        "corrective_retry_v4_visual_qa_required"
    )
    assert sm.can_transition(
        "corrective_retry_v4_visual_qa_required",
        "operator_visual_review"
    )


def test_v4_visual_qa_preflight_not_bypassed():
    """V4 result review cannot bypass preflight directly to visual_qa_required."""
    sm = CombineStateMachine()
    assert not sm.can_transition(
        "corrective_retry_v4_result_review_required",
        "corrective_retry_v4_visual_qa_required"
    )


def test_v4_cli_preflight_succeeds_with_real_asset(tmp_path):
    """CLI preflight command returns 0 with a valid canonical V4 asset."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    import argparse

    project_root = tmp_path / "project"
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    (assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png").write_bytes(b"X" * 4096)
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", "w") as f:
        json.dump({
            "generated_assets": ["output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png"],
            "asset_count": 1,
        }, f)
    with open(control_dir / "combine_v2_corrective_retry_v4_result_review.json", "w") as f:
        json.dump({"branch_selected": "success", "manifest_success_policy_passed": True}, f)

    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    result = combine_preflight_corrective_retry_v4_visual_qa(args)
    assert result == 0


def test_v4_cli_preflight_rejects_stub_asset(tmp_path):
    """CLI preflight command returns 1 when asset is a stub."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    import argparse

    project_root = tmp_path / "project"
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    (assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png").write_bytes(b"\x00" * 8)
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", "w") as f:
        json.dump({
            "generated_assets": ["output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png"],
            "asset_count": 1,
        }, f)
    with open(control_dir / "combine_v2_corrective_retry_v4_result_review.json", "w") as f:
        json.dump({"branch_selected": "success", "manifest_success_policy_passed": True}, f)

    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    result = combine_preflight_corrective_retry_v4_visual_qa(args)
    assert result == 1


def test_v4_preflight_production_accepted_false_hard_boundary(tmp_path):
    """Hard boundary: production_accepted is False after V4 preflight in all artifacts."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa
    import argparse

    project_root = tmp_path / "project"
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    (assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png").write_bytes(b"X" * 4096)
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", "w") as f:
        json.dump({
            "generated_assets": ["output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png"],
            "asset_count": 1,
        }, f)
    with open(control_dir / "combine_v2_corrective_retry_v4_result_review.json", "w") as f:
        json.dump({"branch_selected": "success", "manifest_success_policy_passed": True}, f)

    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    combine_preflight_corrective_retry_v4_visual_qa(args)

    for fname in (
        "combine_v2_corrective_retry_v4_visual_qa_preflight.json",
        "combine_v2_corrective_retry_v4_visual_qa_input_packet.json",
        "artifact_index.json",
    ):
        with open(control_dir / fname) as f:
            data = json.load(f)
        assert data.get("production_accepted") is False, f"{fname}: production_accepted must be False"
