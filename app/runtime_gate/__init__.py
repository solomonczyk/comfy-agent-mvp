"""Runtime Gate Authorization Control Layer.

Project-agnostic layer that converts readiness decisions into closed runtime gate packets.
Core rule: readiness=ready does NOT mean execution_allowed=true.
Readiness only creates pending_operator_authorization.

This layer does NOT execute runtime actions.
It only creates, validates, and inspects gate packets.
"""

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

__all__ = [
    "AuthorizationPolicy",
    "AuthorizationStatus",
    "GateSafetyReport",
    "GateType",
    "GateTypeConfig",
    "GateTypeRegistry",
    "RuntimeGateManifest",
    "RuntimeGatePacket",
    "SafetyCheck",
    "SafetyRule",
]
