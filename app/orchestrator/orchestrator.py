"""
Combine Internal Orchestrator with Universal Role Agent Protocol

Thin orchestrator skeleton for the internal multi-agent system.
This orchestrator manages state, routes, stage execution, and dispatches
to role agents. No real generation or ComfyUI execution occurs at this layer.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from .contracts import (
    CombineStatus,
    CombineRunContext,
    CombineStageResult,
    StageTransitionRequest,
    StageTransitionResult
)
from .state_machine import CombineStateMachine
from .routing import RouteFamilyRegistry


class CombineOrchestrator:
    """Internal orchestrator for Combine multi-agent system"""
    
    # Stage-to-role-agent mapping for dispatch
    _stage_agent_map = {
        "brief_intake_required": "BriefIntakeAgent",
        "route_classification_required": "RouteClassifierAgent",
        "production_plan_required": "StrategyIntentAgent",
        "production_plan_review": "CreativeDirectorAgent",
        "asset_resolution_required": "AssetResolverAgent",
        "workflow_plan_required": "WorkflowTDAgent",
        "workflow_preflight_required": "PromptCompositionAgent",
        "generation_authorization_required": "GenerationAgent",
        "operator_generation_authorization_required": "GenerationAgent",
        "generate_assets": "GenerationAgent",
        "visual_qa_required_stub_pending": "VisualQAAgent",
        "visual_qa_required": "VisualQAAgent",
        "operator_visual_review": "VisualQAAgent",
        "corrective_retry_plan_required": "RetryPolicyAgent",
        "controlled_retry_authorization_required": "RetryPolicyAgent",
        "corrective_retry_implementation_required": "RetryPolicyAgent",
        "real_generation_readiness_required": "RealGenerationReadinessAgent",
        "real_generation_preflight_required": "RealGenerationReadinessAgent",
        "real_generation_payload_review": "GenerationAgent",
        "operator_real_generation_authorization_required": "RealGenerationReadinessAgent",
        "operator_real_generation_approved": "RealGenerationReadinessAgent",
        "real_generate_assets": "GenerationAgent",
        "real_generation_result_collected": "GenerationAgent",
        "real_generation_result_review_required": "GenerationAgent",
        "real_visual_qa_preflight_required": "VisualQAAgent",
        "real_visual_qa_required": "VisualQAAgent",
        "retry_correction_required": "RetryPolicyAgent",
        "corrective_retry_payload_rebuild_required": "GenerationAgent",
        "controlled_asset_resolution_review_required": "AssetResolverAgent",
        "production_brain_audit_required": "ProductionBrainAgent",
        "visual_failure_audit_required": "ProductionBrainAgent",
        "generation_recipe_audit_required": "ProductionBrainAgent",
        "workflow_rebuild_plan_required": "ProductionBrainAgent",
        "operator_strategy_review": "ProductionBrainAgent",
        "workflow_td_rebuild_required": "WorkflowTDRebuildAgent",
        "recipe_rebuild_contract_required": "WorkflowTDRebuildAgent",
        "prompt_contract_rebuild_required": "WorkflowTDRebuildAgent",
        "quality_pipeline_contract_required": "WorkflowTDRebuildAgent",
        "workflow_rebuild_preflight_required": "WorkflowTDRebuildAgent",
        "operator_rebuild_approval_required": "WorkflowTDRebuildAgent",
        "operator_rebuild_approved": "WorkflowRecipeImplementationAgent",
        "workflow_recipe_implementation_required": "WorkflowRecipeImplementationAgent",
        "generation_payload_rebuild_required": "WorkflowRecipeImplementationAgent",
        "workflow_graph_rebuild_required": "WorkflowRecipeImplementationAgent",
        "workflow_rebuild_validation_required": "WorkflowRecipeImplementationAgent",
        "real_generation_readiness_required": "WorkflowRecipeImplementationAgent",
        "assembly_required": "AssemblyAgent",
        "final_qc_required": "FinalQAAgent",
    }
    
    def __init__(self, project_root: str):
        """
        Initialize the orchestrator.
        
        Args:
            project_root: Path to the project root directory
        """
        self.project_root = Path(project_root)
        self.state_machine = CombineStateMachine()
        self.route_registry = RouteFamilyRegistry()
        
        # Lazy-loaded agent instances
        self._agents: Dict[str, Any] = {}
        
        # Ensure output/control directory exists
        self.control_dir = self.project_root / "output" / "control"
        
        # Artifact index path
        self.artifact_index_path = self.control_dir / "artifact_index.json"
        
        # Ledger path
        self.ledger_path = self.control_dir / "episode_ledger.json"
    
    def _read_artifact_index(self) -> Dict[str, Any]:
        """Read artifact index if it exists"""
        if self.artifact_index_path.exists():
            with open(self.artifact_index_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _read_ledger(self) -> List[Dict[str, Any]]:
        """Read ledger if it exists"""
        if self.ledger_path.exists():
            with open(self.ledger_path, 'r') as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        # Canonical format uses 'events' or 'records'
                        return data.get('events', data.get('records', []))
                except json.JSONDecodeError:
                    return []
        return []
    
    def _infer_current_state(self) -> str:
        """
        Infer current state from project structure.
        
        This is a safe inference that defaults to brief_intake_required
        if no state information is found.
        """
        artifact_index = self._read_artifact_index()
        ledger = self._read_ledger()
        
        # Check ledger for last state
        if ledger:
            last_event = ledger[-1]
            if "to_state" in last_event:
                return last_event["to_state"]
        
        # Check artifact index for state
        if "current_state" in artifact_index:
            return artifact_index["current_state"]
        
        # Default to initial state
        return "initial"
    
    def _get_next_allowed_action(self, current_state: str) -> str:
        """Get next allowed action based on current state"""
        # 1. Try to get recommendation from last stage result
        artifact_index = self._read_artifact_index()
        if "stage_results" in artifact_index and artifact_index["stage_results"]:
            last_result = artifact_index["stage_results"][-1]
            if last_result.get("stage") == current_state:
                metadata = last_result.get("metadata", {})
                explicit_next_action = metadata.get("next_allowed_action")
                if explicit_next_action and explicit_next_action != "none":
                    return explicit_next_action

                recommended = metadata.get("next_recommended_stage")
                if recommended and recommended != "none":
                    # Validate if it's an allowed transition
                    if self.state_machine.can_transition(current_state, recommended):
                        return recommended

        # 2. Check artifact_index explicit next_allowed_action
        explicit_next = artifact_index.get("next_allowed_action")
        if explicit_next and explicit_next != "none":
            if explicit_next == current_state or self.state_machine.can_transition(current_state, explicit_next):
                return explicit_next

        # 3. Fallback to state machine default
        allowed_states = self.state_machine.get_allowed_next_states(current_state)
        if allowed_states:
            return allowed_states[0]
        return "none"
    
    def _get_route_family(self) -> str:
        """Get current route family from artifact index"""
        artifact_index = self._read_artifact_index()
        return artifact_index.get("route_family", "custom")
    
    def _get_route_policy(self, route_family: str) -> Dict[str, Any]:
        """Get route family policy"""
        if self.route_registry.is_supported_route_family(route_family):
            return self.route_registry.get_route_family_policy(route_family)
        return {}
    
    # ------------------------------------------------------------------
    # Role Agent Registry and Dispatch
    # ------------------------------------------------------------------
    
    def _load_agent(self, agent_name: str) -> Any:
        """Lazy-load a role agent instance by name.
        
        Avoids circular imports by loading agents on demand.
        """
        if agent_name in self._agents:
            return self._agents[agent_name]
        
        # Import agent classes (avoid circular imports)
        try:
            if agent_name == "BriefIntakeAgent":
                from app.agents.brief_intake_agent import BriefIntakeAgent
                agent = BriefIntakeAgent()
            elif agent_name == "RouteClassifierAgent":
                from app.agents.route_classifier_agent import RouteClassifierAgent
                agent = RouteClassifierAgent()
            elif agent_name == "StrategyIntentAgent":
                from app.agents.strategy_intent_agent import StrategyIntentAgent
                agent = StrategyIntentAgent()
            elif agent_name == "CreativeDirectorAgent":
                from app.agents.creative_director_agent import CreativeDirectorAgent
                agent = CreativeDirectorAgent()
            elif agent_name == "ScriptScenarioAgent":
                from app.agents.script_scenario_agent import ScriptScenarioAgent
                agent = ScriptScenarioAgent()
            elif agent_name == "CharacterDirectorAgent":
                from app.agents.character_director_agent import CharacterDirectorAgent
                agent = CharacterDirectorAgent()
            elif agent_name == "PromptCompositionAgent":
                from app.agents.prompt_composition_agent import PromptCompositionAgent
                agent = PromptCompositionAgent()
            elif agent_name == "WorkflowTDAgent":
                from app.agents.workflow_td_agent import WorkflowTDAgent
                agent = WorkflowTDAgent()
            elif agent_name == "AssetResolverAgent":
                from app.agents.asset_resolver_agent import AssetResolverAgent
                agent = AssetResolverAgent()
            elif agent_name == "GenerationAgent":
                from app.agents.generation_agent import GenerationAgent
                agent = GenerationAgent()
            elif agent_name == "VisualQAAgent":
                from app.agents.visual_qa_agent import VisualQAAgent
                agent = VisualQAAgent()
            elif agent_name == "ArtifactEvidenceAgent":
                from app.agents.artifact_evidence_agent import ArtifactEvidenceAgent
                agent = ArtifactEvidenceAgent()
            elif agent_name == "RetryPolicyAgent":
                from app.agents.retry_policy_agent import RetryPolicyAgent
                agent = RetryPolicyAgent()
            elif agent_name == "RealGenerationReadinessAgent":
                from app.agents.real_generation_readiness_agent import RealGenerationReadinessAgent
                agent = RealGenerationReadinessAgent()
            elif agent_name == "ProductionBrainAgent":
                from app.agents.production_brain_agent import ProductionBrainAgent
                agent = ProductionBrainAgent()
            elif agent_name == "WorkflowTDRebuildAgent":
                from app.agents.workflow_td_rebuild_agent import WorkflowTDRebuildAgent
                agent = WorkflowTDRebuildAgent()
            elif agent_name == "WorkflowRecipeImplementationAgent":
                from app.agents.workflow_recipe_implementation_agent import WorkflowRecipeImplementationAgent
                agent = WorkflowRecipeImplementationAgent()
            elif agent_name == "AssemblyAgent":
                from app.agents.assembly_agent import AssemblyAgent
                agent = AssemblyAgent()
            elif agent_name == "FinalQAAgent":
                from app.agents.final_qa_agent import FinalQAAgent
                agent = FinalQAAgent()
            else:
                raise ValueError(f"Unknown agent: {agent_name}")
            
            self._agents[agent_name] = agent
            return agent
        except ImportError as e:
            raise ImportError(f"Failed to load agent {agent_name}: {e}")
    
    def _dispatch_to_agent(self, stage: str, context: CombineRunContext) -> Dict[str, Any]:
        """Dispatch stage execution to the appropriate role agent.
        
        Args:
            stage: Stage identifier to execute
            context: Run context with project information
            
        Returns:
            Agent result dictionary
        """
        agent_name = self._stage_agent_map.get(stage)
        if not agent_name:
            # No specific agent mapped for this stage - return generic stub
            return {
                "agent": "GenericStageAgent",
                "stage": stage,
                "status": "stubbed",
                "dry_run": True,
                "generation_performed": False,
                "comfyui_execution": False,
                "downstream_executed": False,
                "next_recommended_stage": "none",
                "message": f"Stage {stage} has no dedicated agent (generic stub)"
            }
        
        # Load and run the agent
        agent = self._load_agent(agent_name)
        result = agent.run(context, dry_run=context.dry_run)
        
        # Convert AgentResult to dict for stage result
        return {
            "agent": result.agent,
            "stage": result.stage,
            "status": result.status,
            "dry_run": result.dry_run,
            "generation_performed": result.generation_performed,
            "comfyui_execution": result.comfyui_execution,
            "downstream_executed": result.downstream_executed,
            "not_required_for_route": result.not_required_for_route,
            "next_recommended_stage": result.next_recommended_stage,
            "artifacts": result.artifacts,
            "metadata": result.metadata
        }
    
    def get_status(self) -> CombineStatus:
        """
        Get current status of the Combine project.
        
        Returns:
            CombineStatus with current project state
        """
        current_state = self._infer_current_state()
        next_allowed_action = self._get_next_allowed_action(current_state)
        
        artifact_index = self._read_artifact_index()
        route_family = artifact_index.get("route_family")
        
        return CombineStatus(
            project_root=str(self.project_root),
            current_state=current_state,
            next_allowed_action=next_allowed_action,
            route_family=route_family,
            artifacts=artifact_index,
            ledger_events=self._read_ledger(),
            windsurf_runtime_dependency=False,
            generation_performed=False,
            comfyui_execution=False,
            combine_v2=True
        )
    
    def _validate_stage_execution(self, stage: str, current_state: str) -> bool:
        """
        Validate if a stage can be executed.
        
        Args:
            stage: Stage to execute
            current_state: Current state
            
        Returns:
            True if stage can be executed, False otherwise
        """
        # Check if stage matches current state
        if stage != current_state:
            # Check if stage is an allowed next state
            allowed_states = self.state_machine.get_allowed_next_states(current_state)
            if stage not in allowed_states:
                return False
        
        return True
    
    def _write_stage_result(self, result: CombineStageResult) -> None:
        """
        Write stage result to artifact index.
        
        Args:
            result: Stage execution result
        """
        artifact_index = self._read_artifact_index()
        
        # Update artifact index with stage result
        if "stage_results" not in artifact_index:
            artifact_index["stage_results"] = []
        
        artifact_index["stage_results"].append({
            "stage": result.stage,
            "success": result.success,
            "message": result.message,
            "artifacts": result.artifacts,
            "metadata": result.metadata,
            "timestamp": result.timestamp,
            "no_generation_performed": result.no_generation_performed
        })
        
        # Update current state
        artifact_index["current_state"] = result.stage
        
        # Write artifact index
        self.control_dir.mkdir(parents=True, exist_ok=True)
        with open(self.artifact_index_path, 'w') as f:
            json.dump(artifact_index, f, indent=2)
            
        # Write individual contract files if specified in artifacts
        # We look for metadata keys ending with '_contract'
        for artifact_name in result.artifacts:
            if artifact_name.endswith('.json'):
                # Try to find matching contract data in metadata
                contract_key = artifact_name.replace('.json', '')
                contract_data = result.metadata.get(contract_key)
                
                if contract_data:
                    contract_path = self.control_dir / artifact_name
                    with open(contract_path, 'w') as f:
                        json.dump(contract_data, f, indent=2)
    
    def _append_ledger_event(self, event: Dict[str, Any]) -> None:
        """
        Append event to ledger.
        
        Args:
            event: Event to append
        """
        # Read the raw data to preserve structure
        data = []
        if self.ledger_path.exists():
            with open(self.ledger_path, 'r') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        
        if isinstance(data, list):
            data.append(event)
        elif isinstance(data, dict):
            # Prefer 'events' for new Combine V2 events
            if 'events' not in data:
                data['events'] = []
            data['events'].append(event)
        else:
            # Fallback
            data = [event]
        
        self.control_dir.mkdir(parents=True, exist_ok=True)
        with open(self.ledger_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def run_stage(self, stage: str, dry_run: bool = True, brief_file: Optional[str] = None, route_family: Optional[str] = None) -> CombineStageResult:
        """
        Run a stage using the role agent protocol (stub/dry only).
        
        This method dispatches to the appropriate role agent for the stage.
        It does NOT call ComfyUI, does NOT perform generation, does NOT run QA/downstream.
        All stage execution in this layer is stub/dry only.
        
        Args:
            stage: Stage to run (e.g., "brief_intake_required", "route_classification_required")
            dry_run: If True, perform dry run only (always enforced in this layer)
            brief_file: Optional path to the brief file
            route_family: Optional route family override
            
        Returns:
            CombineStageResult with execution result
        """
        current_state = self._infer_current_state()
        
        # Validate stage execution
        if not self._validate_stage_execution(stage, current_state):
            return CombineStageResult(
                stage=stage,
                success=False,
                message=f"Stage {stage} cannot be executed from current state {current_state}",
                no_generation_performed=True
            )
        
        # Build run context
        current_route_family = route_family or self._get_route_family()
        route_policy = self._get_route_policy(current_route_family)
        
        context = CombineRunContext(
            project_root=str(self.project_root),
            current_state=current_state,
            stage=stage,
            route_family=current_route_family,
            dry_run=True,  # Always True for this layer
            metadata={
                "route_family": current_route_family,
                "route_policy": route_policy,
                "project_root": str(self.project_root),
                "brief_file": brief_file
            }
        )
        
        # Dispatch to role agent
        agent_result = self._dispatch_to_agent(stage, context)
        
        # Build stage result
        success = agent_result["status"] in ["stubbed", "ok", "success"]
        result = CombineStageResult(
            stage=stage,
            success=success,
            message=f"Agent {agent_result['agent']} executed stage (stub)",
            artifacts=agent_result.get("artifacts", []),
            metadata={
                "agent": agent_result["agent"],
                "dry_run": agent_result["dry_run"],
                "generation_performed": agent_result["generation_performed"],
                "comfyui_execution": agent_result["comfyui_execution"],
                "downstream_executed": agent_result["downstream_executed"],
                "not_required_for_route": agent_result.get("not_required_for_route", False),
                "next_recommended_stage": agent_result.get("next_recommended_stage", ""),
                **agent_result.get("metadata", {})
            },
            no_generation_performed=True  # Always True for this layer
        )
        
        # Write stage result
        self._write_stage_result(result)
        
        # Append ledger event
        self._append_ledger_event({
            "event_type": "stage_execution",
            "stage": stage,
            "agent": agent_result["agent"],
            "success": result.success,
            "message": result.message,
            "dry_run": dry_run,
            "generation_performed": agent_result["generation_performed"],
            "comfyui_execution": agent_result["comfyui_execution"],
            "timestamp": result.timestamp
        })
        
        return result

    def run_until(self, target_stage: str, dry_run: bool = True, brief_file: Optional[str] = None, route_family: Optional[str] = None) -> List[CombineStageResult]:
        """
        Run stages sequentially until the target stage is reached.
        
        Args:
            target_stage: The stage to stop at (inclusive)
            dry_run: Whether to perform dry runs
            brief_file: Path to the brief file
            route_family: Optional route family override
            
        Returns:
            List of CombineStageResult for each executed stage
        """
        results = []
        
        # Guard against invalid target stage
        if not self.state_machine.is_valid_state(target_stage):
            raise ValueError(f"Invalid target stage: {target_stage}")
            
        max_iterations = 20  # Safety break
        iterations = 0
        
        while iterations < max_iterations:
            status = self.get_status()
            current_state = status.current_state
            next_action = status.next_allowed_action
            
            # If we reached the target stage (it's the current state or the next action)
            # Actually, the user wants to run until the target stage is REVEALED as the next action,
            # or until it has been EXECUTED.
            # "until production_plan_review" usually means "run everything before it, 
            # and leave production_plan_review as the next_allowed_action".
            
            if current_state == target_stage:
                break
                
            if next_action == "none":
                break
                
            # If next_action is target_stage, and we want to stop BEFORE it:
            if next_action == target_stage:
                # We stop here so that target_stage is the next_allowed_action
                break
            
            # Execute next stage
            result = self.run_stage(next_action, dry_run=dry_run, brief_file=brief_file, route_family=route_family)
            results.append(result)
            
            if not result.success:
                break
                
            iterations += 1
            
        return results
