"""Script/Scenario Agent - stub implementation.

Develops script or scenario from brief. Optional for still-image routes.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class ScriptScenarioAgent(BaseRoleAgent):
    """Script and scenario development agent.
    
    Creates script/scenario for multi-shot or video production.
    Not required for still-image routes without script requirements.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["production_plan_required", "asset_resolution_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "ScriptScenarioContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        route_family = context.route_family or context.metadata.get("route_family", "custom")
        
        # Not required for still-image routes without script
        still_image_routes = ["portrait_character_identity", "product_visual", "ugc_testimonial"]
        not_required = route_family in still_image_routes
        
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
            not_required_for_route=not_required,
            metadata={
                "action": "develop_script_scenario",
                "route_family": route_family,
                "not_required_reason": "still_image_route" if not_required else None,
                "description": "Develops script/scenario (optional for still images)"
            }
        )
