"""MK-CTRL1 — Shot controller data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ActionDefinition:
    action: str
    handler_key: str
    required_inputs: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    command_template: str | None = None


@dataclass
class HandlerExecutionMeta:
    """Execution-semantics metadata for action results and ledger records."""

    control_executed: bool | None = None
    production_executed: bool | None = None
    handler_status: str | None = None


@dataclass
class ActionPlan:
    episode_id: str
    shot_id: str
    action: str
    allowed: bool
    current_state: str
    expected_next_action: str
    brief_path: str | None = None
    required_inputs: list[str] = field(default_factory=list)
    missing_inputs: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    command_preview: str | None = None
    handler_key: str | None = None
    reason: str = ""
    executable: bool = False
    frame_manifest_path: str | None = None  # MK-CTRL21
    output_dir: str = "output"  # MK-CTRL21
    scene_mp4_path: str | None = None  # MK-CTRL22
    brief_path: str | None = None  # MK-CTRL23
    prompt_pack_path: str | None = None  # MK-GEN2R — Prompt pack path for prompt-pack mode
    generation_mode: str | None = None  # MK-GEN2R — "brief" or "prompt_pack"
    recipe_validation: dict | None = None  # MK-RECIPE3 — Recipe validation report

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "action": self.action,
            "allowed": self.allowed,
            "current_state": self.current_state,
            "expected_next_action": self.expected_next_action,
            "brief_path": self.brief_path,
            "required_inputs": self.required_inputs,
            "missing_inputs": self.missing_inputs,
            "expected_outputs": self.expected_outputs,
            "command_preview": self.command_preview,
            "handler_key": self.handler_key,
            "reason": self.reason,
            "executable": self.executable,
            "frame_manifest_path": self.frame_manifest_path,  # MK-CTRL21
            "output_dir": self.output_dir,  # MK-CTRL21
            "scene_mp4_path": self.scene_mp4_path,  # MK-CTRL22
            "brief_path": self.brief_path,  # MK-CTRL23
            "prompt_pack_path": self.prompt_pack_path,  # MK-GEN2R
            "generation_mode": self.generation_mode,  # MK-GEN2R
            "recipe_validation": self.recipe_validation,  # MK-RECIPE3
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class ShotControlResponse:
    episode_id: str
    shot_id: str
    requested_action: str
    mode: str
    state_report: dict
    gate_decision: dict
    action_plan: dict
    action_result: dict | None
    ledger_enabled: bool
    success: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "requested_action": self.requested_action,
            "mode": self.mode,
            "state_report": self.state_report,
            "gate_decision": self.gate_decision,
            "action_plan": self.action_plan,
            "action_result": self.action_result,
            "ledger_enabled": self.ledger_enabled,
            "success": self.success,
            "reason": self.reason,
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class ShotArtifacts:
    brief_path: str | None = None
    generated_frames: list[str] = field(default_factory=list)
    scene_mp4_path: str | None = None
    scene_audio_wav_path: str | None = None
    scene_mp4_with_audio_path: str | None = None
    final_episode_mp4_path: str | None = None
    manifest_path: str | None = None


@dataclass
class ShotStateReport:
    episode_id: str
    shot_id: str
    current_state: str
    next_action: str
    blocked_reason: str | None = None
    artifact_path: str | None = None  # MK-CTRL21 — Path to artifact from state transition
    brief_path: str | None = None  # MK-CTRL23
    existing_artifacts: ShotArtifacts = field(default_factory=ShotArtifacts)
    missing_artifacts: list[str] = field(default_factory=list)
    generation_required: bool = False
    assembly_required: bool = False
    audio_required: bool = False
    qa_required: bool = False
    is_done: bool = False
    # MK-CTRL37R — Typed artifact paths from persisted state for proper handoff
    frame_manifest_path: str | None = None  # Output of generate_frames
    scene_mp4_path: str | None = None  # Output of assemble_scene, input to qa_review and attach_audio
    qa_report_path: str | None = None  # Output of qa_review
    audio_output_path: str | None = None  # Output of attach_audio, input to render_episode
    episode_output_path: str | None = None  # Output of render_episode
    project_root: str | None = None  # MK-CTRL25 — Project root for visual QA gate

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "shot_id": self.shot_id,
            "current_state": self.current_state,
            "next_action": self.next_action,
            "blocked_reason": self.blocked_reason,
            "artifact_path": self.artifact_path,  # MK-CTRL21
            "brief_path": self.brief_path,  # MK-CTRL23
            "existing_artifacts": {
                "brief_path": self.existing_artifacts.brief_path,
                "generated_frames": self.existing_artifacts.generated_frames,
                "scene_mp4_path": self.existing_artifacts.scene_mp4_path,
                "scene_audio_wav_path": self.existing_artifacts.scene_audio_wav_path,
                "scene_mp4_with_audio_path": self.existing_artifacts.scene_mp4_with_audio_path,
                "final_episode_mp4_path": self.existing_artifacts.final_episode_mp4_path,
                "manifest_path": self.existing_artifacts.manifest_path,
            },
            "missing_artifacts": self.missing_artifacts,
            "generation_required": self.generation_required,
            "assembly_required": self.assembly_required,
            "audio_required": self.audio_required,
            "qa_required": self.qa_required,
            "is_done": self.is_done,
            # MK-CTRL37R — Typed artifact paths
            "frame_manifest_path": self.frame_manifest_path,
            "scene_mp4_path": self.scene_mp4_path,
            "qa_report_path": self.qa_report_path,
            "audio_output_path": self.audio_output_path,
            "episode_output_path": self.episode_output_path,
        }

    def to_json(self) -> str:
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
