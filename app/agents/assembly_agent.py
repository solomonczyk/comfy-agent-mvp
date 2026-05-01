"""Assembly Agent - stub implementation.

Assembles final outputs from components.
Optional for single-image routes.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class AssemblyAgent(BaseRoleAgent):
    """Assembly agent for combining components into final outputs.
    
    Assembles scenes, episodes, or final deliverables.
    Not required for single-image output routes.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["assembly_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "AssemblyContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        route_family = context.route_family or context.metadata.get("route_family", "custom")
        
        # Not required for single-image output routes
        single_image_routes = ["portrait_character_identity", "product_visual", "ugc_testimonial"]
        not_required = route_family in single_image_routes
        
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[],
            next_recommended_stage="final_qc_required",
            not_required_for_route=not_required,
            metadata={
                "action": "assemble_outputs",
                "route_family": route_family,
                "not_required_reason": "single_image_output" if not_required else None,
                "description": "Assembles final outputs (not required for single-image routes)"
            }
        )
