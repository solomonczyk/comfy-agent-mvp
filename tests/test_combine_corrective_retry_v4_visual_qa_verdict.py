"""Test for RC-COMBINE-V2-2541-2600 — Corrective Retry V4 Full Visual QA Verdict.

This test validates:
- Input packet is required
- Canonical asset is required and validated
- Stub asset is rejected
- Old shot01 asset is rejected for shot02
- Visual QA failed branch routes to visual_correction_plan_required
- Operator concerns are preserved in failed_reasons
- production_accepted is always false
- No generation performed
- No ComfyUI submit
- No assembly executed
- No downstream executed
- next_allowed_action is never "none"
"""

import json
import pytest
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


class TestCorrectiveRetryV4VisualQAVerdict:
    """Test suite for V4 Visual QA verdict command."""

    def test_input_packet_required(self, tmp_path):
        """Test that command fails without input packet."""
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        # No input packet exists
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        assert result == 1
        
        # Verify artifact was not created
        verdict_path = tmp_path / "output" / "control" / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
        assert not verdict_path.exists()

    def test_canonical_asset_required(self, tmp_path):
        """Test that canonical asset must exist and be readable."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create input packet with non-existent asset
        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/nonexistent.png",
            "sha256": "fake_hash",
            "width": 1344,
            "height": 768,
            "canonical_asset_used": True,
            "operator_visual_concerns": {
                "subject_too_small": True,
                "excessive_empty_space": True,
            },
            "known_visual_issues": ["subject_too_small", "excessive_empty_space"],
        }
        
        input_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
        with open(input_path, 'w') as f:
            json.dump(input_packet, f)
        
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        # Should succeed but mark asset as missing
        assert result == 0
        
        # Verify verdict was created
        verdict_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
        assert verdict_path.exists()
        
        with open(verdict_path) as f:
            verdict = json.load(f)
        
        assert verdict["input_validation"]["asset_exists"] is False
        assert verdict["input_validation"]["asset_readable"] is False

    def test_stub_asset_detected(self, tmp_path):
        """Test that stub assets (tiny files) are detected."""
        control_dir = tmp_path / "output" / "control"
        assets_dir = tmp_path / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a tiny stub image file
        asset_path = assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png"
        from PIL import Image
        img = Image.new('RGB', (50, 50), color='red')  # Tiny image < 100x100
        img.save(asset_path)
        
        # Calculate SHA256
        with open(asset_path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        
        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png",
            "sha256": sha256,
            "width": 50,
            "height": 50,
            "canonical_asset_used": True,
            "operator_visual_concerns": {},
            "known_visual_issues": [],
        }
        
        input_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
        with open(input_path, 'w') as f:
            json.dump(input_packet, f)
        
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        assert result == 0
        
        verdict_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
        with open(verdict_path) as f:
            verdict = json.load(f)
        
        assert verdict["input_validation"]["stub_asset_detected"] is True

    def test_old_shot01_asset_rejected_for_shot02(self, tmp_path):
        """Test that old shot01 asset is detected when processing shot02."""
        control_dir = tmp_path / "output" / "control"
        assets_dir = tmp_path / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a proper sized image
        asset_path = assets_dir / "combine_v2_corrective_retry_v4_shot01_00001_.png"
        from PIL import Image
        img = Image.new('RGB', (1344, 768), color='blue')
        img.save(asset_path)
        
        with open(asset_path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        
        # Input packet references shot01 asset but we're processing shot02
        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot01_00001_.png",
            "sha256": sha256,
            "width": 1344,
            "height": 768,
            "canonical_asset_used": False,  # Not canonical for shot02
            "operator_visual_concerns": {},
            "known_visual_issues": [],
        }
        
        input_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
        with open(input_path, 'w') as f:
            json.dump(input_packet, f)
        
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        assert result == 0
        
        verdict_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
        with open(verdict_path) as f:
            verdict = json.load(f)
        
        assert verdict["input_validation"]["old_shot01_asset_used"] is True

    def test_visual_qa_failed_branch(self, tmp_path):
        """Test that failed visual QA routes to visual_correction_plan_required."""
        control_dir = tmp_path / "output" / "control"
        assets_dir = tmp_path / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a proper sized image
        asset_path = assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png"
        from PIL import Image
        img = Image.new('RGB', (1344, 768), color='green')
        img.save(asset_path)
        
        with open(asset_path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        
        # Input packet with operator concerns
        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png",
            "sha256": sha256,
            "width": 1344,
            "height": 768,
            "canonical_asset_used": True,
            "operator_visual_concerns": {
                "subject_too_small": True,
                "excessive_empty_space": True,
                "weak_composition": True,
                "shot_intent_not_satisfied": True,
                "prompt_scene_alignment_weak": True,
            },
            "known_visual_issues": [
                "subject_too_small",
                "excessive_empty_space",
                "weak_composition",
                "shot_intent_not_satisfied",
                "prompt_scene_alignment_weak"
            ],
        }
        
        input_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
        with open(input_path, 'w') as f:
            json.dump(input_packet, f)
        
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        assert result == 0
        
        verdict_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
        with open(verdict_path) as f:
            verdict = json.load(f)
        
        # Verify failed verdict
        assert verdict["visual_qa_verdict"] == "failed"
        assert verdict["production_accepted"] is False
        assert verdict["recommended_next_action"] == "corrective_retry_v4_visual_correction_plan_required"
        
        # Verify all operator concerns are preserved
        assert "subject_too_small" in verdict["failed_reasons"] or any("subject" in r for r in verdict["failed_reasons"])
        assert "excessive_empty_space" in verdict["failed_reasons"] or any("empty" in r for r in verdict["failed_reasons"])
        assert verdict["operator_concerns_preserved"] is True

    def test_production_accepted_always_false(self, tmp_path):
        """Test that production_accepted is always false."""
        control_dir = tmp_path / "output" / "control"
        assets_dir = tmp_path / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        asset_path = assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png"
        from PIL import Image
        img = Image.new('RGB', (1344, 768), color='white')
        img.save(asset_path)
        
        with open(asset_path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        
        # Input packet with NO concerns (should pass if no issues)
        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png",
            "sha256": sha256,
            "width": 1344,
            "height": 768,
            "canonical_asset_used": True,
            "operator_visual_concerns": {},
            "known_visual_issues": [],
        }
        
        input_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
        with open(input_path, 'w') as f:
            json.dump(input_packet, f)
        
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        assert result == 0
        
        verdict_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
        with open(verdict_path) as f:
            verdict = json.load(f)
        
        # Even if QA passes, production_accepted must be false
        assert verdict["production_accepted"] is False

    def test_no_generation_performed(self, tmp_path):
        """Test that no generation is performed."""
        control_dir = tmp_path / "output" / "control"
        assets_dir = tmp_path / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        asset_path = assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png"
        from PIL import Image
        img = Image.new('RGB', (1344, 768), color='black')
        img.save(asset_path)
        
        with open(asset_path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        
        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png",
            "sha256": sha256,
            "width": 1344,
            "height": 768,
            "canonical_asset_used": True,
            "operator_visual_concerns": {"subject_too_small": True},
            "known_visual_issues": ["subject_too_small"],
        }
        
        input_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
        with open(input_path, 'w') as f:
            json.dump(input_packet, f)
        
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        assert result == 0
        
        verdict_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
        with open(verdict_path) as f:
            verdict = json.load(f)
        
        assert verdict["generation_performed"] is False
        assert verdict["comfyui_execution"] is False
        assert verdict["retry_attempted"] is False
        assert verdict["assembly_executed"] is False
        assert verdict["downstream_executed"] is False

    def test_next_allowed_action_not_none(self, tmp_path):
        """Test that next_allowed_action is never 'none'."""
        control_dir = tmp_path / "output" / "control"
        assets_dir = tmp_path / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        asset_path = assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png"
        from PIL import Image
        img = Image.new('RGB', (1344, 768), color='yellow')
        img.save(asset_path)
        
        with open(asset_path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        
        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png",
            "sha256": sha256,
            "width": 1344,
            "height": 768,
            "canonical_asset_used": True,
            "operator_visual_concerns": {"subject_too_small": True},
            "known_visual_issues": ["subject_too_small"],
        }
        
        input_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
        with open(input_path, 'w') as f:
            json.dump(input_packet, f)
        
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        assert result == 0
        
        verdict_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
        with open(verdict_path) as f:
            verdict = json.load(f)
        
        assert verdict["recommended_next_action"] != "none"
        assert verdict["recommended_next_action"] is not None

    def test_artifact_index_updated(self, tmp_path):
        """Test that artifact_index.json is updated correctly."""
        control_dir = tmp_path / "output" / "control"
        assets_dir = tmp_path / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        asset_path = assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png"
        from PIL import Image
        img = Image.new('RGB', (1344, 768), color='purple')
        img.save(asset_path)
        
        with open(asset_path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        
        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png",
            "sha256": sha256,
            "width": 1344,
            "height": 768,
            "canonical_asset_used": True,
            "operator_visual_concerns": {"subject_too_small": True},
            "known_visual_issues": ["subject_too_small"],
        }
        
        input_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
        with open(input_path, 'w') as f:
            json.dump(input_packet, f)
        
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        assert result == 0
        
        artifact_index_path = control_dir / "artifact_index.json"
        assert artifact_index_path.exists()
        
        with open(artifact_index_path) as f:
            index = json.load(f)
        
        assert index["visual_qa_executed"] is True
        assert index["production_accepted"] is False
        assert index["downstream_blocked"] is True

    def test_episode_ledger_updated(self, tmp_path):
        """Test that episode_ledger.json is updated correctly."""
        control_dir = tmp_path / "output" / "control"
        assets_dir = tmp_path / "output" / "assets"
        control_dir.mkdir(parents=True, exist_ok=True)
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        asset_path = assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png"
        from PIL import Image
        img = Image.new('RGB', (1344, 768), color='orange')
        img.save(asset_path)
        
        with open(asset_path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        
        input_packet = {
            "task_id": "RC-COMBINE-V2-2481-2540",
            "packet_type": "corrective_retry_v4_visual_qa_input_packet",
            "shot_id": "shot02",
            "canonical_asset_path": "output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png",
            "sha256": sha256,
            "width": 1344,
            "height": 768,
            "canonical_asset_used": True,
            "operator_visual_concerns": {"subject_too_small": True},
            "known_visual_issues": ["subject_too_small"],
        }
        
        input_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_input_packet.json"
        with open(input_path, 'w') as f:
            json.dump(input_packet, f)
        
        from app.cli import combine_run_corrective_retry_v4_visual_qa
        
        args = MagicMock()
        args.project_root = str(tmp_path)
        args.shot_id = "shot02"
        args.json = True
        
        result = combine_run_corrective_retry_v4_visual_qa(args)
        
        assert result == 0
        
        ledger_path = control_dir / "episode_ledger.json"
        assert ledger_path.exists()
        
        with open(ledger_path) as f:
            ledger = json.load(f)
        
        assert len(ledger) > 0
        last_event = ledger[-1]
        assert last_event["event_type"] == "corrective_retry_v4_visual_qa_executed"
        assert last_event["shot_id"] == "shot02"
        assert last_event["production_accepted"] is False


class TestVisualQAAgentV4Stage:
    """Test suite for VisualQAAgent handling corrective_retry_v4_visual_qa_required stage."""

    def test_v4_stage_supported(self):
        """Test that V4 visual QA stage is in supported_stages."""
        from app.agents.visual_qa_agent import VisualQAAgent
        
        agent = VisualQAAgent()
        assert "corrective_retry_v4_visual_qa_required" in agent.supported_stages

    def test_v4_stage_execution(self, tmp_path):
        """Test that agent correctly processes V4 stage."""
        from app.agents.visual_qa_agent import VisualQAAgent
        from app.orchestrator.contracts import CombineRunContext
        
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        # Create verdict artifact
        verdict = {
            "task_id": "RC-COMBINE-V2-2541-2600",
            "visual_qa_executed": True,
            "visual_qa_verdict": "failed",
            "failed_reasons": ["subject_too_small"],
            "recommended_next_action": "corrective_retry_v4_visual_correction_plan_required",
            "operator_concerns_preserved": True,
            "production_accepted": False,
        }
        
        verdict_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
        with open(verdict_path, 'w') as f:
            json.dump(verdict, f)
        
        agent = VisualQAAgent()
        context = CombineRunContext(
            project_root=str(tmp_path),
            stage="corrective_retry_v4_visual_qa_required",
            current_state="corrective_retry_v4_visual_qa_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.status == "ok"
        assert result.generation_performed is False
        assert result.comfyui_execution is False
        assert result.downstream_executed is False
        assert result.next_recommended_stage == "corrective_retry_v4_visual_correction_plan_required"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
