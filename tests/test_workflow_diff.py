"""Tests for MK-OBS1.2 — Workflow Diff."""
from __future__ import annotations

from app.control.workflow_diff import WorkflowDiff, compute_workflow_diff


def _make_template_workflow() -> dict:
    """Create a template workflow for testing."""
    return {
        "__inject__": {
            "positive_prompt_node": "6",
            "negative_prompt_node": "7",
        },
        "3": {
            "inputs": {
                "seed": 123,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "karras",
                "denoise": 1.0,
            },
            "class_type": "KSampler",
        },
        "6": {
            "inputs": {
                "text": "original positive prompt",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {
                "text": "original negative prompt",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
    }


def _make_effective_workflow() -> dict:
    """Create an effective workflow with changes."""
    return {
        "__inject__": {
            "positive_prompt_node": "6",
            "negative_prompt_node": "7",
        },
        "3": {
            "inputs": {
                "seed": 747002,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "karras",
                "denoise": 1.0,
            },
            "class_type": "KSampler",
        },
        "6": {
            "inputs": {
                "text": "modified positive prompt",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {
                "text": "original negative prompt",
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
    }


def test_workflow_diff_shows_changed_seed_and_prompt_fields() -> None:
    """Test that workflow diff shows changed seed and prompt fields."""
    template = _make_template_workflow()
    effective = _make_effective_workflow()

    differ = WorkflowDiff(template, effective)
    diff = differ.compute_diff()

    assert diff["changed"] is not None
    assert len(diff["changed"]) == 2

    # Find seed change
    seed_change = next((c for c in diff["changed"] if "seed" in c["field"]), None)
    assert seed_change is not None
    assert seed_change["node_id"] == "3"
    assert seed_change["field"] == "inputs.seed"
    assert seed_change["before"] == 123
    assert seed_change["after"] == 747002

    # Find prompt change
    prompt_change = next((c for c in diff["changed"] if "text" in c["field"]), None)
    assert prompt_change is not None
    assert prompt_change["node_id"] == "6"
    assert prompt_change["field"] == "inputs.text"
    assert prompt_change["before"] == "original positive prompt"
    assert prompt_change["after"] == "modified positive prompt"


def test_workflow_diff_with_no_changes() -> None:
    """Test that workflow diff returns empty when no changes."""
    template = _make_template_workflow()
    effective = _make_template_workflow()  # Same as template

    differ = WorkflowDiff(template, effective)
    diff = differ.compute_diff()

    assert diff["changed"] == []


def test_workflow_diff_detects_added_node() -> None:
    """Test that workflow diff detects added nodes."""
    template = _make_template_workflow()
    effective = _make_effective_workflow()
    effective["10"] = {
        "inputs": {"value": 42},
        "class_type": "NewNode",
    }

    differ = WorkflowDiff(template, effective)
    diff = differ.compute_diff()

    added_change = next((c for c in diff["changed"] if c["field"] == "node_added"), None)
    assert added_change is not None
    assert added_change["node_id"] == "10"
    assert added_change["after"] == "NewNode"


def test_workflow_diff_detects_removed_node() -> None:
    """Test that workflow diff detects removed nodes."""
    template = _make_template_workflow()
    effective = _make_effective_workflow()
    del effective["7"]  # Remove node 7

    differ = WorkflowDiff(template, effective)
    diff = differ.compute_diff()

    removed_change = next((c for c in diff["changed"] if c["field"] == "node_removed"), None)
    assert removed_change is not None
    assert removed_change["node_id"] == "7"
    assert removed_change["before"] == "CLIPTextEncode"


def test_compute_workflow_diff_convenience_function() -> None:
    """Test the convenience function compute_workflow_diff."""
    template = _make_template_workflow()
    effective = _make_effective_workflow()

    diff = compute_workflow_diff(template, effective)

    assert "changed" in diff
    assert isinstance(diff["changed"], list)


def test_workflow_diff_ignores_inject_section() -> None:
    """Test that workflow diff ignores __inject__ section."""
    template = _make_template_workflow()
    effective = _make_effective_workflow()
    effective["__inject__"]["extra_field"] = "value"  # Change inject section

    differ = WorkflowDiff(template, effective)
    diff = differ.compute_diff()

    # Should not report changes in __inject__
    inject_changes = [c for c in diff["changed"] if "__inject__" in c.get("field", "")]
    assert len(inject_changes) == 0


def test_workflow_diff_detects_multiple_field_changes() -> None:
    """Test that workflow diff detects multiple field changes in same node."""
    template = _make_template_workflow()
    effective = _make_effective_workflow()
    effective["3"]["inputs"]["steps"] = 30  # Change steps
    effective["3"]["inputs"]["cfg"] = 8.0  # Change cfg

    differ = WorkflowDiff(template, effective)
    diff = differ.compute_diff()

    node_3_changes = [c for c in diff["changed"] if c["node_id"] == "3"]
    assert len(node_3_changes) == 3  # seed, steps, cfg
