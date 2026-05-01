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
        return ["visual_qa_required_stub_pending", "visual_qa_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root"]
    
    @property
    def output_contract_type(self) -> str:
        return "VisualQAContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        """Create a stub result for the visual_qa_required stage."""
        
        # 1. Create Visual QA Stub Report
        stub_report = {
            "stage": "visual_qa_required",
            "agent": "VisualQAAgent",
            "status": "stubbed",
            "real_image_analysis": False,
            "checks_declared": [
                "artifact_presence_check",
                "dimensions_check",
                "blur_softness_check",
                "composition_check",
                "route_policy_check"
            ],
            "checks_executed": [],
            "operator_review_required": True,
            "visual_qa_passed": False,
            "final_verdict": "operator_review_required",
            "generation_performed": False,
            "comfyui_execution": False,
            "downstream_executed": False
        }
        
        # 2. Create Operator Visual Review Packet
        review_packet = {
            "stage": "operator_visual_review",
            "source_stage": "visual_qa_required",
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
            "downstream_blocked": True
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
                "visual_qa_stub": True,
                "real_image_analysis": False,
                "operator_review_required": True,
                "visual_qa_passed": False,
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
