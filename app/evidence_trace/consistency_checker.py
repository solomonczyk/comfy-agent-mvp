"""Consistency Checker

Validates consistency of evidence trace across layers.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from .models import EvidenceEvent, DecisionStatus, SourceLayer


class ConsistencyCheckResult:
    """Result of a consistency check"""
    def __init__(self, check_id: str, description: str, passed: bool, details: str = ""):
        self.check_id = check_id
        self.description = description
        self.passed = passed
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "check_description": self.description,
            "passed": self.passed,
            "details": self.details
        }


class ConsistencyChecker:
    """Checker for evidence trace consistency"""

    def __init__(self, events: List[EvidenceEvent]):
        self.events = events
        self.checks: List[ConsistencyCheckResult] = []
        self.violations: List[str] = []
        self.warnings: List[str] = []

    def check_readiness_does_not_authorize_execution(self) -> ConsistencyCheckResult:
        """Check: readiness ready does not authorize execution"""
        readiness_events = [e for e in self.events if e.source_layer == SourceLayer.WORKFLOW_READINESS]
        readiness_ready = [e for e in readiness_events if e.decision_status == DecisionStatus.READY]
        
        # If readiness says ready, check if there's a corresponding authorization
        for ready_event in readiness_ready:
            # Look for tool policy events that might have authorized execution based on readiness
            tool_policy_events = [e for e in self.events if e.source_layer == SourceLayer.TOOL_POLICY]
            for tp_event in tool_policy_events:
                if tp_event.allowed_next_action == "execute" and "readiness" in str(tp_event.metadata).lower():
                    self.violations.append(
                        f"Readiness ready at {ready_event.event_id} used to authorize execution at {tp_event.event_id}"
                    )
                    return ConsistencyCheckResult(
                        "READINESS_NO_AUTH",
                        "Readiness ready does not authorize execution",
                        False,
                        f"Event {ready_event.event_id} readiness ready used to authorize execution"
                    )
        
        return ConsistencyCheckResult(
            "READINESS_NO_AUTH",
            "Readiness ready does not authorize execution",
            True,
            "No readiness ready used to authorize execution"
        )

    def check_runtime_gate_requires_authorization(self) -> ConsistencyCheckResult:
        """Check: runtime gate cannot be consumed without authorization"""
        gate_events = [e for e in self.events if e.source_layer == SourceLayer.RUNTIME_GATE]
        
        for gate_event in gate_events:
            if gate_event.decision_status == DecisionStatus.AUTHORIZED:
                # Check if there's a corresponding tool policy authorization
                tool_policy_events = [e for e in self.events if e.source_layer == SourceLayer.TOOL_POLICY]
                authorized = False
                for tp_event in tool_policy_events:
                    if tp_event.decision_status == DecisionStatus.AUTHORIZED:
                        authorized = True
                        break
                
                if not authorized:
                    self.violations.append(
                        f"Runtime gate {gate_event.event_id} consumed without tool policy authorization"
                    )
                    return ConsistencyCheckResult(
                        "GATE_REQUIRES_AUTH",
                        "Runtime gate requires authorization",
                        False,
                        f"Gate {gate_event.event_id} consumed without authorization"
                    )
        
        return ConsistencyCheckResult(
            "GATE_REQUIRES_AUTH",
            "Runtime gate requires authorization",
            True,
            "All gates consumed with proper authorization"
        )

    def check_blocked_tool_policy_cannot_become_allowed(self) -> ConsistencyCheckResult:
        """Check: blocked tool policy cannot become allowed downstream"""
        tool_policy_events = [e for e in self.events if e.source_layer == SourceLayer.TOOL_POLICY]
        
        for tp_event in tool_policy_events:
            if tp_event.decision_status == DecisionStatus.BLOCKED:
                # Check if any downstream event has allowed action
                for event in self.events:
                    if event.event_id != tp_event.event_id and event.timestamp > tp_event.timestamp:
                        if event.allowed_next_action and "execute" in event.allowed_next_action.lower():
                            self.violations.append(
                                f"Blocked tool policy {tp_event.event_id} became allowed in downstream event {event.event_id}"
                            )
                            return ConsistencyCheckResult(
                                "BLOCKED_NO_ALLOW",
                                "Blocked tool policy cannot become allowed",
                                False,
                                f"Blocked {tp_event.event_id} became allowed in {event.event_id}"
                            )
        
        return ConsistencyCheckResult(
            "BLOCKED_NO_ALLOW",
            "Blocked tool policy cannot become allowed",
            True,
            "No blocked tool policy became allowed downstream"
        )

    def check_production_accepted_remains_false(self) -> ConsistencyCheckResult:
        """Check: production_accepted must remain false"""
        for event in self.events:
            metadata = event.metadata
            if isinstance(metadata, dict) and metadata.get("production_accepted") == True:
                self.violations.append(
                    f"Event {event.event_id} has production_accepted=true"
                )
                return ConsistencyCheckResult(
                    "PROD_ACCEPTED_FALSE",
                    "Production accepted must remain false",
                    False,
                    f"Event {event.event_id} has production_accepted=true"
                )
        
        return ConsistencyCheckResult(
            "PROD_ACCEPTED_FALSE",
            "Production accepted must remain false",
            True,
            "No event has production_accepted=true"
        )

    def check_force_push_carryover(self) -> ConsistencyCheckResult:
        """Check: force_push violation remains audit carryover"""
        force_push_events = [e for e in self.events if "force_push" in str(e.metadata).lower()]
        
        if force_push_events:
            # Check if carryover is recorded
            carryover_recorded = any("carryover" in str(e.metadata).lower() for e in self.events)
            if not carryover_recorded:
                self.warnings.append(
                    f"Force push violation detected but carryover not explicitly recorded"
                )
                return ConsistencyCheckResult(
                    "FORCE_PUSH_CARRYOVER",
                    "Force push carryover recorded",
                    False,
                    "Force push violation detected but carryover not recorded"
                )
        
        return ConsistencyCheckResult(
            "FORCE_PUSH_CARRYOVER",
            "Force push carryover recorded",
            True,
            "Force push carryover properly recorded"
        )

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all consistency checks"""
        self.checks = [
            self.check_readiness_does_not_authorize_execution(),
            self.check_runtime_gate_requires_authorization(),
            self.check_blocked_tool_policy_cannot_become_allowed(),
            self.check_production_accepted_remains_false(),
            self.check_force_push_carryover()
        ]
        
        all_passed = all(check.passed for check in self.checks)
        
        return {
            "report_id": str(uuid.uuid4()),
            "task_id": self.events[0].task_id if self.events else "unknown",
            "consistent": all_passed,
            "consistency_checks": [check.to_dict() for check in self.checks],
            "violations": self.violations,
            "warnings": self.warnings,
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": {}
        }
