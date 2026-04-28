"""MK-F1 — ExecutionRunner.

Wires the full stack: Pipeline → ComfySubmitter → FrameAssembler → EpisodeRenderer.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.audio.mux import SceneAudioMuxer
from app.audio.scene_audio import SceneAudioBuilder
from app.comfy.exceptions import ComfySubmitError, ComfyTimeoutError
from app.comfy.models import SubmitResult
from app.comfy.submitter import ComfySubmitter
from app.episode.models import Episode
from app.brief.parser import BriefParser
from app.pipeline import Pipeline, PipelineConfig
from app.render.episode_renderer import EpisodeRenderer
from app.render.frame_assembler import FrameAssembler


class ExecutionRunner:
    def __init__(
        self,
        config: PipelineConfig,
        comfy_host: str = "127.0.0.1",
        comfy_port: int = 8188,
        workflow_template: dict | None = None,
        checkpoint: str | None = None,
        lowvram: bool = True,
    ) -> None:
        self.config = config
        self.comfy_host = comfy_host
        self.comfy_port = comfy_port
        self.checkpoint = checkpoint
        self.lowvram = lowvram
        if workflow_template is None:
            with open("data/workflow_template.json", encoding="utf-8") as f:
                workflow_template = json.load(f)
        self.workflow_template = workflow_template

    def run(
        self,
        brief_source: str | dict,
        output_dir: str | Path = "output",
        scene_ids: list[str] | None = None,
    ) -> Path:
        output_dir = Path(output_dir)
        print("[1/4] Parsing brief...")
        pipeline = Pipeline(self.config)
        episode = pipeline.run(
            brief_source,
            output_dir=output_dir,
            comfy_host=self.comfy_host,
            comfy_port=self.comfy_port,
            checkpoint=self.checkpoint,
        )
        reference_paths: dict[str, Path] = getattr(episode, "reference_paths", {})

        scenes = episode.scenes
        if scene_ids is not None:
            scenes = [s for s in scenes if s.scene_id in scene_ids]
            if not scenes:
                raise RuntimeError(f"No scenes matched filter: {scene_ids}")
            print(f"  Filtered to {len(scenes)} scene(s): {[s.scene_id for s in scenes]}")

        print(f"[2/4] Submitting {len(scenes)} scene(s) to ComfyUI...")
        submitter = ComfySubmitter(
            host=self.comfy_host,
            port=self.comfy_port,
            checkpoint=self.checkpoint,
            lowvram=self.lowvram,
        )
        submitter.flush_queue()
        submit_results: list[SubmitResult] = []
        scene_timings: dict[str, float] = {}
        run_start = time.time()
        for idx, scene in enumerate(scenes):
            print(f"\n[SCENE {idx+1}/{len(episode.scenes)}] {scene.scene_id}  ref={ref_path if 'ref_path' in dir() else None}")
            ref_path = None
            if reference_paths and hasattr(scene, "characters_in_scene"):
                for char_name in (scene.characters_in_scene or []):
                    if char_name in reference_paths:
                        ref_path = reference_paths[char_name]
                        break
            t0 = time.time()
            try:
                result = submitter.submit(
                    scene,
                    self.workflow_template,
                    timeout_sec=3600,
                    reference_image_path=ref_path,
                    reference_weight=self.config.reference_weight,
                )
                elapsed = time.time() - t0
                scene_timings[scene.scene_id] = elapsed
                print(f"  [OK] {len(result.frame_paths)} frames in {elapsed:.1f}s")
                submit_results.append(result)
            except (ComfySubmitError, ComfyTimeoutError) as exc:
                elapsed = time.time() - t0
                scene_timings[scene.scene_id] = elapsed
                print(f"  ERROR: {exc}  ({elapsed:.1f}s)")
                raise

        print("\n=== SCENE TIMING SUMMARY ===")
        for sid, t in scene_timings.items():
            print(f"  {sid}: {t:.1f}s")
        print(f"  Total wall time: {time.time()-run_start:.1f}s")

        print("[3/4] Assembling per-scene MP4s...")
        assembler = FrameAssembler()
        audio_builder = SceneAudioBuilder()
        muxer = SceneAudioMuxer()
        audio_dir = output_dir / "audio"
        scene_mp4s: list[Path] = []
        for result in submit_results:
            scene = next(s for s in scenes if s.scene_id == result.scene_id)
            print(f"  Assembling scene {result.scene_id} ({len(result.frame_paths)} frames)...")
            mp4_path = assembler.assemble(
                scene_id=result.scene_id,
                frame_paths=result.frame_paths,
                fps=scene.fps,
                aspect_ratio=episode.aspect_ratio,
            )

            wav_path = audio_builder.synthesize_scene(scene, output_dir=audio_dir)
            if wav_path is not None:
                muxed_path = mp4_path.parent / f"{result.scene_id}_with_audio.mp4"
                mp4_path = muxer.mux(mp4_path, wav_path, muxed_path)
                print(f"  [audio] scene {result.scene_id} -> muxed")
            else:
                print(f"  [audio] scene {result.scene_id} -> skipped (no dialogue)")

            scene_mp4s.append(mp4_path)

        print("[4/4] Rendering final episode...")
        renderer = EpisodeRenderer()
        final_path = renderer.render(episode.title, scene_mp4s)

        # Write manifest
        brief = BriefParser().parse(brief_source)
        manifest = {
            "episode_id": brief.meta.episode_id,
            "shot_id": brief.meta.shot_id,
            "title": brief.meta.title,
            "duration_sec": brief.meta.target_duration_sec,
            "aspect_ratio": brief.meta.aspect_ratio,
            "fps": brief.meta.fps,
            "dialogue_present": any(s.dialogue for s in brief.scenes if s.dialogue),
            "subtitles_present": any(s.subtitles for s in brief.scenes if s.subtitles),
            "continuity_out": brief.scenes[0].continuity_out if brief.scenes else None,
            "output_clip_path": str(final_path),
            "scene_mp4s": [str(p) for p in scene_mp4s],
            "total_scenes": len(episode.scenes),
            "rendered_scenes": len(scene_mp4s),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Manifest saved: {manifest_path}")

        return final_path
