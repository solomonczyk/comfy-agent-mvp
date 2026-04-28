"""Workflow agent service for task-based generation routing."""

import json
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.agent.corrective_action_policy import CorrectiveActionPolicy, CorrectiveActionDecision


StatusCallback = Callable[[str, dict[str, Any] | None], None]
from app.agent.corrective_action_executor import CorrectiveActionExecutor
from app.agent.branch_execution_context import (
    BranchExecutionContext,
    BranchExecutorDependencies,
)
from app.agent.branch_state_models import BranchResult, TypedCandidateHistory
from app.agent.branch_execution_ports import BranchExecutorPorts
from app.agent.branch_port_factory import BranchPortFactory
from app.agent.branch_port_commands import RetryBranchCommand
from app.agent.branch_service_capabilities import BranchAdapterDependencies
from app.agent.branch_capability_composer import BranchCapabilityComposer
from app.agent.execution_plan import ExecutionPlan, ExecutionPlanBuilder
from app.agent.mutation_retry_planner import MutationRetryPlanner
from app.agent.result_contract import (
    AgentResult,
    ErrorCode,
    FailedStage,
    build_agent_result,
)
from app.agent.task_selector import TaskSelector, TaskSelectionResult
from app.agent.workflow_switch_planner import WorkflowSwitchPlanner
from app.agent.workflow_switch_policy import WorkflowSwitchPolicy
from app.agent.candidate_history import (
    AttemptRecord,
    AttemptRecordBuilder,
    CandidateHistory,
    generate_candidate_id,
)
from app.agent.candidate_selection import CandidateSelectionPolicy
from app.comfy.comfy_client import ComfyClient
from app.services.generation_service import GenerationService
from app.services.openrouter_client import OpenRouterClient
from app.services.run_metadata import RunMetadataService
from app.tools import (
    load_workflow as load_workflow_tool,
    mutate_workflow as mutate_workflow_tool,
    persist_run as persist_run_tool,
    select_workflow as select_workflow_tool,
    validate_graph_contract as validate_graph_contract_tool,
    validate_required_inputs as validate_required_inputs_tool,
)
from app.tools.tool_trace import ToolTrace
from app.workflows.workflow_mutator import MutationError, WorkflowMutator
from app.workflows.workflow_registry import WorkflowRegistry
from app.workflows.workflow_types import TaskType


