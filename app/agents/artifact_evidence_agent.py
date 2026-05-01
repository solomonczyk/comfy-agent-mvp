"""Artifact Evidence Agent - stub implementation.

Collects and validates evidence from generated artifacts.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class ArtifactEvidenceAgent(BaseRoleAgent):
    """Artifact evidence collection and validation agent.
    
    Gathers evidence from generation artifacts for QA review.
    Stub only - no actual artifact generation or processing.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["visual_qa_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root"]
    
    @property
    def output_contract_type(self) -> str:
        return "ArtifactEvidenceContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[],
            next_recommended_stage="operator_visual_review",
            metadata={
                "action": "collect_artifact_evidence",
                "description": "Collects evidence from artifacts (stub only)"
            }
        )
