# RC2-PRODCARDS2M Real Role Decision Submission Contract Acceptance Report

**Date:** 2026-04-28
**Project:** comfy-agent-mvp
**Release:** RC2-MULTISHOT1
**Status:** ACCEPTED

## Summary

RC2-PRODCARDS2M successfully implemented a strict submission contract for real Character Director and Workflow TD decisions based on evidence packets. Submission templates are draft submissions for real role input, NOT decisions. They do NOT approve decisions, do NOT open retry gate, do NOT mark production_accepted=true.

## Implementation Details

### Files Modified/Created

- `app/production_cards/decision_submission.py` (NEW) - Module for creating and validating decision submission contracts
- `app/cli.py` (MODIFIED) - Added CLI commands for create-role-decision-submission-contract and validate-role-decision-submission-contract
- `tests/test_production_role_decision_submission.py` (NEW) - Test suite for decision submission contracts

### CLI Commands Added

```bash
python -m app create-role-decision-submission-contract --project-root "<path>" --json
python -m app validate-role-decision-submission-contract --project-root "<path>" --json
```

### Output Structure

Submission templates and instructions are saved to:
```
data/rc2_multishot1_ep01/output/control/role_decision_submissions/
  - character_director_real_decision.SUBMIT.json
  - workflow_td_real_decision.SUBMIT.json
  - CHARACTER_DIRECTOR_DECISION_INSTRUCTIONS.md
  - WORKFLOW_TD_DECISION_INSTRUCTIONS.md
```

## Verification Results

### 1. py_compile Validation

**Status:** PASSED
**Command:**
```bash
python -m py_compile app/cli.py app/production_cards/decision_submission.py app/production_cards/role_review_packets.py app/production_cards/state_repair.py app/production_cards/decision_apply.py app/production_cards/decision_intake.py app/production_cards/approval_gate.py app/production_cards/role_decisions.py app/production_cards/work_orders.py app/production_cards/router.py app/production_cards/validator.py app/production_cards/materializer.py
```

**Exit Code:** 0

### 2. pytest Tests

**Status:** PASSED
**Command:**
```bash
python -m pytest tests/test_production_card_schemas.py tests/test_production_card_validator.py tests/test_production_role_routing.py tests/test_production_card_materialization.py tests/test_production_work_orders.py tests/test_production_role_decisions.py tests/test_production_role_approval_gate.py tests/test_production_role_approval_fixtures.py tests/test_production_role_decision_intake.py tests/test_production_role_decision_apply.py tests/test_production_role_decision_apply_safety.py tests/test_production_state_repair.py tests/test_production_role_review_packets.py tests/test_production_role_decision_submission.py -q -s --tb=short
```

**Result:** 189 passed, 1134 warnings in 11.36s

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

#### validate-role-review-packets

**Command:**
```bash
python -m app validate-role-review-packets --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Result:**
```json
{
  "status": "valid",
  "packets_found": 2,
  "decision_ready": false,
  "downstream_blocked": true,
  "production_accepted": false,
  "missing_required_evidence": [],
  "evidence_only": true,
  "not_decisions": true
}
```

#### create-role-decision-submission-contract

**Command:**
```bash
python -m app create-role-decision-submission-contract --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Result:**
```json
{
  "status": "completed",
  "project_root": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01",
  "downstream_blocked": true,
  "production_accepted": false,
  "retry_gate_open": false,
  "submission_templates_created": 2,
  "ready_for_real_role_input": true,
  "decision_ready": false,
  "templates": [
    {
      "role": "Character Director",
      "template_path": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\control\\role_decision_submissions\\character_director_real_decision.SUBMIT.json",
      "decision_source": "real_role_decision",
      "fixture_only": false,
      "approved_for_shot": "shot01"
    },
    {
      "role": "Workflow TD / ComfyUI Technical Director",
      "template_path": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\control\\role_decision_submissions\\workflow_td_real_decision.SUBMIT.json",
      "decision_source": "real_role_decision",
      "fixture_only": false,
      "approved_for_shot": "shot01"
    }
  ],
  "instructions": [
    {
      "role": "Character Director",
      "instructions_path": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\control\\role_decision_submissions\\CHARACTER_DIRECTOR_DECISION_INSTRUCTIONS.md"
    },
    {
      "role": "Workflow TD / ComfyUI Technical Director",
      "instructions_path": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\control\\role_decision_submissions\\WORKFLOW_TD_DECISION_INSTRUCTIONS.md"
    }
  ]
}
```

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
  "production_accepted": false,
  "validation_errors": []
}
```

#### validate-role-approval-gate

**Command:**
```bash
python -m app validate-role-approval-gate --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

