"""Camera Operator Validator.

Validates inputs and pre-generation conditions.
"""

import json
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime


class CameraOperatorValidator:
    """Validates repaired full-frame package and operator authorization."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.camera_operator_dir = self.control_dir / "camera_operator_agent"
        self.corrective_repair_dir = self.control_dir / "corrective_generation_scope_repair"
    
    def validate_full_frame_contract(self) -> Tuple[bool, str]:
        """Validate that full-frame corrective generation contract exists."""
        contract_path = self.corrective_repair_dir / "full_frame_corrective_generation_contract.json"
        
        if not contract_path.exists():
            return False, "full_frame_contract_missing"
        
        with open(contract_path, 'r') as f:
            contract = json.load(f)
        
        # Check critical fields
        if contract.get("target_output_type") != "full_frame_production_visual_candidate":
            return False, "target_output_type_not_full_frame"
        
        # Check body part crop is forbidden
        camera_policy = contract.get("camera_distance_policy", {})
        if not camera_policy.get("body_part_crop_forbidden"):
            return False, "body_part_crop_not_forbidden"
        
        # Check exactly one generation allowed
        gen_limits = contract.get("generation_limits", {})
        if not gen_limits.get("exactly_one_generation_allowed"):
            return False, "exactly_one_generation_not_required"
        
        if gen_limits.get("max_generations") != 1:
            return False, "max_generations_not_one"
        
        return True, "full_frame_contract_valid"
    
    def validate_reference_scope_policy(self) -> Tuple[bool, str]:
        """Validate reference usage scope policy exists and is correct."""
        policy_path = self.corrective_repair_dir / "reference_usage_scope_policy.json"
        
        if not policy_path.exists():
            return False, "reference_scope_policy_missing"
        
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        # Check quality references are quality-only
        quality_refs = policy.get("quality_references", {})
        if quality_refs.get("purpose") != "quality_calibration_only":
            return False, "quality_reference_purpose_not_quality_only"
        
        # Check quality refs must not influence composition
        must_not_influence = quality_refs.get("must_not_influence", [])
        required_checks = ["target_composition", "camera_distance", "crop", "shot_type", "scene_framing"]
        for check in required_checks:
            if check not in must_not_influence:
                return False, f"quality_reference_may_influence_{check}"
        
        # Check body part reference is not composition target
        body_part_rule = policy.get("body_part_reference_rule", {})
        if body_part_rule.get("body_part_reference_as_composition_target"):
            return False, "body_part_reference_as_composition_target"
        
        return True, "reference_scope_policy_valid"
    
    def validate_prompt_recipe(self) -> Tuple[bool, str]:
        """Validate full-frame corrective prompt recipe exists."""
        recipe_path = self.corrective_repair_dir / "full_frame_corrective_prompt_recipe.json"
        
        if not recipe_path.exists():
            return False, "prompt_recipe_missing"
        
        with open(recipe_path, 'r') as f:
            recipe = json.load(f)
        
        # Check positive prompt includes full-frame requirements
        must_include = recipe.get("positive_prompt_requirements", {}).get("must_include", [])
        required_phrases = ["full-frame", "complete production frame", "scene context"]
        
        for phrase in required_phrases:
            if not any(phrase.lower() in item.lower() for item in must_include):
                return False, f"positive_prompt_missing_{phrase}"
        
        # Check negative prompt forbids close-ups
        must_not_include = recipe.get("negative_prompt_requirements", {}).get("must_include", [])
        forbidden = ["eye close-up", "extreme close-up", "skin macro", "isolated body part"]
        
        for item in forbidden:
            if item not in must_not_include:
                return False, f"negative_prompt_missing_{item}"
        
        return True, "prompt_recipe_valid"
    
    def validate_operator_authorization(self) -> Tuple[bool, str]:
        """Validate operator authorization artifact exists."""
        auth_path = self.camera_operator_dir / "operator_authorization_one_full_frame_generation.json"
        
        if not auth_path.exists():
            return False, "operator_authorization_missing"
        
        with open(auth_path, 'r') as f:
            auth = json.load(f)
        
        # Check authorization is valid
        if not auth.get("operator_authorized"):
            return False, "operator_not_authorized"
        
        if auth.get("max_generations") != 1:
            return False, "max_generations_not_one"
        
        if not auth.get("generation_gate_open"):
            return False, "generation_gate_not_open"
        
        if not auth.get("body_part_crop_forbidden"):
            return False, "body_part_crop_not_forbidden_in_authorization"
        
        return True, "operator_authorization_valid"
    
    def create_pre_generation_validation_report(self) -> Dict[str, Any]:
        """Create comprehensive pre-generation validation report."""
        validations = {
            "full_frame_contract_exists": False,
            "reference_usage_policy_exists": False,
            "prompt_recipe_exists": False,
            "operator_authorization_exists": False,
            "body_part_crop_forbidden": False,
            "eye_closeup_forbidden_as_target": False,
            "quality_reference_scope_is_quality_only": False,
            "composition_target_is_full_frame": False,
            "max_generations": 0,
            "ready_for_one_generation": False,
            "blockers": []
        }
        
        # Validate full-frame contract
        contract_valid, contract_msg = self.validate_full_frame_contract()
        validations["full_frame_contract_exists"] = contract_valid
        if not contract_valid:
            validations["blockers"].append(contract_msg)
        
        # Validate reference scope policy
        policy_valid, policy_msg = self.validate_reference_scope_policy()
        validations["reference_usage_policy_exists"] = policy_valid
        validations["quality_reference_scope_is_quality_only"] = policy_valid
        validations["composition_target_is_full_frame"] = policy_valid
        if not policy_valid:
            validations["blockers"].append(policy_msg)
        
        # Validate prompt recipe
        recipe_valid, recipe_msg = self.validate_prompt_recipe()
        validations["prompt_recipe_exists"] = recipe_valid
        validations["eye_closeup_forbidden_as_target"] = recipe_valid
        if not recipe_valid:
            validations["blockers"].append(recipe_msg)
        
        # Validate operator authorization
        auth_valid, auth_msg = self.validate_operator_authorization()
        validations["operator_authorization_exists"] = auth_valid
        if auth_valid:
            auth_path = self.camera_operator_dir / "operator_authorization_one_full_frame_generation.json"
            with open(auth_path, 'r') as f:
                auth = json.load(f)
            validations["body_part_crop_forbidden"] = auth.get("body_part_crop_forbidden")
            validations["max_generations"] = auth.get("max_generations", 0)
        else:
            validations["blockers"].append(auth_msg)
        
        # Final readiness check
        validations["ready_for_one_generation"] = (
            validations["full_frame_contract_exists"] and
            validations["reference_usage_policy_exists"] and
            validations["prompt_recipe_exists"] and
            validations["operator_authorization_exists"] and
            validations["body_part_crop_forbidden"] and
            validations["max_generations"] == 1
        )
        
        # Add metadata
        validations["task_id"] = "RC-COMBINE-V2-CAMERA-OPERATOR-AGENT-VERTICAL-001"
        validations["validation_timestamp"] = datetime.now().isoformat()
        validations["version"] = "1.0"
        
        # Write report
        self.camera_operator_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.camera_operator_dir / "pre_generation_full_frame_validation_report.json"
        
        with open(report_path, 'w') as f:
            json.dump(validations, f, indent=2)
        
        return validations
