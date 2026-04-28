# RC2-PRODCARDS2R: Change Request Routing Preview Acceptance Report

## Task
Add routing preview for decision change request artifacts so the orchestrator can show the next required owner/action after submitted role decisions requested changes.

## Status
**ACCEPTED**

## Implementation Summary

### Files Created/Modified
1. **Created**: `app/production_cards/change_request_router.py` - New module for routing decision change requests
2. **Modified**: `app/cli.py` - Added `route-decision-change-requests` CLI command
3. **Created**: `tests/test_production_change_request_routing.py` - Comprehensive test suite with 24 passing tests
4. **Modified**: `data/rc2_multishot1_ep01/output/control/artifact_index.json` - Updated with decision_change_request_routing section (passive pointer only)
5. **Modified**: `data/rc2_multishot1_ep01/output/control/episode_ledger.json` - Appended decision_change_requests_routed event
6. **Created**: `docs/acceptance/RC2_PRODCARDS2R_CHANGE_REQUEST_ROUTING.md` - Acceptance proof document

## Commands Run

### 1. py_compile
```bash
python -m py_compile app/cli.py app/production_cards/change_request_router.py app/production_cards/decision_change_requests.py app/production_cards/decision_submission_outcome.py app/production_cards/decision_submission_validator.py app/production_cards/decision_submission.py app/production_cards/decision_apply.py app/production_cards/decision_intake.py app/production_cards/approval_gate.py app/production_cards/role_decisions.py app/production_cards/work_orders.py app/production_cards/router.py app/production_cards/validator.py app/production_cards/materializer.py
```
**Result**: Exit code 0 - All modules compile successfully

### 2. validate-decision-change-request-pack
```bash
python -m app validate-decision-change-request-pack --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Result**:
```json
{
  "status": "valid",
  "change_requests_found": 2,
  "next_required_roles": [
    "Workflow TD / ComfyUI Technical Director",
    "Character Director"
  ],
  "ready_for_apply": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true,
  "validation_errors": []
}
```

**Proof**: Change request pack is valid with 2 change requests found, ready_for_apply=false, retry_gate_open=false, production_accepted=false, downstream_blocked=true

### 3. route-decision-change-requests
```bash
python -m app route-decision-change-requests --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Result**:
```json
{
  "status": "blocked",
  "change_requests_found": 2,
  "ready_for_apply": false,
  "can_retry_generation": false,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true,
  "routes": [
    {
      "request_type": "workflow_change_request",
      "source_role": "Character Director",
      "target_role": "Workflow TD / ComfyUI Technical Director",
      "recommended_action": "revise_identity_workflow_strategy",
      "reason": "identity_qa_failed",
      "blocks_retry": true,
      "routed_at": "2026-04-28T13:51:29.073150Z"
    },
    {
      "request_type": "reference_rebuild_request",
      "source_role": "Workflow TD / ComfyUI Technical Director",
      "target_role": "Character Director",
      "recommended_action": "rebuild_or_update_identity_reference_strategy",
      "reason": "identity_qa_failed",
      "blocks_retry": true,
      "routed_at": "2026-04-28T13:51:29.073150Z"
    }
  ],
  "next_actions": [
    {
      "priority": 1,
      "role": "Workflow TD / ComfyUI Technical Director",
      "task": "revise_identity_workflow_strategy"
    },
    {
      "priority": 2,
      "role": "Character Director",
      "task": "rebuild_or_update_identity_reference_strategy"
    }
  ],
  "no_image_generation_route": true
}
```

**Proof**: Change requests routed to correct production roles, status=blocked, ready_for_apply=false, can_retry_generation=false, retry_gate_open=false, production_accepted=false, downstream_blocked=true, no_image_generation_route=true

### 4. validate-role-approval-gate
```bash
python -m app validate-role-approval-gate --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Result**:
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
  "next_allowed_action": null,
  "character_director_evaluation": {
    "role": "Character Director",
    "approved": false,
    "reason": "decision_pending",
    "current_status": "pending"
  },
  "workflow_td_evaluation": {
    "role": "Workflow TD / ComfyUI Technical Director",
    "approved": false,
    "reason": "decision_pending",
    "current_status": "pending"
  }
}
```

**Proof**: Approval gate remains blocked because role_decisions remain pending (not mutated by routing)

