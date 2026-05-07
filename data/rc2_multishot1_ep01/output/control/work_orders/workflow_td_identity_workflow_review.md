# Workflow TD Work Order: Identity Workflow Review

## Role: Workflow TD / ComfyUI Technical Director

## Blocked Shot
- **Shot ID:** shot01
- **Issue:** identity_qa_failed

## Current Workflow Configuration
- **Required Generation Mode:** gorynych_identity
- **Legacy Reference Locked Allowed:** False

## Required Decision
You must choose one of the following:
- approve_workflow
- reject_workflow
- request_missing_nodes
- request_missing_models
- request_reference_rebuild

**Description:** Workflow TD must approve the identity workflow or request necessary changes

## Required Artifacts
- **workflow_audit:** Audit of the current identity workflow configuration
- **required_nodes:** List of required nodes for identity consistency
- **required_models:** List of required models for character identity
- **preflight_result:** Preflight validation result for the workflow
- **output_collection_contract:** Contract for collecting workflow outputs

## Handoff
After completion, hand off to: Image Generation Agent (only after Character Director approval)

## Downstream Status
**Blocked:** True

## Created At
2026-04-28T10:32:40.324719Z
