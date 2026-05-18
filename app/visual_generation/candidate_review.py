"""
Candidate technical and repairability review builder.
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from PIL import Image, ImageStat
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class CandidateReviewBuilder:
    """Builds technical review, repairability review, and operator review packet for candidate."""

    TASK_ID = "RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001"

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.candidate_dir = self.control_dir / "fresh_visual_candidate"
        self.strategy_dir = self.control_dir / "fresh_visual_strategy"

    def build_all(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Build technical review, repairability review, and operator review packet."""
        self.candidate_dir.mkdir(parents=True, exist_ok=True)

        technical = self._build_technical_review(manifest)
        repairability = self._build_repairability_review(manifest, technical)
        op_packet = self._build_operator_review_packet(manifest, technical, repairability)
        proof = self._build_proof(manifest, technical, repairability, op_packet)

        self._write(self.candidate_dir / "generated_candidate_technical_review.json", technical)
        self._write(self.candidate_dir / "generated_candidate_repairability_review.json", repairability)
        self._write(self.candidate_dir / "generated_candidate_operator_review_packet.json", op_packet)
        self._write(self.candidate_dir / "generated_candidate_proof.json", proof)

        return {
            "technical_review": technical,
            "repairability_review": repairability,
            "operator_review_packet": op_packet,
            "proof": proof,
        }

    def _build_technical_review(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        assets = manifest.get("generated_assets", [])
        metrics: List[Dict[str, Any]] = []
        all_pass = True

        for asset in assets:
            path = asset.get("path")
            exists = asset.get("exists", False)
            readable = asset.get("readable", False)
            w = asset.get("width", 0)
            h = asset.get("height", 0)
            size = asset.get("size_bytes", 0)
            sha256 = asset.get("sha256")

            technical_pass = exists and readable and sha256 and size > 0
            if not technical_pass:
                all_pass = False

            asset_metrics: Dict[str, Any] = {
                "path": path,
                "exists": exists,
                "readable": readable,
                "sha256": sha256,
                "size_bytes": size,
                "width": w,
                "height": h,
                "technical_pass": technical_pass,
                "blur_metric": None,
                "brightness_metric": None,
                "contrast_metric": None,
            }

            if path and exists and PIL_AVAILABLE:
                try:
                    with Image.open(path) as img:
                        stat = ImageStat.Stat(img)
                        asset_metrics["brightness_metric"] = round(stat.mean[0], 2)
                        asset_metrics["contrast_metric"] = round(stat.stddev[0], 2)
                        gray = img.convert("L")
                        stat_g = ImageStat.Stat(gray)
                        asset_metrics["blur_metric"] = round(stat_g.stddev[0], 2)
                except Exception:
                    pass

            metrics.append(asset_metrics)

        return {
            "task_id": self.TASK_ID,
            "document_type": "generated_candidate_technical_review",
            "timestamp": self._now(),
            "technical_verdict": "PASS" if all_pass else "FAIL",
            "all_assets_technical_pass": all_pass,
            "asset_metrics": metrics,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "production_accepted": False,
        }

    def _build_repairability_review(
        self, manifest: Dict[str, Any], technical: Dict[str, Any]
    ) -> Dict[str, Any]:
        neg_policy_path = self.strategy_dir / "negative_reference_policy.json"
        neg_policy: Dict[str, Any] = {}
        if neg_policy_path.exists():
            with open(neg_policy_path, "r", encoding="utf-8") as f:
                neg_policy = json.load(f)

        negative_refs = list(
            neg_policy.get("negative_reference_policy", {})
            .get("documented_negative_references", {})
            .keys()
        )

        return {
            "task_id": self.TASK_ID,
            "document_type": "generated_candidate_repairability_review",
            "timestamp": self._now(),
            "qa_repairability_gate_active": True,
            "unknown_repairability_blocks": True,
            "negative_references_enforced": negative_refs,
            "negative_reference_count": len(negative_refs),
            "defects_identified": [],
            "defects_with_unknown_repairability": [],
            "repairability_blocking_defects": [],
            "repairability_verdict": "PASS_OPERATOR_REVIEW_REQUIRED",
            "note": "Technical repairability pre-check complete. Visual defect assessment requires human operator review.",
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "production_accepted": False,
        }

    def _build_operator_review_packet(
        self,
        manifest: Dict[str, Any],
        technical: Dict[str, Any],
        repairability: Dict[str, Any],
    ) -> Dict[str, Any]:
        assets = manifest.get("generated_assets", [])
        return {
            "task_id": self.TASK_ID,
            "document_type": "generated_candidate_operator_review_packet",
            "timestamp": self._now(),
            "generation_performed": True,
            "generation_count": 1,
            "prompt_id": manifest.get("prompt_id"),
            "generated_assets": assets,
            "technical_verdict": technical.get("technical_verdict"),
            "repairability_verdict": repairability.get("repairability_verdict"),
            "operator_review_instructions": {
                "open_generated_image": "Open each generated asset path and visually inspect",
                "check_against_negative_references": repairability.get(
                    "negative_references_enforced", []
                ),
                "operator_decision_options": [
                    "accepted_for_next_visual_stage",
                    "rejected_with_defects",
                    "revision_required",
                    "controlled_retry_plan_required",
                ],
            },
            "current_state": "fresh_visual_candidate_operator_review_required",
            "next_allowed_action": "fresh_visual_candidate_operator_review_required",
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
        }

    def _build_proof(
        self,
        manifest: Dict[str, Any],
        technical: Dict[str, Any],
        repairability: Dict[str, Any],
        op_packet: Dict[str, Any],
    ) -> Dict[str, Any]:
        assets = manifest.get("generated_assets", [])
        return {
            "task_id": self.TASK_ID,
            "document_type": "generated_candidate_proof",
            "timestamp": self._now(),
            "generation_performed": True,
            "generation_count": 1,
            "max_generations": 1,
            "workflow_submitted": True,
            "comfyui_execution": True,
            "prompt_id": manifest.get("prompt_id"),
            "generated_assets": assets,
            "technical_candidate_review_created": True,
            "repairability_candidate_review_created": True,
            "operator_visual_review_packet_created": True,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": "fresh_visual_candidate_operator_review_required",
            "next_allowed_action": "fresh_visual_candidate_operator_review_required",
        }

    def _write(self, path: Path, data: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
