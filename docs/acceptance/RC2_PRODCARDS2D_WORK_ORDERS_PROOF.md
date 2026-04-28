# RC2-PRODCARDS2D Work Orders Proof

## Task
Convert production routing output into concrete role work orders for Character Director and Workflow TD so the blocked shot01 identity failure has actionable next tasks.

## Status
Completed

## Commands Run

### py_compile
```bash
python -m py_compile app/cli.py app/production_cards/router.py app/production_cards/validator.py app/production_cards/materializer.py app/production_cards/work_orders.py
```
**Result:** Passed - no errors

### pytest
```bash
python -m pytest tests/test_production_card_schemas.py tests/test_production_card_validator.py tests/test_production_role_routing.py tests/test_production_card_materialization.py tests/test_production_work_orders.py -q -s --tb=short
```
**Result:** 83 passed, 386 warnings

### validate-production-cards
```bash
python -m app validate-production-cards --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```
**Result:**
```json
{
  "status": "passed",
  "project_root": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01",
  "summary": {
    "cards_found": 11,
    "passed_checks": 11,
    "failed_checks": 0,
    "warnings": 0
  },
  "generation_ready": false
}
```

### route-production-tasks
```bash
python -m app route-production-tasks --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```
**Result:**
```json
{
  "status": "blocked",
  "project_root": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01",
  "generation_ready": false,
  "downstream_blocked": true,
  "summary": {
    "cards_found": 11,
    "issues_found": 12,
    "blocked_count": 12,
    "roles_needed": [
      "Character Director",
      "Workflow TD / ComfyUI Technical Director"
    ]
  }
}
```

### create-production-work-orders
```bash
python -m app create-production-work-orders --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```
**Result:**
```json
{
  "status": "completed",
  "project_root": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01",
  "downstream_blocked": true,
  "work_orders_created": 2,
  "work_orders": [
    {
      "role": "Character Director",
      "work_order_path": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\control\\work_orders\\character_director_identity_review.json",
      "blocking_reason": "identity_qa_failed",
      "required_output": "character_identity_approval"
    },
    {
      "role": "Workflow TD / ComfyUI Technical Director",
      "work_order_path": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\control\\work_orders\\workflow_td_identity_workflow_review.json",
      "blocking_reason": "identity_qa_failed",
      "required_output": "workflow_fit_approval"
    }
  ]
}
```

## Character Director Work Order Fragment

```json
{
  "role": "Character Director",
  "work_order_type": "identity_review",
  "blocked_shot": "shot01",
  "character_name": "Alya",
  "character_reference": "Alya",
  "display_name": "Alya",
  "issue": "identity_qa_failed",
  "frame_qc_passed": true,
  "identity_consistency_passed": false,
  "production_accepted": false,
  "required_decision": {
    "options": [
      "approve",
      "reject",
      "request_new_reference",
      "request_workflow_change"
    ]
  },
  "required_artifacts": {
    "approved_character_identity_rules": "Character identity consistency rules for the project",
    "approved_reference_strategy": "Strategy for character reference across shots",
    "identity_acceptance_criteria": "Criteria for accepting character identity as valid"
  },
  "handoff_to": "Workflow TD / ComfyUI Technical Director",
  "downstream_blocked": true,
  "project_specific_data_allowed": true
}
```

## Workflow TD Work Order Fragment

```json
{
  "role": "Workflow TD / ComfyUI Technical Director",
  "work_order_type": "identity_workflow_review",
  "blocked_shot": "shot01",
  "issue": "identity_qa_failed",
  "current_required_generation_mode": "gorynych_identity",
  "legacy_reference_locked_allowed_for_production": false,
  "required_decision": {
    "options": [
      "approve_workflow",
      "reject_workflow",
      "request_missing_nodes",
      "request_missing_models",
      "request_reference_rebuild"
    ]
  },
  "required_artifacts": {
    "workflow_audit": "Audit of the current identity workflow configuration",
    "required_nodes": "List of required nodes for identity consistency",
    "required_models": "List of required models for character identity",
    "preflight_result": "Preflight validation result for the workflow",
    "output_collection_contract": "Contract for collecting workflow outputs"
  },
  "handoff_to": "Image Generation Agent (only after Character Director approval)",
  "downstream_blocked": true,
  "project_specific_data_allowed": true
}
```

