"""KT-8 Minimal Video QC v1 — unit tests.

Validates the deterministic verdict logic against synthetic processed-frame
directories and minimal handcrafted manifests. Isolates the QC gate from
the real KT-6/KT-7 pipeline; the video pipeline is not exercised here.

Each scenario builds:
    - a processed/ directory with N frames of known content
    - a fake export.mp4 (bytes or real ffmpeg-assembled clip)
    - a minimal video manifest JSON

and then calls ``run_video_qc`` and asserts the resulting verdict, the
presence of expected reason codes, and the persistence of the QC report
plus its linkage back into the manifest.
"""
from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from dataclasses import replace

from app.assets.paths import ASSET_PATHS
from app.video import video_qc


# --------------------------------------------------------------------------- #
# Scenario builders
# --------------------------------------------------------------------------- #


def _solid_frame(path: Path, rgb: tuple[int, int, int], size: tuple[int, int] = (64, 64)) -> None:
    """Write a PNG of a single solid colour."""
    Image.new("RGB", size, rgb).save(path, format="PNG")


def _noisy_frame(
    path: Path,
    seed: int,
    size: tuple[int, int] = (64, 64),
) -> None:
    """Write a PNG filled with random noise (deterministic per seed).

    Each frame must have a distinct dhash so the frozen-frame check does not
    fire; noisy frames also have meaningful byte sizes for the size-mismatch
    test.
    """
    rng = random.Random(seed)
    img = Image.new("RGB", size)
    pixels = [
        (rng.randrange(0, 256), rng.randrange(0, 256), rng.randrange(0, 256))
        for _ in range(size[0] * size[1])
    ]
    img.putdata(pixels)
    img.save(path, format="PNG")


