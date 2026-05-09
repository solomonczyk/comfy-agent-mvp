"""RC-COMBINE-V2-TIMELINE-TO-PREVIEW-001 — Timeline-to-Preview Package.

Builds the complete editorial contract set from an approved visual asset:
timeline model -> marker registry -> edit decision list
-> subtitle plan -> transition policy -> voice casting contract
-> preview proof contract -> dry-run -> authorization packet.

No preview render, voice generation, or assembly is executed.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.editorial.timeline_model import TimelineModel, SceneContract, ShotContract
from app.editorial.marker_registry import MarkerRegistry, Marker
from app.editorial.edit_decision_planner import EditDecisionPlanner, EditOperation
from app.editorial.subtitle_planner import SubtitlePlanner, SubtitleEntry
from app.editorial.transition_policy import TransitionPolicy
from app.editorial.voice_casting_policy import VoiceCastingContract
from app.editorial.preview_contract import PreviewProofContract
from app.editorial.timeline_dry_run import TimelineDryRun

TASK_ID = "RC-COMBINE-V2-TIMELINE-TO-PREVIEW-001"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_project_root(project_root: Optional[str]) -> Path:
    if project_root:
        return Path(project_root).resolve()
    return Path.cwd().resolve()


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _read_ledger(ledger_path: Path) -> list:
    data = _read_json(ledger_path)
    return data if isinstance(data, list) else []


def _write_ledger(ledger_path: Path, events: list) -> None:
    _write_json(ledger_path, events)


# ---------------------------------------------------------------------------
# Artifact builders
# ---------------------------------------------------------------------------


def load_approved_asset(
    project_root: Path,
) -> Optional[Dict[str, Any]]:
    """Load the approved visual asset from the manifest."""
    manifest_path = (
        project_root
        / "output"
        / "control"
        / "approved_visual_assets_manifest.json"
    )
    manifest = _read_json(manifest_path)
    if not manifest:
        return None
    assets = manifest.get("approved_assets", [])
    if not assets:
        return None
    return assets[0]


def build_timeline_model(approved_asset: Dict[str, Any]) -> TimelineModel:
    """Create timeline model anchored to the approved visual asset."""
    asset_path = approved_asset.get("path", "")
    asset_filename = os.path.basename(asset_path)

    timeline = TimelineModel(
        project_id="rc2_multishot1_ep01",
        timeline_version="mvp_v1",
        fps=24,
        resolution={"width": 1344, "height": 768},
    )

    # Single scene with the approved asset as the hero shot
    shot = ShotContract(
        shot_id="shot_001",
        candidate_asset=asset_path,
        asset_type="image",
        duration_sec=30.0,
        fit_policy="contain_or_cover",
        safe_area_required=True,
    )

    scene = SceneContract(
        scene_id="scene_001",
        duration_sec=30.0,
        shot_ids=[shot.shot_id],
        asset_refs=[asset_path],
        start_time="00:00:00",
        end_time="00:00:30",
        status="planned",
    )

    timeline.add_scene(scene)

    # Place asset on video_main track
    timeline.operations.append(
        {
            "operation_id": "place_hero_asset",
            "operation": "insert_clip",
            "asset_ref": asset_path,
            "track": "video_main",
            "start_time": "00:00:00",
            "end_time": "00:00:30",
            "duration_sec": 30.0,
            "fit_policy": "contain_or_cover",
            "apply_performed": False,
            "requires_operator_review": True,
        }
    )

    return timeline


def build_marker_registry(timeline: TimelineModel) -> MarkerRegistry:
    """Create marker registry anchored to timeline scene/shot IDs."""
    scene_ids = {s.scene_id for s in timeline.scenes}
    registry = MarkerRegistry()
    registry.set_known_scene_ids(scene_ids)

    markers_data = [
        Marker(
            marker_id="marker_scene_001_start",
            scene_id="scene_001",
            shot_id="shot_001",
            timecode="00:00:00",
            description="Scene 001 start — approved visual asset intro",
            anchor_type="scene_id",
        ),
        Marker(
            marker_id="marker_scene_001_mid",
            scene_id="scene_001",
            shot_id="shot_001",
            timecode="00:00:15",
            description="Mid-point of hero shot — transition / subtitle anchor",
            anchor_type="timecode",
        ),
        Marker(
            marker_id="marker_scene_001_end",
            scene_id="scene_001",
            shot_id="shot_001",
            timecode="00:00:30",
            description="Scene 001 end — fade to black point",
            anchor_type="timecode",
        ),
        Marker(
            marker_id="marker_subtitle_intro",
            scene_id="scene_001",
            shot_id="shot_001",
            timecode="00:00:02",
            description="Subtitle entry point — intro text",
            anchor_type="timecode",
        ),
        Marker(
            marker_id="marker_voiceover_start",
            scene_id="scene_001",
            shot_id="shot_001",
            timecode="00:00:01",
            description="Voiceover start anchor",
            anchor_type="timecode",
        ),
    ]

    for m in markers_data:
        registry.register(m)

    return registry


def build_edit_decision_list(timeline: TimelineModel) -> EditDecisionPlanner:
    """Create EDL describing what operations would be applied during preview render."""
    planner = EditDecisionPlanner()

    operations = [
        EditOperation(
            operation_id="edl_place_hero",
            operation="insert_clip",
            anchor="scene_001/shot_001",
            mode="ripple",
            apply_performed=False,
            requires_preview=True,
            requires_operator_review=True,
        ),
        EditOperation(
            operation_id="edl_add_voiceover_placeholder",
            operation="add_voiceover_placeholder",
            anchor="scene_001",
            mode="overlay",
            apply_performed=False,
            requires_preview=True,
            requires_operator_review=True,
        ),
        EditOperation(
            operation_id="edl_fade_to_black",
            operation="apply_transition",
            anchor="marker_scene_001_end",
            mode="overwrite",
            apply_performed=False,
            requires_preview=True,
            requires_operator_review=True,
        ),
        EditOperation(
            operation_id="edl_subtitle_intro_burnin",
            operation="add_subtitle",
            anchor="marker_subtitle_intro",
            mode="overlay",
            apply_performed=False,
            requires_preview=True,
            requires_operator_review=True,
        ),
    ]

    for op in operations:
        planner.add_operation(op)

    return planner


def build_subtitle_plan(timeline: TimelineModel) -> SubtitlePlanner:
    """Create subtitle plan with text, timing, position, style, safe zones."""
    planner = SubtitlePlanner()

    subtitles = [
        SubtitleEntry(
            subtitle_id="sub_intro_001",
            text="Оператор утвердил визуальный актив. Начинаем монтаж.",
            anchor_type="timecode",
            start_time="00:00:02",
            end_time="00:00:06",
            scene_id="scene_001",
            start_offset=2.0,
            duration=4.0,
            position="bottom_center",
            style="clean_white",
            safe_zone_required=True,
        ),
        SubtitleEntry(
            subtitle_id="sub_mid_001",
            text="Сцена 1: основной кадр. Длительность 30 секунд.",
            anchor_type="timecode",
            start_time="00:00:08",
            end_time="00:00:12",
            scene_id="scene_001",
            start_offset=8.0,
            duration=4.0,
            position="bottom_center",
            style="clean_white",
            safe_zone_required=True,
        ),
        SubtitleEntry(
            subtitle_id="sub_outro_001",
            text="Конец сцены. Переход к следующему эпизоду.",
            anchor_type="timecode",
            start_time="00:00:26",
            end_time="00:00:30",
            scene_id="scene_001",
            start_offset=26.0,
            duration=4.0,
            position="bottom_center",
            style="clean_white",
            safe_zone_required=True,
        ),
    ]

    for s in subtitles:
        planner.add_entry(s)

    return planner


def build_transition_policy() -> TransitionPolicy:
    """Create transition policy with allowed transitions and fade ratio validation."""
    return TransitionPolicy(
        default="hard_cut",
        same_scene_continuation="hard_cut",
        new_topic="crossfade",
        new_chapter="fade_to_black",
        educational_style="clean_cut",
        cinematic_style="fade_or_dissolve",
        forbidden_transitions=[
            "random_wipe",
            "spin",
            "excessive_glitch",
            "star_wipe",
            "checkerboard",
            "explosive_transition",
        ],
        max_total_fade_ratio=0.35,
    )


def build_voice_casting_contract() -> VoiceCastingContract:
    """Create voice casting contract — no voice generation."""
    return VoiceCastingContract(
        language="ru",
        preferred_gender="female",
        age_range="30-45",
        tone=["calm", "clear", "expert", "friendly"],
        pace="medium",
        emotion="confident_warm",
        avoid=[
            "robotic",
            "too_fast",
            "overdramatic",
            "aggressive_sales_tone",
        ],
        sample_required=True,
        operator_review_required=True,
        full_voiceover_generation_allowed=False,
    )


def build_preview_proof_contract() -> PreviewProofContract:
    """Create preview proof contract listing required preview artifacts."""
    return PreviewProofContract(
        preview_lowres_required=True,
        preview_gif_required=True,
        contact_sheet_required=True,
        subtitle_burnin_preview_required=True,
        timeline_report_required=True,
        transition_qa_required=True,
        subtitle_qa_required=True,
        audio_qa_required=True,
        operator_review_required=True,
        final_render_allowed=False,
    )


def run_dry_run(
    timeline: TimelineModel,
    registry: MarkerRegistry,
    subtitle_planner: SubtitlePlanner,
    transition_policy: TransitionPolicy,
    voice_contract: VoiceCastingContract,
    preview_contract: PreviewProofContract,
) -> Dict[str, Any]:
    """Run dry-run validation on all editorial artifacts.

    Returns the dry-run report dict. No preview render is executed.
    """
    dry_run = TimelineDryRun()
    report = dry_run.run(
        timeline_dict=timeline.to_dict(),
        markers=registry.to_dict_list(),
        subtitles=subtitle_planner.to_dict_list(),
        transition_policy=transition_policy.to_dict(),
        voice_casting_contract=voice_contract.to_dict(),
        preview_proof_contract=preview_contract.to_dict(),
    )
    return report.to_dict()


def build_authorization_packet(
    approved_asset: Dict[str, Any],
    timeline: TimelineModel,
    registry: MarkerRegistry,
    edl_planner: EditDecisionPlanner,
    subtitle_planner: SubtitlePlanner,
    transition_policy: TransitionPolicy,
    voice_contract: VoiceCastingContract,
    preview_contract: PreviewProofContract,
    dry_run_report: Dict[str, Any],
    timestamp: str,
) -> Dict[str, Any]:
    """Build the preview render authorization packet for operator review.

    This packet is the gate document — operator must approve before
    preview render is allowed.
    """
    return {
        "task_id": TASK_ID,
        "packet_type": "preview_render_authorization",
        "authorization_required": True,
        "authorization_granted": False,
        "operator_decision": None,
        "timestamp": timestamp,
        "approved_asset": {
            "path": approved_asset.get("path", ""),
            "sha256": approved_asset.get("sha256", ""),
            "approval_stage": approved_asset.get("approval_stage", ""),
        },
        "timeline_summary": {
            "project_id": timeline.project_id,
            "timeline_version": timeline.timeline_version,
            "fps": timeline.fps,
            "resolution": timeline.resolution,
            "scene_count": len(timeline.scenes),
            "operation_count": len(timeline.operations),
        },
        "editorial_summary": {
            "marker_count": len(registry.list_markers()),
            "edl_operation_count": len(edl_planner.list_operations()),
            "subtitle_count": len(subtitle_planner.list_entries()),
            "transition_policy": {
                "default": transition_policy.default,
                "forbidden_count": len(transition_policy.forbidden_transitions),
                "max_fade_ratio": transition_policy.max_total_fade_ratio,
            },
            "voice_casting": {
                "language": voice_contract.language,
                "sample_required": voice_contract.sample_required,
                "operator_review_required": voice_contract.operator_review_required,
            },
            "preview_requirements": {
                "preview_lowres_required": preview_contract.preview_lowres_required,
                "preview_gif_required": preview_contract.preview_gif_required,
                "contact_sheet_required": preview_contract.contact_sheet_required,
                "subtitle_burnin_required": preview_contract.subtitle_burnin_preview_required,
                "transition_qa_required": preview_contract.transition_qa_required,
                "subtitle_qa_required": preview_contract.subtitle_qa_required,
                "audio_qa_required": preview_contract.audio_qa_required,
            },
        },
        "dry_run_status": dry_run_report.get("dry_run_status", "unknown"),
        "dry_run_errors": dry_run_report.get("errors", []),
        "dry_run_warnings": dry_run_report.get("warnings", []),
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "forbidden_actions": {
            "new_generation": False,
            "retry": False,
            "comfyui_submit": False,
            "preview_render_executed": False,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
        },
        "artifacts": [
            "timeline_model.json",
            "marker_registry.json",
            "edit_decision_list.json",
            "subtitle_plan.json",
            "transition_policy.json",
            "voice_casting_contract.json",
            "preview_proof_contract.json",
            "timeline_preview_dry_run_report.json",
            "preview_render_authorization_packet.json",
        ],
    }


# ---------------------------------------------------------------------------
# Ledger helpers
# ---------------------------------------------------------------------------


def _build_ledger_events(
    approved_asset: Dict[str, Any],
    timeline: TimelineModel,
    dry_run_report: Dict[str, Any],
    timestamp: str,
) -> list:
    """Build ledger events for the timeline-to-preview package."""
    status = dry_run_report.get("dry_run_status", "unknown")
    passed = status != "blocked"
    asset_path = approved_asset.get("path", "")

    events = [
        {
            "event_type": "timeline_to_preview_package_started",
            "task_id": TASK_ID,
            "stage": "timeline_to_preview_package_required",
            "approved_asset": asset_path,
            "production_accepted": False,
            "timestamp": timestamp,
        },
        {
            "event_type": "timeline_model_created",
            "stage": "timeline_to_preview_package_required",
            "artifact": "timeline_model.json",
            "timestamp": timestamp,
        },
        {
            "event_type": "marker_registry_created",
            "stage": "timeline_to_preview_package_required",
            "artifact": "marker_registry.json",
            "timestamp": timestamp,
        },
        {
            "event_type": "edit_decision_list_created",
            "stage": "timeline_to_preview_package_required",
            "artifact": "edit_decision_list.json",
            "timestamp": timestamp,
        },
        {
            "event_type": "subtitle_plan_created",
            "stage": "timeline_to_preview_package_required",
            "artifact": "subtitle_plan.json",
            "timestamp": timestamp,
        },
        {
            "event_type": "transition_policy_created",
            "stage": "timeline_to_preview_package_required",
            "artifact": "transition_policy.json",
            "timestamp": timestamp,
        },
        {
            "event_type": "voice_casting_contract_created",
            "stage": "timeline_to_preview_package_required",
            "artifact": "voice_casting_contract.json",
            "timestamp": timestamp,
        },
        {
            "event_type": "preview_proof_contract_created",
            "stage": "timeline_to_preview_package_required",
            "artifact": "preview_proof_contract.json",
            "timestamp": timestamp,
        },
        {
            "event_type": "timeline_preview_dry_run_completed",
            "stage": "timeline_to_preview_package_required",
            "dry_run_status": status,
            "dry_run_passed": passed,
            "error_count": len(dry_run_report.get("errors", [])),
            "warning_count": len(dry_run_report.get("warnings", [])),
            "apply_performed": False,
            "real_render_executed": False,
            "generation_performed": False,
            "production_accepted": False,
            "current_state": "preview_render_authorization_required",
            "next_allowed_action": "preview_render_authorization_required",
            "timestamp": timestamp,
        },
        {
            "event_type": "preview_render_authorization_required",
            "stage": "preview_render_authorization_required",
            "operator_decision": None,
            "preview_render_executed": False,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": "preview_render_authorization_required",
            "next_allowed_action": "preview_render_authorization_required",
            "timestamp": timestamp,
        },
    ]

    return events


def _build_artifact_index_update(
    approved_asset: Dict[str, Any],
    dry_run_report: Dict[str, Any],
    timestamp: str,
) -> Dict[str, Any]:
    """Build the artifact index update payload."""
    asset_path = approved_asset.get("path", "")
    asset_sha256 = approved_asset.get("sha256", "")
    return {
        "task_id": TASK_ID,
        "current_state": "preview_render_authorization_required",
        "next_allowed_action": "preview_render_authorization_required",
        "production_accepted": False,
        "approved_asset_consumed": True,
        "approved_asset_path": asset_path,
        "approved_asset_sha256": asset_sha256,
        "timeline_model_created": True,
        "marker_registry_created": True,
        "edit_decision_list_created": True,
        "subtitle_plan_created": True,
        "transition_policy_created": True,
        "voice_casting_contract_created": True,
        "preview_proof_contract_created": True,
        "timeline_preview_dry_run_report_created": True,
        "preview_render_authorization_packet_created": True,
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "timeline_dry_run_status": dry_run_report.get("dry_run_status", "unknown"),
        "timeline_dry_run_errors": dry_run_report.get("errors", []),
        "timeline_dry_run_warnings": dry_run_report.get("warnings", []),
        "timestamp": timestamp,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def build_timeline_to_preview_package(
    project_root: Optional[str] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """Build the complete timeline-to-preview package.

    Args:
        project_root: Path to the project root (default: cwd).
        dry_run: If True (default), performs all steps but skips actual
                 preview render. This is the only allowed mode.

    Returns:
        A result dict with status, artifact paths, and state info.
    """
    root = _resolve_project_root(project_root)
    control_dir = root / "output" / "control"
    timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Load approved asset
    approved_asset = load_approved_asset(root)
    if not approved_asset:
        return {
            "status": "error",
            "message": "No approved visual asset found in approved_visual_assets_manifest.json",
            "task_id": TASK_ID,
        }

    # 2. Build timeline model
    timeline = build_timeline_model(approved_asset)
    _write_json(control_dir / "timeline_model.json", timeline.to_dict())

    # 3. Build marker registry
    registry = build_marker_registry(timeline)
    _write_json(control_dir / "marker_registry.json", registry.to_dict_list())

    # 4. Build edit decision list
    edl_planner = build_edit_decision_list(timeline)
    _write_json(control_dir / "edit_decision_list.json", edl_planner.to_dict_list())

    # 5. Build subtitle plan
    subtitle_planner = build_subtitle_plan(timeline)
    _write_json(control_dir / "subtitle_plan.json", subtitle_planner.to_dict_list())

    # 6. Build transition policy
    transition_policy = build_transition_policy()
    _write_json(control_dir / "transition_policy.json", transition_policy.to_dict())

    # 7. Build voice casting contract
    voice_contract = build_voice_casting_contract()
    _write_json(control_dir / "voice_casting_contract.json", voice_contract.to_dict())

    # 8. Build preview proof contract
    preview_contract = build_preview_proof_contract()
    _write_json(control_dir / "preview_proof_contract.json", preview_contract.to_dict())

    # 9. Run dry-run validation
    dry_run_report = run_dry_run(
        timeline=timeline,
        registry=registry,
        subtitle_planner=subtitle_planner,
        transition_policy=transition_policy,
        voice_contract=voice_contract,
        preview_contract=preview_contract,
    )
    dry_run_report["timestamp"] = timestamp
    _write_json(control_dir / "timeline_preview_dry_run_report.json", dry_run_report)

    # 10. Build authorization packet
    auth_packet = build_authorization_packet(
        approved_asset=approved_asset,
        timeline=timeline,
        registry=registry,
        edl_planner=edl_planner,
        subtitle_planner=subtitle_planner,
        transition_policy=transition_policy,
        voice_contract=voice_contract,
        preview_contract=preview_contract,
        dry_run_report=dry_run_report,
        timestamp=timestamp,
    )
    _write_json(
        control_dir / "preview_render_authorization_packet.json", auth_packet
    )

    # 11. Update artifact index (merge with existing to preserve prior fields)
    existing_index = _read_json(control_dir / "artifact_index.json") or {}
    index_update = _build_artifact_index_update(
        approved_asset=approved_asset,
        dry_run_report=dry_run_report,
        timestamp=timestamp,
    )
    existing_index.update(index_update)
    _write_json(control_dir / "artifact_index.json", existing_index)

    # 12. Update episode ledger
    ledger_path = control_dir / "episode_ledger.json"
    existing_ledger = _read_ledger(ledger_path)
    new_events = _build_ledger_events(
        approved_asset=approved_asset,
        timeline=timeline,
        dry_run_report=dry_run_report,
        timestamp=timestamp,
    )
    existing_ledger.extend(new_events)
    _write_ledger(ledger_path, existing_ledger)

    # 13. Return result
    return {
        "status": "ok",
        "task_id": TASK_ID,
        "current_state": "preview_render_authorization_required",
        "next_allowed_action": "preview_render_authorization_required",
        "production_accepted": False,
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "dry_run_status": dry_run_report.get("dry_run_status", "unknown"),
        "dry_run_errors": dry_run_report.get("errors", []),
        "dry_run_warnings": dry_run_report.get("warnings", []),
        "artifacts": {
            "timeline_model": "timeline_model.json",
            "marker_registry": "marker_registry.json",
            "edit_decision_list": "edit_decision_list.json",
            "subtitle_plan": "subtitle_plan.json",
            "transition_policy": "transition_policy.json",
            "voice_casting_contract": "voice_casting_contract.json",
            "preview_proof_contract": "preview_proof_contract.json",
            "timeline_preview_dry_run_report": "timeline_preview_dry_run_report.json",
            "preview_render_authorization_packet": "preview_render_authorization_packet.json",
        },
        "forbidden_actions": {
            "new_generation": False,
            "retry": False,
            "comfyui_submit": False,
            "preview_render_executed": False,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
        },
        "timestamp": timestamp,
    }
