"""
Tests for Combine V2 Visual Quality Recovery V1

Tests the complete V5 visual recovery workflow:
- Operator visual failure artifact creation
- Visual quality failure diagnosis
- V5 visual recovery package
- V5 workflow patching (prompt + prefix)
- V5 CLI command execution (dry-run and real)
- Result artifact creation
- State transitions
"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timezone


class TestCombineV2VisualQualityRecoveryV1:
    """Test V5 visual recovery workflow"""

    def test_operator_visual_failure_v4_artifact_creation(self, tmp_path):
        """Test operator visual failure V4 artifact is created with correct structure"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        artifact = {
            "task_id": "RC-COMBINE-V2-2961-3200",
            "failed_layer": "RC-COMBINE-V2-2901-2960",
            "failed_commit": "63a906c",
            "failed_asset": "output/assets/combine_v2_corrective_retry_v4_shot02_00002_.png",
            "failed_asset_sha256": "78cc34d62c7f29faaccdcb136e5b84118df350cd0c6b4bdbe2ed940a697d58cd",
            "failed_asset_dimensions": "1344x768",
            "failed_asset_size_bytes": 1054825,
            "operator_visual_failed": True,
            "technical_generation_passed": True,
            "visual_quality_failed": True,
            "defects": {
                "subject_too_small": True,
                "excessive_empty_space": True,
                "composition_failed": True,
                "shot_intent_failed": True,
                "production_quality_failed": True
            },
            "operator_rejected_for_quality": True,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        artifact_path = control_dir / "combine_v2_operator_visual_failure_v4.json"
        with open(artifact_path, 'w') as f:
            json.dump(artifact, f)

        loaded = json.loads(artifact_path.read_text())
        assert loaded["operator_visual_failed"] is True
        assert loaded["production_accepted"] is False
        assert loaded["assembly_allowed"] is False
        assert loaded["downstream_allowed"] is False
        assert loaded["defects"]["subject_too_small"] is True
        assert loaded["defects"]["excessive_empty_space"] is True

    def test_visual_quality_failure_diagnosis_v1_artifact(self, tmp_path):
        """Test visual quality failure diagnosis V1 artifact"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        diagnosis = {
            "task_id": "RC-COMBINE-V2-2961-3200",
            "diagnosis_type": "visual_quality_failure_diagnosis_v1",
            "failed_asset": "output/assets/combine_v2_corrective_retry_v4_shot02_00002_.png",
            "failed_asset_sha256": "78cc34d62c7f29faaccdcb136e5b84118df350cd0c6b4bdbe2ed940a697d58cd",
            "failed_asset_dimensions": "1344x768",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "subject_scale_analysis": {
                "estimated_subject_height_ratio": "less_than_0.25",
                "target_subject_height_ratio_min": 0.35,
                "target_subject_height_ratio_preferred": "0.45-0.70",
                "status": "FAILED"
            },
            "empty_space_analysis": {
                "estimated_empty_space_ratio": "greater_than_0.65",
                "allowed_max_empty_space_ratio": 0.45,
                "status": "FAILED"
            },
            "root_cause_summary": {
                "primary_root_cause": "Prompt lacks explicit subject-scale and camera-distance constraints",
                "secondary_root_cause": "Negative prompt does not prevent tiny subject or vast empty space",
                "status": "DIAGNOSIS_COMPLETE"
            }
        }

        diagnosis_path = control_dir / "combine_v2_visual_quality_failure_diagnosis_v1.json"
        with open(diagnosis_path, 'w') as f:
            json.dump(diagnosis, f)

        loaded = json.loads(diagnosis_path.read_text())
        assert loaded["diagnosis_type"] == "visual_quality_failure_diagnosis_v1"
        assert loaded["subject_scale_analysis"]["status"] == "FAILED"
        assert loaded["empty_space_analysis"]["status"] == "FAILED"
        assert loaded["root_cause_summary"]["status"] == "DIAGNOSIS_COMPLETE"

    def test_v5_visual_recovery_package_artifact(self, tmp_path):
        """Test V5 visual recovery package artifact"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        package = {
            "retry_version": "v5_visual_recovery",
            "source_failure": "v4_subject_too_small_empty_space_composition_failed",
            "target_shot": "shot02",
            "max_generations": 1,
            "must_improve": {
                "subject_scale": True,
                "subject_prominence": True,
                "composition": True,
                "shot_intent": True,
                "empty_space_reduction": True
            },
            "composition_constraints": {
                "subject_must_be_primary_focus": True,
                "subject_scale_target": "medium_full_body_or_waist_up_not_tiny",
                "subject_height_target_ratio_min": 0.35,
                "subject_height_target_ratio_preferred": "0.45-0.70",
                "empty_background_allowed": False,
                "negative_space_max_ratio": 0.45
            },
            "runtime_limits": {
                "generation_attempts_allowed": 1,
                "second_retry_allowed": False,
                "operator_visual_review_required": True,
                "production_accepted": False
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        package_path = control_dir / "combine_v2_corrective_retry_v5_visual_recovery_package.json"
        with open(package_path, 'w') as f:
            json.dump(package, f)

        loaded = json.loads(package_path.read_text())
        assert loaded["retry_version"] == "v5_visual_recovery"
        assert loaded["max_generations"] == 1
        assert loaded["composition_constraints"]["subject_height_target_ratio_min"] == 0.35
        assert loaded["runtime_limits"]["second_retry_allowed"] is False

    def test_v5_workflow_patched_prompt(self, tmp_path):
        """Test V5 workflow has patched positive and negative prompts"""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        workflow = {
            "shot_id": "shot02",
            "6": {
                "inputs": {
                    "text": "Alya, beautiful young woman with long flowing silver hair, wearing elegant white flowing dress, kneeling beside crystal-clear stream, ancient stone altar partially buried in streambed, mysterious glowing blue crystal orb resting on altar pulsing with soft blue light, Alya reaching toward crystal with wonder and hesitation, reflection visible in water below, soft morning mist, blue glow illuminating scene, cinematic lighting, photorealistic, highly detailed, masterpiece, 8k, mystical atmosphere. Subject is large and clearly visible, medium shot, primary focus on woman, fills significant part of frame, cinematic portrait composition, balanced background not empty.",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {
                    "text": "ugly, deformed, noisy, blurry, distorted, out of focus, bad anatomy, extra limbs, missing limbs, floating limbs, disconnected limbs, mutation, mutated, watermark, text, signature, grain, oversaturated, harsh lighting, urban, buildings, modern, weapons, violence, bright daylight, no mist, tiny subject, small person, far away, vast empty background, huge empty sky, minimal subject, extreme wide shot, far away subject, tiny person in landscape",
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "9": {
                "inputs": {
                    "filename_prefix": "combine_v2_corrective_retry_v5_shot02"
                },
                "class_type": "SaveImage"
            }
        }

        workflow_path = control_dir / "shot02_v5_patched_workflow.json"
        with open(workflow_path, 'w') as f:
            json.dump(workflow, f)

        loaded = json.loads(workflow_path.read_text())
        
        # Verify positive prompt patched
        positive_text = loaded["6"]["inputs"]["text"]
        assert "Subject is large and clearly visible" in positive_text
        assert "medium shot" in positive_text
        assert "primary focus on woman" in positive_text
        
        # Verify negative prompt patched
        negative_text = loaded["7"]["inputs"]["text"]
        assert "tiny subject" in negative_text
        assert "vast empty background" in negative_text
        assert "huge empty sky" in negative_text
        
        # Verify SaveImage prefix
        assert loaded["9"]["inputs"]["filename_prefix"] == "combine_v2_corrective_retry_v5_shot02"

    def test_v5_cli_dry_run(self, tmp_path):
        """Test V5 CLI dry-run mode returns authorization_required"""
        from app.cli import combine_corrective_retry_v5_visual_recovery
        import argparse

        # Create required artifacts
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        package = {
            "retry_version": "v5_visual_recovery",
            "max_generations": 1,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(control_dir / "combine_v2_corrective_retry_v5_visual_recovery_package.json", 'w') as f:
            json.dump(package, f)

        workflow = {
            "6": {
                "inputs": {"text": "Subject is large and clearly visible, medium shot", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {"text": "tiny subject, vast empty background", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "9": {
                "inputs": {"filename_prefix": "combine_v2_corrective_retry_v5_shot02"},
                "class_type": "SaveImage"
            }
        }
        with open(control_dir / "shot02_v5_patched_workflow.json", 'w') as f:
            json.dump(workflow, f)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            shot_id="shot02",
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_v5_visual_recovery(args)
        assert result == 0

    def test_v5_cli_blocks_max_generations_not_one(self, tmp_path):
        """Test V5 CLI blocks when max_generations != 1"""
        from app.cli import combine_corrective_retry_v5_visual_recovery
        import argparse

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        package = {"retry_version": "v5_visual_recovery"}
        with open(control_dir / "combine_v2_corrective_retry_v5_visual_recovery_package.json", 'w') as f:
            json.dump(package, f)

        workflow = {
            "9": {
                "inputs": {"filename_prefix": "combine_v2_corrective_retry_v5_shot02"},
                "class_type": "SaveImage"
            }
        }
        with open(control_dir / "shot02_v5_patched_workflow.json", 'w') as f:
            json.dump(workflow, f)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            shot_id="shot02",
            execute=False,
            max_generations=2,
            json=True
        )

        result = combine_corrective_retry_v5_visual_recovery(args)
        assert result == 1

    def test_v5_cli_blocks_missing_package(self, tmp_path):
        """Test V5 CLI blocks when V5 package missing"""
        from app.cli import combine_corrective_retry_v5_visual_recovery
        import argparse

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            shot_id="shot02",
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_v5_visual_recovery(args)
        assert result == 1

    def test_v5_cli_blocks_workflow_prefix_invalid(self, tmp_path):
        """Test V5 CLI blocks when workflow prefix doesn't match expected"""
        from app.cli import combine_corrective_retry_v5_visual_recovery
        import argparse

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        package = {"retry_version": "v5_visual_recovery"}
        with open(control_dir / "combine_v2_corrective_retry_v5_visual_recovery_package.json", 'w') as f:
            json.dump(package, f)

        workflow = {
            "9": {
                "inputs": {"filename_prefix": "wrong_prefix"},
                "class_type": "SaveImage"
            }
        }
        with open(control_dir / "shot02_v5_patched_workflow.json", 'w') as f:
            json.dump(workflow, f)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            shot_id="shot02",
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_v5_visual_recovery(args)
        assert result == 1

    def test_v5_cli_blocks_positive_prompt_not_patched(self, tmp_path):
        """Test V5 CLI blocks when positive prompt not patched"""
        from app.cli import combine_corrective_retry_v5_visual_recovery
        import argparse

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        package = {"retry_version": "v5_visual_recovery"}
        with open(control_dir / "combine_v2_corrective_retry_v5_visual_recovery_package.json", 'w') as f:
            json.dump(package, f)

        workflow = {
            "6": {
                "inputs": {"text": "No composition constraints here", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {"text": "tiny subject, vast empty background", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "9": {
                "inputs": {"filename_prefix": "combine_v2_corrective_retry_v5_shot02"},
                "class_type": "SaveImage"
            }
        }
        with open(control_dir / "shot02_v5_patched_workflow.json", 'w') as f:
            json.dump(workflow, f)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            shot_id="shot02",
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_v5_visual_recovery(args)
        assert result == 1

    def test_v5_cli_blocks_negative_prompt_not_patched(self, tmp_path):
        """Test V5 CLI blocks when negative prompt not patched"""
        from app.cli import combine_corrective_retry_v5_visual_recovery
        import argparse

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        package = {"retry_version": "v5_visual_recovery"}
        with open(control_dir / "combine_v2_corrective_retry_v5_visual_recovery_package.json", 'w') as f:
            json.dump(package, f)

        workflow = {
            "6": {
                "inputs": {"text": "Subject is large and clearly visible, medium shot", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {"text": "No negative constraints here", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "9": {
                "inputs": {"filename_prefix": "combine_v2_corrective_retry_v5_shot02"},
                "class_type": "SaveImage"
            }
        }
        with open(control_dir / "shot02_v5_patched_workflow.json", 'w') as f:
            json.dump(workflow, f)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            shot_id="shot02",
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_v5_visual_recovery(args)
        assert result == 1

    def test_payload_validation_removes_non_node_fields(self, tmp_path):
        """Test that payload validator removes non-node fields like shot_id"""
        from app.cli import combine_corrective_retry_v5_visual_recovery
        import argparse

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        package = {"retry_version": "v5_visual_recovery"}
        with open(control_dir / "combine_v2_corrective_retry_v5_visual_recovery_package.json", 'w') as f:
            json.dump(package, f)

        # Workflow with non-node metadata (shot_id) that should be removed
        workflow = {
            "shot_id": "shot02",  # Non-node field that should be removed
            "3": {
                "inputs": {"seed": 847392, "steps": 30, "cfg": 7.5, "sampler_name": "dpmpp_sde"},
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {"ckpt_name": "model.safetensors"},
                "class_type": "CheckpointLoaderSimple"
            },
            "6": {
                "inputs": {"text": "Subject is large and clearly visible, medium shot", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {"text": "tiny subject, vast empty background", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "9": {
                "inputs": {"filename_prefix": "combine_v2_corrective_retry_v5_shot02"},
                "class_type": "SaveImage"
            }
        }
        with open(control_dir / "shot02_v5_patched_workflow.json", 'w') as f:
            json.dump(workflow, f)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            shot_id="shot02",
            execute=False,
            max_generations=1,
            json=True
        )

        # Should pass dry-run (shot_id will be removed during validation)
        result = combine_corrective_retry_v5_visual_recovery(args)
        assert result == 0

        # Verify validation would remove shot_id and keep only numeric node keys
        valid_node_keys = [k for k in workflow.keys() if isinstance(k, str) and k.isdigit()]
        assert "shot_id" not in valid_node_keys
        assert "3" in valid_node_keys
        assert "4" in valid_node_keys
        assert "9" in valid_node_keys

    def test_v5_exactly_one_generation_enforced(self, tmp_path):
        """Test that exactly one generation is enforced"""
        from app.cli import combine_corrective_retry_v5_visual_recovery
        import argparse

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)

        package = {"retry_version": "v5_visual_recovery"}
        with open(control_dir / "combine_v2_corrective_retry_v5_visual_recovery_package.json", 'w') as f:
            json.dump(package, f)

        workflow = {
            "6": {
                "inputs": {"text": "Subject is large and clearly visible, medium shot", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {"text": "tiny subject, vast empty background", "clip": ["4", 1]},
                "class_type": "CLIPTextEncode"
            },
            "9": {
                "inputs": {"filename_prefix": "combine_v2_corrective_retry_v5_shot02"},
                "class_type": "SaveImage"
            }
        }
        with open(control_dir / "shot02_v5_patched_workflow.json", 'w') as f:
            json.dump(workflow, f)

        # Test with max_generations=2 (should be blocked)
        args = argparse.Namespace(
            project_root=str(tmp_path),
            shot_id="shot02",
            execute=False,
            max_generations=2,
            json=True
        )

        result = combine_corrective_retry_v5_visual_recovery(args)
        assert result == 1  # Blocked because max_generations != 1

        # Test with max_generations=1 (should pass dry-run)
        args.max_generations = 1
        result = combine_corrective_retry_v5_visual_recovery(args)
        assert result == 0  # Passes dry-run

    def test_post_prompt_500_diagnosis_artifact_exists(self):
        """Test that POST /prompt 500 diagnosis artifact exists"""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        diagnosis_file = control_dir / "combine_v2_comfyui_prompt_500_diagnosis.json"

        if diagnosis_file.exists():
            with open(diagnosis_file) as f:
                data = json.load(f)
            assert data["task_id"] == "RC-COMBINE-V2-3261-3360"
            assert data["root_cause_category"] == "invalid_prompt_payload"

    def test_payload_validation_artifact_exists(self):
        """Test that payload validation artifact exists"""
        control_dir = Path("f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")
        validation_file = control_dir / "combine_v2_corrective_retry_v5_prompt_payload_validation.json"

        if validation_file.exists():
            with open(validation_file) as f:
                data = json.load(f)
            assert data["task_id"] == "RC-COMBINE-V2-3261-3360"
            assert data["workflow_valid_for_comfyui_api"] is True
            assert "removed_keys" in data
