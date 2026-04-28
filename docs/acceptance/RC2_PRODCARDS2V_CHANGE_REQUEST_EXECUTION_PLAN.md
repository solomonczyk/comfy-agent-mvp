# RC2-PRODCARDS2V — Change Request Execution Plan, No Execution

## Acceptance Criteria

Creates concrete execution plans for unresolved change request work orders before any workflow change, reference rebuild, completion submission, apply, or retry generation is allowed.

## Implementation

### Module Created
- `app/production_cards/change_request_execution_plan.py`

### Functions Implemented
- `create_change_request_execution_plan(project_root)` - Main execution plan creation entry point
- `validate_change_request_execution_plan(project_root)` - Validates execution plans exist and are correctly structured
- `create_workflow_td_execution_plan(work_order, completion_template)` - Creates Workflow TD execution plan
- `create_character_director_execution_plan(work_order, completion_template)` - Creates Character Director execution plan
- `load_change_request_work_orders(project_root)` - Loads work orders
- `load_completion_contracts(project_root)` - Loads completion contracts
- `load_artifact_index(project_root)` - Loads artifact index to check current state
- `load_episode_ledger(project_root)` - Loads episode ledger to append events
- `create_execution_plan_summary(...)` - Creates markdown summary
- `append_episode_ledger_event(...)` - Appends event to episode ledger
- `update_artifact_index_for_execution_plan(...)` - Updates artifact index with passive pointer

### CLI Commands Added
- `python -m app create-change-request-execution-plan --project-root "<path>" --json`
- `python -m app validate-change-request-execution-plan --project-root "<path>" --json`

### Output Folder Created
- `data/rc2_multishot1_ep01/output/control/change_request_execution_plan/`

## Files Created

### 1. workflow_td_identity_workflow_execution_plan.json
```json
{
  "plan_type": "workflow_td_change_request_execution_plan",
  "role": "Workflow TD / ComfyUI Technical Director",
  "source_work_order": "workflow_td_identity_workflow_change_order.json",
  "source_completion_template": "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json",
  "blocked_shot": "shot01",
  "reason": "identity_qa_failed",
  "execution_status": "planned",
  "execution_performed": false,
  "required_generation_mode": "gorynych_identity",
  "legacy_reference_locked_allowed_for_production": false,
  "planned_steps": [
    "audit_current_identity_workflow_strategy",
    "verify_required_nodes",
    "verify_required_models",
    "define_updated_workflow_strategy",
    "define_preflight_requirements",
    "define_output_collection_contract"
  ],
  "required_outputs_before_completion": [
    "updated_workflow_strategy",
    "workflow_audit",
    "required_nodes",
    "required_models",
    "preflight_result",
    "output_collection_contract"
  ],
  "completion_submission_allowed": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true
}
```

### 2. character_director_reference_rebuild_execution_plan.json
```json
{
  "plan_type": "character_director_reference_rebuild_execution_plan",
  "role": "Character Director",
  "source_work_order": "character_director_reference_rebuild_order.json",
  "source_completion_template": "character_director_reference_rebuild.COMPLETION_TEMPLATE.json",
  "blocked_shot": "shot01",
  "reason": "identity_qa_failed",
  "execution_status": "planned",
  "execution_performed": false,
  "planned_steps": [
    "review_identity_failure_evidence",
    "review_current_character_identity_rules",
    "define_updated_reference_strategy",
    "define_identity_acceptance_criteria",
    "write_reference_rebuild_notes"
  ],
  "required_outputs_before_completion": [
    "updated_character_identity_rules",
    "updated_reference_strategy",
    "identity_acceptance_criteria",
    "reference_rebuild_notes"
  ],
  "completion_submission_allowed": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true
}
```

### 3. CHANGE_REQUEST_EXECUTION_PLAN.md
Explains:
- Which work orders are still unresolved
- Planned steps for Workflow TD
- Planned steps for Character Director
- Required outputs before completion can be submitted
- Why execution_performed remains false
- Why retry remains blocked
- Why no generation has been authorized

## Expected create-change-request-execution-plan JSON
```json
{
  "status": "completed",
  "execution_plans_created": 2,
  "execution_performed": false,
  "completion_submission_allowed": false,
  "ready_for_resubmission": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true
}
```