**Result:**
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

## Submission Template Fragments

### Character Director Submission Template

**File:** `output/control/role_decision_submissions/character_director_real_decision.SUBMIT.json`

```json
{
  "role": "Character Director",
  "decision_source": "real_role_decision",
  "fixture_only": false,
  "approved_by_role": "Character Director",
  "approved_for_project_id": "rc2_multishot1_ep01",
  "approved_for_shot": "shot01",
  "character_name": "Alya",
  "based_on_evidence_packet": "output\\control\\role_review_packets\\character_director_identity_evidence_packet.json",
  "based_on_work_order": "output\\control\\work_orders\\character_director_identity_review.json",
  "current_decision_status": "draft_submission",
  "allowed_decisions": [
    "approve",
    "reject",
    "request_new_reference",
    "request_workflow_change"
  ],
  "selected_decision": null,
  "required_artifacts": [
    "approved_character_identity_rules",
    "approved_reference_strategy",
    "identity_acceptance_criteria"
  ],
  "production_accepted": false,
  "downstream_blocked": true,
  "next_allowed_action_if_approved": "retry_generate_frames",
  "created_at": "2026-04-28T12:49:03.112279Z",
  "project_specific_data_allowed": true,
  "source_project_root": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
}
```

### Workflow TD Submission Template

**File:** `output/control/role_decision_submissions/workflow_td_real_decision.SUBMIT.json`

```json
{
  "role": "Workflow TD / ComfyUI Technical Director",
  "decision_source": "real_role_decision",
  "fixture_only": false,
  "approved_by_role": "Workflow TD / ComfyUI Technical Director",
  "approved_for_project_id": "rc2_multishot1_ep01",
  "approved_for_shot": "shot01",
  "current_required_generation_mode": "gorynych_identity",
  "legacy_reference_locked_allowed_for_production": false,
  "based_on_evidence_packet": "output\\control\\role_review_packets\\workflow_td_identity_workflow_evidence_packet.json",
  "based_on_work_order": "output\\control\\work_orders\\workflow_td_identity_workflow_review.json",
  "current_decision_status": "draft_submission",
  "allowed_decisions": [
    "approve_workflow",
    "reject_workflow",
    "request_missing_nodes",
    "request_missing_models",
    "request_reference_rebuild"
  ],
  "selected_decision": null,
  "required_artifacts": [
    "workflow_audit",
    "required_nodes",
    "required_models",
    "preflight_result",
    "output_collection_contract"
  ],
  "production_accepted": false,
  "downstream_blocked": true,
  "next_allowed_action_if_approved": "retry_generate_frames",
  "created_at": "2026-04-28T12:49:03.112279Z",
  "project_specific_data_allowed": true,
  "source_project_root": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"
}
```

## Markdown Instructions

**Files:**
- `output/control/role_decision_submissions/CHARACTER_DIRECTOR_DECISION_INSTRUCTIONS.md`
- `output/control/role_decision_submissions/WORKFLOW_TD_DECISION_INSTRUCTIONS.md`

Both files explain:
- What evidence packet to review
- Allowed decisions
- Required artifacts
- What must not be changed
- production_accepted must remain false
- Approval opens retry only, not final acceptance

## Artifact Index Update

**File:** `output/control/artifact_index.json`

**New Section:**
```json
"role_decision_submission_contract": {
  "status": "created",
  "character_director_submission_template": "output\\control\\role_decision_submissions\\character_director_real_decision.SUBMIT.json",
  "workflow_td_submission_template": "output\\control\\role_decision_submissions\\workflow_td_real_decision.SUBMIT.json",
  "downstream_blocked": true,
  "production_accepted": false,
  "retry_gate_open": false
}
```

