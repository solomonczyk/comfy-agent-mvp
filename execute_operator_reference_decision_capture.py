"""Execute operator reference decision capture for RC-COMBINE-V2-OPERATOR-REFERENCE-DECISION-CAPTURE-001.

This script captures the human operator's decision about the canonical reference set.
"""

import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agents.operator_reference_decision_capture import OperatorReferenceDecisionCapture


def main():
    project_root = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
    
    # Operator decision from task specification
    operator_decision = {
        "operator": "Андрей",
        "decision_source": "human_operator_manual_review",
        "decision_text": "Я вручную просмотрел все изображения в input/canonical_references и принимаю их как canonical reference set.",
        "reference_scope": "all_images_in_input_canonical_references",
        "accepted": True
    }
    
    # Initialize capture agent
    capture = OperatorReferenceDecisionCapture(str(project_root))
    
    # Execute full capture
    print(f"Executing operator reference decision capture for {project_root}...")
    print(f"Operator: {operator_decision['operator']}")
    print(f"Decision: {operator_decision['decision_text']}")
    
    proof = capture.execute_full_capture(
        operator=operator_decision["operator"],
        decision_source=operator_decision["decision_source"],
        decision_text=operator_decision["decision_text"],
        reference_scope=operator_decision["reference_scope"],
        accepted=operator_decision["accepted"]
    )
    
    # Save proof
    proof_path = project_root / "output" / "control" / "operator_reference_review" / "operator_reference_decision_capture_proof.json"
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(proof_path, 'w', encoding='utf-8') as f:
        json.dump(proof, f, indent=2, ensure_ascii=False)
    
    print(f"\nCapture completed successfully!")
    print(f"Proof saved to: {proof_path}")
    print(f"\nSummary:")
    print(f"  - Current state: {proof['current_state']}")
    print(f"  - Next allowed action: {proof['next_allowed_action']}")
    print(f"  - Inventory count: {proof['inventory_count']}")
    print(f"  - Old packet reconciled: {proof['old_24_packet_reconciled']}")
    print(f"  - Packet is partial: {proof['packet_is_partial_if_count_mismatch']}")
    print(f"  - Canonical set accepted: {proof['canonical_reference_set_accepted']}")
    print(f"  - Production accepted: {proof['production_accepted']}")
    
    return proof


if __name__ == "__main__":
    main()
