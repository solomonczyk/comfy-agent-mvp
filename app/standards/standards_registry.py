"""Standards Registry — provides lookups and queries over the standards pack."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .standards_pack_loader import StandardsPackLoader


class StandardsRegistry:
    """Registry for querying standards by role, scope, or category."""

    def __init__(self, standards_pack_dir: str | Path) -> None:
        self.loader = StandardsPackLoader(standards_pack_dir)
        self._data: Dict[str, Any] = {}

    def load(self) -> None:
        self._data = self.loader.load_all()

    def get_role_standard(self, role_id: str) -> Dict[str, Any]:
        """Return the standard for a given role ID."""
        if not self._data:
            self.load()
        for key, artifact in self._data.get("artifacts", {}).items():
            if isinstance(artifact, dict) and artifact.get("role_id") == role_id:
                return artifact
        return {"error": f"Role standard '{role_id}' not found"}

    def get_policy(self, policy_id: str) -> Dict[str, Any]:
        """Return the policy for a given policy ID."""
        if not self._data:
            self.load()
        for key, artifact in self._data.get("artifacts", {}).items():
            if isinstance(artifact, dict) and artifact.get("policy_id") == policy_id:
                return artifact
        return {"error": f"Policy '{policy_id}' not found"}

    def get_canon(self, canon_id: str) -> Dict[str, Any]:
        """Return the quality canon for a given canon ID."""
        if not self._data:
            self.load()
        for key, artifact in self._data.get("artifacts", {}).items():
            if isinstance(artifact, dict) and artifact.get("canon_id") == canon_id:
                return artifact
        return {"error": f"Canon '{canon_id}' not found"}

    def list_roles(self) -> List[str]:
        """Return all role IDs in the standards pack."""
        if not self._data:
            self.load()
        roles = []
        for key, artifact in self._data.get("artifacts", {}).items():
            if isinstance(artifact, dict) and "role_id" in artifact:
                roles.append(artifact["role_id"])
        return sorted(roles)

    def list_policies(self) -> List[str]:
        """Return all policy IDs in the standards pack."""
        if not self._data:
            self.load()
        policies = []
        for key, artifact in self._data.get("artifacts", {}).items():
            if isinstance(artifact, dict) and "policy_id" in artifact:
                policies.append(artifact["policy_id"])
        return sorted(policies)

    def list_canons(self) -> List[str]:
        """Return all canon IDs in the standards pack."""
        if not self._data:
            self.load()
        canons = []
        for key, artifact in self._data.get("artifacts", {}).items():
            if isinstance(artifact, dict) and "canon_id" in artifact:
                canons.append(artifact["canon_id"])
        return sorted(canons)
