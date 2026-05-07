# Change Request Work Order Summary

## Current Change Request Routing

### workflow_change_request
- **Source Role**: Character Director
- **Target Role**: Workflow TD / ComfyUI Technical Director
- **Required Action**: revise_identity_workflow_strategy
- **Reason**: identity_qa_failed
- **Blocks Retry**: True

### reference_rebuild_request
- **Source Role**: Workflow TD / ComfyUI Technical Director
- **Target Role**: Character Director
- **Required Action**: rebuild_or_update_identity_reference_strategy
- **Reason**: identity_qa_failed
- **Blocks Retry**: True

## Each Role's Required Work

### Workflow TD / ComfyUI Technical Director
- **Task**: revise_identity_workflow_strategy
- **Required Outputs**:
  - updated_workflow_strategy
  - workflow_audit
  - required_nodes
  - required_models
  - preflight_result
  - output_collection_contract
- **Required Generation Mode**: gorynych_identity
- **Legacy Reference Locked**: Not allowed for production

### Character Director
- **Task**: rebuild_or_update_identity_reference_strategy
- **Required Outputs**:
  - updated_character_identity_rules
  - updated_reference_strategy
  - identity_acceptance_criteria
  - reference_rebuild_notes
- **Required Generation Mode**: gorynych_identity

## Why Retry Remains Blocked

Retry generation is blocked because:
- Role decisions remain pending (not yet approved)
- Change requests have been created but not yet executed
- Workflow TD must revise the identity workflow strategy
- Character Director must rebuild or update the reference strategy
- No generation has been authorized

## What Must Happen Before Decisions Can Be Resubmitted

Before role decisions can be resubmitted for approval:
1. Workflow TD must complete the workflow change work order
2. Character Director must complete the reference rebuild work order
3. Both roles must provide the required outputs
4. New decision drafts can then be created with updated evidence
5. Decisions must be approved (not request changes)

## No Generation Authorized

This work order creation does NOT authorize any generation:
- No ComfyUI execution will occur
- No frames will be generated
- No references will be rebuilt
- No workflow execution outputs will be created
- This is a planning step only

## Current State

- **Retry Gate Open**: False
- **Production Accepted**: False
- **Downstream Blocked**: True
- **Role Decisions Status**: pending
