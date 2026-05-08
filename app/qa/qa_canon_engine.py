"""QA Canon Engine — main runner.

Orchestrates canon loading, scene routing, defect detection, decision policy
application, operator feedback integration, and QA report generation.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.qa.canon_registry import (
    load_domain_canon,
    load_universal_canon,
    merge_canons,
)
from app.qa.decision_policy import apply_decision_policy, load_decision_policy
from app.qa.defect_taxonomy import map_operator_feedback_to_defects
from app.qa.opencv_checks import run_opencv_checks
from app.qa.reference_memory import (
    add_feedback_entry,
    save_negative_reference,
)
from app.qa.region_checks import run_region_checks
from app.qa.scene_router import classify_scene_type


class QADecision:
    """Structured QA decision result."""

    def __init__(
        self,
        candidate_version: str,
        scene_type: str,
        canons_used: List[str],
        region_check_result: Dict[str, Any],
        opencv_result: Dict[str, Any],
        operator_feedback_used: bool,
        detected_defects: List[str],
        critical_failures: List[str],
        decision: str,
        production_accepted: bool,
        assembly_allowed: bool,
        downstream_allowed: bool,
        recommended_next_action: str,
    ):
        self.candidate_version = candidate_version
        self.scene_type = scene_type
        self.canons_used = canons_used
        self.region_check_result = region_check_result
        self.opencv_result = opencv_result
        self.operator_feedback_used = operator_feedback_used
        self.detected_defects = detected_defects
        self.critical_failures = critical_failures
        self.decision = decision
        self.production_accepted = production_accepted
        self.assembly_allowed = assembly_allowed
        self.downstream_allowed = downstream_allowed
        self.recommended_next_action = recommended_next_action

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_version": self.candidate_version,
            "scene_type": self.scene_type,
            "canons_used": self.canons_used,
            "region_check_result": self.region_check_result,
            "opencv_result": self.opencv_result,
            "operator_feedback_used": self.operator_feedback_used,
            "detected_defects": self.detected_defects,
            "critical_failures": self.critical_failures,
            "decision": self.decision,
            "production_accepted": self.production_accepted,
            "assembly_allowed": self.assembly_allowed,
            "downstream_allowed": self.downstream_allowed,
            "recommended_next_action": self.recommended_next_action,
        }


class QACanonEngine:
    """Main QA Canon Engine runner.

    Usage:
        engine = QACanonEngine(project_root)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path="output/assets/combine_v2_v12_candidate_...",
            task_contract={...},
            operator_feedback="teeth do not pass visual approval",
        )
    """

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.canon_dir = self.control_dir / "qa" / "canons"
        self.policy_dir = self.control_dir / "qa" / "policies"
        self.feedback_dir = self.control_dir / "qa" / "feedback"
        self.ref_dir = self.control_dir / "qa" / "references"

    def evaluate(
        self,
        candidate_version: str,
        asset_path: str,
        task_contract: Optional[Dict[str, Any]] = None,
        operator_feedback: Optional[str] = None,
    ) -> QADecision:
        """Run the full QA evaluation pipeline.

        Steps:
        1. Load canons (universal + domain)
        2. Route scene type
        3. Run region checks (PIL-based)
        4. Run OpenCV checks (with safe fallback)
        5. Map operator feedback to defects
        6. Apply decision policy
        7. Return structured QADecision
        """
        # 1. Load canons
        universal = load_universal_canon(self.canon_dir)
        scene_type = classify_scene_type(candidate_version, task_contract)
        domain = load_domain_canon(scene_type, self.canon_dir)
        merged = merge_canons(universal, domain, task_contract)

        canons_used: List[str] = merged.get("canons_used", [])
        hard_reject_defects: List[str] = merged.get("hard_reject_defects", [])

        # 2. Resolve asset path
        asset_full_path = self._resolve_asset_path(asset_path)

        # 3. Run region checks (PIL-based, always available)
        region_result = run_region_checks(asset_full_path)

        # 4. Run OpenCV checks (safe fallback if cv2 unavailable)
        opencv_result = run_opencv_checks(asset_full_path)

        # 5. Detect defects
        detected_defects: List[str] = []
        critical_failures: List[str] = []

        # 5a. Universal defects from region checks
        if region_result.get("stub_asset", False):
            detected_defects.append("stub_asset")
            critical_failures.append("stub_asset")
        if not region_result.get("readable", False):
            detected_defects.append("unreadable_asset")
            critical_failures.append("unreadable_asset")

        # 5b. OpenCV-based defects (only if checks executed)
        if opencv_result.get("checks_executed") and opencv_result.get("opencv_available"):
            if opencv_result.get("is_blurry"):
                detected_defects.append("severe_blur")
                critical_failures.append("severe_blur")

            mouth = opencv_result.get("mouth_analysis", {})
            if mouth.get("suspicious_mouth"):
                detected_defects.append("unnatural_mouth")
                critical_failures.append("unnatural_mouth")

        # 5c. Map operator feedback to defects
        operator_feedback_used = False
        if operator_feedback:
            operator_feedback_used = True
            feedback_defects = map_operator_feedback_to_defects(operator_feedback)
            for defect_id in feedback_defects:
                if defect_id not in detected_defects:
                    detected_defects.append(defect_id)
                # Critical if it's a hard_reject defect
                if defect_id in hard_reject_defects and defect_id not in critical_failures:
                    critical_failures.append(defect_id)

        # 6. Apply decision policy
        policy = load_decision_policy(self.policy_dir)
        policy_result = apply_decision_policy(policy, critical_failures, detected_defects)

        # 7. Build final decision
        decision = QADecision(
            candidate_version=candidate_version,
            scene_type=scene_type,
            canons_used=canons_used,
            region_check_result=region_result,
            opencv_result=opencv_result,
            operator_feedback_used=operator_feedback_used,
            detected_defects=detected_defects,
            critical_failures=critical_failures,
            decision=policy_result["decision"],
            production_accepted=policy_result["production_accepted"],
            assembly_allowed=policy_result["assembly_allowed"],
            downstream_allowed=policy_result["downstream_allowed"],
            recommended_next_action=policy_result["recommended_next_action"],
        )

        return decision

    def record_operator_feedback(
        self,
        candidate_version: str,
        asset_path: str,
        operator_comment: str,
        defects: Optional[List[str]] = None,
        failed_regions: Optional[List[str]] = None,
    ) -> None:
        """Record operator feedback and negative reference."""
        # Add to feedback memory
        add_feedback_entry(
            feedback_dir=self.feedback_dir,
            candidate_version=candidate_version,
            asset_path=asset_path,
            label="negative",
            failed_regions=failed_regions or [],
            defects=defects or [],
            operator_comment=operator_comment,
        )

        # Save negative reference
        save_negative_reference(
            ref_dir=self.ref_dir,
            candidate_version=candidate_version,
            asset_path=asset_path,
            failed_regions=failed_regions or [],
            defects=defects or [],
            operator_comment=operator_comment,
        )

    def save_qa_report(self, decision: QADecision) -> Path:
        """Save the QA decision as a JSON report file."""
        report_dir = self.control_dir / "qa" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        report = decision.to_dict()
        report["timestamp"] = datetime.now().isoformat()

        filename = f"combine_v2_{decision.candidate_version}_qa_canon_report.json"
        path = report_dir / filename

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        return path

    def _resolve_asset_path(self, asset_path: str) -> Path:
        """Resolve asset path relative to project root if not absolute."""
        p = Path(asset_path)
        if p.is_absolute():
            return p
        return self.project_root / asset_path
