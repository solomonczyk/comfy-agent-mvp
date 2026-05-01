"""Generation Agent - stub implementation.

Coordinates generation execution. In this layer, generation is
explicitly refused and stubbed only. No real ComfyUI execution occurs.

CRITICAL: This agent exists as a role but refuses actual generation.
"""

from typing import List, Dict, Any
from app.agents.base import BaseRoleAgent, AgentResult
from app.orchestrator.contracts import CombineRunContext


class GenerationAgent(BaseRoleAgent):
    """Generation coordination agent (stub only).
    
    THIS AGENT REFUSES REAL GENERATION. It exists to fulfill the role
    structure but returns stub results only. No ComfyUI execution,
    no actual generation, no downstream actions.
    
    This ensures the role-agent protocol is complete while maintaining
    the no-generation boundary for this layer.
    """
    
    @property
    def supported_stages(self) -> List[str]:
        return ["generate_assets"]
    
    @property
    def required_inputs(self) -> List[str]:
        return ["project_root", "route_family"]
    
    @property
    def output_contract_type(self) -> str:
        return "GenerationExecutionContract"
    
    def validate_inputs(self, context: CombineRunContext) -> bool:
        return bool(context.project_root)
    
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        return AgentResult(
            agent=self.role_name,
            stage=context.stage,
            status="stubbed",
            dry_run=True,  # Always True - generation refused
            generation_performed=False,  # Always False - generation refused
            comfyui_execution=False,  # Always False - no ComfyUI
            downstream_executed=False,  # Always False - no downstream
            artifacts=[],
            next_recommended_stage="visual_qa_required",
            metadata={
                "action": "generation_refused_stub_only",
                "generation_executed": False,
                "comfyui_called": False,
                "refusal_reason": "Layer boundary: generation refused in stub layer",
                "description": "Generation role exists but refuses execution (stub only)"
            }
        )
    
    def run(self, context: CombineRunContext, dry_run: bool = True) -> AgentResult:
        """Execute the generation agent.
        
        OVERRIDE: Always forces dry_run=True and returns stub result.
        Real generation is explicitly refused at this layer.
        """
        # Validate inputs
        if not self.validate_inputs(context):
            missing = set(self.required_inputs) - set(context.metadata.keys())
            return AgentResult(
                agent=self.role_name,
                stage=context.stage,
                status="error",
                dry_run=True,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                metadata={
                    "error": "validation_failed",
                    "missing_inputs": list(missing)
                }
            )
        
        # ALWAYS return stub - generation refused
        result = self.create_stub_result(context)
        result.dry_run = True  # Enforce
        result.generation_performed = False  # Enforce
        result.comfyui_execution = False  # Enforce
        result.downstream_executed = False  # Enforce
        
        return result
