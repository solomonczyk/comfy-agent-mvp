# Workflow TD Decision Submission Instructions

## Role
Workflow TD / ComfyUI Technical Director

## Purpose
Review evidence packet and submit real decision for identity workflow failure on shot01.

## Evidence Packet to Review
- File: `output/control/role_review_packets/workflow_td_identity_workflow_evidence_packet.json`
- Type: workflow_td_identity_workflow_review
- Generation Mode: gorynych_identity
- Issue: identity_qa_failed

## Allowed Decisions
- **approve_workflow**: Approve workflow for retry
- **reject_workflow**: Reject current workflow
- **request_missing_nodes**: Request missing ComfyUI nodes
- **request_missing_models**: Request missing models
- **request_reference_rebuild**: Request reference rebuild

## Required Artifacts
Before submitting your decision, ensure you have reviewed:
- Workflow audit
- Required nodes (IPAdapter, ControlNet, KSampler)
- Required models (character_reference_model, identity_preservation_model)
- Preflight result
- Output collection contract (frame_manifest.json)

## What Must Not Be Changed
- **DO NOT** modify `production_accepted` (must remain false)
- **DO NOT** modify `downstream_blocked` (must remain true)
- **DO NOT** open retry gate (this is handled by decision intake/apply)
- **DO NOT** approve automatically (this is a manual role decision)
- **DO NOT** allow legacy reference_locked for production (must remain false)

## Submission Process
1. Review the evidence packet at `output/control/role_review_packets/workflow_td_identity_workflow_evidence_packet.json`
2. Review the work order at `output/control/workflows/workflow_td_identity_workflow_review.json`
3. Make your decision based on the evidence
4. Fill in the `selected_decision` field in `output/control/role_decision_submissions/workflow_td_real_decision.SUBMIT.json`
5. Add any required artifacts to your decision
6. Submit for validation

## Important Notes
- This is a **real role decision submission**, not a fixture
- Your decision will be validated before being applied
- Approval opens retry gate for frame generation, but does not mark production_accepted=true
- production_accepted=true is only set after successful frame generation passes identity QA
- Downstream remains blocked until your decision is validated and applied
- Legacy reference_locked workflow is not allowed for production
