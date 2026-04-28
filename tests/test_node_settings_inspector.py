"""Tests for MK-OBS1.1 — Node Settings Inspector."""
from __future__ import annotations

import json
from pathlib import Path

from app.control.node_settings_inspector import NodeSettingsInspector, inspect_workflow


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
                "sampler_name": "euler",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["20", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
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
                "text": "a beautiful portrait of a woman",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {
                "text": "blurry, deformed, bad anatomy",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
        "9": {
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": "agent/output",
            },
            "class_type": "SaveImage",
        },
    }


def test_inspector_extracts_ksampler_seed_steps_cfg_sampler_scheduler() -> None:
    """Test that inspector extracts KSampler seed/steps/cfg/sampler/scheduler."""
    workflow = _make_sample_workflow()
    inspector = NodeSettingsInspector(workflow)
    settings = inspector.inspect()

    ksampler = settings["ksampler"]
    assert ksampler is not None
    assert ksampler["seed"] == 747002
    assert ksampler["steps"] == 20
    assert ksampler["cfg"] == 7.0
    assert ksampler["sampler_name"] == "euler"
    assert ksampler["scheduler"] == "karras"
    assert ksampler["denoise"] == 1.0
    assert ksampler["node_id"] == "3"


def test_inspector_extracts_checkpoint_name() -> None:
    """Test that inspector extracts checkpoint name."""
    workflow = _make_sample_workflow()
    inspector = NodeSettingsInspector(workflow)
    settings = inspector.inspect()

    checkpoint = settings["checkpoint_loader"]
    assert checkpoint is not None
    assert checkpoint["ckpt_name"] == "juggernautXL_version2.safetensors"
    assert checkpoint["node_id"] == "4"


def test_inspector_extracts_latent_width_height_batch_size() -> None:
    """Test that inspector extracts latent width/height/batch_size."""
    workflow = _make_sample_workflow()
    inspector = NodeSettingsInspector(workflow)
    settings = inspector.inspect()

    latent = settings["empty_latent"]
    assert latent is not None
    assert latent["width"] == 512
    assert latent["height"] == 512
    assert latent["batch_size"] == 1
    assert latent["node_id"] == "5"


def test_inspector_extracts_prompt_hashes() -> None:
    """Test that inspector extracts prompt hashes."""
    workflow = _make_sample_workflow()
    inspector = NodeSettingsInspector(workflow)
    settings = inspector.inspect()

    positive = settings["positive_prompt"]
    assert positive is not None
    assert positive["node_id"] == "6"
    assert positive["source"] == "prompt_pack.json"
    assert positive["text_sha256"] != ""  # Should have a hash
    assert len(positive["text_sha256"]) == 64  # SHA256 hex length

    negative = settings["negative_prompt"]
    assert negative is not None
    assert negative["node_id"] == "7"
    assert negative["source"] == "prompt_pack.json"
    assert negative["text_sha256"] != ""


def test_inspector_extracts_save_image() -> None:
    """Test that inspector extracts SaveImage settings."""
    workflow = _make_sample_workflow()
    inspector = NodeSettingsInspector(workflow)
    settings = inspector.inspect()

    save_image = settings["save_image"]
    assert save_image is not None
    assert save_image["node_id"] == "9"
    assert save_image["filename_prefix"] == "agent/output"


def test_inspector_handles_missing_nodes() -> None:
    """Test that inspector handles missing nodes gracefully."""
    workflow = {"__inject__": {}}
    inspector = NodeSettingsInspector(workflow)
    settings = inspector.inspect()

    assert settings["checkpoint_loader"] is None
    assert settings["ksampler"] is None
    assert settings["empty_latent"] is None
    assert settings["positive_prompt"] is None
    assert settings["negative_prompt"] is None
    assert settings["save_image"] is None


def test_inspector_infers_positive_negative_without_inject() -> None:
    """Test that inspector infers positive/negative without __inject__ config."""
    workflow = {
        "3": {
            "inputs": {
                "seed": 123,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "karras",
                "denoise": 1.0,
            },
            "class_type": "KSampler",
        },
        "6": {
            "inputs": {
                "text": "a beautiful portrait",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {
                "text": "blurry, deformed, bad anatomy",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
    }
    inspector = NodeSettingsInspector(workflow)
    settings = inspector.inspect()

    # Should infer positive from non-negative text
    positive = settings["positive_prompt"]
    assert positive is not None
    assert positive["source"] == "inferred_positive"

    # Should infer negative from negative keywords
    negative = settings["negative_prompt"]
    assert negative is not None
    assert negative["source"] == "inferred_negative"


def test_inspect_workflow_convenience_function() -> None:
    """Test the convenience function inspect_workflow."""
    workflow = _make_sample_workflow()
    settings = inspect_workflow(workflow)

    assert "checkpoint_loader" in settings
    assert "ksampler" in settings
    assert "empty_latent" in settings
    assert "positive_prompt" in settings
    assert "negative_prompt" in settings
    assert "save_image" in settings
