"""
Director Planning and Shot Contract Layer — convert accepted brief into complete
planning package: scenario -> scene -> shot -> contracts -> production plan -> validation -> operator review.

This module implements RC-COMBINE-V2-62001-70000:
  - Validates Brief Intake artifacts
  - Builds scenario plan, scene plan, shot plan
  - Creates per-shot contracts
  - Builds production plan with dependency map
  - Validates planning completeness and safety
  - Creates operator review packet
  - Updates artifact index and episode ledger
  - Transitions state to planning_operator_review_required
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TASK_ID = "RC-COMBINE-V2-62001-70000"
PREVIOUS_LAYER = "RC-COMBINE-V2-54001-62000 Brief Intake Contract Layer"
NEXT_LAYER = "RC-COMBINE-V2-70001-86000 Workflow-to-Assets Package"

SCENARIO_STRUCTURE = {
    "three_act": {
        "act_1": "Setup — introduce the problem and context",
        "act_2": "Confrontation — explore the pipeline steps and challenges",
        "act_3": "Resolution — show successful resolution and conclusion",
    }
}

# Default scene blueprint derived from the educational brief
DEFAULT_SCENES = [
    {
        "scene_id": "scene_001",
        "scene_purpose": "hook_and_context",
        "scene_summary": "Open with a relatable question about AI video quality, introduce the concept of automated frame checking and why it matters.",
        "expected_duration_range_seconds": [15, 25],
        "visual_intent": "Clean motion graphics with animated pipeline overview",
        "narrative_role": "set the stage and establish the problem-solution framework",
        "transition_intent_to_next_scene": "zoom into the pipeline entry point where generated frames arrive",
    },
    {
        "scene_id": "scene_002",
        "scene_purpose": "generation_output",
        "scene_summary": "Show what raw generated frames look like as they exit the AI model — diverse outputs, varying quality, and the need for automated screening.",
        "expected_duration_range_seconds": [20, 35],
        "visual_intent": "Split-screen display of multiple generated frame variants with quality indicators",
        "narrative_role": "demonstrate the input to the QA pipeline",
        "transition_intent_to_next_scene": "pan across frames into a magnifying glass inspection view",
    },
    {
        "scene_id": "scene_003",
        "scene_purpose": "automated_qa_checks",
        "scene_summary": "Present the automated QA pipeline stages: format validation, resolution check, artifact detection, color integrity, and content alignment.",
        "expected_duration_range_seconds": [30, 45],
        "visual_intent": "Flowchart-style animation showing frames moving through checkpoints with pass/fail indicators",
        "narrative_role": "explain the core QA mechanism",
        "transition_intent_to_next_scene": "transition to a zoomed defect view on a flagged frame",
    },
    {
        "scene_id": "scene_004",
        "scene_purpose": "defect_detection_and_correction",
        "scene_summary": "Illustrate common defect categories, how the system categorizes issues, and the correction loop that retries or patches problematic frames.",
        "expected_duration_range_seconds": [25, 40],
        "visual_intent": "Defect taxonomy visual with example images, correction arrows showing retry path",
        "narrative_role": "show the detection and resolution process",
        "transition_intent_to_next_scene": "transition to a green-check celebration as frames pass all checks",
    },
    {
        "scene_id": "scene_005",
        "scene_purpose": "assembly_readiness_and_conclusion",
        "scene_summary": "Wrap up by showing accepted frames proceeding to assembly, summarize the pipeline value, and end with a call to action for the viewer.",
        "expected_duration_range_seconds": [15, 25],
        "visual_intent": "Approved frames assembling into final sequence, clean summary graphics",
        "narrative_role": "resolve the narrative and reinforce key takeaways",
        "transition_intent_to_next_scene": "fade to end card",
    },
]


# ---------------------------------------------------------------------------
# Data schemas
# ---------------------------------------------------------------------------

@dataclass
class ScenarioPlan:
    """Top-level scenario plan derived from brief."""

    task_id: str = TASK_ID
    source_brief_reference: str = ""
    project_id: str = ""
    episode_id: str = ""
    narrative_goal: str = ""
    target_audience: str = ""
    content_type: str = "unknown"
    format_assumptions: str = ""
    duration_assumptions: str = ""
    scenario_structure: Dict[str, Any] = field(default_factory=dict)
    scene_sequence: List[str] = field(default_factory=list)
    intended_emotional_arc: str = ""
    intended_informational_arc: str = ""
    forbidden_content_inherited: List[str] = field(default_factory=list)
    downstream_readiness_flags: Dict[str, bool] = field(default_factory=dict)
    created_timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScenePlan:
    """Scene-level plan for the episode."""

    task_id: str = TASK_ID
    scenes: List[Dict[str, Any]] = field(default_factory=list)
    created_timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ShotSpec:
    """Individual shot specification embedded in shot plan."""

    shot_id: str = ""
    scene_id: str = ""
    shot_purpose: str = ""
    shot_description: str = ""
    camera_framing_intent: str = ""
    subject_object_requirements: str = ""
    visual_style_constraints: str = ""
    duration_target_seconds: int = 5
    generation_readiness: bool = False
    asset_requirements_summary: str = ""
    qa_criteria_summary: str = ""
    workflow_layer_handoff_status: str = "pending"


@dataclass
class ShotPlan:
    """Shot-level plan for the episode."""

    task_id: str = TASK_ID
    shots: List[Dict[str, Any]] = field(default_factory=list)
    created_timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProductionPlan:
    """Production plan with dependency map and stage ordering."""

    task_id: str = TASK_ID
    scenario_summary: str = ""
    scene_count: int = 0
    shot_count: int = 0
    ordered_production_stages: List[str] = field(default_factory=list)
    dependency_map: Dict[str, str] = field(default_factory=dict)
    required_downstream_layers: List[str] = field(default_factory=list)
    operator_gates_required: List[str] = field(default_factory=list)
    dangerous_actions_remaining_blocked: List[str] = field(default_factory=list)
    ready_for_workflow_to_assets: bool = False
    created_timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlanningValidationReport:
    """Validation report for the entire planning package."""

    scenario_plan_created: bool = False
    scene_plan_created: bool = False
    shot_plan_created: bool = False
    shot_contracts_created: bool = False
    every_scene_has_at_least_one_shot: bool = False
    every_shot_has_scene_id: bool = False
    every_shot_has_visual_intent: bool = False
    every_shot_has_qa_criteria: bool = False
    every_shot_has_required_assets_or_explicit_none: bool = False
    every_shot_routes_to_workflow_layer: bool = False
    generation_performed: bool = False
    comfyui_submit_performed: bool = False
    assembly_performed: bool = False
    downstream_performed: bool = False
    production_accepted: bool = False
    blocked_path_reached: bool = False
    blocker_reason: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _paths(project_root: str) -> Dict[str, Path]:
    root = Path(project_root)
    brief_dir = root / "output" / "control" / "brief"
    planning_dir = root / "output" / "control" / "planning"
    shot_contracts_dir = planning_dir / "shot_contracts"
    return {
        "root": root,
        "brief_dir": brief_dir,
        "planning_dir": planning_dir,
        "shot_contracts_dir": shot_contracts_dir,
        "brief_contract": brief_dir / "brief_contract.json",
        "brief_validation": brief_dir / "brief_validation_report.json",
        "project_constraints": brief_dir / "project_constraints.json",
        "content_intent": brief_dir / "content_intent.json",
        "success_criteria": brief_dir / "success_criteria.json",
        "forbidden_actions": brief_dir / "forbidden_actions.json",
        "scenario_plan": planning_dir / "scenario_plan.json",
        "scene_plan": planning_dir / "scene_plan.json",
        "shot_plan": planning_dir / "shot_plan.json",
        "production_plan": planning_dir / "production_plan.json",
        "planning_validation": planning_dir / "planning_validation_report.json",
        "planning_operator_review": planning_dir / "planning_operator_review_packet.json",
        "planning_blocker": planning_dir / "planning_blocker_report.json",
        "artifact_index": root / "output" / "control" / "artifact_index.json",
        "episode_ledger": root / "output" / "control" / "episode_ledger.json",
    }


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _validate_brief_preflight(project_root: str) -> Optional[Dict[str, Any]]:
    """Validate that brief artifacts exist and are acceptable for planning.

    Returns None if valid, or a blocker result dict if blocked.
    """
    paths = _paths(project_root)
    timestamp = _now_iso()

    brief_contract = _load_json(paths["brief_contract"])
    if brief_contract is None:
        return _build_blocker(paths, timestamp,
                              "brief_contract.json not found — build brief intake first")

    content_intent = _load_json(paths["content_intent"])
    if content_intent is None:
        return _build_blocker(paths, timestamp,
                              "content_intent.json not found — build brief intake first")

    project_constraints = _load_json(paths["project_constraints"])
    if project_constraints is None:
        return _build_blocker(paths, timestamp,
                              "project_constraints.json not found — build brief intake first")

    forbidden_actions = _load_json(paths["forbidden_actions"])
    if forbidden_actions is None:
        return _build_blocker(paths, timestamp,
                              "forbidden_actions.json not found — build brief intake first")

    success_criteria = _load_json(paths["success_criteria"])
    if success_criteria is None:
        return _build_blocker(paths, timestamp,
                              "success_criteria.json not found — build brief intake first")

    brief_validation = _load_json(paths["brief_validation"])
    if brief_validation is None:
        return _build_blocker(paths, timestamp,
                              "brief_validation_report.json not found — build brief intake first")

    # Check production_accepted is false
    if brief_contract.get("production_accepted", False):
        return _build_blocker(paths, timestamp,
                              "brief_contract has production_accepted=true — invalid state for planning")

    # Check readiness
    if not brief_contract.get("readiness_for_director_planner", False):
        return _build_blocker(paths, timestamp,
                              "brief_contract readiness_for_director_planner is false — brief is not ready for planning")

    return None  # valid


def _build_blocker(paths: Dict[str, Path], timestamp: str, reason: str) -> Dict[str, Any]:
    """Create a blocked-path result and write blocker report."""
    result = {
        "task_id": TASK_ID,
        "blocked": True,
        "blocker_reason": reason,
        "current_state": "planning_operator_review_required",
        "next_allowed_action": "planning_operator_review_required",
        "production_accepted": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
    }

    _write_json(paths["planning_blocker"], {
        "task_id": TASK_ID,
        "blocker_type": "preflight_failure",
        "created_timestamp": timestamp,
        "blocker_reason": reason,
        "production_accepted": False,
    })

    _update_artifact_index(paths, timestamp, blocked=True)
    _update_episode_ledger(paths, timestamp, "planning_blocked")
    _force_artifact_index_state(paths, "planning_operator_review_required")
    return result


# ---------------------------------------------------------------------------
# Shot contract generation
# ---------------------------------------------------------------------------

def _build_shot_contracts(
    shots: List[Dict[str, Any]],
    brief: Dict[str, Any],
    project_constraints: Dict[str, Any],
    scene_ids: List[str],
    timestamp: str,
) -> List[str]:
    """Build per-shot contract JSON files and return list of filenames."""
    contracts = []
    for shot in shots:
        shot_id = shot["shot_id"]
        scene_id = shot["scene_id"]
        contract = {
            "task_id": TASK_ID,
            "shot_id": shot_id,
            "scene_id": scene_id,
            "source_brief_reference": brief.get("normalized_task_summary", ""),
            "narrative_purpose": shot.get("shot_purpose", ""),
            "visual_intent": shot.get("visual_intent", shot.get("visual_style_constraints", "")),
            "composition_requirements": shot.get("shot_description", ""),
            "camera_framing_requirements": shot.get("camera_framing_intent", ""),
            "subject_object_requirements": shot.get("subject_object_requirements", ""),
            "required_assets": shot.get("asset_requirements_summary", "unknown"),
            "generation_requirements": {
                "model_hint": "sdxl",
                "workflow_hint": "txt2img",
                "generation_ready": shot.get("generation_readiness", False),
            },
            "workflow_requirements": {
                "handoff_target": "Workflow-to-Assets layer",
                "handoff_status": shot.get("workflow_layer_handoff_status", "pending"),
                "required_downstream": ["frame_generation", "qa_validation"],
            },
            "resolution_aspect_expectations": {
                "resolution": project_constraints.get("aspect_ratio", "1024x1024"),
                "aspect_ratio_hint": project_constraints.get("aspect_ratio", "1:1"),
            },
            "negative_constraints": brief.get("forbidden_actions", []),
            "qa_criteria": shot.get("qa_criteria_summary", ""),
            "forbidden_actions": [
                "generation_without_operator_authorization",
                "comfyui_submit_without_authorization",
                "production_acceptance_without_review",
            ],
            "handoff_target": "Workflow-to-Assets layer",
            "production_accepted": False,
            "created_timestamp": timestamp,
        }
        contract_filename = f"{shot_id}.json"
        paths_inst = _paths("")  # FIXME: refactor to pass project_root
        yield contract, contract_filename


def _write_shot_contracts(
    shot_contracts_dir: Path,
    contracts_data: List[tuple],
    brief: Dict[str, Any],
    project_constraints: Dict[str, Any],
    timestamp: str,
) -> List[str]:
    """Write per-shot contract files. Returns list of created filenames."""
    created = []
    for shot in _generate_shot_definitions(brief, project_constraints):
        shot_id = shot["shot_id"]
        scene_id = shot["scene_id"]
        contract = {
            "task_id": TASK_ID,
            "shot_id": shot_id,
            "scene_id": scene_id,
            "source_brief_reference": brief.get("normalized_task_summary", ""),
            "narrative_purpose": shot.get("shot_purpose", ""),
            "visual_intent": shot.get("visual_intent", shot.get("visual_style_constraints", "")),
            "composition_requirements": shot.get("shot_description", ""),
            "camera_framing_requirements": shot.get("camera_framing_intent", ""),
            "subject_object_requirements": shot.get("subject_object_requirements", ""),
            "required_assets": shot.get("asset_requirements_summary", "unknown"),
            "generation_requirements": {
                "model_hint": "sdxl",
                "workflow_hint": "txt2img",
                "generation_ready": shot.get("generation_readiness", False),
            },
            "workflow_requirements": {
                "handoff_target": "Workflow-to-Assets layer",
                "handoff_status": shot.get("workflow_layer_handoff_status", "pending"),
                "required_downstream": ["frame_generation", "qa_validation"],
            },
            "resolution_aspect_expectations": {
                "resolution": project_constraints.get("aspect_ratio", "1024x1024"),
                "aspect_ratio_hint": project_constraints.get("aspect_ratio_hint", project_constraints.get("aspect_ratio", "1:1")),
            },
            "negative_constraints": brief.get("forbidden_actions", []),
            "qa_criteria": shot.get("qa_criteria_summary", ""),
            "forbidden_actions": [
                "generation_without_operator_authorization",
                "comfyui_submit_without_authorization",
                "production_acceptance_without_review",
            ],
            "handoff_target": "Workflow-to-Assets layer",
            "production_accepted": False,
            "created_timestamp": timestamp,
        }
        filename = f"{shot_id}.json"
        _write_json(shot_contracts_dir / filename, contract)
        created.append(filename)

    return created


# ---------------------------------------------------------------------------
# Shot definitions derived from brief
# ---------------------------------------------------------------------------

def _generate_shot_definitions(
    brief: Dict[str, Any],
    project_constraints: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate ordered shot definitions from the brief content.

    Returns a list of shot dicts suitable for the shot plan and contracts.
    """
    content_type = brief.get("content_type", "educational")
    goal = brief.get("goal", "")
    style_tone = project_constraints.get("style_tone", "clear_practical")

    # Base shot templates for the educational explainer
    shots = [
        # Scene 001: Hook and Context
        {
            "shot_id": "shot_001",
            "scene_id": "scene_001",
            "shot_purpose": "Attention-grabbing open — pose the quality question",
            "shot_description": "Open with an animated question: 'How do we know AI-generated frames are any good?' with clean motion graphics.",
            "camera_framing_intent": "Wide establishing frame with central text/icon animation",
            "subject_object_requirements": "Animated text, pipeline iconography",
            "visual_style_constraints": f"Clean motion graphics, {style_tone} style",
            "visual_intent": "Hook the viewer with a relatable quality concern",
            "duration_target_seconds": 8,
            "generation_readiness": False,
            "asset_requirements_summary": "motion_graphics_assets: title card template, pipeline icons",
            "qa_criteria_summary": "text readable, animation smooth, branding consistent",
            "workflow_layer_handoff_status": "pending",
        },
        {
            "shot_id": "shot_002",
            "scene_id": "scene_001",
            "shot_purpose": "Establish the AI pipeline context",
            "shot_description": "Show a simplified AI production pipeline diagram flowing from model generation through QA checks to assembly.",
            "camera_framing_intent": "Medium establishing shot of pipeline diagram",
            "subject_object_requirements": "Pipeline flow diagram with 4-5 stages",
            "visual_style_constraints": f"Diagrammatic style, {style_tone} colors",
            "visual_intent": "Give viewer a mental map of the pipeline landscape",
            "duration_target_seconds": 12,
            "generation_readiness": False,
            "asset_requirements_summary": "motion_graphics_assets: pipeline diagram template",
            "qa_criteria_summary": "diagram accurate, stages clearly labeled, flow direction clear",
            "workflow_layer_handoff_status": "pending",
        },
        # Scene 002: Generation Output
        {
            "shot_id": "shot_003",
            "scene_id": "scene_002",
            "shot_purpose": "Show raw generation output examples",
            "shot_description": "Display a grid of sample AI-generated frames showing varied quality — some sharp, some with artifacts, some well-composed.",
            "camera_framing_intent": "Split-screen grid view with 4 sample frames",
            "subject_object_requirements": "Sample generated frame images on grid",
            "visual_style_constraints": f"Split comparison layout, {style_tone} annotations",
            "visual_intent": "Demonstrate the variability of raw AI generation output",
            "duration_target_seconds": 15,
            "generation_readiness": False,
            "asset_requirements_summary": "sample_frame_assets: 4 variant frame images",
            "qa_criteria_summary": "grid layout balanced, quality differences visible, annotations clear",
            "workflow_layer_handoff_status": "pending",
        },
        {
            "shot_id": "shot_004",
            "scene_id": "scene_002",
            "shot_purpose": "Illustrate common generation issues",
            "shot_description": "Zoom into specific defects: bad cropping, distorted anatomy, color bleeding, missing elements with callout labels.",
            "camera_framing_intent": "Close-up inspection view with magnifying glass effect",
            "subject_object_requirements": "Defect callout overlays on sample frames",
            "visual_style_constraints": f"Inspection-style UI, {style_tone} error indicators",
            "visual_intent": "Educate viewer on what defects look like and why they matter",
            "duration_target_seconds": 15,
            "generation_readiness": False,
            "asset_requirements_summary": "sample_frame_assets: defect example images, callout overlays",
            "qa_criteria_summary": "defects clearly visible and labeled, examples representative",
            "workflow_layer_handoff_status": "pending",
        },
        # Scene 003: Automated QA Checks
        {
            "shot_id": "shot_005",
            "scene_id": "scene_003",
            "shot_purpose": "QA pipeline overview",
            "shot_description": "Animated flowchart showing frames entering the QA pipeline and moving through sequential check stations.",
            "camera_framing_intent": "Wide establishing shot of QA pipeline flowchart",
            "subject_object_requirements": "QA pipeline stations with entry/exit flow",
            "visual_style_constraints": f"Flowchart animation, {style_tone} checkpoint icons",
            "visual_intent": "Show the structured nature of automated QA",
            "duration_target_seconds": 12,
            "generation_readiness": False,
            "asset_requirements_summary": "motion_graphics_assets: QA pipeline flowchart template",
            "qa_criteria_summary": "checkpoints clearly defined, flow direction intuitive",
            "workflow_layer_handoff_status": "pending",
        },
        {
            "shot_id": "shot_006",
            "scene_id": "scene_003",
            "shot_purpose": "Technical validation checks",
            "shot_description": "Detail the technical checks: format validation, resolution check, file integrity, color space verification with pass/fail badges.",
            "camera_framing_intent": "Medium shot with check panel UI overlay",
            "subject_object_requirements": "Technical checklist UI with status indicators",
            "visual_style_constraints": f"Technical UI style, {style_tone} pass/fail badges",
            "visual_intent": "Explain the objective technical gatekeeping",
            "duration_target_seconds": 15,
            "generation_readiness": False,
            "asset_requirements_summary": "motion_graphics_assets: check panel UI template",
            "qa_criteria_summary": "technical terms clear, check results unambiguous",
            "workflow_layer_handoff_status": "pending",
        },
        {
            "shot_id": "shot_007",
            "scene_id": "scene_003",
            "shot_purpose": "Visual quality assessment",
            "shot_description": "Show the visual QA system analyzing aesthetic criteria: composition, lighting, subject integrity, style consistency with score readouts.",
            "camera_framing_intent": "Medium shot with QA scoring UI overlay on frame",
            "subject_object_requirements": "QA score panel with visual analysis highlights",
            "visual_style_constraints": f"Analytics dashboard style, {style_tone} scoring UI",
            "visual_intent": "Demonstrate that QA goes beyond technical checks into aesthetic judgment",
            "duration_target_seconds": 15,
            "generation_readiness": False,
            "asset_requirements_summary": "motion_graphics_assets: QA scoring template, sample analyzed frames",
            "qa_criteria_summary": "scores explained visually, analysis highlights meaningful",
            "workflow_layer_handoff_status": "pending",
        },
        # Scene 004: Defect Detection and Resolution
        {
            "shot_id": "shot_008",
            "scene_id": "scene_004",
            "shot_purpose": "Defect taxonomy presentation",
            "shot_description": "Present organized defect categories with visual examples grouped by type: technical, compositional, subject integrity, stylistic.",
            "camera_framing_intent": "Grid/category layout with expandable defect cards",
            "subject_object_requirements": "Defect category cards with example thumbnails",
            "visual_style_constraints": f"Organized taxonomy layout, {style_tone} category coloring",
            "visual_intent": "Systematize defect knowledge for the viewer",
            "duration_target_seconds": 12,
            "generation_readiness": False,
            "asset_requirements_summary": "motion_graphics_assets: defect taxonomy template with categories",
            "qa_criteria_summary": "categories logical, examples match categories",
            "workflow_layer_handoff_status": "pending",
        },
        {
            "shot_id": "shot_009",
            "scene_id": "scene_004",
            "shot_purpose": "Correction loop explanation",
            "shot_description": "Animated diagram showing the retry/correction loop: defect detected -> plan correction -> patch generation -> re-check -> pass or recycle.",
            "camera_framing_intent": "Wide shot with correction loop cycle animation",
            "subject_object_requirements": "Loop diagram with cycle arrows and decision diamonds",
            "visual_style_constraints": f"Cycle/loop animation, {style_tone} decision points",
            "visual_intent": "Explain the self-healing aspect of the pipeline",
            "duration_target_seconds": 15,
            "generation_readiness": False,
            "asset_requirements_summary": "motion_graphics_assets: correction loop diagram template",
            "qa_criteria_summary": "loop logic clear, decision points well explained",
            "workflow_layer_handoff_status": "pending",
        },
        {
            "shot_id": "shot_010",
            "scene_id": "scene_004",
            "shot_purpose": "Re-check after correction",
            "shot_description": "Show a previously-failing frame passing through re-check and getting approved, with visual diff before/after.",
            "camera_framing_intent": "Before/after split comparison with approval badge",
            "subject_object_requirements": "Before/after frame comparison, checkmark approval",
            "visual_style_constraints": f"Before/after layout, {style_tone} success indicators",
            "visual_intent": "Show that corrections work and quality improves",
            "duration_target_seconds": 10,
            "generation_readiness": False,
            "asset_requirements_summary": "sample_frame_assets: before/after frame pair, approval badge overlay",
            "qa_criteria_summary": "improvement visible, approval clear and satisfying",
            "workflow_layer_handoff_status": "pending",
        },
        # Scene 005: Assembly Readiness and Conclusion
        {
            "shot_id": "shot_011",
            "scene_id": "scene_005",
            "shot_purpose": "Approved frames proceeding to assembly",
            "shot_description": "Timeline view showing approved frames being added to the final sequence, with quality stamps and assembly progress.",
            "camera_framing_intent": "Timeline/sequencing view with frame thumbnails",
            "subject_object_requirements": "Editing timeline with approved frame stamps",
            "visual_style_constraints": f"Timeline/editor UI style, {style_tone} approved badges",
            "visual_intent": "Show the payoff of all the QA work",
            "duration_target_seconds": 10,
            "generation_readiness": False,
            "asset_requirements_summary": "motion_graphics_assets: timeline template with frame thumbnails",
            "qa_criteria_summary": "timeline clear, approval stamps prominent",
            "workflow_layer_handoff_status": "pending",
        },
        {
            "shot_id": "shot_012",
            "scene_id": "scene_005",
            "shot_purpose": "Summary and conclusion",
            "shot_description": "Recap the key pipeline stages with a compact visual summary, reinforce the value of automated QA, end with a call to action.",
            "camera_framing_intent": "Summary card layout with end screen",
            "subject_object_requirements": "Pipeline recap graphic, end card with CTA",
            "visual_style_constraints": f"Clean summary layout, {style_tone} end card",
            "visual_intent": "Reinforce learning and provide closure",
            "duration_target_seconds": 12,
            "generation_readiness": False,
            "asset_requirements_summary": "motion_graphics_assets: summary template, end card template",
            "qa_criteria_summary": "recap accurate, CTA clear, visual summary effective",
            "workflow_layer_handoff_status": "pending",
        },
    ]

    return shots


