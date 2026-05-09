"""Preview Correction Planner Agent.

Part of RC-COMBINE-V2-PREVIEW-CORRECTION-PLAN-001. This agent:
  - Reads Script Supervisor audit, timeline, EDL, and preview artifacts
  - Builds a static preview root cause report
  - Creates a preview correction plan
  - Creates a preview repair contract
  - Creates a static preview prevention policy
  - Creates a controlled re-render gate package (but does NOT execute render)
  - Updates artifact_index, episode_ledger, and state
  - NEVER renders, generates, or modifies production artifacts
"""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class PreviewCorrectionPlanner:
    """Preview Correction Planner Agent.

    Diagnoses why a preview became static, produces the corrective plan and
    contracts, and creates the gate package for a future controlled re-render.
    This agent is purely diagnostic and contractual — it never executes renders.

    Attributes:
        agent_id: Unique identifier for this agent.
        project_root: Root path of the project.
        control_path: Path to the output/control directory.
    """

    def __init__(self, project_root: str):
        self.agent_id = "preview_correction_planner"
        self.project_root = project_root
        self.control_path = os.path.join(project_root, "output", "control")

    # -----------------------------------------------------------------------
    # Artifact Reading Helpers
    # -----------------------------------------------------------------------

    def _read_json(self, relative_path: str) -> Optional[Dict[str, Any]]:
        """Read a JSON artifact from the control directory."""
        path = os.path.join(self.control_path, relative_path)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _read_timeline(self) -> Dict[str, Any]:
        """Read the timeline model."""
        return self._read_json("editorial/timeline_model.json") or {}

    def _read_marker_registry(self) -> List[Dict[str, Any]]:
        """Read the marker registry."""
        data = self._read_json("editorial/marker_registry.json")
        return data if isinstance(data, list) else []

    def _read_edit_decision_list(self) -> List[Dict[str, Any]]:
        """Read the edit decision list."""
        data = self._read_json("editorial/edit_decision_list.json")
        return data if isinstance(data, list) else []

    def _read_transition_policy(self) -> Dict[str, Any]:
        """Read the transition policy."""
        return self._read_json("editorial/transition_policy.json") or {}

    def _read_preview_proof_contract(self) -> Dict[str, Any]:
        """Read the preview proof contract."""
        return self._read_json("editorial/preview_proof_contract.json") or {}

    def _read_preview_render_report(self) -> Dict[str, Any]:
        """Read the preview render report."""
        return self._read_json("preview_render_report.json") or {}

    def _read_preview_result_review(self) -> Dict[str, Any]:
        """Read the preview result review."""
        return self._read_json("preview_result_review.json") or {}

    def _read_script_supervisor_audit(self) -> Dict[str, Any]:
        """Read the Script Supervisor preview audit report."""
        return self._read_json("script_supervisor_preview_audit_report.json") or {}

    def _read_preview_operator_review_packet(self) -> Dict[str, Any]:
        """Read the preview operator review packet."""
        return self._read_json("preview_operator_review_packet.json") or {}

    def _read_artifact_index(self) -> Dict[str, Any]:
        """Read the current artifact index."""
        path = os.path.join(self.control_path, "artifact_index.json")
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    # -----------------------------------------------------------------------
    # Root Cause Analysis
    # -----------------------------------------------------------------------

    def build_root_cause_report(self) -> Dict[str, Any]:
        """Analyze all artifacts and determine the root cause of static preview."""
        timeline = self._read_timeline()
        markers = self._read_marker_registry()
        edl = self._read_edit_decision_list()
        transition = self._read_transition_policy()
        preview_proof = self._read_preview_proof_contract()
        render_report = self._read_preview_render_report()
        result_review = self._read_preview_result_review()
        audit = self._read_script_supervisor_audit()

        # --- Check 1: Timeline has single repeated asset ---
        scenes = timeline.get("scenes", [])
        has_single_scene = len(scenes) <= 1
        all_asset_refs_empty = all(
            len(s.get("asset_refs", [])) == 0 for s in scenes
        )
        video_tracks_empty = (
            len(timeline.get("tracks", {}).get("video_main", [])) == 0
            and len(timeline.get("tracks", {}).get("video_overlay", [])) == 0
        )
        timeline_has_single_repeated_asset = (
            has_single_scene and all_asset_refs_empty and video_tracks_empty
        )

        # --- Check 2: EDL reuses same frame or asset ---
        edl_operations = len(edl)
        edl_all_unapplied = all(
            op.get("apply_performed", True) is False for op in edl
        )
        edl_reuses_same_frame = edl_operations <= 2 and edl_all_unapplied

        # --- Check 3: Preview renderer samples same source ---
        total_frames = render_report.get("outputs", {}).get(
            "preview_lowres.mp4", {}
        ).get("duration_sec", 0) * render_report.get("fps", 24)
        gif_frame_count = render_report.get("outputs", {}).get(
            "preview.gif", {}
        ).get("frame_count", 0)
        preview_renderer_samples_same = gif_frame_count <= 50 and total_frames > 600

        # --- Check 4: Frame sequence not progressing ---
        duplicate_ratio = audit.get("duplicate_static_ratio", 0)
        frame_sequence_not_progressing = duplicate_ratio > 0.85

        # --- Check 5: Contact sheet sampling invalid ---
        contact_sheet_useful = audit.get("contact_sheet_useful", False)
        contact_sheet_sampling_invalid = not contact_sheet_useful

        # --- Check 6: Path mismatch affects preview collection ---
        path_mismatch_detected = audit.get("preview_path_mismatch_detected", False)

        # --- Evidence collection ---
        evidence = []

        if timeline_has_single_repeated_asset:
            evidence.append(
                f"Timeline has {len(scenes)} scene(s) with all empty asset_refs "
                f"and empty video tracks — no visual content to render"
            )

        if edl_reuses_same_frame:
            evidence.append(
                f"EDL has {edl_operations} operation(s), all unapplied "
                f"(apply_performed=false) — no clip insertions executed"
            )

        if frame_sequence_not_progressing:
            evidence.append(
                f"Frame duplicate ratio is {duplicate_ratio:.1%} "
                f"({audit.get('duplicate_frame_count', 0)} duplicate "
                f"out of {audit.get('total_frame_count', 0)} total)"
            )

        if contact_sheet_sampling_invalid:
            evidence.append(
                "Contact sheet does not prove timeline progression "
                "(contact_sheet_useful=false)"
            )

        if len(markers) <= 1:
            evidence.append(
                f"Only {len(markers)} marker(s) defined — insufficient "
                f"time reference points for scene progression"
            )

        # Determine primary root cause
        if timeline_has_single_repeated_asset:
            primary_root_cause = (
                "timeline_empty_no_assets_placed: "
                "Timeline model contains a single empty scene (scene_001) "
                "with no asset_refs, no video_main/video_overlay clips, "
                f"and {len(edl)} unapplied EDL operations. "
                "The ffmpeg renderer had no visual variety to produce."
            )
        elif frame_sequence_not_progressing:
            primary_root_cause = (
                "frame_sequence_static: "
                f"{duplicate_ratio:.1%} of frames are duplicates, "
                "indicating the render source had no visual progression."
            )
        else:
            primary_root_cause = (
                "unresolved: "
                "No single definitive cause identified; multiple contributing factors."
            )

        # Build the report
        return {
            "report_type": "static_preview_root_cause",
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "possible_causes_checked": {
                "timeline_has_single_repeated_asset": timeline_has_single_repeated_asset,
                "edl_reuses_same_frame_or_asset": edl_reuses_same_frame,
                "preview_renderer_samples_same_source": preview_renderer_samples_same,
                "frame_sequence_not_progressing": frame_sequence_not_progressing,
                "contact_sheet_sampling_invalid": contact_sheet_sampling_invalid,
                "path_mismatch_affects_preview_collection": path_mismatch_detected,
            },
            "primary_root_cause": primary_root_cause,
            "confidence": "high" if timeline_has_single_repeated_asset else "medium",
            "evidence": evidence,
            "artifacts_analyzed": {
                "timeline_model": bool(timeline),
                "marker_registry": len(markers) > 0,
                "edit_decision_list": len(edl) > 0,
                "transition_policy": bool(transition),
                "preview_proof_contract": bool(preview_proof),
                "preview_render_report": bool(render_report),
                "preview_result_review": bool(result_review),
                "script_supervisor_audit": bool(audit),
            },
        }

    # -----------------------------------------------------------------------
    # Correction Plan
    # -----------------------------------------------------------------------

    def build_correction_plan(
        self, root_cause: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the preview correction plan based on root cause analysis."""
        return {
            "plan_type": "preview_correction_plan",
            "correction_goal": (
                "produce a non-static preview that proves "
                "real timeline/scene progression"
            ),
            "root_cause_summary": root_cause.get("primary_root_cause", "unknown"),
            "required_repairs": [
                (
                    "ensure timeline has multiple distinct visual segments "
                    "or intentional stillness is declared"
                ),
                (
                    "ensure EDL references correct assets/clips per scene "
                    "and operations are applied"
                ),
                (
                    "ensure preview renderer samples frames across "
                    "timeline progression"
                ),
                (
                    "ensure contact_sheet samples meaningful "
                    "timeline positions"
                ),
                "canonicalize output/previews path to output/preview",
                "block preview acceptance if duplicate ratio exceeds threshold",
            ],
            "duplicate_frame_policy": {
                "max_duplicate_ratio": 0.85,
                "static_preview_blocker_required": True,
            },
            "contact_sheet_policy": {
                "must_prove_timeline_progression": True,
                "technical_file_exists_is_not_enough": True,
            },
            "next_gate_required": (
                "controlled_preview_rerender_authorization_required"
            ),
            "plan_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -----------------------------------------------------------------------
    # Repair Contract
    # -----------------------------------------------------------------------

    def build_repair_contract(self) -> Dict[str, Any]:
        """Build the preview repair contract that governs the next render."""
        return {
            "contract_type": "preview_repair_contract",
            "governs_render_type": "controlled_preview_rerender",
            "render_must_prove": {
                "non_static_visual_progression": (
                    "The rendered preview must show visual change "
                    "across the timeline — duplicate frame ratio must "
                    "be below 0.85 or justified by explicit still-scene "
                    "contract"
                ),
                "valid_frame_sampling": (
                    "Frames must be sampled at regular intervals "
                    "across the full timeline duration"
                ),
                "useful_contact_sheet": (
                    "The contact sheet must show visually distinct "
                    "frames that prove timeline progression"
                ),
                "canonical_preview_path": (
                    "All preview outputs must use the canonical path "
                    "output/preview/ (singular), not output/previews/ "
                    "(plural)"
                ),
            },
            "duplicate_frame_justification": {
                "max_allowed_ratio": 0.85,
                "above_threshold_requires_explicit_still_scene_contract": True,
            },
            "blocked_downstream_stages": {
                "voice_generation": False,
                "audio_generation": False,
                "assembly": False,
                "downstream": False,
                "production_acceptance": False,
            },
            "contract_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -----------------------------------------------------------------------
    # Prevention Policy
    # -----------------------------------------------------------------------

    def build_prevention_policy(self) -> Dict[str, Any]:
        """Build the static preview prevention policy."""
        return {
            "policy_type": "static_preview_prevention_policy",
            "static_preview_detection_required": True,
            "duplicate_frame_threshold": 0.85,
            "contact_sheet_must_show_progression": True,
            (
                "preview_result_review_must_include_motion_"
                "or_variation_metrics"
            ): True,
            (
                "technical_preview_success_is_not_operator_acceptance"
            ): True,
            "voice_stage_blocked_until_real_operator_preview_approval": True,
            "prevention_rules": [
                (
                    "Before any preview render, verify the timeline "
                    "contains at least 2 visually distinct segments "
                    "or an explicit still-scene declaration"
                ),
                (
                    "After render, measure frame-to-frame variance. "
                    "If duplicate ratio > 0.85, block acceptance "
                    "and route to correction plan"
                ),
                (
                    "Contact sheet must be evaluated for visual "
                    "progression, not just file existence"
                ),
                (
                    "Operator preview acceptance must come from a "
                    "real human operator, never from an agent"
                ),
            ],
            "policy_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -----------------------------------------------------------------------
    # Re-render Gate Package
    # -----------------------------------------------------------------------

    def build_rerender_gate_package(self) -> Dict[str, Any]:
        """Build the controlled re-render gate package (no render executed)."""
        return {
            "gate_type": "controlled_preview_rerender_authorization",
            "render_authorized_now": False,
            "requires_operator_authorization": True,
            "max_preview_renders_after_authorization": 1,
            "stop_after_preview_render": True,
            "voice_generation_allowed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "required_preconditions": [
                "preview_correction_plan_exists",
                "preview_repair_contract_exists",
                "static_preview_prevention_policy_exists",
                "script_supervisor_blocker_acknowledged",
            ],
            "gate_timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # -----------------------------------------------------------------------
    # Full Pipeline
    # -----------------------------------------------------------------------

    def run_correction_pipeline(self) -> Dict[str, Any]:
        """Run the full correction pipeline.

        Returns:
            Dict with all generated artifacts and status.
        """
        # 1. Root cause analysis
        root_cause = self.build_root_cause_report()

        # 2. Build correction plan
        correction_plan = self.build_correction_plan(root_cause)

        # 3. Build repair contract
        repair_contract = self.build_repair_contract()

        # 4. Build prevention policy
        prevention_policy = self.build_prevention_policy()

        # 5. Build re-render gate package
        rerender_gate = self.build_rerender_gate_package()

        return {
            "pipeline": "preview_correction_plan",
            "task_id": "RC-COMBINE-V2-PREVIEW-CORRECTION-PLAN-001",
            "pipeline_timestamp": datetime.now(timezone.utc).isoformat(),
            "static_preview_root_cause_report": root_cause,
            "preview_correction_plan": correction_plan,
            "preview_repair_contract": repair_contract,
            "static_preview_prevention_policy": prevention_policy,
            "controlled_preview_rerender_gate_package": rerender_gate,
            "forbidden_actions_not_executed": {
                "generation_performed": False,
                "retry_attempted": False,
                "comfyui_submit_executed": False,
                "preview_render_executed": False,
                "voice_generation_executed": False,
                "visual_qa_executed": False,
                "visual_acceptance_executed": False,
                "assembly_executed": False,
                "downstream_executed": False,
                "production_accepted": False,
            },
        }

    # -----------------------------------------------------------------------
    # Artifact Persistence
    # -----------------------------------------------------------------------

    def _ensure_control_dir(self) -> str:
        """Ensure the control directory exists, return its path."""
        os.makedirs(self.control_path, exist_ok=True)
        return self.control_path

    def _write_artifact(self, filename: str, data: Dict[str, Any]) -> str:
        """Write a JSON artifact to the control directory."""
        ctrl = self._ensure_control_dir()
        path = os.path.join(ctrl, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def write_all_artifacts(
        self, pipeline_result: Dict[str, Any]
    ) -> Dict[str, str]:
        """Write all canonical artifacts from the pipeline result."""
        written = {}

        # 1. Static preview root cause report
        written["static_preview_root_cause_report"] = self._write_artifact(
            "static_preview_root_cause_report.json",
            pipeline_result.get("static_preview_root_cause_report", {}),
        )

        # 2. Preview correction plan
        written["preview_correction_plan"] = self._write_artifact(
            "preview_correction_plan.json",
            pipeline_result.get("preview_correction_plan", {}),
        )

        # 3. Preview repair contract
        written["preview_repair_contract"] = self._write_artifact(
            "preview_repair_contract.json",
            pipeline_result.get("preview_repair_contract", {}),
        )

        # 4. Static preview prevention policy
        written["static_preview_prevention_policy"] = self._write_artifact(
            "static_preview_prevention_policy.json",
            pipeline_result.get("static_preview_prevention_policy", {}),
        )

        # 5. Controlled re-render gate package
        written["controlled_preview_rerender_gate_package"] = (
            self._write_artifact(
                "controlled_preview_rerender_gate_package.json",
                pipeline_result.get(
                    "controlled_preview_rerender_gate_package", {}
                ),
            )
        )

        return written

    # -----------------------------------------------------------------------
    # State / Index / Ledger Updates
    # -----------------------------------------------------------------------

    def update_artifact_index(
        self, pipeline_result: Dict[str, Any], written: Dict[str, str]
    ) -> Dict[str, Any]:
        """Update artifact_index.json with correction plan results."""
        index = self._read_artifact_index()

        root_cause = pipeline_result.get("static_preview_root_cause_report", {})
        correction_plan = pipeline_result.get("preview_correction_plan", {})

        index["preview_correction_plan_executed"] = True
        index["preview_correction_plan_task_id"] = (
            "RC-COMBINE-V2-PREVIEW-CORRECTION-PLAN-001"
        )
        index["preview_correction_plan_timestamp"] = pipeline_result.get(
            "pipeline_timestamp"
        )
        index["static_preview_root_cause"] = root_cause.get(
            "primary_root_cause", "unknown"
        )
        index["static_preview_confidence"] = root_cause.get("confidence", "unknown")
        index["correction_goal"] = correction_plan.get("correction_goal", "")
        index["next_gate_required"] = correction_plan.get(
            "next_gate_required", ""
        )
        index["render_authorized_now"] = False
        index["requires_operator_authorization"] = True
        index["voice_generation_allowed"] = False
        index["voice_generation_ready"] = False
        index["assembly_allowed"] = False
        index["downstream_allowed"] = False
        index["production_accepted"] = False
        index["current_state"] = "controlled_preview_rerender_authorization_required"
        index["next_allowed_action"] = (
            "controlled_preview_rerender_authorization_required"
        )
        index["script_supervisor_blocker_active"] = True
        index["correction_plan_artifacts"] = list(written.keys())

        index_path = os.path.join(self.control_path, "artifact_index.json")
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        return index

    def update_episode_ledger(
        self, pipeline_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Record correction plan event in the episode ledger."""
        ledger_path = os.path.join(self.control_path, "episode_ledger.json")
        ledger: list = []
        if os.path.isfile(ledger_path):
            try:
                with open(ledger_path, "r", encoding="utf-8") as f:
                    ledger = json.load(f)
            except (json.JSONDecodeError, IOError):
                ledger = []

        root_cause = pipeline_result.get("static_preview_root_cause_report", {})

        event = {
            "event_type": "preview_correction_plan_executed",
            "agent_id": self.agent_id,
            "task_id": "RC-COMBINE-V2-PREVIEW-CORRECTION-PLAN-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "previous_state": "preview_correction_plan_required",
            "current_state": "controlled_preview_rerender_authorization_required",
            "next_allowed_action": (
                "controlled_preview_rerender_authorization_required"
            ),
            "primary_root_cause": root_cause.get("primary_root_cause", "unknown"),
            "root_cause_confidence": root_cause.get("confidence", "unknown"),
            "duplicate_static_ratio": root_cause.get(
                "possible_causes_checked", {}
            ).get("frame_sequence_not_progressing", False),
            "render_authorized_now": False,
            "requires_operator_authorization": True,
            "voice_generation_allowed": False,
            "voice_generation_ready": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "generation_performed": False,
            "retry_attempted": False,
            "comfyui_submit_executed": False,
            "preview_render_executed": False,
            "voice_generation_executed": False,
            "visual_qa_executed": False,
            "visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "artifacts_created": [
                "static_preview_root_cause_report.json",
                "preview_correction_plan.json",
                "preview_repair_contract.json",
                "static_preview_prevention_policy.json",
                "controlled_preview_rerender_gate_package.json",
            ],
            "notes": (
                "Static preview correction plan completed. "
                "Next render requires explicit operator authorization "
                "via controlled_preview_rerender_authorization_required gate."
            ),
        }
        ledger.append(event)

        with open(ledger_path, "w", encoding="utf-8") as f:
            json.dump(ledger, f, indent=2, ensure_ascii=False)

        return ledger
