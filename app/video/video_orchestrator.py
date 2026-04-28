"""KT-6/KT-7 video orchestrator.

Wires the minimal pipeline:
    input video
      -> extract all frames
      -> select subset (every Nth)
      -> process selected frames (processor: "pil" or "comfy")
      -> assemble processed frames into export.mp4
      -> persist video manifest (including per-frame linkage for comfy)
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.assets.paths import ASSET_PATHS
from app.video.comfy_processor import process_frames_via_comfy
from app.video.frames import assemble_frames, extract_frames, probe_video
from app.video.manifest import VideoManifest, VideoManifestPersistence
from app.video.processor import process_frames_sequential
from app.video.video_intelligence import generate_video_intelligence_report


def _sanitize_video_id(raw: str) -> str:
    """Sanitize a string into a safe lowercase video_id."""
    s = raw.lower()
    s = re.sub(r"[^a-z0-9_\-]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "video"


def derive_video_id(input_path: Path, explicit_id: str | None = None) -> str:
    """Derive a stable video_id. If `explicit_id` is provided, use it (sanitized);
    otherwise derive from the input filename stem + a short timestamp suffix.
    """
    if explicit_id:
        return _sanitize_video_id(explicit_id)
    stem = _sanitize_video_id(input_path.stem)
    suffix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{stem}_{suffix}"


def select_subset(
    frame_paths: list[Path],
    every: int = 5,
    max_frames: int | None = None,
    intelligence_subset: list[int] | None = None,
) -> list[Path]:
    """Select a subset of frames: every Nth, optionally capped at `max_frames`.

    Args:
        frame_paths: List of frame paths
        every: Pick every Nth frame (used when intelligence_subset is None)
        max_frames: Optional cap on frames
        intelligence_subset: Optional list of frame indices from intelligence report

    Returns:
        Selected frame paths
    """
    if intelligence_subset is not None:
        # Use intelligence-driven selection
        selected = [frame_paths[i] for i in intelligence_subset if i < len(frame_paths)]
    else:
        # Use simple "every Nth" selection
        if every < 1:
            every = 1
        selected = [p for i, p in enumerate(frame_paths) if i % every == 0]

    if max_frames is not None and max_frames > 0:
        selected = selected[:max_frames]
    return selected


async def run_video_pipeline(
    input_path: Path,
    video_id: str | None = None,
    extract_fps: float | None = None,
    subset_every: int = 5,
    export_fps: float = 12.0,
    max_processed_frames: int | None = None,
    processor: str = "pil",
    prompt: str | None = None,
    comfy_recipe: dict[str, Any] | None = None,
    intelligence_mode: bool = False,
    multi_scene: bool = False,
) -> dict[str, Any]:
    """Run the full KT-6/KT-7 video pipeline end-to-end.

    Args:
        input_path: Local input video file.
        video_id: Optional explicit id; otherwise derived from input filename.
        extract_fps: Optional override for extraction fps.
        subset_every: Pick every Nth frame from the extracted set.
        export_fps: Output fps for the assembled export.
        max_processed_frames: Optional cap on processed frames (recommended for comfy).
        processor: "pil" (KT-6 plumbing proof) or "comfy" (KT-7 real edit path).
        prompt: Required when processor == "comfy" — the edit prompt.
        comfy_recipe: Optional canonical_recipe overrides forwarded to run_agent
            (e.g. {"width":512,"height":512,"steps":15,"cfg":6.0,
            "sampler_name":"dpmpp_2m","scheduler":"karras"}).
        intelligence_mode: If True, use intelligence-driven subset selection (v1.1).
        multi_scene: If True, use multi-scene detection with per-scene decisions (v1.1 Layer 2).

    Returns:
        A dict with video_id, all artifact paths, manifest_path, and the
        per_frame linkage list when processor == "comfy".
    """
    if processor not in {"pil", "comfy"}:
        raise ValueError(f"Unknown processor: {processor}. Use 'pil' or 'comfy'.")
    if processor == "comfy" and not prompt:
        raise ValueError("processor='comfy' requires a non-empty prompt for the edit path.")
    input_path = Path(input_path).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input video not found: {input_path}")

    vid = video_id or derive_video_id(input_path)
    video_dir = ASSET_PATHS.video_dir(vid)
    frames_dir = video_dir / "frames"
    processed_dir = video_dir / "processed"
    export_path = video_dir / "export.mp4"

    video_dir.mkdir(parents=True, exist_ok=True)

    persistence = VideoManifestPersistence(ASSET_PATHS.manifests)
    manifest = VideoManifest(
        video_id=vid,
        input_path=str(input_path),
        video_dir=video_dir,
    )
    persistence.save(manifest)

    # Intelligence report path
    intelligence_report_path = video_dir / "intelligence_report.json"
    intelligence_subset = None

    try:
        # 1. Probe input
        probe = probe_video(input_path)
        manifest.set_probe(probe)
        persistence.save(manifest)

        # 2. Extract all frames
        frame_count = extract_frames(input_path, frames_dir, fps=extract_fps)
        manifest.set_extraction(frames_dir, frame_count, extract_fps)
        persistence.save(manifest)

        all_frames = sorted(frames_dir.glob("frame_*.png"))
        if not all_frames:
            raise RuntimeError("No frames were extracted from the input video")

        # 3. Generate intelligence report if in intelligence mode (v1.1)
        if intelligence_mode:
            intelligence_report = generate_video_intelligence_report(
                video_id=vid,
                frames_dir=frames_dir,
                fps=probe.get("fps", extract_fps or 30.0),
                max_processed_frames=max_processed_frames,
                multi_scene=multi_scene,
            )
            intelligence_report.save(intelligence_report_path)
            intelligence_subset = intelligence_report.selected_subset
            selection_strategy = f"intelligence_v1_multi_scene" if multi_scene else "intelligence_v1"
        else:
            selection_strategy = f"every_{subset_every}" + (f"_cap_{max_processed_frames}" if max_processed_frames else "")

        # 4. Select subset
        selected = select_subset(
            all_frames,
            every=subset_every,
            max_frames=max_processed_frames,
            intelligence_subset=intelligence_subset,
        )
        if not selected:
            raise RuntimeError("Frame selection produced zero frames")
        manifest.set_selection(
            selected=[p.name for p in selected],
            strategy=selection_strategy,
        )
        persistence.save(manifest)

        # 4. Process selected frames
        per_frame_linkage: list[dict[str, Any]] = []
        if processor == "pil":
            processed_paths = process_frames_sequential(selected, processed_dir)
            processor_name = "autocontrast+sharpen_1.3"
            processed_count = len(processed_paths)
            manifest.set_processing(
                processed_dir=processed_dir,
                processed_count=processed_count,
                processor=processor_name,
            )
        else:  # processor == "comfy"
            per_frame_linkage = await process_frames_via_comfy(
                selected_paths=selected,
                processed_dir=processed_dir,
                prompt=prompt or "",
                comfy_recipe=comfy_recipe,
            )
            processor_name = "comfy_img2img_v1"
            processed_count = sum(1 for e in per_frame_linkage if e.get("processed_frame"))
            manifest.set_processing(
                processed_dir=processed_dir,
                processed_count=processed_count,
                processor=processor_name,
                per_frame=per_frame_linkage,
                prompt=prompt,
                recipe=comfy_recipe,
            )
        persistence.save(manifest)

        if processed_count == 0:
            raise RuntimeError(
                f"Processor '{processor_name}' produced zero processed frames"
            )

        # 5. Renumber successful processed frames contiguously for ffmpeg assembly.
        #    (comfy may have some failed entries; PIL always produces contiguous output.)
        if processor == "comfy":
            _compact_processed_dir(processed_dir)

        # 6. Assemble into export.mp4
        assemble_frames(processed_dir, export_path, fps=export_fps)
        manifest.set_export(export_path, fps=export_fps)

        manifest.complete()
        persistence.save(manifest)

        return {
            "status": "completed",
            "video_id": vid,
            "video_dir": str(video_dir),
            "input_path": str(input_path),
            "frames_dir": str(frames_dir),
            "frames_extracted": frame_count,
            "processed_dir": str(processed_dir),
            "processed_count": processed_count,
            "export_path": str(export_path),
            "manifest_path": str(ASSET_PATHS.video_manifest_path(vid)),
            "intelligence_report_path": str(intelligence_report_path) if intelligence_mode else None,
            "processor": processor_name,
            "per_frame": per_frame_linkage,
        }

    except Exception as exc:
        manifest.fail(str(exc))
        persistence.save(manifest)
        raise


def _compact_processed_dir(processed_dir: Path) -> None:
    """Ensure processed frames are contiguous frame_000001..N.

    Sorts the existing frame_*.png files and rewrites them as a contiguous
    sequence starting from 1. Used after the comfy path in case any frame
    failed and left a gap.
    """
    existing = sorted(processed_dir.glob("frame_*.png"))
    if not existing:
        return
    # Move to temp names first to avoid overwrite collisions.
    tmp_names: list[Path] = []
    for i, src in enumerate(existing, start=1):
        tmp = processed_dir / f".tmp_{i:06d}.png"
        src.rename(tmp)
        tmp_names.append(tmp)
    for i, tmp in enumerate(tmp_names, start=1):
        tmp.rename(processed_dir / f"frame_{i:06d}.png")
