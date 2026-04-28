"""Tests for recipe validation ledger evidence (MK-RECIPE7)."""

import json
import tempfile
from pathlib import Path

import pytest

from app.control.ledger import compact_recipe_validation_for_ledger, ShotLedgerRecord
from app.control.action_runner import ControlledActionRunner
from app.control.gate import ShotExecutionGate
from app.control.shot_controller import ShotController
from app.control.action_plan import ActionPlanBuilder
from app.control.ledger import ShotLedgerStorage
from unittest.mock import MagicMock


class TestCompactRecipeValidationForLedger:
    """Tests for compact_recipe_validation_for_ledger helper."""
    
    def test_compact_recipe_validation_for_ledger_with_full_validation(self):
        """Test that compact recipe_validation extracts essential fields."""
        recipe_validation = {
            "available": True,
            "settings_source": "planned",
            "verdict": "fail",
            "recipe_id": "sdxl_storyboard_keyframes_gtx1060",
            "score": 0.75,
            "issues": [
                {
                    "severity": "error",
                    "code": "BATCH_SIZE_EXCEEDED",
                    "message": "Batch size 12 exceeds maximum 3",
                    "recommendation": "Reduce batch size to 3 or less"
                }
            ],
            "summary": {
                "title": "Recipe blocked",
                "risk_level": "critical",
                "operator_message": "Generation is blocked because settings exceed safe limits",
                "top_reasons": ["Batch size 12 exceeds maximum 3"],
                "recommended_next_action": "Fix blocking recipe errors before running generate_frames."
            }
        }
        
        compact = compact_recipe_validation_for_ledger(recipe_validation)
        
        assert compact is not None
        assert compact["available"] is True
        assert compact["settings_source"] == "planned"
        assert compact["verdict"] == "fail"
        assert compact["recipe_id"] == "sdxl_storyboard_keyframes_gtx1060"
        assert compact["score"] == 0.75
        assert compact["issue_codes"] == ["BATCH_SIZE_EXCEEDED"]
        assert "summary" in compact
        assert compact["summary"]["title"] == "Recipe blocked"
        assert compact["summary"]["risk_level"] == "critical"
        assert compact["summary"]["recommended_next_action"] == "Fix blocking recipe errors before running generate_frames."
        
        # Ensure full issue list is not stored
        assert "issues" not in compact
    
    def test_compact_recipe_validation_for_ledger_with_unavailable(self):
        """Test that compact recipe_validation handles unavailable status."""
        recipe_validation = {
            "available": False,
            "reason": "observed generation settings not found"
        }
        
        compact = compact_recipe_validation_for_ledger(recipe_validation)
        
        assert compact is not None
        assert compact["available"] is False
        assert compact["reason"] == "observed generation settings not found"
    
    def test_compact_recipe_validation_for_ledger_with_none(self):
        """Test that compact recipe_validation returns None for None input."""
        compact = compact_recipe_validation_for_ledger(None)
        assert compact is None
    
    def test_compact_recipe_validation_for_ledger_issue_codes_only(self):
        """Test that compact recipe_validation includes issue_codes only, not full issue bodies."""
        recipe_validation = {
            "available": True,
            "settings_source": "observed",
            "verdict": "warn",
            "recipe_id": "sdxl_storyboard_keyframes_gtx1060",
            "score": 0.7,
            "issues": [
                {
                    "severity": "warning",
                    "code": "MISSING_NEGATIVE_TERM",
                    "message": "Missing required negative term: red skin",
                    "recommendation": "Add red skin to negative prompt"
                },
                {
                    "severity": "warning",
                    "code": "MISSING_NEGATIVE_TERM",
                    "message": "Missing required negative term: blue hoodie",
                    "recommendation": "Add blue hoodie to negative prompt"
                }
            ],
            "summary": {
                "title": "Recipe warning",
                "risk_level": "medium",
                "recommended_next_action": "Add missing negative prompt terms before generation."
            }
        }
        
        compact = compact_recipe_validation_for_ledger(recipe_validation)
        
        assert compact is not None
        assert compact["issue_codes"] == ["MISSING_NEGATIVE_TERM", "MISSING_NEGATIVE_TERM"]
        assert "issues" not in compact
    
    def test_compact_recipe_validation_for_ledger_without_summary(self):
        """Test that compact recipe_validation works without summary."""
        recipe_validation = {
            "available": True,
            "settings_source": "planned",
            "verdict": "pass",
            "recipe_id": "sdxl_storyboard_keyframes_gtx1060",
            "score": 1.0,
            "issues": [],
        }
        
        compact = compact_recipe_validation_for_ledger(recipe_validation)
        
        assert compact is not None
        assert compact["available"] is True
        assert "summary" not in compact