def _fake_export_bytes(path: Path, nbytes: int = 4096) -> None:
    """Write ``nbytes`` of pseudo-random bytes to simulate a non-empty export.

    ffprobe will error out on this file (it is not a valid video container),
    which mirrors a real broken export. QC treats a broken probe as ``reject``
    on the export check, so scenarios needing a PASSING export check must use
    :func:`_real_export` instead.
    """
    path.write_bytes(b"\x00\x01" * (nbytes // 2))


def _real_export(processed_dir: Path, export_path: Path, fps: float = 6.0) -> None:
    """Assemble processed frames into a real h264 export via ffmpeg."""
    if os.environ.get("RUN_REAL_FFMPEG_TESTS") != "1":
        pytest.skip("real ffmpeg tests disabled; set RUN_REAL_FFMPEG_TESTS=1 to enable")
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not on PATH; real-export scenarios are skipped.")
    export_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(fps),
        "-start_number", "1",
        "-i", str(processed_dir / "frame_%06d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        str(export_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)


def _write_manifest(
    manifests_dir: Path,
    *,
    video_id: str,
    video_dir: Path,
    processed_dir: Path,
    export_path: Path,
    selected_count: int,
    processed_count: int,
) -> Path:
    manifest: dict[str, Any] = {
        "video_id": video_id,
        "input_path": str(video_dir / "synthetic_input.mp4"),
        "video_dir": str(video_dir),
        "started_at": "2026-04-18T00:00:00",
        "completed_at": "2026-04-18T00:00:01",
        "status": "completed",
        "probe": {"duration_s": 1.0, "fps": 6.0, "frame_count": processed_count},
        "extraction": {"frames_dir": str(video_dir / "frames"), "frame_count": processed_count},
        "selection": {
            "strategy": "every_1",
            "selected_count": selected_count,
            "selected_frames": [f"frame_{i:06d}.png" for i in range(1, selected_count + 1)],
        },
        "processing": {
            "processed_dir": str(processed_dir),
            "processed_count": processed_count,
            "processor": "kt8_test_fixture",
        },
        "export": {"export_path": str(export_path), "fps": 6.0},
        "error": None,
    }
    path = manifests_dir / f"video_{video_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path


@pytest.fixture
def redirect_asset_paths(tmp_path, monkeypatch):
    """Point ASSET_PATHS.manifests at a tmp dir so the QC writes don't pollute data/.

    ``AssetPaths`` is a frozen dataclass so we cannot mutate it in place;
    instead we build a replacement instance with the ``manifests`` field
    redirected at a temporary directory and rebind the module-level
    ``ASSET_PATHS`` symbol that ``video_qc`` imported.
    """
    fake_manifests = tmp_path / "manifests"
    fake_manifests.mkdir(parents=True, exist_ok=True)
    patched = replace(ASSET_PATHS, manifests=fake_manifests)
    monkeypatch.setattr(video_qc, "ASSET_PATHS", patched)
    return fake_manifests


# --------------------------------------------------------------------------- #
# Low-level primitive tests (no full run_video_qc invocation)
# --------------------------------------------------------------------------- #


def test_max_consecutive_run_basic():
    assert video_qc._max_consecutive_run([]) == 0
    assert video_qc._max_consecutive_run(["a"]) == 1
    assert video_qc._max_consecutive_run(["a", "a", "a"]) == 3
    assert video_qc._max_consecutive_run(["a", "b", "b", "c"]) == 2
    assert video_qc._max_consecutive_run(["a", "a", "b", "a", "a", "a"]) == 3


def test_is_black_or_blank_thresholds():
    # Very dark => black
    assert video_qc._is_black_or_blank(mean=5.0, std=50.0) is True
    # Near-uniform mid-grey => blank
    assert video_qc._is_black_or_blank(mean=128.0, std=2.0) is True
    # Normal colourful image
    assert video_qc._is_black_or_blank(mean=140.0, std=60.0) is False


def test_dhash_changes_between_distinct_images(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    _noisy_frame(a, seed=1)
    _noisy_frame(b, seed=2)
    assert video_qc._dhash(a) != video_qc._dhash(b)


def test_dhash_identical_for_identical_files(tmp_path):
    src = tmp_path / "src.png"
    copy = tmp_path / "copy.png"
    _noisy_frame(src, seed=42)
    shutil.copy2(src, copy)
    assert video_qc._dhash(src) == video_qc._dhash(copy)


# --------------------------------------------------------------------------- #
# End-to-end verdict tests
# --------------------------------------------------------------------------- #


def test_verdict_accept_on_clean_run(tmp_path, redirect_asset_paths):
    """All six checks pass => verdict == accept."""
    video_id = "kt8_unit_accept"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 5):
        _noisy_frame(processed_dir / f"frame_{i:06d}.png", seed=100 + i)
    export_path = video_dir / "export.mp4"
    _real_export(processed_dir, export_path)

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=4,
        processed_count=4,
    )

    report = video_qc.run_video_qc(manifest_path=manifest_path)
    assert report["verdict"] == "accept", report
    assert report["reasons"] == []
    assert all(info["passed"] for info in report["checks"].values())
    assert Path(report["qc_report_path"]).exists()

    # Manifest should carry the qc linkage now.
    with open(manifest_path, encoding="utf-8") as f:
        manifest_after = json.load(f)
    assert manifest_after["qc"]["verdict"] == "accept"
    assert manifest_after["qc"]["qc_report_path"] == report["qc_report_path"]


def test_verdict_reject_on_broken_export(tmp_path, redirect_asset_paths):
    """Missing export file => hard reject."""
    video_id = "kt8_unit_broken_export"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        _noisy_frame(processed_dir / f"frame_{i:06d}.png", seed=200 + i)
    export_path = video_dir / "export.mp4"  # deliberately never created

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=3,
        processed_count=3,
    )

    report = video_qc.run_video_qc(manifest_path=manifest_path)
    assert report["verdict"] == "reject"
    assert any(r.startswith("reject:export_broken") for r in report["reasons"])
    assert report["checks"]["export_broken"]["passed"] is False


def test_verdict_reject_on_empty_export_file(tmp_path, redirect_asset_paths):
    """Zero-byte export file => hard reject."""
    video_id = "kt8_unit_empty_export"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        _noisy_frame(processed_dir / f"frame_{i:06d}.png", seed=300 + i)
    export_path = video_dir / "export.mp4"
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_bytes(b"")  # zero bytes

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=3,
        processed_count=3,
    )

    report = video_qc.run_video_qc(manifest_path=manifest_path)
    assert report["verdict"] == "reject"
    assert any(r.startswith("reject:export_broken") for r in report["reasons"])


