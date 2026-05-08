"""Test V8 operator visual review outcome artifact.

Tests for RC-COMBINE-V2-8601-9600 task.
"""

import json
import pytest


def test_v8_operator_visual_review_outcome_exists():
    """Test that V8 operator visual review outcome artifact exists."""
    artifact_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_operator_visual_review_outcome.json"
    with open(artifact_path, 'r') as f:
        outcome = json.load(f)
    
    assert outcome is not None
    assert outcome["task_id"] == "RC-COMBINE-V2-8601-9600"


def test_v8_operator_visual_review_outcome_sha256_must_match_manifest():
    """Test that sha256 in outcome matches the known good asset."""
    outcome_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_operator_visual_review_outcome.json"
    result_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_real_generation_result.json"
    
    with open(outcome_path, 'r') as f:
        outcome = json.load(f)
    with open(result_path, 'r') as f:
        result = json.load(f)
    
    assert outcome["reviewed_asset_sha256"] == result["sha256"]
    assert outcome["reviewed_asset_sha256"] == "e551c745e28ad7979f5eb63b206f85f4974cb1227e84121f337f8f81239e90cd"


def test_v8_operator_visual_review_recorded():
    """Test that operator visual review was recorded."""
    outcome_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_operator_visual_review_outcome.json"
    
    with open(outcome_path, 'r') as f:
        outcome = json.load(f)
    
    assert outcome["operator_visual_review_executed"] == True


def test_candidate_can_be_accepted_without_production_acceptance():
    """Test that candidate can be accepted for pipeline without production acceptance."""
    outcome_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_operator_visual_review_outcome.json"
    
    with open(outcome_path, 'r') as f:
        outcome = json.load(f)
    
    assert outcome["visual_candidate_accepted_for_pipeline"] == True
    assert outcome["production_accepted"] == False


def test_production_accepted_false():
    """Test that production_accepted is explicitly false."""
    outcome_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_operator_visual_review_outcome.json"
    
    with open(outcome_path, 'r') as f:
        outcome = json.load(f)
    
    assert outcome["production_accepted"] == False
    assert outcome["assembly_allowed"] == False
    assert outcome["downstream_allowed"] == False


def test_assembly_downstream_blocked():
    """Test that assembly and downstream are blocked."""
    outcome_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_operator_visual_review_outcome.json"
    
    with open(outcome_path, 'r') as f:
        outcome = json.load(f)
    
    assert outcome["assembly_allowed"] == False
    assert outcome["downstream_allowed"] == False


def test_generation_gate_not_opened():
    """Test that V9 generation gate is not opened."""
    outcome_path = "data/rc2_multishot1_ep01/output/control/combine_v2_v8_operator_visual_review_outcome.json"
    
    with open(outcome_path, 'r') as f:
        outcome = json.load(f)
    
    assert outcome["next_decision"] == "prepare_v9_corrective_plan_without_generation"