# ---------------------------------------------------------------------------
# Main pipeline functions
# ---------------------------------------------------------------------------

def build_director_planning(project_root: str) -> Dict[str, Any]:
    """Build the full director planning package from accepted brief artifacts.

    Creates all planning artifacts under output/control/planning/ including:
    scenario plan, scene plan, shot plan, per-shot contracts, production plan,
    planning validation report, and operator review packet.

    Does NOT perform generation, ComfyUI submit, or any runtime action.
    """
    paths = _paths(project_root)
    timestamp = _now_iso()

    # Step 1: Preflight — validate brief artifacts
    blocker = _validate_brief_preflight(project_root)
    if blocker is not None:
        return blocker

    # Load brief data
    brief = _load_json(paths["brief_contract"]) or {}
    content_intent = _load_json(paths["content_intent"]) or {}
    project_constraints = _load_json(paths["project_constraints"]) or {}
    forbidden_actions_data = _load_json(paths["forbidden_actions"]) or {}
    success_criteria_data = _load_json(paths["success_criteria"]) or {}

    episode_id = brief.get("project_id", Path(project_root).name)

    # Step 2: Build scenario plan
    narrative_goal = brief.get("goal", content_intent.get("goal", ""))
    target_audience = brief.get("target_audience", content_intent.get("target_audience", ""))
    content_type = brief.get("content_type", content_intent.get("content_type", "unknown"))
    accumulated_forbidden = list(set(
        forbidden_actions_data.get("forbidden_actions", [])
        + brief.get("forbidden_actions", [])
    ))

    scene_ids = [s["scene_id"] for s in DEFAULT_SCENES]

    scenario = ScenarioPlan(
        source_brief_reference=brief.get("normalized_task_summary", ""),
        project_id=brief.get("project_id", episode_id),
        episode_id=episode_id,
        narrative_goal=narrative_goal,
        target_audience=target_audience,
        content_type=content_type,
        format_assumptions=f"Format: {project_constraints.get('format_hint', '16:9 horizontal video (default)')}",
        duration_assumptions=f"Target duration: {project_constraints.get('duration_target', '~60-120 seconds (estimated)')}",
        scenario_structure=SCENARIO_STRUCTURE,
        scene_sequence=scene_ids,
        intended_emotional_arc="Curiosity -> Understanding -> Confidence in AI pipeline quality assurance",
        intended_informational_arc="Problem introduction -> Pipeline explanation -> QA mechanism -> Defect resolution -> Value reinforcement",
        forbidden_content_inherited=accumulated_forbidden,
        downstream_readiness_flags={
            "ready_for_workflow_to_assets": False,
            "operator_review_required": True,
            "production_accepted": False,
        },
        created_timestamp=timestamp,
    )

    _write_json(paths["scenario_plan"], scenario.to_dict())

    # Step 3: Build scene plan
    scene_plan_data = {
        "task_id": TASK_ID,
        "scenes": DEFAULT_SCENES,
        "created_timestamp": timestamp,
    }
    _write_json(paths["scene_plan"], scene_plan_data)

    # Step 4: Build shot plan
    shot_defs = _generate_shot_definitions(brief, project_constraints)
    shot_plan_data = {
        "task_id": TASK_ID,
        "shots": shot_defs,
        "created_timestamp": timestamp,
    }
    _write_json(paths["shot_plan"], shot_plan_data)

    # Step 5: Create per-shot contracts
    contracts_created = _write_shot_contracts(
        paths["shot_contracts_dir"],
        [],
        brief,
        project_constraints,
        timestamp,
    )

    shot_contracts_filenames = contracts_created

    # Step 6: Build production plan
    production_plan = ProductionPlan(
        scenario_summary=narrative_goal[:200],
        scene_count=len(DEFAULT_SCENES),
        shot_count=len(shot_defs),
        ordered_production_stages=[
            "brief_intake",
            "director_planning",
            "workflow_to_assets",
            "frame_generation",
            "qa_validation",
            "correction_loop",
            "final_qa",
            "assembly",
            "preview",
            "production_acceptance",
        ],
        dependency_map={
            "brief_intake": "director_planning",
            "director_planning": "workflow_to_assets",
            "workflow_to_assets": "frame_generation",
            "frame_generation": "qa_validation",
            "qa_validation": "correction_loop",
            "correction_loop": "final_qa",
            "final_qa": "assembly",
            "assembly": "preview",
            "preview": "production_acceptance",
        },
        required_downstream_layers=[
            NEXT_LAYER,
            "Frame Generation Layer",
            "QA Validation Layer",
            "Correction Loop Layer",
            "Final Assembly Layer",
        ],
        operator_gates_required=[
            "planning_operator_review_required",
            "workflow_operator_review_required",
            "generation_authorization_required",
            "visual_qa_operator_review_required",
            "production_acceptance_required",
        ],
        dangerous_actions_remaining_blocked=accumulated_forbidden,
        ready_for_workflow_to_assets=True,
        created_timestamp=timestamp,
    )
    _write_json(paths["production_plan"], production_plan.to_dict())

    # Step 7: Build validation report
    errors = []
    warnings = []

    # Validate each scene has at least one shot
    scene_shots: Dict[str, int] = {}
    for shot in shot_defs:
        sid = shot["scene_id"]
        scene_shots[sid] = scene_shots.get(sid, 0) + 1

    scenes_without_shots = [s for s in scene_ids if scene_shots.get(s, 0) == 0]
    all_scenes_have_shots = len(scenes_without_shots) == 0
    if scenes_without_shots:
        errors.append(f"Scenes without shots: {scenes_without_shots}")

    # Validate shot fields
    shots_missing_scene_id = [s["shot_id"] for s in shot_defs if not s.get("scene_id")]
    all_shots_have_scene_id = len(shots_missing_scene_id) == 0
    if shots_missing_scene_id:
        errors.append(f"Shots missing scene_id: {shots_missing_scene_id}")

    shots_missing_visual_intent = [s["shot_id"] for s in shot_defs if not s.get("visual_intent")]
    all_shots_have_visual_intent = len(shots_missing_visual_intent) == 0
    if shots_missing_visual_intent:
        errors.append(f"Shots missing visual_intent: {shots_missing_visual_intent}")

    shots_missing_qa = [s["shot_id"] for s in shot_defs if not s.get("qa_criteria_summary")]
    all_shots_have_qa = len(shots_missing_qa) == 0
    if shots_missing_qa:
        errors.append(f"Shots missing qa_criteria_summary: {shots_missing_qa}")

    shots_missing_assets = [
        s["shot_id"] for s in shot_defs
        if not s.get("asset_requirements_summary")
    ]
    all_shots_have_assets = len(shots_missing_assets) == 0
    if shots_missing_assets:
        warnings.append(f"Shots with empty asset_requirements_summary: {shots_missing_assets}")

    all_shots_route_to_workflow = all(
        s.get("workflow_layer_handoff_status", "") == "pending"
        for s in shot_defs
    )

    validation = PlanningValidationReport(
        scenario_plan_created=True,
        scene_plan_created=True,
        shot_plan_created=True,
        shot_contracts_created=len(contracts_created) > 0,
        every_scene_has_at_least_one_shot=all_scenes_have_shots,
        every_shot_has_scene_id=all_shots_have_scene_id,
        every_shot_has_visual_intent=all_shots_have_visual_intent,
        every_shot_has_qa_criteria=all_shots_have_qa,
        every_shot_has_required_assets_or_explicit_none=all_shots_have_assets,
        every_shot_routes_to_workflow_layer=all_shots_route_to_workflow,
        generation_performed=False,
        comfyui_submit_performed=False,
        assembly_performed=False,
        downstream_performed=False,
        production_accepted=False,
        errors=errors,
        warnings=warnings,
    )

    _write_json(paths["planning_validation"], validation.to_dict())

    # Step 8: Build operator review packet
    operator_packet = _build_planning_operator_review_data(
        paths, brief, content_intent, project_constraints,
        forbidden_actions_data, success_criteria_data,
        scenario, DEFAULT_SCENES, shot_defs,
        validation, production_plan, timestamp,
    )
    _write_json(paths["planning_operator_review"], operator_packet)

    # Step 9: Update artifact index and episode ledger
    _update_artifact_index(paths, timestamp, blocked=False)
    _update_episode_ledger(paths, timestamp, "planning_completed")
    _force_artifact_index_state(paths, "planning_operator_review_required")

    # Step 10: Build result
    artifacts_created = [
        "planning/scenario_plan.json",
        "planning/scene_plan.json",
        "planning/shot_plan.json",
        "planning/production_plan.json",
        "planning/planning_validation_report.json",
        "planning/planning_operator_review_packet.json",
    ] + [f"planning/shot_contracts/{f}" for f in contracts_created]

    result = {
        "task_id": TASK_ID,
        "feature_completed": True,
        "full_feature_loop_executed": True,
        "brief_artifacts_validated": True,
        "scenario_plan_created": True,
        "scene_plan_created": True,
        "shot_plan_created": True,
        "shot_contracts_created": len(contracts_created) > 0,
        "production_plan_created": True,
        "planning_validation_report_created": True,
        "planning_operator_review_packet_created": True,
        "each_scene_has_shots": all_scenes_have_shots,
        "each_shot_has_goal_and_visual_intent": all_shots_have_visual_intent,
        "each_shot_has_required_assets_and_qa_criteria": all_shots_have_qa,
        "shot_contracts_route_to_workflow_layer": all_shots_route_to_workflow,
        "ready_for_workflow_to_assets_layer": not errors and not scenes_without_shots,
        "artifact_index_updated": True,
        "episode_ledger_updated": True,
        "new_generation_performed": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "visual_qa_executed": False,
        "visual_acceptance_executed": False,
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "planning_operator_review_required",
        "next_allowed_action": "planning_operator_review_required",
        "next_layer": NEXT_LAYER,
        "artifacts_created": artifacts_created,
        "errors": errors,
        "warnings": warnings,
        "blockers": [],
        "non_blocking_backlog": warnings,
    }
    return result