## Expected validate-change-request-execution-plan JSON
```json
{
  "status": "valid",
  "execution_plans_found": 2,
  "execution_performed": false,
  "completion_submission_allowed": false,
  "ready_for_resubmission": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true,
  "validation_errors": []
}
```

## Artifact Index Update (Passive Section Only)
```json
{
  "change_request_execution_plan": {
    "status": "created",
    "execution_plans_created": 2,
    "execution_performed": false,
    "completion_submission_allowed": false,
    "ready_for_resubmission": false,
    "retry_gate_open": false,
    "production_accepted": false,
    "downstream_blocked": true
  }
}
```

## Episode Ledger Event
```json
{
  "event_type": "change_request_execution_plan_created",
  "execution_plans_created": 2,
  "execution_performed": false,
  "completion_submission_allowed": false,
  "ready_for_resubmission": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true,
  "comfyui_generation": false,
  "pipeline_action_rerun": false
}
```

## No Mutation Guarantees

The execution plan creation does NOT mutate:
- `role_decisions/`
- Submitted role decisions
- Submitted completions
- `completion_status=submitted`
- `execution_performed=true`
- `role_decision_apply`
- `retry_gate_open=true`
- `production_accepted=true`
- Final manifests
- Generation artifacts
- Generated references
- Workflow execution outputs

## Test Coverage

### Test File
- `tests/test_production_change_request_execution_plan.py`

### Tests Implemented (31 tests)
1. **Workflow TD Execution Plan Creation**
   - `test_creates_workflow_td_execution_plan`
   - `test_execution_status_planned`
   - `test_execution_performed_false`
   - `test_requires_gorynych_identity`
   - `test_rejects_legacy_reference_locked_production_path`
   - `test_includes_planned_steps`
   - `test_includes_required_outputs`
   - `test_completion_submission_allowed_false`
   - `test_retry_gate_open_false`
   - `test_production_accepted_false`
   - `test_downstream_blocked_true`

2. **Character Director Execution Plan Creation**
   - `test_creates_character_director_execution_plan`
   - `test_execution_status_planned`
   - `test_execution_performed_false`
   - `test_includes_planned_steps`
   - `test_includes_required_outputs`
   - `test_completion_submission_allowed_false`
   - `test_retry_gate_open_false`
   - `test_production_accepted_false`
   - `test_downstream_blocked_true`

3. **Execution Plan Creation**
   - `test_creates_execution_plans_based_on_work_orders`
   - `test_execution_plans_reference_completion_templates`
   - `test_creates_execution_plan_summary`

4. **No Mutation**
   - `test_plans_do_not_modify_role_decisions`
   - `test_plans_do_not_submit_completions`
   - `test_plans_do_not_open_retry_gate`
   - `test_plans_keep_production_accepted_false`
   - `test_plans_keep_downstream_blocked_true`

5. **Artifact Index and Episode Ledger**
   - `test_artifact_index_records_passive_execution_plan_section_only`
   - `test_episode_ledger_records_change_request_execution_plan_created`

6. **Validation**
   - `test_validates_execution_plan_structure`

## Verification Results

### py_compile
```
python -m py_compile app/cli.py app/production_cards/change_request_execution_plan.py app/production_cards/change_request_completion_validator.py app/production_cards/change_request_completion.py app/production_cards/change_request_work_orders.py app/production_cards/change_request_router.py app/production_cards/decision_change_requests.py app/production_cards/decision_submission_outcome.py app/production_cards/decision_submission_validator.py app/production_cards/decision_submission.py app/production_cards/decision_apply.py app/production_cards/decision_intake.py app/production_cards/approval_gate.py app/production_cards/role_decisions.py app/production_cards/work_orders.py app/production_cards/router.py app/production_cards/validator.py app/production_cards/materializer.py
```
**Result:** Exit code 0 - Success

