"""
Combine Universal State Machine

Universal state machine for the internal multi-agent orchestrator.
This state machine is route-agnostic and works for all route families.
"""

from typing import List, Dict, Set, Optional


class CombineStateMachine:
    """Universal state machine for Combine orchestrator"""
    
    # All valid states
    STATES = [
        "initial",
        "brief_intake_required",
        "route_classification_required",
        "production_plan_required",
        "production_plan_review",
        "asset_resolution_required",
        "workflow_plan_required",
        "workflow_preflight_required",
        "generation_authorization_required",
        "operator_generation_authorization_required",
        "generate_assets",
        "visual_qa_required_stub_pending",
        "visual_qa_required",
        "operator_visual_review",
        "corrective_retry_plan_required",
        "controlled_retry_authorization_required",
        "corrective_retry_implementation_required",
        "operator_retry_generation_authorization_required",
        "corrective_retry_generate_assets",
        "corrective_retry_result_review_required",
        "corrective_retry_visual_qa_preflight_required",
        "corrective_retry_generate_assets_v2",
        "corrective_retry_v2_result_review_required",
        "corrective_retry_v2_visual_qa_preflight_required",
        "corrective_retry_v2_visual_qa",
        "corrective_retry_v3_plan_required",
        "operator_retry_v3_plan_review_required",
        "corrective_retry_v4_plan_required",
        "operator_retry_v4_plan_review_required",
        "corrective_retry_v4_generate_assets",
        "corrective_retry_v4_submit_path_fix_required",
        "corrective_retry_v4_result_review_required",
        "corrective_retry_v4_non_stub_execution_route_required",
        "operator_retry_v4_real_execution_authorization_required",
        "corrective_retry_v4_real_execute_assets",
        "corrective_retry_v4_visual_qa_preflight_required",
        "corrective_retry_v4_visual_qa_required",
        "corrective_retry_v4_visual_correction_plan_required",
        "operator_retry_v4_visual_correction_plan_review_required",
        "corrective_retry_v4_retry_implementation_plan_update_required",
        "operator_retry_v4_updated_implementation_plan_review_required",
        "operator_retry_v4_generation_authorization_required",
        "corrective_retry_v5_visual_recovery_required",
        "corrective_retry_v5_generation_runtime_blocked",
        "operator_visual_review_required",
        "real_generation_readiness_required",
        "real_generation_preflight_required",
        "real_generation_payload_review",
        "operator_real_generation_authorization_required",
        "operator_real_generation_approved",
        "real_generate_assets",
        "real_generation_result_collected",
        "real_generation_result_review_required",
        "real_visual_qa_preflight_required",
        "real_visual_qa_required",
        "retry_correction_required",
        "retry_plan_review_required",
        "operator_retry_authorization_required",
        "corrective_retry_payload_rebuild_required",
        "controlled_asset_resolution_review_required",
        "production_brain_audit_required",
        "visual_failure_audit_required",
        "generation_recipe_audit_required",
        "workflow_rebuild_plan_required",
        "operator_strategy_review",
        "workflow_td_rebuild_required",
        "recipe_rebuild_contract_required",
        "prompt_contract_rebuild_required",
        "quality_pipeline_contract_required",
        "workflow_rebuild_preflight_required",
        "operator_rebuild_approval_required",
        "operator_rebuild_approved",
        "workflow_recipe_implementation_required",
        "generation_payload_rebuild_required",
        "workflow_graph_rebuild_required",
        "workflow_rebuild_validation_required",
        "assembly_preflight_required",
        "assembly_required",
        "final_qc_required",
        "final_operator_acceptance",
        "completed",
        "blocked_manual_review",
        "blocked_generation_route_aborted",
        "targeted_visual_refinement_plan_required",
        "targeted_refinement_generation_authorization_required",
        "v8_quality_locked_generation_authorization_required",
        "v8_generation_runtime_blocked",
        "v8_generation_runtime_recovery_required",
        "v8_generation_reexecution_authorization_required",
        "v8_operator_visual_review_required"
    ]
    
    # Terminal states
    TERMINAL_STATES = {
        "completed",
        "blocked_manual_review",
        "blocked_generation_route_aborted"
    }
    
    # Allowed transitions
    # Format: from_state -> [to_state, ...]
    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        "initial": {
            "brief_intake_required"
        },
        "brief_intake_required": {
            "route_classification_required"
        },
        "route_classification_required": {
            "production_plan_required"
        },
        "production_plan_required": {
            "production_plan_review"
        },
        "production_plan_review": {
            "asset_resolution_required",
            "production_plan_required"  # Revision
        },
        "asset_resolution_required": {
            "workflow_plan_required",
            "controlled_asset_resolution_review_required"
        },
        "controlled_asset_resolution_review_required": {
            "workflow_plan_required",
            "asset_resolution_required"  # Re-resolve
        },
        "workflow_plan_required": {
            "workflow_preflight_required"
        },
        "workflow_preflight_required": {
            "generation_authorization_required"
        },
        "generation_authorization_required": {
            "operator_generation_authorization_required",
            "controlled_asset_resolution_review_required",
            "corrective_retry_payload_rebuild_required"
        },
        "operator_generation_authorization_required": {
            "generate_assets"
        },
        "operator_retry_generation_authorization_required": {
            "corrective_retry_generate_assets"
        },
        "corrective_retry_generate_assets": {
            "corrective_retry_result_review_required"
        },
        "corrective_retry_result_review_required": {
            "corrective_retry_visual_qa_preflight_required",
            "corrective_retry_plan_required",  # Loop back for retry
            "blocked_manual_review"
        },
        "corrective_retry_visual_qa_preflight_required": {
            "visual_qa_required"
        },
        "corrective_retry_generate_assets_v2": {
            "corrective_retry_v2_result_review_required"
        },
        "corrective_retry_v2_result_review_required": {
            "corrective_retry_v2_visual_qa_preflight_required",
            "blocked_manual_review"
        },
        "corrective_retry_v2_visual_qa_preflight_required": {
            "corrective_retry_v2_visual_qa"
        },
        "corrective_retry_v2_visual_qa": {
            "operator_visual_review"
        },
        "generate_assets": {
            "visual_qa_required_stub_pending",
            "operator_generation_authorization_required"
        },
        "visual_qa_required_stub_pending": {
            "visual_qa_required"
        },
        "visual_qa_required": {
            "operator_visual_review",
            "retry_correction_required",
            "real_generation_readiness_required",
        },
        "operator_visual_review": {
            "assembly_preflight_required",
            "assembly_required",
            "retry_correction_required",
            "real_generation_readiness_required",
            "corrective_retry_plan_required",
            "corrective_retry_v3_plan_required",
            "blocked_manual_review"
        },
        "corrective_retry_v3_plan_required": {
            "operator_retry_v3_plan_review_required"
        },
        "operator_retry_v3_plan_review_required": {
            "operator_retry_v3_plan_review_required",  # Self-loop: stays halted here
            "blocked_manual_review"
        },
        "corrective_retry_v4_plan_required": {
            "operator_retry_v4_plan_review_required"
        },
        "operator_retry_v4_plan_review_required": {
            "operator_retry_v4_plan_review_required",  # Self-loop: stays halted here
            "blocked_manual_review"
        },
        "corrective_retry_v4_generate_assets": {
            "corrective_retry_v4_submit_path_fix_required"
        },
        "corrective_retry_v4_submit_path_fix_required": {
            "corrective_retry_v4_non_stub_execution_route_required"
        },
        "corrective_retry_v4_non_stub_execution_route_required": {
            "operator_retry_v4_real_execution_authorization_required",
            "blocked_manual_review"
        },
        "operator_retry_v4_real_execution_authorization_required": {
            "operator_retry_v4_real_execution_authorization_required",  # Self-loop: halted pending operator
            "corrective_retry_v4_real_execute_assets",  # Transition to real execution after authorization
            "blocked_manual_review"
        },
        "corrective_retry_v4_real_execute_assets": {
            "corrective_retry_v4_result_review_required"
        },
        "corrective_retry_v4_result_review_required": {
            "corrective_retry_v4_visual_qa_preflight_required",
            "blocked_manual_review"
        },
        "corrective_retry_v4_visual_qa_preflight_required": {
            "corrective_retry_v4_visual_qa_required"
        },
        "corrective_retry_v4_visual_qa_required": {
            "operator_visual_review",
            "corrective_retry_v4_visual_correction_plan_required"
        },
        "corrective_retry_v4_visual_correction_plan_required": {
            "operator_retry_v4_visual_correction_plan_review_required"
        },
        "operator_retry_v4_visual_correction_plan_review_required": {
            "operator_retry_v4_visual_correction_plan_review_required",  # Self-loop: halted pending operator
            "corrective_retry_v4_plan_required",  # Operator approved - proceed to V4 plan
            "corrective_retry_v4_retry_implementation_plan_update_required",  # Operator approved visual correction plan
            "blocked_manual_review"
        },
        "corrective_retry_v4_retry_implementation_plan_update_required": {
            "operator_retry_v4_updated_implementation_plan_review_required"
        },
        "operator_retry_v4_updated_implementation_plan_review_required": {
            "operator_retry_v4_updated_implementation_plan_review_required",  # Self-loop: halted pending operator
            "corrective_retry_v4_retry_implementation_plan_update_required",  # Request changes — back to update
            "operator_retry_v4_generation_authorization_required",  # Operator approved - proceed to generation authorization
            "blocked_manual_review"
        },
        "operator_retry_v4_generation_authorization_required": {
            "operator_retry_v4_generation_authorization_required",  # Self-loop: halted pending operator
            "corrective_retry_v4_generate_assets",  # Authorized - proceed to generation
            "blocked_manual_review"
        },
        "corrective_retry_v5_visual_recovery_required": {
            "operator_visual_review_required"
        },
        "corrective_retry_v5_generation_runtime_blocked": {
            "corrective_retry_v5_generation_runtime_blocked",  # Self-loop: blocked until ComfyUI available
            "targeted_visual_refinement_plan_required"  # Can transition to refinement planning
        },
        "targeted_visual_refinement_plan_required": {
            "targeted_refinement_generation_authorization_required",
            "targeted_visual_refinement_plan_required"  # Self-loop: halted pending refinement plan
        },
        "targeted_refinement_generation_authorization_required": {
            "targeted_refinement_generation_authorization_required",  # Self-loop: halted pending operator authorization
            "generate_assets",  # Once authorized, can generate refined asset
            "blocked_manual_review"
        },
        "v8_quality_locked_generation_authorization_required": {
            "v8_quality_locked_generation_authorization_required",  # Self-loop: halted pending operator authorization
            "generate_assets",  # Operator authorized -> proceed to generate
            "v8_operator_visual_review_required",  # V8 runtime recovery -> operator visual review
            "blocked_manual_review"
        },
        "v8_generation_runtime_blocked": {
            "v8_generation_runtime_blocked",  # Self-loop: blocked until ComfyUI available
            "v8_generation_runtime_recovery_required",  # Can transition to recovery
            "v8_generation_reexecution_authorization_required",  # Can advance to reexecution authorization gate
            "v8_quality_locked_generation_authorization_required"  # Can restart authorization
        },
        "v8_generation_runtime_recovery_required": {
            "v8_generation_runtime_recovery_required",  # Self-loop: halted pending recovery
            "v8_quality_locked_generation_authorization_required",  # Can go back to generation authorization
            "v8_generation_reexecution_authorization_required",  # Can advance to reexecution authorization gate
            "blocked_manual_review"
        },
        "v8_generation_reexecution_authorization_required": {
            "v8_generation_reexecution_authorization_required",  # Self-loop: halted pending authorization
            "v8_quality_locked_generation_authorization_required"  # Authorized -> proceed to generation
        },
        "operator_visual_review_required": {
            "operator_visual_review_required",  # Self-loop: halted pending operator
            "assembly_preflight_required",  # Approved - proceed to assembly
            "blocked_manual_review",
            "v8_quality_locked_generation_authorization_required"  # V7 rejected -> V8 quality lock
        },
        "v8_operator_visual_review_required": {
            "v8_operator_visual_review_required",  # Self-loop: halted pending operator
            "assembly_preflight_required",  # Approved - proceed to assembly
            "blocked_manual_review",
        },
        "real_generation_readiness_required": {
            "real_generation_preflight_required"
        },
        "real_generation_preflight_required": {
            "real_generation_payload_review"
        },
        "real_generation_payload_review": {
            "operator_real_generation_authorization_required"
        },
        "operator_real_generation_authorization_required": {
            "operator_real_generation_approved",
        },
        "operator_real_generation_approved": {
            "real_generate_assets",
        },
        "real_generate_assets": {
            "real_generation_result_collected",
        },
        "real_generation_result_collected": {
            "real_generation_result_review_required",
            "real_visual_qa_preflight_required",
        },
        "real_generation_result_review_required": {
            "operator_visual_review",
            "blocked_manual_review",
        },
        "real_visual_qa_preflight_required": {
            "real_visual_qa_required",
            "production_brain_audit_required",
        },
        "real_visual_qa_required": {
            "operator_visual_review",
        },
        "production_brain_audit_required": {
            "visual_failure_audit_required",
        },
        "visual_failure_audit_required": {
            "generation_recipe_audit_required",
        },
        "generation_recipe_audit_required": {
            "workflow_rebuild_plan_required",
        },
        "workflow_rebuild_plan_required": {
            "operator_strategy_review",
        },
        "operator_strategy_review": {
            "brief_intake_required",  # Restart with new workflow
            "route_classification_required",
            "production_plan_required",
            "workflow_plan_required",
            "workflow_td_rebuild_required",  # New rebuild path
            "blocked_manual_review",
        },
        "workflow_td_rebuild_required": {
            "recipe_rebuild_contract_required",
        },
        "recipe_rebuild_contract_required": {
            "prompt_contract_rebuild_required",
        },
        "prompt_contract_rebuild_required": {
            "quality_pipeline_contract_required",
        },
        "quality_pipeline_contract_required": {
            "workflow_rebuild_preflight_required",
        },
        "workflow_rebuild_preflight_required": {
            "operator_rebuild_approval_required",
        },
        "operator_rebuild_approval_required": {
            "operator_rebuild_approved",  # New: operator approves rebuild implementation
            "workflow_plan_required",  # Restart with rebuilt workflow
            "brief_intake_required",  # Full restart
            "blocked_manual_review",
        },
        "operator_rebuild_approved": {
            "workflow_recipe_implementation_required",
        },
        "workflow_recipe_implementation_required": {
            "generation_payload_rebuild_required",
        },
        "generation_payload_rebuild_required": {
            "workflow_graph_rebuild_required",
        },
        "workflow_graph_rebuild_required": {
            "workflow_rebuild_validation_required",
        },
        "workflow_rebuild_validation_required": {
            "real_generation_readiness_required",
        },
        "retry_correction_required": {
            "retry_plan_review_required",
            "operator_retry_authorization_required"
        },
        "corrective_retry_plan_required": {
            "controlled_retry_authorization_required"
        },
        "controlled_retry_authorization_required": {
            "corrective_retry_plan_required",
            "corrective_retry_implementation_required",
            "brief_intake_required",
            "route_classification_required",
            "production_plan_required",
            "blocked_manual_review"
        },
        "corrective_retry_implementation_required": {
            "operator_retry_generation_authorization_required",
            "blocked_manual_review"
        },
        "retry_plan_review_required": {
            "operator_retry_authorization_required"
        },
        "operator_retry_authorization_required": {
            "generation_authorization_required"
        },
        "corrective_retry_payload_rebuild_required": {
            "real_generation_readiness_required"
        },
        "assembly_preflight_required": {
            "assembly_required"
        },
        "assembly_required": {
            "final_qc_required"
        },
        "final_qc_required": {
            "final_operator_acceptance",
            "assembly_required"  # Re-assemble
        },
        "final_operator_acceptance": {
            "completed"
        },
        "completed": set(),  # No transitions from terminal
        "blocked_manual_review": {
            "brief_intake_required",  # Restart
            "route_classification_required",
            "production_plan_required"
        },
        "blocked_generation_route_aborted": {
            "brief_intake_required",  # Restart
            "route_classification_required",
            "production_plan_required"
        }
    }
    
    # Forbidden transitions (explicitly blocked for safety)
    FORBIDDEN_TRANSITIONS: Set[tuple] = {
        # Generation cannot happen before preflight/authorization
        ("workflow_plan_required", "generate_assets"),
        ("workflow_preflight_required", "generate_assets"),
        ("brief_intake_required", "generate_assets"),
        ("route_classification_required", "generate_assets"),
        
        # QA cannot happen before generated artifacts
        ("brief_intake_required", "visual_qa_required"),
        ("route_classification_required", "visual_qa_required"),
        ("production_plan_required", "visual_qa_required"),
        ("workflow_plan_required", "visual_qa_required"),
        ("workflow_preflight_required", "visual_qa_required"),
        ("generation_authorization_required", "visual_qa_required"),
        
        # Assembly cannot happen before accepted visuals/assets
        ("brief_intake_required", "assembly_required"),
        ("route_classification_required", "assembly_required"),
        ("production_plan_required", "assembly_required"),
        ("workflow_plan_required", "assembly_required"),
        ("workflow_preflight_required", "assembly_required"),
        ("generation_authorization_required", "assembly_required"),
        ("generate_assets", "assembly_required"),  # Must go through QA first
        
        # Final export cannot happen before final QC
        ("visual_qa_required", "completed"),
        ("operator_visual_review", "completed"),
        ("assembly_required", "completed"),
        ("generate_assets", "completed"),
        ("operator_real_generation_authorization_required", "real_generate_assets"),
        ("real_generate_assets", "assembly_required"),
        ("real_generate_assets", "production_accepted"),
        ("real_generation_result_collected", "assembly_required"),
        
        # Production brain layer: cannot skip to generation without rebuild
        ("production_brain_audit_required", "real_generate_assets"),
        ("workflow_rebuild_plan_required", "real_generate_assets"),
        ("operator_strategy_review", "real_generate_assets"),
        ("operator_strategy_review", "assembly_required"),
        
        # Workflow TD rebuild layer: cannot skip rebuild steps
        ("workflow_td_rebuild_required", "real_generate_assets"),
        ("recipe_rebuild_contract_required", "real_generate_assets"),
        ("prompt_contract_rebuild_required", "real_generate_assets"),
        ("quality_pipeline_contract_required", "real_generate_assets"),
        ("workflow_rebuild_preflight_required", "real_generate_assets"),
        ("operator_rebuild_approval_required", "real_generate_assets"),
        ("operator_rebuild_approved", "real_generate_assets"),
        ("workflow_recipe_implementation_required", "real_generate_assets"),
        ("generation_payload_rebuild_required", "real_generate_assets"),
        ("workflow_graph_rebuild_required", "real_generate_assets"),
        ("workflow_rebuild_validation_required", "real_generate_assets"),
        
        # Corrective retry implementation layer: cannot skip to generation or downstream
        ("corrective_retry_implementation_required", "generate_assets"),
        ("corrective_retry_implementation_required", "real_generate_assets"),
        ("corrective_retry_implementation_required", "assembly_required"),
        ("corrective_retry_implementation_required", "visual_qa_required"),
        ("corrective_retry_implementation_required", "real_visual_qa_required"),
        ("corrective_retry_implementation_required", "completed"),
        ("corrective_retry_implementation_required", "production_accepted"),
        
        # Corrective retry generation layer: cannot skip to downstream or second generation
        ("operator_retry_generation_authorization_required", "generate_assets"),
        ("operator_retry_generation_authorization_required", "real_generate_assets"),
        ("operator_retry_generation_authorization_required", "assembly_required"),
        ("operator_retry_generation_authorization_required", "completed"),
        ("corrective_retry_generate_assets", "generate_assets"),
        ("corrective_retry_generate_assets", "real_generate_assets"),
        ("corrective_retry_generate_assets", "assembly_required"),
        ("corrective_retry_generate_assets", "completed"),
        ("corrective_retry_generate_assets", "production_accepted"),
        ("corrective_retry_generate_assets", "visual_qa_required"),
        ("corrective_retry_generate_assets", "real_visual_qa_required"),
        ("corrective_retry_result_review_required", "assembly_required"),
        ("corrective_retry_result_review_required", "completed"),
        ("corrective_retry_result_review_required", "production_accepted"),
        ("corrective_retry_visual_qa_preflight_required", "assembly_required"),
        ("corrective_retry_visual_qa_preflight_required", "completed"),
        ("corrective_retry_visual_qa_preflight_required", "production_accepted"),

        # Cannot jump to assembly without completing rebuild
        ("workflow_td_rebuild_required", "assembly_required"),
        ("recipe_rebuild_contract_required", "assembly_required"),
        ("prompt_contract_rebuild_required", "assembly_required"),
        ("quality_pipeline_contract_required", "assembly_required"),
        ("workflow_rebuild_preflight_required", "assembly_required"),
        ("operator_rebuild_approval_required", "assembly_required"),
        ("operator_rebuild_approved", "assembly_required"),
        ("workflow_recipe_implementation_required", "assembly_required"),
        ("generation_payload_rebuild_required", "assembly_required"),
        ("workflow_graph_rebuild_required", "assembly_required"),
        ("workflow_rebuild_validation_required", "assembly_required"),

        # RC-COMBINE-V2-2781-2840: Block direct transitions from updated plan review to runtime actions
        ("operator_retry_v4_updated_implementation_plan_review_required", "corrective_retry_v4_generate_assets"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "corrective_retry_v4_real_execute_assets"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "generate_assets"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "real_generate_assets"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "visual_qa_required"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "corrective_retry_v4_visual_qa_required"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "real_visual_qa_required"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "assembly_required"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "assembly_preflight_required"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "completed"),
        ("operator_retry_v4_updated_implementation_plan_review_required", "production_accepted"),

        # v8_generation_reexecution_authorization_required: cannot skip to runtime, visual review, assembly, or downstream
        ("v8_generation_reexecution_authorization_required", "generate_assets"),
        ("v8_generation_reexecution_authorization_required", "real_generate_assets"),
        ("v8_generation_reexecution_authorization_required", "operator_visual_review_required"),
        ("v8_generation_reexecution_authorization_required", "visual_qa_required"),
        ("v8_generation_reexecution_authorization_required", "assembly_required"),
        ("v8_generation_reexecution_authorization_required", "assembly_preflight_required"),
        ("v8_generation_reexecution_authorization_required", "completed"),
        ("v8_generation_reexecution_authorization_required", "production_accepted"),

        # v8_operator_visual_review_required: cannot skip to downstream, final, or production
        ("v8_operator_visual_review_required", "completed"),
        ("v8_operator_visual_review_required", "production_accepted"),
        ("v8_operator_visual_review_required", "final_qc_required"),
        ("v8_operator_visual_review_required", "final_operator_acceptance"),
    }
    
    @classmethod
    def is_valid_state(cls, state: str) -> bool:
        """Check if a state is valid"""
        return state in cls.STATES
    
    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> bool:
        """Check if a transition is allowed"""
        # Validate both states
        if not cls.is_valid_state(from_state):
            return False
        if not cls.is_valid_state(to_state):
            return False
        
        # Check if explicitly forbidden
        if (from_state, to_state) in cls.FORBIDDEN_TRANSITIONS:
            return False
        
        # Check if allowed
        allowed = cls.ALLOWED_TRANSITIONS.get(from_state, set())
        return to_state in allowed
    
    @classmethod
    def validate_transition(cls, from_state: str, to_state: str) -> None:
        """Validate a transition, raise ValueError if invalid"""
        if not cls.is_valid_state(from_state):
            raise ValueError(f"Invalid from_state: {from_state}")
        
        if not cls.is_valid_state(to_state):
            raise ValueError(f"Invalid to_state: {to_state}")
        
        if (from_state, to_state) in cls.FORBIDDEN_TRANSITIONS:
            raise ValueError(
                f"Forbidden transition: {from_state} -> {to_state}. "
                f"This transition is explicitly blocked for safety."
            )
        
        allowed = cls.ALLOWED_TRANSITIONS.get(from_state, set())
        if to_state not in allowed:
            raise ValueError(
                f"Transition not allowed: {from_state} -> {to_state}. "
                f"Allowed transitions from {from_state}: {sorted(allowed)}"
            )
    
    @classmethod
    def get_allowed_next_states(cls, state: str) -> List[str]:
        """Get list of allowed next states from a given state"""
        if not cls.is_valid_state(state):
            return []
        
        return sorted(cls.ALLOWED_TRANSITIONS.get(state, set()))
    
    @classmethod
    def is_terminal_state(cls, state: str) -> bool:
        """Check if a state is terminal"""
        return state in cls.TERMINAL_STATES
    
    @classmethod
    def get_all_states(cls) -> List[str]:
        """Get all valid states"""
        return cls.STATES.copy()
    
    @classmethod
    def get_terminal_states(cls) -> List[str]:
        """Get all terminal states"""
        return sorted(cls.TERMINAL_STATES)
