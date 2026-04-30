# RC2-PRODCARDS3L — Corrective Work Order Instructions

**Task:** RC2-PRODCARDS3L  
**Episode:** ep01  
**Shot:** shot01 (authoritative rejected shot)  
**State:** corrective_plan_review complete → corrective work orders created  
**Next allowed action:** corrective_work_order_review  

---

## Context

ep01_shot01 was rejected by operator override after retry #2. Root cause: model/checkpoint
incompatibility (realvisxlV50_v50Bakedvae.safetensors) causing character identity instability
and low visual quality. A corrective plan (RC2-PRODCARDS3K) was created and scope-reconciled
(RC2-PRODCARDS3L-SCOPE-RECONCILIATION). This document governs the corrective work orders
derived from that plan.

---

## Work Orders Created

| File | Role | Status |
|------|------|--------|
| `character_director_corrective_work_order.json` | Character Director | pending |
| `workflow_td_corrective_work_order.json` | Workflow TD | pending |

---

## Character Director — Required Tasks

1. **cd-001 — Model/Checkpoint Evaluation**  
   Evaluate whether `realvisxlV50_v50Bakedvae.safetensors` can reliably render the target character type.  
   Deliver: compatibility verdict (compatible/incompatible) with rationale.

2. **cd-002 — Alternative Checkpoint Specification** *(depends on cd-001)*  
   If incompatible, specify an alternative checkpoint by name/path.  
   Deliver: explicit checkpoint recommendation.

3. **cd-003 — Character Identity Guidance Revision** *(depends on cd-002)*  
   Revise prompt guidance, identity preservation requirements, and consistency targets for the new checkpoint.  
   Deliver: revised character identity specification.

4. **cd-004 — Reference/Identity Preservation Requirements** *(depends on cd-003)*  
   Define reference image requirements for retry. Update reference image if specification changes.  
   Deliver: updated reference path or explicit confirmation existing reference is valid.

---

## Workflow TD — Required Tasks

1. **wd-001 — Alternative Checkpoint Workflow Compatibility** *(depends on cd-002)*  
   Test that Character Director's recommended checkpoint loads in the ComfyUI workflow.  
   Deliver: compatibility report with recommended checkpoint for retry.

2. **wd-002 — Workflow Parameter Changes**  
   Review and revise reference_locked workflow parameters (denoising, guidance scale, reference weighting, sampler).  
   Deliver: current vs. proposed parameter values with rationale.

3. **wd-003 — Identity Preservation Component Evaluation** *(depends on wd-001)*  
   Evaluate IP-Adapter, LoRA, reference lock, or stronger reference weighting availability and configuration.  
   Deliver: evaluation report with enable/disable recommendations and configuration values.

4. **wd-004 — Workflow Revision Requirements** *(depends on wd-001, wd-002, wd-003)*  
   Define complete workflow revision specification for retry: checkpoint path, revised parameters, identity preservation config.  
   Deliver: complete workflow revision specification ready for retry authorization review.

---

## Joint Approval Gate (joint-001)

**Both Character Director and Workflow TD outputs must be completed and reviewed before controlled retry authorization is issued.**

- Retry is blocked (`retry_gate_open: false`) until this gate clears.
- After joint gate clears, a new controlled retry decision (joint-002) must be made before any generation begins.
- No ComfyUI execution, frame generation, QA rerun, assembly, audio, or render may occur until authorized.

---

## Blocked Actions (boundary enforcement)

The following actions are **explicitly prohibited** while corrective work orders are in `pending` state:

- `retry_generate_frames` — BLOCKED
- ComfyUI generation — BLOCKED
- `qa_review` rerun — BLOCKED
- `assemble_scene` — BLOCKED
- audio attachment — BLOCKED
- episode render — BLOCKED
- `production_accepted = true` — BLOCKED
- `downstream_blocked = false` — BLOCKED

---

## State Summary

| Key | Value |
|-----|-------|
| `next_allowed_action` | `corrective_work_order_review` |
| `retry_gate_open` | `false` |
| `production_accepted` | `false` |
| `assemble_scene_allowed` | `false` |
| `downstream_blocked` | `true` |
| `corrective_work_orders_created` | `true` |
| `corrective_work_orders_count` | `2` |
