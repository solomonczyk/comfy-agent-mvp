#!/usr/bin/env python3
"""
Project hygiene validation script.
Validates that the project adheres to cleanup standards.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any


def load_cleanup_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the cleanup candidates manifest."""
    with open(manifest_path, 'r') as f:
        return json.load(f)


def validate_cleanup_candidates(candidates: List[Dict[str, Any]], project_root: Path) -> List[str]:
    """Validate that cleanup candidates exist and are correctly categorized."""
    issues = []
    
    for candidate in candidates:
        path_str = candidate['path']
        # Convert to local path format
        local_path = Path(path_str.replace('F:/ComfyUI/comfy-agent-mvp/', ''))
        full_path = project_root / local_path
        
        # Check if path exists
        if not full_path.exists():
            issues.append(f"Missing cleanup candidate: {local_path}")
            continue
        
        # Check if protected items still exist
        if candidate.get('protected', False) and candidate['action_recommendation'] == 'keep':
            if not full_path.exists():
                issues.append(f"Protected item missing: {local_path}")
        
        # Check type matches
        expected_type = candidate['type']
        if full_path.is_dir() and expected_type != 'directory':
            issues.append(f"Type mismatch: {local_path} expected {expected_type}, is directory")
        elif full_path.is_file() and expected_type != 'file':
            issues.append(f"Type mismatch: {local_path} expected {expected_type}, is file")
    
    return issues


def validate_no_untracked_cleanup_items(project_root: Path, manifest: Dict[str, Any]) -> List[str]:
    """Validate that items marked for cleanup are not in critical directories."""
    issues = []
    critical_dirs = ['app', 'tests', 'scripts', 'docs']
    
    for candidate in manifest['cleanup_candidates']:
        path_str = candidate['path']
        local_path = Path(path_str.replace('F:/ComfyUI/comfy-agent-mvp/', ''))
        
        # Check if cleanup candidate is in a critical directory
        for critical_dir in critical_dirs:
            if local_path.parts and local_path.parts[0] == critical_dir:
                # Allow __pycache__ directories in critical directories (they are cache)
                if '__pycache__' in str(local_path):
                    continue
                if candidate['action_recommendation'] in ['archive', 'delete_later']:
                    issues.append(f"Cleanup candidate in critical directory: {local_path}")
    
    return issues


def validate_gitignore(project_root: Path) -> List[str]:
    """Validate that .gitignore exists and has basic patterns."""
    issues = []
    gitignore_path = project_root / '.gitignore'
    
    if not gitignore_path.exists():
        issues.append(".gitignore file missing")
        return issues
    
    required_patterns = ['__pycache__', '.pytest_cache', '*.log']
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            issues.append(f".gitignore missing pattern: {pattern}")
    
    return issues


def validate_quarantine_exists(project_root: Path) -> List[str]:
    """Validate that quarantine folder exists."""
    issues = []
    quarantine_path = project_root / 'data' / '_quarantine_rc2_cleanup1'
    
    if not quarantine_path.exists():
        issues.append("Quarantine folder missing: data/_quarantine_rc2_cleanup1")
    
    return issues


def main():
    """Main validation entry point."""
    project_root = Path(__file__).parent.parent
    manifest_path = project_root / 'data' / 'cleanup' / 'CLEANUP_CANDIDATES.json'
    
    print(f"Validating project hygiene at: {project_root}")
    print("=" * 60)
    
    all_issues = []
    
    # Load manifest
    if not manifest_path.exists():
        print(f"ERROR: Cleanup manifest not found at {manifest_path}")
        sys.exit(1)
    
    manifest = load_cleanup_manifest(manifest_path)
    candidates = manifest['cleanup_candidates']
    
    # Run validations
    print(f"Checking {len(candidates)} cleanup candidates...")
    candidate_issues = validate_cleanup_candidates(candidates, project_root)
    all_issues.extend(candidate_issues)
    
    print("Checking for untracked cleanup items in critical directories...")
    untracked_issues = validate_no_untracked_cleanup_items(project_root, manifest)
    all_issues.extend(untracked_issues)
    
    print("Validating .gitignore...")
    gitignore_issues = validate_gitignore(project_root)
    all_issues.extend(gitignore_issues)
    
    print("Checking quarantine folder...")
    quarantine_issues = validate_quarantine_exists(project_root)
    all_issues.extend(quarantine_issues)
    
    # Report results
    print("=" * 60)
    if all_issues:
        print(f"VALIDATION FAILED: {len(all_issues)} issues found")
        print()
        for issue in all_issues:
            print(f"  - {issue}")
        sys.exit(1)
    else:
        print("VALIDATION PASSED: All hygiene checks passed")
        sys.exit(0)


if __name__ == '__main__':
    main()
