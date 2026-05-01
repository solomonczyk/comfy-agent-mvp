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
        return ["visual_qa_required_stub_pending", "visual_qa_required", "operator_visual_review"]
    
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
                "downstream_blocked": True
            }
            
            if decision == "accepted":
                gate_result.update({
                    "visuals_accepted": True,
                    "next_allowed_action": "assembly_required",
                    "assembly_allowed": False,
                    "assembly_authorization_required": True
                })
                next_recommended_stage = "assembly_required"
                status = "ok"
            elif decision == "rejected":
                gate_result.update({
                    "visuals_accepted": False,
                    "next_allowed_action": "retry_correction_required",
                    "retry_authorized": False,
                    "generation_performed": False
                })
                next_recommended_stage = "retry_correction_required"
                status = "ok"
            elif decision == "manual_review":
                gate_result.update({
                    "next_allowed_action": "blocked_manual_review"
                })
                next_recommended_stage = "blocked_manual_review"
                status = "ok"
            else:
                next_recommended_stage = "operator_visual_review"
                status = "blocked"
                gate_result["message"] = "Waiting for operator decision"
                
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
                    "combine_v2_visual_acceptance_gate_result": gate_result
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