**Verification:**
- `downstream_blocked`: true
- `production_accepted`: false
- `retry_gate_open`: false
- `next_allowed_action`: "blocked_by_role_approval"

## Episode Ledger Update

**File:** `output/control/episode_ledger.json`

**New Event:**
```json
{
  "event_type": "role_decision_submission_contract_created",
  "timestamp": "2026-04-28T12:49:07.709563Z",
  "roles": [
    "Character Director",
    "Workflow TD / ComfyUI Technical Director"
  ],
  "reason": "identity_qa_failed",
  "downstream_blocked": true,
  "production_accepted": false,
  "retry_gate_open": false,
  "comfyui_generation": false,
  "pipeline_action_rerun": false
}
```

## Compliance Verification

### Templates Are Real-Decision-Ready But Not Approvals

**Proof:**
- Both templates have `"decision_source": "real_role_decision"`
- Both templates have `"fixture_only": false`
- Both templates have `"current_decision_status": "draft_submission"`
- Both templates have `"selected_decision": null`
- create-role-decision-submission-contract result has `"ready_for_real_role_input": true` and `"decision_ready": false`

### Selected Decision Remains Null

**Proof:**
- Character Director template has `"selected_decision": null`
- Workflow TD template has `"selected_decision": null`
- validate-role-decision-submission-contract returns `"decision_ready": false`

### Retry Gate Remains Closed

**Proof:**
- artifact_index has `"retry_gate_open": false`
- create-role-decision-submission-contract result has `"retry_gate_open": false`
- validate-role-decision-submission-contract returns `"retry_gate_open": false`
- validate-role-approval-gate returns `"can_retry_generation": false` and `"next_allowed_action": null`

### Production Accepted Remains False

**Proof:**
- artifact_index has `"production_accepted": false`
- Both templates have `"production_accepted": false`
- create-role-decision-submission-contract result has `"production_accepted": false`
- validate-role-decision-submission-contract returns `"production_accepted": false`
- validate-role-approval-gate returns `"production_accepted": false`

### Downstream Remains Blocked

**Proof:**
- artifact_index has `"downstream_blocked": true`
- Both templates have `"downstream_blocked": true`
- create-role-decision-submission-contract result has `"downstream_blocked": true`
- validate-role-decision-submission-contract returns `"downstream_blocked": true`
- validate-role-approval-gate returns `"downstream_blocked": true` and `"status": "blocked"`

### No Generation Happened

**Proof:**
- create-role-decision-submission-contract result has no comfyui_generation field (default false)
- episode_ledger event has `"comfyui_generation": false`
- episode_ledger event has `"pipeline_action_rerun": false`
- No frames were generated during submission contract creation

### No Downstream Action Executed

**Proof:**
- validate-role-approval-gate returns `"next_allowed_action": null`
- No decision intake or apply occurred
- No retry gate opening occurred
- No production_accepted mutation occurred
- episode_ledger event has `"pipeline_action_rerun": false`

### Templates Based on Evidence Packets

**Proof:**
- Character Director template has `"based_on_evidence_packet": "output\\control\\role_review_packets\\character_director_identity_evidence_packet.json"`
- Workflow TD template has `"based_on_evidence_packet": "output\\control\\role_review_packets\\workflow_td_identity_workflow_evidence_packet.json"`
- Both templates have `"based_on_work_order"` fields pointing to work orders

### Templates Use Real Project Data

**Proof:**
- Character Director template has `"character_name": "Alya"` (from project data, not hardcoded)
- Both templates have `"approved_for_project_id": "rc2_multishot1_ep01"`
- Both templates have `"project_specific_data_allowed": true`
- Both templates have `"source_project_root": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01"`

### Templates Contain Required Fields

**Proof:**
- Character Director template has all required fields: role, decision_source, fixture_only, approved_by_role, approved_for_project_id, approved_for_shot, based_on_evidence_packet, based_on_work_order, current_decision_status, allowed_decisions, selected_decision, required_artifacts, production_accepted, downstream_blocked, next_allowed_action_if_approved
- Workflow TD template has all required fields plus: current_required_generation_mode, legacy_reference_locked_allowed_for_production

