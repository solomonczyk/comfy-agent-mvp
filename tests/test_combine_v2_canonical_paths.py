"""
Tests for Combine V2 Canonical State Paths

Verifies that:
- artifact_index.json is resolved to output/control/artifact_index.json
- ledger is resolved to output/control/episode_ledger.json
- No root-level state files are created
"""

import pytest
import json
import os
from pathlib import Path
from app.orchestrator.orchestrator import CombineOrchestrator

class TestCombineCanonicalPaths:
    """Test that Combine V2 uses canonical paths for state persistence"""
    
    def test_orchestrator_resolves_canonical_paths(self, tmp_path):
        """Test that orchestrator resolves paths to output/control/"""
        orchestrator = CombineOrchestrator(str(tmp_path))
        
        expected_artifact_path = tmp_path / "output" / "control" / "artifact_index.json"
        expected_ledger_path = tmp_path / "output" / "control" / "episode_ledger.json"
        
        assert orchestrator.artifact_index_path == expected_artifact_path
        assert orchestrator.ledger_path == expected_ledger_path
        
    def test_run_stage_creates_files_in_canonical_directory_only(self, tmp_path):
        """Test that run_stage does not create root-level files"""
        orchestrator = CombineOrchestrator(str(tmp_path))
        
        # Run a stage
        orchestrator.run_stage("brief_intake_required", dry_run=True)
        
        # Check canonical files exist
        assert (tmp_path / "output" / "control" / "artifact_index.json").exists()
        assert (tmp_path / "output" / "control" / "episode_ledger.json").exists()
        
        # Check root files do NOT exist
        assert not (tmp_path / "artifact_index.json").exists()
        assert not (tmp_path / "ledger.json").exists()
        assert not (tmp_path / "episode_ledger.json").exists()

    def test_orchestrator_reads_from_canonical_paths(self, tmp_path):
        """Test that orchestrator reads existing state from canonical paths"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {"current_state": "production_plan_required", "route_family": "portrait_character_identity"}
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(artifact_index, f)
            
        orchestrator = CombineOrchestrator(str(tmp_path))
        status = orchestrator.get_status()
        
        assert status.current_state == "production_plan_required"
        assert status.route_family == "portrait_character_identity"
