"""Agent Tool Access Matrix

Defines which agents can access which tools, with role-based permissions.
"""

from typing import Dict, List, Optional
from .models import ToolPolicy


class AgentToolAccessMatrix:
    """Matrix of agent tool access permissions"""

    # Built-in role examples as specified in requirements
    BUILTIN_ROLES = {
        "orchestrator",
        "director_agent",
        "script_supervisor_agent",
        "camera_operator_agent",
        "editor_agent",
        "sound_agent",
        "state_audit_guard_agent",
    }

    # Additional dangerous tools that should be blocked
    ADDITIONAL_DANGEROUS = {
        "image.edit": ["image", "edit", "execution"],
        "image.upscale": ["image", "upscale", "execution"],
        "visual_qa.accept": ["visual", "qa", "acceptance"],
        "operator.visual.accept": ["visual", "operator", "acceptance"],
        "state.mutate": ["state", "mutation", "destructive"],
    }

    # All dangerous tools combined (will be populated from registry)
    ALL_DANGEROUS_TOOLS = []

    # Safe read/validation tools allowed for most agents
    SAFE_TOOLS = [
        "tool_policy.validate",
        "tool_policy.inspect",
        "tool_policy.evaluate_request",
        "tool_policy.readiness_report",
        "json.read",
        "json.validate",
        "json.inspect",
        "artifact.read",
        "artifact.validate",
        "schema.validate",
        "manifest.read",
        "matrix.read",
        "registry.read",
        "report.read",
        "policy.read",
        "gate.inspect",
        "state.audit",
    ]

    def __init__(self):
        self.policies: Dict[str, ToolPolicy] = {}
        # Populate ALL_DANGEROUS_TOOLS from registry
        from .dangerous_tool_registry import DangerousToolRegistry
        registry = DangerousToolRegistry()
        AgentToolAccessMatrix.ALL_DANGEROUS_TOOLS = (
            list(registry.registry.keys()) + 
            list(self.ADDITIONAL_DANGEROUS.keys())
        )
        self._initialize_builtin_policies()

    def _initialize_builtin_policies(self):
        """Initialize built-in role policies"""
        
        # Orchestrator - can inspect and validate
        self.policies["orchestrator"] = ToolPolicy(
            agent_id="orchestrator",
            role="orchestrator",
            allowed_tools=self.SAFE_TOOLS + [
                "agent.list",
                "agent.status",
                "workflow.inspect",
            ],
            forbidden_tools=self.ALL_DANGEROUS_TOOLS,
            dangerous_actions=[],
            required_gate_types=[],
            runtime_execution_allowed=False,
            can_mutate_production_acceptance=False,
            can_force_push=False,
            description="Orchestrator can inspect and validate but cannot execute",
        )

        # Director Agent - can inspect workflows
        self.policies["director_agent"] = ToolPolicy(
            agent_id="director_agent",
            role="director_agent",
            allowed_tools=self.SAFE_TOOLS + [
                "workflow.inspect",
                "workflow.validate",
                "script.inspect",
            ],
            forbidden_tools=self.ALL_DANGEROUS_TOOLS,
            dangerous_actions=[],
            required_gate_types=[],
            runtime_execution_allowed=False,
            can_mutate_production_acceptance=False,
            can_force_push=False,
            description="Director agent can inspect workflows but cannot execute",
        )

        # Script Supervisor Agent - can inspect scripts but not submit to ComfyUI
        self.policies["script_supervisor_agent"] = ToolPolicy(
            agent_id="script_supervisor_agent",
            role="script_supervisor_agent",
            allowed_tools=self.SAFE_TOOLS + [
                "script.inspect",
                "script.validate",
                "prompt.inspect",
            ],
            forbidden_tools=self.ALL_DANGEROUS_TOOLS,
            dangerous_actions=[],
            required_gate_types=[],
            runtime_execution_allowed=False,
            can_mutate_production_acceptance=False,
            can_force_push=False,
            description="Script supervisor can inspect scripts but cannot submit to ComfyUI",
        )

        # Camera Operator Agent - can inspect but not generate without gate
        self.policies["camera_operator_agent"] = ToolPolicy(
            agent_id="camera_operator_agent",
            role="camera_operator_agent",
            allowed_tools=self.SAFE_TOOLS + [
                "camera.inspect",
                "shot.inspect",
                "frame.inspect",
            ],
            forbidden_tools=self.ALL_DANGEROUS_TOOLS,
            dangerous_actions=[],
            required_gate_types=["preview_gate", "generation_gate"],
            runtime_execution_allowed=False,
            can_mutate_production_acceptance=False,
            can_force_push=False,
            description="Camera operator can inspect but cannot generate without authorized gate",
        )

        # Editor Agent - can inspect but not preview render without gate
        self.policies["editor_agent"] = ToolPolicy(
            agent_id="editor_agent",
            role="editor_agent",
            allowed_tools=self.SAFE_TOOLS + [
                "edit.inspect",
                "timeline.inspect",
                "sequence.inspect",
            ],
            forbidden_tools=self.ALL_DANGEROUS_TOOLS,
            dangerous_actions=[],
            required_gate_types=["preview_gate"],
            runtime_execution_allowed=False,
            can_mutate_production_acceptance=False,
            can_force_push=False,
            description="Editor can inspect but cannot preview render without preview gate",
        )

        # Sound Agent - can inspect but not generate voice without gate
        self.policies["sound_agent"] = ToolPolicy(
            agent_id="sound_agent",
            role="sound_agent",
            allowed_tools=self.SAFE_TOOLS + [
                "audio.inspect",
                "sound.inspect",
                "mix.inspect",
            ],
            forbidden_tools=self.ALL_DANGEROUS_TOOLS,
            dangerous_actions=[],
            required_gate_types=["voice_gate"],
            runtime_execution_allowed=False,
            can_mutate_production_acceptance=False,
            can_force_push=False,
            description="Sound agent can inspect but cannot generate voice without voice gate",
        )

        # State Audit Guard Agent - can inspect but cannot mutate production acceptance
        self.policies["state_audit_guard_agent"] = ToolPolicy(
            agent_id="state_audit_guard_agent",
            role="state_audit_guard_agent",
            allowed_tools=self.SAFE_TOOLS + [
                "state.audit",
                "state.inspect",
                "state.validate",
                "gate.inspect",
                "artifact.validate",
            ],
            forbidden_tools=self.ALL_DANGEROUS_TOOLS,
            dangerous_actions=[],
            required_gate_types=[],
            runtime_execution_allowed=False,
            can_mutate_production_acceptance=False,
            can_force_push=False,
            description="State audit guard can inspect JSON/artifacts but cannot mutate production acceptance",
        )

    def get_policy(self, agent_id: str) -> Optional[ToolPolicy]:
        """Get policy for an agent"""
        return self.policies.get(agent_id)

    def add_policy(self, policy: ToolPolicy):
        """Add or update a policy"""
        self.policies[policy.agent_id] = policy

    def get_all_policies(self) -> Dict[str, ToolPolicy]:
        """Get all policies"""
        return self.policies.copy()

    def get_agents_by_role(self, role: str) -> List[str]:
        """Get all agents with a specific role"""
        return [agent_id for agent_id, policy in self.policies.items() if policy.role == role]

    def to_dict(self) -> Dict:
        """Export matrix as dictionary"""
        return {
            "policies": {
                agent_id: {
                    "agent_id": policy.agent_id,
                    "role": policy.role,
                    "allowed_tools": policy.allowed_tools,
                    "forbidden_tools": policy.forbidden_tools,
                    "dangerous_actions": policy.dangerous_actions,
                    "required_gate_types": policy.required_gate_types,
                    "runtime_execution_allowed": policy.runtime_execution_allowed,
                    "can_mutate_production_acceptance": policy.can_mutate_production_acceptance,
                    "can_force_push": policy.can_force_push,
                    "description": policy.description,
                }
                for agent_id, policy in self.policies.items()
            },
            "total_agents": len(self.policies),
        }