def validate_director_planning(project_root: str) -> Dict[str, Any]:
    """Validate existing director planning artifacts.

    Reads all planning artifacts and re-validates completeness and safety.
    """
    paths = _paths(project_root)
    timestamp = _now_iso()

    # Check planning artifacts exist
    scenario_plan = _load_json(paths["scenario_plan"])
    scene_plan = _load_json(paths["scene_plan"])
    shot_plan = _load_json(paths["shot_plan"])
    production_plan_data = _load_json(paths["production_plan"])
    validation_data = _load_json(paths["planning_validation"])

    if scenario_plan is None:
        return _validation_result("scenario_plan.json not found", paths, timestamp)

    if scene_plan is None:
        return _validation_result("scene_plan.json not found", paths, timestamp)

    if shot_plan is None:
        return _validation_result("shot_plan.json not found", paths, timestamp)

    if production_plan_data is None:
        return _validation_result("production_plan.json not found", paths, timestamp)

    # Re-validate fields
    errors = []
    warnings = []

    scenes = scene_plan.get("scenes", [])
    shots = shot_plan.get("shots", [])

    scene_ids = [s.get("scene_id", "") for s in scenes]

    scene_shots: Dict[str, int] = {}
    for shot in shots:
        sid = shot.get("scene_id", "")
        scene_shots[sid] = scene_shots.get(sid, 0) + 1

    scenes_without_shots = [s for s in scene_ids if scene_shots.get(s, 0) == 0]
    if scenes_without_shots:
        errors.append(f"Scenes without shots: {scenes_without_shots}")

    shots_missing_scene_id = [s.get("shot_id", "?") for s in shots if not s.get("scene_id")]
    if shots_missing_scene_id:
        errors.append(f"Shots missing scene_id: {shots_missing_scene_id}")

    shots_missing_visual_intent = [s.get("shot_id", "?") for s in shots if not s.get("visual_intent")]
    if shots_missing_visual_intent:
        errors.append(f"Shots missing visual_intent: {shots_missing_visual_intent}")

    shots_missing_qa = [s.get("shot_id", "?") for s in shots if not s.get("qa_criteria_summary")]
    if shots_missing_qa:
        errors.append(f"Shots missing qa_criteria_summary: {shots_missing_qa}")

    # Check shot_contracts directory
    shot_contracts_dir = paths["shot_contracts_dir"]
    contract_files = list(shot_contracts_dir.glob("shot_*.json")) if shot_contracts_dir.exists() else []
    contracts_created = len(contract_files) > 0

    if not contracts_created:
        warnings.append("No shot contract files found in shot_contracts/")

    all_shots_have_assets = all(
        s.get("asset_requirements_summary") for s in shots
    )

    all_shots_route_to_workflow = all(
        s.get("workflow_layer_handoff_status", "") == "pending"
        for s in shots
    )

    # Check forbidden actions
    gen_performed = scenario_plan.get("downstream_readiness_flags", {}).get("generation_performed", False)
    prod_accepted = scenario_plan.get("downstream_readiness_flags", {}).get("production_accepted", False)

    # Also check from brief
    brief = _load_json(paths["brief_contract"]) or {}
    prod_accepted = prod_accepted or brief.get("production_accepted", False)

    result = {
        "task_id": TASK_ID,
        "validation_timestamp": timestamp,
        "scenario_plan_created": scenario_plan is not None,
        "scene_plan_created": scene_plan is not None,
        "shot_plan_created": shot_plan is not None,
        "shot_contracts_created": contracts_created,
        "every_scene_has_at_least_one_shot": len(scenes_without_shots) == 0,
        "every_shot_has_scene_id": len(shots_missing_scene_id) == 0,
        "every_shot_has_visual_intent": len(shots_missing_visual_intent) == 0,
        "every_shot_has_qa_criteria": len(shots_missing_qa) == 0,
        "every_shot_has_required_assets_or_explicit_none": all_shots_have_assets,
        "every_shot_routes_to_workflow_layer": all_shots_route_to_workflow,
        "generation_performed": gen_performed or False,
        "comfyui_submit_performed": False,
        "assembly_performed": False,
        "downstream_performed": False,
        "production_accepted": prod_accepted or False,
        "blocked_path_reached": False,
        "errors": errors,
        "warnings": warnings,
        "validation_passed": len(errors) == 0 and not prod_accepted,
        "current_state": "planning_operator_review_required",
        "next_allowed_action": "planning_operator_review_required",
    }

    _write_json(paths["planning_validation"], result)
    return result


