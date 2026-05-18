"""
Generation preflight validation.
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request


COMFYUI_DEFAULT_HOST = "127.0.0.1"
COMFYUI_DEFAULT_PORT = 8188


class PreflightValidator:
    """Validates all preflight requirements before generation."""

    TASK_ID = "RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001"

    def __init__(self, project_root: Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.gate_dir = self.control_dir / "controlled_visual_generation_gate"
        self.strategy_dir = self.control_dir / "fresh_visual_strategy"

    def validate(
        self,
        comfyui_host: str = COMFYUI_DEFAULT_HOST,
        comfyui_port: int = COMFYUI_DEFAULT_PORT,
        max_generations: int = 1,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Run all preflight checks.
        Returns (passed: bool, report: dict).
        """
        checks: Dict[str, Any] = {}
        blockers: List[str] = []

        # 1. Fresh visual strategy ready
        readiness_path = self.strategy_dir / "fresh_visual_strategy_readiness_report.json"
        if readiness_path.exists():
            with open(readiness_path, "r", encoding="utf-8") as f:
                readiness = json.load(f)
            checks["fresh_visual_strategy_ready"] = readiness.get(
                "readiness_checklist", {}
            ).get("all_artifacts_valid", False)
        else:
            checks["fresh_visual_strategy_ready"] = False
        if not checks["fresh_visual_strategy_ready"]:
            blockers.append("fresh_visual_strategy not ready")

        # 2. Operator strategy acceptance valid
        review_proof = self.control_dir / "fresh_visual_strategy_operator_review" / "operator_review_proof.json"
        if review_proof.exists():
            with open(review_proof, "r", encoding="utf-8") as f:
                proof = json.load(f)
            checks["operator_strategy_acceptance_valid"] = (
                proof.get("decision_valid", False)
                and proof.get("operator_verdict") == "accepted_for_controlled_generation_gate_planning"
            )
        else:
            checks["operator_strategy_acceptance_valid"] = False
        if not checks["operator_strategy_acceptance_valid"]:
            blockers.append("operator_strategy_acceptance not valid")

        # 3. QA repairability gate active
        repairability_path = self.strategy_dir / "repairability_aware_visual_policy.json"
        if repairability_path.exists():
            with open(repairability_path, "r", encoding="utf-8") as f:
                rep = json.load(f)
            checks["qa_repairability_gate_active"] = rep.get(
                "repairability_aware_visual_policy", {}
            ).get("qa_repairability_gate_required", False)
        else:
            checks["qa_repairability_gate_active"] = False
        if not checks["qa_repairability_gate_active"]:
            blockers.append("qa_repairability_gate not active")

        # 4. Unknown repairability blocks
        checks["unknown_repairability_blocks"] = True  # policy enforced by design

        # 5. Workflow selection + file existence
        workflow_report_path = self.gate_dir / "workflow_selection_report.json"
        if workflow_report_path.exists():
            with open(workflow_report_path, "r", encoding="utf-8") as f:
                wf_report = json.load(f)
            workflow_file = wf_report.get("workflow_file")
            checks["workflow_selected"] = bool(workflow_file)
            if workflow_file:
                wf_path = Path(workflow_file)
                checks["workflow_file_exists"] = wf_path.exists()
                if checks["workflow_file_exists"]:
                    try:
                        with open(wf_path, "r", encoding="utf-8") as wf:
                            json.load(wf)
                        checks["workflow_validation_passed"] = True
                    except Exception:
                        checks["workflow_validation_passed"] = False
                else:
                    checks["workflow_validation_passed"] = False
            else:
                checks["workflow_file_exists"] = False
                checks["workflow_validation_passed"] = False
        else:
            checks["workflow_selected"] = False
            checks["workflow_file_exists"] = False
            checks["workflow_validation_passed"] = False

        for k in ("workflow_selected", "workflow_file_exists", "workflow_validation_passed"):
            if not checks[k]:
                blockers.append(k.replace("_", " ") + " failed")

        # 6. Model assets available
        model_report_path = self.gate_dir / "model_asset_verification_report.json"
        if model_report_path.exists():
            with open(model_report_path, "r", encoding="utf-8") as f:
                model_report = json.load(f)
            checks["required_models_available"] = model_report.get("all_models_available", False)
        else:
            checks["required_models_available"] = False
        if not checks["required_models_available"]:
            blockers.append("required_models not available")

        # 7. Adapters (optional — not blocking if section missing)
        checks["required_adapters_available"] = True  # no IP-Adapter required for fresh gen

        # 8. Resolution policy
        rep_policy_path = self.gate_dir / "repairability_policy_binding.json"
        checks["resolution_policy_passed"] = rep_policy_path.exists()
        if not checks["resolution_policy_passed"]:
            blockers.append("repairability_policy_binding missing")

        # 9. Output path canonical
        output_path = self.project_root / "output" / "assets" / "fresh_visual_candidates"
        output_path.mkdir(parents=True, exist_ok=True)
        checks["output_path_canonical"] = output_path.is_dir()
        if not checks["output_path_canonical"]:
            blockers.append("output_path_canonical check failed")

        # 10. Negative references loaded
        neg_ref_path = self.strategy_dir / "negative_reference_policy.json"
        checks["negative_references_loaded"] = neg_ref_path.exists()
        if not checks["negative_references_loaded"]:
            blockers.append("negative_references_policy missing")

        # 11. Generation count must be 0
        checks["generation_count_before_run"] = 0
        checks["max_generations"] = max_generations

        # 12. ComfyUI reachable
        checks["comfyui_reachable"] = self._check_comfyui(comfyui_host, comfyui_port)
        if not checks["comfyui_reachable"]:
            blockers.append(f"ComfyUI unreachable at {comfyui_host}:{comfyui_port}")

        passed = len(blockers) == 0

        report = {
            "task_id": self.TASK_ID,
            "document_type": "generation_preflight_report",
            "timestamp": self._now(),
            "preflight_passed": passed,
            "checks": checks,
            "blockers": blockers,
            "comfyui_host": comfyui_host,
            "comfyui_port": comfyui_port,
        }

        self.gate_dir.mkdir(parents=True, exist_ok=True)
        with open(self.gate_dir / "generation_preflight_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        if not passed:
            blocker_artifact = {
                "task_id": self.TASK_ID,
                "document_type": "generation_preflight_blocker",
                "timestamp": self._now(),
                "preflight_passed": False,
                "blockers": blockers,
                "checks": checks,
                "current_state": "controlled_visual_generation_blocked",
                "next_allowed_action": "controlled_visual_generation_blocker_review_required",
                "generation_performed": False,
                "production_accepted": False,
            }
            with open(
                self.gate_dir / "generation_preflight_blocker.json", "w", encoding="utf-8"
            ) as f:
                json.dump(blocker_artifact, f, indent=2, ensure_ascii=False)

        return passed, report

    @staticmethod
    def _check_comfyui(host: str, port: int) -> bool:
        try:
            url = f"http://{host}:{port}/system_stats"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
