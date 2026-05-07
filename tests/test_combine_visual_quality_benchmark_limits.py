"""RC-COMBINE-V2-3361-3600 — Benchmark generation limits and guard tests."""
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
        "combine-run-visual-quality-baseline-benchmark",
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


def test_max_benchmark_generations_limited_to_2():
    rc, out = _run_cli("--max-generations", "3")
    assert rc == 1
    assert out.get("current_state") == "visual_quality_baseline_runtime_blocked"
    reason = out.get("blocked_reason", "")
    assert "2" in reason or "max_generations" in reason.lower()


def test_dry_run_does_not_generate():
    rc, out = _run_cli()
    assert rc == 0
    assert out.get("baseline_generation_performed") is False
    assert out.get("workflow_submitted") is False
    assert out.get("comfyui_execution") is False
    assert out.get("production_accepted") is False


def test_blind_v5_retry_blocked():
    result = _load("combine_v2_visual_quality_baseline_benchmark_result.json")
    assert result.get("production_accepted") is False
    assert result.get("assembly_allowed") is False
    assert result.get("downstream_allowed") is False


def test_benchmark_count_does_not_exceed_2():
    result = _load("combine_v2_visual_quality_baseline_benchmark_result.json")
    count = result.get("benchmark_generation_count", 0)
    assert count <= 2, f"benchmark_generation_count {count} exceeds max 2"


def test_production_accepted_false_in_result():
    result = _load("combine_v2_visual_quality_baseline_benchmark_result.json")
    assert result["production_accepted"] is False


def test_runtime_failure_routes_to_visual_quality_baseline_runtime_blocked():
    rc, out = _run_cli("--max-generations", "5")
    assert rc == 1
    assert out.get("current_state") == "visual_quality_baseline_runtime_blocked"
    assert out.get("next_allowed_action") == "visual_quality_baseline_runtime_blocked"


def test_native_output_reconciliation_required_if_manifest_missing():
    manifest_path = CONTROL_DIR / "combine_v2_visual_quality_baseline_outputs_manifest.json"
    assert manifest_path.exists(), (
        "If ComfyUI generated an image, manifest must exist. "
        "If manifest is missing, native output must be reconciled first."
    )


def test_recipe_decision_created():
    data = _load("combine_v2_visual_quality_recipe_decision.json")
    assert data["v5_visual_failed"] is True
    assert data["baseline_generated"] is True
    assert data["recommended_next_recipe"] in (
        "baseline_default_sdxl", "simplified_v5", "rebuild_required"
    )
    assert data["operator_visual_review_required"] is True
    assert data["production_accepted"] is False


def test_operator_review_packet_created():
    data = _load("combine_v2_visual_quality_operator_review_packet.json")
    assert data["operator_visual_review_required"] is True
    assert data["production_accepted"] is False
    assert "approve_baseline_direction" in data["allowed_operator_actions"]
    assert "production_acceptance" in data["forbidden_automatic_actions"]
    assert "assembly" in data["forbidden_automatic_actions"]