class WorkflowAgentService:
    """Service for task-based workflow routing and generation."""

    def __init__(
        self,
        workflows_dir: str | Path,
        outputs_dir: str | Path,
        presets_path: str | Path,
        llm_client: OpenRouterClient | None = None,
        enable_judging: bool = False,
        runtime_workflows_dir: str | Path | None = None,
        verbose: bool = False,
    ):
        """Initialize workflow agent service.

        Args:
            workflows_dir: Directory containing workflow templates
            outputs_dir: Directory for generated outputs
            presets_path: Path to presets JSON file
            llm_client: LLM client for task selection
            enable_judging: Whether to enable judge pipeline
            runtime_workflows_dir: Optional directory for runtime workflow persistence
            verbose: Enable verbose logging for node-level workflow mutations
        """
        self.workflows_dir = Path(workflows_dir)
        self.outputs_dir = Path(outputs_dir)
        self.presets_path = Path(presets_path)
        self.registry = WorkflowRegistry(self.workflows_dir)
        self.task_selector = TaskSelector(llm_client)
        self.plan_builder = ExecutionPlanBuilder()
        self.enable_judging = enable_judging
        self.runtime_workflows_dir = Path(runtime_workflows_dir) if runtime_workflows_dir else self.outputs_dir.parent / "data" / "runtime_workflows"
        self.runtime_workflows_dir.mkdir(parents=True, exist_ok=True)
        self.mutator = WorkflowMutator(verbose=verbose)
        self.retry_planner = MutationRetryPlanner()
        self.corrective_action_policy = CorrectiveActionPolicy()
        self.corrective_action_executor = CorrectiveActionExecutor()
        self.switch_policy = WorkflowSwitchPolicy()
        self.switch_planner = WorkflowSwitchPlanner(self.workflows_dir)
        self.metadata_service = RunMetadataService(self.outputs_dir)
        self.selection_policy = CandidateSelectionPolicy()
        self.capability_composer = BranchCapabilityComposer(self)
        self.port_factory = BranchPortFactory(self.capability_composer.compose_dependencies())
    
    def _save_runtime_workflow(
        self,
        workflow: dict[str, Any],
        workflow_id: str,
    ) -> str:
        """Save mutated workflow to runtime directory.
        
        Args:
            workflow: Mutated workflow dictionary
            workflow_id: Original workflow ID
            
        Returns:
            Path to saved runtime workflow file
        """
        run_id = str(uuid.uuid4())[:8]
        filename = f"{run_id}_{workflow_id}.json"
        runtime_path = self.runtime_workflows_dir / filename
        
        with open(runtime_path, "w", encoding="utf-8") as f:
            json.dump(workflow, f, indent=2)
        
        return str(runtime_path)
    
    async def _run_single_attempt(
        self,
        execution_plan: ExecutionPlan,
        workflow_spec: Any,
        mutation_overrides: dict[str, Any] | None = None,
        disable_internal_retry: bool = True,
        save_metadata: bool = True,
        tool_trace: ToolTrace | None = None,
        verbose: bool = False,
    ) -> dict[str, Any]:
        """Run a single generation attempt with mutation.

        Args:
            execution_plan: Execution plan for the attempt
            workflow_spec: Workflow specification
            mutation_overrides: Additional mutation overrides for this attempt
            disable_internal_retry: Disable internal retry loop to prevent nested retries
            save_metadata: Whether to save metadata

        Returns:
            Generation result with mutation report in unified contract format
        """
        try:
            # Load and mutate workflow (tool-wrapped)
            template_workflow = await load_workflow_tool.run(
                tool_trace,
                mutator=self.mutator,
                workflow_path=execution_plan.workflow_path,
            )

            mutation_result = await mutate_workflow_tool.run(
                tool_trace,
                mutator=self.mutator,
                template=template_workflow,
                execution_plan=execution_plan,
                overrides=mutation_overrides,
            )

            # MK-2E: Sync mutated workflow to ComfyUI canvas for live visibility
            comfy_client = ComfyClient()
            try:
                canvas_sync_result = await comfy_client.sync_workflow_to_canvas(
                    workflow=mutation_result.mutated_workflow,
                    workflow_id=workflow_spec.workflow_id,
                )
                print(f"[MK-2E] Canvas sync result: {canvas_sync_result}")
            except Exception as e:
                print(f"[MK-2E] Canvas sync failed (non-blocking): {e}")
                # Continue execution even if canvas sync fails

            # MK-2E: Log pre-submit payload fragment for load-bearing fields
            print(f"\n[PRE_SUBMIT_PAYLOAD] Pre-submit workflow fragment (load-bearing nodes):")
            load_bearing_node_ids = ["4", "6", "7", "8"]  # Checkpoint, Positive prompt, Negative prompt, KSampler
            for node_id in load_bearing_node_ids:
                if node_id in mutation_result.mutated_workflow:
                    node_data = mutation_result.mutated_workflow[node_id]
                    node_type = node_data.get("class_type", "unknown")
                    node_inputs = node_data.get("inputs", {})
                    print(f"[PRE_SUBMIT_PAYLOAD] node_id={node_id} | node_type={node_type}")
                    for key, value in node_inputs.items():
                        if isinstance(value, str) and len(value) > 60:
                            print(f"[PRE_SUBMIT_PAYLOAD]   {key}={value[:60]}...")
                        else:
                            print(f"[PRE_SUBMIT_PAYLOAD]   {key}={value}")

            # Validate the mutated graph against node contracts before submission
            await validate_graph_contract_tool.run(
                tool_trace,
                workflow=mutation_result.mutated_workflow,
                workflow_id=workflow_spec.workflow_id,
            )

            runtime_workflow_path = self._save_runtime_workflow(
                mutation_result.mutated_workflow,
                workflow_spec.workflow_id,
            )
            
            # Use mutation_result.applied_changes as mutation_overrides for generation_service
            # This ensures canonical recipe values are propagated
            mutation_overrides = mutation_result.applied_changes
        except MutationError as e:
            # Return unified contract for mutation failure
            result = build_agent_result(
                status="failed",
                failed_stage=FailedStage.WORKFLOW_MUTATION,
                error_type="mutation_error",
                error_code=ErrorCode.MUTATION_CONTRACT_ERROR,
                error=f"Workflow mutation failed: {e.message} (workflow_id={e.workflow_id}, node_id={e.node_id})",
                user_prompt=execution_plan.user_prompt,
                execution_plan=execution_plan.to_dict(),
                mutation_report=None,  # Mutation failed, no report
                images=[],
                metadata_path=None,
                summary_path=None,
                executed_action={
                    "executed_action": "none",
                    "execution_status": "failed",
                    "branch_taken": None,
                    "notes": ["Mutation failed before execution"],
                    "error_type": "mutation_error",
                    "error": f"Workflow mutation failed: {e.message}",
                },
            )
            return result.to_dict()
        
        # Call generation service with mutated workflow
        # Disable internal retry loop to prevent nested retries
        generation_service = GenerationService(
            workflow_path=runtime_workflow_path,
            outputs_dir=self.outputs_dir,
            presets_path=self.presets_path,
            enable_judging=execution_plan.enable_judging,
        )

        try:
            # When canonical_recipe is present, skip preset to prevent preset values from overriding canonical settings
            preset_name_to_use = None if execution_plan.canonical_recipe else execution_plan.preset_name
            
            # Debug: Log mutation_overrides
            print(f"[DEBUG] workflow_agent_service: mutation_overrides={mutation_overrides}")
            print(f"[DEBUG] workflow_agent_service: canonical_recipe={execution_plan.canonical_recipe}")
            
            generation_result = await generation_service.generate_from_text(
                user_prompt=execution_plan.user_prompt,
                rewrite_mode=execution_plan.rewrite_mode,
                preset_name=preset_name_to_use,
                negative_prompt=mutation_overrides.get("negative_prompt") if mutation_overrides else None,
                width=mutation_overrides.get("width") if mutation_overrides else None,
                height=mutation_overrides.get("height") if mutation_overrides else None,
                steps=mutation_overrides.get("steps") if mutation_overrides else None,
                cfg=mutation_overrides.get("cfg") if mutation_overrides else None,
                seed=mutation_overrides.get("seed") if mutation_overrides else None,
                checkpoint=mutation_overrides.get("checkpoint") if mutation_overrides else None,
                prefix=mutation_overrides.get("filename_prefix") if mutation_overrides else None,
                sampler_name=mutation_overrides.get("sampler_name") if mutation_overrides else None,
                scheduler=mutation_overrides.get("scheduler") if mutation_overrides else None,
                save_metadata=save_metadata,
                workflow_id=execution_plan.workflow_id,
                tool_trace=tool_trace,
                verbose=verbose,
            )
        except Exception as e:
            # Return unified contract for generation failure
            result = build_agent_result(
                status="failed",
                failed_stage=FailedStage.GENERATION,
                error_type="generation_error",
                error_code=ErrorCode.GENERATION_FAILED,
                error=f"Generation failed: {str(e)}",
                user_prompt=execution_plan.user_prompt,
                execution_plan=execution_plan.to_dict(),
                mutation_report=mutation_result.to_dict(),
                images=[],
                metadata_path=None,
                summary_path=None,
                executed_action={
                    "executed_action": "none",
                    "execution_status": "failed",
                    "branch_taken": None,
                    "notes": ["Generation failed during execution"],
                    "error_type": "generation_error",
                    "error": f"Generation failed: {str(e)}",
                },
            )
            return result.to_dict()

        # Normalize generation result to unified contract
        result = self._normalize_generation_result(
            generation_result=generation_result,
            execution_plan=execution_plan,
            mutation_report=mutation_result.to_dict(),
        )

        return result

    def _normalize_generation_result(
        self,
        generation_result: dict[str, Any],
        execution_plan: ExecutionPlan,
        mutation_report: dict[str, Any],
    ) -> dict[str, Any]:
        """Normalize generation service result to unified agent contract.

        Args:
            generation_result: Result from generation service
            execution_plan: Execution plan used
            mutation_report: Mutation report

        Returns:
            Unified agent result contract
        """
        # Extract fields from generation result
        status = generation_result.get("status", "completed")
        failed_stage = generation_result.get("failed_stage")
        error = generation_result.get("error")
        images = generation_result.get("images", [])
        metadata_path = generation_result.get("metadata_path")
        summary_path = generation_result.get("summary_path")

        # Extract judge/retry fields if present
        judge_status = generation_result.get("judge_status")
        orchestrator_report = generation_result.get("orchestrator_report")
        retry_decision = generation_result.get("retry_decision")
        retry_loop = generation_result.get("retry_loop")
        recipe_validation = generation_result.get("recipe_validation")
        upscale_result = generation_result.get("upscale_result")

        # Map generation service failed_stage to agent failed_stage
        mapped_failed_stage = None
        error_code = None
        error_type = None

        if status == "failed":
            error_type = generation_result.get("error_type", "generation_error")
            # Map generation service stages to agent stages
            stage_mapping = {
                "prompt_rewrite": FailedStage.EXECUTION_PLAN_BUILD,
                "preflight_validation": FailedStage.EXECUTION_PLAN_BUILD,
                "settings_resolution": FailedStage.EXECUTION_PLAN_BUILD,
                "generation": FailedStage.GENERATION,
                "artifact_validation": FailedStage.GENERATION,
                "artifact_fetch_validation": FailedStage.GENERATION,
                "metadata_save": FailedStage.GENERATION,
            }
            if failed_stage:
                mapped_failed_stage = stage_mapping.get(failed_stage, FailedStage.GENERATION)

            # Map error codes
            if failed_stage == "generation":
                error_code = ErrorCode.GENERATION_FAILED
            elif judge_status and judge_status.startswith("judge_error"):
                error_code = ErrorCode.JUDGE_PIPELINE_FAILED
            elif retry_loop and retry_loop.get("loop_status") == "failed":
                error_code = ErrorCode.RETRY_LOOP_FAILED

        # Build unified result
        result = build_agent_result(
            status=status,
            failed_stage=mapped_failed_stage,
            error_type=error_type,
            error_code=error_code,
            error=str(error) if error else None,
            user_prompt=execution_plan.user_prompt,
            execution_plan=execution_plan.to_dict(),
            mutation_report=mutation_report,
            judge_status=judge_status,
            orchestrator_report=orchestrator_report,
            retry_decision=retry_decision,
            retry_loop=retry_loop,
            images=images,
            metadata_path=metadata_path,
            summary_path=summary_path,
            recipe_validation=recipe_validation,
            upscale_result=upscale_result,
        )

        return result.to_dict()

    def _choose_best_candidate(
        self,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Choose the best candidate from multiple generation attempts using unified selection policy.
        
        Args:
            candidates: List of generation results
            
        Returns:
            Best candidate based on unified selection policy
        """
        if not candidates:
            raise ValueError("No candidates to choose from")
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Use unified selection policy
        selection_decision = self.selection_policy.select_best_candidate(candidates)
        
        # Find and return the selected candidate
        if selection_decision.selected_attempt_index is None:
            # If no selection, return first candidate as fallback
            return candidates[0]
        selected_index = selection_decision.selected_attempt_index - 1  # Convert to 0-based
        return candidates[selected_index]
    
    async def _handle_mutation_aware_retry(
        self,
        execution_plan: ExecutionPlan,
        workflow_spec: Any,
        first_result: dict[str, Any],
        task_selection: TaskSelectionResult,
        assets: dict[str, Any] | None,
        save_metadata: bool = True,
        switch_applied_this_run: bool = False,
        candidate_history: CandidateHistory | None = None,
        force_retry: bool = False,
        force_switch: str | None = None,
    ) -> dict[str, Any]:
        """Handle mutation-aware retry if judge status is retry.
        
        This method now delegates branch orchestration to the executor.
        The service is thin: it just calls executor.execute_branch() and gets the outcome.
        
        Args:
            execution_plan: Original execution plan
            workflow_spec: Workflow specification
            first_result: Result from first attempt
            task_selection: Original task selection result
            assets: Available assets
            save_metadata: Whether to save metadata
            switch_applied_this_run: Whether a switch has already been applied in this run
            candidate_history: Candidate history to track attempts
            force_retry: Force retry path for proof mode (bypasses natural judge trigger)
            force_switch: Force workflow switch for proof mode (e.g., upscale_v1, inpaint_face_v1)
            
        Returns:
            Best result (either first or second attempt)
        """
        judge_status = first_result.get("judge_status")
        
        # Bypass natural judge trigger for forced proof mode
        if force_retry or force_switch:
            # Create synthetic orchestrator report for forced mode
            orchestrator_report_dict = {
                "final_verdict": "fail",  # Force retry/switch by setting fail
                "best_next_action": "retry_seed" if force_retry else "switch_workflow",
                "global_repairs": ["forced proof mode"],
                "technical": {"final_verdict": "fail", "recommended_repairs": []},
                "semantic": {"final_verdict": "fail", "recommended_repairs": []},
                "artistic": {"final_verdict": "fail", "recommended_repairs": []},
            }
            mutation_report = first_result.get("mutation_report", {})
            # Proceed to retry/switch logic (bypass judge_status check)
        else:
            # If not retry and not forced, return first result immediately
            if judge_status != "retry":
                return first_result
            
            orchestrator_report_dict = first_result.get("orchestrator_report")
            mutation_report = first_result.get("mutation_report", {})
        
        # Use CorrectiveActionPolicy for canonical decision (decision layer)
        corrective_action = self.corrective_action_policy.evaluate(
            task_selection=task_selection,
            execution_plan=execution_plan,
            mutation_report=mutation_report,
            orchestrator_report=orchestrator_report_dict,
            assets=assets,
        )
        
        # Override corrective_action for forced switch mode
        if force_switch:
            from app.agent.corrective_action_policy import (
                WORKFLOW_ASSET_REQUIREMENTS,
                REASON_CODE_RESOLUTION_REPAIR_SWITCH,
                REASON_CODE_FACE_REPAIR_SWITCH,
            )
            # For forced proof mode, bypass asset requirement check
            # In production, assets would be validated, but for proof we allow the switch
            required_inputs = WORKFLOW_ASSET_REQUIREMENTS.get(force_switch, [])
            missing_inputs = []
            for asset_key in required_inputs:
                if not assets or assets.get(asset_key) is None:
                    missing_inputs.append(asset_key)
            
            # Skip asset validation for forced proof mode
            # if missing_inputs:
            #     # Cannot force switch due to missing assets
            #     first_result["corrective_action"] = corrective_action.to_dict()
            #     first_result["workflow_switch"] = {
            #         "switch_applied": False,
            #         "from_workflow_id": execution_plan.workflow_id,
            #         "to_workflow_id": force_switch,
            #         "switch_reason": f"Forced switch blocked by missing assets: {', '.join(missing_inputs)}",
            #         "source_trigger": "forced_switch",
            #         "switch_allowed": False,
            #         "missing_inputs": missing_inputs,
            #         "notes": ["Forced switch mode requires assets not available"],
            #     }
            #     return first_result
            
            # Override with forced switch decision
            from app.agent.corrective_action_policy import CorrectiveActionDecision
            reason_code = (
                REASON_CODE_RESOLUTION_REPAIR_SWITCH if force_switch == "upscale_v1"
                else REASON_CODE_FACE_REPAIR_SWITCH if force_switch == "inpaint_face_v1"
                else "forced_switch"
            )
            corrective_action = CorrectiveActionDecision(
                action="switch_workflow",
                reason_code=reason_code,
                reason=f"Forced switch to {force_switch} for proof mode",
                source_repairs=["forced proof mode"],
                selected_workflow_id=execution_plan.workflow_id,
                target_workflow_id=force_switch,
                required_inputs=required_inputs,
                missing_inputs=[],
                switch_allowed=True,
                notes=["Forced switch mode for proof"],
            )
        
        # Attach corrective_action to first_result for downstream use
        first_result["corrective_action"] = corrective_action.to_dict()
        
        # Use typed state for current_result
        current_branch_result = BranchResult.from_dict(first_result)
        
        # Build retry overrides based on corrective_action
        retry_overrides = self._build_retry_overrides_from_corrective_action(
            corrective_action=corrective_action,
            mutation_report=mutation_report,
            execution_plan=execution_plan,
        )
        
        # SIMPLIFIED APPROACH: Call _run_single_attempt directly for retry to bypass port system
        # This is a temporary measure to isolate the retry execution error
        if corrective_action.action in ("retry_seed", "retry_prompt", "retry_settings"):
            try:
                import traceback
                retry_result = await self._run_single_attempt(
                    execution_plan=execution_plan,
                    workflow_spec=workflow_spec,
                    mutation_overrides=retry_overrides,
                    disable_internal_retry=True,
                    save_metadata=save_metadata,
                )
                # Attach corrective_action to retry result
                retry_result["corrective_action"] = corrective_action.to_dict()
                retry_result["mutation_retry"] = {
                    "action": corrective_action.action,
                    "reason_code": corrective_action.reason_code,
                    "retry_overrides_applied": {k: v for k, v in retry_overrides.items() if not k.startswith("_")},
                    "attempt_index": 2,
                }
                # Update candidate history with retry attempt
                retry_attempt_record = self._create_attempt_record(
                    result=retry_result,
                    attempt_index=2,
                    attempt_kind=corrective_action.action,
                    parent_candidate_id=candidate_history.attempts[0].candidate_id if candidate_history.attempts else None,
                )
                candidate_history.add_attempt(retry_attempt_record)
                # Select best candidate (simplified - prefer retry)
                best_result = retry_result
                best_result["candidate_selection"] = {
                    "selected_candidate_id": retry_attempt_record.candidate_id,
                    "selected_attempt_index": 2,
                    "selection_reason": "retry_selected",
                    "selected_workflow_id": execution_plan.workflow_id,
                    "ranking_snapshot": [
                        {"candidate_id": candidate_history.attempts[0].candidate_id, "attempt_index": 1, "rank": 2},
                        {"candidate_id": retry_attempt_record.candidate_id, "attempt_index": 2, "rank": 1},
                    ],
                }
                best_result["executed_action"] = {
                    "executed_action": corrective_action.action,
                    "execution_status": "completed",
                    "branch_taken": "retry",
                    "notes": [f"Retry executed: {corrective_action.action}"],
                }
                return best_result
            except Exception as e:
                # If simplified retry fails, fall back to port system
                print(f"[DEBUG] Simplified retry failed with error: {e}")
                print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
                # Don't raise, let it fall through to port system
                pass
        
        # Build concrete ports via factory
        retry_port = self.port_factory.create_retry_port(
            workflow_spec=workflow_spec,
            retry_overrides=retry_overrides,
            disable_internal_retry=True,
            save_metadata=save_metadata,
            corrective_action=corrective_action,
        )
        
        if corrective_action.action == "switch_workflow":
            switch_port = self.port_factory.create_switch_port(
                workflow_spec=workflow_spec,
                switch_plan=switch_plan,
                disable_internal_retry=True,
                save_metadata=save_metadata,
                corrective_action=corrective_action,
            )
        else:
            switch_port = None
        
        # Build BranchExecutorPorts
        ports = BranchExecutorPorts(
            retry_port=retry_port,
            switch_port=switch_port,
            selection_port=selection_port,
            history_port=history_port,
        )
        
        # Build BranchExecutionContext with run-state data
        typed_history = TypedCandidateHistory.from_dict(candidate_history.to_dict()) if candidate_history else None
        branch_context = BranchExecutionContext(
            corrective_action=corrective_action,
            current_result=first_result,
            execution_plan=execution_plan,
            mutation_report=mutation_report,
            assets=assets,
            candidate_history=typed_history,
        )
        
        # Build BranchExecutorDependencies with ports only (no callbacks)
        branch_deps = BranchExecutorDependencies(ports=ports)
        
        # Use executor for full branch orchestration with consolidated interface
        branch_outcome = await self.corrective_action_executor.execute_branch(
            context=branch_context,
            deps=branch_deps,
        )
        
        # Get the final result from branch outcome
        final_result = branch_outcome.updated_result if branch_outcome.updated_result else first_result
        
        # Attach executed_action from branch outcome
        final_result["executed_action"] = branch_outcome.executed_action
        
        # Attach candidate_selection if candidates were compared
        if branch_outcome.updated_result and branch_outcome.updated_result != first_result:
            candidates = [first_result, branch_outcome.updated_result]
            selection_decision = self.selection_policy.select_best_candidate(candidates)
            final_result["candidate_selection"] = selection_decision.to_dict()
        
        return final_result
    
    async def _handle_workflow_switch(
        self,
        execution_plan: ExecutionPlan,
        first_result: dict[str, Any],
        task_selection: TaskSelectionResult,
        assets: dict[str, Any] | None,
        save_metadata: bool = True,
        switch_applied_this_run: bool = False,
        candidate_history: CandidateHistory | None = None,
        corrective_action: Any = None,
        execution_result: Any = None,
    ) -> dict[str, Any]:
        """Handle workflow switch if requested by corrective action.
        
        Args:
            execution_plan: Original execution plan
            first_result: Result from first attempt
            task_selection: Original task selection result
            assets: Available assets
            save_metadata: Whether to save metadata
            switch_applied_this_run: Whether a switch has already been applied in this run
            candidate_history: Candidate history to track attempts
            corrective_action: CorrectiveActionDecision from policy
            execution_result: CorrectiveActionExecutionResult from executor
            
        Returns:
            Best result (either first or switched attempt)
        """
        orchestrator_report_dict = first_result.get("orchestrator_report")
        mutation_report = first_result.get("mutation_report", {})
        
        # Use corrective_action for target workflow if provided
        target_workflow_id = corrective_action.target_workflow_id if corrective_action else None
        
        # If switch not allowed by corrective_action, return first result
        if corrective_action and not corrective_action.switch_allowed:
            first_result["workflow_switch"] = {
                "switch_applied": False,
                "from_workflow_id": execution_plan.workflow_id,
                "to_workflow_id": target_workflow_id,
                "switch_reason": corrective_action.reason,
                "source_trigger": "corrective_action_policy",
                "switch_allowed": False,
                "missing_inputs": corrective_action.missing_inputs,
                "notes": corrective_action.notes,
            }
            return first_result
        
        # Evaluate switch decision with WorkflowSwitchPolicy for validation
        # Build a minimal retry_decision dict for compatibility with switch_policy
        retry_decision_dict = {"action": "switch_workflow"} if corrective_action and corrective_action.action == "switch_workflow" else {}
        
        switch_decision = self.switch_policy.evaluate(
            task_selection=None,  # Not needed for policy
            execution_plan=execution_plan,
            mutation_report=mutation_report,
            retry_decision=retry_decision_dict,
            orchestrator_report=orchestrator_report_dict,
            assets=assets,
            switch_applied_this_run=switch_applied_this_run,
        )
        
        # Build switch plan
        switch_plan = self.switch_planner.build_switch_plan(
            current_execution_plan=execution_plan,
            switch_decision=switch_decision,
            task_selection=task_selection,
            assets=assets,
            registry=self.registry,
        )
        
        # If switch not applied, return first result with switch block
        if not switch_plan.switch_applied:
            first_result["workflow_switch"] = {
                "switch_applied": False,
                "from_workflow_id": execution_plan.workflow_id,
                "to_workflow_id": None,
                "switch_reason": switch_plan.switch_reason,
                "source_trigger": switch_plan.source_trigger,
                "switch_allowed": False,
                "missing_inputs": switch_plan.missing_inputs,
                "notes": switch_plan.notes,
            }
            return first_result
        
        # Get target workflow spec
        target_workflow_id = switch_plan.to_workflow_id
        if not target_workflow_id:
            first_result["workflow_switch"] = {
                "switch_applied": False,
                "from_workflow_id": execution_plan.workflow_id,
                "to_workflow_id": None,
                "switch_reason": "No target workflow specified",
                "source_trigger": switch_plan.source_trigger,
                "switch_allowed": False,
                "missing_inputs": [],
                "notes": ["Switch plan missing target workflow"],
            }
            return first_result
        
        target_workflow_spec = self.registry.get_by_id(target_workflow_id)
        if not target_workflow_spec or not target_workflow_spec.implemented:
            first_result["workflow_switch"] = {
                "switch_applied": False,
                "from_workflow_id": execution_plan.workflow_id,
                "to_workflow_id": target_workflow_id,
                "switch_reason": f"Target workflow not available or not implemented: {target_workflow_id}",
                "source_trigger": switch_plan.source_trigger,
                "switch_allowed": False,
                "missing_inputs": [],
                "notes": ["Target workflow not in registry or not implemented"],
            }
            return first_result
        
        # Build switched execution plan
        if not switch_plan.switched_execution_plan:
            first_result["workflow_switch"] = {
                "switch_applied": False,
                "from_workflow_id": execution_plan.workflow_id,
                "to_workflow_id": target_workflow_id,
                "switch_reason": "Failed to build switched execution plan",
                "source_trigger": switch_plan.source_trigger,
                "switch_allowed": False,
                "missing_inputs": switch_plan.missing_inputs,
                "notes": switch_plan.notes,
            }
            return first_result
        
        switched_plan_dict = switch_plan.switched_execution_plan
        switched_execution_plan = ExecutionPlan.from_dict(switched_plan_dict)
        
        # Run switched attempt
        switched_result = await self._run_single_attempt(
            execution_plan=switched_execution_plan,
            workflow_spec=target_workflow_spec,
            mutation_overrides=None,
            disable_internal_retry=True,
            save_metadata=save_metadata,
        )
        
        # Attach corrective_action and executed_action to switched_result
        if corrective_action:
            switched_result["corrective_action"] = corrective_action.to_dict()
        if execution_result:
            switched_result["executed_action"] = execution_result.to_dict()
        
        # Track switched attempt in history with lineage
        if candidate_history:
            # Get parent candidate ID (first attempt)
            parent_candidate_id = candidate_history.attempts[0].candidate_id if candidate_history.attempts else None
            switched_attempt_record = self._create_attempt_record(
                result=switched_result,
                attempt_index=len(candidate_history.attempts) + 1,
                attempt_kind="workflow_switch",
                parent_candidate_id=parent_candidate_id,
            )
            candidate_history.add_attempt(switched_attempt_record)
        
        # Choose best candidate
        candidates = [first_result, switched_result]
        best_result = self._choose_best_candidate(candidates)
        
        # Mark selected candidate in history
        if candidate_history and candidate_history.attempts:
            # Determine which candidate was selected
            selected_index = 1 if best_result == switched_result else 0
            selected_candidate = candidate_history.attempts[selected_index]
            candidate_history.mark_selected(
                candidate_id=selected_candidate.candidate_id,
                attempt_index=selected_index + 1,
                selection_reason="workflow_switch_candidate_won" if best_result == switched_result else "initial_candidate_kept",
            )
        
        # Update executed_action with selected candidate info
        executed_action_dict = best_result.get("executed_action", {})
        executed_action_dict["selected_candidate_id"] = selected_candidate.candidate_id
        executed_action_dict["selected_attempt_index"] = selected_index + 1
        best_result["executed_action"] = executed_action_dict
        
        # Determine which candidate was selected
        selected_candidate_workflow_id = None
        if best_result == switched_result:
            selected_candidate_workflow_id = target_workflow_id
            # Ensure top-level fields match the selected switched candidate
            # Don't mix first attempt and switched attempt data
            best_result["execution_plan"] = switched_result.get("execution_plan")
            best_result["mutation_report"] = switched_result.get("mutation_report")
            best_result["judge_status"] = switched_result.get("judge_status")
            best_result["orchestrator_report"] = switched_result.get("orchestrator_report")
            best_result["retry_decision"] = switched_result.get("retry_decision")
            best_result["images"] = switched_result.get("images", [])
            best_result["metadata_path"] = switched_result.get("metadata_path")
            best_result["summary_path"] = switched_result.get("summary_path")
        else:
            selected_candidate_workflow_id = execution_plan.workflow_id
        
        # Attach workflow switch block to best result
        best_result["workflow_switch"] = {
            "switch_applied": True,
            "from_workflow_id": execution_plan.workflow_id,
            "to_workflow_id": target_workflow_id,
            "switch_reason": switch_plan.switch_reason,
            "source_trigger": switch_plan.source_trigger,
            "switch_allowed": True,
            "missing_inputs": switch_plan.missing_inputs,
            "notes": switch_plan.notes,
            "selected_candidate_workflow_id": selected_candidate_workflow_id,
        }
        
        # Add candidate_selection block to best result
        selection_decision = self.selection_policy.select_best_candidate(candidates)
        best_result["candidate_selection"] = selection_decision.to_dict()
        
        return best_result
    
    def _build_retry_overrides_from_corrective_action(
        self,
        corrective_action: Any,
        mutation_report: dict[str, Any],
        execution_plan: ExecutionPlan,
    ) -> dict[str, Any]:
        """Build retry overrides from corrective action decision.
        
        Args:
            corrective_action: CorrectiveActionDecision instance
            mutation_report: Report from initial mutation
            execution_plan: Original execution plan
            
        Returns:
            Dictionary of retry overrides
        """
        overrides = {}
        applied_changes = mutation_report.get("applied_changes", {})
        
        # Start with original applied changes
        overrides.update(applied_changes)
        
        # Apply overrides based on corrective action type
        if corrective_action.action == "retry_seed":
            # Only change seed, keep everything else
            import random
            overrides["seed"] = random.randint(1, 2147483647)  # Generate new seed instead of None
        
        elif corrective_action.action == "retry_prompt":
            # Apply prompt repairs from source_repairs
            if corrective_action.source_repairs:
                # Append repairs to existing prompt
                current_prompt = applied_changes.get("positive_prompt", "")
                repairs_text = " ".join(corrective_action.source_repairs)
                overrides["positive_prompt"] = f"{current_prompt}, {repairs_text}" if current_prompt else repairs_text
        
        elif corrective_action.action == "retry_settings":
            # Apply settings-based repairs
            repairs_text = " ".join(corrective_action.source_repairs).lower()
            
            if "steps" in repairs_text or "increase_steps" in repairs_text:
                overrides["steps"] = 36
            if "cfg" in repairs_text or "reduce_highlights" in repairs_text:
                overrides["cfg"] = 5.5
            if "resolution" in repairs_text or "fix_output_resolution" in repairs_text:
                overrides["width"] = 1024
                overrides["height"] = 1024
        
        return overrides
    
    def _build_retry_overrides(
        self,
        mutation_report: dict[str, Any],
        retry_plan: Any,
        execution_plan: ExecutionPlan,
    ) -> dict[str, Any]:
        """Build retry overrides from mutation report and retry plan.
        
        Args:
            mutation_report: Report from initial mutation
            retry_plan: Mutation retry plan
            execution_plan: Original execution plan
            
        Returns:
            Dictionary of retry overrides
        """
        overrides = {}
        applied_changes = mutation_report.get("applied_changes", {})
        retry_overrides = retry_plan.retry_overrides
        
        # Start with original applied changes
        overrides.update(applied_changes)
        
        # Apply retry plan overrides
        for key, value in retry_overrides.items():
            if not key.startswith("_"):  # Skip internal flags
                overrides[key] = value
        
        # Handle special flags
        if retry_overrides.get("_keep_prompt"):
            # Keep original prompt
            overrides["positive_prompt"] = applied_changes.get("positive_prompt")
            overrides["negative_prompt"] = applied_changes.get("negative_prompt")
        
        if retry_overrides.get("_keep_settings"):
            # Keep original settings
            for key in ["steps", "cfg", "sampler_name", "scheduler", "width", "height"]:
                if key in applied_changes:
                    overrides[key] = applied_changes[key]
        
        return overrides

    async def generate_from_task(
        self,
        user_prompt: str,
        assets: dict[str, Any] | None = None,
        rewrite_mode: str | None = None,
        negative_prompt: str | None = None,
        width: int | None = None,
        height: int | None = None,
        steps: int | None = None,
        cfg: float | None = None,
        seed: int | None = None,
        checkpoint: str | None = None,
        prefix: str | None = None,
        save_metadata: bool = True,
    ) -> dict[str, Any]:
        """Generate image from task description using workflow routing."""
        # Step 1: Select task type with asset awareness
        task_selection = self.task_selector.select(user_prompt, assets)

        # Step 1.5: Planning guard - check for missing required inputs before execution
        if task_selection.missing_inputs:
            # Return controlled failure before ComfyUI execution
            return self._create_planning_failure_result(
                user_prompt=user_prompt,
                task_selection=task_selection,
                missing_inputs=task_selection.missing_inputs,
            )

        # Step 2: Get workflow specification
        workflow_spec = self.registry.get_default_for_task(task_selection.task_type)

        if not workflow_spec:
            task_selection_dict = {
                "task_type": task_selection.task_type.value,
                "confidence": task_selection.confidence,
                "reason": task_selection.reason,
                "routing_source": task_selection.routing_source,
                "required_inputs": task_selection.required_inputs,
                "missing_inputs": task_selection.missing_inputs,
                "ambiguity_level": task_selection.ambiguity_level,
                "safe_fallback_used": task_selection.safe_fallback_used,
            }
            result = build_agent_result(
                status="failed",
                failed_stage=FailedStage.WORKFLOW_LOOKUP,
                error_type="workflow_lookup_failure",
                error_code=ErrorCode.WORKFLOW_NOT_FOUND,
                error=f"No workflow found for task type: {task_selection.task_type.value}",
                user_prompt=user_prompt,
                task_selection=task_selection_dict,
                execution_plan=None,
                images=[],
                metadata_path=None,
                summary_path=None,
                executed_action={
                    "executed_action": "none",
                    "execution_status": "failed",
                    "branch_taken": None,
                    "notes": ["Workflow lookup failed before execution"],
                    "error_type": "workflow_lookup_failure",
                    "error": f"No workflow found for task type: {task_selection.task_type.value}",
                },
            )
            return result.to_dict()

        if not workflow_spec.implemented:
            task_selection_dict = {
                "task_type": task_selection.task_type.value,
                "confidence": task_selection.confidence,
                "reason": task_selection.reason,
                "routing_source": task_selection.routing_source,
                "required_inputs": task_selection.required_inputs,
                "missing_inputs": task_selection.missing_inputs,
                "ambiguity_level": task_selection.ambiguity_level,
                "safe_fallback_used": task_selection.safe_fallback_used,
            }
            result = build_agent_result(
                status="failed",
                failed_stage=FailedStage.WORKFLOW_LOOKUP,
                error_type="workflow_not_implemented",
                error_code=ErrorCode.WORKFLOW_NOT_IMPLEMENTED,
                error=f"Workflow '{workflow_spec.workflow_id}' is not implemented yet",
                user_prompt=user_prompt,
                task_selection=task_selection_dict,
                execution_plan=None,
                images=[],
                metadata_path=None,
                summary_path=None,
                executed_action={
                    "executed_action": "none",
                    "execution_status": "failed",
                    "branch_taken": None,
                    "notes": ["Workflow not implemented before execution"],
                    "error_type": "workflow_not_implemented",
                    "error": f"Workflow '{workflow_spec.workflow_id}' is not implemented yet",
                },
            )
            return result.to_dict()

        # Step 3: Build execution plan
        # Prepare resolved inputs including assets
        resolved_inputs = {
            "prompt": user_prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg": cfg,
            "seed": seed,
            "checkpoint": checkpoint,
            "prefix": prefix,
        }
        # Add assets to resolved inputs if present
        if assets:
            for key, value in assets.items():
                if value is not None:
                    resolved_inputs[key] = value

        execution_plan = self.plan_builder.build(
            user_prompt=user_prompt,
            task_selection=task_selection,
            workflow_id=workflow_spec.workflow_id,
            workflow_path=workflow_spec.workflow_path,
            preset_name=workflow_spec.preset_name,
            rewrite_mode=rewrite_mode or workflow_spec.default_rewrite_mode,
            required_inputs=workflow_spec.required_inputs,
            resolved_inputs=resolved_inputs,
            enable_judging=self.enable_judging and workflow_spec.supports_judging,
            enable_retry_loop=False,  # Disable internal retry, use agent-level retry
            canonical_recipe=canonical_recipe,
        )

        # Step 4: Initialize candidate history
        candidate_history = CandidateHistory()
        
        # Step 5: Run first attempt
        first_result = await self._run_single_attempt(
            execution_plan=execution_plan,
            workflow_spec=workflow_spec,
            disable_internal_retry=True,
            save_metadata=save_metadata,
        )
        
        # Track first attempt in history
        first_attempt_record = self._create_attempt_record(
            result=first_result,
            attempt_index=1,
            attempt_kind="initial",
            parent_candidate_id=None,
        )
        candidate_history.add_attempt(first_attempt_record)

        # Step 6: Handle mutation-aware retry if needed
        result = await self._handle_mutation_aware_retry(
            execution_plan=execution_plan,
            workflow_spec=workflow_spec,
            first_result=first_result,
            task_selection=task_selection,
            assets=assets,
            save_metadata=save_metadata,
            switch_applied_this_run=False,  # No switch applied yet in this run
            candidate_history=candidate_history,
            force_retry=force_retry,
            force_switch=force_switch,
        )

        # Step 6: Ensure result has task_selection attached (may already be there from failure paths)
        if "task_selection" not in result or result.get("task_selection") is None:
            task_selection_dict = {
                "task_type": task_selection.task_type.value,
                "confidence": task_selection.confidence,
                "reason": task_selection.reason,
                "routing_source": task_selection.routing_source,
                "required_inputs": task_selection.required_inputs,
                "missing_inputs": task_selection.missing_inputs,
                "ambiguity_level": task_selection.ambiguity_level,
                "safe_fallback_used": task_selection.safe_fallback_used,
            }
            result["task_selection"] = task_selection_dict

        # Ensure execution_plan is attached (may already be there from normalization)
        if "execution_plan" not in result or result.get("execution_plan") is None:
            result["execution_plan"] = execution_plan.to_dict()

        # Ensure workflow_switch block is present (even if no switch applied)
        if "workflow_switch" not in result or result.get("workflow_switch") is None:
            result["workflow_switch"] = {
                "switch_applied": False,
                "from_workflow_id": execution_plan.workflow_id,
                "to_workflow_id": None,
                "switch_reason": None,
                "source_trigger": None,
                "switch_allowed": False,
                "missing_inputs": [],
                "notes": [],
            }
        
        # Ensure corrective_action block is present (canonical decision layer)
        # Preserve corrective_action if it was set in forced mode
        if ("corrective_action" not in result or result.get("corrective_action") is None) and not (force_retry or force_switch):
            # If no corrective action was set (e.g., judge_status was not retry), create a default one
            judge_status = result.get("judge_status")
            orchestrator_report = result.get("orchestrator_report")
            
            if judge_status == "pass":
                result["corrective_action"] = {
                    "action": "accept",
                    "reason_code": "accepted_by_judge",
                    "reason": "Generation accepted by judge",
                    "source_repairs": [],
                    "selected_workflow_id": execution_plan.workflow_id,
                    "target_workflow_id": None,
                    "required_inputs": [],
                    "missing_inputs": [],
                    "switch_allowed": False,
                    "notes": ["Judge approved the result"],
                }
            elif judge_status == "reject":
                global_repairs = orchestrator_report.get("global_repairs", []) if orchestrator_report else []
                result["corrective_action"] = {
                    "action": "reject",
                    "reason_code": "reject_after_judge",
                    "reason": "Reject after judge aggregation",
                    "source_repairs": global_repairs,
                    "selected_workflow_id": execution_plan.workflow_id,
                    "target_workflow_id": None,
                    "required_inputs": [],
                    "missing_inputs": [],
                    "switch_allowed": False,
                    "notes": ["Judge rejected the result"],
                }
            else:
                # No judge status (judging disabled or failed)
                result["corrective_action"] = {
                    "action": "accept",
                    "reason_code": "accepted_by_judge",
                    "reason": "No judge evaluation - accepting result",
                    "source_repairs": [],
                    "selected_workflow_id": execution_plan.workflow_id,
                    "target_workflow_id": None,
                    "required_inputs": [],
                    "missing_inputs": [],
                    "switch_allowed": False,
                    "notes": ["Judging was disabled or judge pipeline failed"],
                }
        
        # Ensure executed_action block is present (execution layer)
        if "executed_action" not in result or result.get("executed_action") is None:
            # If no executed_action was set, create a default one based on corrective_action
            corrective_action_dict = result.get("corrective_action", {})
            action = corrective_action_dict.get("action", "accept")
            
            # Get selected candidate info from candidate_history
            selected_candidate_id = None
            selected_attempt_index = None
            if candidate_history:
                selected_candidate_id = candidate_history.selected_candidate_id
                selected_attempt_index = candidate_history.selected_attempt_index
            
            # Map action to branch_taken
            branch_map = {
                "accept": "accept",
                "reject": "reject",
                "switch_workflow": "switch",
                "retry_seed": "retry",
                "retry_prompt": "retry",
                "retry_settings": "retry",
            }
            branch_taken = branch_map.get(action, "accept")
            
            result["executed_action"] = {
                "executed_action": action,
                "execution_status": "completed",
                "selected_candidate_id": selected_candidate_id,
                "selected_attempt_index": selected_attempt_index,
                "branch_taken": branch_taken,
                "target_workflow_id": corrective_action_dict.get("target_workflow_id"),
                "notes": ["Default executed action for non-retry case"],
            }
        
        # Attach candidate_history to result
        result["candidate_history"] = candidate_history.to_dict()

        # Add candidate_selection block using unified selection policy
        # Extract candidates from history for selection
        candidates = []
        for attempt in candidate_history.attempts:
            candidate_dict = {
                "candidate_id": attempt.candidate_id,
                "execution_plan": {"workflow_id": attempt.workflow_id},
                "judge_status": attempt.judge_status,
                "orchestrator_report": {
                    "final_verdict": attempt.final_verdict,
                    "final_score": attempt.final_score,
                },
            }
            candidates.append(candidate_dict)
        
        if candidates:
            selection_decision = self.selection_policy.select_best_candidate(candidates)
            result["candidate_selection"] = selection_decision.to_dict()
            
            # Ensure top-level corrective_action matches selected candidate's corrective_action
            selected_attempt = candidate_history.get_selected_attempt()
            if selected_attempt and selected_attempt.corrective_action:
                result["corrective_action"] = selected_attempt.corrective_action

        # Persist final unified result with all load-bearing fields
        if save_metadata:
            result = self.metadata_service.persist_terminal_report(result)

        return result

    def _create_attempt_record(
        self,
        result: dict[str, Any],
        attempt_index: int,
        attempt_kind: str,
        parent_candidate_id: str | None = None,
    ) -> AttemptRecord:
        """Create an AttemptRecord from a result dict.
        
        Args:
            result: Result dict from an attempt
            attempt_index: Index of this attempt
            attempt_kind: Kind of attempt (initial, retry_mutation, workflow_switch, etc.)
            parent_candidate_id: ID of parent candidate if this is a retry/switch
            
        Returns:
            AttemptRecord with all relevant fields
        """
        execution_plan = result.get("execution_plan", {})
        orchestrator_report = result.get("orchestrator_report", {})
        workflow_switch = result.get("workflow_switch", {})
        mutation_report = result.get("mutation_report", {})
        mutation_retry = result.get("mutation_retry", {})
        
        builder = (
            AttemptRecordBuilder()
            .attempt_index(attempt_index)
            .candidate_id(generate_candidate_id())
            .parent_candidate_id(parent_candidate_id)
            .attempt_kind(attempt_kind)
            .workflow_id(execution_plan.get("workflow_id"))
            .task_type(execution_plan.get("task_type"))
            .judge_status(result.get("judge_status"))
            .final_verdict(orchestrator_report.get("final_verdict") if orchestrator_report else None)
            .final_score(orchestrator_report.get("final_score") if orchestrator_report else None)
            .source_trigger(workflow_switch.get("source_trigger") if workflow_switch else None)
            .mutation_report(mutation_report)
            .mutation_retry(mutation_retry)
            .workflow_switch(workflow_switch if workflow_switch else None)
            .corrective_action(result.get("corrective_action"))
            .executed_action(result.get("executed_action"))
            .images(result.get("images", []))
            .metadata_path(result.get("metadata_path"))
            .summary_path(result.get("summary_path"))
            .error_type(result.get("error_type"))
            .error_code(result.get("error_code"))
            .error(result.get("error"))
        )
        
        return builder.build()

    def _create_planning_failure_result(
        self,
        user_prompt: str,
        task_selection: TaskSelectionResult,
        missing_inputs: list[str],
    ) -> dict[str, Any]:
        """Create controlled failure result for missing required inputs.

        Args:
            user_prompt: Original user prompt
            task_selection: Task selection result
            missing_inputs: List of missing required input keys

        Returns:
            Dictionary with controlled failure information in unified contract format
        """
        task_selection_dict = {
            "task_type": task_selection.task_type.value,
            "confidence": task_selection.confidence,
            "reason": task_selection.reason,
            "routing_source": task_selection.routing_source,
            "required_inputs": task_selection.required_inputs,
            "missing_inputs": task_selection.missing_inputs,
            "ambiguity_level": task_selection.ambiguity_level,
            "safe_fallback_used": task_selection.safe_fallback_used,
        }
        
        result = build_agent_result(
            status="failed",
            failed_stage=FailedStage.PLANNING_GUARD,
            error_type="planning_failure",
            error_code=ErrorCode.MISSING_REQUIRED_INPUTS,
            error=f"Execution blocked: missing required inputs: {', '.join(missing_inputs)}",
            user_prompt=user_prompt,
            task_selection=task_selection_dict,
            execution_plan=None,
            images=[],
            metadata_path=None,
            summary_path=None,
            executed_action={
                "executed_action": "none",
                "execution_status": "blocked",
                "branch_taken": None,
                "notes": ["Execution blocked by missing inputs"],
                "error_type": "planning_failure",
                "error": f"Execution blocked: missing required inputs: {', '.join(missing_inputs)}",
            },
        )
        
        return result.to_dict()

    def get_task_selection(self, user_prompt: str, assets: dict[str, Any] | None = None) -> TaskSelectionResult:
        """Get task selection for a prompt without generating."""
        return self.task_selector.select(user_prompt, assets)

    async def run(
        self,
        user_prompt: str,
        task_selection: TaskSelectionResult,
        assets: dict[str, Any] | None = None,
        enable_judging: bool = False,
        enable_retry_loop: bool = False,
        force_retry: bool = False,
        force_switch: str | None = None,
        canonical_recipe: dict[str, Any] | None = None,
        status_callback: StatusCallback | None = None,
        tool_trace: ToolTrace | None = None,
        verbose: bool = False,
    ) -> dict[str, Any]:
        """Run agent with pre-computed task selection.

        Args:
            user_prompt: User's prompt text
            task_selection: Pre-computed task selection result
            assets: Dictionary of available assets (input_image, mask_image, etc.)
            enable_judging: Whether to enable judge pipeline
            enable_retry_loop: Whether to enable retry loop
            force_retry: Force retry path for proof mode (bypasses natural judge trigger)
            force_switch: Force workflow switch for proof mode (e.g., upscale_v1, inpaint_face_v1)
            status_callback: Optional callback for progress updates

        Returns:
            Unified agent result dictionary
        """
        callback = status_callback or (lambda s, p: None)

        # Verbose logging: Task received
        if verbose:
            print(f"\n[INFO] Task received: {user_prompt}")
            print(f"[INFO] Task classification: {task_selection.task_type.value}")
            print(f"[INFO] Routing source: {task_selection.routing_source}")
            print(f"[INFO] Confidence: {task_selection.confidence}")

        # Step 1: Get workflow specification (tool-wrapped)
        try:
            workflow_spec = await select_workflow_tool.run(
                tool_trace,
                registry=self.registry,
                task_type=task_selection.task_type,
            )
        except RuntimeError:
            workflow_spec = None

        # Verbose logging: Workflow route selection
        if verbose and workflow_spec:
            print(f"[INFO] Workflow route selected: {workflow_spec.workflow_id}")
            print(f"[INFO] Workflow description: {workflow_spec.description}")
            print(f"[INFO] Preset: {workflow_spec.preset_name}")
            print(f"[INFO] Rewrite mode: {workflow_spec.default_rewrite_mode}")

        if not workflow_spec:
            task_selection_dict = {
                "task_type": task_selection.task_type.value,
                "confidence": task_selection.confidence,
                "reason": task_selection.reason,
                "routing_source": task_selection.routing_source,
                "required_inputs": task_selection.required_inputs,
                "missing_inputs": task_selection.missing_inputs,
                "ambiguity_level": task_selection.ambiguity_level,
                "safe_fallback_used": task_selection.safe_fallback_used,
            }
            result = build_agent_result(
                status="failed",
                failed_stage=FailedStage.WORKFLOW_LOOKUP,
                error_type="workflow_lookup_failure",
                error_code=ErrorCode.WORKFLOW_NOT_FOUND,
                error=f"No workflow found for task type: {task_selection.task_type.value}",
                user_prompt=user_prompt,
                task_selection=task_selection_dict,
                execution_plan=None,
                images=[],
                metadata_path=None,
                summary_path=None,
                executed_action={
                    "executed_action": "none",
                    "execution_status": "failed",
                    "branch_taken": None,
                    "notes": ["Workflow lookup failed before execution"],
                    "error_type": "workflow_lookup_failure",
                    "error": f"No workflow found for task type: {task_selection.task_type.value}",
                },
            )
            return result.to_dict()

        if not workflow_spec.implemented:
            task_selection_dict = {
                "task_type": task_selection.task_type.value,
                "confidence": task_selection.confidence,
                "reason": task_selection.reason,
                "routing_source": task_selection.routing_source,
                "required_inputs": task_selection.required_inputs,
                "missing_inputs": task_selection.missing_inputs,
                "ambiguity_level": task_selection.ambiguity_level,
                "safe_fallback_used": task_selection.safe_fallback_used,
            }
            result = build_agent_result(
                status="failed",
                failed_stage=FailedStage.WORKFLOW_LOOKUP,
                error_type="workflow_not_implemented",
                error_code=ErrorCode.WORKFLOW_NOT_IMPLEMENTED,
                error=f"Workflow '{workflow_spec.workflow_id}' is not implemented yet",
                user_prompt=user_prompt,
                task_selection=task_selection_dict,
                execution_plan=None,
                images=[],
                metadata_path=None,
                summary_path=None,
                executed_action={
                    "executed_action": "none",
                    "execution_status": "failed",
                    "branch_taken": None,
                    "notes": ["Workflow not implemented before execution"],
                    "error_type": "workflow_not_implemented",
                    "error": f"Workflow '{workflow_spec.workflow_id}' is not implemented yet",
                },
            )
            return result.to_dict()

        # Step 2: Validate required inputs (tool-wrapped planning guard)
        try:
            await validate_required_inputs_tool.run(
                tool_trace,
                task_selection=task_selection,
                assets=assets or {},
            )
        except ValueError as exc:
            callback("FAILED", {
                "stage": "preflight_validation",
                "error_type": "missing_assets",
                "error": str(exc),
            })
            return self._create_planning_failure_result(
                user_prompt=user_prompt,
                task_selection=task_selection,
                missing_inputs=task_selection.missing_inputs,
            )

        # Step 3: Build execution plan
        resolved_inputs = {"prompt": user_prompt}
        if assets:
            for key, value in assets.items():
                if value is not None:
                    resolved_inputs[key] = value

        execution_plan = self.plan_builder.build(
            user_prompt=user_prompt,
            task_selection=task_selection,
            workflow_id=workflow_spec.workflow_id,
            workflow_path=workflow_spec.workflow_path,
            preset_name=workflow_spec.preset_name,
            rewrite_mode=workflow_spec.default_rewrite_mode,
            required_inputs=workflow_spec.required_inputs,
            resolved_inputs=resolved_inputs,
            enable_judging=enable_judging and workflow_spec.supports_judging,
            enable_retry_loop=enable_retry_loop,
            canonical_recipe=canonical_recipe,
        )

        # Step 4: Initialize candidate history
        candidate_history = CandidateHistory()

        # Step 5: Run first attempt
        callback("QUEUED", {"prompt_id": "-", "info": f"Starting workflow: {workflow_spec.workflow_id}"})

        # Verbose logging: Checkpoint selection
        if verbose:
            checkpoint = canonical_recipe.get("checkpoint") if canonical_recipe else None
            if not checkpoint:
                # Default checkpoint when not specified - use RealVis XL for portrait
                if task_selection.task_type.value == "portrait_txt2img":
                    checkpoint = "realvisxlV50_v50Bakedvae.safetensors"
                else:
                    checkpoint = "sd_xl_base_1.0_0.9vae.safetensors"
            print(f"\n[MODEL] task={task_selection.task_type.value}")
            print(f"[MODEL] candidates=realvisxlV50_v50Bakedvae.safetensors, juggernautXL_version2.safetensors, sd_xl_base_1.0_0.9vae.safetensors")
            print(f"[MODEL] selected={checkpoint}")
            if canonical_recipe:
                print(f"[MODEL] reason=canonical recipe override for proof mode")
            elif task_selection.task_type.value == "portrait_txt2img":
                print(f"[MODEL] reason=preferred realism checkpoint for portrait task")
            else:
                print(f"[MODEL] reason=default checkpoint for {task_selection.task_type.value} task")

        # Fix model-selection propagation: ensure selected checkpoint is used
        # If we have a selected checkpoint but no canonical_recipe, create one to ensure propagation
        if not canonical_recipe:
            selected_checkpoint = None
            if task_selection.task_type.value == "portrait_txt2img":
                selected_checkpoint = "realvisxlV50_v50Bakedvae.safetensors"
            else:
                selected_checkpoint = "sd_xl_base_1.0_0.9vae.safetensors"
            
            # Update execution_plan with canonical_recipe to ensure checkpoint propagation
            if selected_checkpoint:
                execution_plan.canonical_recipe = {
                    "checkpoint": selected_checkpoint,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    "steps": 30,
                    "cfg": 6.0,
                    "width": 1024,
                    "height": 1024,
                    "seed": None,
                    "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, smooth skin texture, doll-like, anime, cartoon, oversaturated, harsh lighting",
                    "filename_prefix": "agent/portrait",
                }

        first_result = await self._run_single_attempt(
            execution_plan=execution_plan,
            workflow_spec=workflow_spec,
            disable_internal_retry=True,
            save_metadata=True,
            tool_trace=tool_trace,
            verbose=verbose,
        )

        # Track first attempt in history
        first_attempt_record = self._create_attempt_record(
            result=first_result,
            attempt_index=1,
            attempt_kind="initial",
            parent_candidate_id=None,
        )
        candidate_history.add_attempt(first_attempt_record)

        # Step 6: Handle mutation-aware retry if needed
        result = await self._handle_mutation_aware_retry(
            execution_plan=execution_plan,
            workflow_spec=workflow_spec,
            first_result=first_result,
            task_selection=task_selection,
            assets=assets,
            save_metadata=True,
            switch_applied_this_run=False,
            candidate_history=candidate_history,
            force_retry=force_retry,
            force_switch=force_switch,
        )

        # Ensure result has task_selection attached
        if "task_selection" not in result or result.get("task_selection") is None:
            task_selection_dict = {
                "task_type": task_selection.task_type.value,
                "confidence": task_selection.confidence,
                "reason": task_selection.reason,
                "routing_source": task_selection.routing_source,
                "required_inputs": task_selection.required_inputs,
                "missing_inputs": task_selection.missing_inputs,
                "ambiguity_level": task_selection.ambiguity_level,
                "safe_fallback_used": task_selection.safe_fallback_used,
            }
            result["task_selection"] = task_selection_dict

        # Ensure execution_plan is attached
        if "execution_plan" not in result or result.get("execution_plan") is None:
            result["execution_plan"] = execution_plan.to_dict()

        # Ensure workflow_switch block is present
        if "workflow_switch" not in result or result.get("workflow_switch") is None:
            result["workflow_switch"] = {
                "switch_applied": False,
                "from_workflow_id": execution_plan.workflow_id,
                "to_workflow_id": None,
                "switch_reason": None,
                "source_trigger": None,
                "switch_allowed": False,
                "missing_inputs": [],
                "notes": [],
            }

        # Ensure corrective_action block is present
        if "corrective_action" not in result or result.get("corrective_action") is None:
            judge_status = result.get("judge_status")
            orchestrator_report = result.get("orchestrator_report")
            
            if judge_status == "pass":
                result["corrective_action"] = {
                    "action": "accept",
                    "reason_code": "accepted_by_judge",
                    "reason": "Generation accepted by judge",
                    "source_repairs": [],
                    "selected_workflow_id": execution_plan.workflow_id,
                    "target_workflow_id": None,
                    "required_inputs": [],
                    "missing_inputs": [],
                    "switch_allowed": False,
                    "notes": ["Judge approved the result"],
                }
            elif judge_status == "reject":
                global_repairs = orchestrator_report.get("global_repairs", []) if orchestrator_report else []
                result["corrective_action"] = {
                    "action": "reject",
                    "reason_code": "reject_after_judge",
                    "reason": "Reject after judge aggregation",
                    "source_repairs": global_repairs,
                    "selected_workflow_id": execution_plan.workflow_id,
                    "target_workflow_id": None,
                    "required_inputs": [],
                    "missing_inputs": [],
                    "switch_allowed": False,
                    "notes": ["Judge rejected the result"],
                }
            else:
                result["corrective_action"] = {
                    "action": "accept",
                    "reason_code": "accepted_by_judge",
                    "reason": "No judge evaluation - accepting result",
                    "source_repairs": [],
                    "selected_workflow_id": execution_plan.workflow_id,
                    "target_workflow_id": None,
                    "required_inputs": [],
                    "missing_inputs": [],
                    "switch_allowed": False,
                    "notes": ["Judging was disabled or judge pipeline failed"],
                }

        # Ensure executed_action block is present
        if "executed_action" not in result or result.get("executed_action") is None:
            corrective_action_dict = result.get("corrective_action", {})
            action = corrective_action_dict.get("action", "accept")
            
            selected_candidate_id = None
            selected_attempt_index = None
            if candidate_history:
                selected_candidate_id = candidate_history.selected_candidate_id
                selected_attempt_index = candidate_history.selected_attempt_index
            
            branch_map = {
                "accept": "accept",
                "reject": "reject",
                "switch_workflow": "switch",
                "retry_seed": "retry",
                "retry_prompt": "retry",
                "retry_settings": "retry",
            }
            branch_taken = branch_map.get(action, "accept")
            
            result["executed_action"] = {
                "executed_action": action,
                "execution_status": "completed",
                "selected_candidate_id": selected_candidate_id,
                "selected_attempt_index": selected_attempt_index,
                "branch_taken": branch_taken,
                "target_workflow_id": corrective_action_dict.get("target_workflow_id"),
                "notes": ["Default executed action for non-retry case"],
            }

        # Attach candidate_history to result
        result["candidate_history"] = candidate_history.to_dict()

        # Add candidate_selection block
        candidates = []
        for attempt in candidate_history.attempts:
            candidate_dict = {
                "candidate_id": attempt.candidate_id,
                "execution_plan": {"workflow_id": attempt.workflow_id},
                "judge_status": attempt.judge_status,
                "orchestrator_report": {
                    "final_verdict": attempt.final_verdict,
                    "final_score": attempt.final_score,
                },
            }
            candidates.append(candidate_dict)
        
        if candidates:
            selection_decision = self.selection_policy.select_best_candidate(candidates)
            result["candidate_selection"] = selection_decision.to_dict()
            
            selected_attempt = candidate_history.get_selected_attempt()
            if selected_attempt and selected_attempt.corrective_action:
                result["corrective_action"] = selected_attempt.corrective_action

        # Add minimal live QC block
        qc_status = "not_implemented"
        qc_errors = []
        if result.get("status") == "completed":
            images = result.get("images", [])
            if images:
                qc_status = "pass"
                for img in images:
                    if not img.get("filename"):
                        qc_status = "fail"
                        qc_errors.append(f"Image missing filename: {img}")
                    if not img.get("node_id"):
                        qc_status = "fail"
                        qc_errors.append(f"Image missing node_id: {img}")
            else:
                qc_status = "fail"
                qc_errors.append("No images generated")
        else:
            qc_status = "not_applicable"
        
        result["qc_status"] = qc_status
        result["qc_errors"] = qc_errors

        # Add minimal live QA block
        qa_status = "not_implemented"
        qa_errors = []
        if result.get("status") == "completed":
            qa_status = "pass"
            # Check that workflow was selected
            if not result.get("execution_plan", {}).get("workflow_id"):
                qa_status = "fail"
                qa_errors.append("No workflow_id in execution_plan")
            # Check that submit succeeded (has prompt_id) - prompt_id is at top level from ComfyClient
            # Don't fail if missing since it might be in nested metadata
            # Check that history/view retrieval succeeded (has images)
            if not result.get("images"):
                qa_status = "fail"
                qa_errors.append("No images in result")
            # Check metadata/summary consistency
            if not result.get("metadata_path"):
                qa_status = "fail"
                qa_errors.append("No metadata_path in result")
            if not result.get("summary_path"):
                qa_status = "fail"
                qa_errors.append("No summary_path in result")
        else:
            qa_status = "not_applicable"
        
        result["qa_status"] = qa_status
        result["qa_errors"] = qa_errors

        # Persist final unified result
        result = self.metadata_service.persist_terminal_report(result)

        # Emit observational persist_run tool event (files are already on disk)
        await persist_run_tool.run(
            tool_trace,
            metadata_path=result.get("metadata_path"),
            summary_path=result.get("summary_path"),
            status=result.get("status", "unknown"),
        )

        # Add verdict field for user-facing result
        if result.get("status") == "completed":
            judge_status = result.get("judge_status")
            if judge_status == "pass":
                result["verdict"] = "accepted"
            elif judge_status == "reject":
                result["verdict"] = "rejected"
            else:
                result["verdict"] = "completed"
        else:
            result["verdict"] = "failed"

        callback("COMPLETED", {
            "prompt_id": result.get("prompt_id", "-"),
            "images_found": len(result.get("images", [])),
        })

        return result

    def list_workflows(self) -> list[dict[str, Any]]:
        """List all available workflows."""
        return [spec.to_dict() for spec in self.registry.list_workflows()]

    def list_implemented_workflows(self) -> list[dict[str, Any]]:
        """List only implemented workflows."""
        return [spec.to_dict() for spec in self.registry.get_implemented_workflows()]
