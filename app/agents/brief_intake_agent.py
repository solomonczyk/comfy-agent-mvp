"""Brief Intake Agent - stub implementation.

Handles initial brief parsing and validation.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class BriefIntakeAgent(BaseRoleAgent):
    """Intake agent for initial brief processing.
    
    This agent would normally parse and validate briefs.
    In this stub layer, it only returns a structured result.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["brief_intake_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root"]
    
    @property
    def output_contract_type(self) -> str:
        return "BriefIntakeContract"
    
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
            next_recommended_stage="route_classification_required",
            metadata={
                "action": "parse_and_validate_brief",
                "description": "Would parse brief.md and validate structure",
                "route_agnostic": True
            }
        )
