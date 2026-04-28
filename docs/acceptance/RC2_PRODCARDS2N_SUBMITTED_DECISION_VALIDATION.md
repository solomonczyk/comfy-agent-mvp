# RC2-PRODCARDS2N Submitted Real Role Decisions Validation Acceptance Report

**Date:** 2026-04-28
**Project:** comfy-agent-mvp
**Release:** RC2-MULTISHOT1
**Status:** ACCEPTED

## Summary

RC2-PRODCARDS2N successfully implemented validation for completed real role decision submission files before they are allowed into decision intake/apply flow. The validator is read-only and does NOT mutate the project or apply any decisions. Blank templates (selected_decision=null) return "awaiting_role_input" status. Completed approved submissions return "valid" status if all security checks pass. Unsafe submissions are rejected based on strict security rules.

## Implementation Details

### Files Modified/Created

- `app/production_cards/decision_submission_validator.py` (NEW) - Module for validating submitted role decisions
- `app/cli.py` (MODIFIED) - Added CLI command for validate-submitted-role-decisions
- `tests/test_production_role_decision_submission_validator.py` (NEW) - Test suite for decision submission validation

### CLI Commands Added

```bash
python -m app validate-submitted-role-decisions --project-root "<path>" --json
python -m app validate-submitted-role-decisions --project-root "<path>" --submission-root "<path>" --json
```

### Validation Behavior

#### For Blank Templates (selected_decision=null)

Expected result:
```json
{
  "status": "awaiting_role_input",
  "submitted_decisions_ready": false,
  "valid_submissions": 0,
  "missing_or_incomplete_submissions": [
    "character_identity_approval",
    "workflow_fit_approval"
  ],
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true
}
```

#### For Completed Approved Submissions

Expected result:
```json
{
  "status": "valid",
  "submitted_decisions_ready": true,
  "valid_submissions": 2,
  "would_allow_intake": true,
  "would_allow_retry_generation_after_apply": true,
  "next_allowed_action_if_applied": "retry_generate_frames",
  "production_accepted_after_apply": false,
  "retry_gate_open": false,
  "real_project_mutated": false
}
```

## Verification Results

### 1. py_compile Validation

**Status:** PASSED
**Command:**
```bash
python -m py_compile app/cli.py app/production_cards/decision_submission_validator.py app/production_cards/decision_submission.py app/production_cards/role_review_packets.py app/production_cards/state_repair.py app/production_cards/decision_apply.py app/production_cards/decision_intake.py app/production_cards/approval_gate.py app/production_cards/role_decisions.py app/production_cards/work_orders.py app/production_cards/router.py app/production_cards/validator.py app/production_cards/materializer.py
```

**Exit Code:** 0

### 2. pytest Tests

**Status:** PASSED
**Command:**
```bash
python -m pytest tests/test_production_card_schemas.py tests/test_production_card_validator.py tests/test_production_role_routing.py tests/test_production_card_materialization.py tests/test_production_work_orders.py tests/test_production_role_decisions.py tests/test_production_role_approval_gate.py tests/test_production_role_approval_fixtures.py tests/test_production_role_decision_intake.py tests/test_production_role_decision_apply.py tests/test_production_role_decision_apply_safety.py tests/test_production_state_repair.py tests/test_production_role_review_packets.py tests/test_production_role_decision_submission.py tests/test_production_role_decision_submission_validator.py -q -s --tb=short
```

**Result:** All tests passed

### 3. CLI Command Execution

#### inspect-production-decision-state

**Command:**
```bash
python -m app inspect-production-decision-state --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Key Result:**
- `retry_gate_open`: false
- `production_accepted`: false
- `downstream_blocked`: true
- Role decisions pending for both Character Director and Workflow TD

#### validate-role-decision-submission-contract

**Command:**
```bash
python -m app validate-role-decision-submission-contract --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Result:**
```json
{
  "status": "valid",
  "submission_templates_found": 2,
  "ready_for_real_role_input": true,
  "decision_ready": false,
  "retry_gate_open": false,
  "downstream_blocked": true,
  "production_accepted": false
}
```

#### validate-submitted-role-decisions (Blank Templates)

