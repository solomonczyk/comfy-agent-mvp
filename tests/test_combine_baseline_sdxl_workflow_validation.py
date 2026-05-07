"""RC-COMBINE-V2-3361-3600 — Baseline SDXL workflow validation tests."""
from __future__ import annotations

import json
from pathlib import Path

CONTROL_DIR = Path(
    "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control"
)


def _load_wf() -> dict:
    p = CONTROL_DIR / "shot02_baseline_default_sdxl_workflow.json"
    assert p.exists(), "Baseline workflow missing"
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_baseline_workflow_exists():
    p = CONTROL_DIR / "shot02_baseline_default_sdxl_workflow.json"
    assert p.exists()


def test_baseline_workflow_is_valid_node_graph():
    wf = _load_wf()
    assert wf, "Workflow must not be empty"
    for key, val in wf.items():
        assert isinstance(val, dict), f"Node {key} is not a dict"
        assert "class_type" in val, f"Node {key} missing class_type"


def test_baseline_workflow_has_no_non_node_metadata():
    wf = _load_wf()
    non_node_keys = [k for k, v in wf.items() if not isinstance(v, dict) or "class_type" not in v]
    assert non_node_keys == [], f"Non-node metadata found: {non_node_keys}"


def test_baseline_workflow_has_saveimage_with_correct_prefix():
    wf = _load_wf()
    found = False
    for node in wf.values():
        if node.get("class_type") == "SaveImage":
            prefix = node.get("inputs", {}).get("filename_prefix", "")
            assert prefix == "combine_v2_baseline_default_sdxl_shot02", \
                f"SaveImage prefix wrong: {prefix}"
            found = True
    assert found, "No SaveImage node found"


def test_baseline_workflow_resolution_minimum_1024():
    wf = _load_wf()
    for node in wf.values():
        if node.get("class_type") == "EmptyLatentImage":
            w = node["inputs"]["width"]
            h = node["inputs"]["height"]
            assert min(w, h) >= 1024, f"Short side {min(w,h)} < 1024"
            return
    assert False, "No EmptyLatentImage node found"


def test_baseline_workflow_uses_juggernaut_checkpoint():
    wf = _load_wf()
    for node in wf.values():
        if node.get("class_type") == "CheckpointLoaderSimple":
            ckpt = node.get("inputs", {}).get("ckpt_name", "")
            assert "juggernautXL" in ckpt or "juggernaut" in ckpt.lower(), \
                f"Unexpected checkpoint: {ckpt}"
            return
    assert False, "No CheckpointLoaderSimple node found"


def test_baseline_workflow_denoise_is_1():
    wf = _load_wf()
    for node in wf.values():
        if node.get("class_type") == "KSampler":
            denoise = node.get("inputs", {}).get("denoise", None)
            assert denoise == 1.0, f"denoise must be 1.0, got {denoise}"
            return
    assert False, "No KSampler node found"


def test_baseline_workflow_has_no_lora_stack():
    wf = _load_wf()
    lora_nodes = [k for k, v in wf.items() if v.get("class_type") == "LoraLoader"]
    assert lora_nodes == [], f"Baseline workflow must not have LoraLoader nodes: {lora_nodes}"


def test_baseline_workflow_outputs_manifest_exists_after_generation():
    p = CONTROL_DIR / "combine_v2_visual_quality_baseline_outputs_manifest.json"
    assert p.exists(), "Outputs manifest missing after generation"
    with open(p, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    assert isinstance(manifest, list), "Manifest must be a list"
    assert len(manifest) >= 1, "Manifest must have at least one entry"
    entry = manifest[0]
    assert entry.get("readable") is True
    assert entry.get("size_bytes", 0) > 0
    assert entry.get("sha256", "")


def test_baseline_canonical_asset_exists():
    p = CONTROL_DIR / "combine_v2_visual_quality_baseline_outputs_manifest.json"
    assert p.exists()
    with open(p, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    for entry in manifest:
        asset_path = Path("F:/ComfyUI/comfy-agent-mvp") / entry["path"]
        assert asset_path.exists(), f"Canonical asset missing: {asset_path}"
        assert asset_path.stat().st_size > 0
