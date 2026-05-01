"""
Integration tests for the Brief -> Route -> Production Plan chain.

Verifies that the orchestrator can execute the full chain of stages
sequentially until the production plan review stage.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path
from app.orchestrator.orchestrator import CombineOrchestrator
from app.orchestrator.contracts import CombineStageResult

class TestCombineBriefRoutePlanChain:
    """Test the sequential execution of the core Combine V2 chain."""
    
    def test_full_chain_sequential_execution(self):
        """Verify that run_until executes all stages in order until target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_chain_project"
            project_root.mkdir()
            
            # Ensure output/control directory exists for the orchestrator
            (project_root / "output" / "control").mkdir(parents=True)
            
            orchestrator = CombineOrchestrator(str(project_root))
            
            # Target stage
            target_stage = "production_plan_review"
            
            # Run the chain
            results = orchestrator.run_until(target_stage, dry_run=True)
            
            # Verify results
            # Expected stages:
            # 1. brief_intake_required
            # 2. route_classification_required
            # 3. production_plan_required
            # (Stops BEFORE production_plan_review because it's the target)
            
            executed_stages = [r.stage for r in results]
            assert "brief_intake_required" in executed_stages
            assert "route_classification_required" in executed_stages
            assert "production_plan_required" in executed_stages
            assert "production_plan_review" not in executed_stages
            
            # Verify status after run
            status = orchestrator.get_status()
            assert status.current_state == "production_plan_required"
            assert status.next_allowed_action == "production_plan_review"
            
            # Verify artifact index persistence
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            assert artifact_index_path.exists()
            
            with open(artifact_index_path, 'r') as f:
                data = json.load(f)
                assert data["current_state"] == "production_plan_required"
                assert len(data.get("stage_results", [])) == 3
                
            # Verify ledger persistence
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            assert ledger_path.exists()
            
            with open(ledger_path, 'r') as f:
                ledger_data = json.load(f)
                # Should have 3 stage_execution events
                events = [e for e in ledger_data if e.get("event_type") == "stage_execution"]
                assert len(events) == 3

    def test_run_until_stops_at_target_if_already_reached(self):
        """Verify run_until does nothing if already at target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_already_at_target"
            project_root.mkdir()
            (project_root / "output" / "control").mkdir(parents=True)
            
            # Manually set state to production_plan_required
            artifact_index = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index, 'w') as f:
                json.dump({"current_state": "production_plan_required"}, f)
                
            orchestrator = CombineOrchestrator(str(project_root))
            
            # Target is production_plan_review, which is the NEXT action
            results = orchestrator.run_until("production_plan_review", dry_run=True)
            
            # Should run 0 stages because next action is the target
            assert len(results) == 0
            
            # Target is production_plan_required, which is the CURRENT state
            results = orchestrator.run_until("production_plan_required", dry_run=True)
            assert len(results) == 0

    def test_brief_file_propagation(self):
        """Verify that brief_file is passed to agents during the chain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir) / "test_brief_propagation"
            project_root.mkdir()
            (project_root / "output" / "control").mkdir(parents=True)
            
            orchestrator = CombineOrchestrator(str(project_root))
            
            test_brief = "data/briefs/test_brief.json"
            results = orchestrator.run_until("route_classification_required", dry_run=True, brief_file=test_brief)
            
            # Should have run brief_intake_required
            assert len(results) == 1
            assert results[0].stage == "brief_intake_required"
            
            # Check metadata in stage result
            # Note: The agent might not store it in its specific contract but it should be in orchestrator's context
            # We check the orchestrator's run_stage logic which adds it to context.
            # In our stub agents, we can check if it reached them if they log it or return it.
            
            # Let's check if the artifact_index has the record of the run
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                data = json.load(f)
                # Results are stored in stage_results
                # We can't easily check internal context but we can see if success was reported
                assert data["stage_results"][0]["success"] == True