## artifact_index work_orders Fragment

```json
{
  "work_orders": {
    "character_director_work_order": "output/control/work_orders/character_director_identity_review.json",
    "workflow_td_work_order": "output/control/work_orders/workflow_td_identity_workflow_review.json"
  },
  "current_blocking_roles": [
    "Character Director",
    "Workflow TD / ComfyUI Technical Director"
  ],
  "downstream_blocked": true
}
```

## episode_ledger role_work_orders_created Fragment

```json
{
  "event_type": "role_work_orders_created",
  "timestamp": "2026-04-28T10:24:46.883402Z",
  "roles": [
    "Character Director",
    "Workflow TD / ComfyUI Technical Director"
  ],
  "reason": "identity_qa_failed",
  "downstream_blocked": true,
  "comfyui_generation": false,
  "pipeline_action_rerun": false,
  "work_order_count": 2
}
```

## Proof: downstream_blocked=true

- Character Director work order: `"downstream_blocked": true`
- Workflow TD work order: `"downstream_blocked": true`
- create-production-work-orders result: `"downstream_blocked": true`
- artifact_index: `"downstream_blocked": true`
- episode_ledger event: `"downstream_blocked": true`

## Proof: production_accepted=false

- Character Director work order: `"production_accepted": false`
- Shot card: `"production_accepted": false`
- No work order sets production_accepted to true

## Proof: No Generation/Downstream Action Executed

- episode_ledger event: `"comfyui_generation": false`
- episode_ledger event: `"pipeline_action_rerun": false`
- No ComfyUI generation commands were executed
- No TTS, ffmpeg, assembly, or render commands were executed
- Only work order creation commands were run

## Proof: Alya Project Data Preserved

- Character Director work order: `"character_name": "Alya"`, `"display_name": "Alya"`, `"character_reference": "Alya"`, `"project_specific_data_allowed": true`
- Shot card: `"character_reference": "Alya"`
- Work orders preserve real project data without sanitization

## Runtime Generated Artifacts Policy

The following runtime artifacts are local generated artifacts and are excluded from Git by .gitignore policy:
- `data/rc2_multishot1_ep01/output/control/work_orders/character_director_identity_review.json`
- `data/rc2_multishot1_ep01/output/control/work_orders/workflow_td_identity_workflow_review.json`
- `data/rc2_multishot1_ep01/output/control/work_orders/character_director_identity_review.md`
- `data/rc2_multishot1_ep01/output/control/work_orders/workflow_td_identity_workflow_review.md`
- `data/rc2_multishot1_ep01/output/control/artifact_index.json`
- `data/rc2_multishot1_ep01/output/control/episode_ledger.json`

These artifacts can be regenerated by running:
```bash
python -m app create-production-work-orders --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --json
```

## Files Tracked by Git

- `app/production_cards/work_orders.py` - Work orders module implementation
- `app/cli.py` - CLI command handler for create-production-work-orders
- `tests/test_production_work_orders.py` - Reproducibility tests for work orders
- `docs/acceptance/RC2_PRODCARDS2D_WORK_ORDERS_PROOF.md` - This tracked proof document
- `.gitignore` - Fixed to allow test files to be tracked

## Commit Information

- **Commit hash:** 1f86b52 (initial implementation)
- **Commit message:** "feat: create role work orders for identity failure"

## Acceptance Confirmation

RC2-PRODCARDS2D is fully accepted only if the work order implementation, reproducibility tests, and tracked proof summary are committed, generated runtime artifacts are either intentionally ignored or explicitly justified, downstream remains blocked, production_accepted remains false, tests pass, and no generation or downstream action executes.

**RC2-PRODCARDS2D is fully accepted.**