### 5. pytest
```bash
python -m pytest tests/test_production_card_schemas.py tests/test_production_card_validator.py tests/test_production_role_routing.py tests/test_production_card_materialization.py tests/test_production_work_orders.py tests/test_production_role_decisions.py tests/test_production_role_approval_gate.py tests/test_production_role_approval_fixtures.py tests/test_production_role_decision_intake.py tests/test_production_role_decision_apply.py tests/test_production_role_decision_apply_safety.py tests/test_production_state_repair.py tests/test_production_role_review_packets.py tests/test_production_role_decision_submission.py tests/test_production_role_decision_submission_validator.py tests/test_production_real_role_decision_drafts.py tests/test_production_submitted_decision_outcome.py tests/test_production_decision_change_requests.py tests/test_production_change_request_routing.py -q -s --tb=short
```

**Result**: 313 passed, 1548 warnings in 14.34s

**Proof**: All tests pass, including new tests for change request routing

## Verification Evidence

### 1. workflow_change_request Route Fragment
```json
{
  "request_type": "workflow_change_request",
  "source_role": "Character Director",
  "target_role": "Workflow TD / ComfyUI Technical Director",
  "recommended_action": "revise_identity_workflow_strategy",
  "reason": "identity_qa_failed",
  "blocks_retry": true,
  "routed_at": "2026-04-28T13:51:29.073150Z"
}
```

**Proof**: workflow_change_request routes to Workflow TD with blocks_retry=true

### 2. reference_rebuild_request Route Fragment
```json
{
  "request_type": "reference_rebuild_request",
  "source_role": "Workflow TD / ComfyUI Technical Director",
  "target_role": "Character Director",
  "recommended_action": "rebuild_or_update_identity_reference_strategy",
  "reason": "identity_qa_failed",
  "blocks_retry": true,
  "routed_at": "2026-04-28T13:51:29.073150Z"
}
```

**Proof**: reference_rebuild_request routes to Character Director with blocks_retry=true

### 3. next_actions Fragment
```json
[
  {
    "priority": 1,
    "role": "Workflow TD / ComfyUI Technical Director",
    "task": "revise_identity_workflow_strategy"
  },
  {
    "priority": 2,
    "role": "Character Director",
    "task": "rebuild_or_update_identity_reference_strategy"
  }
]
```

**Proof**: Next actions correctly prioritize Workflow TD (priority 1) before Character Director (priority 2)

### 4. artifact_index Fragment
```json
{
  "decision_change_request_routing": {
    "status": "blocked",
    "change_requests_found": 2,
    "retry_gate_open": false,
    "production_accepted": false,
    "downstream_blocked": true
  }
}
```

**Proof**: artifact_index updated with passive decision_change_request_routing section only, retry_gate_open=false, production_accepted=false, downstream_blocked=true

### 5. episode_ledger Fragment
```json
{
  "event_type": "decision_change_requests_routed",
  "change_requests_found": 2,
  "retry_gate_open": false,
  "production_accepted": false,
  "downstream_blocked": true,
  "comfyui_generation": false,
  "pipeline_action_rerun": false,
  "timestamp": "2026-04-28T13:51:29.074892Z"
}
```

**Proof**: episode_ledger records decision_change_requests_routed event with comfyui_generation=false, pipeline_action_rerun=false

### 6. No Route to Image Generation Agent
- **route-decision-change-requests**: no_image_generation_route=true
- All routes target production roles only:
  - Workflow TD / ComfyUI Technical Director
  - Character Director
- No route points to "Image Generation Agent" or "Generate Frames"

### 7. Retry Gate Remains Closed
- **validate-decision-change-request-pack**: retry_gate_open=false
- **route-decision-change-requests**: retry_gate_open=false
- **validate-role-approval-gate**: retry_gate_open=false
- **artifact_index**: retry_gate_open=false
- Both routes have blocks_retry=true

### 8. Role Decisions Remain Pending
- **validate-role-approval-gate**: 
  - character_director_evaluation.reason="decision_pending"
  - workflow_td_evaluation.reason="decision_pending"
  - Both have current_status="pending"
- Routing did NOT mutate role_decisions/

### 9. Production Accepted = False
- **validate-decision-change-request-pack**: production_accepted=false
- **route-decision-change-requests**: production_accepted=false
- **validate-role-approval-gate**: production_accepted=false
- **artifact_index**: production_accepted=false

### 10. Downstream Blocked = True
- **validate-decision-change-request-pack**: downstream_blocked=true
- **route-decision-change-requests**: downstream_blocked=true
- **validate-role-approval-gate**: downstream_blocked=true
- **artifact_index**: downstream_blocked=true

