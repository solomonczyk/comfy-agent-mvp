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
        "retry_correction_required",
        "retry_plan_review_required",
        "operator_retry_authorization_required",
        "controlled_asset_resolution_review_required",
        "assembly_required",
        "final_qc_required",
        "final_operator_acceptance",
        "completed",
        "blocked_manual_review"
    ]
    
    # Terminal states
    TERMINAL_STATES = {
        "completed",
        "blocked_manual_review"
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
            "controlled_asset_resolution_review_required"
        },
        "operator_generation_authorization_required": {
            "generate_assets"
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
            "retry_correction_required"
        },
        "operator_visual_review": {
            "assembly_required",
            "retry_correction_required",
            "blocked_manual_review"
        },
        "retry_correction_required": {
            "retry_plan_review_required"
        },
        "retry_plan_review_required": {
            "operator_retry_authorization_required"
        },
        "operator_retry_authorization_required": {
            "generation_authorization_required"
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
