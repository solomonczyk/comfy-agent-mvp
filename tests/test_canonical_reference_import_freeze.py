"""
Tests for RC-COMBINE-V2-CANONICAL-REFERENCE-ASSET-IMPORT-VALIDATION-FREEZE-001
Tests canonical reference import, validation, and freeze.
"""

import pytest
import json
from pathlib import Path
from PIL import Image

project_root = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
canonical_dir = project_root / "input" / "canonical_references"
output_dir = project_root / "output" / "control" / "identity_environment_lock"


def test_all_canonical_folders_exist():
    """Test that all 6 canonical folders exist."""
    categories = [
        "01_identity",
        "02_face_details",
        "03_costume_materials",
        "04_style_light",
        "05_environment",
        "06_quality_negative"
    ]
    
    for category in categories:
        category_path = canonical_dir / category
        assert category_path.exists(), f"Category folder {category} does not exist"
        assert category_path.is_dir(), f"Category folder {category} is not a directory"


def test_at_least_one_readable_image_in_required_categories():
    """Test that at least one readable image exists in required categories."""
    required_categories = ["01_identity", "05_environment"]
    
    for category in required_categories:
        category_path = canonical_dir / category
        image_files = list(category_path.glob("*.png")) + list(category_path.glob("*.jpg"))
        
        assert len(image_files) > 0, f"No images found in required category {category}"
        
        # Test at least one is readable
        readable_found = False
        for img_file in image_files:
            try:
                img = Image.open(img_file)
                img.verify()
                readable_found = True
                break
            except:
                continue
        
        assert readable_found, f"No readable images found in required category {category}"


def test_reference_manifest_paths_point_to_real_files():
    """Test that manifest paths point to real files."""
    manifest_path = canonical_dir / "reference_manifest.json"
    assert manifest_path.exists(), "reference_manifest.json does not exist"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    for category, file_paths in manifest["canonical_references"].items():
        for file_path in file_paths:
            full_path = project_root / file_path
            assert full_path.exists(), f"Manifest path {file_path} does not exist"
            assert full_path.is_file(), f"Manifest path {file_path} is not a file"


def test_sha256_and_dimensions_recorded():
    """Test that SHA256 and dimensions are recorded in inventory."""
    inventory_path = output_dir / "canonical_reference_inventory.json"
    assert inventory_path.exists(), "canonical_reference_inventory.json does not exist"
    
    with open(inventory_path) as f:
        inventory = json.load(f)
    
    # Check that at least some files have sha256 and dimensions
    files_with_metadata = 0
    for category, data in inventory["categories"].items():
        for file_data in data["files"]:
            if file_data["valid"]:
                assert "sha256" in file_data, f"File {file_data['filename']} missing sha256"
                assert file_data["sha256"] is not None, f"File {file_data['filename']} has null sha256"
                assert "width" in file_data, f"File {file_data['filename']} missing width"
                assert "height" in file_data, f"File {file_data['filename']} missing height"
                assert file_data["width"] > 0, f"File {file_data['filename']} has invalid width"
                assert file_data["height"] > 0, f"File {file_data['filename']} has invalid height"
                files_with_metadata += 1
    
    assert files_with_metadata > 0, "No valid files with metadata found"


def test_contact_sheets_created():
    """Test that all contact sheets were created."""
    # Full contact sheet
    full_contact_sheet = output_dir / "canonical_reference_contact_sheet.jpg"
    assert full_contact_sheet.exists(), "Full canonical reference contact sheet does not exist"
    
    # Category contact sheets
    categories = [
        "01_identity",
        "02_face_details",
        "03_costume_materials",
        "04_style_light",
        "05_environment",
        "06_quality_negative"
    ]
    
    for category in categories:
        contact_sheet = output_dir / f"category_contact_sheet_{category}.jpg"
        assert contact_sheet.exists(), f"Category contact sheet {category} does not exist"


def test_lock_registries_do_not_point_to_generated_fallback_assets():
    """Test that lock registries do not point to generated fallback assets."""
    char_registry_path = output_dir / "character_lock_registry.json"
    env_registry_path = output_dir / "environment_lock_registry.json"
    
    assert char_registry_path.exists(), "character_lock_registry.json does not exist"
    assert env_registry_path.exists(), "environment_lock_registry.json does not exist"
    
    with open(char_registry_path) as f:
        char_registry = json.load(f)
    
    with open(env_registry_path) as f:
        env_registry = json.load(f)
    
    # Check that canonical assets point to canonical_references, not output/assets
    char_asset_path = char_registry["canonical_character_asset"]["path"]
    env_asset_path = env_registry["canonical_environment_asset"]["path"]
    
    assert "canonical_references" in char_asset_path, f"Character asset path {char_asset_path} does not point to canonical_references"
    assert "canonical_references" in env_asset_path, f"Environment asset path {env_asset_path} does not point to canonical_references"
    
    # Check that source is operator_provided_canonical
    assert char_registry["source"] == "operator_provided_canonical", "Character registry source is not operator_provided_canonical"
    assert env_registry["source"] == "operator_provided_canonical", "Environment registry source is not operator_provided_canonical"


