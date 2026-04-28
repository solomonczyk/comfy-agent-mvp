"""Tests for MK-F2 — CLI.

Uses argparse direct call and mocks ExecutionRunner.
"""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pytest

from app.cli import main


# ── helpers ───────────────────────────────────────────────────────────────────

def _create_config_file(tmp_path):
    config = {
        "lora_dir": "test/loras",
        "fallback_voice_id": "tts_ru_01",
        "default_negative": "blurry",
        "fps": 8,
        "min_keyframes": 2,
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    return config_path


def _create_brief_file(tmp_path):
    brief = """
## Meta
title: Test
duration: 5

## Characters
- name: Hero
  visual: knight

## Scenes
- action: hero walks
"""
    brief_path = tmp_path / "brief.md"
    brief_path.write_text(brief)
    return brief_path


def _create_voice_map(tmp_path):
    voice_map = {"tts_ru_01": {"engine": "coqui", "lang": "ru"}}
    voice_path = tmp_path / "voice_map.json"
    voice_path.write_text(json.dumps(voice_map))
    return voice_path


# ── argument parsing ───────────────────────────────────────────────────────────

def test_brief_missing_exits_nonzero():
    with patch("sys.argv", ["app", "run"]):
        with pytest.raises(SystemExit):
            main()


def test_valid_brief_calls_runner(tmp_path, monkeypatch):
    config_path = _create_config_file(tmp_path)
    brief_path = _create_brief_file(tmp_path)
    voice_path = _create_voice_map(tmp_path)

    monkeypatch.chdir(tmp_path)

    # Create a mock that returns different data based on path
    file_data = {
        str(config_path): config_path.read_text(),
        str(voice_path): voice_path.read_text(),
        str(brief_path): brief_path.read_text(),
        "data/voice_map.json": voice_path.read_text(),
    }

    def custom_open(path, *args, **kwargs):
        path_str = str(path)
        if path_str in file_data:
            return StringIO(file_data[path_str])
        raise FileNotFoundError(path_str)

    with patch("builtins.open", side_effect=custom_open):
        with patch("app.cli.ExecutionRunner") as mock_runner_class:
            mock_runner = Mock()
            mock_runner.run.return_value = Path("output/test.mp4")
            mock_runner_class.return_value = mock_runner

            sys.argv = ["app", "run", "--brief", str(brief_path), "--config", str(config_path)]
            result = main()

            assert result == 0
            mock_runner.run.assert_called_once()


# ── MK-REAL3R — Workflow template selection tests ─────────────────────────────────

def test_cli_selects_img2img_reference_template_for_reference_locked_mode(tmp_path, monkeypatch):
    """MK-REAL3R — Test that CLI selects img2img/reference template when generation_mode == 'reference_locked'."""
    from app.cli import generate_frames_from_prompt_pack
    
    config_path = _create_config_file(tmp_path)
    
    # Create img2img reference template
    img2img_template = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],  # Connected to VAEEncode
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/alya_reference_01.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {},
        },
    }
    img2img_template_path = tmp_path / "data" / "config" / "workflow_template_img2img_reference.json"
    img2img_template_path.parent.mkdir(parents=True, exist_ok=True)
    img2img_template_path.write_text(json.dumps(img2img_template))
    
    # Create prompt_pack.json with generation_mode="reference_locked" and beats
    prompt_pack = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "characters": ["Alya"],
        "beats": [
            {
                "beat_id": "beat_001",
                "positive_prompt": "test prompt",
                "negative_prompt": "blurry",
                "seed_policy": "deterministic",
            }
        ],
        "generation_mode": "reference_locked",
        "reference_image_path": "data/references/alya.png",
        "denoise": 0.42,
    }
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    prompt_pack_path = control_dir / "prompt_pack.json"
    prompt_pack_path.write_text(json.dumps(prompt_pack))
    
    # Create voice_map.json
    voice_map_path = tmp_path / "data" / "voice_map.json"
    voice_map_path.parent.mkdir(parents=True, exist_ok=True)
    voice_map_path.write_text(json.dumps({"default": "tts_ru_01"}))
    
    monkeypatch.chdir(tmp_path)
    
    # Mock ComfySubmitter to capture the workflow template used
    with patch("app.comfy.submitter.ComfySubmitter") as mock_submitter_class:
        mock_submitter = Mock()
        
        # Capture workflow_template from submit calls
        captured_workflow = {}
        
        def mock_submit(*args, **kwargs):
            # workflow_template is the second positional argument (args[1])
            if len(args) >= 2:
                captured_workflow["template"] = args[1]
            from app.comfy.models import SubmitResult
            return SubmitResult(
                prompt_id="test-123",
                scene_id="shot01",
                frame_paths=[],
                elapsed_sec=1.0,
            )
        
        mock_submitter.submit = mock_submit
        mock_submitter.flush_queue = Mock()
        mock_submitter_class.return_value = mock_submitter
        
        # Call generate_frames_from_prompt_pack directly with Namespace args
        import argparse
        args = argparse.Namespace(
            config=str(config_path),
            output=str(tmp_path / "output"),
            host="localhost",
            port=8188,
            episode_id="ep01",
            shot_id="shot01",
            prompt_pack=True,
            brief="",  # Used as metadata reference only
        )
        generate_frames_from_prompt_pack(args)
        
        # Verify img2img reference template was used (has LoadImage node)
        assert captured_workflow["template"] is not None
        assert any(
            node.get("class_type") == "LoadImage"
            for node in captured_workflow["template"].values()
        )


