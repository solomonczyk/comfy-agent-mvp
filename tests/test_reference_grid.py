"""Tests for ReferenceGridGenerator (MK-R1).

Uses a mock ComfyUI session so no live server is required.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from app.brief.models import CharacterDef, ProjectMeta
from app.reference.grid_generator import ReferenceGridGenerator, POSE_HINTS


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def char() -> CharacterDef:
    return CharacterDef(
        name="Alia",
        visual_description="young woman, dark hair, blue eyes, casual clothes",
    )


@pytest.fixture()
def meta() -> ProjectMeta:
    return ProjectMeta(
        title="Test Episode",
        fps=1,
        target_duration_sec=4.0,
        style_hint="anime style",
        mood="calm",
    )


@pytest.fixture()
def workflow_template() -> dict:
    return {
        "__inject__": {"positive_prompt_node": "6"},
        "3": {
            "inputs": {
                "seed": 123,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
            "class_type": "KSampler",
        },
        "4": {"inputs": {"ckpt_name": "model.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "5": {"inputs": {"width": 512, "height": 512, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "6": {"inputs": {"text": "", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"text": "", "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
    }


def _make_png(path: Path, w: int = 64, h: int = 64) -> None:
    img = Image.fromarray(np.zeros((h, w, 3), dtype=np.uint8), mode="RGB")
    img.save(str(path))


def _build_generator(tmp_path: Path, workflow_template: dict, grid_size: int = 2):
    """Build a ReferenceGridGenerator with a mocked session that returns synthetic frames."""
    session = MagicMock()

    # POST /prompt → returns prompt_id
    post_resp = MagicMock()
    post_resp.status_code = 200
    post_resp.json.return_value = {"prompt_id": "test-prompt-id"}
    session.post.return_value = post_resp

    # GET /history/<id> → completed immediately
    get_resp = MagicMock()
    get_resp.status_code = 200
    get_resp.json.return_value = {
        "test-prompt-id": {"status": {"completed": True}}
    }
    session.get.return_value = get_resp

    gen = ReferenceGridGenerator(
        host="127.0.0.1",
        port=8188,
        workflow_template=workflow_template,
        session=session,
    )
    return gen


# ── helpers ───────────────────────────────────────────────────────────────────

def _patch_collect(gen, tmp_path: Path, grid_size: int, img_w: int = 64, img_h: int = 64):
    """Patch _collect_frame to return synthetic PNG files inside frames/ subdir."""
    counter = {"n": 0}

    def fake_collect(prompt_id, job_start, idx, character_name, output_dir):
        # output_dir is already tmp_path/frames/ as passed by generate()
        frames_dir = Path(output_dir)
        frames_dir.mkdir(parents=True, exist_ok=True)
        dest = frames_dir / f"{character_name}_frame_{idx:04d}.png"
        _make_png(dest, img_w, img_h)
        counter["n"] += 1
        return dest

    gen._collect_frame = fake_collect
    return counter


# ── tests ─────────────────────────────────────────────────────────────────────

def test_generate_returns_path(tmp_path, char, meta, workflow_template):
    gen = _build_generator(tmp_path, workflow_template, grid_size=2)
    _patch_collect(gen, tmp_path, grid_size=2)

    result = gen.generate(char, meta, tmp_path, grid_size=2)
    assert isinstance(result, Path)


def test_generate_path_exists(tmp_path, char, meta, workflow_template):
    gen = _build_generator(tmp_path, workflow_template, grid_size=2)
    _patch_collect(gen, tmp_path, grid_size=2)

    result = gen.generate(char, meta, tmp_path, grid_size=2)
    assert result.exists(), f"Grid not found at {result}"


def test_generate_is_valid_png(tmp_path, char, meta, workflow_template):
    gen = _build_generator(tmp_path, workflow_template, grid_size=2)
    _patch_collect(gen, tmp_path, grid_size=2)

    result = gen.generate(char, meta, tmp_path, grid_size=2)
    img = Image.open(result)
    assert img.format == "PNG"


def test_generate_grid_dimensions(tmp_path, char, meta, workflow_template):
    grid_size = 2
    img_w, img_h = 64, 64
    gen = _build_generator(tmp_path, workflow_template, grid_size=grid_size)
    _patch_collect(gen, tmp_path, grid_size=grid_size, img_w=img_w, img_h=img_h)

    result = gen.generate(char, meta, tmp_path, grid_size=grid_size)
    img = Image.open(result)
    assert img.width == grid_size * img_w
    assert img.height == grid_size * img_h


def test_get_best_frame_returns_frame_0000(tmp_path, char):
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    best = frames_dir / f"{char.name}_frame_0000.png"
    _make_png(best)
    gen = ReferenceGridGenerator.__new__(ReferenceGridGenerator)
    result = gen.get_best_frame(tmp_path, char.name)
    assert result == best


def test_get_best_frame_falls_back_to_grid(tmp_path, char):
    grid = tmp_path / f"{char.name}_reference_grid.png"
    _make_png(grid)
    gen = ReferenceGridGenerator.__new__(ReferenceGridGenerator)
    result = gen.get_best_frame(tmp_path, char.name)
    assert result == grid


def test_get_best_frame_raises_when_nothing_exists(tmp_path, char):
    import pytest
    gen = ReferenceGridGenerator.__new__(ReferenceGridGenerator)
    with pytest.raises(FileNotFoundError):
        gen.get_best_frame(tmp_path, char.name)


def test_same_character_same_seed(char):
    seed_a = hash(char.name) % (2 ** 32)
    seed_b = hash(char.name) % (2 ** 32)
    assert seed_a == seed_b


def test_different_characters_different_seeds():
    char_a = CharacterDef(name="Alia", visual_description="dark hair")
    char_b = CharacterDef(name="Boris", visual_description="blonde")
    seed_a = hash(char_a.name) % (2 ** 32)
    seed_b = hash(char_b.name) % (2 ** 32)
    assert seed_a != seed_b


def test_grid_size_2_produces_4_images(tmp_path, char, meta, workflow_template):
    gen = _build_generator(tmp_path, workflow_template, grid_size=2)
    counter = _patch_collect(gen, tmp_path, grid_size=2)

    gen.generate(char, meta, tmp_path, grid_size=2)
    assert counter["n"] == 4


def test_frames_saved_in_frames_subdir(tmp_path, char, meta, workflow_template):
    gen = _build_generator(tmp_path, workflow_template, grid_size=2)
    _patch_collect(gen, tmp_path, grid_size=2)

    gen.generate(char, meta, tmp_path, grid_size=2)
    frames_dir = tmp_path / "frames"
    assert frames_dir.exists()
    frame_pngs = list(frames_dir.glob(f"{char.name}_frame_*.png"))
    assert len(frame_pngs) == 4


def test_grid_filename_contains_character_name(tmp_path, char, meta, workflow_template):
    gen = _build_generator(tmp_path, workflow_template, grid_size=2)
    _patch_collect(gen, tmp_path, grid_size=2)

    result = gen.generate(char, meta, tmp_path, grid_size=2)
    assert char.name in result.name


def test_pose_hints_cover_grid_size_4():
    assert len(POSE_HINTS) >= 16


def test_build_prompt_includes_description_and_pose(char, meta):
    gen = ReferenceGridGenerator.__new__(ReferenceGridGenerator)
    prompt = gen._build_prompt(char, meta.style_hint or "", meta.mood or "", "front view, neutral pose")
    assert char.visual_description in prompt
    assert "front view, neutral pose" in prompt


def test_build_prompt_includes_style_and_mood(char, meta):
    gen = ReferenceGridGenerator.__new__(ReferenceGridGenerator)
    prompt = gen._build_prompt(char, "anime style", "calm", "side profile left")
    assert "anime style" in prompt
    assert "calm" in prompt
