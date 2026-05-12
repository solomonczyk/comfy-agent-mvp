"""
Validator for Fresh Visual Strategy artifacts.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    artifact_path: str


class StrategyValidator:
    """Validates fresh visual strategy artifacts."""
    
    REQUIRED_ARTIFACTS = [
        "fresh_visual_strategy_manifest.json",
        "fresh_visual_strategy_brief.json",
        "visual_style_direction.json",
        "visual_quality_targets.json",
        "negative_reference_policy.json",
        "reference_acquisition_plan.json",
        "repairability_aware_visual_policy.json",
        "generation_readiness_blocker_policy.json",
        "future_generation_gate_requirements.json",
        "visual_strategy_operator_review_packet.json",
        "fresh_visual_strategy_readiness_report.json"
    ]
    
    REQUIRED_MANIFEST_FIELDS = [
        "task_id",
        "version",
        "timestamp",
        "strategy_type",
        "previous_task",
        "previous_commit",
        "visuals_purged",
        "generation_authorized_by_this_layer",
        "qa_repairability_gate_active",
        "unknown_repairability_blocks"
    ]
    
    REQUIRED_REPAIRABILITY_POLICY_FIELDS = [
        "qa_repairability_gate_required",
        "unknown_repairability_blocks",
        "downstream_requires_validated_repairability",
        "technical_pass_is_not_visual_pass",
        "visual_operator_review_required",
        "production_accepted_must_remain_false"
    ]
    
    REQUIRED_GENERATION_GATE_FIELDS = [
        "generation_authorized_by_this_layer",
        "future_generation_requires_explicit_gate"
    ]
    
    def __init__(self, strategy_dir: Path):
        self.strategy_dir = Path(strategy_dir)
    
    def validate_all(self) -> ValidationResult:
        """Validate all required strategy artifacts."""
        errors = []
        warnings = []
        
        # Check all required artifacts exist
        for artifact in self.REQUIRED_ARTIFACTS:
            artifact_path = self.strategy_dir / artifact
            if not artifact_path.exists():
                errors.append(f"Missing required artifact: {artifact}")
        
        if errors:
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                artifact_path=str(self.strategy_dir)
            )
        
        # Validate individual artifacts
        manifest_result = self.validate_manifest()
        errors.extend(manifest_result.errors)
        warnings.extend(manifest_result.warnings)
        
        repairability_result = self.validate_repairability_policy()
        errors.extend(repairability_result.errors)
        warnings.extend(repairability_result.warnings)
        
        gate_result = self.validate_generation_gate_requirements()
        errors.extend(gate_result.errors)
        warnings.extend(gate_result.warnings)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            artifact_path=str(self.strategy_dir)
        )
    
    def validate_manifest(self) -> ValidationResult:
        """Validate the strategy manifest."""
        manifest_path = self.strategy_dir / "fresh_visual_strategy_manifest.json"
        errors = []
        warnings = []
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Check required fields
            for field in self.REQUIRED_MANIFEST_FIELDS:
                if field not in manifest:
                    errors.append(f"Manifest missing required field: {field}")
            
            # Validate critical boolean fields
            if manifest.get("generation_authorized_by_this_layer") is True:
                errors.append("Manifest generation_authorized_by_this_layer must be false for fresh visual strategy layer")
            
            if manifest.get("qa_repairability_gate_active") is not True:
                errors.append("Manifest qa_repairability_gate_active must be true")
            
            if manifest.get("unknown_repairability_blocks") is not True:
                errors.append("Manifest unknown_repairability_blocks must be true")
            
            # Check forbidden actions are all false
            forbidden = manifest.get("forbidden_actions_enforced", {})
            for action, value in forbidden.items():
                if value is True:
                    errors.append(f"Forbidden action {action} is marked as true in manifest")
        
        except Exception as e:
            errors.append(f"Failed to load manifest: {str(e)}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            artifact_path=str(manifest_path)
        )
    
    def validate_repairability_policy(self) -> ValidationResult:
        """Validate the repairability-aware visual policy."""
        policy_path = self.strategy_dir / "repairability_aware_visual_policy.json"
        errors = []
        warnings = []
        
        try:
            with open(policy_path, 'r') as f:
                policy = json.load(f)
            
            # Access nested structure
            policy_data = policy.get("repairability_aware_visual_policy", policy)
            
            # Check required fields
            for field in self.REQUIRED_REPAIRABILITY_POLICY_FIELDS:
                if field not in policy_data:
                    errors.append(f"Repairability policy missing required field: {field}")
            
            # Validate critical boolean fields
            if policy_data.get("qa_repairability_gate_required") is not True:
                errors.append("Repairability policy qa_repairability_gate_required must be true")
            
            if policy_data.get("unknown_repairability_blocks") is not True:
                errors.append("Repairability policy unknown_repairability_blocks must be true")
            
            if policy_data.get("downstream_requires_validated_repairability") is not True:
                errors.append("Repairability policy downstream_requires_validated_repairability must be true")
            
            if policy_data.get("technical_pass_is_not_visual_pass") is not True:
                errors.append("Repairability policy technical_pass_is_not_visual_pass must be true")
            
            if policy_data.get("visual_operator_review_required") is not True:
                errors.append("Repairability policy visual_operator_review_required must be true")
            
            if policy_data.get("production_accepted_must_remain_false") is not True:
                errors.append("Repairability policy production_accepted_must_remain_false must be true")
            
            # Check defect classification exists
            if "defect_classification" not in policy_data:
                errors.append("Repairability policy missing defect_classification")
        
        except Exception as e:
            errors.append(f"Failed to load repairability policy: {str(e)}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            artifact_path=str(policy_path)
        )
    
    def validate_generation_gate_requirements(self) -> ValidationResult:
        """Validate the future generation gate requirements."""
        gate_path = self.strategy_dir / "future_generation_gate_requirements.json"
        errors = []
        warnings = []
        
        try:
            with open(gate_path, 'r') as f:
                gate = json.load(f)
            
            # Access nested structure
            gate_data = gate.get("future_generation_gate_requirements", gate)
            
            # Check required fields
            for field in self.REQUIRED_GENERATION_GATE_FIELDS:
                if field not in gate_data:
                    errors.append(f"Generation gate requirements missing required field: {field}")
            
            # Validate critical boolean fields
            if gate_data.get("generation_authorized_by_this_layer") is True:
                errors.append("Generation gate requirements generation_authorized_by_this_layer must be false")
            
            if gate_data.get("future_generation_requires_explicit_gate") is not True:
                errors.append("Generation gate requirements future_generation_requires_explicit_gate must be true")
            
            # Check gate status is closed
            gate_status = gate_data.get("gate_status", {})
            if gate_status.get("current_status") != "closed":
                errors.append("Generation gate status must be 'closed' for fresh visual strategy layer")
        
        except Exception as e:
            errors.append(f"Failed to load generation gate requirements: {str(e)}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            artifact_path=str(gate_path)
        )
    
    def validate_forbidden_actions(self, artifact_data: Dict[str, Any]) -> ValidationResult:
        """Validate that all forbidden actions are false."""
        errors = []
        warnings = []
        
        forbidden_fields = [
            "generation_performed",
            "comfyui_submit_executed",
            "retry_attempted",
            "preview_rerender_executed",
            "preview_render_executed",
            "visual_qa_acceptance_executed",
            "operator_visual_acceptance_executed",
            "voice_generation_executed",
            "audio_generation_executed",
            "assembly_executed",
            "final_render_executed",
            "downstream_executed",
            "production_accepted"
        ]
        
        for field in forbidden_fields:
            if field in artifact_data and artifact_data[field] is True:
                errors.append(f"Forbidden action {field} is marked as true")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            artifact_path="artifact_data"
        )
