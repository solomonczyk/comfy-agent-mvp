"""MK-CTRL1 — Shot orchestration state controller.  Inspect-only, never executes."""
from __future__ import annotations

import time
from pathlib import Path

from .models import ShotArtifacts, ShotStateReport
from .shot_state_storage import ShotStateStorage


class ShotController:
    def __init__(self, project_root: Path | str) -> None:
        self.root = Path(project_root)
        self.state_storage = ShotStateStorage(project_root)

    # ── public API ────────────────────────────────────────────────────

    def inspect(self, episode_id: str, shot_id: str) -> ShotStateReport:
        # MK-CTRL19 — Read from state persistence first
        persisted_state = self.state_storage.load(episode_id, shot_id)
        if persisted_state:
            # Return report based on persisted state
            artifacts = self._discover_artifacts(episode_id, shot_id)
            return self._report_from_persisted_state(persisted_state, artifacts)
        
        # Fall back to artifact-based inspection
        artifacts = self._discover_artifacts(episode_id, shot_id)
        brief_text = self._load_brief_text(artifacts.brief_path)
        audio_required = self._audio_required(brief_text)

        blocked = self._detect_corruption(artifacts, episode_id, shot_id)
        if blocked:
            return self._report(episode_id, shot_id, "blocked", "none",
                                artifacts, blocked_reason=blocked)

        if not artifacts.brief_path:
            return self._report(episode_id, shot_id, "missing_brief", "create_brief", artifacts)

        if not artifacts.generated_frames and not artifacts.scene_mp4_path:
            return self._report(episode_id, shot_id, "ready_for_generation",
                                "generate_frames", artifacts, generation_required=True)

        if artifacts.generated_frames and not artifacts.scene_mp4_path:
            return self._report(episode_id, shot_id, "partial_generation",
                                "continue_generation", artifacts, generation_required=True)

        if audio_required and not artifacts.scene_mp4_with_audio_path:
            return self._report(episode_id, shot_id, "ready_for_audio",
                                "synthesize_and_mux_audio", artifacts,
                                assembly_required=True, audio_required=True)

        if not artifacts.final_episode_mp4_path:
            return self._report(episode_id, shot_id, "ready_for_final_episode",
                                "assemble_episode", artifacts,
                                assembly_required=True, audio_required=audio_required)

        if not self._find_qa_marker(episode_id, shot_id):
            return self._report(episode_id, shot_id, "ready_for_qa",
                                "run_qa", artifacts, qa_required=True)

        return self._report(episode_id, shot_id, "done", "none",
                            artifacts, is_done=True)

    # ── helpers ───────────────────────────────────────────────────────

    def _discover_artifacts(self, episode_id: str, shot_id: str) -> ShotArtifacts:
        a = ShotArtifacts()
        for p in [
            self.root / f"data/briefs/{episode_id}_{shot_id}_brief.md",
            self.root / f"data/briefs/{shot_id}_brief.md",
            self.root / f"data/{shot_id}_brief.md",
        ]:
            if p.exists() and p.stat().st_size > 0:
                a.brief_path = str(p)
                break

        out = self.root / "output"
        if out.exists():
            frames = []
            for d in out.rglob("*"):
                if d.is_dir():
                    for f in d.glob(f"{shot_id}*.png"):
                        if f.stat().st_size > 0:
                            frames.append(str(f))
            a.generated_frames = sorted(frames)
            # RC-FLOW1D — Also check scenes directory for scene.mp4
            # Check both {episode_id}_{shot_id} and {shot_id} patterns
            for shot_dir_name in [f"{episode_id}_{shot_id}", shot_id]:
                scenes_dir = out / "scenes" / shot_dir_name
                scene_mp4 = scenes_dir / "scene.mp4"
                if scene_mp4.exists() and scene_mp4.stat().st_size > 0:
                    a.scene_mp4_path = str(scene_mp4)
                    break
            if not a.scene_mp4_path:
                # Fallback to original scan
                for f in out.rglob("*.mp4"):
                    if f.stat().st_size == 0:
                        continue
                    n = f.stem
                    if (n == shot_id or n.startswith(f"{shot_id}_")) and "with_audio" not in n:
                        a.scene_mp4_path = str(f)
                        break
            for f in out.rglob("*.mp4"):
                if f.stat().st_size == 0:
                    continue
                if f"{shot_id}_with_audio" in f.name or f"{shot_id}-with-audio" in f.name:
                    a.scene_mp4_with_audio_path = str(f)
                    break
            for f in out.rglob("*.wav"):
                if shot_id in f.name and f.stat().st_size > 0:
                    a.scene_audio_wav_path = str(f)
                    break
        ep = self.root / "output/episodes"
        if ep.exists():
            for f in ep.glob("*.mp4"):
                if episode_id.lower() in f.name.lower() and f.stat().st_size > 0:
                    a.final_episode_mp4_path = str(f)
                    break
        for p in [
            self.root / f"output/{episode_id}/manifest.json",
            self.root / f"output/{episode_id}_{shot_id}/manifest.json",
            self.root / "output/manifest.json",
        ]:
            if p.exists() and p.stat().st_size > 0:
                a.manifest_path = str(p)
                break
        return a

    def _load_brief_text(self, path: str | None) -> str:
        if not path:
            return ""
        p = Path(path)
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def _audio_required(self, text: str) -> bool:
        if not text:
            return False
        for line in text.splitlines():
            low = line.lower().lstrip("- ")
            if low.startswith("dialogue:") or low.startswith("subtitles:"):
                after = line.split(":", 1)[1].strip()
                if after and after.lower() not in ("none", "null", "n/a", "", "no"):
                    return True
        return False

    def _find_qa_marker(self, episode_id: str, shot_id: str) -> Path | None:
        for p in [
            self.root / f"output/{episode_id}_{shot_id}/qa.json",
            self.root / f"output/{episode_id}_{shot_id}/qa_passed",
            self.root / "output/qa.json",
            self.root / "output/qa_passed",
        ]:
            if p.exists() and p.stat().st_size > 0:
                return p
        return None

    def _detect_corruption(self, a: ShotArtifacts, episode_id: str, shot_id: str) -> str | None:
        out = self.root / "output"
        if out.exists():
            for pattern in [f"{shot_id}*.mp4", f"{shot_id}*.wav", f"{shot_id}*.png"]:
                for p in out.rglob(pattern):
                    if p.exists() and p.stat().st_size == 0:
                        return f"zero-byte file: {p.name}"
        for field_name in ["brief_path", "manifest_path"]:
            val = getattr(a, field_name)
            if val:
                p = Path(val)
                if p.exists() and p.stat().st_size == 0:
                    return f"zero-byte file: {field_name}"
        if a.scene_mp4_with_audio_path and not a.scene_mp4_path:
            return "scene_mp4 missing but scene_mp4_with_audio exists"
        if a.final_episode_mp4_path and not a.scene_mp4_path:
            return "final_episode exists but no scene_mp4"
        if a.manifest_path and not a.brief_path:
            return "manifest exists but brief missing"
        return None

    def _report(
        self,
        episode_id: str, shot_id: str,
        state: str, action: str,
        artifacts: ShotArtifacts,
        blocked_reason: str | None = None,
        generation_required: bool = False,
        assembly_required: bool = False,
        audio_required: bool = False,
        qa_required: bool = False,
        is_done: bool = False,
    ) -> ShotStateReport:
        missing: list[str] = []
        if not artifacts.brief_path:
            missing.append("brief")
        elif not artifacts.generated_frames:
            missing.append("generated_frames")
        elif not artifacts.scene_mp4_path:
            missing.append("scene_mp4")
        if audio_required and not artifacts.scene_audio_wav_path:
            missing.append("scene_audio_wav")
        if audio_required and not artifacts.scene_mp4_with_audio_path:
            missing.append("scene_mp4_with_audio")
        if not artifacts.final_episode_mp4_path:
            missing.append("final_episode_mp4")
        if not artifacts.manifest_path:
            missing.append("manifest")
        if qa_required and not self._find_qa_marker(episode_id, shot_id):
            missing.append("qa_marker")
        return ShotStateReport(
            episode_id=episode_id,
            shot_id=shot_id,
            current_state=state,
            next_action=action,
            blocked_reason=blocked_reason,
            artifact_path=None,  # MK-CTRL21 — No artifact_path for artifact-based inspection
            brief_path=artifacts.brief_path,  # MK-CTRL27 — Set brief_path from artifacts
            existing_artifacts=artifacts,
            missing_artifacts=missing,
            generation_required=generation_required,
            assembly_required=assembly_required,
            audio_required=audio_required,
            qa_required=qa_required,
            is_done=is_done,
        )

    def _report_from_persisted_state(
        self,
        persisted_state: ShotState,
        artifacts: ShotArtifacts,
    ) -> ShotStateReport:
        """Generate state report from persisted state.

        MK-CTRL19 — When state is persisted, use it instead of artifact inspection.
        This allows controlled state transitions after accepted artifacts.
        MK-CTRL22 — Added qa_passed and qa_failed state transitions.
        MK-CTRL37R — Populate typed artifact paths from persisted state for proper handoff.
        """
        # Determine next action based on current state
        state = persisted_state.current_state
        if state == "frames_generated":
            next_action = "assemble_scene"  # or whatever the next step is
        elif state == "scene_assembled":
            next_action = "qa_review"  # MK-CTRL22
        elif state == "qa_passed":
            next_action = "attach_audio"  # MK-CTRL22
        elif state == "audio_attached":
            next_action = "render_episode"  # MK-CTRL23
        elif state == "episode_rendered":
            next_action = "none"  # MK-CTRL24 - episode_rendered is terminal state
        elif state == "qa_failed":
            next_action = "generate_frames"  # MK-CTRL22
        elif state == "ready_for_generation":
            next_action = "generate_frames"
        elif state == "partial_generation":
            next_action = "continue_generation"
        elif state == "ready_for_audio":
            next_action = "synthesize_and_mux_audio"
        elif state == "ready_for_final_episode":
            next_action = "assemble_episode"
        elif state == "ready_for_qa":
            next_action = "run_qa"
        elif state == "done":
            next_action = "none"
        elif state == "blocked":
            next_action = "none"
        elif state == "missing_brief":
            next_action = "create_brief"
        else:
            next_action = "none"

        return ShotStateReport(
            episode_id=persisted_state.episode_id,
            shot_id=persisted_state.shot_id,
            current_state=state,
            next_action=next_action,
            blocked_reason=None,
            artifact_path=persisted_state.artifact_path,  # MK-CTRL21 — Include artifact_path from persisted state
            brief_path=persisted_state.brief_path,  # MK-CTRL23
            existing_artifacts=artifacts,
            missing_artifacts=[],  # Could derive from artifacts if needed
            generation_required=state in ["ready_for_generation", "partial_generation"],
            assembly_required=state in ["ready_for_audio", "ready_for_final_episode"],
            audio_required=state == "ready_for_audio",
            qa_required=state == "ready_for_qa",
            is_done=state in ["done", "episode_rendered"],  # MK-CTRL24 - episode_rendered is terminal
            # MK-CTRL37R — Typed artifact paths from persisted state
            frame_manifest_path=persisted_state.frame_manifest_path,
            scene_mp4_path=persisted_state.scene_mp4_path,
            qa_report_path=persisted_state.qa_report_path,
            audio_output_path=persisted_state.audio_output_path,
            episode_output_path=persisted_state.episode_output_path,
            project_root=str(self.root),  # MK-CTRL25 — Pass project_root for visual QA gate
        )
