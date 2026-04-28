# RC2-PRODCARDS2J — Reject Fixture Approvals for Real Project Apply

## Acceptance Summary

**Status:** ACCEPTED  
**Date:** 2026-04-28  
**Previous Accepted State:** RC2-PRODCARDS2I  

## Goal

Harden the role decision apply layer so safe fixture approvals can never be applied to the real project as real approvals.

## Proof Items

### 1. Real project apply attempt with fixture decisions → REJECTED

Command:
```
python -m app apply-role-decisions --project-root "data/rc2_multishot1_ep01" --decisions-root "data/fixtures/production_role_approvals/identity_retry_ready" --apply --json
```

Result:
```json
{
  "status": "rejected",
  "reason": "fixture_decisions_cannot_be_applied_to_real_project",
  "dry_run": false,
  "applied_decisions": 0,
  "can_retry_generation": false,
  "production_accepted": false,
  "downstream_unblocked_for": [],
  "backup_created": false,
  "real_project_mutated": false,
  "blocked_decision_files": [
    "character_director_identity_decision.json",
    "workflow_td_identity_workflow_decision.json"
  ],
  "validation_errors": [
    "Character Director: fixture_only=true cannot be applied to real project",
    "Workflow TD: fixture_only=true cannot be applied to real project"
  ],
  "missing_decisions": []
}
```

### 2. Proof applied_decisions = 0

`result["applied_decisions"]` is `0`.

### 3. Proof real_project_mutated = false

`result["real_project_mutated"]` is `false`.

### 4. Proof production_accepted = false

`result["production_accepted"]` is `false`.

### 5. Proof dry-run fixture path still works

Command:
```
python -m app apply-role-decisions --project-root "data/rc2_multishot1_ep01" --decisions-root "data/fixtures/production_role_approvals/identity_retry_ready" --dry-run --json
```

Result:
```json
{
  "status": "valid",
  "dry_run": true,
  "would_apply_decisions": 2,
  "would_allow_retry_generation": true,
  "next_allowed_action_if_applied": "retry_generate_frames",
  "production_accepted_after_apply": false,
  "real_project_mutated": false
}
```

### 6. Proof no generation happened

`result["can_retry_generation"]` is `false` after rejection. No `generate-frames` or `comfyui_generation` event is triggered.

### 7. Proof no downstream action executed

`result["downstream_unblocked_for"]` is empty `[]`. No `assemble_scene`, `qa_review`, `attach_audio`, or `render_episode` is triggered.

### 8. Real project state unchanged

The real project artifact_index.json, episode_ledger.json, and role_decisions directory remain unmodified before and after the rejected apply attempt.

## Decision Source Validation Rules

Real apply now requires decision metadata:
- `fixture_only`: false
- `decision_source`: "real_role_decision"
- `approved_by_role`: matches expected role
- `approved_for_project_id`: matches project root
- `approved_for_shot`: matches blocked shot
- `production_accepted`: must not be true inside decision file

## Files Modified

- `app/production_cards/decision_apply.py`
- `app/cli.py`
- `tests/test_production_role_decision_apply_safety.py`
- `docs/acceptance/RC2_PRODCARDS2J_REJECT_FIXTURE_REAL_APPLY.md`

## Test Coverage

- `test_real_project_apply_rejects_fixture_only_decisions`
- `test_rejection_does_not_mutate_real_project`
- `test_dry_run_still_accepts_fixture_approvals_for_contract_proof`
- `test_real_apply_rejects_missing_decision_source`
- `test_real_apply_rejects_wrong_decision_source`
- `test_real_apply_rejects_mismatched_approved_for_project_id`
- `test_real_apply_rejects_mismatched_approved_for_shot`
- `test_real_apply_rejects_production_accepted_true_in_decision_file`
- `test_temp_fixture_apply_tests_from_2i_still_pass`
- `test_no_core_hardcode_for_alya_mir_erdan`

## Explicit Confirmation

RC2-PRODCARDS2J is accepted only if fixture approvals can be used for dry-run contract validation but cannot be applied to the real project, rejected apply attempts mutate nothing, production_accepted remains false, tests pass, tracked proof exists, and no generation or downstream action executes.
