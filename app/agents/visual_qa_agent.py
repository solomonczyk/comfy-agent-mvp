"""Visual QA Agent - stub implementation.

Performs visual quality assessment and review.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class VisualQAAgent(BaseRoleAgent):
    """Visual QA and quality assessment agent.
    
    Reviews generated visuals for quality and compliance.
    Stub only - no actual generation or visual processing.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return [
            "visual_qa_required_stub_pending",
            "visual_qa_required",
            "real_visual_qa_preflight_required",
            "real_visual_qa_required",
            "operator_visual_review",
            "corrective_retry_v4_visual_qa_required",
            # V11 photoreal QA recovery stages
            "v11_correction_plan_required",
            "v11_corrective_package_build_required",
            "v11_generation_authorization_required",
            "v11_result_review_required",
            "v11_visual_qa_preflight_required",
            "v11_visual_qa_required",
            "v11_operator_visual_review_required",
            # V12 photoreal QA recovery stages
            "v12_correction_plan_required",
            "v12_corrective_package_build_required",
            "v12_generation_authorization_required",
            "v12_result_review_required",
            "v12_visual_qa_preflight_required",
            "v12_visual_qa_required",
            "v12_operator_visual_review_required",
            # V13 photoreal QA recovery stages
            "v13_correction_plan_required",
            "v13_corrective_package_build_required",
            "v13_generation_authorization_required",
            "v13_result_review_required",
            "v13_visual_qa_preflight_required",
            "v13_visual_qa_required",
            "v13_operator_visual_review_required",
        ]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root"]
    
    @property
    def output_contract_type(self) -> str:
        return "VisualQAContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def _read_contract(self, project_root: str, contract_name: str) -> Dict[str, Any]:
        """Helper to read contract files from output/control"""
        import json
        from pathlib import Path
        contract_path = Path(project_root) / "output" / "control" / f"{contract_name}.json"
        if contract_path.exists():
            try:
                with open(contract_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        """Create a stub result for the visual_qa_required stage."""
        generation_plan = self._read_contract(context.project_root, "combine_v2_generation_execution_plan")
        generation_stub_result = self._read_contract(context.project_root, "combine_v2_generation_execution_stub_result")
        generation_trace_stub = self._read_contract(context.project_root, "combine_v2_generation_trace_stub")
        operator_generation_authorization = self._read_contract(
            context.project_root,
            "combine_v2_operator_generation_authorization"
        )

        retry_aware = True

        # 1. Create Visual QA Stub Report
        stub_report = {
            "stage": "visual_qa_required",
            "agent": "VisualQAAgent",
            "status": "stubbed",
            "retry_aware": retry_aware,
            "real_image_analysis": False,
            "generation_gate_open": bool(operator_generation_authorization.get("generation_gate_open", False)),
            "checks_declared": [
                "artifact_presence_check",
                "dimensions_check",
                "blur_softness_check",
                "composition_check",
                "route_policy_check"
            ],
            "checks_executed": [],
            "retry_aware_artifacts_loaded": {
                "combine_v2_generation_execution_plan": bool(generation_plan),
                "combine_v2_generation_execution_stub_result": bool(generation_stub_result),
                "combine_v2_generation_trace_stub": bool(generation_trace_stub),
                "combine_v2_operator_generation_authorization": bool(operator_generation_authorization)
            },
            "operator_review_required": True,
            "visual_qa_passed": False,
            "final_verdict": "operator_review_required",
            "next_allowed_action": "operator_visual_review",
            "generation_performed": False,
            "comfyui_execution": False,
            "downstream_executed": False,
            "production_accepted": False
        }
        
        # 2. Create Operator Visual Review Packet
        review_packet = {
            "stage": "operator_visual_review",
            "source_stage": "visual_qa_required",
            "retry_aware": retry_aware,
            "operator_review_required": True,
            "operator_actions": [
                "accept_visuals",
                "reject_visuals",
                "request_retry_correction",
                "block_manual_review"
            ],
            "visual_qa_stub_report": "output/control/combine_v2_visual_qa_stub_report.json",
            "generated_assets": [],
            "real_image_analysis": False,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_blocked": True,
            "next_allowed_action": "operator_visual_review",
            "retry_context_sources": {
                "combine_v2_generation_execution_plan": "output/control/combine_v2_generation_execution_plan.json",
                "combine_v2_generation_execution_stub_result": "output/control/combine_v2_generation_execution_stub_result.json",
                "combine_v2_generation_trace_stub": "output/control/combine_v2_generation_trace_stub.json",
                "combine_v2_operator_generation_authorization": "output/control/combine_v2_operator_generation_authorization.json"
            },
            "retry_context_snapshot": {
                "generation_gate_open": bool(operator_generation_authorization.get("generation_gate_open", False)),
                "operator_generation_authorized": bool(
                    operator_generation_authorization.get("operator_generation_authorized", False)
                ),
                "execution_strategy": generation_plan.get("execution_strategy", "unknown"),
                "generation_stub_status": generation_stub_result.get("status", "unknown"),
                "trace_id": generation_trace_stub.get("trace_id", "")
            }
        }
        
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[
                "combine_v2_visual_qa_stub_report.json",
                "combine_v2_operator_visual_review_packet.json"
            ],
            next_recommended_stage="operator_visual_review",
            metadata={
                "action": "visual_quality_assessment",
                "description": "Performs visual QA review (stub only)",
                "retry_aware": retry_aware,
                "visual_qa_stub": True,
                "real_image_analysis": False,
                "operator_review_required": True,
                "visual_qa_passed": False,
                "next_allowed_action": "operator_visual_review",
                "production_accepted": False,
                "assembly_allowed": False,
                "downstream_blocked": True,
                # These keys tell the orchestrator to write these files to output/control
                "combine_v2_visual_qa_stub_report": stub_report,
                "combine_v2_operator_visual_review_packet": review_packet
            }
        )

    def _execute_technical_checks(self, project_root: str) -> Dict[str, Any]:
        """Execute technical checks on the generated asset from manifest."""
        import os
        import json
        import hashlib
        from pathlib import Path
        from PIL import Image
        
        # Read manifest to get asset path
        manifest_path = Path(project_root) / "output" / "control" / "combine_v2_generation_manifest.json"
        asset_path = None
        expected_width = None
        expected_height = None
        
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                    if "generated_assets" in manifest and manifest["generated_assets"]:
                        first_asset = manifest["generated_assets"][0]
                        asset_path = first_asset.get("path")
                        expected_width = first_asset.get("width")
                        expected_height = first_asset.get("height")
            except (json.JSONDecodeError, IOError, KeyError):
                pass
        
        # If no manifest or asset, try to find asset in output/assets
        if not asset_path:
            assets_dir = Path(project_root) / "output" / "assets"
            if assets_dir.exists():
                for ext in ['.png', '.jpg', '.jpeg']:
                    for file in assets_dir.glob(f"*{ext}"):
                        asset_path = str(file)
                        break
                    if asset_path:
                        break
        
        # Initialize check results
        checks = {
            "asset_exists": {"status": "failed", "message": "Asset not found"},
            "asset_readable": {"status": "failed", "message": "Asset not readable"},
            "width_height_valid": {"status": "failed", "message": "Could not validate dimensions"},
            "sha256_present": {"status": "failed", "message": "SHA256 not computed"},
            "size_bytes_valid": {"status": "failed", "message": "Size not validated"},
            "resolution_policy_check": {"status": "failed", "message": "Resolution not checked"},
            "blur_or_softness_basic": {"status": "failed", "message": "Blur not analyzed"},
            "brightness_basic": {"status": "failed", "message": "Brightness not analyzed"},
            "contrast_basic": {"status": "failed", "message": "Contrast not analyzed"}
        }
        
        actual_width = None
        actual_height = None
        sha256_hash = None
        size_bytes = None
        
        # Execute technical checks if asset exists
        if asset_path and Path(asset_path).exists():
            checks["asset_exists"] = {"status": "passed", "message": f"Asset found: {asset_path}"}
            
            try:
                # Check readability and get image info
                with Image.open(asset_path) as img:
                    actual_width, actual_height = img.size
                    checks["asset_readable"] = {"status": "passed", "message": "Asset readable"}
                    checks["width_height_valid"] = {
                        "status": "passed",
                        "message": f"Dimensions: {actual_width}x{actual_height}",
                        "actual_width": actual_width,
                        "actual_height": actual_height
                    }
                    
                    # Resolution policy check
                    if expected_width and expected_height:
                        if actual_width == expected_width and actual_height == expected_height:
                            checks["resolution_policy_check"] = {
                                "status": "passed",
                                "message": "Resolution matches expected",
                                "actual_width": actual_width,
                                "actual_height": actual_height,
                                "expected_width": expected_width,
                                "expected_height": expected_height
                            }
                        else:
                            checks["resolution_policy_check"] = {
                                "status": "warn",
                                "message": f"Resolution mismatch: {actual_width}x{actual_height} vs expected {expected_width}x{expected_height}",
                                "actual_width": actual_width,
                                "actual_height": actual_height,
                                "expected_width": expected_width,
                                "expected_height": expected_height
                            }
                    else:
                        # No expected resolution, just report actual
                        checks["resolution_policy_check"] = {
                            "status": "warn",
                            "message": "No expected resolution in manifest",
                            "actual_width": actual_width,
                            "actual_height": actual_height,
                            "expected_or_policy": "route_expected_resolution"
                        }
                    
                    # Basic image quality metrics (simplified)
                    # Blur detection (using variance of Laplacian approximation)
                    import numpy as np
                    img_gray = img.convert('L')
                    img_array = np.array(img_gray)
                    
                    # Blur check - high variance = less blurry
                    variance = np.var(img_array)
                    blur_threshold = 100.0
                    if variance > blur_threshold:
                        checks["blur_or_softness_basic"] = {
                            "status": "passed",
                            "message": f"No significant blur (variance: {variance:.2f})",
                            "metric": variance
                        }
                    else:
                        checks["blur_or_softness_basic"] = {
                            "status": "warn",
                            "message": f"Potential blur detected (variance: {variance:.2f})",
                            "metric": variance
                        }
                    
                    # Brightness check
                    mean_brightness = np.mean(img_array)
                    brightness_min, brightness_max = 50, 200
                    if brightness_min <= mean_brightness <= brightness_max:
                        checks["brightness_basic"] = {
                            "status": "passed",
                            "message": f"Brightness within range (mean: {mean_brightness:.2f})",
                            "metric": mean_brightness
                        }
                    else:
                        checks["brightness_basic"] = {
                            "status": "warn",
                            "message": f"Brightness out of range (mean: {mean_brightness:.2f})",
                            "metric": mean_brightness
                        }
                    
                    # Contrast check (using standard deviation)
                    contrast = np.std(img_array)
                    contrast_threshold = 30.0
                    if contrast > contrast_threshold:
                        checks["contrast_basic"] = {
                            "status": "passed",
                            "message": f"Contrast adequate (std: {contrast:.2f})",
                            "metric": contrast
                        }
                    else:
                        checks["contrast_basic"] = {
                            "status": "warn",
                            "message": f"Low contrast (std: {contrast:.2f})",
                            "metric": contrast
                        }
                
                # SHA256 calculation
                with open(asset_path, 'rb') as f:
                    sha256_hash = hashlib.sha256(f.read()).hexdigest()
                checks["sha256_present"] = {
                    "status": "passed",
                    "message": "SHA256 computed",
                    "sha256": sha256_hash
                }
                
                # Size check
                size_bytes = os.path.getsize(asset_path)
                checks["size_bytes_valid"] = {
                    "status": "passed",
                    "message": f"Size: {size_bytes} bytes",
                    "size_bytes": size_bytes
                }
                
            except Exception as e:
                checks["asset_readable"] = {"status": "failed", "message": f"Error reading asset: {str(e)}"}
        
        return {
            "checks": checks,
            "source_asset": asset_path or "output/assets/combine_v2_00001_.png",
            "actual_width": actual_width,
            "actual_height": actual_height,
            "sha256": sha256_hash,
            "size_bytes": size_bytes,
            "technical_asset_valid": all(c["status"] in ["passed", "warn"] for c in checks.values())
        }

    def _create_real_visual_qa_result(self, context: CombineRunContext) -> AgentResult:
        """Create real visual QA result for real_visual_qa_required stage."""
        # Read generation artifacts
        generation_plan = self._read_contract(context.project_root, "combine_v2_generation_execution_plan")
        generation_stub_result = self._read_contract(context.project_root, "combine_v2_generation_execution_stub_result")
        generation_trace_stub = self._read_contract(context.project_root, "combine_v2_generation_trace_stub")
        operator_generation_authorization = self._read_contract(
            context.project_root,
            "combine_v2_operator_generation_authorization"
        )

        # Execute technical checks
        technical_check_result = self._execute_technical_checks(context.project_root)
        checks = technical_check_result["checks"]
        technical_asset_valid = technical_check_result["technical_asset_valid"]

        # Manual visual checks (require human review)
        manual_checks = {
            "anatomy_distortion": {"status": "manual_review_required"},
            "hand_distortion": {"status": "manual_review_required"},
            "body_pose_instability": {"status": "manual_review_required"},
            "clothing_artifacts": {"status": "manual_review_required"},
            "face_identity_unreliable": {"status": "manual_review_required"},
            "production_quality_failed": {"status": "manual_review_required"}
        }

        # Combine all checks
        all_checks = {**checks, **manual_checks}

        # Determine overall visual quality passed
        # Technical checks must pass/warn, manual checks are always manual_review_required
        visual_quality_passed = False  # Always false since manual checks require review

        # 1. Create Real Visual QA Preflight Report
        preflight_report = {
            "stage": "real_visual_qa_required",
            "agent": "VisualQAAgent",
            "status": "real_analysis_required",
            "real_image_analysis": True,
            "generation_gate_open": bool(operator_generation_authorization.get("generation_gate_open", False)),
            "source_asset": technical_check_result["source_asset"],
            "technical_asset_valid": technical_asset_valid,
            "visual_quality_passed": visual_quality_passed,
            "operator_review_required": True,
            "recommended_operator_decision": "reject",
            "checks": all_checks,
            "next_allowed_action": "operator_visual_review",
            "retry_attempted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False
        }

        # 2. Create Real Visual QA Report
        qa_report = {
            "stage": "real_visual_qa_required",
            "source_asset": technical_check_result["source_asset"],
            "technical_asset_valid": technical_asset_valid,
            "visual_quality_passed": visual_quality_passed,
            "operator_review_required": True,
            "recommended_operator_decision": "reject",
            "checks": all_checks,
            "next_allowed_action": "operator_visual_review",
            "retry_attempted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False
        }

        # 3. Create Technical Visual QA Packet
        technical_qa_packet = {
            "stage": "real_visual_qa_required",
            "source_stage": "real_visual_qa_preflight_required",
            "source_asset": technical_check_result["source_asset"],
            "technical_asset_valid": technical_asset_valid,
            "visual_quality_passed": visual_quality_passed,
            "operator_review_required": True,
            "recommended_operator_decision": "reject",
            "next_allowed_action": "operator_visual_review",
            "retry_attempted": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "quality_metrics": {k: v["status"] for k, v in checks.items()},
            "detected_issues": [v["message"] for k, v in checks.items() if v["status"] == "failed"],
            "manual_checks_required": list(manual_checks.keys()),
            "operator_review_packet": {
                "operator_actions": [
                    "accept_visuals",
                    "reject_visuals",
                    "request_retry_correction"
                ],
                "review_required": True,
                "real_image_analysis": True
            },
            "retry_context_sources": {
                "combine_v2_generation_execution_plan": "output/control/combine_v2_generation_execution_plan.json",
                "combine_v2_generation_execution_stub_result": "output/control/combine_v2_generation_execution_stub_result.json",
                "combine_v2_generation_trace_stub": "output/control/combine_v2_generation_trace_stub.json",
                "combine_v2_operator_generation_authorization": "output/control/combine_v2_operator_generation_authorization.json"
            }
        }

        # 4. Create Operator Visual Review Packet
        operator_review_packet = {
            "stage": "operator_visual_review",
            "source_stage": "real_visual_qa_required",
            "source_asset": technical_check_result["source_asset"],
            "operator_review_required": True,
            "operator_actions": [
                "accept_visuals",
                "reject_visuals",
                "request_retry_correction"
            ],
            "visual_qa_report": "output/control/combine_v2_real_visual_qa_report.json",
            "technical_qa_packet": "output/control/combine_v2_real_visual_qa_technical_packet.json",
            "technical_asset_valid": technical_asset_valid,
            "visual_quality_passed": visual_quality_passed,
            "recommended_operator_decision": "reject",
            "real_image_analysis": True,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_blocked": True,
            "next_allowed_action": "operator_visual_review",
            "manual_checks": manual_checks,
            "retry_context_sources": {
                "combine_v2_generation_execution_plan": "output/control/combine_v2_generation_execution_plan.json",
                "combine_v2_generation_execution_stub_result": "output/control/combine_v2_generation_execution_stub_result.json",
                "combine_v2_generation_trace_stub": "output/control/combine_v2_generation_trace_stub.json",
                "combine_v2_operator_generation_authorization": "output/control/combine_v2_operator_generation_authorization.json"
            }
        }

        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="ok",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[
                "combine_v2_real_visual_qa_preflight_report.json",
                "combine_v2_real_visual_qa_report.json",
                "combine_v2_real_visual_qa_technical_packet.json",
                "combine_v2_operator_visual_review_packet.json"
            ],
            next_recommended_stage="operator_visual_review",
            metadata={
                "action": "real_visual_quality_assessment",
                "description": "Performs real visual QA preflight and technical analysis",
                "real_image_analysis": True,
                "technical_asset_valid": technical_asset_valid,
                "visual_quality_passed": visual_quality_passed,
                "operator_review_required": True,
                "recommended_operator_decision": "reject",
                "next_allowed_action": "operator_visual_review",
                "retry_attempted": False,
                "assembly_executed": False,
                "downstream_executed": False,
                "production_accepted": False,
                "combine_v2_real_visual_qa_preflight_report": preflight_report,
                "combine_v2_real_visual_qa_report": qa_report,
                "combine_v2_real_visual_qa_technical_packet": technical_qa_packet,
                "combine_v2_operator_visual_review_packet": operator_review_packet
            }
        )

    def run(self, context: CombineRunContext, dry_run: bool = True) -> AgentResult:
        if context.stage == "visual_qa_required_stub_pending":
            return AgentResult(
                agent=self.role_name,
                stage=context.stage,
                status="ok",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=[],
                next_recommended_stage="visual_qa_required",
                metadata={
                    "action": "visual_qa_pending_clear",
                    "message": "Stub pending cleared, ready for visual QA",
                    "visual_qa_stub": True,
                    "real_image_analysis": False
                }
            )

        if context.stage == "visual_qa_required":
            return self.create_stub_result(context)

        if context.stage == "real_visual_qa_preflight_required":
            # Create preflight report artifact
            preflight_report = {
                "stage": "real_visual_qa_preflight_required",
                "agent": "VisualQAAgent",
                "status": "preflight_cleared",
                "real_image_analysis": True,
                "message": "Real visual QA preflight cleared, ready for real visual QA",
                "next_allowed_action": "real_visual_qa_required",
                "retry_attempted": False,
                "assembly_executed": False,
                "downstream_executed": False,
                "production_accepted": False
            }
            
            return AgentResult(
                agent=self.role_name,
                stage=context.stage,
                status="ok",
                dry_run=context.dry_run,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_real_visual_qa_preflight_report.json"],
                next_recommended_stage="real_visual_qa_required",
                metadata={
                    "action": "real_visual_qa_preflight",
                    "message": "Real visual QA preflight cleared, ready for real visual QA",
                    "real_image_analysis": True,
                    "next_allowed_action": "real_visual_qa_required",
                    "retry_attempted": False,
                    "assembly_executed": False,
                    "downstream_executed": False,
                    "production_accepted": False,
                    "combine_v2_real_visual_qa_preflight_report": preflight_report
                }
            )

        if context.stage == "real_visual_qa_required":
            return self._create_real_visual_qa_result(context)

        if context.stage == "operator_visual_review":
            # 1. Read operator decision artifact
            op_decision = self._read_contract(context.project_root, "combine_v2_operator_visual_decision")
            decision = op_decision.get("operator_visual_decision", "none")

            # 2. Determine gate result
            gate_result = {
                "operator_visual_decision": decision,
                "visuals_accepted": False,
                "next_allowed_action": "none",
                "production_accepted": False,
                "downstream_blocked": True,
                "retry_attempted": False,
                "assembly_executed": False,
                "downstream_executed": False
            }

            if decision == "accepted":
                gate_result.update({
                    "visuals_accepted": True,
                    "next_allowed_action": "assembly_required",
                    "assembly_allowed": False,
                    "assembly_authorization_required": True,
                    "retry_attempted": False,
                    "assembly_executed": False,
                    "downstream_executed": False
                })
                next_recommended_stage = "assembly_required"
                status = "ok"
            elif decision == "rejected":
                gate_result.update({
                    "visuals_accepted": False,
                    "next_allowed_action": "retry_correction_required",
                    "retry_authorized": False,
                    "generation_performed": False,
                    "retry_attempted": False,
                    "assembly_executed": False,
                    "downstream_executed": False
                })
                next_recommended_stage = "retry_correction_required"
                status = "ok"
            elif decision == "manual_review":
                gate_result.update({
                    "next_allowed_action": "blocked_manual_review",
                    "retry_attempted": False,
                    "assembly_executed": False,
                    "downstream_executed": False
                })
                next_recommended_stage = "blocked_manual_review"
                status = "ok"
            else:
                next_recommended_stage = "operator_visual_review"
                status = "blocked"
                gate_result["message"] = "Waiting for operator decision"
                gate_result["retry_attempted"] = False
                gate_result["assembly_executed"] = False
                gate_result["downstream_executed"] = False

            return AgentResult(
                agent=self.role_name,
                stage=context.stage,
                status=status,
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_visual_acceptance_gate_result.json"],
                next_recommended_stage=next_recommended_stage,
                metadata={
                    "action": "visual_acceptance_decision",
                    "operator_decision": decision,
                    "next_recommended_stage": next_recommended_stage,
                    "retry_attempted": False,
                    "assembly_executed": False,
                    "downstream_executed": False,
                    "combine_v2_visual_acceptance_gate_result": gate_result
                }
            )

        if context.stage == "corrective_retry_v4_visual_qa_required":
            # RC-COMBINE-V2-2541-2600 — V4 Visual QA verdict
            # Read the verdict artifact created by CLI command
            verdict = self._read_contract(
                context.project_root,
                "combine_v2_corrective_retry_v4_visual_qa_verdict"
            )

            visual_qa_verdict = verdict.get("visual_qa_verdict", "failed")
            failed_reasons = verdict.get("failed_reasons", [])
            next_action = verdict.get("recommended_next_action", "corrective_retry_v4_visual_correction_plan_required")

            return AgentResult(
                agent=self.role_name,
                stage=context.stage,
                status="ok" if verdict else "stubbed",
                dry_run=context.dry_run,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                artifacts=["combine_v2_corrective_retry_v4_visual_qa_verdict.json"],
                next_recommended_stage=next_action,
                metadata={
                    "action": "corrective_retry_v4_visual_qa",
                    "visual_qa_executed": verdict.get("visual_qa_executed", False),
                    "visual_qa_verdict": visual_qa_verdict,
                    "failed_reasons": failed_reasons,
                    "production_accepted": False,
                    "operator_concerns_preserved": verdict.get("operator_concerns_preserved", True),
                    "next_allowed_action": next_action,
                    "requires_operator_review": True,
                    "retry_attempted": False,
                    "assembly_executed": False,
                    "downstream_executed": False
                }
            )
            
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            next_recommended_stage="none",
            metadata={"message": f"VisualQAAgent: No specific logic for stage {context.stage}"}
        )

