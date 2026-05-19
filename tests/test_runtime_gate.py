"""Tests for runtime gate authorization control layer.

Task: RC-COMBINE-V2-RUNTIME-GATE-AUTHORIZATION-CONTROL-001
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.runtime_gate.builder import RuntimeGateBuilder
from app.runtime_gate.inspector import RuntimeGateInspector
from app.runtime_gate.models import (
    AuthorizationPolicy,
    AuthorizationStatus,
    GateSafetyReport,
    GateType,
    GateTypeConfig,
    GateTypeRegistry,
    RuntimeGateManifest,
    RuntimeGatePacket,
    SafetyCheck,
    SafetyRule,
)
from app.runtime_gate.validator import RuntimeGateValidator


class TestRuntimeGateModels:
    """Test runtime gate data models."""

    def test_runtime_gate_packet_default_values(self):
        """Test that runtime gate packet has safe default values."""
        packet = RuntimeGatePacket(
            gate_id="test-gate-id",
            gate_type=GateType.GENERATION_GATE,
            target_action="test_action",
            required_readiness_status="ready",
        )

        # CRITICAL: These must be false by default
        assert packet.execution_allowed is False
        assert packet.generation_authorized is False
        assert packet.production_accepted is False
        assert packet.force_push_used is False

        # Authorization status must be pending
        assert packet.authorization_status == AuthorizationStatus.PENDING_OPERATOR_AUTHORIZATION
        assert packet.operator_authorization_required is True

    def test_runtime_gate_packet_to_dict_roundtrip(self):
        """Test that packet can be serialized and deserialized."""
        original = RuntimeGatePacket(
            gate_id="test-gate-id",
            gate_type=GateType.GENERATION_GATE,
            target_action="test_action",
            required_readiness_status="ready",
        )

        data = original.to_dict()
        restored = RuntimeGatePacket.from_dict(data)

        assert restored.gate_id == original.gate_id
        assert restored.gate_type == original.gate_type
        assert restored.execution_allowed is False
        assert restored.generation_authorized is False
        assert restored.production_accepted is False

    def test_runtime_gate_manifest_project_agnostic(self):
        """Test that manifest is project-agnostic."""
        manifest = RuntimeGateManifest(
            task_id="test-task",
        )

        assert manifest.project_agnostic is True
        assert manifest.gate_layer_active is True
        assert manifest.document_type == "runtime_gate_manifest"

    def test_gate_type_enum_values(self):
        """Test that all required gate types exist."""
        assert GateType.GENERATION_GATE.value == "generation_gate"
        assert GateType.RETRY_GATE.value == "retry_gate"
        assert GateType.PREVIEW_RENDER_GATE.value == "preview_render_gate"
        assert GateType.VOICE_GENERATION_GATE.value == "voice_generation_gate"
        assert GateType.ASSEMBLY_GATE.value == "assembly_gate"
        assert GateType.FINAL_RENDER_GATE.value == "final_render_gate"
        assert GateType.ASSET_ACQUISITION_GATE.value == "asset_acquisition_gate"
        assert GateType.EXTERNAL_API_CALL_GATE.value == "external_api_call_gate"


class TestRuntimeGateBuilder:
    """Test runtime gate builder."""

    def test_build_manifest(self):
        """Test manifest building."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            manifest = builder.build_manifest()

            assert manifest.task_id == "RC-COMBINE-V2-RUNTIME-GATE-AUTHORIZATION-CONTROL-001"
            assert manifest.project_agnostic is True
            assert manifest.gate_layer_active is True
            assert len(manifest.supported_gate_types) == 8

    def test_build_gate_type_registry(self):
        """Test gate type registry building."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            registry = builder.build_gate_type_registry()

            assert len(registry.gate_types) == 8
            assert "generation_gate" in registry.gate_types
            assert registry.gate_types["generation_gate"].operator_authorization_required is True
            assert registry.gate_types["generation_gate"].dangerous_action is True

    def test_build_authorization_policy(self):
        """Test authorization policy building."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            policy = builder.build_authorization_policy()

            assert len(policy.safety_rules) > 0
            assert policy.core_rule == "readiness=ready does NOT mean execution_allowed=true. Readiness only creates pending_operator_authorization."
            assert len(policy.forbidden_patterns) > 0
            assert "rc2_multishot1_ep01" in policy.forbidden_patterns

    def test_build_gate_packet_creates_pending_authorization(self):
        """Test that building a gate packet creates pending authorization, NOT authorization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            packet = builder.build_gate_packet(
                gate_type=GateType.GENERATION_GATE,
                target_action="test_generation",
            )

            # CRITICAL: Readiness does NOT authorize execution
            assert packet.authorization_status == AuthorizationStatus.PENDING_OPERATOR_AUTHORIZATION
            assert packet.execution_allowed is False
            assert packet.generation_authorized is False
            assert packet.production_accepted is False

    def test_build_gate_packet_max_executions_default(self):
        """Test that generation gate has max_executions=1 by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            packet = builder.build_gate_packet(
                gate_type=GateType.GENERATION_GATE,
                target_action="test_generation",
            )

            assert packet.max_executions == 1
            assert packet.current_execution_count == 0

    def test_build_retry_gate_requires_corrective_plan(self):
        """Test that retry gate requires corrective plan reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            
            # Without corrective plan - should still build packet
            packet = builder.build_gate_packet(
                gate_type=GateType.RETRY_GATE,
                target_action="test_retry",
            )
            assert packet.corrective_plan_reference is None

            # With corrective plan
            packet_with_plan = builder.build_gate_packet(
                gate_type=GateType.RETRY_GATE,
                target_action="test_retry",
                corrective_plan_reference="corrective_plan_001.json",
            )
            assert packet_with_plan.corrective_plan_reference == "corrective_plan_001.json"

    def test_build_safety_report_detects_violations(self):
        """Test that safety report detects unsafe configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            
            # Safe packet
            safe_packet = RuntimeGatePacket(
                gate_id="safe-gate",
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                required_readiness_status="ready",
                execution_allowed=False,
                generation_authorized=False,
                production_accepted=False,
            )
            safe_report = builder.build_safety_report(safe_packet)
            assert safe_report.safe is True

            # Unsafe packet - execution_allowed true
            unsafe_packet = RuntimeGatePacket(
                gate_id="unsafe-gate",
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                required_readiness_status="ready",
                execution_allowed=True,  # VIOLATION
                generation_authorized=False,
                production_accepted=False,
            )
            unsafe_report = builder.build_safety_report(unsafe_packet)
            assert unsafe_report.safe is False
            assert "execution_allowed must be false" in unsafe_report.violations

    def test_check_hardcoding_detects_project_specific_patterns(self):
        """Test that hardcoding check detects project-specific patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a readiness report with hardcoding
            readiness_path = Path(tmpdir) / "readiness_report.json"
            with open(readiness_path, "w") as f:
                json.dump({
                    "overall_status": "ready",
                    "hardcoded_paths_detected": {
                        "rc2_multishot1_ep01": ["found in config"]
                    }
                }, f)

            builder = RuntimeGateBuilder(Path(tmpdir))
            packet = builder.build_gate_packet(
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                readiness_report_path=readiness_path,
            )

            assert len(packet.project_specific_hardcoding_detected) > 0
            assert packet.authorization_status == AuthorizationStatus.BLOCKED


class TestRuntimeGateValidator:
    """Test runtime gate validator."""

    def test_validate_packet_rejects_execution_allowed_true(self):
        """Test that validator rejects execution_allowed=true."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = RuntimeGateValidator(Path(tmpdir))
            policy = AuthorizationPolicy(policy_id="test", version="1.0.0")

            # Unsafe packet
            packet = RuntimeGatePacket(
                gate_id="test",
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                required_readiness_status="ready",
                execution_allowed=True,  # VIOLATION
            )

            errors = validator.validate_packet(packet, policy)
            assert "execution_allowed must be false" in errors

    def test_validate_packet_rejects_generation_authorized_true(self):
        """Test that validator rejects generation_authorized=true."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = RuntimeGateValidator(Path(tmpdir))
            policy = AuthorizationPolicy(policy_id="test", version="1.0.0")

            packet = RuntimeGatePacket(
                gate_id="test",
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                required_readiness_status="ready",
                generation_authorized=True,  # VIOLATION
            )

            errors = validator.validate_packet(packet, policy)
            assert "generation_authorized must be false" in errors

    def test_validate_packet_rejects_production_accepted_true(self):
        """Test that validator rejects production_accepted=true."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = RuntimeGateValidator(Path(tmpdir))
            policy = AuthorizationPolicy(policy_id="test", version="1.0.0")

            packet = RuntimeGatePacket(
                gate_id="test",
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                required_readiness_status="ready",
                production_accepted=True,  # VIOLATION
            )

            errors = validator.validate_packet(packet, policy)
            assert "production_accepted must be false" in errors

    def test_validate_packet_rejects_force_push_used_true(self):
        """Test that validator rejects force_push_used=true."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = RuntimeGateValidator(Path(tmpdir))
            policy = AuthorizationPolicy(policy_id="test", version="1.0.0")

            packet = RuntimeGatePacket(
                gate_id="test",
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                required_readiness_status="ready",
                force_push_used=True,  # VIOLATION
            )

            errors = validator.validate_packet(packet, policy)
            assert "force_push_used must be false" in errors

    def test_validate_retry_gate_requires_corrective_plan(self):
        """Test that retry gate validation requires corrective plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = RuntimeGateValidator(Path(tmpdir))
            policy = AuthorizationPolicy(policy_id="test", version="1.0.0")

            packet = RuntimeGatePacket(
                gate_id="test",
                gate_type=GateType.RETRY_GATE,
                target_action="test",
                required_readiness_status="ready",
                corrective_plan_reference=None,  # Missing corrective plan
            )

            errors = validator.validate_packet(packet, policy)
            assert "retry_gate requires corrective_plan_reference" in errors

    def test_validate_file(self):
        """Test file validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            validator = RuntimeGateValidator(Path(tmpdir))
            
            # Create a valid packet file
            packet_path = Path(tmpdir) / "packet.json"
            packet = RuntimeGatePacket(
                gate_id="test",
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                required_readiness_status="ready",
            )
            with open(packet_path, "w") as f:
                json.dump(packet.to_dict(), f)

            result = validator.validate_file(packet_path)
            assert result["valid"] is True

    def test_validate_all(self):
        """Test validation of all artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            builder.write_artifacts()

            validator = RuntimeGateValidator(Path(tmpdir))
            result = validator.validate_all()

            assert result["overall_valid"] is True
            assert "manifest" in result["results"]
            assert "registry" in result["results"]
            assert "policy" in result["results"]


