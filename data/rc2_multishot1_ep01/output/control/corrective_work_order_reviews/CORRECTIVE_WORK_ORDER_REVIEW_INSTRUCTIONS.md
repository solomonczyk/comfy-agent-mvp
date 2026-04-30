# RC2-PRODCARDS3M — Corrective Work Order Review Instructions

**Task:** RC2-PRODCARDS3M  
**Episode:** ep01  
**Shot:** shot01 (authoritative rejected shot)  
**State:** corrective_work_orders created → review contracts created  
**Next allowed action:** corrective_work_order_submission  

---

## Context

ep01_shot01 was rejected by operator override after retry #2. Corrective work orders were created (RC2-PRODCARDS3L) for Character Director and Workflow TD. This document governs the review and completion contract submission process.

---

## Review Contracts Created

| File | Role | Status |
|------|------|--------|
| `character_director_completion_contract.json` | Character Director | awaiting_submission |
| `workflow_td_completion_contract.json` | Workflow TD | awaiting_submission |

---

## Character Director — Required Submission Fields

### 1. Checkpoint Suitability Assessment
- **checkpoint_name**: Exact checkpoint evaluated
- **compatibility_verdict**: compatible / incompatible / partially_compatible_with_limitations
- **assessment_rationale**: Detailed rationale
- **character_type_match_score**: 0-100 score
- **visual_quality_benchmark**: Expected quality level
- **identity_stability_assessment**: Identity consistency capability

### 2. Alternative Checkpoint Recommendation (if incompatible)
- **recommendation_status**: recommend_alternative / current_checkpoint_acceptable
- **recommended_checkpoint_name**: Alternative model name
- **recommended_checkpoint_path**: Path or identifier
- **character_compatibility_rationale**: Why this checkpoint is better
- **expected_visual_quality**: Expected quality with alternative
- **workflow_compatibility_notes**: For Workflow TD evaluation

### 3. Character Identity Guidance Revision
- **revision_required**: Boolean indicating if revision needed
- **revised_positive_prompt_guidance**: Updated positive prompts
- **revised_negative_prompt_guidance**: Updated negative prompts
- **identity_preservation_requirements**: Specific preservation requirements
- **consistency_targets**: Facial features, body proportions, clothing style, overall appearance
- **checkpoint_specific_considerations**: Any checkpoint-specific rendering notes

### 4. Reference/Identity Preservation Requirements
- **existing_reference_valid**: Whether current refs remain valid
- **updated_reference_required**: Whether new refs needed
- **updated_reference_path**: Path to updated refs if applicable
- **identity_preservation_mechanism**: reference_only / ip_adapter / lora / combined_techniques
- **identity_strength_requirements**: Required preservation strength level
- **reference_weighting_recommendation**: Recommended weighting if applicable

### 5. Retry Readiness Verdict
- **verdict**: ready / not_ready / ready_with_conditions
- **verdict_rationale**: Detailed rationale
- **blocking_issues**: List of blocking issues if not ready
- **conditions_for_readiness**: Conditions if ready_with_conditions
- **recommended_next_action**: Recommended next step
- **confidence_level**: high / medium / low

---

## Workflow TD — Required Submission Fields

### 1. Workflow Compatibility Assessment
- **checkpoint_tested**: Name of checkpoint tested
- **workflow_load_status**: loads_successfully / loads_with_warnings / fails_to_load
- **compatibility_verdict**: compatible / compatible_with_modifications / incompatible
- **test_results_summary**: Summary of test results
- **checkpoint_path_verified**: Boolean path verification
- **vae_compatibility_notes**: VAE considerations
- **memory_requirements_assessment**: VRAM requirements
- **performance_characteristics**: Expected generation speed

### 2. Parameter/Settings Revision Proposal
- **revision_required**: Boolean
- **current_parameters**: denoising_strength, guidance_scale, reference_image_weight, sampler, scheduler, steps
- **proposed_parameters**: New values with rationale for each change
- **parameter_compatibility_notes**: Compatibility with recommended checkpoint

### 3. IP-Adapter / LoRA / Reference-Lock Evaluation
- **ip_adapter_evaluation**: Available, enabled status, recommendation, weight, rationale
- **lora_evaluation**: Available, character LoRA exists, recommendation, path, weight, rationale
- **reference_lock_evaluation**: Enabled status, mechanism type, recommended configuration
- **combined_identity_strategy**: Overall identity preservation approach
- **identity_strength_target**: Target preservation level
- **implementation_complexity**: low / medium / high

### 4. Implementation Requirements Before Retry
- **workflow_revision_summary**: Executive summary of all changes
- **checkpoint_implementation**: Path, load requirements, fallback checkpoint
- **parameter_implementation**: Parameters to modify, workflow file updates needed
- **identity_preservation_implementation**: Components to enable, configuration changes
- **testing_requirements_before_retry**: Required pre-retry tests
- **risk_assessment**: Implementation risk assessment
- **rollback_plan**: Plan if implementation fails

### 5. Retry Readiness Verdict
- **verdict**: ready / not_ready / ready_with_conditions
- **verdict_rationale**: Detailed rationale
- **blocking_issues**: Blocking issues list
- **conditions_for_readiness**: Conditions if applicable
- **character_director_dependency_status**: Status of CD completion
- **estimated_implementation_time**: Time estimate for changes
- **confidence_level**: high / medium / low
- **technical_risk_level**: low / medium / high

---

## Joint Review Gate (joint-002)

**Both Character Director and Workflow TD completion contracts must be submitted and validated before controlled retry can be authorized.**

### Gate Requirements:
1. Character Director completion contract submitted with all required fields populated
2. Workflow TD completion contract submitted with all required fields populated
3. Both contracts pass validation rules
4. At least one role reports "ready" or "ready_with_conditions" verdict

### Gate Blocking Conditions:
- Either contract incomplete or invalid → GATE BLOCKED
- Both roles report "not_ready" → GATE BLOCKED
- Either role has unresolved blocking issues → GATE BLOCKED

---

## Blocked Actions (boundary enforcement)

The following actions are **explicitly prohibited** until joint gate clears:

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
| `next_allowed_action` | `corrective_work_order_submission` |
| `retry_gate_open` | `false` |
| `production_accepted` | `false` |
| `assemble_scene_allowed` | `false` |
| `downstream_blocked` | `true` |
| `corrective_work_orders_created` | `true` |
| `corrective_work_orders_count` | `2` |
| `corrective_work_order_review_contracts_created` | `true` |
| `corrective_work_order_review_contracts_count` | `2` |

---

## Submission Process

1. Role completes their corrective work order tasks
2. Role fills in all required fields in their completion contract
3. Role submits contract (via controlled submission mechanism)
4. System validates submission completeness
5. When both contracts submitted, joint-002 gate evaluation triggers
6. If gate passes, next_allowed_action advances to controlled_retry_decision
