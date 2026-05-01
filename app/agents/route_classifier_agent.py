"""Route Classifier Agent - stub implementation.

Classifies the brief into a route family without anchoring to any
specific route as default. All routes are treated equally.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class RouteClassifierAgent(BaseRoleAgent):
    """Route classification agent for determining route family.
    
    Uses the route family registry to classify briefs into route families.
    No single route family is treated as a universal default - all are
    route options with equal standing. UGC, Meta, portrait, and product
    are routes only, not core assumptions.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["route_classification_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "RouteClassificationContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        route_family = context.metadata.get("route_family", "custom")
        route_policy = context.metadata.get("route_policy", {})
        
        # Determine if this agent is required for the route
        # All routes need classification, so always required
        not_required = False
        
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[],
            next_recommended_stage="production_plan_required",
            not_required_for_route=not_required,
            metadata={
                "action": "classify_route",
                "route_family": route_family,
                "route_policy": route_policy,
                "description": "Classifies brief into route family without universal defaults",
                "anchor_proof": {
                    "no_ugc_default": True,
                    "no_meta_default": True,
                    "no_portrait_default": True,
                    "no_product_default": True,
                    "all_routes_equal": True
                }
            }
        )
