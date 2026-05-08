"""Generation Gate Package — evaluate generation readiness and build gate artifacts.

RC-COMBINE-V2-86001-94000:
  - Validates Workflow-to-Assets artifacts
  - Evaluates generation readiness against asset blockers
  - Produces canonical generation gate decision
  - Builds READY-path or BLOCKED-path package
  - Updates artifact index and episode ledger
  - Transitions state to generation_operator_authorization_required
    or controlled_asset_acquisition_required
"""

from .generation_preflight_gate import (
    TASK_ID,
    PREVIOUS_LAYER,
    NEXT_LAYER,
    evaluate_generation_gate,
    build_generation_gate_package,
    validate_generation_gate_package,
)

__all__ = [
    "TASK_ID",
    "PREVIOUS_LAYER",
    "NEXT_LAYER",
    "evaluate_generation_gate",
    "build_generation_gate_package",
    "validate_generation_gate_package",
]