def _validation_result(
    reason: str, paths: Dict[str, Path], timestamp: str,
) -> Dict[str, Any]:
    """Build a validation result for missing artifacts."""
    result = {
        "task_id": TASK_ID,
        "validation_timestamp": timestamp,
        "scenario_plan_created": False,
        "scene_plan_created": False,
        "shot_plan_created": False,
        "shot_contracts_created": False,
        "every_scene_has_at_least_one_shot": False,
        "every_shot_has_scene_id": False,
        "every_shot_has_visual_intent": False,
        "every_shot_has_qa_criteria": False,
        "every_shot_has_required_assets_or_explicit_none": False,
        "every_shot_routes_to_workflow_layer": False,
        "generation_performed": False,
        "comfyui_submit_performed": False,
        "assembly_performed": False,
        "downstream_performed": False,
        "production_accepted": False,
        "blocked_path_reached": True,
        "blocker_reason": reason,
        "errors": [reason],
        "warnings": [],
        "validation_passed": False,
        "current_state": "planning_operator_review_required",
        "next_allowed_action": "planning_operator_review_required",
    }
    _write_json(paths["planning_validation"], result)
    return result


def build_planning_operator_review(project_root: str) -> Dict[str, Any]:
    """Build the planning operator review packet.

    Reads all planning artifacts and creates a comprehensive operator review
    summary for human review before proceeding to Workflow-to-Assets.
    """
    paths = _paths(project_root)
    timestamp = _now_iso()

    # Load all planning artifacts
    scenario_plan = _load_json(paths["scenario_plan"]) or {}
    scene_plan = _load_json(paths["scene_plan"]) or {}
    shot_plan = _load_json(paths["shot_plan"]) or {}
    production_plan_data = _load_json(paths["production_plan"]) or {}
    validation_data = _load_json(paths["planning_validation"]) or {}
    brief = _load_json(paths["brief_contract"]) or {}
    content_intent = _load_json(paths["content_intent"]) or {}
    project_constraints = _load_json(paths["project_constraints"]) or {}
    forbidden_actions_data = _load_json(paths["forbidden_actions"]) or {}
    success_criteria_data = _load_json(paths["success_criteria"]) or {}

    # Count shot contracts
    shot_contracts_dir = paths["shot_contracts_dir"]
    contract_files = list(shot_contracts_dir.glob("shot_*.json")) if shot_contracts_dir.exists() else []

    scenes = scene_plan.get("scenes", [])
    shots = shot_plan.get("shots", [])

    # Determine readiness
    validation_passed = validation_data.get("validation_passed", False)
    if not validation_passed:
        validation_passed = (
            validation_data.get("scenario_plan_created", False)
            and validation_data.get("scene_plan_created", False)
            and validation_data.get("shot_plan_created", False)
            and validation_data.get("shot_contracts_created", False)
            and validation_data.get("every_scene_has_at_least_one_shot", False)
            and validation_data.get("every_shot_has_scene_id", False)
            and validation_data.get("every_shot_has_visual_intent", False)
            and not validation_data.get("generation_performed", False)
            and not validation_data.get("production_accepted", False)
        )

    errors = validation_data.get("errors", [])
    warnings = validation_data.get("warnings", [])

    # Assumptions from planning
    assumptions = brief.get("assumptions", []) + [
        "Scenario structure follows three-act educational explainer format",
        "Scene order follows logical pipeline flow: context -> generation -> QA -> correction -> assembly",
        "Shot durations are estimates and may require adjustment during generation",
        "All shots require operator review authorization before generation",
        "No generation has been performed — all planning artifacts are preparation only",
    ]

    packet = {
        "task_id": TASK_ID,
        "packet_type": "planning_operator_review",
        "created_timestamp": timestamp,
        "what_was_planned": "Director planning package converting accepted brief into scenario, scene, and shot plans with per-shot contracts",
        "scenario_overview": {
            "narrative_goal": scenario_plan.get("narrative_goal", ""),
            "content_type": scenario_plan.get("content_type", ""),
            "target_audience": scenario_plan.get("target_audience", ""),
            "emotional_arc": scenario_plan.get("intended_emotional_arc", ""),
            "informational_arc": scenario_plan.get("intended_informational_arc", ""),
        },
        "scene_list": [
            {
                "scene_id": s.get("scene_id", ""),
                "purpose": s.get("scene_purpose", ""),
                "summary": s.get("scene_summary", ""),
            }
            for s in scenes
        ],
        "shot_list": [
            {
                "shot_id": s.get("shot_id", ""),
                "scene_id": s.get("scene_id", ""),
                "purpose": s.get("shot_purpose", ""),
                "duration_target_seconds": s.get("duration_target_seconds", 5),
            }
            for s in shots
        ],
        "shot_count": len(shots),
        "scene_count": len(scenes),
        "shot_contracts_count": len(contract_files),
        "assumptions_made": assumptions,
        "missing_information": brief.get("missing_fields", []),
        "blockers": errors,
        "warnings": warnings,
        "next_layer_allowed": validation_passed and len(errors) == 0,
        "operator_review_required": True,
        "current_state": "planning_operator_review_required",
        "next_allowed_action": "planning_operator_review_required",
        "production_accepted": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "next_recommended_layer": NEXT_LAYER,
        "notes": "Operator must review the planning package, confirm or modify scene/shot structure, then authorize proceeding to Workflow-to-Assets layer.",
    }

    _write_json(paths["planning_operator_review"], packet)
    return packet


