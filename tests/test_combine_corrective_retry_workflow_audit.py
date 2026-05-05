"""Tests for RC-COMBINE-V2-921-980-DIAG workflow audit."""
from __future__ import annotations

import json
import argparse
from pathlib import Path

import pytest

from app.cli import (
    combine_audit_corrective_retry_workflow,
    combine_diagnose_corrective_retry_recipe,
    combine_build_corrective_recipe_v2,
)


def _make_args(project_root: str, json_output: bool = True) -> argparse.Namespace:
    return argparse.Namespace(project_root=project_root, json=json_output)


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_audit_identifies_existing_submitted_workflow(tmp_path: Path) -> None:
    control = tmp_path / "output" / "control"
    existing_wf = {
        "3": {"inputs": {"seed": 1, "steps": 20, "cfg": 7.5, "sampler_name": "dpmpp_sde", "scheduler": "karras", "denoise": 0.5, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
        "4": {"inputs": {"ckpt_name": "juggernautXL_version2.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "5": {"inputs": {"width": 1344, "height": 768, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "6": {"inputs": {"text": "positive prompt", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"text": "negative prompt", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"images": ["8", 0], "filename_prefix": "prefix"}, "class_type": "SaveImage"},
        "10": {"inputs": {"lora_stack": []}, "class_type": "LoraLoader"},
    }
    submit_request = {
        "workflow_payload_snapshot": existing_wf,
        "prompt_id": "test-prompt-id",
    }
    _write_json(control / "combine_v2_corrective_retry_submit_request.json", submit_request)
    _write_json(control / "ep01_shot01_submitted_workflow.json", existing_wf)
    _write_json(control / "artifact_index.json", {})
    _write_json(control / "episode_ledger.json", [])

    args = _make_args(str(tmp_path))
    ret = combine_audit_corrective_retry_workflow(args)
    assert ret == 0

    audit_path = control / "combine_v2_corrective_retry_workflow_audit.json"
    assert audit_path.exists()
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["workflow_source_decision"] == "existing_submitted_workflow"
    assert audit["used_existing_submitted_workflow"] is True
    assert "ep01_shot01_submitted_workflow.json" in audit["actual_submitted_workflow_path"]
    assert audit["ksampler_settings"]["sampler_name"] == "dpmpp_sde"
    assert audit["conditioning_chain"]["ksampler_present"] is True
    assert audit["conditioning_chain"]["lora_present"] is False
    assert audit["generation_allowed"] is False
    assert audit["comfyui_execution"] is False
    assert audit["visual_qa_executed"] is False
    assert audit["assembly_executed"] is False
    assert audit["downstream_executed"] is False
    assert audit["production_accepted"] is False


def test_audit_falls_back_to_minimal_workflow(tmp_path: Path) -> None:
    control = tmp_path / "output" / "control"
    minimal_wf = {
        "1": {"inputs": {"ckpt_name": "realvisxlV50_v50Bakedvae.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "2": {"inputs": {"text": "test", "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
        "3": {"inputs": {"text": "test", "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
        "4": {"inputs": {"seed": 123, "steps": 20, "cfg": 7, "sampler_name": "euler", "scheduler": "normal", "denoise": 1, "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
        "5": {"inputs": {"width": 1024, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "6": {"inputs": {"samples": ["4", 0], "vae": ["1", 2]}, "class_type": "VAEDecode"},
        "7": {"inputs": {"filename_prefix": "combine_v2_123", "images": ["6", 0]}, "class_type": "SaveImage"},
    }
    submit_request = {"workflow_payload_snapshot": minimal_wf}
    _write_json(control / "combine_v2_corrective_retry_submit_request.json", submit_request)
    _write_json(control / "artifact_index.json", {})
    _write_json(control / "episode_ledger.json", [])

    args = _make_args(str(tmp_path))
    ret = combine_audit_corrective_retry_workflow(args)
    assert ret == 0

    audit = json.loads((control / "combine_v2_corrective_retry_workflow_audit.json").read_text(encoding="utf-8"))
    assert audit["workflow_source_decision"] == "fallback_minimal_workflow"
    assert audit["used_fallback_minimal_workflow"] is True


def test_audit_handles_missing_files(tmp_path: Path) -> None:
    control = tmp_path / "output" / "control"
    _write_json(control / "artifact_index.json", {})
    _write_json(control / "episode_ledger.json", [])

    args = _make_args(str(tmp_path))
    ret = combine_audit_corrective_retry_workflow(args)
    assert ret == 0

    audit = json.loads((control / "combine_v2_corrective_retry_workflow_audit.json").read_text(encoding="utf-8"))
    assert audit["workflow_source_decision"] == "unknown"
    assert audit["actual_submitted_workflow_path"] == "unknown"


def test_diagnosis_detects_prompt_mismatch_and_cross_shot_reuse(tmp_path: Path) -> None:
    control = tmp_path / "output" / "control"
    existing_wf = {
        "3": {"inputs": {"seed": 1, "steps": 20, "cfg": 7.5, "sampler_name": "dpmpp_sde", "scheduler": "karras", "denoise": 0.5, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
        "4": {"inputs": {"ckpt_name": "juggernautXL_version2.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "5": {"inputs": {"width": 1344, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "6": {"inputs": {"text": "old prompt from shot01", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"text": "ugly, deformed", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"images": ["8", 0], "filename_prefix": "prefix"}, "class_type": "SaveImage"},
        "10": {"inputs": {"lora_stack": []}, "class_type": "LoraLoader"},
    }
    payload = {
        "base_payload": {
            "prompts": {"positive": "expected new prompt", "negative": "expected negative"}
        }
    }
    submit_request = {"workflow_payload_snapshot": existing_wf}
    _write_json(control / "combine_v2_corrective_retry_generation_payload.json", payload)
    _write_json(control / "combine_v2_corrective_retry_submit_request.json", submit_request)
    _write_json(control / "combine_v2_corrective_retry_prompt_patch.json", {"corrective_actions": {"prompt": {"increase_steps": 25}}})
    _write_json(control / "combine_v2_corrective_retry_workflow_patch.json", {"corrective_actions": {"workflow": {"enforced_resolution": {"width": 1344, "height": 1024}}}})
    _write_json(control / "combine_v2_corrective_retry_outputs_manifest.json", {"generated_assets_count": 1})
    _write_json(control / "ep01_shot01_submitted_workflow.json", existing_wf)
    _write_json(control / "artifact_index.json", {})
    _write_json(control / "episode_ledger.json", [])

    args = _make_args(str(tmp_path))
    ret = combine_diagnose_corrective_retry_recipe(args)
    assert ret == 0

    diagnosis = json.loads((control / "combine_v2_corrective_retry_recipe_diagnosis.json").read_text(encoding="utf-8"))
    assert diagnosis["root_cause_count"] >= 2
    cause_names = {c["name"] for c in diagnosis["root_causes"]}
    assert "prompt_patch_mismatch_bug" in cause_names
    assert "cross_shot_workflow_reuse" in cause_names
    assert diagnosis["expected_vs_actual"]["prompt_diff"]["positive_match"] is False
    assert diagnosis["generation_allowed"] is False
    assert diagnosis["comfyui_execution"] is False
    assert diagnosis["visual_qa_executed"] is False
    assert diagnosis["assembly_executed"] is False
    assert diagnosis["downstream_executed"] is False
    assert diagnosis["production_accepted"] is False


def test_recipe_v2_builds_from_diagnosis(tmp_path: Path) -> None:
    control = tmp_path / "output" / "control"
    root_causes = [
        {"name": "prompt_patch_mismatch_bug", "likelihood": "high"},
        {"name": "cross_shot_workflow_reuse", "likelihood": "high"},
    ]
    _write_json(control / "combine_v2_corrective_retry_root_cause_report.json", {"root_causes": root_causes})
    _write_json(control / "combine_v2_corrective_retry_recipe_diagnosis.json", {"root_causes": root_causes})
    _write_json(control / "combine_v2_corrective_retry_workflow_audit.json", {})
    _write_json(control / "artifact_index.json", {})
    _write_json(control / "episode_ledger.json", [])

    args = _make_args(str(tmp_path))
    ret = combine_build_corrective_recipe_v2(args)
    assert ret == 0

    v2 = json.loads((control / "combine_v2_corrective_retry_recipe_v2_recommendation.json").read_text(encoding="utf-8"))
    actions = {a["action"] for a in v2["recommended_actions"]}
    assert "fix_prompt_injection_logic" in actions
    assert "fix_workflow_source_selection" in actions
    assert v2["generation_allowed"] is False
    assert v2["retry_allowed"] is False
    assert v2["comfyui_execution"] is False
    assert v2["visual_qa_executed"] is False
    assert v2["assembly_executed"] is False
    assert v2["downstream_executed"] is False
    assert v2["production_accepted"] is False
    assert "new_generation" in v2["forbidden_actions"]


def test_boundary_all_commands_forbid_generation_and_downstream(tmp_path: Path) -> None:
    """All three diagnostic commands must forbid generation, retry, QA, assembly, downstream, production."""
    control = tmp_path / "output" / "control"
    existing_wf = {
        "3": {"inputs": {"seed": 1, "steps": 20, "cfg": 7.5, "sampler_name": "dpmpp_sde", "scheduler": "karras", "denoise": 0.5, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}, "class_type": "KSampler"},
        "4": {"inputs": {"ckpt_name": "juggernautXL_version2.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "5": {"inputs": {"width": 1344, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "6": {"inputs": {"text": "old prompt", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"text": "ugly", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"images": ["8", 0], "filename_prefix": "prefix"}, "class_type": "SaveImage"},
        "10": {"inputs": {"lora_stack": []}, "class_type": "LoraLoader"},
    }
    payload = {"base_payload": {"prompts": {"positive": "new", "negative": "neg"}}}
    _write_json(control / "combine_v2_corrective_retry_generation_payload.json", payload)
    _write_json(control / "combine_v2_corrective_retry_submit_request.json", {"workflow_payload_snapshot": existing_wf})
    _write_json(control / "combine_v2_corrective_retry_prompt_patch.json", {})
    _write_json(control / "combine_v2_corrective_retry_workflow_patch.json", {})
    _write_json(control / "combine_v2_corrective_retry_outputs_manifest.json", {})
    _write_json(control / "ep01_shot01_submitted_workflow.json", existing_wf)
    _write_json(control / "artifact_index.json", {})
    _write_json(control / "episode_ledger.json", [])

    for func in (combine_audit_corrective_retry_workflow, combine_diagnose_corrective_retry_recipe):
        ret = func(_make_args(str(tmp_path)))
        assert ret == 0

    # Verify audit and diagnosis artifacts before recipe v2
    boundary_keys = ("generation_allowed", "retry_allowed", "comfyui_execution", "visual_qa_executed", "assembly_executed", "downstream_executed", "production_accepted")
    for artifact_name in (
        "combine_v2_corrective_retry_workflow_audit.json",
        "combine_v2_corrective_retry_recipe_diagnosis.json",
    ):
        data = json.loads((control / artifact_name).read_text(encoding="utf-8"))
        for key in boundary_keys:
            assert data.get(key) is False, f"{artifact_name} failed boundary check on {key}"

    # Recipe v2 requires diagnosis artifact
    _write_json(control / "combine_v2_corrective_retry_root_cause_report.json", {"root_causes": []})
    _write_json(control / "combine_v2_corrective_retry_recipe_diagnosis.json", {"root_causes": []})
    ret = combine_build_corrective_recipe_v2(_make_args(str(tmp_path)))
    assert ret == 0

    data = json.loads((control / "combine_v2_corrective_retry_recipe_v2_recommendation.json").read_text(encoding="utf-8"))
    for key in boundary_keys:
        assert data.get(key) is False, f"recipe_v2 failed boundary check on {key}"
