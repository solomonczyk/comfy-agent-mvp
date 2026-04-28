"""KT-8 Minimal Video QC v1.

First practical video quality gate. Classifies a processed video export
produced by the KT-6/KT-7 pipeline as one of:

    - ``accept`` : all checks passed
    - ``retry``  : soft defects (recoverable by re-running)
    - ``reject`` : hard defects (output is unusable)

Intentionally narrow scope (non-goals, enforced by KT-8):
    - no montage
    - no advanced temporal / optical-flow scoring
    - no checkpoint comparison
    - no modification of the KT-6/KT-7 video structure

Checks (all deterministic, PIL + stdlib only):
    1. broken / missing export                (hard -> reject)
    2. missing processed frames               (hard -> reject)
    3. black / blank frames                   (soft -> retry, majority -> reject)
    4. frame count mismatch                   (soft -> retry)
    5. severe per-frame size mismatch         (soft -> retry)
    6. obvious repeated-frame / frozen output (soft -> retry)

The QC report is persisted as its own JSON file at
``data/manifests/video_qc_{video_id}.json`` and the main video manifest at
``data/manifests/video_{video_id}.json`` is updated with a compact ``qc``
section that points at the full report.
"""
from __future__ import annotations

import json
import statistics
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat

from app.assets.paths import ASSET_PATHS
from app.video.frames import probe_video


# --------------------------------------------------------------------------- #
# Tunables (kept conservative; KT-8 explicitly avoids advanced scoring).
# --------------------------------------------------------------------------- #

# Black / blank frame thresholds (matching app/judges/local_qc_judge.py
# heuristic: very dark OR near-uniform).
BLACK_MEAN_MAX = 10.0
BLACK_STD_MAX = 5.0

# Majority-black reject threshold (0.5 -> strictly more than half).
BLACK_MAJORITY_RATIO = 0.5

# Per-frame size mismatch: a frame is "severe" if its size is <1/4 or >4x the
# median of all processed frames' sizes.
SIZE_LOW_FACTOR = 0.25
SIZE_HIGH_FACTOR = 4.0
# RETRY if at least this many frames are severe, OR the ratio exceeds this.
SIZE_MISMATCH_MIN_COUNT = 2
SIZE_MISMATCH_RATIO = 0.25

# Frozen-output heuristic: a consecutive run of >= this many identical
# perceptual hashes is the minimum we consider suspicious. RETRY requires that
# AND the run covers at least this ratio of total frames.
FROZEN_RUN_MIN_LEN = 3
FROZEN_RUN_MIN_RATIO = 0.5

# Frame-count mismatch tolerance between export's probed frame_count and the
# number of processed frames on disk. ffmpeg assembly with libx264 pad can
# drift by at most 1 frame for very short clips; anything beyond is a RETRY.
FRAME_COUNT_TOLERANCE = 1

# Perceptual hash size used for the frozen-frame check. Small grid keeps it
# cheap and also robust to trivial noise between near-identical outputs.
DHASH_SIZE = 8


# --------------------------------------------------------------------------- #
# Low-level primitives.
# --------------------------------------------------------------------------- #

def _grayscale_stats(path: Path) -> tuple[float, float]:
    """Return (mean, stddev) of the luminance channel for a PNG frame."""
    with Image.open(path) as img:
        gray = img.convert("L")
        stat = ImageStat.Stat(gray)
        return float(stat.mean[0]), float(stat.stddev[0])


def _is_black_or_blank(mean: float, std: float) -> bool:
    """True if a frame is black/near-black or almost uniform (blank)."""
    return mean < BLACK_MEAN_MAX or std < BLACK_STD_MAX


