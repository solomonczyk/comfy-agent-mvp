# Character Director Decision Submission Instructions

## Role
Character Director

## Purpose
Review evidence packet and submit real decision for identity QA failure on shot01.

## Evidence Packet to Review
- File: `output/control/role_review_packets/character_director_identity_evidence_packet.json`
- Type: character_director_identity_review
- Character: Alya
- Issue: identity_qa_failed

## Allowed Decisions
- **approve**: Approve character identity strategy for retry
- **reject**: Reject current character identity strategy
- **request_new_reference**: Request new character reference
- **request_workflow_change**: Request workflow changes

## Required Artifacts
Before submitting your decision, ensure you have reviewed:
- Approved character identity rules
- Approved reference strategy
- Identity acceptance criteria

## What Must Not Be Changed
- **DO NOT** modify `production_accepted` (must remain false)
- **DO NOT** modify `downstream_blocked` (must remain true)
- **DO NOT** open retry gate (this is handled by decision intake/apply)
- **DO NOT** approve automatically (this is a manual role decision)

## Submission Process
1. Review the evidence packet at `output/control/role_review_packets/character_director_identity_evidence_packet.json`
2. Review the work order at `output/control/work_orders/character_director_identity_review.json`
3. Make your decision based on the evidence
4. Fill in the `selected_decision` field in `output/control/role_decision_submissions/character_director_real_decision.SUBMIT.json`
5. Add any required artifacts to your decision
6. Submit for validation

## Important Notes
- This is a **real role decision submission**, not a fixture
- Your decision will be validated before being applied
- Approval opens retry gate for frame generation, but does not mark production_accepted=true
- production_accepted=true is only set after successful frame generation passes identity QA
- Downstream remains blocked until your decision is validated and applied
