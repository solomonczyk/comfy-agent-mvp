"""Prompt Composition Agent - stub implementation.

Composes and optimizes generation prompts.
No real generation or ComfyUI execution.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class PromptCompositionAgent(BaseRoleAgent):
    """Prompt composition and optimization agent.
    
    Crafts and refines generation prompts from creative direction.
    Pure stub - no actual prompt execution.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["workflow_plan_required", "workflow_preflight_required", "generation_authorization_required"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "PromptCompositionContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        contract_name = "combine_v2_prompt_contract"
        contract_file = f"{contract_name}.json"
        
        contract_data = {
            "agent": self.role_name,
            "stage": context.stage,
            "prompts": {
                "positive": "A professional cinematic shot of a person in an office, high quality, 8k",
                "negative": "low quality, blurry, distorted"
            },
            "status": "composed"
        }
        
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=context.dry_run,
            generation_performed=False,
            comfyui_execution=False,
            downstream_executed=False,
            artifacts=[contract_file],
            next_recommended_stage="generation_authorization_required",
            metadata={
                "action": "compose_prompts",
                "description": "Composes and optimizes prompts (no execution)",
                contract_name: contract_data
            }
        )