def test_verdict_reject_on_missing_processed_frames(tmp_path, redirect_asset_paths):
    """Empty processed dir => hard reject."""
    video_id = "kt8_unit_no_frames"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    # no frames written
    export_path = video_dir / "export.mp4"
    _fake_export_bytes(export_path)  # bytes present but ffprobe will fail

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=4,
        processed_count=4,
    )

    report = video_qc.run_video_qc(manifest_path=manifest_path)
    assert report["verdict"] == "reject"
    assert any(r.startswith("reject:missing_processed_frames") for r in report["reasons"])


def test_verdict_retry_on_some_black_frames(tmp_path, redirect_asset_paths):
    """1 of 4 frames fully black => retry."""
    video_id = "kt8_unit_some_black"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    _noisy_frame(processed_dir / "frame_000001.png", seed=400)
    _noisy_frame(processed_dir / "frame_000002.png", seed=401)
    _solid_frame(processed_dir / "frame_000003.png", (0, 0, 0))  # black
    _noisy_frame(processed_dir / "frame_000004.png", seed=403)
    export_path = video_dir / "export.mp4"
    _real_export(processed_dir, export_path)

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=4,
        processed_count=4,
    )

    report = video_qc.run_video_qc(manifest_path=manifest_path)
    assert report["verdict"] == "retry", report
    assert any(r.startswith("retry:black_frames") for r in report["reasons"])
    assert report["checks"]["black_frames"]["black_count"] == 1


def test_verdict_reject_on_majority_black_frames(tmp_path, redirect_asset_paths):
    """3 of 4 frames black => reject."""
    video_id = "kt8_unit_majority_black"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    _solid_frame(processed_dir / "frame_000001.png", (0, 0, 0))
    _solid_frame(processed_dir / "frame_000002.png", (0, 0, 0))
    _solid_frame(processed_dir / "frame_000003.png", (0, 0, 0))
    _noisy_frame(processed_dir / "frame_000004.png", seed=500)
    export_path = video_dir / "export.mp4"
    _real_export(processed_dir, export_path)

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=4,
        processed_count=4,
    )

    report = video_qc.run_video_qc(manifest_path=manifest_path)
    assert report["verdict"] == "reject"
    assert any(r.startswith("reject:black_frames") for r in report["reasons"])


def test_verdict_retry_on_frozen_output(tmp_path, redirect_asset_paths):
    """Frames 1-3 identical (run of 3, ratio 0.75) => retry."""
    video_id = "kt8_unit_frozen"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    # Write one noisy frame, duplicate it three times, then a different frame.
    src = processed_dir / "frame_000001.png"
    _noisy_frame(src, seed=600)
    shutil.copy2(src, processed_dir / "frame_000002.png")
    shutil.copy2(src, processed_dir / "frame_000003.png")
    _noisy_frame(processed_dir / "frame_000004.png", seed=601)
    export_path = video_dir / "export.mp4"
    _real_export(processed_dir, export_path)

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=4,
        processed_count=4,
    )

    report = video_qc.run_video_qc(manifest_path=manifest_path)
    assert report["verdict"] == "retry", report
    assert any(r.startswith("retry:frozen_output") for r in report["reasons"])
    assert report["checks"]["frozen_output"]["max_consecutive_run"] >= 3