def test_generate_frames_prompt_pack_path_preserves_reference_locked_metadata(tmp_path, monkeypatch):
    """MK-REAL3R-4 — generate-frames --prompt-pack must load prompt_pack.json, preserve reference_locked metadata, and submit correct workflow."""
    from app.cli import generate_frames_from_prompt_pack
    import argparse

    # Create project structure
    (tmp_path / "data" / "config").mkdir(parents=True)
    (tmp_path / "output" / "control").mkdir(parents=True)
    (tmp_path / "references").mkdir(parents=True)
    alya_ref = tmp_path / "references" / "Аля.png"
    alya_ref.write_bytes(b"fake_ref_image")

    # Create img2img reference workflow template
    img2img_template = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 0,
                "steps": 16,
                "cfg": 7.0,
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "denoise": 0.5,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["8", 0],
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"},
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/alya_reference_01.png", "upload": "image"},
        },
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "", "clip": ["4", 1]}},
        "8": {"class_type": "VAEEncode", "inputs": {"pixels": ["11", 0], "vae": ["4", 2]}},
        "10": {"class_type": "EmptyLatentImage", "inputs": {"width": 480, "height": 640, "batch_size": 1}},
        "11": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["5", 0],
                "upscale_method": "lanczos",
                "width": 480,
                "height": 640,
                "crop": "disabled",
            },
        },
    }
    workflow_path = tmp_path / "data" / "config" / "workflow_template_img2img_reference.json"
    workflow_path.write_text(json.dumps(img2img_template))

    # Create config.json and voice_map.json (required by generate_frames_from_prompt_pack)
    config_data = {
        "lora_dir": "data/loras",
        "fallback_voice_id": "default",
        "default_negative": "bad anatomy",
        "fps": 24,
        "min_keyframes": 1,
        "checkpoint": "CyberRealisticXLPlay_V7.0_FP16.safetensors",
    }
    (tmp_path / "data" / "config.json").write_text(json.dumps(config_data), encoding="utf-8")
    (tmp_path / "data" / "voice_map.json").write_text(json.dumps({"default": "default_voice"}), encoding="utf-8")

    # Create a proper brief file (required by parser even in prompt-pack mode)
    (tmp_path / "data" / "briefs").mkdir(parents=True)
    (tmp_path / "data" / "briefs" / "ep01_shot01_brief.md").write_text(
        "## Meta\ntitle: Test\nduration: 5\n\n## Characters\n- name: Hero\n  visual: knight\n\n## Scenes\n- action: hero walks\n"
    )

    # Create prompt_pack.json with reference_locked metadata
    prompt_pack = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "characters": ["Alya"],
        "beats": [
            {
                "beat_id": "beat_001",
                "positive_prompt": "vertical portrait composition, ordinary tired young woman",
                "negative_prompt": "glamour, fashion model, beauty portrait, studio portrait",
                "seed_policy": "deterministic",
            }
        ],
        "generation_mode": "reference_locked",
        "reference_image_path": str(alya_ref),
        "denoise": 0.5,
    }
    (tmp_path / "output" / "control" / "prompt_pack.json").write_text(
        json.dumps(prompt_pack), encoding="utf-8"
    )

    monkeypatch.chdir(tmp_path)

    # Mock ComfySubmitter to capture submitted workflow and verify graph contract
    with patch("app.comfy.submitter.ComfySubmitter") as mock_submitter_class:
        mock_submitter = Mock()
        captured_workflow = {"wf": None}
        captured_kwargs = {"kwargs": None}

        def mock_submit(*args, **kwargs):
            if len(args) >= 2:
                captured_workflow["wf"] = args[1]
            captured_kwargs["kwargs"] = kwargs
            from app.comfy.models import SubmitResult
            return SubmitResult(
                prompt_id="test-123",
                scene_id="shot01",
                frame_paths=[],
                elapsed_sec=1.0,
            )

        mock_submitter.submit = mock_submit
        mock_submitter.flush_queue = Mock()
        mock_submitter_class.return_value = mock_submitter

        args = argparse.Namespace(
            config=str(tmp_path / "data" / "config.json"),
            output=str(tmp_path / "output"),
            host="localhost",
            port=8188,
            episode_id="ep01",
            shot_id="shot01",
            prompt_pack=True,
            brief=str(tmp_path / "data" / "briefs" / "ep01_shot01_brief.md"),
        )

        generate_frames_from_prompt_pack(args)

        # Verify submitter was called with correct metadata
        assert captured_kwargs["kwargs"]["generation_mode"] == "reference_locked"
        assert "Аля.png" in str(captured_kwargs["kwargs"]["reference_image_path"])

        # Verify workflow contains correct reference_locked node chain
        wf = captured_workflow["wf"]
        assert any(
            node.get("class_type") == "LoadImage"
            for node in wf.values()
            if isinstance(node, dict)
        )
        assert any(
            node.get("class_type") == "ImageScale"
            for node in wf.values()
            if isinstance(node, dict)
        )
        assert any(
            node.get("class_type") == "VAEEncode"
            for node in wf.values()
            if isinstance(node, dict)
        )

        # Verify KSampler latent_image points to VAEEncode, not EmptyLatentImage
        ksampler = next(
            node for node in wf.values()
            if isinstance(node, dict) and node.get("class_type") == "KSampler"
        )
        latent_source_id = str(ksampler["inputs"]["latent_image"][0])
        assert wf[latent_source_id]["class_type"] == "VAEEncode"

        # Verify EmptyLatentImage batch_size == 1
        empty_latent = next(
            node for node in wf.values()
            if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage"
        )
        assert empty_latent["inputs"]["batch_size"] == 1

        # Verify ImageScale resolution is 480x640
        image_scale = next(
            node for node in wf.values()
            if isinstance(node, dict) and node.get("class_type") == "ImageScale"
        )
        assert image_scale["inputs"]["width"] == 480
        assert image_scale["inputs"]["height"] == 640


