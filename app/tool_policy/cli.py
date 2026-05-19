"""Tool Policy CLI Commands

Provides CLI commands for tool policy validation and inspection.
"""

import json
import sys
from pathlib import Path
from typing import Optional
from .models import ToolRequest
from .decision_engine import DecisionEngine
from .dangerous_tool_registry import DangerousToolRegistry
from .agent_tool_access_matrix import AgentToolAccessMatrix


def combine_tool_policy_validate(policy_root: str, json_output: bool = False):
    """Validate tool policy configuration"""
    policy_path = Path(policy_root)
    
    if not policy_path.exists():
        result = {
            "valid": False,
            "error": f"Policy root does not exist: {policy_root}",
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"ERROR: {result['error']}")
        return False
    
    # Check for required artifacts
    required_files = [
        "tool_policy_manifest.json",
        "agent_tool_access_matrix.json",
        "dangerous_tool_registry.json",
    ]
    
    missing_files = []
    for file_name in required_files:
        file_path = policy_path / file_name
        if not file_path.exists():
            missing_files.append(file_name)
    
    if missing_files:
        result = {
            "valid": False,
            "error": "Missing required files",
            "missing_files": missing_files,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"ERROR: {result['error']}")
            print(f"Missing files: {', '.join(missing_files)}")
        return False
    
    # Validate JSON structure
    errors = []
    for file_name in required_files:
        file_path = policy_path / file_name
        try:
            with open(file_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{file_name}: {str(e)}")
    
    if errors:
        result = {
            "valid": False,
            "error": "Invalid JSON in files",
            "errors": errors,
        }
        if json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"ERROR: {result['error']}")
            for error in errors:
                print(f"  - {error}")
        return False
    
    result = {
        "valid": True,
        "message": "Tool policy configuration is valid",
        "policy_root": str(policy_path),
        "checked_files": required_files,
    }
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"SUCCESS: {result['message']}")
        print(f"Policy root: {result['policy_root']}")
        print(f"Checked files: {', '.join(result['checked_files'])}")
    
    return True


def combine_tool_policy_inspect(policy_root: str, json_output: bool = False):
    """Inspect tool policy configuration"""
    policy_path = Path(policy_root)
    
    # Load dangerous tool registry
    registry = DangerousToolRegistry()
    
    # Load agent tool access matrix
    matrix = AgentToolAccessMatrix()
    
    result = {
        "policy_root": str(policy_path),
        "dangerous_tools": registry.to_dict(),
        "agent_policies": matrix.to_dict(),
    }
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Policy Root: {result['policy_root']}")
        print(f"\nDangerous Tools ({registry.to_dict()['total_count']}):")
        for tool, categories in registry.registry.items():
            print(f"  - {tool}: {', '.join(categories)}")
        
        print(f"\nAgent Policies ({matrix.to_dict()['total_agents']}):")
        for agent_id, policy_data in matrix.to_dict()['policies'].items():
            print(f"  - {agent_id} ({policy_data['role']}):")
            print(f"    Allowed: {len(policy_data['allowed_tools'])} tools")
            print(f"    Forbidden: {len(policy_data['forbidden_tools'])} tools")
            print(f"    Runtime execution: {policy_data['runtime_execution_allowed']}")


def combine_tool_policy_evaluate_request(
    policy_root: str,
    agent_id: str,
    tool: str,
    action: str,
    target_stage: Optional[str] = None,
    gate_reference: Optional[str] = None,
    json_output: bool = False,
):
    """Evaluate a tool request against policy"""
    # Initialize components
    registry = DangerousToolRegistry()
    matrix = AgentToolAccessMatrix()
    engine = DecisionEngine(matrix, registry)
    
    # Create request
    request = ToolRequest(
        requester_agent_id=agent_id,
        requested_tool=tool,
        requested_action=action,
        target_stage=target_stage,
        gate_packet_reference=gate_reference,
    )
    
    # Evaluate
    decision = engine.evaluate(request)
    
    result = {
        "request": {
            "agent_id": request.requester_agent_id,
            "tool": request.requested_tool,
            "action": request.requested_action,
            "target_stage": request.target_stage,
            "gate_reference": request.gate_packet_reference,
        },
        "decision": {
            "status": decision.status.value,
            "allowed": decision.allowed,
            "reason": decision.reason,
            "policy_role": decision.policy_applied.role,
            "missing_gates": decision.missing_gates,
            "dangerous_categories": decision.dangerous_categories,
        },
    }
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Request Evaluation:")
        print(f"  Agent: {result['request']['agent_id']}")
        print(f"  Tool: {result['request']['tool']}")
        print(f"  Action: {result['request']['action']}")
        print(f"\nDecision:")
        print(f"  Status: {result['decision']['status']}")
        print(f"  Allowed: {result['decision']['allowed']}")
        print(f"  Reason: {result['decision']['reason']}")
        if result['decision']['missing_gates']:
            print(f"  Missing Gates: {', '.join(result['decision']['missing_gates'])}")
        if result['decision']['dangerous_categories']:
            print(f"  Dangerous Categories: {', '.join(result['decision']['dangerous_categories'])}")


def combine_tool_policy_readiness_report(policy_root: str, json_output: bool = False):
    """Generate tool policy readiness report"""
    registry = DangerousToolRegistry()
    matrix = AgentToolAccessMatrix()
    
    # Check each agent's policy
    agent_readiness = []
    for agent_id, policy in matrix.get_all_policies().items():
        issues = []
        
        # Check if runtime execution is disabled (should be false for project-agnostic)
        if policy.runtime_execution_allowed:
            issues.append("Runtime execution is allowed (should be false for project-agnostic)")
        
        # Check if production acceptance mutation is allowed (should be false)
        if policy.can_mutate_production_acceptance:
            issues.append("Production acceptance mutation is allowed (should be false)")
        
        # Check if force push is allowed (should be false)
        if policy.can_force_push:
            issues.append("Force push is allowed (should be false)")
        
        # Check if dangerous tools are in forbidden list
        dangerous_tools = registry.get_all_dangerous_tools()
        missing_dangerous = [dt for dt in dangerous_tools if dt not in policy.forbidden_tools]
        if missing_dangerous:
            issues.append(f"Missing dangerous tools in forbidden list: {', '.join(missing_dangerous)}")
        
        agent_readiness.append({
            "agent_id": agent_id,
            "role": policy.role,
            "ready": len(issues) == 0,
            "issues": issues,
        })
    
    overall_ready = all(agent["ready"] for agent in agent_readiness)
    
    result = {
        "overall_ready": overall_ready,
        "policy_root": policy_root,
        "total_agents": len(agent_readiness),
        "ready_agents": sum(1 for a in agent_readiness if a["ready"]),
        "agent_readiness": agent_readiness,
        "dangerous_tools_count": len(registry.get_all_dangerous_tools()),
    }
    
    if json_output:
        print(json.dumps(result, indent=2))
    else:
        print(f"Tool Policy Readiness Report")
        print(f"Overall Ready: {result['overall_ready']}")
        print(f"Policy Root: {result['policy_root']}")
        print(f"Total Agents: {result['total_agents']}")
        print(f"Ready Agents: {result['ready_agents']}")
        print(f"Dangerous Tools: {result['dangerous_tools_count']}")
        print(f"\nAgent Readiness:")
        for agent in agent_readiness:
            status = "✓" if agent["ready"] else "✗"
            print(f"  {status} {agent['agent_id']} ({agent['role']})")
            if agent["issues"]:
                for issue in agent["issues"]:
                    print(f"    - {issue}")
