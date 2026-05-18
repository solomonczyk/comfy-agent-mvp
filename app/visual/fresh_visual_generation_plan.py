"""
Fresh Visual Generation Plan module.

Planning-layer only. No generation. No ComfyUI submit. No retry.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PLAN_DIR = Path(
    "data/rc2_multishot1_ep01/output/control/fresh_visual_generation_plan"
)

PLAN_FILE = PLAN_DIR / "fresh_visual_generation_plan.json"
APP_MAP_FILE = PLAN_DIR / "quality_reference_application_map.json"
CONSTRAINTS_FILE = PLAN_DIR / "visual_recipe_constraints.json"
GATE_REQUIREMENTS_FILE = PLAN_DIR / "future_generation_gate_requirements.json"
SCOPE_GUARD_FILE = PLAN_DIR / "generation_plan_scope_guard.json"
UPDATE_REPORT_FILE = PLAN_DIR / "generation_plan_update_report.json"


def load_plan(project_root: Path | None = None) -> dict[str, Any]:
    path = (project_root / PLAN_FILE) if project_root else PLAN_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def load_application_map(project_root: Path | None = None) -> dict[str, Any]:
    path = (project_root / APP_MAP_FILE) if project_root else APP_MAP_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def load_recipe_constraints(project_root: Path | None = None) -> dict[str, Any]:
    path = (project_root / CONSTRAINTS_FILE) if project_root else CONSTRAINTS_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def load_gate_requirements(project_root: Path | None = None) -> dict[str, Any]:
    path = (project_root / GATE_REQUIREMENTS_FILE) if project_root else GATE_REQUIREMENTS_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def load_scope_guard(project_root: Path | None = None) -> dict[str, Any]:
    path = (project_root / SCOPE_GUARD_FILE) if project_root else SCOPE_GUARD_FILE
    return json.loads(path.read_text(encoding="utf-8"))


def validate_plan_semantics(plan: dict[str, Any]) -> list[str]:
    """Return list of violation strings; empty means valid."""
    violations: list[str] = []

    if plan.get("plan_type") != "future_generation_plan_only":
        violations.append("plan_type must be future_generation_plan_only")
    if plan.get("generation_authorized") is not False:
        violations.append("generation_authorized must be false")
    if plan.get("comfyui_submit_authorized") is not False:
        violations.append("comfyui_submit_authorized must be false")
    if plan.get("retry_authorized") is not False:
        violations.append("retry_authorized must be false")
    if plan.get("quality_reference_usage") != "quality_calibration_only":
        violations.append("quality_reference_usage must be quality_calibration_only")
    if plan.get("requires_separate_generation_gate") is not True:
        violations.append("requires_separate_generation_gate must be true")
    if plan.get("requires_operator_authorization_before_generation") is not True:
        violations.append("requires_operator_authorization_before_generation must be true")
    if plan.get("production_accepted") is not False:
        violations.append("production_accepted must be false")
    if plan.get("assembly_allowed") is not False:
        violations.append("assembly_allowed must be false")
    if plan.get("downstream_blocked") is not True:
        violations.append("downstream_blocked must be true")

    return violations


def validate_application_map_scope(app_map: dict[str, Any]) -> list[str]:
    """Return list of scope violation strings; empty means valid."""
    violations: list[str] = []

    must_not = app_map.get("must_not_define", [])
    forbidden_defines = [
        "character_identity",
        "full_face_identity",
        "full_body_appearance",
        "final_scene_composition",
        "production_asset_acceptance",
    ]
    for item in forbidden_defines:
        if item not in must_not:
            violations.append(f"must_not_define missing: {item}")

    if not app_map.get("scope_expansion_requires_operator_review"):
        violations.append("scope_expansion_requires_operator_review must be true")

    return violations


def validate_gate_requirements(gate: dict[str, Any]) -> list[str]:
    """Return list of gate requirement violations; empty means valid."""
    violations: list[str] = []

    if gate.get("generation_gate_required") is not True:
        violations.append("generation_gate_required must be true")
    if gate.get("operator_authorization_required") is not True:
        violations.append("operator_authorization_required must be true")
    if gate.get("blind_retry_allowed") is not False:
        violations.append("blind_retry_allowed must be false")
    if gate.get("must_stop_after_generation") is not True:
        violations.append("must_stop_after_generation must be true")
    if gate.get("assembly_allowed_after_generation") is not False:
        violations.append("assembly_allowed_after_generation must be false")
    if gate.get("production_acceptance_allowed_after_generation") is not False:
        violations.append("production_acceptance_allowed_after_generation must be false")

    return violations
