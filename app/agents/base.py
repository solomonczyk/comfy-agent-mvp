"""Base role agent protocol for Combine universal agent system.

Defines the BaseRoleAgent protocol and structured result format for all
stub agents. No real generation or ComfyUI execution occurs here.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from app.orchestrator.contracts import CombineRunContext


@dataclass
class AgentResult:
    """Structured result returned by every role agent.
    
    Every agent must return a result matching this structure to ensure
    consistency across the universal role agent protocol.
    
    Attributes:
        agent: Name of the agent class
        stage: Current stage identifier
        status: Execution status (always "stubbed" for this layer)
        dry_run: Whether this was a dry run
        generation_performed: Always False - no real generation
        comfyui_execution: Always False - no ComfyUI execution
        downstream_executed: Always False - no downstream actions
        artifacts: List of artifact identifiers (empty for stubs)
        next_recommended_stage: Next stage the orchestrator should consider
        metadata: Additional context about the execution
        not_required_for_route: Whether this agent is optional for current route
    """
    agent: str
    stage: str
    status: str = "stubbed"
    dry_run: bool = True
    generation_performed: bool = False
    comfyui_execution: bool = False
    downstream_executed: bool = False
    artifacts: List[str] = field(default_factory=list)
    next_recommended_stage: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    not_required_for_route: bool = False


class BaseRoleAgent(ABC):
    """Base protocol for all role agents in the Combine system.
    
    Every role agent must implement this protocol. Key design principles:
    
    1. No real generation: Agents in this layer are stubs only
    2. No ComfyUI: This layer does not call ComfyUI or downstream services
    3. Route-aware optionality: Agents can mark themselves as not_required_for_route
    4. Universal structure: All agents return AgentResult with consistent format
    5. No UGC/Metas/portrait/product anchoring: These are routes, not defaults
    
    Attributes:
        role_name: Unique identifier for this agent's role
        supported_stages: List of stages this agent can execute
        required_inputs: List of input keys required from context
        output_contract_type: Type name of the output contract
    """
    
    def __init__(self):
        self.role_name = self.__class__.__name__
    
    @property
    @abstractmethod
    def supported_stages(self) -> List[str]:
        """List of stage identifiers this agent can handle."""
        pass
    
    @property
    @abstractmethod
    def required_inputs(self) -> List[str]:
        """List of required input keys from the run context."""
        pass
    
    @property
    @abstractmethod
    def output_contract_type(self) -> str:
        """Type identifier for the output contract."""
        pass
    
    @abstractmethod
    def validate_inputs(self, context: CombineRunContext) -> bool:
        """Validate that required inputs are present in context.
        
        Args:
            context: The run context to validate
            
        Returns:
            True if all required inputs are present, False otherwise
        """
        pass
    
    @abstractmethod
    def create_stub_result(self, context: CombineRunContext) -> AgentResult:
        """Create a stub result for dry-run execution.
        
        This method MUST NOT perform any real generation, ComfyUI execution,
        or downstream actions. It only creates a structured result indicating
        what would happen if this agent were to execute.
        
        Args:
            context: The run context with project information
            
        Returns:
            AgentResult with stubbed execution details
        """
        pass
    
    def run(self, context: CombineRunContext, dry_run: bool = True) -> AgentResult:
        """Execute the agent for the given context.
        
        This is the main entry point for orchestrator dispatch. In this
        layer, execution is always stubbed/dry-run only.
        
        Args:
            context: The run context with project and stage information
            dry_run: If True, perform dry run (always True in this layer)
            
        Returns:
            AgentResult with execution details (always stubbed)
        """
        # Validate inputs
        if not self.validate_inputs(context):
            missing = set(self.required_inputs) - set(context.metadata.keys())
            return AgentResult(
                agent=self.role_name,
                stage=context.stage,
                status="error",
                dry_run=dry_run,
                generation_performed=False,
                comfyui_execution=False,
                downstream_executed=False,
                metadata={
                    "error": "validation_failed",
                    "missing_inputs": list(missing)
                }
            )
        
        # Always return stub result in this layer
        result = self.create_stub_result(context)
        result.dry_run = True  # Enforce dry-run for this layer
        result.generation_performed = False  # Enforce no generation
        result.comfyui_execution = False  # Enforce no ComfyUI
        result.downstream_executed = False  # Enforce no downstream
        
        return result
