"""MK-OBS1.2 — Workflow Diff for comparing template vs effective workflows.

Compares workflow_template.json against effective_workflow.json
to identify exactly what fields were changed during generation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class WorkflowDiff:
    """Compares workflow template against effective workflow."""

    def __init__(self, template: dict[str, Any], effective: dict[str, Any]) -> None:
        """
        Initialize diff with template and effective workflows.

        Args:
            template: Original workflow template
            effective: Effective workflow with injected values
        """
        self.template = template
        self.effective = effective

    def compute_diff(self) -> dict[str, Any]:
        """
        Compute differences between template and effective workflow.

        Returns:
            Dictionary with changed fields
        """
        changed = []
        template_nodes = {k: v for k, v in self.template.items() if k != "__inject__"}
        effective_nodes = {k: v for k, v in self.effective.items() if k != "__inject__"}

        # Find all node IDs present in either workflow
        all_node_ids = set(template_nodes.keys()) | set(effective_nodes.keys())

        for node_id in sorted(all_node_ids):
            template_node = template_nodes.get(node_id)
            effective_node = effective_nodes.get(node_id)

            if template_node is None:
                # Node added in effective
                changed.append({
                    "node_id": node_id,
                    "field": "node_added",
                    "before": None,
                    "after": effective_node.get("class_type"),
                })
            elif effective_node is None:
                # Node removed in effective
                changed.append({
                    "node_id": node_id,
                    "field": "node_removed",
                    "before": template_node.get("class_type"),
                    "after": None,
                })
            else:
                # Compare node inputs
                node_changes = self._compare_node_inputs(node_id, template_node, effective_node)
                changed.extend(node_changes)

        return {"changed": changed}

    def _compare_node_inputs(
        self, node_id: str, template_node: dict[str, Any], effective_node: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Compare inputs between template and effective node."""
        changes = []
        template_inputs = template_node.get("inputs", {})
        effective_inputs = effective_node.get("inputs", {})

        # Find all input keys
        all_keys = set(template_inputs.keys()) | set(effective_inputs.keys())

        for key in sorted(all_keys):
            template_value = template_inputs.get(key)
            effective_value = effective_inputs.get(key)

            if template_value != effective_value:
                changes.append({
                    "node_id": node_id,
                    "field": f"inputs.{key}",
                    "before": template_value,
                    "after": effective_value,
                })

        return changes


def compute_workflow_diff(
    template: dict[str, Any], effective: dict[str, Any]
) -> dict[str, Any]:
    """
    Convenience function to compute workflow diff.

    Args:
        template: Original workflow template
        effective: Effective workflow with injected values

    Returns:
        Dictionary with changed fields
    """
    differ = WorkflowDiff(template, effective)
    return differ.compute_diff()


def compute_workflow_diff_files(
    template_path: str | Path, effective_path: str | Path
) -> dict[str, Any]:
    """
    Compute workflow diff from JSON files.

    Args:
        template_path: Path to workflow template JSON
        effective_path: Path to effective workflow JSON

    Returns:
        Dictionary with changed fields
    """
    template_path = Path(template_path)
    effective_path = Path(effective_path)

    with open(template_path, "r", encoding="utf-8") as f:
        template = json.load(f)

    with open(effective_path, "r", encoding="utf-8") as f:
        effective = json.load(f)

    return compute_workflow_diff(template, effective)


if __name__ == "__main__":
    # CLI for testing
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m app.control.workflow_diff <template.json> <effective.json>")
        sys.exit(1)

    template_path = sys.argv[1]
    effective_path = sys.argv[2]
    diff = compute_workflow_diff_files(template_path, effective_path)
    print(json.dumps(diff, indent=2))