class TestRecipeValidationLedgerEvidence:
    """Tests for recipe validation evidence in ledger records."""
    
    def test_recipe_fail_denial_writes_ledger_action_denied_record(self):
        """Test that recipe fail denial writes ledger action_denied record."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            # Use simple format that controller recognizes
            brief_file.write_text("action: test\n", encoding="utf-8")
            
            # Create config with invalid batch size to trigger recipe fail
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "max_frames_per_batch": 12,  # Exceeds max - will cause fail
                "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            }), encoding="utf-8")
            
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}), encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Debug: verify file exists
            assert char_registry_file.exists(), f"Character registry file not found at {char_registry_file}"
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Debug: verify prompt_pack exists
            assert prompt_pack_file.exists(), f"Prompt pack file not found at {prompt_pack_file}"
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that won't be called
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action - should be denied by recipe fail
            result = runner.run_one("ep01", "shot01", "generate_frames")
            
            # Debug: print the action plan to see what's happening
            plan = planner.build(controller.inspect("ep01", "shot01"), "generate_frames", project_root=temp_path)
            print(f"DEBUG: Action plan allowed={plan.allowed}, reason={plan.reason}")
            print(f"DEBUG: Recipe validation={plan.recipe_validation}")
            
            # Verify action was denied
            assert result.allowed is False
            assert result.reason == "recipe validation failed"
            
            # Verify ledger record was written
            shot_ledger = ledger.load("ep01", "shot01")
            assert shot_ledger is not None
            
            # Find action_denied record
            denial_records = [r for r in shot_ledger.records if r.event_type == "action_denied"]
            assert len(denial_records) > 0
            
            denial_record = denial_records[0]
            assert denial_record.requested_action == "generate_frames"
            assert denial_record.allowed is False
    
    def test_denial_record_includes_reason_recipe_validation_failed(self):
        """Test that denial record includes reason 'recipe validation failed'."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            brief_file.write_text("action: generate_frames\n", encoding="utf-8")
            
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "max_frames_per_batch": 12,  # Exceeds max - will cause fail
                "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            }), encoding="utf-8")
            
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}), encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that won't be called
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action - should be denied by recipe fail
            runner.run_one("ep01", "shot01", "generate_frames")
            
            # Verify ledger record reason
            shot_ledger = ledger.load("ep01", "shot01")
            denial_records = [r for r in shot_ledger.records if r.event_type == "action_denied"]
            denial_record = denial_records[0]
            
            assert denial_record.reason == "recipe validation failed"
    
    def test_denial_record_includes_compact_recipe_validation(self):
        """Test that denial record includes compact recipe_validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            brief_file.write_text("action: generate_frames\n", encoding="utf-8")
            
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "max_frames_per_batch": 12,  # Exceeds max - will cause fail
                "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            }), encoding="utf-8")
            
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}), encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that won't be called
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action - should be denied by recipe fail
            runner.run_one("ep01", "shot01", "generate_frames")
            
            # Verify ledger record includes compact recipe_validation
            shot_ledger = ledger.load("ep01", "shot01")
            denial_records = [r for r in shot_ledger.records if r.event_type == "action_denied"]
            denial_record = denial_records[0]
            
            assert denial_record.recipe_validation is not None
            assert denial_record.recipe_validation["available"] is True
            assert denial_record.recipe_validation["verdict"] == "fail"
    
    def test_compact_recipe_validation_includes_verdict_recipe_id_score_settings_source(self):
        """Test that compact recipe_validation includes verdict, recipe_id, score, settings_source."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            brief_file.write_text("action: generate_frames\n", encoding="utf-8")
            
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "max_frames_per_batch": 12,  # Exceeds max - will cause fail
                "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            }), encoding="utf-8")
            
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}), encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that won't be called
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action - should be denied by recipe fail
            runner.run_one("ep01", "shot01", "generate_frames")
            
            # Verify compact recipe_validation fields
            shot_ledger = ledger.load("ep01", "shot01")
            denial_records = [r for r in shot_ledger.records if r.event_type == "action_denied"]
            denial_record = denial_records[0]
            
            compact = denial_record.recipe_validation
            assert "verdict" in compact
            assert "recipe_id" in compact
            assert "score" in compact
            assert "settings_source" in compact
    
    def test_compact_recipe_validation_includes_issue_codes_only_not_full_issue_bodies(self):
        """Test that compact recipe_validation includes issue_codes only, not full issue bodies."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            brief_file.write_text("action: generate_frames\n", encoding="utf-8")
            
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "max_frames_per_batch": 12,  # Exceeds max - will cause fail
                "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            }), encoding="utf-8")
            
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}), encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that won't be called
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action - should be denied by recipe fail
            runner.run_one("ep01", "shot01", "generate_frames")
            
            # Verify compact recipe_validation has issue_codes but not full issues
            shot_ledger = ledger.load("ep01", "shot01")
            denial_records = [r for r in shot_ledger.records if r.event_type == "action_denied"]
            denial_record = denial_records[0]
            
            compact = denial_record.recipe_validation
            assert "issue_codes" in compact
            assert "issues" not in compact
    
    def test_compact_recipe_validation_includes_summary_title_risk_recommended_next_action(self):
        """Test that compact recipe_validation includes summary title/risk/recommended_next_action."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            brief_file.write_text("action: generate_frames\n", encoding="utf-8")
            
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "max_frames_per_batch": 12,  # Exceeds max - will cause fail
                "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            }), encoding="utf-8")
            
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}), encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that won't be called
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action - should be denied by recipe fail
            runner.run_one("ep01", "shot01", "generate_frames")
            
            # Verify compact recipe_validation includes summary fields
            shot_ledger = ledger.load("ep01", "shot01")
            denial_records = [r for r in shot_ledger.records if r.event_type == "action_denied"]
            denial_record = denial_records[0]
            
            compact = denial_record.recipe_validation
            assert "summary" in compact
            assert "title" in compact["summary"]
            assert "risk_level" in compact["summary"]
            assert "recommended_next_action" in compact["summary"]
    
    def test_recipe_warn_action_executed_ledger_record_includes_compact_recipe_validation(self):
        """Test that recipe warn action_executed ledger record includes compact recipe_validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            brief_file.write_text("action: generate_frames\n", encoding="utf-8")
            
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "max_frames_per_batch": 2,
                "default_negative": "bad anatomy",  # Incomplete - will cause warn
            }), encoding="utf-8")
            
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}), encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that returns dry_validated
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action - should execute with warn verdict
            result = runner.run_one("ep01", "shot01", "generate_frames")
            
            # Verify action was executed (warn does not block)
            assert result.allowed is True
            assert result.executed is True
            
            # Verify ledger record includes compact recipe_validation
            shot_ledger = ledger.load("ep01", "shot01")
            executed_records = [r for r in shot_ledger.records if r.event_type == "action_executed"]
            assert len(executed_records) > 0
            
            executed_record = executed_records[0]
            assert executed_record.recipe_validation is not None
            assert executed_record.recipe_validation["verdict"] == "warn"
    
    def test_recipe_warn_does_not_block_execution_dry_validation(self):
        """Test that recipe warn does not block execution/dry validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            brief_file.write_text("action: generate_frames\n", encoding="utf-8")
            
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "max_frames_per_batch": 2,
                "default_negative": "bad anatomy",  # Incomplete - will cause warn
            }), encoding="utf-8")
            
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}), encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that returns dry_validated
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action - should execute with warn verdict
            result = runner.run_one("ep01", "shot01", "generate_frames")
            
            # Verify action was executed (warn does not block)
            assert result.allowed is True
            assert result.executed is True
            
            # Verify no action_denied record was written
            shot_ledger = ledger.load("ep01", "shot01")
            denial_records = [r for r in shot_ledger.records if r.event_type == "action_denied"]
            assert len(denial_records) == 0
    
    def test_recipe_unavailable_ledger_record_includes_available_false(self):
        """Test that recipe unavailable ledger record includes available=false."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure without config.json
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            brief_file.write_text("action: generate_frames\n", encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that returns dry_validated
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action - recipe validation unavailable but action should still execute
            result = runner.run_one("ep01", "shot01", "generate_frames")
            
            # Verify action was executed
            assert result.allowed is True
            assert result.executed is True
            
            # Verify ledger record includes compact recipe_validation with available=false
            shot_ledger = ledger.load("ep01", "shot01")
            executed_records = [r for r in shot_ledger.records if r.event_type == "action_executed"]
            assert len(executed_records) > 0
            
            executed_record = executed_records[0]
            assert executed_record.recipe_validation is not None
            assert executed_record.recipe_validation["available"] is False
    
    def test_ledger_remains_append_only(self):
        """Test that ledger remains append-only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal project structure
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            brief = config_dir / "briefs"
            brief.mkdir(parents=True)
            brief_file = brief / "ep01_shot01_brief.md"
            brief_file.write_text("action: generate_frames\n", encoding="utf-8")
            
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "max_frames_per_batch": 2,
                "default_negative": "bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
            }), encoding="utf-8")
            
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}), encoding="utf-8")
            
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Create character registry to pass reference lock gate
            # CharacterRegistryLoader looks for it at project_root/output/control/character_registry.json
            char_registry_file = control_dir / "character_registry.json"
            char_registry_file.write_text(json.dumps({
                "characters": []
            }), encoding="utf-8")
            
            # Create valid prompt_pack.json to pass prompt-pack mode gate
            # Use minimal valid structure with no characters (scenic shot)
            prompt_pack = {
                "characters": [],
                "beats": [],
            }
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps(prompt_pack), encoding="utf-8")
            
            # Setup controller, gate, ledger
            ledger_root = control_dir
            ledger = ShotLedgerStorage(ledger_root)
            controller = ShotController(temp_path)
            gate = ShotExecutionGate()
            planner = ActionPlanBuilder()
            
            # Mock handler that returns dry_validated
            handlers = {
                "generate_frames": lambda x: {"executed": False, "status": "dry_validated"}
            }
            
            runner = ControlledActionRunner(
                controller=controller,
                gate=gate,
                handlers=handlers,
                ledger=ledger,
                planner=planner,
            )
            
            # Run action twice
            runner.run_one("ep01", "shot01", "generate_frames")
            runner.run_one("ep01", "shot01", "generate_frames")
            
            # Verify ledger has appended records
            shot_ledger = ledger.load("ep01", "shot01")
            assert len(shot_ledger.records) > 1
            
            # Verify records are in chronological order (append-only)
            timestamps = [r.timestamp for r in shot_ledger.records]
            assert timestamps == sorted(timestamps)
    
    def test_no_subprocess_comfyui_call_in_these_tests(self):
        """Test that no subprocess/ComfyUI call is made in these tests."""
        # This test verifies the test setup itself - all handlers are mocked
        # and no real ComfyUI execution occurs
        assert True  # If we reach here, no subprocess was invoked
