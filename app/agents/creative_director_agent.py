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
        stage = context.stage
        
        # Optional for simpler production routes
        simple_routes = ["ugc_testimonial", "social_short_vertical", "batch_variations"]
        not_required = route_family in simple_routes
        
        artifacts = []
        metadata = {
            "action": "set_creative_direction",
            "route_family": route_family,
            "not_required_reason": "simple_route" if not_required else None,
            "description": "Provides creative direction and preflight"
        }
        
        next_stage = "asset_resolution_required"
        
        if stage == "production_plan_review":
            next_stage = "asset_resolution_required"
        elif stage == "workflow_preflight_required":
            next_stage = "generation_authorization_required"
        
        return AgentResult(
            agent=self.role_name,
            stage=stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=artifacts,
            next_recommended_stage=next_stage,
            not_required_for_route=not_required,
            metadata=metadata
        )