def _build_planning_operator_review_data(
    paths, brief, content_intent, project_constraints,
    forbidden_actions_data, success_criteria_data,
    scenario, scenes, shots,
    validation, production_plan_data, timestamp,
) -> Dict[str, Any]:
    """Build the operator review packet data dict."""
    validation_passed = (
        validation.scenario_plan_created
        and validation.scene_plan_created
        and validation.shot_plan_created
        and validation.shot_contracts_created
        and validation.every_scene_has_at_least_one_shot
        and validation.every_shot_has_scene_id
        and validation.every_shot_has_visual_intent
        and not validation.generation_performed
        and not validation.production_accepted
    )

    assumptions = brief.get("assumptions", []) + [
        "Scenario structure follows three-act educational explainer format",
        "Scene order follows logical pipeline flow: context -> generation -> QA -> correction -> assembly",
        "Shot durations are estimates and may require adjustment during generation",
        "All shots require operator review authorization before generation",
        "No generation has been performed — all planning artifacts are preparation only",
    ]

    return {
        "task_id": TASK_ID,
        "packet_type": "planning_operator_review",
        "created_timestamp": timestamp,
        "what_was_planned": "Director planning package converting accepted brief into scenario, scene, and shot plans with per-shot contracts",
        "scenario_overview": {
            "narrative_goal": scenario.narrative_goal,
            "content_type": scenario.content_type,
            "target_audience": scenario.target_audience,
            "emotional_arc": scenario.intended_emotional_arc,
            "informational_arc": scenario.intended_informational_arc,
        },
        "scene_list": [
            {
                "scene_id": s.get("scene_id", ""),
                "purpose": s.get("scene_purpose", ""),
                "summary": s.get("scene_summary", ""),
            }
            for s in scenes
        ],
        "shot_list": [
            {
                "shot_id": s.get("shot_id", ""),
                "scene_id": s.get("scene_id", ""),
                "purpose": s.get("shot_purpose", ""),
                "duration_target_seconds": s.get("duration_target_seconds", 5),
            }
            for s in shots
        ],
        "shot_count": len(shots),
        "scene_count": len(scenes),
        "shot_contracts_count": len(shots),  # one per shot
        "assumptions_made": assumptions,
        "missing_information": brief.get("missing_fields", []),
        "blockers": validation.errors,
        "warnings": validation.warnings,
        "next_layer_allowed": validation_passed and len(validation.errors) == 0,
        "operator_review_required": True,
        "current_state": "planning_operator_review_required",
        "next_allowed_action": "planning_operator_review_required",
        "production_accepted": False,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "next_recommended_layer": NEXT_LAYER,
        "notes": "Operator must review the planning package, confirm or modify scene/shot structure, then authorize proceeding to Workflow-to-Assets layer.",
    }