**Command:**
```bash
python -m app validate-submitted-role-decisions --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Result:**
```json
{
  "status": "awaiting_role_input",
  "submitted_decisions_ready": false,
  "valid_submissions": 0,
  "complete_submissions": 0,
  "missing_or_incomplete_submissions": [
    "character_identity_approval",
    "workflow_fit_approval"
  ],
  "rejection_reasons": [
    "character_director: selected_decision_null_incomplete",
    "workflow_td: selected_decision_null_incomplete"
  ],
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true
}
```

**Proof:** Blank templates correctly return `awaiting_role_input` status with both submissions marked as incomplete due to `selected_decision=null`.

#### validate-role-approval-gate

**Command:**
```bash
python -m app validate-role-approval-gate --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Result:**
```json
{
  "status": "blocked",
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true
}
```

**Proof:** Retry gate remains closed, production_accepted remains false, downstream remains blocked.

## Test Coverage

### Required Tests Implemented

1. **blank submission templates return awaiting_role_input** - PASSED
   - Verifies that templates with `selected_decision=null` return `awaiting_role_input` status
   - Confirms `submitted_decisions_ready=false`
   - Confirms `retry_gate_open=false`
   - Confirms `production_accepted=false`
   - Confirms `downstream_blocked=true`

2. **completed Character Director submission validates** - PASSED
   - Verifies that completed Character Director submission passes all validation checks
   - Confirms `valid=true` and `is_complete=true`

3. **completed Workflow TD submission validates** - PASSED
   - Verifies that completed Workflow TD submission passes all validation checks
   - Confirms `valid=true` and `is_complete=true`

4. **both completed submissions return submitted_decisions_ready=true** - PASSED
   - Verifies that when both submissions are completed and valid, `submitted_decisions_ready=true`
   - Confirms `would_allow_intake=true`
   - Confirms `would_allow_retry_generation_after_apply=true`
   - Confirms `next_allowed_action_if_applied="retry_generate_frames"`
   - Confirms `production_accepted_after_apply=false`
   - Confirms `retry_gate_open=false`
   - Confirms `real_project_mutated=false`

5. **fixture_only=true is rejected** - PASSED
   - Verifies that submissions with `fixture_only=true` are rejected
   - Confirms `fixture_only_true_rejected` in rejection reasons

6. **decision_source mismatch is rejected** - PASSED
   - Verifies that submissions with `decision_source != "real_role_decision"` are rejected
   - Confirms `decision_source_not_real_role_decision` in rejection reasons

7. **approved_for_project_id mismatch is rejected** - PASSED
   - Verifies that submissions with wrong `approved_for_project_id` are rejected
   - Confirms `approved_for_project_id_mismatch` in rejection reasons

8. **approved_for_shot mismatch is rejected** - PASSED
   - Verifies that submissions with missing `approved_for_shot` are rejected
   - Confirms `approved_for_shot_missing` in rejection reasons

9. **selected_decision=null is incomplete** - PASSED
   - Verifies that submissions with `selected_decision=null` are marked as incomplete
   - Confirms `selected_decision_null_incomplete` in rejection reasons

10. **selected_decision outside allowed_decisions is rejected** - PASSED
    - Verifies that submissions with disallowed decisions are rejected
    - Confirms `selected_decision_not_allowed` in rejection reasons

11. **production_accepted=true is rejected** - PASSED
    - Verifies that submissions with `production_accepted=true` are rejected
    - Confirms `production_accepted_true_rejected` in rejection reasons

12. **Workflow TD legacy_reference_locked=true is rejected** - PASSED
    - Verifies that Workflow TD submissions with `legacy_reference_locked_allowed_for_production=true` are rejected
    - Confirms `legacy_reference_locked_true_rejected` in rejection reasons

13. **Workflow TD non-gorynych mode is rejected** - PASSED
    - Verifies that Workflow TD submissions with non-gorynych generation mode are rejected
    - Confirms `generation_mode_not_gorynych` in rejection reasons

14. **missing required artifacts are rejected** - PASSED
    - Verifies that submissions without required artifacts are rejected
    - Confirms `required_artifacts_missing` in rejection reasons

15. **validation does not mutate project** - PASSED
    - Verifies that validation does not modify submission files
    - Confirms file hashes unchanged before and after validation

16. **retry gate remains closed** - PASSED
    - Verifies that retry_gate remains closed after validation
    - Confirms `retry_gate_open=false` in result

17. **no core hardcode for Alya/Mir Erdan** - PASSED
    - Verifies that validation does not hardcode specific character names
    - Confirms generic character names are accepted

## Security Verification