def test_host_port_passed_to_runner(tmp_path, monkeypatch):
    config_path = _create_config_file(tmp_path)
    brief_path = _create_brief_file(tmp_path)
    voice_path = _create_voice_map(tmp_path)

    monkeypatch.chdir(tmp_path)

    file_data = {
        str(config_path): config_path.read_text(),
        str(voice_path): voice_path.read_text(),
        str(brief_path): brief_path.read_text(),
        "data/voice_map.json": voice_path.read_text(),
    }

    def custom_open(path, *args, **kwargs):
        path_str = str(path)
        if path_str in file_data:
            return StringIO(file_data[path_str])
        raise FileNotFoundError(path_str)

    with patch("builtins.open", side_effect=custom_open):
        with patch("app.cli.ExecutionRunner") as mock_runner_class:
            mock_runner_class.return_value.run.return_value = Path("output/test.mp4")

            sys.argv = [
                "app",
                "run",
                "--brief",
                str(brief_path),
                "--config",
                str(config_path),
                "--host",
                "192.168.1.100",
                "--port",
                "9999",
            ]
            main()

            mock_runner_class.assert_called_once()
            call_kwargs = mock_runner_class.call_args[1]
            assert call_kwargs["comfy_host"] == "192.168.1.100"
            assert call_kwargs["comfy_port"] == 9999


def test_runner_exception_exits_with_error(tmp_path, monkeypatch):
    config_path = _create_config_file(tmp_path)
    brief_path = _create_brief_file(tmp_path)
    voice_path = _create_voice_map(tmp_path)

    monkeypatch.chdir(tmp_path)

    file_data = {
        str(config_path): config_path.read_text(),
        str(voice_path): voice_path.read_text(),
        str(brief_path): brief_path.read_text(),
        "data/voice_map.json": voice_path.read_text(),
    }

    def custom_open(path, *args, **kwargs):
        path_str = str(path)
        if path_str in file_data:
            return StringIO(file_data[path_str])
        raise FileNotFoundError(path_str)

    with patch("builtins.open", side_effect=custom_open):
        with patch("app.cli.ExecutionRunner") as mock_runner_class:
            mock_runner_class.return_value.run.side_effect = Exception("Test error")

            sys.argv = ["app", "run", "--brief", str(brief_path), "--config", str(config_path)]
            result = main()

            assert result == 1


def test_success_prints_episode_saved(tmp_path, monkeypatch, capsys):
    config_path = _create_config_file(tmp_path)
    brief_path = _create_brief_file(tmp_path)
    voice_path = _create_voice_map(tmp_path)

    monkeypatch.chdir(tmp_path)

    file_data = {
        str(config_path): config_path.read_text(),
        str(voice_path): voice_path.read_text(),
        str(brief_path): brief_path.read_text(),
        "data/voice_map.json": voice_path.read_text(),
    }

    def custom_open(path, *args, **kwargs):
        path_str = str(path)
        if path_str in file_data:
            return StringIO(file_data[path_str])
        raise FileNotFoundError(path_str)

    with patch("builtins.open", side_effect=custom_open):
        with patch("app.cli.ExecutionRunner") as mock_runner_class:
            mock_runner_class.return_value.run.return_value = Path("output/test_episode.mp4")

            sys.argv = ["app", "run", "--brief", str(brief_path), "--config", str(config_path)]
            main()

            captured = capsys.readouterr()
            assert "Episode saved:" in captured.out
            assert "test_episode.mp4" in captured.out