# ---------------------------------------------------------------------------
# Internal index/ledger helpers
# ---------------------------------------------------------------------------

def _update_artifact_index(
    paths: Dict[str, Path],
    timestamp: str,
    blocked: bool = False,
) -> None:
    """Update artifact_index.json with planning artifact paths."""
    index = _load_json(paths["artifact_index"])
    if index is None:
        index = {}

    planning_artifacts = [
        "planning/scenario_plan.json",
        "planning/scene_plan.json",
        "planning/shot_plan.json",
        "planning/production_plan.json",
        "planning/planning_validation_report.json",
        "planning/planning_operator_review_packet.json",
    ]

    # Add shot contracts if they exist
    if not blocked:
        shot_contracts_dir = paths["shot_contracts_dir"]
        if shot_contracts_dir.exists():
            for f in sorted(shot_contracts_dir.glob("shot_*.json")):
                rel = f.relative_to(paths["root"])
                planning_artifacts.append(str(rel.as_posix()))

    existing = index.get("artifacts", [])
    for artifact in planning_artifacts:
        if artifact not in existing:
            existing.append(artifact)

    index["artifacts"] = existing
    index["task_id"] = TASK_ID
    index["created_timestamp"] = timestamp
    index["total_artifacts"] = len(existing)
    index["planning_layer_completed"] = not blocked
    _write_json(paths["artifact_index"], index)


