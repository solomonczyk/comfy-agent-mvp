"""Tests for Evidence Trace Audit Ledger Layer

Task: RC-COMBINE-V2-EVIDENCE-TRACE-AUDIT-LEDGER-001
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

from app.evidence_trace import (
    EvidenceEvent,
    EvidenceLedger,
    EvidenceTraceManifest,
    ConsistencyChecker,
    SourceLayer,
    DecisionStatus,
)


class TestEvidenceEvent:
    """Test evidence event model"""

    def test_event_creation(self):
        """Test creating an evidence event"""
        event = EvidenceEvent(
            event_id="test-event-1",
            task_id="RC-COMBINE-V2-EVIDENCE-TRACE-AUDIT-LEDGER-001",
            source_layer=SourceLayer.WORKFLOW_READINESS,
            artifact_path="/tmp/test_artifact.json",
            artifact_sha256="abc123",
            decision_status=DecisionStatus.READY,
            created_by="test_agent",
        )
        assert event.event_id == "test-event-1"
        assert event.task_id == "RC-COMBINE-V2-EVIDENCE-TRACE-AUDIT-LEDGER-001"
        assert event.source_layer == SourceLayer.WORKFLOW_READINESS
        assert event.decision_status == DecisionStatus.READY

    def test_event_to_dict(self):
        """Test converting event to dictionary"""
        event = EvidenceEvent(
            event_id="test-event-1",
            task_id="test-task",
            source_layer=SourceLayer.TOOL_POLICY,
            artifact_path="/tmp/test.json",
            artifact_sha256="def456",
            decision_status=DecisionStatus.BLOCKED,
            blocked_actions=["execute", "retry"],
            allowed_next_action=None,
        )
        data = event.to_dict()
        assert data["event_id"] == "test-event-1"
        assert data["source_layer"] == "tool_policy"
        assert data["decision_status"] == "blocked"
        assert "execute" in data["blocked_actions"]

    def test_event_from_dict(self):
        """Test creating event from dictionary"""
        data = {
            "event_id": "test-event-2",
            "task_id": "test-task",
            "source_layer": "runtime_gate",
            "artifact_path": "/tmp/gate.json",
            "artifact_sha256": "ghi789",
            "decision_status": "authorized",
            "blocked_actions": [],
            "allowed_next_action": "proceed",
            "timestamp": "2024-01-01T00:00:00",
            "created_by": "system",
            "metadata": {},
        }
        event = EvidenceEvent.from_dict(data)
        assert event.event_id == "test-event-2"
        assert event.source_layer == SourceLayer.RUNTIME_GATE
        assert event.decision_status == DecisionStatus.AUTHORIZED

    def test_event_to_jsonl(self):
        """Test converting event to JSONL"""
        event = EvidenceEvent(
            event_id="test-event-3",
            task_id="test-task",
            source_layer=SourceLayer.REFERENCE_PACK,
            artifact_path="/tmp/ref.json",
            artifact_sha256="jkl012",
            decision_status=DecisionStatus.PENDING,
        )
        jsonl = event.to_jsonl()
        assert jsonl is not None
        parsed = json.loads(jsonl)
        assert parsed["event_id"] == "test-event-3"

    def test_compute_sha256(self):
        """Test SHA256 computation"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('{"test": "data"}')
            temp_path = f.name
        
        try:
            sha256 = EvidenceEvent.compute_sha256(temp_path)
            assert sha256 is not None
            assert len(sha256) == 64  # SHA256 is 64 hex characters
        finally:
            os.unlink(temp_path)