### Validation Returns Correct Structure

**Proof:**
- validate-role-decision-submission-contract returns `"status": "valid"`
- validate-role-decision-submission-contract returns `"submission_templates_found": 2`
- validate-role-decision-submission-contract returns `"ready_for_real_role_input": true`
- validate-role-decision-submission-contract returns `"decision_ready": false` (correct - templates are draft submissions, not submitted decisions)
- validate-role-decision-submission-contract returns `"validation_errors": []`

### Test Coverage

**Proof:**
- Test suite includes 16 test cases covering:
  - Character Director submission template creation
  - Workflow TD submission template creation
  - Templates are fixture_only=false
  - Templates use decision_source=real_role_decision
  - Templates contain approved_for_project_id
  - Templates contain approved_for_shot=shot01
  - Templates reference evidence packet paths
  - Templates reference work order paths
  - selected_decision remains null
  - Templates do not approve decisions
  - Templates do not open retry gate
  - production_accepted remains false
  - Markdown instructions are created
  - Artifact index includes submission contract
  - Episode ledger records role_decision_submission_contract_created
  - validate command returns ready_for_real_role_input=true but decision_ready=false
  - No core hardcode for Alya/Mir Erdan

### Forbidden Actions Compliance

**Proof:**
- No ComfyUI execution during submission contract creation
- No frame generation during submission contract creation
- No TTS execution during submission contract creation
- No ffmpeg execution during submission contract creation
- No scene assembly during submission contract creation
- No qa_review execution during submission contract creation
- No decision apply during submission contract creation
- No decision approval during submission contract creation
- No retry gate opening during submission contract creation
- No production_accepted=true mutation during submission contract creation
- No final artifact mutation during submission contract creation

## Risks

**None identified.** The implementation strictly follows draft submission semantics and does not approve decisions, open retry gate, or mutate production state.

## Conclusion

RC2-PRODCARDS2M is **ACCEPTED**. All requirements have been met:

1. ✅ Created `app/production_cards/decision_submission.py` module with required functions
2. ✅ Added CLI commands `create-role-decision-submission-contract` and `validate-role-decision-submission-contract`
3. ✅ Created output folder structure `output/control/role_decision_submissions/`
4. ✅ Created Character Director submission template with required fields
5. ✅ Created Workflow TD submission template with required fields
6. ✅ Created Markdown instructions for both roles
7. ✅ Updated `artifact_index.json` with role_decision_submission_contract section
8. ✅ Updated `episode_ledger.json` with role_decision_submission_contract_created event
9. ✅ Created comprehensive test suite `tests/test_production_role_decision_submission.py`
10. ✅ py_compile validation passed
11. ✅ pytest tests passed (189 passed)
12. ✅ CLI commands executed successfully with correct JSON output
13. ✅ Submission templates are fixture_only=false and decision_source=real_role_decision
14. ✅ Submission templates are based on evidence packets
15. ✅ Submission templates do not approve decisions
16. ✅ selected_decision remains null
17. ✅ Retry gate remains closed
18. ✅ production_accepted remains false
19. ✅ downstream remains blocked
20. ✅ No generation happened
21. ✅ No downstream action executed
22. ✅ Tracked proof doc created with all required fragments
23. ✅ Templates use real project data (character_name from project, not hardcoded)
24. ✅ Validation returns ready_for_real_role_input=true but decision_ready=false

## Git Commit

**Commit Message:** feat: add real role decision submission contract

**Files Committed:**
- app/production_cards/decision_submission.py
- app/cli.py
- tests/test_production_role_decision_submission.py
- docs/acceptance/RC2_PRODCARDS2M_REAL_DECISION_SUBMISSION_CONTRACT.md
- data/rc2_multishot1_ep01/output/control/artifact_index.json
- data/rc2_multishot1_ep01/output/control/episode_ledger.json

**Commit Hash:** f9c668f

**Push Status:** SUCCESS (pushed to main branch)
