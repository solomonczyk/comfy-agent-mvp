"""RC-COMBINE-V2-1401-1460 — Operator Visual Acceptance V3 Tests."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.cli import combine_operator_visual_decision_v3


def test_operator_can_accept_qa_passed_v3_asset(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    qa_report = {"stage": "corrective_retry_v3_visual_qa", "shot_id": "shot02", "qa_verdict": "qa_passed", "source_asset": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png", "failure_categories": [], "timestamp": "2025-01-15T10:00:00Z"}
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(qa_report, f, indent=2)
    
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump({"current_state": "operator_visual_review", "shot_id": "shot02"}, f, indent=2)
    
    class Args:
        project_root = str(tmp_path); shot_id = "shot02"; decision = "accept_visual_quality"; asset = "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png"; reason = "Visual quality meets standards"; json = True
    
    result = combine_operator_visual_decision_v3(Args())
    assert result == 0
    assert (control_dir / "combine_v2_operator_visual_acceptance_v3.json").exists()
    
    with open(control_dir / "artifact_index.json", 'r') as f:
        idx = json.load(f)
    assert idx["next_allowed_action"] == "assembly_preflight_required"
    assert idx["generation_allowed"] == False
    assert idx["downstream_executed"] == False
    assert idx["production_accepted"] == False


def test_operator_cannot_accept_qa_failed_asset(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    qa_report = {"stage": "corrective_retry_v3_visual_qa", "shot_id": "shot02", "qa_verdict": "qa_failed", "source_asset": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png", "failure_categories": ["blur_detected"], "timestamp": "2025-01-15T10:00:00Z"}
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(qa_report, f, indent=2)
    
    class Args:
        project_root = str(tmp_path); shot_id = "shot02"; decision = "accept_visual_quality"; asset = "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png"; reason = "Visual quality meets standards"; json = True
    
    result = combine_operator_visual_decision_v3(Args())
    assert result == 1


def test_operator_cannot_accept_missing_asset(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    qa_report = {"stage": "corrective_retry_v3_visual_qa", "shot_id": "shot02", "qa_verdict": "qa_passed", "source_asset": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png", "failure_categories": [], "timestamp": "2025-01-15T10:00:00Z"}
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(qa_report, f, indent=2)
    
    class Args:
        project_root = str(tmp_path); shot_id = "shot02"; decision = "accept_visual_quality"; asset = "output/assets/wrong_asset.png"; reason = "Visual quality meets standards"; json = True
    
    result = combine_operator_visual_decision_v3(Args())
    assert result == 1


def test_operator_cannot_accept_asset_not_from_v3_visual_qa(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    qa_report = {"stage": "corrective_retry_v3_visual_qa", "shot_id": "shot02", "qa_verdict": "qa_passed", "source_asset": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png", "failure_categories": [], "timestamp": "2025-01-15T10:00:00Z"}
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(qa_report, f, indent=2)
    
    class Args:
        project_root = str(tmp_path); shot_id = "shot02"; decision = "accept_visual_quality"; asset = "output/assets/different_asset.png"; reason = "Visual quality meets standards"; json = True
    
    result = combine_operator_visual_decision_v3(Args())
    assert result == 1


def test_visual_asset_acceptance_record_created(tmp_path):
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    qa_report = {"stage": "corrective_retry_v3_visual_qa", "shot_id": "shot02", "qa_verdict": "qa_passed", "source_asset": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png", "failure_categories": [], "timestamp": "2025-01-15T10:00:00Z"}
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(qa_report, f, indent=2)
    
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump({"current_state": "operator_visual_review", "shot_id": "shot02"}, f, indent=2)
    
    class Args:
        project_root = str(tmp_path); shot_id = "shot02"; decision = "accept_visual_quality"; asset = "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png"; reason = "Visual quality meets standards"; json = True
    
    result = combine_operator_visual_decision_v3(Args())
    assert result == 0
    assert (control_dir / "combine_v2_visual_asset_acceptance_record_v3.json").exists()
    
    with open(control_dir / "combine_v2_visual_asset_acceptance_record_v3.json", 'r') as f:
        record = json.load(f)
    assert record["acceptance_type"] == "corrective_retry_v3_visual_acceptance"
    assert record["visual_asset_accepted"] == True