def _dhash(path: Path, hash_size: int = DHASH_SIZE) -> str:
    """Compute a tiny difference-hash (dhash) for a frame.

    Downsample to ``(hash_size+1, hash_size)`` grayscale and compare each
    pixel to its right neighbour. Stable across minor compression noise and
    perfect for spotting frozen / repeated frames.
    """
    with Image.open(path) as img:
        small = img.convert("L").resize(
            (hash_size + 1, hash_size), Image.Resampling.LANCZOS
        )
    pixels = list(small.getdata())
    w = hash_size + 1
    bits: list[str] = []
    for row in range(hash_size):
        for col in range(hash_size):
            left = pixels[row * w + col]
            right = pixels[row * w + col + 1]
            bits.append("1" if left > right else "0")
    return "".join(bits)


def _max_consecutive_run(items: list[str]) -> int:
    """Return the longest run of identical consecutive entries in ``items``."""
    if not items:
        return 0
    best = cur = 1
    for i in range(1, len(items)):
        if items[i] == items[i - 1]:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 1
    return best


def _probe_export(export_path: Path) -> tuple[bool, dict[str, Any], str | None]:
    """Probe an export video. Returns (ok, probe_dict, error_msg)."""
    if not export_path.exists():
        return False, {}, f"export file not found: {export_path}"
    try:
        size = export_path.stat().st_size
    except OSError as exc:
        return False, {}, f"stat failed: {exc}"
    if size == 0:
        return False, {"size_bytes": 0}, "export file is empty (0 bytes)"
    try:
        probe = probe_video(export_path)
    except subprocess.CalledProcessError as exc:
        return False, {"size_bytes": size}, f"ffprobe failed: {exc.stderr or exc}"
    except Exception as exc:  # pragma: no cover - defensive
        return False, {"size_bytes": size}, f"probe raised: {exc}"
    probe["size_bytes"] = size
    return True, probe, None


# --------------------------------------------------------------------------- #
# Manifest loading.
# --------------------------------------------------------------------------- #

def _resolve_manifest_path(
    manifest_path: Path | None,
    video_id: str | None,
) -> Path:
    if manifest_path is None and video_id is None:
        raise ValueError("Provide either manifest_path or video_id")
    if manifest_path is not None:
        return Path(manifest_path).resolve()
    return ASSET_PATHS.video_manifest_path(video_id).resolve()  # type: ignore[arg-type]


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Video manifest not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# Per-frame analysis.
# --------------------------------------------------------------------------- #

def _analyse_frames(processed_dir: Path) -> list[dict[str, Any]]:
    """Walk processed_dir and compute per-frame QC signals.

    Returns a list ordered by the on-disk contiguous naming
    (frame_000001.png, frame_000002.png, ...). Each entry contains
    index, filename, size_bytes, mean, std, is_black, dhash.
    """
    entries: list[dict[str, Any]] = []
    for i, frame_path in enumerate(sorted(processed_dir.glob("frame_*.png")), start=1):
        try:
            size_bytes = frame_path.stat().st_size
        except OSError:
            size_bytes = 0
        entry: dict[str, Any] = {
            "index": i,
            "filename": frame_path.name,
            "path": str(frame_path),
            "size_bytes": size_bytes,
            "mean": None,
            "std": None,
            "is_black": False,
            "dhash": None,
            "error": None,
        }
        if size_bytes == 0:
            entry["error"] = "zero-byte frame"
            entry["is_black"] = True  # treat as black/broken
            entries.append(entry)
            continue
        try:
            mean, std = _grayscale_stats(frame_path)
            entry["mean"] = round(mean, 3)
            entry["std"] = round(std, 3)
            entry["is_black"] = _is_black_or_blank(mean, std)
            entry["dhash"] = _dhash(frame_path)
        except Exception as exc:  # pragma: no cover - defensive
            entry["error"] = f"analyse failed: {exc}"
            entry["is_black"] = True
        entries.append(entry)
    return entries


# --------------------------------------------------------------------------- #
# Verdict computation.
# --------------------------------------------------------------------------- #

