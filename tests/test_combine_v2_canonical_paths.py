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


# ── RC-COMBINE-V2-2481-2540: V4 preflight canonical path tests ───────────────

class TestV4VisualQAPreflightCanonicalPaths:
    """Verify V4 visual QA preflight writes only to canonical control paths."""

    def _setup(self, tmp_path):
        project_root = tmp_path / "project"
        control_dir = project_root / "output" / "control"
        assets_dir = project_root / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png").write_bytes(b"P" * 4096)
        with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
            json.dump({
                "generated_assets": ["output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png"],
                "asset_count": 1,
            }, f)
        with open(control_dir / "combine_v2_corrective_retry_v4_result_review.json", 'w') as f:
            json.dump({"branch_selected": "success", "manifest_success_policy_passed": True}, f)
        return project_root, control_dir

    def test_preflight_artifact_written_to_control_dir(self, tmp_path):
        """Preflight artifact is written to output/control/, not project root."""
        import argparse
        from app.cli import combine_preflight_corrective_retry_v4_visual_qa
        project_root, control_dir = self._setup(tmp_path)

        combine_preflight_corrective_retry_v4_visual_qa(argparse.Namespace(
            project_root=str(project_root), shot_id="shot02", json=False))

        assert (control_dir / "combine_v2_corrective_retry_v4_visual_qa_preflight.json").exists()
        assert not (project_root / "combine_v2_corrective_retry_v4_visual_qa_preflight.json").exists()

    def test_input_packet_written_to_control_dir(self, tmp_path):
        """Visual QA input packet is written to output/control/, not project root."""
        import argparse
        from app.cli import combine_preflight_corrective_retry_v4_visual_qa
        project_root, control_dir = self._setup(tmp_path)

        combine_preflight_corrective_retry_v4_visual_qa(argparse.Namespace(
            project_root=str(project_root), shot_id="shot02", json=False))

        assert (control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json").exists()
        assert not (project_root / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json").exists()

    def test_artifact_index_updated_in_canonical_path(self, tmp_path):
        """artifact_index.json is updated in canonical output/control/ path."""
        import argparse
        from app.cli import combine_preflight_corrective_retry_v4_visual_qa
        project_root, control_dir = self._setup(tmp_path)

        combine_preflight_corrective_retry_v4_visual_qa(argparse.Namespace(
            project_root=str(project_root), shot_id="shot02", json=False))

        assert (control_dir / "artifact_index.json").exists()
        assert not (project_root / "artifact_index.json").exists()

    def test_episode_ledger_updated_in_canonical_path(self, tmp_path):
        """episode_ledger.json is updated in canonical output/control/ path."""
        import argparse
        from app.cli import combine_preflight_corrective_retry_v4_visual_qa
        project_root, control_dir = self._setup(tmp_path)

        combine_preflight_corrective_retry_v4_visual_qa(argparse.Namespace(
            project_root=str(project_root), shot_id="shot02", json=False))

        assert (control_dir / "episode_ledger.json").exists()
        assert not (project_root / "episode_ledger.json").exists()

    def test_no_stray_artifacts_at_root(self, tmp_path):
        """No stray JSON artifacts are written to project root by preflight."""
        import argparse
        from app.cli import combine_preflight_corrective_retry_v4_visual_qa
        project_root, control_dir = self._setup(tmp_path)

        combine_preflight_corrective_retry_v4_visual_qa(argparse.Namespace(
            project_root=str(project_root), shot_id="shot02", json=False))

        root_jsons = list(project_root.glob("*.json"))
        assert root_jsons == [], f"Stray JSON at project root: {root_jsons}"
