"""Retry Policy Agent - stub implementation.

Determines retry and correction policies for failed stages.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class RetryPolicyAgent(BaseRoleAgent):
    """Retry and correction policy agent.
    
    Determines appropriate retry strategy for failed stages.
    Pure stub - no actual retry execution.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["retry_correction_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root"]
    
    @property
    def output_contract_type(self) -> str:
        return "RetryPolicyContract"
    
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
            next_recommended_stage="workflow_plan_required",
            metadata={
                "action": "determine_retry_policy",
                "description": "Determines retry strategy (stub only)"
            }
        )