def _evaluate_checks(
    manifest: dict[str, Any],
    per_frame: list[dict[str, Any]],
    export_ok: bool,
    export_probe: dict[str, Any],
    export_error: str | None,
) -> tuple[dict[str, dict[str, Any]], str, list[str]]:
    """Run each QC check and return (checks, verdict, reasons)."""
    processing = manifest.get("processing") or {}
    selection = manifest.get("selection") or {}
    manifest_processed_count = int(processing.get("processed_count") or 0)
    manifest_selected_count = int(selection.get("selected_count") or 0)

    total_frames = len(per_frame)
    checks: dict[str, dict[str, Any]] = {}

    # --- 1. Broken / missing export --------------------------------------- #
    checks["export_broken"] = {
        "passed": export_ok,
        "detail": export_error if not export_ok else "export ok",
        "size_bytes": export_probe.get("size_bytes"),
    }

    # --- 2. Missing processed frames -------------------------------------- #
    # Reject if zero on disk; retry if fewer on disk than expected.
    missing_severity: str | None = None
    expected = max(manifest_processed_count, manifest_selected_count)
    if total_frames == 0:
        missing_severity = "reject"
        missing_detail = "no processed frames found on disk"
    elif expected and total_frames < expected:
        missing_severity = "retry"
        missing_detail = (
            f"on-disk processed frames ({total_frames}) "
            f"< expected ({expected})"
        )
    else:
        missing_detail = f"{total_frames} processed frames on disk"
    checks["missing_processed_frames"] = {
        "passed": missing_severity is None,
        "severity": missing_severity,
        "on_disk_count": total_frames,
        "expected_count": expected,
        "detail": missing_detail,
    }

    # --- 3. Black / blank frames ------------------------------------------ #
    black_indices = [e["index"] for e in per_frame if e.get("is_black")]
    black_count = len(black_indices)
    black_ratio = (black_count / total_frames) if total_frames else 0.0
    if total_frames == 0:
        black_severity = None  # covered by missing_processed_frames
    elif black_ratio > BLACK_MAJORITY_RATIO:
        black_severity = "reject"
    elif black_count > 0:
        black_severity = "retry"
    else:
        black_severity = None
    checks["black_frames"] = {
        "passed": black_severity is None,
        "severity": black_severity,
        "black_count": black_count,
        "black_ratio": round(black_ratio, 3),
        "black_indices": black_indices,
    }

    # --- 4. Frame count mismatch ----------------------------------------- #
    # Compare on-disk processed frames to: (a) manifest processed_count,
    # and (b) export nb_frames probed from ffprobe.
    export_frame_count = int(export_probe.get("frame_count") or 0) if export_ok else 0
    manifest_mismatch = (
        manifest_processed_count
        and total_frames
        and abs(total_frames - manifest_processed_count) > FRAME_COUNT_TOLERANCE
    )
    export_mismatch = (
        export_ok
        and export_frame_count
        and total_frames
        and abs(total_frames - export_frame_count) > FRAME_COUNT_TOLERANCE
    )
    fc_severity = "retry" if (manifest_mismatch or export_mismatch) else None
    checks["frame_count_mismatch"] = {
        "passed": fc_severity is None,
        "severity": fc_severity,
        "on_disk_count": total_frames,
        "manifest_processed_count": manifest_processed_count,
        "export_frame_count": export_frame_count,
        "tolerance": FRAME_COUNT_TOLERANCE,
    }

    # --- 5. Severe per-frame size mismatch -------------------------------- #
    sizes = [e["size_bytes"] for e in per_frame if e.get("size_bytes")]
    size_mismatch_indices: list[int] = []
    median_size = 0
    if sizes:
        median_size = int(statistics.median(sizes))
        lo = median_size * SIZE_LOW_FACTOR
        hi = median_size * SIZE_HIGH_FACTOR
        for e in per_frame:
            sb = e.get("size_bytes") or 0
            if sb == 0 or sb < lo or sb > hi:
                size_mismatch_indices.append(e["index"])
    mismatch_count = len(size_mismatch_indices)
    mismatch_ratio = (mismatch_count / total_frames) if total_frames else 0.0
    size_severity = None
    if mismatch_count >= SIZE_MISMATCH_MIN_COUNT or mismatch_ratio >= SIZE_MISMATCH_RATIO:
        if mismatch_count > 0:
            size_severity = "retry"
    checks["size_mismatch"] = {
        "passed": size_severity is None,
        "severity": size_severity,
        "median_size_bytes": median_size,
        "mismatch_count": mismatch_count,
        "mismatch_ratio": round(mismatch_ratio, 3),
        "mismatch_indices": size_mismatch_indices,
        "low_factor": SIZE_LOW_FACTOR,
        "high_factor": SIZE_HIGH_FACTOR,
    }

    # --- 6. Frozen-output heuristic --------------------------------------- #
    hashes = [e.get("dhash") or "" for e in per_frame]
    max_run = _max_consecutive_run(hashes) if hashes else 0
    max_run_ratio = (max_run / total_frames) if total_frames else 0.0
    frozen_severity = None
    if (
        total_frames >= FROZEN_RUN_MIN_LEN
        and max_run >= FROZEN_RUN_MIN_LEN
        and max_run_ratio >= FROZEN_RUN_MIN_RATIO
    ):
        frozen_severity = "retry"
    checks["frozen_output"] = {
        "passed": frozen_severity is None,
        "severity": frozen_severity,
        "max_consecutive_run": max_run,
        "max_run_ratio": round(max_run_ratio, 3),
        "min_run": FROZEN_RUN_MIN_LEN,
        "min_ratio": FROZEN_RUN_MIN_RATIO,
    }

    # --- Aggregate verdict ------------------------------------------------ #
    reasons: list[str] = []
    has_reject = False
    has_retry = False
    for name, info in checks.items():
        if info.get("passed"):
            continue
        sev = info.get("severity")
        if name == "export_broken":
            # broken export is always a hard reject
            has_reject = True
            reasons.append(f"reject:{name}")
            continue
        if sev == "reject":
            has_reject = True
            reasons.append(f"reject:{name}")
        elif sev == "retry":
            has_retry = True
            reasons.append(f"retry:{name}")

    if has_reject:
        verdict = "reject"
    elif has_retry:
        verdict = "retry"
    else:
        verdict = "accept"
    return checks, verdict, reasons


