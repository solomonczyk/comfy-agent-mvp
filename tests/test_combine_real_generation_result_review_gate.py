import json
import subprocess
import sys
from io import BytesIO

from PIL import Image


def _run_cli(args):
    cmd = [sys.executable, "-m", "app.cli"] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    payload = {}
    if result.stdout.strip().startswith("{"):
        payload = json.loads(result.stdout)
    return result, payload


def _png_2x3_bytes():
    image = Image.new("RGB", (2, 3), color=(255, 10, 10))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _seed_zero_assets(project_root):
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    (control_dir / "combine_v2_real_generation_observed_settings.json").write_text(
        json.dumps({"stage": "real_generate_assets"}),
        encoding="utf-8",
    )
    (control_dir / "combine_v2_real_generation_trace.json").write_text(
        json.dumps({"stage": "real_generate_assets", "events": []}),
        encoding="utf-8",
    )
    (control_dir / "combine_v2_real_generation_result.json").write_text(
        json.dumps(
            {
                "stage": "real_generate_assets",
                "status": "failed",
                "generated_assets_count": 0,
                "failure_code": "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS",
                "next_allowed_action": "real_generation_result_review_required",
                "visual_qa_executed": False,
                "retry_attempted": False,
                "downstream_executed": False,
                "production_accepted": False,
            }
        ),
        encoding="utf-8",
    )
    (control_dir / "combine_v2_real_generation_outputs_manifest.json").write_text(
        json.dumps(
            {
                "stage": "real_generate_assets",
                "status": "failed",
                "generated_assets_count": 0,
                "generated_assets": [],
                "failure_code": "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS",
                "output_control_root": "output/control",
            }
        ),
        encoding="utf-8",
    )
    return control_dir


def _seed_valid_assets(project_root):
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    image_bytes = _png_2x3_bytes()
    image_path = assets_dir / "frame_001.png"
    image_path.write_bytes(image_bytes)

    import hashlib

    sha256 = hashlib.sha256(image_bytes).hexdigest()
    asset_record = {
        "path": "output/assets/frame_001.png",
        "exists": True,
        "readable": True,
        "width": 2,
        "height": 3,
        "size_bytes": len(image_bytes),
        "sha256": sha256,
    }

    (control_dir / "combine_v2_real_generation_observed_settings.json").write_text(
        json.dumps({"stage": "real_generate_assets"}),
        encoding="utf-8",
    )
    (control_dir / "combine_v2_real_generation_trace.json").write_text(
        json.dumps({"stage": "real_generate_assets", "events": []}),
        encoding="utf-8",
    )
    (control_dir / "combine_v2_real_generation_result.json").write_text(
        json.dumps(
            {
                "stage": "real_generate_assets",
                "status": "completed",
                "generated_assets_count": 1,
                "generated_assets": [asset_record],
                "next_allowed_action": "real_generation_result_review_required",
                "visual_qa_executed": False,
                "retry_attempted": False,
                "downstream_executed": False,
                "production_accepted": False,
            }
        ),
        encoding="utf-8",
    )
    (control_dir / "combine_v2_real_generation_outputs_manifest.json").write_text(
        json.dumps(
            {
                "stage": "real_generate_assets",
                "status": "completed",
                "generated_assets_count": 1,
                "generated_assets": [asset_record],
                "output_control_root": "output/control",
            }
        ),
        encoding="utf-8",
    )
    return control_dir


def test_review_gate_blocks_visual_qa_on_zero_assets(tmp_path):
    control_dir = _seed_zero_assets(tmp_path)

    result, payload = _run_cli(
        [
            "combine-review-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert result.returncode == 1
    assert payload["status"] == "blocked"
    assert payload["next_allowed_action"] == "real_generation_result_review_required"
    assert payload["entry_decision"] == "block_visual_qa_entry"
    assert payload["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"
    assert payload["visual_qa_executed"] is False
    assert payload["retry_attempted"] is False
    assert payload["assembly_executed"] is False
    assert payload["downstream_executed"] is False
    assert payload["production_accepted"] is False
    assert payload["generation_attempted"] is False
    assert payload["comfyui_execution"] is False

    review_payload = json.loads(
        (control_dir / "combine_v2_real_generation_result_review.json").read_text(encoding="utf-8")
    )
    decision_payload = json.loads(
        (control_dir / "combine_v2_real_visual_qa_entry_decision.json").read_text(encoding="utf-8")
    )
    assert review_payload["status"] == "blocked"
    assert review_payload["generated_assets_count"] == 0
    assert review_payload["assets_checked"] is True
    assert review_payload["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"
    assert review_payload["operator_review_required"] is True
    assert decision_payload["entry_decision"] == "block_visual_qa_entry"
    assert decision_payload["next_allowed_action"] == "real_generation_result_review_required"
    assert not (tmp_path / "artifact_index.json").exists()
    assert not (tmp_path / "episode_ledger.json").exists()


def test_review_gate_allows_visual_qa_preflight_on_valid_assets(tmp_path):
    control_dir = _seed_valid_assets(tmp_path)

    result, payload = _run_cli(
        [
            "combine-review-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert result.returncode == 0
    assert payload["status"] == "ready_for_visual_qa"
    assert payload["next_allowed_action"] == "real_visual_qa_preflight_required"
    assert payload["entry_decision"] == "allow_real_visual_qa_preflight"
    assert payload["visual_qa_executed"] is False
    assert payload["retry_attempted"] is False
    assert payload["assembly_executed"] is False
    assert payload["downstream_executed"] is False
    assert payload["production_accepted"] is False
    assert payload["generation_attempted"] is False
    assert payload["comfyui_execution"] is False

    review_payload = json.loads(
        (control_dir / "combine_v2_real_generation_result_review.json").read_text(encoding="utf-8")
    )
    decision_payload = json.loads(
        (control_dir / "combine_v2_real_visual_qa_entry_decision.json").read_text(encoding="utf-8")
    )
    assert review_payload["status"] == "ready_for_visual_qa"
    assert review_payload["generated_assets_count"] == 1
    assert review_payload["assets_checked"] is True
    assert review_payload["assets_exist"] is True
    assert review_payload["assets_readable"] is True
    assert review_payload["generated_assets"][0]["width"] == 2
    assert review_payload["generated_assets"][0]["height"] == 3
    assert len(review_payload["generated_assets"][0]["sha256"]) == 64
    assert review_payload["visual_qa_executed"] is False
    assert review_payload["retry_attempted"] is False
    assert review_payload["assembly_executed"] is False
    assert review_payload["downstream_executed"] is False
    assert review_payload["production_accepted"] is False
    assert decision_payload["entry_decision"] == "allow_real_visual_qa_preflight"
    assert decision_payload["next_allowed_action"] == "real_visual_qa_preflight_required"
    assert not (tmp_path / "artifact_index.json").exists()
    assert not (tmp_path / "episode_ledger.json").exists()
