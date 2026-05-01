"""Workflow TD Agent - stub implementation.

Technical direction for workflow assembly and configuration.
Optional based on route requirements.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class WorkflowTDAgent(BaseRoleAgent):
    """Workflow technical direction agent.
    
    Provides technical workflow configuration and assembly direction.
    Optional for routes with simpler workflow needs.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["workflow_plan_required", "workflow_preflight_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "WorkflowTDContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        route_family = context.route_family or context.metadata.get("route_family", "custom")
        
        # Optional for simpler workflows
        simple_workflow_routes = ["ugc_testimonial", "social_short_vertical", "batch_variations"]
        not_required = route_family in simple_workflow_routes
        
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[],
            next_recommended_stage="generation_authorization_required",
            not_required_for_route=not_required,
            metadata={
                "action": "technical_workflow_direction",
                "route_family": route_family,
                "not_required_reason": "simple_workflow" if not_required else None,
                "description": "Provides workflow TD (optional for simple workflows)"
            }
        )
