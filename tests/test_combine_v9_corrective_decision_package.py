"""Test V9 corrective decision package artifact.

Tests for RC-COMBINE-V2-8601-9600 task.
"""

import json
import pytest


def test_v9_corrective_decision_package_exists():
    """Test that V9 corrective decision package artifact exists."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v9_corrective_decision_package.json"
    with open(artifact_path, 'r') as f:
        package = json.load(f)
    
    assert package is not None


def test_v9_generation_allowed_now_false():
    """Test that V9 generation is not allowed now."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v9_corrective_decision_package.json"
    with open(artifact_path, 'r') as f:
        package = json.load(f)
    
    assert package["v9_generation_allowed_now"] == False


def test_requires_separate_operator_generation_gate():
    """Test that separate operator generation gate is required."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v9_corrective_decision_package.json"
    with open(artifact_path, 'r') as f:
        package = json.load(f)
    
    assert package["requires_separate_operator_generation_gate"] == True


def test_v9_plan_created_without_generation():
    """Test that V9 plan was created without generation."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v9_corrective_decision_package.json"
    with open(artifact_path, 'r') as f:
        package = json.load(f)
    
    assert package["use_v8_as_positive_reference"] == True
    assert len(package["preserve_v8_strengths"]) > 0


def test_v9_corrective_targets_exist():
    """Test that V9 corrective targets are defined."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v9_corrective_decision_package.json"
    with open(artifact_path, 'r') as f:
        package = json.load(f)
    
    assert "corrective_targets" in package
    assert len(package["corrective_targets"]) > 0


def test_v9_forbidden_regressions_exist():
    """Test that V9 forbidden regressions are defined."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v9_corrective_decision_package.json"
    with open(artifact_path, 'r') as f:
        package = json.load(f)
    
    assert "forbidden_regressions" in package
    assert len(package["forbidden_regressions"]) > 0


def test_v9_preserve_v8_strengths_content():
    """Test that V8 strengths to preserve are documented."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v9_corrective_decision_package.json"
    with open(artifact_path, 'r') as f:
        package = json.load(f)
    
    strengths = package["preserve_v8_strengths"]
    assert "face clarity" in strengths
    assert "eye integrity" in strengths
    assert "mouth integrity" in strengths


def test_v9_forbidden_regressions_content():
    """Test that forbidden regressions include key items."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v9_corrective_decision_package.json"
    with open(artifact_path, 'r') as f:
        package = json.load(f)
    
    forbidden = package["forbidden_regressions"]
    assert "blurred face" in forbidden
    assert "broken eyes" in forbidden
    assert "broken mouth" in forbidden