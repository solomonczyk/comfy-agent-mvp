"""Tests for combine corrective retry V4 one submit.

RC-COMBINE-V2-1701-1760 — Test one controlled retry V4 generation submit with post-submit validation.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_combine_corrective_retry_v4_generate_assets_execute(tmp_path):
    """Test executing one corrective retry V4 generation."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required authorization
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    # Create implementation package
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert success
    assert result == 0
    
    # Verify artifacts created
    assert (control_dir / "combine_v2_corrective_retry_v4_generation_pre_submit_validation.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v4_generation_submit_request.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v4_generation_result.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v4_generation_trace.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json").exists()


def test_pre_submit_validation_required(tmp_path):
    """Test that pre-submit validation is required."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create authorization
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    # Create implementation package
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Missing some guard contracts
    with open(control_dir / "combine_v2_retry_v4_pre_submit_validation_contract.json", 'w') as f:
        json.dump({}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Should fail due to missing patches
    assert result == 1


def test_generation_attempts_limited_to_one(tmp_path):
    """Test that generation attempts are limited to one."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args with max_generations=1
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert success
    assert result == 0
    
    # Verify generation result
    result_path = control_dir / "combine_v2_corrective_retry_v4_generation_result.json"
    with open(result_path, 'r') as f:
        gen_result = json.load(f)
    
    assert gen_result["max_generations"] == 1
    assert gen_result["second_generation_attempted"] == False


def test_second_generation_blocked(tmp_path):
    """Test that second generation is blocked."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert success
    assert result == 0
    
    # Verify second generation blocked
    result_path = control_dir / "combine_v2_corrective_retry_v4_generation_result.json"
    with open(result_path, 'r') as f:
        gen_result = json.load(f)
    
    assert gen_result["second_generation_attempted"] == False


def test_blind_retry_blocked(tmp_path):
    """Test that blind retry is blocked."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert success
    assert result == 0
    
    # Verify blind retry blocked
    result_path = control_dir / "combine_v2_corrective_retry_v4_generation_result.json"
    with open(result_path, 'r') as f:
        gen_result = json.load(f)
    
    assert gen_result["blind_retry_allowed"] == False


def test_no_authorization_no_generation(tmp_path):
    """Test that generation is blocked without authorization."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create authorization with not authorized
    authorization = {
        "operator_retry_v4_generation_authorized": False,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert failure
    assert result == 1


def test_visual_qa_not_executed(tmp_path):
    """Test that Visual QA is not executed."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert success
    assert result == 0
    
    # Verify visual QA not executed
    result_path = control_dir / "combine_v2_corrective_retry_v4_generation_result.json"
    with open(result_path, 'r') as f:
        gen_result = json.load(f)
    
    assert gen_result["visual_qa_executed"] == False


def test_assembly_not_executed(tmp_path):
    """Test that assembly is not executed."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert success
    assert result == 0
    
    # Verify assembly not executed
    result_path = control_dir / "combine_v2_corrective_retry_v4_generation_result.json"
    with open(result_path, 'r') as f:
        gen_result = json.load(f)
    
    assert gen_result["assembly_executed"] == False
    assert gen_result["downstream_executed"] == False


def test_post_submit_validation_executed(tmp_path):
    """Test that post-submit validation is executed."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert success
    assert result == 0
    
    # Verify post-submit validation executed
    post_validation_path = control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json"
    assert post_validation_path.exists()
    
    with open(post_validation_path, 'r') as f:
        post_validation = json.load(f)
    
    assert post_validation["post_submit_validation_executed"] == True
    assert post_validation["stub_asset_guard_enforced"] == True


def test_stub_asset_guard_enforced(tmp_path):
    """Test that stub asset guard is enforced."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert success
    assert result == 0
    
    # Verify stub asset guard enforced
    post_validation_path = control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json"
    with open(post_validation_path, 'r') as f:
        post_validation = json.load(f)
    
    assert post_validation["stub_asset_guard_enforced"] == True
    assert post_validation["stub_asset_detected"] == True


def test_production_accepted_false(tmp_path):
    """Test that production_accepted is false."""
    from app.cli import combine_corrective_retry_v4_generate_assets
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    authorization = {
        "operator_retry_v4_generation_authorized": True,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization.json", 'w') as f:
        json.dump(authorization, f)
    
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create required V4 guard contracts
    guard_contracts = [
        "combine_v2_retry_v4_pre_submit_validation_contract.json",
        "combine_v2_retry_v4_post_submit_validation_contract.json",
        "combine_v2_retry_v4_manifest_success_policy.json",
        "combine_v2_retry_v4_visual_qa_input_guard.json",
        "combine_v2_retry_v4_assembly_asset_guard.json",
    ]
    for contract in guard_contracts:
        with open(control_dir / contract, 'w') as f:
            json.dump({"contract_type": contract.replace('.json', ''), "created": True}, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        execute=True,
        max_generations=1,
        json=True,
    )
    
    # Run command
    result = combine_corrective_retry_v4_generate_assets(args)
    
    # Assert success
    assert result == 0
    
    # Verify production_accepted is false
    result_path = control_dir / "combine_v2_corrective_retry_v4_generation_result.json"
    with open(result_path, 'r') as f:
        gen_result = json.load(f)
    
    assert gen_result["production_accepted"] == False