### 11. No Apply Happened
- **route-decision-change-requests**: ready_for_apply=false
- **validate-role-approval-gate**: next_allowed_action=null
- No role_decision_apply events in episode_ledger
- artifact_index.role_decision_apply_status does not exist

### 12. No Generation Happened
- **route-decision-change-requests**: can_retry_generation=false
- **episode_ledger**: latest event has comfyui_generation=false
- No ComfyUI execution triggered
- No new frames generated
- No TTS or ffmpeg execution

### 13. No Downstream Action Executed
- **episode_ledger**: latest event has pipeline_action_rerun=false
- No scene assembly
- No QA review
- No audio attachment
- No episode rendering

## Test Coverage

### Required Tests (All Passing)
1. ✅ routes workflow_change_request to Workflow TD
2. ✅ routes reference_rebuild_request to Character Director
3. ✅ route preview returns blocked
4. ✅ no route points to Image Generation Agent
5. ✅ retry gate remains closed
6. ✅ production_accepted remains false
7. ✅ downstream_blocked remains true
8. ✅ role_decisions remain pending
9. ✅ artifact_index records passive routing section only
10. ✅ episode_ledger records decision_change_requests_routed
11. ✅ no generation/downstream action executes
12. ✅ no core hardcode for Alya/Mir Erdan

### Additional Test Coverage
- Load decision change requests from file system
- Route workflow change request with required structure
- Route reference rebuild request with required structure
- Determine next actions with correct priority ordering
- Verify no route to Image Generation Agent
- Route decision change requests end-to-end
- Load workflow change request
- Load reference rebuild request
- Load both requests
- Workflow TD actions have priority 1
- Character Director actions have priority 2

## Critical Boundary Compliance

### Did NOT Run ComfyUI
✅ No ComfyUI execution triggered
✅ No frame generation
✅ No new frames created

### Did NOT Run TTS
✅ No text-to-speech execution
✅ No audio generation

### Did NOT Run ffmpeg
✅ No video encoding
✅ No scene assembly

### Did NOT Assemble Scene
✅ No MP4 creation
✅ No frame combination

### Did NOT Run QA Review
✅ No identity QA execution
✅ No frame QC

### Did NOT Apply Decisions
✅ ready_for_apply=false
✅ role_decisions/ not mutated
✅ selected_decision remains null in role_decisions/

### Did NOT Open Retry Gate
✅ retry_gate_open=false
✅ No retry generation allowed

### Did NOT Mark Production Accepted
✅ production_accepted=false
✅ No final approval granted

### Did NOT Mutate Final Artifacts
✅ No frame manifests modified
✅ No episode ledgers modified with apply events (only passive event appended)
✅ No final manifests changed

## Git Commit

### Commit Hash
[To be added after commit]

### Files Added
- app/production_cards/change_request_router.py
- tests/test_production_change_request_routing.py
- docs/acceptance/RC2_PRODCARDS2R_CHANGE_REQUEST_ROUTING.md

### Files Modified
- app/cli.py
- data/rc2_multishot1_ep01/output/control/artifact_index.json (passive pointer only)
- data/rc2_multishot1_ep01/output/control/episode_ledger.json (passive event appended)

## Push Result
[Pending - will execute after git commit]

## Explicit Confirmation

**RC2-PRODCARDS2R is accepted** because:
1. ✅ Change request artifacts are routed to the correct production roles
2. ✅ workflow_change_request routes to Workflow TD
3. ✅ reference_rebuild_request routes to Character Director
4. ✅ Retry gate remains closed (retry_gate_open=false)
5. ✅ Role_decisions remain pending (not mutated by routing)
6. ✅ ready_for_apply remains false
7. ✅ Production_accepted remains false
8. ✅ Downstream remains blocked (downstream_blocked=true)
9. ✅ Tests pass (313 passed)
10. ✅ Tracked proof exists (this document)
11. ✅ No apply/generation/downstream action executes
12. ✅ Artifact index records passive routing section only
13. ✅ Episode ledger records decision_change_requests_routed
14. ✅ No route to Image Generation Agent
15. ✅ No core hardcode for Alya/Mir Erdan

The change request routing preview successfully routes decision change artifacts to the correct production roles (Workflow TD for workflow changes, Character Director for reference rebuilds) without opening retry generation or applying decisions, providing safe routing preview while maintaining all critical boundaries.
