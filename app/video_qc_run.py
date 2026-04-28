"""KT-8 Minimal Video QC v1 CLI entrypoint.

Usage (by video_id, resolves data/manifests/video_{video_id}.json):
    python -m app.video_qc_run --video-id kt7_proof_001

Usage (by explicit manifest path):
    python -m app.video_qc_run --manifest-path data/manifests/video_kt7_proof_001.json

Reads an existing KT-6/KT-7 video manifest, runs the minimal video QC gate,
persists a standalone QC report at data/manifests/video_qc_{video_id}.json
and updates the main manifest with a compact ``qc`` linkage section.

Exit codes:
    0 - verdict == accept
    1 - verdict == retry
    2 - verdict == reject
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.assets.paths import ensure_asset_dirs
from app.video.video_qc import run_video_qc


_EXIT_BY_VERDICT = {"accept": 0, "retry": 1, "reject": 2}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="KT-8 Minimal Video QC v1 — classify a processed video export",
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--video-id",
        default=None,
        help="video_id whose manifest lives at data/manifests/video_{video_id}.json",
    )
    src.add_argument(
        "--manifest-path",
        default=None,
        help="Explicit path to a video manifest JSON",
    )
    parser.add_argument(
        "--print-report-json",
        action="store_true",
        help="Print the full QC report as JSON at the end",
    )
    return parser


def _render(report: dict) -> None:
    print("\n" + "=" * 60)
    print("VIDEO QC REPORT (KT-8 Minimal Video QC v1)")
    print("=" * 60)
    print(f"video_id:         {report.get('video_id')}")
    print(f"verdict:          {report.get('verdict', '').upper()}")
    print(f"qc_version:       {report.get('qc_version')}")
    print(f"manifest_path:    {report.get('manifest_path')}")
    print(f"export_path:      {report.get('export_path')}")
    print(f"processed_dir:    {report.get('processed_dir')}")
    print(f"qc_report_path:   {report.get('qc_report_path')}")
    reasons = report.get("reasons") or []
    if reasons:
        print("-" * 60)
        print("REASONS:")
        for r in reasons:
            print(f"  - {r}")
    print("-" * 60)
    print("SUMMARY:")
    summary = report.get("summary") or {}
    for k, v in summary.items():
        print(f"  {k:28s} {v}")
    print("-" * 60)
    print("CHECKS:")
    checks = report.get("checks") or {}
    for name, info in checks.items():
        passed = "PASS" if info.get("passed") else "FAIL"
        sev = info.get("severity") or "-"
        detail = info.get("detail") or ""
        print(f"  [{passed}] {name:28s} severity={sev} {detail}")
    print("=" * 60 + "\n")


def main() -> None:
    args = build_parser().parse_args()
    ensure_asset_dirs()

    try:
        report = run_video_qc(
            manifest_path=Path(args.manifest_path) if args.manifest_path else None,
            video_id=args.video_id,
        )
    except FileNotFoundError as exc:
        print(f"VIDEO QC FAILED: {exc}")
        raise SystemExit(3)
    except Exception as exc:
        print(f"VIDEO QC FAILED: {exc}")
        raise SystemExit(3)

    _render(report)

    if args.print_report_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    verdict = report.get("verdict", "reject")
    sys.exit(_EXIT_BY_VERDICT.get(verdict, 2))


if __name__ == "__main__":
    main()
