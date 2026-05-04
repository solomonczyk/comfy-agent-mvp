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
                "status": "completed",
                "generated_assets_count": 0,
                "failure_code": None,
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
                "generated_assets_count": 0,
                "generated_assets": [],
                "output_control_root": "output/control",
            }
        ),
        encoding="utf-8",
    )
    return control_dir


def _seed_with_assets(project_root):
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
                "generated_assets_count": 0,
                "failure_code": None,
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
                "generated_assets_count": 0,
                "generated_assets": [],
                "output_control_root": "output/control",
            }
        ),
        encoding="utf-8",
    )
    return control_dir, asset_record


def test_recovery_does_not_submit_comfyui(tmp_path):
    """1. recovery не запускает ComfyUI submit"""
    _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert payload["comfyui_execution"] is False
    assert payload["generation_attempted"] is False


def test_recovery_does_not_create_new_generation_attempt(tmp_path):
    """2. recovery не создаёт новую generation attempt"""
    _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert payload["generation_attempted"] is False


def test_zero_assets_canonicalizes_result_to_failed(tmp_path):
    """3. zero assets canonicalizes result to failed"""
    control_dir = _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert result.returncode == 1
    assert payload["status"] == "failed"
    assert payload["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"

    result_payload = json.loads(
        (control_dir / "combine_v2_real_generation_result.json").read_text(encoding="utf-8")
    )
    assert result_payload["status"] == "failed"
    assert result_payload["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"


def test_zero_assets_keeps_next_allowed_action_review_required(tmp_path):
    """4. zero assets keeps next_allowed_action=real_generation_result_review_required"""
    control_dir = _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert payload["next_allowed_action"] == "real_generation_result_review_required"

    decision_payload = json.loads(
        (control_dir / "combine_v2_real_generation_recovery_decision.json").read_text(encoding="utf-8")
    )
    assert decision_payload["next_allowed_action"] == "real_generation_result_review_required"
    assert decision_payload["operator_review_required"] is True


def test_found_assets_updates_manifest_with_object_entries(tmp_path):
    """5. found assets updates manifest with object entries"""
    control_dir, _ = _seed_with_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert result.returncode == 0
    manifest_payload = json.loads(
        (control_dir / "combine_v2_real_generation_outputs_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest_payload["generated_assets_count"] == 1
    assert len(manifest_payload["generated_assets"]) == 1
    assert isinstance(manifest_payload["generated_assets"][0], dict)


def test_found_assets_allows_real_visual_qa_preflight(tmp_path):
    """6. found assets allows real_visual_qa_preflight_required"""
    control_dir, _ = _seed_with_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert payload["next_allowed_action"] == "real_visual_qa_preflight_required"

    decision_payload = json.loads(
        (control_dir / "combine_v2_real_generation_recovery_decision.json").read_text(encoding="utf-8")
    )
    assert decision_payload["next_allowed_action"] == "real_visual_qa_preflight_required"


def test_recovered_asset_has_required_fields(tmp_path):
    """7. recovered asset has path/exists/readable/width/height/size_bytes/sha256"""
    control_dir, expected_record = _seed_with_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    recovered = payload["recovered_assets_count"]
    assert recovered == 1
    manifest_payload = json.loads(
        (control_dir / "combine_v2_real_generation_outputs_manifest.json").read_text(encoding="utf-8")
    )
    asset = manifest_payload["generated_assets"][0]
    assert asset["path"] == expected_record["path"]
    assert asset["exists"] is True
    assert asset["readable"] is True
    assert asset["width"] == 2
    assert asset["height"] == 3
    assert asset["size_bytes"] == expected_record["size_bytes"]
    assert len(asset["sha256"]) == 64


def test_visual_qa_executed_is_false(tmp_path):
    """8. visual_qa_executed=false"""
    control_dir = _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert payload["visual_qa_executed"] is False

    report_payload = json.loads(
        (control_dir / "combine_v2_real_generation_canonicalization_report.json").read_text(encoding="utf-8")
    )
    assert report_payload["visual_qa_executed"] is False


def test_retry_attempted_is_false(tmp_path):
    """9. retry_attempted=false"""
    control_dir = _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert payload.get("retry_attempted", False) is False

    report_payload = json.loads(
        (control_dir / "combine_v2_real_generation_canonicalization_report.json").read_text(encoding="utf-8")
    )
    assert report_payload.get("retry_attempted", False) is False


def test_assembly_executed_is_false(tmp_path):
    """10. assembly_executed=false"""
    control_dir = _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert payload.get("assembly_executed", False) is False

    report_payload = json.loads(
        (control_dir / "combine_v2_real_generation_canonicalization_report.json").read_text(encoding="utf-8")
    )
    assert report_payload.get("assembly_executed", False) is False


def test_downstream_executed_is_false(tmp_path):
    """11. downstream_executed=false"""
    control_dir = _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert payload["downstream_executed"] is False

    report_payload = json.loads(
        (control_dir / "combine_v2_real_generation_canonicalization_report.json").read_text(encoding="utf-8")
    )
    assert report_payload["downstream_executed"] is False


def test_production_accepted_is_false(tmp_path):
    """12. production_accepted=false"""
    control_dir = _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert payload["production_accepted"] is False

    report_payload = json.loads(
        (control_dir / "combine_v2_real_generation_canonicalization_report.json").read_text(encoding="utf-8")
    )
    assert report_payload["production_accepted"] is False


def test_recovery_creates_all_three_artifacts(tmp_path):
    """Verify all three required artifacts are created"""
    control_dir = _seed_zero_assets(tmp_path)
    result, payload = _run_cli(
        [
            "combine-recover-real-generation-result",
            "--project-root",
            str(tmp_path),
            "--json",
        ]
    )
    assert (control_dir / "combine_v2_real_generation_result_recovery_attempt.json").exists()
    assert (control_dir / "combine_v2_real_generation_canonicalization_report.json").exists()
    assert (control_dir / "combine_v2_real_generation_recovery_decision.json").exists()
    assert len(payload["artifacts"]) == 3