def test_verdict_retry_on_frame_count_mismatch(tmp_path, redirect_asset_paths):
    """Manifest claims 6 processed, only 3 on disk => retry (missing) + possibly count mismatch.

    With on-disk < expected the ``missing_processed_frames`` check fires at
    severity=retry. That alone is enough to assert retry.
    """
    video_id = "kt8_unit_count_mismatch"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):  # only 3 frames on disk
        _noisy_frame(processed_dir / f"frame_{i:06d}.png", seed=700 + i)
    export_path = video_dir / "export.mp4"
    _real_export(processed_dir, export_path)

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=6,  # manifest expected 6
        processed_count=6,
    )

    report = video_qc.run_video_qc(manifest_path=manifest_path)
    assert report["verdict"] == "retry", report
    assert any(r.startswith("retry:missing_processed_frames") for r in report["reasons"])


def test_verdict_retry_on_severe_size_mismatch(tmp_path, redirect_asset_paths):
    """Two tiny frames among otherwise big frames => size mismatch => retry."""
    video_id = "kt8_unit_size_mismatch"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    # Big frames: 256x256 noise compresses to thousands of bytes.
    # Tiny frames: 16x16 noise compresses to a few hundred bytes — below
    # median/4, flagging size mismatch without being black.
    _noisy_frame(processed_dir / "frame_000001.png", seed=800, size=(256, 256))
    _noisy_frame(processed_dir / "frame_000002.png", seed=801, size=(256, 256))
    _noisy_frame(processed_dir / "frame_000003.png", seed=802, size=(16, 16))
    _noisy_frame(processed_dir / "frame_000004.png", seed=803, size=(16, 16))
    export_path = video_dir / "export.mp4"
    # Assembly may fail because ffmpeg dislikes mixed sizes; catch that.
    try:
        _real_export(processed_dir, export_path)
    except subprocess.CalledProcessError:
        # Fallback: write a plausible export file so the export check doesn't
        # dominate and mask the size mismatch signal. A non-empty but invalid
        # file still yields export_broken=reject; the size-mismatch check
        # remains observable in report["checks"].
        _fake_export_bytes(export_path)

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=4,
        processed_count=4,
    )

    report = video_qc.run_video_qc(manifest_path=manifest_path)
    size_check = report["checks"]["size_mismatch"]
    assert size_check["passed"] is False
    assert size_check["mismatch_count"] >= 2


def test_manifest_linkage_and_report_structure(tmp_path, redirect_asset_paths):
    """After QC, the manifest has a qc section and the report is self-consistent."""
    video_id = "kt8_unit_linkage"
    video_dir = tmp_path / "videos" / video_id
    processed_dir = video_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 4):
        _noisy_frame(processed_dir / f"frame_{i:06d}.png", seed=900 + i)
    export_path = video_dir / "export.mp4"
    _real_export(processed_dir, export_path)

    manifest_path = _write_manifest(
        redirect_asset_paths,
        video_id=video_id,
        video_dir=video_dir,
        processed_dir=processed_dir,
        export_path=export_path,
        selected_count=3,
        processed_count=3,
    )

    report = video_qc.run_video_qc(video_id=video_id)

    # Standalone QC report was persisted at the expected path.
    expected_qc_path = redirect_asset_paths / f"video_qc_{video_id}.json"
    assert report["qc_report_path"] == str(expected_qc_path)
    assert expected_qc_path.exists()

    with open(expected_qc_path, encoding="utf-8") as f:
        persisted = json.load(f)
    assert persisted["video_id"] == video_id
    assert persisted["verdict"] == report["verdict"]
    assert "per_frame_qc" in persisted
    assert len(persisted["per_frame_qc"]) == 3

    # Main manifest was updated with a compact qc section pointing at the
    # report, without dropping any other existing sections.
    with open(manifest_path, encoding="utf-8") as f:
        manifest_after = json.load(f)
    for required in ("probe", "extraction", "selection", "processing", "export"):
        assert required in manifest_after
    assert manifest_after["qc"]["qc_report_path"] == str(expected_qc_path)
    assert manifest_after["qc"]["verdict"] == report["verdict"]
    assert manifest_after["qc"]["qc_version"] == "kt8_minimal_v1"
