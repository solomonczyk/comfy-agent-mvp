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
        "brief_operator_review_required",
        "planning_operator_review_required",
        "generation_preflight_operator_review_required",
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
        "v8_operator_visual_review_required",
        "v9_generation_authorization_required",
        "v9_generation_runtime_blocked",
        "v9_generation_runtime_recovery_required",
        "v9_operator_visual_review_required",
        "v10_generation_authorization_required",
        "v10_generation_runtime_blocked",
        "v10_generation_runtime_recovery_required",
        "v10_operator_visual_review_required",
        # V11 photoreal character QA recovery states
        "v11_correction_plan_required",
        "v11_corrective_package_build_required",
        "v11_generation_authorization_required",
        "v11_generate_assets",
        "v11_result_review_required",
        "v11_visual_qa_preflight_required",
        "v11_visual_qa_required",
        "v11_operator_visual_review_required",
        # V12 photoreal character QA recovery states
        "v12_correction_plan_required",
        "v12_corrective_package_build_required",
        "v12_generation_authorization_required",
        "v12_generate_assets",
        "v12_result_review_required",
        "v12_visual_qa_preflight_required",
        "v12_visual_qa_required",
        "v12_operator_visual_review_required",
        # V13 photoreal character QA recovery states
        "v13_correction_plan_required",
        "v13_corrective_package_build_required",
        "v13_generation_authorization_required",
        "v13_generate_assets",
        "v13_result_review_required",
        "v13_visual_qa_preflight_required",
        "v13_visual_qa_required",
        "v13_operator_visual_review_required",
        # Terminal states for QA recovery
        "visual_candidate_accepted_for_pipeline",
        "qa_recovery_blocked_after_max_candidates",

        # RC-COMBINE-V2-102001-106000: Controlled generation asset review states
        "generation_result_review_required",

        # RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001: Operator visual decision routing
        "visual_asset_operator_accepted",
        "visual_correction_required",
        "visual_review_needs_fix",
    ]
    
    # Terminal states
    TERMINAL_STATES = {
        "completed",
        "blocked_manual_review",
        "blocked_generation_route_aborted",
        "visual_candidate_accepted_for_pipeline",
        "qa_recovery_blocked_after_max_candidates"
    }
    
    # Allowed transitions
    # Format: from_state -> [to_state, ...]
    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        "initial": {
            "brief_intake_required"
        },
        "brief_intake_required": {
            "brief_operator_review_required",
            "route_classification_required"
        },
        "brief_operator_review_required": {
            "route_classification_required",
            "brief_intake_required",
            "planning_operator_review_required",
        },
        "planning_operator_review_required": {
            "planning_operator_review_required",
            "brief_intake_required",
            "generation_preflight_operator_review_required",
        },
        "generation_preflight_operator_review_required": {
            "generation_preflight_operator_review_required",
            "planning_operator_review_required",
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

        # RC-COMBINE-V2-102001-106000: generation_result_review_required transitions
        "generation_result_review_required": {
            "operator_visual_review_required",  # After Visual QA technical package
            "generation_result_review_required",  # Self-loop: stays here pending QA
            "blocked_manual_review",  # If QA reveals fatal issues
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
            "v8_quality_locked_generation_authorization_required",  # V7 rejected -> V8 quality lock
            # RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001: Operator visual decision routing
            "visual_asset_operator_accepted",  # Accepted branch
            "visual_correction_required",  # Rejected branch
            "visual_review_needs_fix",  # Needs-fix branch
        },
        "v8_operator_visual_review_required": {
            "v8_operator_visual_review_required",  # Self-loop: halted pending operator
            "assembly_preflight_required",  # Approved - proceed to assembly
            "blocked_manual_review",
        },
        "v9_generation_authorization_required": {
            "v9_generation_authorization_required",  # Self-loop: halted pending operator authorization
            "v9_operator_visual_review_required",  # Success path after generation
            "v9_generation_runtime_blocked",  # Runtime failure
            "blocked_manual_review",
        },
        "v9_generation_runtime_blocked": {
            "v9_generation_runtime_blocked",  # Self-loop: blocked until ComfyUI available
            "v9_generation_runtime_recovery_required",  # Can transition to recovery
            "v9_generation_authorization_required",  # Can restart authorization
            "blocked_manual_review",
        },
        "v9_generation_runtime_recovery_required": {
            "v9_generation_runtime_recovery_required",  # Self-loop: halted pending recovery
            "v9_generation_authorization_required",  # Can go back to generation authorization
            "blocked_manual_review",
        },
        "v9_operator_visual_review_required": {
            "v9_operator_visual_review_required",  # Self-loop: halted pending operator
            "assembly_preflight_required",  # Approved - proceed to assembly
            "blocked_manual_review",
        },
        "v10_generation_authorization_required": {
            "v10_generation_authorization_required",  # Self-loop: halted pending operator authorization
            "v10_operator_visual_review_required",  # Success path after generation
            "v10_generation_runtime_blocked",  # Runtime failure
            "blocked_manual_review",
        },
        "v10_generation_runtime_blocked": {
            "v10_generation_runtime_blocked",  # Self-loop: blocked until ComfyUI available
            "v10_generation_runtime_recovery_required",  # Can transition to recovery
            "v10_generation_authorization_required",  # Can restart authorization
            "blocked_manual_review",
        },
        "v10_generation_runtime_recovery_required": {
            "v10_generation_runtime_recovery_required",  # Self-loop: halted pending recovery
            "v10_generation_authorization_required",  # Can go back to generation authorization
            "blocked_manual_review",
        },
        "v10_operator_visual_review_required": {
            "v10_operator_visual_review_required",  # Self-loop: halted pending operator
            "assembly_preflight_required",  # Approved - proceed to assembly
            "blocked_manual_review",
            "v11_correction_plan_required",  # V10 visual rejection -> V11 recovery
        },
        # V11 photoreal character QA recovery loop states
        "v11_correction_plan_required": {
            "v11_corrective_package_build_required"
        },
        "v11_corrective_package_build_required": {
            "v11_generation_authorization_required"
        },
        "v11_generation_authorization_required": {
            "v11_generation_authorization_required",  # Self-loop: halted pending operator
            "v11_generate_assets",  # Authorized -> proceed to generation
            "blocked_manual_review"
        },
        "v11_generate_assets": {
            "v11_result_review_required"
        },
        "v11_result_review_required": {
            "v11_visual_qa_preflight_required",  # Success: assets collected
            "v11_correction_plan_required",  # Failure: retry within loop
            "blocked_manual_review"  # Unrecoverable failure
        },
        "v11_visual_qa_preflight_required": {
            "v11_visual_qa_required"
        },
        "v11_visual_qa_required": {
            "v11_operator_visual_review_required"
        },
        "v11_operator_visual_review_required": {
            "v11_operator_visual_review_required",  # Self-loop: pending operator decision
            "v11_correction_plan_required",  # Rejected: loop for next candidate (if candidates remain)
            "visual_candidate_accepted_for_pipeline",  # Accepted: pipeline success
            "qa_recovery_blocked_after_max_candidates",  # Rejected max candidates -> blocker
            "blocked_manual_review"
        },
        # V12 photoreal character QA recovery loop states
        "v12_correction_plan_required": {
            "v12_corrective_package_build_required"
        },
        "v12_corrective_package_build_required": {
            "v12_generation_authorization_required"
        },
        "v12_generation_authorization_required": {
            "v12_generation_authorization_required",  # Self-loop: halted pending operator
            "v12_generate_assets",  # Authorized -> proceed to generation
            "blocked_manual_review"
        },
        "v12_generate_assets": {
            "v12_result_review_required"
        },
        "v12_result_review_required": {
            "v12_visual_qa_preflight_required",  # Success: assets collected
            "v12_correction_plan_required",  # Failure: retry within loop
            "blocked_manual_review"
        },
        "v12_visual_qa_preflight_required": {
            "v12_visual_qa_required"
        },
        "v12_visual_qa_required": {
            "v12_operator_visual_review_required"
        },
        "v12_operator_visual_review_required": {
            "v12_operator_visual_review_required",  # Self-loop: pending operator decision
            "v12_correction_plan_required",  # Rejected: loop for next candidate (if remain)
            "visual_candidate_accepted_for_pipeline",  # Accepted: pipeline success
            "qa_recovery_blocked_after_max_candidates",  # Rejected max candidates -> blocker
            "blocked_manual_review"
        },
        # V13 photoreal character QA recovery loop states
        "v13_correction_plan_required": {
            "v13_corrective_package_build_required"
        },
        "v13_corrective_package_build_required": {
            "v13_generation_authorization_required"
        },
        "v13_generation_authorization_required": {
            "v13_generation_authorization_required",  # Self-loop: halted pending operator
            "v13_generate_assets",  # Authorized -> proceed to generation
            "blocked_manual_review"
        },
        "v13_generate_assets": {
            "v13_result_review_required"
        },
        "v13_result_review_required": {
            "v13_visual_qa_preflight_required",  # Success: assets collected
            "v13_correction_plan_required",  # Failure: retry within loop
            "blocked_manual_review"
        },
        "v13_visual_qa_preflight_required": {
            "v13_visual_qa_required"
        },
        "v13_visual_qa_required": {
            "v13_operator_visual_review_required"
        },
        "v13_operator_visual_review_required": {
            "v13_operator_visual_review_required",  # Self-loop: pending operator decision
            "v13_correction_plan_required",  # Rejected: loop for next candidate
            "visual_candidate_accepted_for_pipeline",  # Accepted: pipeline success
            "qa_recovery_blocked_after_max_candidates",  # Rejected max candidates -> blocker
            "blocked_manual_review"
        },
        # Terminal states
        "visual_candidate_accepted_for_pipeline": set(),
        "qa_recovery_blocked_after_max_candidates": set(),

        # RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001: new routing states
        "visual_asset_operator_accepted": {
            "timeline_to_preview_package_required",
            "blocked_manual_review",
        },
        "visual_correction_required": {
            "qa_to_correction_package_required",
            "blocked_manual_review",
        },
        "visual_review_needs_fix": {
            "visual_issue_triage_required",
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
        ("brief_intake_required", "generate_assets"),
        ("brief_operator_review_required", "generate_assets"),
        ("brief_operator_review_required", "real_generate_assets"),
        ("brief_operator_review_required", "assembly_required"),
        ("brief_operator_review_required", "assembly_preflight_required"),
        ("brief_operator_review_required", "visual_qa_required"),
        ("brief_operator_review_required", "real_visual_qa_required"),
        ("brief_operator_review_required", "completed"),
        ("brief_operator_review_required", "production_accepted"),
        # Planning operator review: cannot skip to generation, assembly, QA, or downstream
        ("planning_operator_review_required", "generate_assets"),
        ("planning_operator_review_required", "real_generate_assets"),
        ("planning_operator_review_required", "assembly_required"),
        ("planning_operator_review_required", "assembly_preflight_required"),
        ("planning_operator_review_required", "visual_qa_required"),
        ("planning_operator_review_required", "real_visual_qa_required"),
        ("planning_operator_review_required", "completed"),
        ("planning_operator_review_required", "production_accepted"),
        ("planning_operator_review_required", "final_qc_required"),
        ("planning_operator_review_required", "final_operator_acceptance"),

        # Generation preflight operator review: cannot skip to generation, assembly, QA, or downstream
        ("generation_preflight_operator_review_required", "generate_assets"),
        ("generation_preflight_operator_review_required", "real_generate_assets"),
        ("generation_preflight_operator_review_required", "assembly_required"),
        ("generation_preflight_operator_review_required", "assembly_preflight_required"),
        ("generation_preflight_operator_review_required", "visual_qa_required"),
        ("generation_preflight_operator_review_required", "real_visual_qa_required"),
        ("generation_preflight_operator_review_required", "completed"),
        ("generation_preflight_operator_review_required", "production_accepted"),
        ("generation_preflight_operator_review_required", "final_qc_required"),
        ("generation_preflight_operator_review_required", "final_operator_acceptance"),

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

        # v9 states: generation authorization required cannot skip to runtime or downstream
        ("v9_generation_authorization_required", "generate_assets"),
        ("v9_generation_authorization_required", "real_generate_assets"),
        ("v9_generation_authorization_required", "visual_qa_required"),
        ("v9_generation_authorization_required", "assembly_required"),
        ("v9_generation_authorization_required", "assembly_preflight_required"),
        ("v9_generation_authorization_required", "completed"),
        ("v9_generation_authorization_required", "production_accepted"),

        # v9 runtime blocked: cannot skip to visual review, assembly, downstream, or production
        ("v9_generation_runtime_blocked", "v9_operator_visual_review_required"),
        ("v9_generation_runtime_blocked", "visual_qa_required"),
        ("v9_generation_runtime_blocked", "assembly_required"),
        ("v9_generation_runtime_blocked", "assembly_preflight_required"),
        ("v9_generation_runtime_blocked", "completed"),
        ("v9_generation_runtime_blocked", "production_accepted"),

        # v9 recovery: cannot skip to visual review or downstream
        ("v9_generation_runtime_recovery_required", "v9_operator_visual_review_required"),
        ("v9_generation_runtime_recovery_required", "visual_qa_required"),
        ("v9_generation_runtime_recovery_required", "assembly_required"),
        ("v9_generation_runtime_recovery_required", "assembly_preflight_required"),
        ("v9_generation_runtime_recovery_required", "completed"),
        ("v9_generation_runtime_recovery_required", "production_accepted"),

        # v9 operator visual review: cannot skip to downstream, final, or production
        ("v9_operator_visual_review_required", "completed"),
        ("v9_operator_visual_review_required", "production_accepted"),
        ("v9_operator_visual_review_required", "final_qc_required"),
        ("v9_operator_visual_review_required", "final_operator_acceptance"),

        # v10 states: generation authorization required cannot skip to runtime or downstream
        ("v10_generation_authorization_required", "generate_assets"),
        ("v10_generation_authorization_required", "real_generate_assets"),
        ("v10_generation_authorization_required", "visual_qa_required"),
        ("v10_generation_authorization_required", "assembly_required"),
        ("v10_generation_authorization_required", "assembly_preflight_required"),
        ("v10_generation_authorization_required", "completed"),
        ("v10_generation_authorization_required", "production_accepted"),

        # v10 runtime blocked: cannot skip to visual review, assembly, downstream, or production
        ("v10_generation_runtime_blocked", "v10_operator_visual_review_required"),
        ("v10_generation_runtime_blocked", "visual_qa_required"),
        ("v10_generation_runtime_blocked", "assembly_required"),
        ("v10_generation_runtime_blocked", "assembly_preflight_required"),
        ("v10_generation_runtime_blocked", "completed"),
        ("v10_generation_runtime_blocked", "production_accepted"),

        # v10 recovery: cannot skip to visual review or downstream
        ("v10_generation_runtime_recovery_required", "v10_operator_visual_review_required"),
        ("v10_generation_runtime_recovery_required", "visual_qa_required"),
        ("v10_generation_runtime_recovery_required", "assembly_required"),
        ("v10_generation_runtime_recovery_required", "assembly_preflight_required"),
        ("v10_generation_runtime_recovery_required", "completed"),
        ("v10_generation_runtime_recovery_required", "production_accepted"),

        # v10 operator visual review: cannot skip to downstream, final, or production
        ("v10_operator_visual_review_required", "completed"),
        ("v10_operator_visual_review_required", "production_accepted"),
        ("v10_operator_visual_review_required", "final_qc_required"),
        ("v10_operator_visual_review_required", "final_operator_acceptance"),

        # v11 states: generation authorization cannot skip to downstream
        ("v11_generation_authorization_required", "generate_assets"),
        ("v11_generation_authorization_required", "real_generate_assets"),
        ("v11_generation_authorization_required", "visual_qa_required"),
        ("v11_generation_authorization_required", "assembly_required"),
        ("v11_generation_authorization_required", "assembly_preflight_required"),
        ("v11_generation_authorization_required", "completed"),
        ("v11_generation_authorization_required", "production_accepted"),

        # v11 generate_assets: cannot skip to downstream
        ("v11_generate_assets", "assembly_required"),
        ("v11_generate_assets", "assembly_preflight_required"),
        ("v11_generate_assets", "completed"),
        ("v11_generate_assets", "production_accepted"),
        ("v11_generate_assets", "visual_qa_required"),
        ("v11_generate_assets", "real_visual_qa_required"),
        ("v11_generate_assets", "generate_assets"),
        ("v11_generate_assets", "real_generate_assets"),

        # v11 result review: cannot skip to downstream
        ("v11_result_review_required", "assembly_required"),
        ("v11_result_review_required", "completed"),
        ("v11_result_review_required", "production_accepted"),

        # v11 operator visual review: cannot skip to downstream
        ("v11_operator_visual_review_required", "completed"),
        ("v11_operator_visual_review_required", "production_accepted"),
        ("v11_operator_visual_review_required", "final_qc_required"),
        ("v11_operator_visual_review_required", "final_operator_acceptance"),
        ("v11_operator_visual_review_required", "assembly_required"),
        ("v11_operator_visual_review_required", "assembly_preflight_required"),

        # v12 states: generation authorization cannot skip to downstream
        ("v12_generation_authorization_required", "generate_assets"),
        ("v12_generation_authorization_required", "real_generate_assets"),
        ("v12_generation_authorization_required", "visual_qa_required"),
        ("v12_generation_authorization_required", "assembly_required"),
        ("v12_generation_authorization_required", "assembly_preflight_required"),
        ("v12_generation_authorization_required", "completed"),
        ("v12_generation_authorization_required", "production_accepted"),

        # v12 generate_assets: cannot skip to downstream
        ("v12_generate_assets", "assembly_required"),
        ("v12_generate_assets", "assembly_preflight_required"),
        ("v12_generate_assets", "completed"),
        ("v12_generate_assets", "production_accepted"),
        ("v12_generate_assets", "visual_qa_required"),
        ("v12_generate_assets", "real_visual_qa_required"),
        ("v12_generate_assets", "generate_assets"),
        ("v12_generate_assets", "real_generate_assets"),

        # v12 result review: cannot skip to downstream
        ("v12_result_review_required", "assembly_required"),
        ("v12_result_review_required", "completed"),
        ("v12_result_review_required", "production_accepted"),

        # v12 operator visual review: cannot skip to downstream
        ("v12_operator_visual_review_required", "completed"),
        ("v12_operator_visual_review_required", "production_accepted"),
        ("v12_operator_visual_review_required", "final_qc_required"),
        ("v12_operator_visual_review_required", "final_operator_acceptance"),
        ("v12_operator_visual_review_required", "assembly_required"),
        ("v12_operator_visual_review_required", "assembly_preflight_required"),

        # v13 states: generation authorization cannot skip to downstream
        ("v13_generation_authorization_required", "generate_assets"),
        ("v13_generation_authorization_required", "real_generate_assets"),
        ("v13_generation_authorization_required", "visual_qa_required"),
        ("v13_generation_authorization_required", "assembly_required"),
        ("v13_generation_authorization_required", "assembly_preflight_required"),
        ("v13_generation_authorization_required", "completed"),
        ("v13_generation_authorization_required", "production_accepted"),

        # v13 generate_assets: cannot skip to downstream
        ("v13_generate_assets", "assembly_required"),
        ("v13_generate_assets", "assembly_preflight_required"),
        ("v13_generate_assets", "completed"),
        ("v13_generate_assets", "production_accepted"),
        ("v13_generate_assets", "visual_qa_required"),
        ("v13_generate_assets", "real_visual_qa_required"),
        ("v13_generate_assets", "generate_assets"),
        ("v13_generate_assets", "real_generate_assets"),

        # v13 result review: cannot skip to downstream
        ("v13_result_review_required", "assembly_required"),
        ("v13_result_review_required", "completed"),
        ("v13_result_review_required", "production_accepted"),

        # v13 operator visual review: cannot skip to downstream
        ("v13_operator_visual_review_required", "completed"),
        ("v13_operator_visual_review_required", "production_accepted"),
        ("v13_operator_visual_review_required", "final_qc_required"),
        ("v13_operator_visual_review_required", "final_operator_acceptance"),
        ("v13_operator_visual_review_required", "assembly_required"),
        ("v13_operator_visual_review_required", "assembly_preflight_required"),

        # RC-COMBINE-V2-102001-106000: generation_result_review_required forbidden transitions
        ("generation_result_review_required", "generate_assets"),
        ("generation_result_review_required", "real_generate_assets"),
        ("generation_result_review_required", "visual_qa_required"),
        ("generation_result_review_required", "assembly_required"),
        ("generation_result_review_required", "assembly_preflight_required"),
        ("generation_result_review_required", "completed"),
        ("generation_result_review_required", "production_accepted"),
        ("generation_result_review_required", "final_qc_required"),
        ("generation_result_review_required", "final_operator_acceptance"),
        ("generation_result_review_required", "visual_acceptance_executed"),
        ("generation_result_review_required", "corrective_retry_plan_required"),
        ("generation_result_review_required", "retry_correction_required"),

        # RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001: visual_asset_operator_accepted forbidden
        ("visual_asset_operator_accepted", "generate_assets"),
        ("visual_asset_operator_accepted", "real_generate_assets"),
        ("visual_asset_operator_accepted", "visual_qa_required"),
        ("visual_asset_operator_accepted", "completed"),
        ("visual_asset_operator_accepted", "production_accepted"),
        ("visual_asset_operator_accepted", "final_qc_required"),
        ("visual_asset_operator_accepted", "final_operator_acceptance"),
        ("visual_correction_required", "generate_assets"),
        ("visual_correction_required", "real_generate_assets"),
        ("visual_correction_required", "visual_qa_required"),
        ("visual_correction_required", "completed"),
        ("visual_correction_required", "production_accepted"),
        ("visual_correction_required", "assembly_required"),
        ("visual_correction_required", "assembly_preflight_required"),
        ("visual_review_needs_fix", "generate_assets"),
        ("visual_review_needs_fix", "real_generate_assets"),
        ("visual_review_needs_fix", "visual_qa_required"),
        ("visual_review_needs_fix", "completed"),
        ("visual_review_needs_fix", "production_accepted"),
        ("visual_review_needs_fix", "assembly_required"),
        ("visual_review_needs_fix", "assembly_preflight_required"),

        # Terminal QA states: no transitions to downstream
        ("visual_candidate_accepted_for_pipeline", "assembly_required"),
        ("visual_candidate_accepted_for_pipeline", "assembly_preflight_required"),
        ("visual_candidate_accepted_for_pipeline", "completed"),
        ("visual_candidate_accepted_for_pipeline", "production_accepted"),
        ("visual_candidate_accepted_for_pipeline", "final_qc_required"),
        ("visual_candidate_accepted_for_pipeline", "final_operator_acceptance"),
        ("qa_recovery_blocked_after_max_candidates", "assembly_required"),
        ("qa_recovery_blocked_after_max_candidates", "assembly_preflight_required"),
        ("qa_recovery_blocked_after_max_candidates", "completed"),
        ("qa_recovery_blocked_after_max_candidates", "production_accepted"),
        ("qa_recovery_blocked_after_max_candidates", "final_qc_required"),
        ("qa_recovery_blocked_after_max_candidates", "final_operator_acceptance"),
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
