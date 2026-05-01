"""Brief Intake Agent - stub implementation.

Handles initial brief parsing and validation.
No real generation or ComfyUI execution.
"""

from datetime import datetime
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
        brief_file = context.metadata.get("brief_file", "brief.md")
        
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=["combine_v2_brief_contract.json"],
            next_recommended_stage="route_classification_required",
            metadata={
                "action": "parse_and_validate_brief",
                "brief_file": brief_file,
                "combine_v2_brief_contract": {
                    "brief_file": brief_file,
                    "parsed_at": datetime.utcnow().isoformat(),
                    "status": "valid",
                    "content_summary": "Stubbed brief content"
                },
                "description": "Parses brief.md and validates structure",
                "route_agnostic": True
            }
        )
