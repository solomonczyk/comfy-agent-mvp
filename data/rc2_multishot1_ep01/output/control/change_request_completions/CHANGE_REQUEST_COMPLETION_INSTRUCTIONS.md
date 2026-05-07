# Change Request Completion Instructions

## Overview

These completion templates provide formal contracts for Workflow TD and Character Director
to complete their assigned work orders from the routed change requests. These are templates,
not completions—no work has been executed yet.

## Workflow TD / ComfyUI Technical Director

### Work Order: revise_identity_workflow_strategy
### Required Generation Mode: gorynych_identity

### Required Outputs:
- updated_workflow_strategy
- workflow_audit
- required_nodes
- required_models
- preflight_result
- output_collection_contract

### Allowed Resolutions:
- **workflow_strategy_updated**: Workflow strategy has been revised and is ready for retry
- **missing_nodes_reported**: Required nodes are missing and must be procured before retry
- **missing_models_reported**: Required models are missing and must be procured before retry
- **reference_rebuild_required**: Character Director must rebuild reference strategy first
- **blocked**: Work cannot proceed due to external dependencies

## Character Director

### Work Order: rebuild_or_update_identity_reference_strategy

### Required Outputs:
- updated_character_identity_rules
- updated_reference_strategy
- identity_acceptance_criteria
- reference_rebuild_notes

### Allowed Resolutions:
- **reference_strategy_updated**: Reference strategy has been updated and is ready for retry
- **identity_rules_updated**: Character identity rules have been updated
- **new_reference_required**: New reference images must be created before retry
- **workflow_change_required**: Workflow TD must revise workflow strategy first
- **blocked**: Work cannot proceed due to external dependencies

## Why These Are Templates, Not Completions

These completion templates are NOT completions because:
- No workflow execution has occurred
- No reference rebuild has occurred
- No required outputs have been provided
- No resolution has been selected
- completion_status is 'template', not 'completed'
- selected_resolution is null

## Why Retry Remains Blocked

Retry generation is blocked because:
- Completion templates are not yet completed
- Required outputs have not been provided
- No resolution has been selected
- Role decisions remain pending (not yet resubmitted)
- No generation has been authorized

## What Must Happen Before Retry Can Be Authorized

Before retry generation can be authorized:
1. Workflow TD must complete their work order with required outputs
2. Character Director must complete their work order with required outputs
3. Both roles must select a valid resolution
4. Completion status must change from 'template' to 'completed'
5. New role decision drafts can be created with updated evidence
6. Role decisions must be submitted and approved (not request changes)

## No Generation Authorized

This completion contract creation does NOT authorize any generation:
- No ComfyUI execution will occur
- No frames will be generated
- No references will be rebuilt
- No workflow execution outputs will be created
- This is a planning step only

