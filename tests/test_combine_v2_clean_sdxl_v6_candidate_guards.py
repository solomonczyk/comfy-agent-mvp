"""RC-COMBINE-V2-3601-3900 — Guard and preflight tests for v6 candidate generation."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CONTROL_DIR = Path(
    "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control"
)
PROJECT_ROOT = "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
CLI_MODULE = "app.cli"


def _load(name: str) -> dict:
    p = CONTROL_DIR / name
    assert p.exists(), f"Missing: {name}"
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _run_cli(*extra_args: str) -> tuple[int, dict]:
    cmd = [
        sys.executable, "-m", CLI_MODULE,
        "combine-run-clean-sdxl-v6-candidate",
        "--project-root", PROJECT_ROOT,
        "--json",
    ] + list(extra_args)
    result = subprocess.run(cmd, capture_output=True, text=True,
                            cwd="F:\\ComfyUI\\comfy-agent-mvp")
    try:
        out = json.loads(result.stdout)
    except json.JSONDecodeError:
        out = {"raw": result.stdout, "stderr": result.stderr}
    return result.returncode, out


def test_dry_run_does_not_generate():
    """Dry-run (no --execute) must not perform a generation."""
    rc, out = _run_cli()
    assert rc == 0
    assert out.get("new_generation_performed") is False
    assert out.get("workflow_submitted") is False
    assert out.get("comfyui_execution") is False
    assert out.get("production_accepted") is False


def test_second_generation_blocked():
    """After one generation, a second attempt must be blocked."""
    result_path = CONTROL_DIR / "combine_v2_clean_sdxl_v6_candidate_result.json"
    if not result_path.exists():
        return  # only meaningful after first run
    data = json.loads(result_path.read_text(encoding="utf-8"))
    count = data.get("generation_count", 0)
    if count >= 1:
        rc, out = _run_cli("--execute")
        assert rc == 1
        reason = out.get("blocked_reason", "")
        assert "generation_count" in reason or out.get("second_generation_attempted") is True


def test_production_accepted_always_false():
    """production_accepted must never be true in the v6 result."""
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assert data["production_accepted"] is False


def test_assembly_and_downstream_blocked():
    """Assembly and downstream must be blocked in the v6 result."""
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assert data.get("assembly_executed") is False
    assert data.get("downstream_executed") is False


def test_baseline_rejection_required_preflight():
    """Baseline rejection artifact must exist before v6 can run."""
    rejection = _load("combine_v2_baseline_operator_visual_rejection.json")
    assert rejection.get("production_accepted") is False


def test_saveimage_prefix_in_workflow():
    """v6 workflow SaveImage prefix must match expected value."""
    wf = _load("shot02_clean_sdxl_v6_candidate_workflow.json")
    prefixes = [
        node.get("inputs", {}).get("filename_prefix", "")
        for node in wf.values()
        if isinstance(node, dict) and node.get("class_type") == "SaveImage"
    ]
    assert any(p == "combine_v2_clean_sdxl_v6_candidate_shot02" for p in prefixes)


def test_resolution_meets_minimum():
    """v6 workflow EmptyLatentImage must have short side >= 1024."""
    wf = _load("shot02_clean_sdxl_v6_candidate_workflow.json")
    for node in wf.values():
        if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage":
            inp = node.get("inputs", {})
            w, h = inp.get("width", 0), inp.get("height", 0)
            assert min(w, h) >= 1024, f"Resolution {w}x{h} below minimum 1024"
