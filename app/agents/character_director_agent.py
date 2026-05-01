"""Character Director Agent - stub implementation.

Manages character consistency and identity across shots.
Optional for routes without characters.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class CharacterDirectorAgent(BaseRoleAgent):
    """Character direction and consistency agent.
    
    Ensures character identity and consistency across production.
    Not required for routes without character elements.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["production_plan_review", "asset_resolution_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "CharacterDirectionContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        route_family = context.route_family or context.metadata.get("route_family", "custom")
        
        # Not required for routes without characters
        character_routes = ["portrait_character_identity", "cinematic_scene", "educational_explainer"]
        has_characters = route_family in character_routes
        not_required = not has_characters
        
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
                "action": "manage_character_consistency",
                "route_family": route_family,
                "has_characters": has_characters,
                "description": "Manages character identity (not required for non-character routes)"
            }
        )
