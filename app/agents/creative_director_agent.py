"""Creative Director Agent - stub implementation.

Provides creative direction and quality standards.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class CreativeDirectorAgent(BaseRoleAgent):
    """Creative direction and quality standards agent.
    
    Sets creative vision and quality benchmarks.
    Optional for simpler routes without creative review needs.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["production_plan_review", "workflow_preflight_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "CreativeDirectionContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        route_family = context.route_family or context.metadata.get("route_family", "custom")
        
        # Optional for simpler production routes
        simple_routes = ["ugc_testimonial", "social_short_vertical", "batch_variations"]
        not_required = route_family in simple_routes
        
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[],
            next_recommended_stage="asset_resolution_required",
            not_required_for_route=not_required,
            metadata={
                "action": "set_creative_direction",
                "route_family": route_family,
                "not_required_reason": "simple_route" if not_required else None,
                "description": "Provides creative direction (optional for simple routes)"
            }
        )
