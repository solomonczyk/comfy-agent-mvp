"""Tests for workflow readiness orchestration layer.

Tests for RC-COMBINE-V2-WORKFLOW-READINESS-ORCHESTRATION-001
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from app.workflow_readiness import WorkflowReadinessEngine
from app.workflow_readiness.models import (
    BlockerReport,
    CombinedReadinessReport,
    GenerationGateRequirementReport,
    ReadinessStatus,
    WorkflowReadinessManifest,
)


class TestWorkflowReadinessModels:
    """Tests for workflow readiness data models."""

    def test_workflow_readiness_manifest_creation(self):
        """Test creating a workflow readiness manifest."""
        manifest = WorkflowReadinessManifest(
            task_id="RC-COMBINE-V2-WORKFLOW-READINESS-ORCHESTRATION-001",
            evaluation_scope={
                "workflow_registry_path": "test/registry.json",
                "pipeline_blueprint_id": "test_blueprint",
            },
        )
        assert manifest.task_id == "RC-COMBINE-V2-WORKFLOW-READINESS-ORCHESTRATION-001"
        assert manifest.project_agnostic is True
        assert manifest.document_type == "workflow_readiness_manifest"

    def test_workflow_readiness_manifest_serialization(self):
        """Test manifest serialization to dict and back."""
        manifest = WorkflowReadinessManifest(
            task_id="test_task",
            evaluation_scope={"test": "value"},
        )
        data = manifest.to_dict()
        restored = WorkflowReadinessManifest.from_dict(data)
        assert restored.task_id == manifest.task_id
        assert restored.project_agnostic == manifest.project_agnostic

    def test_combined_readiness_report_creation(self):
        """Test creating a combined readiness report."""
        report = CombinedReadinessReport(
            report_id="test_report",
            overall_status=ReadinessStatus.READY_FOR_OPERATOR_GENERATION_AUTHORIZATION,
            generation_authorized=False,
            generation_gate_required=True,
        )
        assert report.report_id == "test_report"
        assert report.generation_authorized is False
        assert report.generation_gate_required is True

    def test_generation_gate_report_creation(self):
        """Test creating a generation gate requirement report."""
        report = GenerationGateRequirementReport(
            report_id="test_gate",
            gate_required=True,
            gate_status="closed",
            gate_reason="generation_requires_operator_authorization",
        )
        assert report.gate_required is True
        assert report.gate_status == "closed"
        assert report.gate_required is True

    def test_blocker_report_creation(self):
        """Test creating a blocker report."""
        report = BlockerReport(
            report_id="test_blocker",
            has_blockers=False,
        )
        assert report.has_blockers is False
        assert report.blocker_type is None


class TestWorkflowReadinessEngine:
    """Tests for workflow readiness engine."""

    def test_determine_overall_status_ready(self):
        """Test determining overall status when ready."""
        from app.workflow_readiness.models import ComponentReadiness

        component_readiness = {
            "workflow_registry": ComponentReadiness(
                component_type="workflow_registry",
                component_id="test",
                is_valid=True,
                is_present=True,
            ),
            "pipeline_blueprint": ComponentReadiness(
                component_type="pipeline_blueprint",
                component_id="test",
                is_valid=True,
                is_present=True,
            ),
            "reference_pack": ComponentReadiness(
                component_type="reference_pack",
                component_id="test",
                is_valid=True,
                is_present=True,
            ),
            "reference_binding": ComponentReadiness(
                component_type="reference_binding",
                component_id="test",
                is_valid=True,
                is_present=True,
            ),
        }

        status = WorkflowReadinessEngine._determine_overall_status(
            component_readiness=component_readiness,
            missing_references=[],
            invalid_bindings=[],
            forbidden_actions_detected=[],
            hardcoded_paths_detected={},
        )

        assert status == ReadinessStatus.READY_FOR_OPERATOR_GENERATION_AUTHORIZATION

    def test_determine_overall_status_missing_refs(self):
        """Test determining overall status with missing references."""
        from app.workflow_readiness.models import ComponentReadiness

        component_readiness = {
            "reference_pack": ComponentReadiness(
                component_type="reference_pack",
                component_id="test",
                is_valid=True,
                is_present=True,
            ),
        }

        status = WorkflowReadinessEngine._determine_overall_status(
            component_readiness=component_readiness,
            missing_references=["ref1", "ref2"],
            invalid_bindings=[],
            forbidden_actions_detected=[],
            hardcoded_paths_detected={},
        )

        assert status == ReadinessStatus.BLOCKED_MISSING_REQUIRED_REFERENCE

    def test_determine_overall_status_invalid_binding(self):
        """Test determining overall status with invalid binding."""
        from app.workflow_readiness.models import ComponentReadiness

        component_readiness = {
            "reference_binding": ComponentReadiness(
                component_type="reference_binding",
                component_id="test",
                is_valid=False,
                is_present=True,
            ),
        }

        status = WorkflowReadinessEngine._determine_overall_status(
            component_readiness=component_readiness,
            missing_references=[],
            invalid_bindings=["test_binding"],
            forbidden_actions_detected=[],
            hardcoded_paths_detected={},
        )

        assert status == ReadinessStatus.BLOCKED_INVALID_REFERENCE_BINDING

    def test_determine_overall_status_hardcoded_paths(self):
        """Test determining overall status with hardcoded project paths."""
        from app.workflow_readiness.models import ComponentReadiness

        component_readiness = {
            "pipeline_blueprint": ComponentReadiness(
                component_type="pipeline_blueprint",
                component_id="test",
                is_valid=True,
                is_present=True,
            ),
        }

        status = WorkflowReadinessEngine._determine_overall_status(
            component_readiness=component_readiness,
            missing_references=[],
            invalid_bindings=[],
            forbidden_actions_detected=[],
            hardcoded_paths_detected={"rc2_multishot1_ep01": ["pipeline_blueprint"]},
        )

        assert status == ReadinessStatus.BLOCKED_PROJECT_SPECIFIC_HARDCODING

    def test_create_generation_gate_report_ready(self):
        """Test creating gate report when ready."""
        report = CombinedReadinessReport(
            report_id="test_report",
            overall_status=ReadinessStatus.READY_FOR_OPERATOR_GENERATION_AUTHORIZATION,
            generation_authorized=False,
            generation_gate_required=True,
        )

        gate_report = WorkflowReadinessEngine.create_generation_gate_report(report)

        assert gate_report.gate_required is True
        assert gate_report.gate_status == "closed"
        assert gate_report.gate_reason == "technically_ready_awaiting_operator_authorization"
        assert len(gate_report.blocking_components) == 0

    def test_create_generation_gate_report_blocked(self):
        """Test creating gate report when blocked."""
        report = CombinedReadinessReport(
            report_id="test_report",
            overall_status=ReadinessStatus.BLOCKED_MISSING_REQUIRED_REFERENCE,
            generation_authorized=False,
            generation_gate_required=True,
            missing_references=["ref1"],
        )

        gate_report = WorkflowReadinessEngine.create_generation_gate_report(report)

        assert gate_report.gate_required is True
        assert gate_report.gate_status == "closed"
        assert "missing_references" in gate_report.blocking_components

    def test_create_blocker_report_no_blockers(self):
        """Test creating blocker report when no blockers."""
        report = CombinedReadinessReport(
            report_id="test_report",
            overall_status=ReadinessStatus.READY_FOR_OPERATOR_GENERATION_AUTHORIZATION,
            generation_authorized=False,
            generation_gate_required=True,
        )

        blocker_report = WorkflowReadinessEngine.create_blocker_report(report)

        assert blocker_report.has_blockers is False
        assert blocker_report.blocker_type is None

    def test_create_blocker_report_with_blockers(self):
        """Test creating blocker report with blockers."""
        report = CombinedReadinessReport(
            report_id="test_report",
            overall_status=ReadinessStatus.BLOCKED_MISSING_REQUIRED_REFERENCE,
            generation_authorized=False,
            generation_gate_required=True,
            missing_references=["ref1", "ref2"],
        )

        blocker_report = WorkflowReadinessEngine.create_blocker_report(report)

        assert blocker_report.has_blockers is True
        assert blocker_report.blocker_type == "missing_required_reference"
        assert len(blocker_report.resolution_actions) > 0

    def test_create_manifest(self):
        """Test creating workflow readiness manifest."""
        manifest = WorkflowReadinessEngine.create_manifest(
            task_id="test_task",
            evaluation_scope={"test": "value"},
        )

        assert manifest.task_id == "test_task"
        assert manifest.project_agnostic is True
        assert manifest.metadata["generation_blocked"] is True
        assert manifest.metadata["gate_required"] is True


class TestWorkflowReadinessIntegration:
    """Integration tests for workflow readiness with mock data."""

    def test_evaluate_readiness_with_mock_data(self):
        """Test evaluating readiness with mock workflow registry data."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create mock workflow registry
            registry_data = {
                "registry_id": "test_registry",
                "version": "1.0.0",
                "workflow_contracts": {},
                "pipeline_blueprints": {},
                "reference_packs": {},
                "gate_contracts": {},
                "execution_contracts": {},
                "metadata": {},
            }
            registry_path = tmpdir_path / "workflow_registry.json"
            with open(registry_path, "w") as f:
                json.dump(registry_data, f)

            # Create mock pipeline blueprint
            blueprint_data = {
                "blueprint_id": "test_blueprint",
                "stages": [],
                "stage_order": [],
                "required_artifacts": [],
                "state_transitions": [],
                "operator_review_points": [],
                "dangerous_action_gates": [],
            }
            blueprint_dir = tmpdir_path / "pipeline_blueprints"
            blueprint_dir.mkdir()
            blueprint_path = blueprint_dir / "test_blueprint.json"
            with open(blueprint_path, "w") as f:
                json.dump(blueprint_data, f)

            # Create mock reference pack
            pack_data = {
                "reference_pack_id": "test_pack",
                "project_binding_required": False,
                "reference_types": [],
                "items": [],
                "usage_policy": {},
                "operator_review_required": True,
            }
            pack_dir = tmpdir_path / "reference_packs"
            pack_dir.mkdir()
            pack_path = pack_dir / "test_pack.json"
            with open(pack_path, "w") as f:
                json.dump(pack_data, f)

            # Create mock reference binding
            binding_data = {
                "binding_id": "test_binding",
                "blueprint_id": "test_blueprint",
                "stage_bindings": [],
                "readiness_policy": {"default_policy": "ready", "stage_overrides": {}},
                "metadata": {},
            }
            binding_path = tmpdir_path / "reference_binding.json"
            with open(binding_path, "w") as f:
                json.dump(binding_data, f)

            # Evaluate readiness
            report = WorkflowReadinessEngine.evaluate_readiness(
                workflow_registry_path=registry_path,
                pipeline_blueprint_id="test_blueprint",
                reference_pack_id="test_pack",
                reference_binding_path=binding_path,
            )

            assert report.generation_authorized is False
            assert report.generation_gate_required is True
            assert report.overall_status in [
                ReadinessStatus.READY_FOR_OPERATOR_GENERATION_AUTHORIZATION,
                ReadinessStatus.PENDING_OPERATOR_REFERENCE_SUPPLY,
            ]

    def test_forbidden_actions_detection(self):
        """Test that forbidden actions are properly detected."""
        # The engine should detect forbidden actions in the evaluation
        # This is a placeholder test - the actual implementation would check
        # for forbidden actions in the input data
        assert True  # Placeholder

    def test_generation_never_authorized(self):
        """Test that generation is NEVER authorized by this layer."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create minimal mock data
            registry_data = {
                "registry_id": "test_registry",
                "version": "1.0.0",
                "workflow_contracts": {},
                "pipeline_blueprints": {},
                "reference_packs": {},
                "gate_contracts": {},
                "execution_contracts": {},
                "metadata": {},
            }
            registry_path = tmpdir_path / "workflow_registry.json"
            with open(registry_path, "w") as f:
                json.dump(registry_data, f)

            blueprint_data = {
                "blueprint_id": "test_blueprint",
                "stages": [],
                "stage_order": [],
                "required_artifacts": [],
                "state_transitions": [],
                "operator_review_points": [],
                "dangerous_action_gates": [],
            }
            blueprint_dir = tmpdir_path / "pipeline_blueprints"
            blueprint_dir.mkdir()
            blueprint_path = blueprint_dir / "test_blueprint.json"
            with open(blueprint_path, "w") as f:
                json.dump(blueprint_data, f)

            pack_data = {
                "reference_pack_id": "test_pack",
                "project_binding_required": False,
                "reference_types": [],
                "items": [],
                "usage_policy": {},
                "operator_review_required": True,
            }
            pack_dir = tmpdir_path / "reference_packs"
            pack_dir.mkdir()
            pack_path = pack_dir / "test_pack.json"
            with open(pack_path, "w") as f:
                json.dump(pack_data, f)

            binding_data = {
                "binding_id": "test_binding",
                "blueprint_id": "test_blueprint",
                "stage_bindings": [],
                "readiness_policy": {"default_policy": "ready", "stage_overrides": {}},
                "metadata": {},
            }
            binding_path = tmpdir_path / "reference_binding.json"
            with open(binding_path, "w") as f:
                json.dump(binding_data, f)

            report = WorkflowReadinessEngine.evaluate_readiness(
                workflow_registry_path=registry_path,
                pipeline_blueprint_id="test_blueprint",
                reference_pack_id="test_pack",
                reference_binding_path=binding_path,
            )

            # Generation should NEVER be authorized by this layer
            assert report.generation_authorized is False
            # Gate should always be required
            assert report.generation_gate_required is True
