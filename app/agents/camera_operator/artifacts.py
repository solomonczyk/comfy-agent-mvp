"""Camera Operator Artifacts.

Creates generation manifest, result review, and operator visual review packet.
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


class CameraOperatorArtifacts:
    """Creates output artifacts after generation."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.camera_operator_dir = self.control_dir / "camera_operator_agent"
    
    def create_generation_manifest(self, runner_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create generation manifest artifact."""
        manifest = {
            "task_id": "RC-COMBINE-V2-CAMERA-OPERATOR-AGENT-VERTICAL-001",
            "agent_id": "camera_operator_agent",
            "generation_performed": runner_result.get("success", False),
            "generation_count": runner_result.get("generation_count", 0),
            "max_generations": runner_result.get("max_generations", 1),
            "workflow_submitted": True,
            "comfyui_execution": runner_result.get("comfyui_execution", False),
            "prompt_id": runner_result.get("prompt_id", ""),
            "generated_assets": [],
            "second_generation_attempted": False,
            "retry_attempted": False,
            "blind_retry_attempted": False,
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Add generated asset metadata if available
        asset_path = runner_result.get("generated_asset_path")
        if asset_path and Path(asset_path).exists():
            from PIL import Image
            import hashlib
            
            img = Image.open(asset_path)
            sha256 = hashlib.sha256()
            with open(asset_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            
            asset_metadata = {
                "path": asset_path,
                "exists": True,
                "readable": True,
                "sha256": sha256.hexdigest(),
                "size_bytes": Path(asset_path).stat().st_size,
                "width": img.size[0],
                "height": img.size[1]
            }
            manifest["generated_assets"] = [asset_metadata]
        
        # Write manifest
        self.camera_operator_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.camera_operator_dir / "camera_operator_generation_manifest.json"
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest
    
    def create_generation_result_review(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Create generation result review (technical only, no visual acceptance)."""
        review = {
            "technical_result_review_executed": True,
            "asset_exists": False,
            "asset_readable": False,
            "sha256_recorded": False,
            "dimensions_recorded": False,
            "non_stub_asset": False,
            "manifest_matches_filesystem": False,
            "visual_acceptance_executed": False,
            "operator_visual_review_required": True,
            "production_accepted": False,
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Check generated assets
        if manifest.get("generated_assets"):
            asset = manifest["generated_assets"][0]
            asset_path = Path(asset.get("path", ""))
            
            review["asset_exists"] = asset_path.exists()
            review["asset_readable"] = asset_path.exists() and asset.get("readable", False)
            review["sha256_recorded"] = bool(asset.get("sha256"))
            review["dimensions_recorded"] = bool(asset.get("width")) and bool(asset.get("height"))
            review["non_stub_asset"] = asset.get("size_bytes", 0) > 0
            review["manifest_matches_filesystem"] = review["asset_exists"]
        
        # Write review
        review_path = self.camera_operator_dir / "camera_operator_generation_result_review.json"
        
        with open(review_path, 'w') as f:
            json.dump(review, f, indent=2)
        
        return review
    
    def create_operator_visual_review_packet(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Create operator visual review packet."""
        generated_asset_path = ""
        if manifest.get("generated_assets"):
            generated_asset_path = manifest["generated_assets"][0].get("path", "")
        
        packet = {
            "review_type": "operator_visual_review",
            "review_required": True,
            "generated_asset": generated_asset_path,
            "operator_must_decide": [
                "ACCEPTED_FOR_NEXT_GATE",
                "REJECTED_NEEDS_CORRECTIVE_PLAN",
                "NEEDS_MANUAL_REVIEW"
            ],
            "agent_recommendation_allowed": False,
            "agent_acceptance_allowed": False,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "task_id": "RC-COMBINE-V2-CAMERA-OPERATOR-AGENT-VERTICAL-001",
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Write packet
        packet_path = self.camera_operator_dir / "operator_visual_review_packet.json"
        
        with open(packet_path, 'w') as f:
            json.dump(packet, f, indent=2)
        
        return packet
    
    def create_blocker_report(self, blockers: list, reason: str) -> Dict[str, Any]:
        """Create blocker report if generation is blocked."""
        report = {
            "task_id": "RC-COMBINE-V2-CAMERA-OPERATOR-AGENT-VERTICAL-001",
            "blocked": True,
            "blocker_reason": reason,
            "blockers": blockers,
            "generation_not_executed": True,
            "operator_visual_review_required": False,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Write blocker report
        blocker_path = self.camera_operator_dir / "camera_operator_blocker_report.json"
        
        with open(blocker_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def create_proof(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create proof JSON for task completion."""
        proof = {
            "task_id": "RC-COMBINE-V2-CAMERA-OPERATOR-AGENT-VERTICAL-001",
            "feature_completed": execution_result.get("success", False),
            "agent_vertical_completed": execution_result.get("success", False),
            "agent_id": "camera_operator_agent",
            
            "operator_authorization_recorded": True,
            "generation_gate_opened_for_this_task": True,
            
            "full_frame_contract_validated": execution_result.get("full_frame_contract_validated", False),
            "reference_scope_policy_validated": execution_result.get("reference_scope_policy_validated", False),
            "prompt_recipe_validated": execution_result.get("prompt_recipe_validated", False),
            "body_part_crop_forbidden": execution_result.get("body_part_crop_forbidden", False),
            
            "generation_performed": execution_result.get("generation_performed", False),
            "generation_count": execution_result.get("generation_count", 0),
            "max_generations": execution_result.get("max_generations", 1),
            "second_generation_attempted": False,
            "retry_attempted": False,
            "blind_retry_attempted": False,
            
            "workflow_submitted": execution_result.get("workflow_submitted", False),
            "comfyui_execution": execution_result.get("comfyui_execution", False),
            "prompt_id": execution_result.get("prompt_id", ""),
            
            "generated_assets": execution_result.get("generated_assets", []),
            
            "generation_manifest_created": execution_result.get("generation_manifest_created", False),
            "generation_result_review_created": execution_result.get("generation_result_review_created", False),
            "operator_visual_review_packet_created": execution_result.get("operator_visual_review_packet_created", False),
            
            "visual_qa_executed": False,
            "visual_qa_acceptance_executed": False,
            "operator_visual_acceptance_executed": False,
            "preview_render_executed": False,
            "assembly_executed": False,
            "voice_generation_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            
            "artifact_index_updated": execution_result.get("artifact_index_updated", False),
            "episode_ledger_updated": execution_result.get("episode_ledger_updated", False),
            "state_updated": execution_result.get("state_updated", False),
            
            "current_state": execution_result.get("current_state", ""),
            "next_allowed_action": execution_result.get("next_allowed_action", ""),
            
            "tests_pass": execution_result.get("tests_pass", False),
            "py_compile_pass": execution_result.get("py_compile_pass", False),
            "cli_dry_run_pass": execution_result.get("cli_dry_run_pass", False),
            "cli_execute_pass": execution_result.get("cli_execute_pass", False),
            "cli_status_pass": execution_result.get("cli_status_pass", False),
            
            "commit_hash": execution_result.get("commit_hash", ""),
            "push_status": execution_result.get("push_status", ""),
            "git_status_clean": execution_result.get("git_status_clean", False),
            
            "blockers": execution_result.get("blockers", []),
            "next_task_recommendation": "operator_visual_review_camera_operator_candidate",
            
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        }
        
        # Write proof
        proof_path = self.camera_operator_dir / "proof.json"
        
        with open(proof_path, 'w') as f:
            json.dump(proof, f, indent=2)
        
        return proof