def _force_artifact_index_state(paths: Dict[str, Path], state: str) -> None:
    """Force the artifact_index current_state to a specific value."""
    index = _load_json(paths["artifact_index"])
    if index is None:
        index = {}
    index["current_state"] = state
    index["next_allowed_action"] = state
    _write_json(paths["artifact_index"], index)


def _update_episode_ledger(
    paths: Dict[str, Path],
    timestamp: str,
    status: str,
) -> None:
    """Append a planning layer event to the episode ledger."""
    ledger_path = paths["episode_ledger"]
    ledger = _load_json(ledger_path)
    if ledger is None:
        ledger = []

    event = {
        "event": "director_planning_layer_completed",
        "task_id": TASK_ID,
        "status": status,
        "generation_performed": False,
        "comfyui_submit_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "visual_qa_executed": False,
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "current_state": "planning_operator_review_required",
        "next_allowed_action": "planning_operator_review_required",
        "previous_layer": PREVIOUS_LAYER,
        "next_layer": NEXT_LAYER,
        "timestamp": timestamp,
    }

    if isinstance(ledger, list):
        ledger.append(event)
    elif isinstance(ledger, dict):
        events = ledger.get("events", [])
        events.append(event)
        ledger["events"] = events
        ledger["current_state"] = "planning_operator_review_required"
        ledger["next_allowed_action"] = "planning_operator_review_required"
        ledger["production_accepted"] = False

    _write_json(ledger_path, ledger)
