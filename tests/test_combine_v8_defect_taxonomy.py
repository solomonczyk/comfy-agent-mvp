"""Test V8 defect taxonomy artifact.

Tests for RC-COMBINE-V2-8601-9600 task.
"""

import json
import pytest


def test_v8_defect_taxonomy_exists():
    """Test that V8 defect taxonomy artifact exists."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_defect_taxonomy.json"
    with open(artifact_path, 'r') as f:
        taxonomy = json.load(f)
    
    assert taxonomy is not None


def test_defect_taxonomy_created():
    """Test that defect taxonomy is properly structured."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_defect_taxonomy.json"
    with open(artifact_path, 'r') as f:
        taxonomy = json.load(f)
    
    assert "blocking_defects" in taxonomy
    assert "non_blocking_improvements" in taxonomy
    assert "production_acceptance_blockers" in taxonomy


def test_blocking_defects_empty():
    """Test that blocking defects list is empty for accepted candidate."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_defect_taxonomy.json"
    with open(artifact_path, 'r') as f:
        taxonomy = json.load(f)
    
    assert taxonomy["blocking_defects"] == []


def test_non_blocking_improvements_list():
    """Test that non-blocking improvements are documented."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_defect_taxonomy.json"
    with open(artifact_path, 'r') as f:
        taxonomy = json.load(f)
    
    assert len(taxonomy["non_blocking_improvements"]) > 0


def test_production_acceptance_blockers_list():
    """Test that production acceptance blockers are documented."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_defect_taxonomy.json"
    with open(artifact_path, 'r') as f:
        taxonomy = json.load(f)
    
    assert len(taxonomy["production_acceptance_blockers"]) > 0


def test_non_blocking_improvements_count():
    """Test that non-blocking improvements has expected count."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_defect_taxonomy.json"
    with open(artifact_path, 'r') as f:
        taxonomy = json.load(f)
    
    assert len(taxonomy["non_blocking_improvements"]) >= 3


def test_production_acceptance_blockers_count():
    """Test that production acceptance blockers has expected count."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_defect_taxonomy.json"
    with open(artifact_path, 'r') as f:
        taxonomy = json.load(f)
    
    assert len(taxonomy["production_acceptance_blockers"]) >= 3