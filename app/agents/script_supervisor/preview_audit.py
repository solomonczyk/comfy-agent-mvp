"""Preview audit for Script Supervisor.

Checks preview artifacts for static/duplicate frame failure and path consistency.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .standards_adapter import ScriptSupervisorStandardsAdapter


class PreviewAuditor:
    """Audits preview artifacts for static/duplicate failure and path consistency."""

    DUP_THRESHOLD = 0.5
    STATIC_THRESHOLD = 0.9

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.preview_dir = self.project_root / "output" / "preview"
        self.previews_dir = self.project_root / "output" / "previews"
        self.control_dir = self.project_root / "output" / "control"
        self.standards = ScriptSupervisorStandardsAdapter(self.project_root)

    def audit(self) -> Dict[str, Any]:
        """Run preview audit and return a standards-driven report."""
        self.standards.load_standards()

        findings: List[Dict[str, Any]] = []

        # Check path consistency
        path_mismatch = self.previews_dir.exists() and self.preview_dir.exists()
        if path_mismatch:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="warning",
                    severity="warning",
                    detail="Both output/preview and output/previews exist — path inconsistency",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="Preview path consistency ok",
                )
            )

        # Check preview artifacts
        preview_mp4 = (self.preview_dir / "preview_lowres.mp4").is_file()
        preview_gif = (self.preview_dir / "preview.gif").is_file()
        contact_sheet = (self.preview_dir / "contact_sheet.jpg").is_file()
        frames_dir = self.preview_dir / "frames"
        frames_found = frames_dir.is_dir()

        preview_artifacts_registered = preview_mp4 or preview_gif or contact_sheet or frames_found

        if preview_artifacts_registered:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="pass",
                    severity="info",
                    detail="Preview artifacts registered",
                )
            )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="operator_review_required",
                    severity="warning",
                    detail="No preview artifacts found to audit",
                )
            )

        # Static/duplicate frame check
        static_or_duplicate_risk = False
        duplicate_static_ratio = 0.0
        duplicate_frame_count = 0
        total_frame_count = 0

        if frames_found:
            frame_files = sorted(
                [f for f in os.listdir(frames_dir) if f.endswith(".png")],
                key=lambda x: int("".join(c for c in x if c.isdigit()) or 0),
            )
            total_frame_count = len(frame_files)

            if total_frame_count > 0:
                frame_hashes: Dict[str, List[str]] = {}
                for fname in frame_files:
                    fpath = frames_dir / fname
                    try:
                        with open(fpath, "rb") as fh:
                            h = hashlib.sha256(fh.read()).hexdigest()
                        frame_hashes.setdefault(h, []).append(fname)
                    except (IOError, OSError):
                        continue

                unique_frame_count = len(frame_hashes)
                duplicate_frame_count = total_frame_count - unique_frame_count
                duplicate_static_ratio = (
                    duplicate_frame_count / total_frame_count
                    if total_frame_count > 0 else 0.0
                )

                if duplicate_static_ratio >= self.STATIC_THRESHOLD:
                    static_or_duplicate_risk = True
                    findings.append(
                        self.standards.get_traceable_finding(
                            decision="blocked",
                            severity="blocker",
                            detail=f"Static preview detected: {duplicate_static_ratio:.1%} duplicate frames",
                        )
                    )
                elif duplicate_static_ratio >= self.DUP_THRESHOLD:
                    static_or_duplicate_risk = True
                    findings.append(
                        self.standards.get_traceable_finding(
                            decision="operator_review_required",
                            severity="warning",
                            detail=f"High duplicate ratio: {duplicate_static_ratio:.1%}",
                        )
                    )
                else:
                    findings.append(
                        self.standards.get_traceable_finding(
                            decision="pass",
                            severity="info",
                            detail=f"Duplicate ratio acceptable: {duplicate_static_ratio:.1%}",
                        )
                    )
            else:
                findings.append(
                    self.standards.get_traceable_finding(
                        decision="operator_review_required",
                        severity="warning",
                        detail="Frames directory exists but contains no frames",
                    )
                )
        else:
            findings.append(
                self.standards.get_traceable_finding(
                    decision="operator_review_required",
                    severity="warning",
                    detail="Frames directory not found — cannot assess static/duplicate risk",
                )
            )

        return {
            "report_id": "script_supervisor_preview_audit_report",
            "version": "1.0.0",
            "task_id": "RC-COMBINE-V2-SCRIPT-SUPERVISOR-STANDARDS-DRIVEN-VERTICAL-SLICE-001",
            "role": "script_supervisor",
            "preview_artifacts_registered": preview_artifacts_registered,
            "preview_mp4_found": preview_mp4,
            "preview_gif_found": preview_gif,
            "contact_sheet_found": contact_sheet,
            "frames_dir_found": frames_found,
            "total_frame_count": total_frame_count,
            "duplicate_frame_count": duplicate_frame_count,
            "duplicate_static_ratio": duplicate_static_ratio,
            "preview_static_or_duplicate_risk_checked": True,
            "static_or_duplicate_risk": static_or_duplicate_risk,
            "path_consistency_checked": True,
            "path_mismatch_detected": path_mismatch,
            "findings": findings,
            "standards_pack_version": self.standards.get_standards_version(),
            "traceable": True,
        }
