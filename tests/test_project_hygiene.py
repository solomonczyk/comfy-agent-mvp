"""
Tests for project hygiene validation.
"""

import json
import pytest
from pathlib import Path
from scripts.validate_project_hygiene import (
    load_cleanup_manifest,
    validate_cleanup_candidates,
    validate_no_untracked_cleanup_items,
    validate_gitignore,
    validate_quarantine_exists,
)


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def manifest_path(project_root):
    """Get the cleanup manifest path."""
    return project_root / 'data' / 'cleanup' / 'CLEANUP_CANDIDATES.json'


@pytest.fixture
def manifest(manifest_path):
    """Load the cleanup manifest."""
    return load_cleanup_manifest(manifest_path)


def test_manifest_exists(manifest_path):
    """Test that the cleanup manifest exists."""
    assert manifest_path.exists(), f"Cleanup manifest not found at {manifest_path}"


def test_manifest_is_valid_json(manifest_path):
    """Test that the cleanup manifest is valid JSON."""
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    assert 'cleanup_candidates' in data
    assert isinstance(data['cleanup_candidates'], list)


def test_manifest_has_required_fields(manifest):
    """Test that all cleanup candidates have required fields."""
    required_fields = ['path', 'type', 'reason', 'status', 'action_recommendation', 'protected', 'risk_level', 'depends_on']
    
    for candidate in manifest['cleanup_candidates']:
        for field in required_fields:
            assert field in candidate, f"Missing field '{field}' in candidate: {candidate.get('path', 'unknown')}"


def test_protected_items_are_kept(manifest):
    """Test that protected items have 'keep' action recommendation."""
    for candidate in manifest['cleanup_candidates']:
        if candidate.get('protected', False):
            assert candidate['action_recommendation'] == 'keep', \
                f"Protected item should be kept: {candidate['path']}"


def test_gitignore_exists(project_root):
    """Test that .gitignore exists."""
    gitignore_path = project_root / '.gitignore'
    assert gitignore_path.exists(), ".gitignore file missing"


def test_gitignore_has_python_cache(project_root):
    """Test that .gitignore includes Python cache patterns."""
    gitignore_path = project_root / '.gitignore'
    with open(gitignore_path, 'r') as f:
        content = f.read()
    assert '__pycache__' in content, ".gitignore missing __pycache__ pattern"
    assert '*.py[cod]' in content, ".gitignore missing *.py[cod] pattern"


def test_gitignore_has_log_patterns(project_root):
    """Test that .gitignore includes log file patterns."""
    gitignore_path = project_root / '.gitignore'
    with open(gitignore_path, 'r') as f:
        content = f.read()
    assert '*.log' in content, ".gitignore missing *.log pattern"


def test_quarantine_folder_exists(project_root):
    """Test that quarantine folder exists."""
    quarantine_path = project_root / 'data' / '_quarantine_rc2_cleanup1'
    assert quarantine_path.exists(), f"Quarantine folder missing: {quarantine_path}"


def test_cleanup_candidates_paths_use_forward_slashes(manifest):
    """Test that all paths in cleanup candidates use forward slashes."""
    for candidate in manifest['cleanup_candidates']:
        path = candidate['path']
        assert '\\' not in path, f"Path contains backslash: {path}"


def test_cleanup_candidates_no_double_slashes(manifest):
    """Test that paths don't have double slashes after the protocol."""
    for candidate in manifest['cleanup_candidates']:
        path = candidate['path']
        # Allow double slash in file:// URLs but not in regular paths
        if 'file://' not in path:
            # Check for double slashes after the drive letter
            if ':' in path:
                drive_part, rest = path.split(':', 1)
                assert not rest.startswith('//'), f"Path has double slash after drive: {path}"


def test_no_cleanup_candidates_in_app_directory(manifest):
    """Test that no cleanup candidates are in the app directory (except __pycache__)."""
    for candidate in manifest['cleanup_candidates']:
        path = candidate['path']
        local_path = path.replace('F:/ComfyUI/comfy-agent-mvp/', '')
        if candidate['action_recommendation'] in ['archive', 'delete_later']:
            # Allow __pycache__ directories as they are cache
            if '__pycache__' in local_path:
                continue
            assert not local_path.startswith('app/'), \
                f"Cleanup candidate in app directory: {local_path}"


def test_no_cleanup_candidates_in_tests_directory(manifest):
    """Test that no cleanup candidates are in the tests directory (except __pycache__)."""
    for candidate in manifest['cleanup_candidates']:
        path = candidate['path']
        local_path = path.replace('F:/ComfyUI/comfy-agent-mvp/', '')
        if candidate['action_recommendation'] in ['archive', 'delete_later']:
            # Allow __pycache__ directories as they are cache
            if '__pycache__' in local_path:
                continue
            assert not local_path.startswith('tests/'), \
                f"Cleanup candidate in tests directory: {local_path}"


def test_no_cleanup_candidates_in_scripts_directory(manifest):
    """Test that no cleanup candidates are in the scripts directory."""
    for candidate in manifest['cleanup_candidates']:
        path = candidate['path']
        local_path = path.replace('F:/ComfyUI/comfy-agent-mvp/', '')
        if candidate['action_recommendation'] in ['archive', 'delete_later']:
            assert not local_path.startswith('scripts/'), \
                f"Cleanup candidate in scripts directory: {local_path}"


def test_no_cleanup_candidates_in_docs_directory(manifest):
    """Test that no cleanup candidates are in the docs directory."""
    for candidate in manifest['cleanup_candidates']:
        path = candidate['path']
        local_path = path.replace('F:/ComfyUI/comfy-agent-mvp/', '')
        if candidate['action_recommendation'] in ['archive', 'delete_later']:
            assert not local_path.startswith('docs/'), \
                f"Cleanup candidate in docs directory: {local_path}"


def test_validation_script_exists(project_root):
    """Test that the validation script exists."""
    validation_script = project_root / 'scripts' / 'validate_project_hygiene.py'
    assert validation_script.exists(), f"Validation script missing: {validation_script}"


def test_cleanup_inventory_exists(project_root):
    """Test that the cleanup inventory document exists."""
    inventory_path = project_root / 'docs' / 'PROJECT_CLEANUP_INVENTORY.md'
    assert inventory_path.exists(), f"Cleanup inventory missing: {inventory_path}"


def test_source_of_truth_map_exists(project_root):
    """Test that the source of truth map exists."""
    sot_path = project_root / 'docs' / 'SOURCE_OF_TRUTH_MAP.md'
    assert sot_path.exists(), f"Source of truth map missing: {sot_path}"