### pytest
```
python -m pytest tests/test_production_card_schemas.py tests/test_production_card_validator.py tests/test_production_role_routing.py tests/test_production_card_materialization.py tests/test_production_work_orders.py tests/test_production_role_decisions.py tests/test_production_role_approval_gate.py tests/test_production_role_approval_fixtures.py tests/test_production_role_decision_intake.py tests/test_production_role_decision_apply.py tests/test_production_role_decision_apply_safety.py tests/test_production_state_repair.py tests/test_production_role_review_packets.py tests/test_production_role_decision_submission.py tests/test_production_role_decision_submission_validator.py tests/test_production_real_role_decision_drafts.py tests/test_production_submitted_decision_outcome.py tests/test_production_decision_change_requests.py tests/test_production_change_request_routing.py tests/test_production_change_request_work_orders.py tests/test_production_change_request_completion.py tests/test_production_change_request_completion_validator.py tests/test_production_change_request_execution_plan.py -q -s --tb=short
```
**Result:** 446 passed, 1760 warnings in 15.59s

### validate-submitted-change-request-completions
```json
{
  "status": "awaiting_completion_input",
  "submitted_completions_ready": false,
  "valid_completions": 0,
  "complete_completions": 0,
  "missing_or_incomplete_completions": [
    "workflow_change_completion",
    "reference_rebuild_completion"
  ],
  "rejection_reasons": [
    "workflow_td: completion_status_not_submitted: template",
    "character_director: completion_status_not_submitted: template"
  ],
  "ready_for_resubmission": false,
  "execution_performed": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true
}
```

### create-change-request-execution-plan
```json
{
  "status": "completed",
  "execution_plans_created": 2,
  "execution_performed": false,
  "completion_submission_allowed": false,
  "ready_for_resubmission": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true
}
```

### validate-change-request-execution-plan
```json
{
  "status": "valid",
  "execution_plans_found": 2,
  "execution_performed": false,
  "completion_submission_allowed": false,
  "ready_for_resubmission": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true,
  "validation_errors": []
}
```

### validate-role-approval-gate
```json
{
  "status": "blocked",
  "can_retry_generation": false,
  "downstream_blocked": true,
  "production_accepted": false,
  "required_approvals": [
    "character_identity_approval",
    "workflow_fit_approval"
  ],
  "missing_approvals": [
    "character_identity_approval",
    "workflow_fit_approval"
  ],
  "blocking_roles": [
    "Character Director",
    "Workflow TD / ComfyUI Technical Director"
  ],
  "next_allowed_action": null
}
```

## Execution Plan File Paths
- `data/rc2_multishot1_ep01/output/control/change_request_execution_plan/workflow_td_identity_workflow_execution_plan.json`
- `data/rc2_multishot1_ep01/output/control/change_request_execution_plan/character_director_reference_rebuild_execution_plan.json`
- `data/rc2_multishot1_ep01/output/control/change_request_execution_plan/CHANGE_REQUEST_EXECUTION_PLAN.md`

## Proof Summary

1. ✅ Execution plans created based on change request work orders
2. ✅ Execution plans reference completion templates
3. ✅ Workflow TD plan requires gorynych_identity
4. ✅ Workflow TD plan rejects legacy_reference_locked production path
5. ✅ Character Director plan requires reference strategy outputs
6. ✅ execution_status=planned
7. ✅ execution_performed=false
8. ✅ completion_submission_allowed=false
9. ✅ ready_for_resubmission=false
10. ✅ Plans do not modify role_decisions/
11. ✅ Plans do not submit completions
12. ✅ Plans do not open retry gate
13. ✅ Plans keep production_accepted=false
14. ✅ Plans keep downstream_blocked=true
15. ✅ artifact_index records passive execution plan section only
16. ✅ episode_ledger records change_request_execution_plan_created
17. ✅ No generation/downstream action executes
18. ✅ No core hardcode for Alya/Mir Erdan
19. ✅ No completion submission happened
20. ✅ No apply happened
21. ✅ No generation happened
22. ✅ No downstream action executed

## Status

**RC2-PRODCARDS2V is ACCEPTED**

Unresolved change request work orders have concrete execution plans, execution_status remains planned, execution_performed remains false, completion_submission_allowed remains false, retry gate remains closed, role_decisions remain pending, production_accepted remains false, downstream remains blocked, tests pass, tracked proof exists, and no completion/apply/generation/downstream action executes.