class TestRuntimeGateInspector:
    """Test runtime gate inspector."""

    def test_inspect_packet(self):
        """Test packet inspection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            inspector = RuntimeGateInspector(Path(tmpdir))
            
            packet = RuntimeGatePacket(
                gate_id="test",
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                required_readiness_status="ready",
            )

            result = inspector.inspect_packet(packet)
            assert result["gate_id"] == "test"
            assert result["gate_type"] == "generation_gate"
            assert result["execution_allowed"] is False
            assert result["generation_authorized"] is False

    def test_inspect_all(self):
        """Test inspection of all artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            builder.write_artifacts()

            inspector = RuntimeGateInspector(Path(tmpdir))
            result = inspector.inspect_all()

            assert "manifest" in result
            assert "registry" in result
            assert "policy" in result
            assert "error" not in result["manifest"]
            assert "error" not in result["registry"]
            assert "error" not in result["policy"]

    def test_generate_readiness_report(self):
        """Test readiness report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            builder.write_artifacts()

            inspector = RuntimeGateInspector(Path(tmpdir))
            report = inspector.generate_readiness_report()

            assert report["overall_ready"] is True
            assert report["manifest_valid"] is True
            assert report["registry_valid"] is True
            assert report["policy_valid"] is True


class TestSafetyRules:
    """Test safety rules enforcement."""

    def test_cli_cannot_create_fake_operator_authorization(self):
        """Test that CLI cannot create fake operator authorization."""
        # The builder only creates pending_operator_authorization status
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            packet = builder.build_gate_packet(
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
            )

            # CLI cannot set authorization to authorized_not_executed
            assert packet.authorization_status != AuthorizationStatus.AUTHORIZED_NOT_EXECUTED
            assert packet.authorization_status == AuthorizationStatus.PENDING_OPERATOR_AUTHORIZATION

    def test_production_accepted_cannot_be_set(self):
        """Test that production_accepted cannot be set to true."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            packet = builder.build_gate_packet(
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
            )

            # production_accepted is always false
            assert packet.production_accepted is False
            
            # Even if we try to create a packet with it true, validator will reject
            validator = RuntimeGateValidator(Path(tmpdir))
            policy = AuthorizationPolicy(policy_id="test", version="1.0.0")
            
            unsafe_packet = RuntimeGatePacket(
                gate_id="test",
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
                required_readiness_status="ready",
                production_accepted=True,  # Trying to set it true
            )
            
            errors = validator.validate_packet(unsafe_packet, policy)
            assert "production_accepted must be false" in errors

    def test_rc2_multishot1_ep01_hardcoding_rejected(self):
        """Test that rc2_multishot1_ep01 hardcoding is rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            policy = builder.build_authorization_policy()

            assert "rc2_multishot1_ep01" in policy.forbidden_patterns
            assert "rc2_multishot1_ep01" in policy.hardcoded_paths_blocked

    def test_readiness_ready_creates_pending_gate_not_authorized(self):
        """Test that readiness=ready creates pending gate, not authorized gate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = RuntimeGateBuilder(Path(tmpdir))
            
            # Simulate ready status
            packet = builder.build_gate_packet(
                gate_type=GateType.GENERATION_GATE,
                target_action="test",
            )

            # CRITICAL: Ready does NOT mean authorized
            assert packet.authorization_status == AuthorizationStatus.PENDING_OPERATOR_AUTHORIZATION
            assert packet.authorization_status != AuthorizationStatus.AUTHORIZED_NOT_EXECUTED
            assert packet.execution_allowed is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
