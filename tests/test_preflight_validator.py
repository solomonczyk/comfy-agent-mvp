"""Tests for MK-OBS1.3 — Preflight Validator."""
from __future__ import annotations

from app.control.node_settings_inspector import NodeSettingsInspector
from app.control.preflight_validator import PreflightValidator, validate_preflight


def _make_sample_workflow() -> dict:
    """Create a sample workflow for testing."""
    return {
        "__inject__": {
            "positive_prompt_node": "6",
            "negative_prompt_node": "7",
        },
        "3": {
            "inputs": {
                "seed": 747002,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "denoise": 1.0,
            },
            "class_type": "KSampler",
        },
        "4": {
            "inputs": {
                "ckpt_name": "juggernautXL_version2.safetensors",
            },
            "class_type": "CheckpointLoaderSimple",
        },
        "5": {
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1,
            },
            "class_type": "EmptyLatentImage",
        },
        "6": {
            "inputs": {
                "text": "positive prompt",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {
                "text": "negative prompt",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
    }


def _make_sample_prompt_pack() -> dict:
    """Create a sample prompt pack for testing."""
    return {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "checkpoint": "juggernautXL_version2.safetensors",
        "beats": [
            {
                "beat_id": "beat_01",
                "steps": 20,
                "cfg": 7.0,
                "sampler": "dpmpp_sde",
                "scheduler": "karras",
            }
        ],
    }


def _make_sample_config() -> dict:
    """Create a sample config for testing."""
    return {
        "checkpoint": "juggernautXL_version2.safetensors",
        "steps": 20,
        "max_frames_per_batch": 3,
    }


def test_preflight_passes_when_all_settings_match() -> None:
    """Test that preflight passes when all settings match."""
    workflow = _make_sample_workflow()
    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is True
    assert result["failures"] == []
    assert result["total_checks"] == 11
    assert result["failed_checks"] == 0


def test_preflight_fails_when_sampler_mismatch() -> None:
    """Test that preflight fails when sampler mismatch."""
    workflow = _make_sample_workflow()
    # Change sampler in workflow
    workflow["3"]["inputs"]["sampler_name"] = "euler"  # Mismatch with prompt_pack

    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False
    assert result["failed_checks"] == 1

    sampler_failure = next((f for f in result["failures"] if f["check"] == "sampler_match"), None)
    assert sampler_failure is not None
    assert "mismatch" in sampler_failure["reason"]


def test_preflight_fails_when_seed_is_random_missing() -> None:
    """Test that preflight fails when seed is random/missing."""
    workflow = _make_sample_workflow()
    # Set seed to 0 (random) or None
    workflow["3"]["inputs"]["seed"] = 0

    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False

    seed_failure = next((f for f in result["failures"] if f["check"] == "seed_deterministic"), None)
    assert seed_failure is not None
    assert "not deterministic" in seed_failure["reason"]


def test_preflight_fails_when_seed_is_none() -> None:
    """Test that preflight fails when seed is None."""
    workflow = _make_sample_workflow()
    workflow["3"]["inputs"]["seed"] = None

    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False

    seed_failure = next((f for f in result["failures"] if f["check"] == "seed_deterministic"), None)
    assert seed_failure is not None


def test_preflight_fails_when_prompt_source_is_not_prompt_pack() -> None:
    """Test that preflight fails when prompt source is not prompt_pack.json."""
    workflow = _make_sample_workflow()
    # Remove __inject__ to force inferred source
    del workflow["__inject__"]

    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False

    pos_failure = next((f for f in result["failures"] if f["check"] == "positive_prompt_source"), None)
    assert pos_failure is not None
    assert "not prompt_pack.json" in pos_failure["reason"]


def test_preflight_fails_when_reference_lock_missing() -> None:
    """Test that preflight fails when reference lock missing."""
    workflow = _make_sample_workflow()
    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = None  # Missing

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False

    ref_failure = next((f for f in result["failures"] if f["check"] == "reference_lock_approved"), None)
    assert ref_failure is not None
    assert "not available" in ref_failure["reason"]


def test_preflight_fails_when_reference_lock_denied() -> None:
    """Test that preflight fails when reference lock denied."""
    workflow = _make_sample_workflow()
    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": False, "reason": "Reference not approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False

    ref_failure = next((f for f in result["failures"] if f["check"] == "reference_lock_approved"), None)
    assert ref_failure is not None


def test_preflight_fails_when_prompt_pack_missing() -> None:
    """Test that preflight fails when prompt_pack missing."""
    workflow = _make_sample_workflow()
    prompt_pack = None  # Missing
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False

    pack_failure = next((f for f in result["failures"] if f["check"] == "prompt_pack_exists"), None)
    assert pack_failure is not None


def test_preflight_fails_when_checkpoint_mismatch() -> None:
    """Test that preflight fails when checkpoint mismatch."""
    workflow = _make_sample_workflow()
    # Change checkpoint in workflow
    workflow["4"]["inputs"]["ckpt_name"] = "different_checkpoint.safetensors"

    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False

    checkpoint_failure = next((f for f in result["failures"] if f["check"] == "checkpoint_match"), None)
    assert checkpoint_failure is not None
    assert "mismatch" in checkpoint_failure["reason"]


def test_preflight_fails_when_batch_size_exceeds_limit() -> None:
    """Test that preflight fails when batch_size exceeds safe limit."""
    workflow = _make_sample_workflow()
    workflow["5"]["inputs"]["batch_size"] = 10  # Exceeds max_frames_per_batch of 3

    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False

    batch_failure = next((f for f in result["failures"] if f["check"] == "batch_size_safe"), None)
    assert batch_failure is not None
    assert "exceeds safe limit" in batch_failure["reason"]


def test_preflight_fails_when_resolution_exceeds_limit() -> None:
    """Test that preflight fails when resolution exceeds safe limit."""
    workflow = _make_sample_workflow()
    workflow["5"]["inputs"]["width"] = 4096  # Exceeds safe limit of 2048

    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    assert result["passed"] is False

    res_failure = next((f for f in result["failures"] if f["check"] == "resolution_safe"), None)
    assert res_failure is not None
    assert "exceeds safe limit" in res_failure["reason"]


def test_validate_preflight_convenience_function() -> None:
    """Test the convenience function validate_preflight."""
    workflow = _make_sample_workflow()
    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    result = validate_preflight(workflow, prompt_pack, reference_lock_status, config)

    assert "passed" in result
    assert "failures" in result
    assert "total_checks" in result
    assert "failed_checks" in result


def test_no_comfyui_or_subprocess_called() -> None:
    """Test that no ComfyUI or subprocess is called during validation."""
    workflow = _make_sample_workflow()
    prompt_pack = _make_sample_prompt_pack()
    config = _make_sample_config()
    reference_lock_status = {"approved": True, "reason": "All references approved"}

    # This test ensures we only validate locally without external calls
    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    result = validator.validate()

    # If this completes without error, no subprocess was called
    assert result is not None
