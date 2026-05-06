"""RC-COMBINE-V2-1401-1460 — Assembly Readiness Packet V3 Tests."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.cli import combine_build_assembly_readiness_packet_v3


def test_assembly_readiness_packet_created(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    operator_acceptance = {"stage": "operator_visual_review", "shot_id": "shot02", "operator_visual_decision": "accept_visual_quality", "source_asset": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png", "previous_qa_verdict": "qa_passed", "operator_visual_acceptance_confirmed": True, "visual_asset_accepted": True, "timestamp": "2025-01-15T10:00:00Z"}
    with open(control_dir / "combine_v2_operator_visual_acceptance_v3.json", 'w') as f:
        json.dump(operator_acceptance, f, indent=2)
    
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump({"current_state": "operator_visual_review", "shot_id": "shot02"}, f, indent=2)
    
    class Args:
        project_root = str(tmp_path); shot_id = "shot02"; json = True
    
    result = combine_build_assembly_readiness_packet_v3(Args())
    assert result == 0
    assert (control_dir / "combine_v2_assembly_readiness_packet_v3.json").exists()
    
    with open(control_dir / "artifact_index.json", 'r') as f:
        idx = json.load(f)
    assert idx["current_state"] == "assembly_preflight_required"
    assert idx["assembly_executed"] == False
    assert idx["downstream_executed"] == False
    assert idx["production_accepted"] == False


def test_assembly_readiness_packet_requires_operator_acceptance(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    class Args:
        project_root = str(tmp_path); shot_id = "shot02"; json = True
    
    result = combine_build_assembly_readiness_packet_v3(Args())
    assert result == 1


def test_assembly_readiness_packet_boundary_enforcement(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    operator_acceptance = {"stage": "operator_visual_review", "shot_id": "shot02", "operator_visual_decision": "accept_visual_quality", "source_asset": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png", "previous_qa_verdict": "qa_passed", "operator_visual_acceptance_confirmed": True, "visual_asset_accepted": True, "timestamp": "2025-01-15T10:00:00Z"}
    with open(control_dir / "combine_v2_operator_visual_acceptance_v3.json", 'w') as f:
        json.dump(operator_acceptance, f, indent=2)
    
    class Args:
        project_root = str(tmp_path); shot_id = "shot02"; json = True
    
    result = combine_build_assembly_readiness_packet_v3(Args())
    assert result == 0
    
    with open(control_dir / "combine_v2_assembly_readiness_packet_v3.json", 'r') as f:
        packet = json.load(f)
    
    assert packet["boundary_enforcement"]["new_generation"] == False
    assert packet["boundary_enforcement"]["retry_submit"] == False
    assert packet["boundary_enforcement"]["visual_qa_rerun"] == False
    assert packet["boundary_enforcement"]["assembly"] == False
    assert packet["boundary_enforcement"]["audio"] == False
    assert packet["boundary_enforcement"]["render"] == False
    assert packet["boundary_enforcement"]["downstream"] == False
    assert packet["boundary_enforcement"]["production_accepted"] == False


def test_assembly_readiness_packet_next_action_is_assembly_preflight_required(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    operator_acceptance = {"stage": "operator_visual_review", "shot_id": "shot02", "operator_visual_decision": "accept_visual_quality", "source_asset": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png", "previous_qa_verdict": "qa_passed", "operator_visual_acceptance_confirmed": True, "visual_asset_accepted": True, "timestamp": "2025-01-15T10:00:00Z"}
    with open(control_dir / "combine_v2_operator_visual_acceptance_v3.json", 'w') as f:
        json.dump(operator_acceptance, f, indent=2)
    
    class Args:
        project_root = str(tmp_path); shot_id = "shot02"; json = True
    
    result = combine_build_assembly_readiness_packet_v3(Args())
    assert result == 0
    
    with open(control_dir / "combine_v2_assembly_readiness_packet_v3.json", 'r') as f:
        packet = json.load(f)
    
    assert packet["next_allowed_action"] == "assembly_preflight_required"
