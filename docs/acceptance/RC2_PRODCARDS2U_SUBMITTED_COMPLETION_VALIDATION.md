# RC2-PRODCARDS2U — Submitted Change Request Completion Validation, No Apply

## Acceptance Criteria

Validates submitted change request completion files before they are allowed to trigger resubmission of role decisions, without executing workflow changes, rebuilding references, applying decisions, or opening retry generation.

## Implementation

### Module Created
- `app/production_cards/change_request_completion_validator.py`

### Functions Implemented
- `validate_submitted_change_request_completions(project_root, completion_root=None)` - Main validation entry point
- `validate_workflow_td_completion_submission(completion, work_order)` - Validates Workflow TD completion
- `validate_character_director_completion_submission(completion, work_order)` - Validates Character Director completion
- `compare_completion_against_contract(completion, work_order)` - Compares completion against work order contract
- `load_submitted_completions(project_root, completion_root=None)` - Loads completion files
- `load_change_request_work_orders(project_root)` - Loads work orders for comparison

### CLI Command Added
- `python -m app validate-submitted-change-request-completions --project-root "<path>" --json`
- Optional: `--completion-root "<path>"` for fixture validation

## Validation Behavior

### For Blank Templates (Current State)
When completion files are templates (completion_status=template, selected_resolution=null):
```json
{
  "status": "awaiting_completion_input",
  "submitted_completions_ready": false,
  "valid_completions": 0,
  "missing_or_incomplete_completions": [
    "workflow_change_completion",
    "reference_rebuild_completion"
  ],
  "ready_for_resubmission": false,
  "execution_performed": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true
}
```

### For Completed Submitted Completions (Test Fixtures Only)
When both completions are valid and submitted (completion_status=submitted, selected_resolution set, required outputs provided):
```json
{
  "status": "valid",
  "submitted_completions_ready": true,
  "valid_completions": 2,
  "ready_for_resubmission": true,
  "would_allow_new_role_decision_drafts": true,
  "execution_performed": true,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true,
  "real_project_mutated": false
}
```

**Important:** Even valid completions do NOT open retry gate. They only allow future resubmission/draft decision layer.

## Unsafe Completion Rejection Criteria

Completions are rejected if:
- `completion_status != submitted`
- `selected_resolution is null`
- `selected_resolution not in allowed_resolutions`
- Required outputs are missing
- `production_accepted=true`
- `retry_gate_open=true`
- `apply_performed=true`
- Workflow TD: `legacy_reference_locked_allowed_for_production=true`
- Workflow TD: `current_required_generation_mode != gorynych_identity`
- `execution_performed=true` without required output evidence
- `source_work_order mismatch`
- `role mismatch`
- `blocked_shot mismatch`

## No Mutation Guarantees

The validator does NOT mutate:
- `role_decisions/`
- Submitted role decisions
- `role_decision_apply`
- Artifact index retry gate
- Episode final state
- `production_accepted`
- Final manifests
- Generation artifacts
- Generated references
- Workflow execution outputs

## Test Coverage

### Test File
- `tests/test_production_change_request_completion_validator.py`

### Tests Implemented
1. **Blank Completion Templates**
   - `test_blank_completion_templates_return_awaiting_completion_input`
   - `test_completion_status_template_is_incomplete`
   - `test_selected_resolution_null_is_incomplete`

2. **Submitted Completion Validation**
   - `test_workflow_td_submitted_completion_validates_in_temp_fixture`
   - `test_character_director_submitted_completion_validates_in_temp_fixture`
   - `test_both_completed_submissions_return_submitted_completions_ready_true`
   - `test_valid_completions_do_not_open_retry_gate`

3. **Unsafe Completion Rejection**
   - `test_selected_resolution_outside_allowed_resolutions_is_rejected`
   - `test_missing_required_outputs_are_rejected`
   - `test_production_accepted_true_is_rejected`
   - `test_retry_gate_open_true_is_rejected`
   - `test_apply_performed_true_is_rejected`
   - `test_legacy_reference_locked_workflow_is_rejected`
   - `test_non_gorynych_mode_is_rejected`

4. **No Mutation**
   - `test_validation_does_not_mutate_project`
   - `test_role_decisions_remain_pending`
   - `test_retry_gate_remains_closed`
   - `test_production_accepted_remains_false`
   - `test_downstream_blocked_remains_true`

5. **Contract Comparison**
   - `test_compare_completion_against_contract_compliant`
   - `test_compare_completion_against_contract_non_compliant`

## Verification Results

### py_compile
```
python -m py_compile app/cli.py app/production_cards/change_request_completion_validator.py ...
```
**Result:** Exit code 0 - Success

### pytest
```
python -m pytest tests/test_production_change_request_completion_validator.py ...
```
**Result:** 415 passed, 1707 warnings in 16.37s

### validate-change-request-completion-contracts
```json
{
  "status": "valid",
  "completion_templates_found": 2,
  "submitted_completions_found": 0,
  "execution_performed": false,
  "ready_for_resubmission": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true,
  "validation_errors": []
}
```

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

## Proof Summary

1. ✅ Blank templates return `awaiting_completion_input`
2. ✅ `submitted_completions_ready=false` for templates
3. ✅ `ready_for_resubmission=false` for templates
4. ✅ Temp completed submissions validate only in tests
5. ✅ Valid completions do not open retry gate
6. ✅ Unsafe completions are rejected
7. ✅ Role_decisions remain pending
8. ✅ `retry_gate_open=false`
9. ✅ `production_accepted=false`
10. ✅ `downstream_blocked=true`
11. ✅ No apply happened (read-only validation)
12. ✅ No generation happened (read-only validation)
13. ✅ No downstream action executed (read-only validation)

## Status

**RC2-PRODCARDS2U is ACCEPTED**

Submitted change request completions are validated before any resubmission/apply flow, blank templates remain awaiting_completion_input, unsafe completions are rejected, completed submissions are proven only in tests/temp fixtures, retry gate remains closed, role_decisions remain pending, production_accepted remains false, downstream remains blocked, tests pass, tracked proof exists, and no apply/generation/downstream action executes.
