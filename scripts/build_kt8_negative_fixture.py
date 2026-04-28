"""Build a synthetic negative-case video fixture for KT-8 QC.

Takes the existing real KT-7 proof directory + manifest and clones it under
a new ``video_id``, then degrades exactly ONE processed frame to a fully
black PNG. This is a minimum-impact degradation that:

    - leaves the export.mp4 untouched (export check still passes)
    - leaves the on-disk count == manifest count (count check passes)
    - leaves per-frame sizes roughly similar (size check passes)
    - introduces a single black frame (25% of 4) which is:
        * strictly greater than 0          -> triggers ``retry:black_frames``
        * not > 50% of frames              -> does NOT escalate to reject

Running ``app.video_qc_run --video-id kt8_neg_proof_001`` should therefore
produce ``verdict == retry``.

Does not alter the original KT-7 fixture.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image

from app.assets.paths import ASSET_PATHS


SOURCE_VIDEO_ID = "kt7_proof_001"
TARGET_VIDEO_ID = "kt8_neg_proof_001"
BLACK_FRAME_INDEX = 2  # frame_000002.png in the cloned processed dir


def _update_paths_in_manifest(manifest: dict, src_dir: Path, dst_dir: Path) -> dict:
    """Rewrite absolute paths inside a manifest dict to match the new target dir.

    Only performs path string replacement for strings that start with the
    source dir (case-insensitive on Windows). Paths outside the cloned
    directory (e.g. per_frame source_frame paths that point at the original
    KT-7 frames dir) are left intact — they still resolve and are useful
    context.
    """
    src_prefix = str(src_dir)
    dst_prefix = str(dst_dir)

    def _rewrite(value):
        if isinstance(value, str):
            if value.lower().startswith(src_prefix.lower()):
                return dst_prefix + value[len(src_prefix):]
            return value
        if isinstance(value, list):
            return [_rewrite(v) for v in value]
        if isinstance(value, dict):
            return {k: _rewrite(v) for k, v in value.items()}
        return value

    return _rewrite(manifest)


def main() -> None:
    src_video_dir = ASSET_PATHS.video_dir(SOURCE_VIDEO_ID)
    dst_video_dir = ASSET_PATHS.video_dir(TARGET_VIDEO_ID)

    if not src_video_dir.exists():
        raise SystemExit(
            f"source video dir missing: {src_video_dir}\n"
            f"Run the KT-7 proof first, or pick a different SOURCE_VIDEO_ID."
        )

    src_manifest_path = ASSET_PATHS.video_manifest_path(SOURCE_VIDEO_ID)
    if not src_manifest_path.exists():
        raise SystemExit(f"source manifest missing: {src_manifest_path}")

    # Clone the video dir (frames + processed + export.mp4).
    if dst_video_dir.exists():
        shutil.rmtree(dst_video_dir)
    shutil.copytree(src_video_dir, dst_video_dir)

    # Degrade exactly one processed frame: overwrite with a solid-black PNG
    # of identical dimensions so the size-mismatch check doesn't also fire.
    processed_dir = dst_video_dir / "processed"
    target_frame = processed_dir / f"frame_{BLACK_FRAME_INDEX:06d}.png"
    if not target_frame.exists():
        raise SystemExit(f"target frame missing in clone: {target_frame}")

    with Image.open(target_frame) as img:
        w, h = img.size
    Image.new("RGB", (w, h), (0, 0, 0)).save(target_frame, format="PNG")
    print(f"[kt8-neg] blackened frame: {target_frame} ({w}x{h})")

    # Clone + rewrite the main video manifest (strip any pre-existing qc
    # linkage from KT-7; QC will repopulate it on the next run).
    with open(src_manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["video_id"] = TARGET_VIDEO_ID
    manifest = _update_paths_in_manifest(manifest, src_video_dir, dst_video_dir)
    manifest.pop("qc", None)

    dst_manifest_path = ASSET_PATHS.video_manifest_path(TARGET_VIDEO_ID)
    dst_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dst_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[kt8-neg] wrote manifest: {dst_manifest_path}")
    print(f"[kt8-neg] video_id:       {TARGET_VIDEO_ID}")
    print(
        "[kt8-neg] run:           "
        "python -m app.video_qc_run --video-id kt8_neg_proof_001"
    )


if __name__ == "__main__":
    main()