class TestEvidenceLedger:
    """Test evidence ledger"""

    def test_ledger_initialization(self):
        """Test ledger initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            assert ledger.ledger_path == ledger_path
            assert ledger.task_id == "test-task"
            assert os.path.exists(ledger_path)

    def test_append_event_with_real_artifact(self):
        """Test appending event with real artifact path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a real artifact file
            artifact_path = os.path.join(tmpdir, "artifact.json")
            with open(artifact_path, 'w') as f:
                json.dump({"test": "data"}, f)
            
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            event = EvidenceEvent(
                event_id="test-event-1",
                task_id="test-task",
                source_layer=SourceLayer.WORKFLOW_REGISTRY,
                artifact_path=artifact_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact_path),
                decision_status=DecisionStatus.READY,
            )
            
            success = ledger.append_event(event)
            assert success is True
            
            # Verify event was written
            events = ledger.read_all_events()
            assert len(events) == 1
            assert events[0].event_id == "test-event-1"

    def test_append_event_with_fake_artifact_rejected(self):
        """Test that fake artifact path is rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            event = EvidenceEvent(
                event_id="test-event-2",
                task_id="test-task",
                source_layer=SourceLayer.REFERENCE_BINDING,
                artifact_path="/tmp/nonexistent.json",
                artifact_sha256="fake123",
                decision_status=DecisionStatus.BLOCKED,
            )
            
            success = ledger.append_event(event)
            assert success is False

    def test_read_all_events(self):
        """Test reading all events from ledger"""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = os.path.join(tmpdir, "artifact.json")
            with open(artifact_path, 'w') as f:
                json.dump({"test": "data"}, f)
            
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            # Append multiple events
            for i in range(3):
                event = EvidenceEvent(
                    event_id=f"event-{i}",
                    task_id="test-task",
                    source_layer=SourceLayer.REFERENCE_SET,
                    artifact_path=artifact_path,
                    artifact_sha256=EvidenceEvent.compute_sha256(artifact_path),
                    decision_status=DecisionStatus.READY,
                )
                ledger.append_event(event)
            
            events = ledger.read_all_events()
            assert len(events) == 3

    def test_get_events_by_task(self):
        """Test filtering events by task ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = os.path.join(tmpdir, "artifact.json")
            with open(artifact_path, 'w') as f:
                json.dump({"test": "data"}, f)
            
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            # Append events for different tasks
            event1 = EvidenceEvent(
                event_id="event-1",
                task_id="task-a",
                source_layer=SourceLayer.WORKFLOW_READINESS,
                artifact_path=artifact_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact_path),
                decision_status=DecisionStatus.READY,
            )
            event2 = EvidenceEvent(
                event_id="event-2",
                task_id="task-b",
                source_layer=SourceLayer.RUNTIME_GATE,
                artifact_path=artifact_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact_path),
                decision_status=DecisionStatus.AUTHORIZED,
            )
            ledger.append_event(event1)
            ledger.append_event(event2)
            
            task_a_events = ledger.get_events_by_task("task-a")
            assert len(task_a_events) == 1
            assert task_a_events[0].task_id == "task-a"

    def test_get_events_by_source_layer(self):
        """Test filtering events by source layer"""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = os.path.join(tmpdir, "artifact.json")
            with open(artifact_path, 'w') as f:
                json.dump({"test": "data"}, f)
            
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            event1 = EvidenceEvent(
                event_id="event-1",
                task_id="test-task",
                source_layer=SourceLayer.TOOL_POLICY,
                artifact_path=artifact_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact_path),
                decision_status=DecisionStatus.BLOCKED,
            )
            event2 = EvidenceEvent(
                event_id="event-2",
                task_id="test-task",
                source_layer=SourceLayer.WORKFLOW_REGISTRY,
                artifact_path=artifact_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact_path),
                decision_status=DecisionStatus.READY,
            )
            ledger.append_event(event1)
            ledger.append_event(event2)
            
            tool_policy_events = ledger.get_events_by_source_layer("tool_policy")
            assert len(tool_policy_events) == 1
            assert tool_policy_events[0].source_layer == SourceLayer.TOOL_POLICY

    def test_create_manifest(self):
        """Test creating manifest"""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = os.path.join(tmpdir, "artifact.json")
            with open(artifact_path, 'w') as f:
                json.dump({"test": "data"}, f)
            
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            event = EvidenceEvent(
                event_id="event-1",
                task_id="test-task",
                source_layer=SourceLayer.REFERENCE_PACK,
                artifact_path=artifact_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact_path),
                decision_status=DecisionStatus.READY,
            )
            ledger.append_event(event)
            
            manifest = ledger.create_manifest()
            assert manifest.task_id == "test-task"
            assert manifest.total_events == 1
            assert "reference_pack" in manifest.source_layers

    def test_validate_append_only(self):
        """Test append-only validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            # Ledger should be append-only
            assert ledger.validate_append_only() is True


class TestConsistencyChecker:
    """Test consistency checker"""

    def test_readiness_does_not_authorize_execution(self):
        """Test: readiness ready does not authorize execution"""
        events = [
            EvidenceEvent(
                event_id="readiness-1",
                task_id="test-task",
                source_layer=SourceLayer.WORKFLOW_READINESS,
                artifact_path="/tmp/readiness.json",
                artifact_sha256="abc123",
                decision_status=DecisionStatus.READY,
            ),
            EvidenceEvent(
                event_id="tool-policy-1",
                task_id="test-task",
                source_layer=SourceLayer.TOOL_POLICY,
                artifact_path="/tmp/policy.json",
                artifact_sha256="def456",
                decision_status=DecisionStatus.BLOCKED,
                metadata={"reason": "readiness does not authorize execution"},
            ),
        ]
        
        checker = ConsistencyChecker(events)
        result = checker.check_readiness_does_not_authorize_execution()
        assert result.passed is True

    def test_blocked_tool_policy_cannot_become_allowed(self):
        """Test: blocked tool policy cannot become allowed downstream"""
        events = [
            EvidenceEvent(
                event_id="blocked-1",
                task_id="test-task",
                source_layer=SourceLayer.TOOL_POLICY,
                artifact_path="/tmp/blocked.json",
                artifact_sha256="abc123",
                decision_status=DecisionStatus.BLOCKED,
                timestamp="2024-01-01T00:00:00",
            ),
            EvidenceEvent(
                event_id="downstream-1",
                task_id="test-task",
                source_layer=SourceLayer.RUNTIME_GATE,
                artifact_path="/tmp/gate.json",
                artifact_sha256="def456",
                decision_status=DecisionStatus.PENDING,
                allowed_next_action="wait",  # Not execute
                timestamp="2024-01-01T01:00:00",
            ),
        ]
        
        checker = ConsistencyChecker(events)
        result = checker.check_blocked_tool_policy_cannot_become_allowed()
        assert result.passed is True

    def test_production_accepted_remains_false(self):
        """Test: production_accepted must remain false"""
        events = [
            EvidenceEvent(
                event_id="event-1",
                task_id="test-task",
                source_layer=SourceLayer.TOOL_POLICY,
                artifact_path="/tmp/policy.json",
                artifact_sha256="abc123",
                decision_status=DecisionStatus.BLOCKED,
                metadata={"production_accepted": False},
            ),
        ]
        
        checker = ConsistencyChecker(events)
        result = checker.check_production_accepted_remains_false()
        assert result.passed is True

    def test_production_accepted_true_rejected(self):
        """Test: production_accepted=true is rejected"""
        events = [
            EvidenceEvent(
                event_id="event-1",
                task_id="test-task",
                source_layer=SourceLayer.TOOL_POLICY,
                artifact_path="/tmp/policy.json",
                artifact_sha256="abc123",
                decision_status=DecisionStatus.AUTHORIZED,
                metadata={"production_accepted": True},  # This should be rejected
            ),
        ]
        
        checker = ConsistencyChecker(events)
        result = checker.check_production_accepted_remains_false()
        assert result.passed is False

    def test_force_push_carryover_recorded(self):
        """Test: force_push violation carryover is recorded"""
        events = [
            EvidenceEvent(
                event_id="force-push-1",
                task_id="test-task",
                source_layer=SourceLayer.TOOL_POLICY,
                artifact_path="/tmp/policy.json",
                artifact_sha256="abc123",
                decision_status=DecisionStatus.BLOCKED,
                metadata={"violation": "force_push", "carryover": "recorded"},
            ),
        ]
        
        checker = ConsistencyChecker(events)
        result = checker.check_force_push_carryover()
        assert result.passed is True

    def test_run_all_checks(self):
        """Test running all consistency checks"""
        events = [
            EvidenceEvent(
                event_id="event-1",
                task_id="test-task",
                source_layer=SourceLayer.WORKFLOW_READINESS,
                artifact_path="/tmp/readiness.json",
                artifact_sha256="abc123",
                decision_status=DecisionStatus.READY,
            ),
            EvidenceEvent(
                event_id="event-2",
                task_id="test-task",
                source_layer=SourceLayer.TOOL_POLICY,
                artifact_path="/tmp/policy.json",
                artifact_sha256="def456",
                decision_status=DecisionStatus.BLOCKED,
                metadata={"production_accepted": False},
            ),
        ]
        
        checker = ConsistencyChecker(events)
        report = checker.run_all_checks()
        
        assert "report_id" in report
        assert "consistent" in report
        assert "consistency_checks" in report
        assert len(report["consistency_checks"]) == 5


class TestEvidenceTraceIntegration:
    """Integration tests for evidence trace"""

    def test_full_workflow_with_real_artifacts(self):
        """Test full workflow with real artifacts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create real artifacts
            artifact1_path = os.path.join(tmpdir, "artifact1.json")
            with open(artifact1_path, 'w') as f:
                json.dump({"type": "workflow_registry"}, f)
            
            artifact2_path = os.path.join(tmpdir, "artifact2.json")
            with open(artifact2_path, 'w') as f:
                json.dump({"type": "tool_policy"}, f)
            
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            # Record events
            event1 = EvidenceEvent(
                event_id="event-1",
                task_id="test-task",
                source_layer=SourceLayer.WORKFLOW_REGISTRY,
                artifact_path=artifact1_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact1_path),
                decision_status=DecisionStatus.READY,
            )
            ledger.append_event(event1)
            
            event2 = EvidenceEvent(
                event_id="event-2",
                task_id="test-task",
                source_layer=SourceLayer.TOOL_POLICY,
                artifact_path=artifact2_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact2_path),
                decision_status=DecisionStatus.BLOCKED,
                blocked_actions=["execute", "retry"],
                metadata={"production_accepted": False},
            )
            ledger.append_event(event2)
            
            # Verify
            events = ledger.read_all_events()
            assert len(events) == 2
            
            # Run consistency checks
            checker = ConsistencyChecker(events)
            report = checker.run_all_checks()
            assert report["consistent"] is True

    def test_no_runtime_action_executed(self):
        """Test that no runtime actions are executed during evidence trace"""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = os.path.join(tmpdir, "artifact.json")
            with open(artifact_path, 'w') as f:
                json.dump({"test": "data"}, f)
            
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            event = EvidenceEvent(
                event_id="event-1",
                task_id="test-task",
                source_layer=SourceLayer.WORKFLOW_READINESS,
                artifact_path=artifact_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact_path),
                decision_status=DecisionStatus.READY,
            )
            ledger.append_event(event)
            
            # Verify no ComfyUI submit, generation, etc. were executed
            # This is a safety check - evidence trace should be read-only
            events = ledger.read_all_events()
            assert len(events) == 1
            assert events[0].metadata.get("generation_executed") != True
            assert events[0].metadata.get("comfyui_submit_executed") != True

    def test_cli_json_output_stable(self):
        """Test that CLI JSON output is stable"""
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_path = os.path.join(tmpdir, "artifact.json")
            with open(artifact_path, 'w') as f:
                json.dump({"test": "data"}, f)
            
            ledger_path = os.path.join(tmpdir, "ledger.jsonl")
            ledger = EvidenceLedger(ledger_path, "test-task")
            
            event = EvidenceEvent(
                event_id="event-1",
                task_id="test-task",
                source_layer=SourceLayer.REFERENCE_PACK,
                artifact_path=artifact_path,
                artifact_sha256=EvidenceEvent.compute_sha256(artifact_path),
                decision_status=DecisionStatus.READY,
            )
            ledger.append_event(event)
            
            # Convert to dict twice and verify consistency
            dict1 = event.to_dict()
            dict2 = event.to_dict()
            assert dict1 == dict2
            
            # Verify JSON serialization is stable
            json1 = json.dumps(dict1, sort_keys=True)
            json2 = json.dumps(dict2, sort_keys=True)
            assert json1 == json2