def test_generation_preflight_blocks_missing_locks():
    """Test that generation preflight blocks missing locks."""
    gate_path = output_dir / "generation_preflight_idempotency_gate.json"
    assert gate_path.exists(), "generation_preflight_idempotency_gate.json does not exist"
    
    with open(gate_path) as f:
        gate = json.load(f)
    
    # Check that required checks include lock validation
    required_checks = gate["required_checks"]
    assert "character_lock_registry_exists" in required_checks, "character_lock_registry_exists not in required checks"
    assert "environment_lock_registry_exists" in required_checks, "environment_lock_registry_exists not in required checks"
    assert "canonical_character_asset_valid" in required_checks, "canonical_character_asset_valid not in required checks"
    assert "canonical_environment_asset_valid" in required_checks, "canonical_environment_asset_valid not in required checks"
    
    # Check block conditions
    block_conditions = gate["block_conditions"]
    assert "missing_character_lock" in block_conditions, "missing_character_lock not in block conditions"
    assert "missing_environment_lock" in block_conditions, "missing_environment_lock not in block conditions"


def test_production_accepted_remains_false():
    """Test that production_accepted remains false after canonical freeze."""
    state_path = project_root / "output" / "control" / "state.json"
    assert state_path.exists(), "state.json does not exist"
    
    with open(state_path) as f:
        state = json.load(f)
    
    assert state["production_accepted"] == False, "production_accepted should be false after canonical freeze"
    
    # Also check artifact_index
    artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
    with open(artifact_index_path) as f:
        artifact_index = json.load(f)
    
    assert artifact_index["production_accepted"] == False, "production_accepted in artifact_index should be false"


def test_canonical_character_asset_used_true():
    """Test that canonical_character_asset_used is true after successful freeze."""
    state_path = project_root / "output" / "control" / "state.json"
    assert state_path.exists(), "state.json does not exist"
    
    with open(state_path) as f:
        state = json.load(f)
    
    assert state["canonical_character_asset_used"] == True, "canonical_character_asset_used should be true after canonical freeze"
    assert state["canonical_references_available"] == True, "canonical_references_available should be true after canonical freeze"


def test_scene_idempotency_policy_enforced():
    """Test that scene idempotency policy is properly enforced."""
    policy_path = output_dir / "scene_idempotency_policy.json"
    assert policy_path.exists(), "scene_idempotency_policy.json does not exist"
    
    with open(policy_path) as f:
        policy = json.load(f)
    
    proof = policy["workflow_proof_required"]
    assert proof["canonical_character_asset_used"] == True, "canonical_character_asset_used should be true in policy"
    assert proof["character_lock_id"] == "char_lock_001", "character_lock_id should be char_lock_001"
    assert proof["environment_lock_id"] == "env_lock_001", "environment_lock_id should be env_lock_001"
    assert proof["same_scene_idempotency_enforced"] == True, "same_scene_idempotency_enforced should be true"
    assert proof["random_identity_generation_blocked"] == True, "random_identity_generation_blocked should be true"
    assert proof["random_environment_generation_blocked"] == True, "random_environment_generation_blocked should be true"


def test_freeze_proof_created():
    """Test that canonical_asset_import_freeze_proof.json was created."""
    proof_path = output_dir / "canonical_asset_import_freeze_proof.json"
    assert proof_path.exists(), "canonical_asset_import_freeze_proof.json does not exist"
    
    with open(proof_path) as f:
        proof = json.load(f)
    
    assert proof["task_id"] == "RC-COMBINE-V2-CANONICAL-REFERENCE-ASSET-IMPORT-VALIDATION-FREEZE-001", "Task ID mismatch"
    assert proof["status"] == "completed", "Proof status should be completed"
    assert proof["no_generation_performed"] == True, "no_generation_performed should be true"
    assert proof["no_comfyui_submit"] == True, "no_comfyui_submit should be true"
    assert proof["no_preview_render"] == True, "no_preview_render should be true"
    assert proof["no_assembly"] == True, "no_assembly should be true"
    assert proof["no_downstream"] == True, "no_downstream should be true"


def test_validation_report_exists():
    """Test that validation report exists and has correct structure."""
    validation_report_path = output_dir / "canonical_reference_validation_report.json"
    assert validation_report_path.exists(), "canonical_reference_validation_report.json does not exist"
    
    with open(validation_report_path) as f:
        report = json.load(f)
    
    assert "total_files_scanned" in report, "total_files_scanned not in validation report"
    assert "valid_files" in report, "valid_files not in validation report"
    assert "invalid_files" in report, "invalid_files not in validation report"
    assert "categories" in report, "categories not in validation report"
    
    # Check that all files are valid (24/24 from our scan)
    assert report["total_files_scanned"] == 24, f"Expected 24 files scanned, got {report['total_files_scanned']}"
    assert report["valid_files"] == 24, f"Expected 24 valid files, got {report['valid_files']}"
    assert report["invalid_files"] == 0, f"Expected 0 invalid files, got {report['invalid_files']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