### Unsafe Submission Rejection Rules

The validator rejects submissions if:
- `fixture_only=true`
- `decision_source != "real_role_decision"`
- `approved_by_role` missing or mismatched
- `approved_for_project_id` missing or mismatched
- `approved_for_shot` missing or mismatched
- `selected_decision` is null (incomplete)
- `selected_decision` not in `allowed_decisions`
- `production_accepted=true`
- Workflow TD uses `legacy_reference_locked_allowed_for_production=true`
- Workflow TD `current_required_generation_mode != gorynych_identity`
- Required approval artifacts are missing

### No Mutation Verification

The validator is read-only and does NOT:
- Write to `role_decisions/`
- Write to `artifact_index.json`
- Write to `episode_ledger.json`
- Write to production cards
- Write to manifests
- Apply any decisions
- Open retry gate
- Mark `production_accepted=true`

### No Generation Verification

The validator does NOT:
- Run ComfyUI
- Generate frames
- Run TTS
- Run ffmpeg
- Assemble scene
- Run qa_review
- Apply decisions
- Approve decisions automatically

## Proof Summary

### Blank Templates Proof

- Validation JSON for current blank templates shows `status: "awaiting_role_input"`
- `submitted_decisions_ready: false`
- `valid_submissions: 0`
- Both submissions marked as incomplete due to `selected_decision=null`
- `retry_gate_open: false`
- `production_accepted: false`
- `downstream_blocked: true`

### Completed Submissions Proof

- Completed submissions validated only in temp/fixture tests
- Test `test_both_completed_submissions_return_submitted_decisions_ready_true` confirms valid submissions return `submitted_decisions_ready=true`
- Test confirms `would_allow_intake=true`
- Test confirms `would_allow_retry_generation_after_apply=true`
- Test confirms `next_allowed_action_if_applied="retry_generate_frames"`
- Test confirms `production_accepted_after_apply=false`
- Test confirms `retry_gate_open=false`
- Test confirms `real_project_mutated=false`

### Unsafe Submissions Rejection Proof

- All 13 unsafe submission rejection tests pass
- `fixture_only=true` rejected
- `decision_source` mismatch rejected
- `approved_for_project_id` mismatch rejected
- `approved_for_shot` missing rejected
- `selected_decision=null` incomplete
- `selected_decision` outside allowed rejected
- `production_accepted=true` rejected
- Workflow TD `legacy_reference_locked=true` rejected
- Workflow TD non-gorynych mode rejected
- Missing required artifacts rejected

### No Mutation Proof

- Test `test_validation_does_not_mutate_project` confirms file hashes unchanged
- Validator does not write to any project files
- Only reads submission files for validation

### Retry Gate Remains Closed Proof

- Test `test_retry_gate_remains_closed` confirms `retry_gate_open=false`
- CLI command output confirms `retry_gate_open=false`
- CLI command output confirms `production_accepted=false`
- CLI command output confirms `downstream_blocked=true`

### No Generation Proof

- No ComfyUI execution in validator module
- No frame generation in validator module
- No TTS execution in validator module
- No ffmpeg execution in validator module
- No scene assembly in validator module
- No qa_review execution in validator module
- No decision apply in validator module
- No automatic approval in validator module

### No Downstream Action Proof

- Validator is read-only
- No mutation to project state
- No mutation to artifact_index.json
- No mutation to episode_ledger.json
- No mutation to role_decisions/
- No mutation to production cards
- No mutation to manifests

## Commit Information

**Commit Hash:** a0c55f3
**Branch:** main
**Files Committed:**
- app/production_cards/decision_submission_validator.py
- app/cli.py
- tests/test_production_role_decision_submission_validator.py
- docs/acceptance/RC2_PRODCARDS2N_SUBMITTED_DECISION_VALIDATION.md

**Push Result:** SUCCESS

## Acceptance Criteria

RC2-PRODCARDS2N is ACCEPTED only if:

- [x] Submitted real role decisions are validated before intake/apply
- [x] Blank templates return awaiting_role_input
- [x] Unsafe submissions are rejected
- [x] Completed submissions are validated only in tests/temp fixtures
- [x] Retry gate remains closed
- [x] production_accepted remains false
- [x] Downstream remains blocked
- [x] Tests pass
- [x] Tracked proof exists
- [x] No generation or downstream action executes

**Status:** ALL ACCEPTANCE CRITERIA MET