# --------------------------------------------------------------------------- #
# Manifest linkage.
# --------------------------------------------------------------------------- #

def _update_manifest_with_qc(
    manifest_path: Path,
    manifest: dict[str, Any],
    qc_section: dict[str, Any],
) -> None:
    """Write the ``qc`` section back into the main video manifest JSON.

    Non-destructive: preserves every existing field and only adds/replaces
    the top-level ``qc`` key. Does not alter KT-6/KT-7 behaviour.
    """
    manifest["qc"] = qc_section
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


# --------------------------------------------------------------------------- #
# Public API.
# --------------------------------------------------------------------------- #

def run_video_qc(
    *,
    manifest_path: str | Path | None = None,
    video_id: str | None = None,
) -> dict[str, Any]:
    """Run KT-8 Minimal Video QC v1 on an existing video manifest.

    Args:
        manifest_path: Explicit path to ``data/manifests/video_{id}.json``.
        video_id: Alternatively, pass a video_id to resolve the canonical
            manifest path via ``ASSET_PATHS.video_manifest_path``.

    Returns:
        A dict containing the full QC report, including ``verdict``
        (``accept``/``retry``/``reject``), ``reasons``, per-check results,
        per-frame signals, and the persisted ``qc_report_path`` and
        ``manifest_path``.
    """
    resolved_manifest_path = _resolve_manifest_path(
        Path(manifest_path) if manifest_path else None, video_id
    )
    manifest = _load_manifest(resolved_manifest_path)
    resolved_video_id = manifest.get("video_id") or video_id
    if not resolved_video_id:
        raise ValueError(
            "Manifest is missing video_id and none was provided"
        )

    # Locate the export + processed dir from the manifest.
    export_info = manifest.get("export") or {}
    processing_info = manifest.get("processing") or {}
    export_path_str = export_info.get("export_path") or ""
    processed_dir_str = processing_info.get("processed_dir") or ""
    export_path = Path(export_path_str) if export_path_str else Path()
    processed_dir = Path(processed_dir_str) if processed_dir_str else Path()

    # 1-6: run all checks.
    export_ok, export_probe, export_error = _probe_export(export_path)

    if processed_dir and processed_dir.exists():
        per_frame = _analyse_frames(processed_dir)
    else:
        per_frame = []

    checks, verdict, reasons = _evaluate_checks(
        manifest=manifest,
        per_frame=per_frame,
        export_ok=export_ok,
        export_probe=export_probe,
        export_error=export_error,
    )

    # Build QC report.
    qc_report_path = ASSET_PATHS.manifests / f"video_qc_{resolved_video_id}.json"
    qc_report_path.parent.mkdir(parents=True, exist_ok=True)

    black_count = checks["black_frames"]["black_count"]
    total_frames = len(per_frame)
    summary = {
        "export_ok": export_ok,
        "export_frame_count": int(export_probe.get("frame_count") or 0),
        "export_size_bytes": int(export_probe.get("size_bytes") or 0),
        "processed_frames_on_disk": total_frames,
        "manifest_processed_count": int(processing_info.get("processed_count") or 0),
        "manifest_selected_count": int((manifest.get("selection") or {}).get("selected_count") or 0),
        "black_frame_count": black_count,
        "black_frame_ratio": checks["black_frames"]["black_ratio"],
        "size_mismatch_count": checks["size_mismatch"]["mismatch_count"],
        "size_mismatch_ratio": checks["size_mismatch"]["mismatch_ratio"],
        "frozen_run_max_length": checks["frozen_output"]["max_consecutive_run"],
        "frozen_run_ratio": checks["frozen_output"]["max_run_ratio"],
    }

    report: dict[str, Any] = {
        "video_id": resolved_video_id,
        "generated_at": datetime.utcnow().isoformat(),
        "manifest_path": str(resolved_manifest_path),
        "export_path": export_path_str,
        "processed_dir": processed_dir_str,
        "qc_version": "kt8_minimal_v1",
        "verdict": verdict,
        "reasons": reasons,
        "summary": summary,
        "checks": checks,
        "per_frame_qc": per_frame,
    }

    # Persist the standalone QC report.
    with open(qc_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    report["qc_report_path"] = str(qc_report_path)

    # Update the main video manifest with a compact qc linkage section.
    qc_section = {
        "qc_report_path": str(qc_report_path),
        "qc_version": "kt8_minimal_v1",
        "verdict": verdict,
        "reasons": reasons,
        "summary": summary,
        "generated_at": report["generated_at"],
    }
    try:
        _update_manifest_with_qc(resolved_manifest_path, manifest, qc_section)
    except OSError as exc:  # pragma: no cover - best effort
        report["manifest_update_error"] = f"failed to update manifest: {exc}"

    return report


__all__ = [
    "run_video_qc",
    "BLACK_MEAN_MAX",
    "BLACK_STD_MAX",
    "BLACK_MAJORITY_RATIO",
    "SIZE_LOW_FACTOR",
    "SIZE_HIGH_FACTOR",
    "SIZE_MISMATCH_MIN_COUNT",
    "SIZE_MISMATCH_RATIO",
    "FROZEN_RUN_MIN_LEN",
    "FROZEN_RUN_MIN_RATIO",
    "FRAME_COUNT_TOLERANCE",
]
