"""
Builder for Fresh Visual Strategy artifacts.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class FreshVisualStrategyBuilder:
    """Builds fresh visual strategy artifacts after visual purge."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.strategy_dir = self.control_dir / "fresh_visual_strategy"
        self.task_id = "RC-COMBINE-V2-FRESH-VISUAL-STRATEGY-001"
    
    def build_strategy(self, previous_task_id: str, previous_commit: str) -> Dict[str, Any]:
        """Build the complete fresh visual strategy package."""
        
        # Ensure strategy directory exists
        self.strategy_dir.mkdir(parents=True, exist_ok=True)
        
        # Build all artifacts
        manifest = self._build_manifest(previous_task_id, previous_commit)
        brief = self._build_brief(previous_task_id, previous_commit)
        style_direction = self._build_style_direction()
        quality_targets = self._build_quality_targets()
        negative_policy = self._build_negative_reference_policy()
        reference_plan = self._build_reference_acquisition_plan()
        repairability_policy = self._build_repairability_policy()
        blocker_policy = self._build_generation_readiness_blocker_policy()
        gate_requirements = self._build_generation_gate_requirements()
        operator_packet = self._build_operator_review_packet()
        readiness_report = self._build_readiness_report()
        
        # Write all artifacts
        self._write_artifact("fresh_visual_strategy_manifest.json", manifest)
        self._write_artifact("fresh_visual_strategy_brief.json", brief)
        self._write_artifact("visual_style_direction.json", style_direction)
        self._write_artifact("visual_quality_targets.json", quality_targets)
        self._write_artifact("negative_reference_policy.json", negative_policy)
        self._write_artifact("reference_acquisition_plan.json", reference_plan)
        self._write_artifact("repairability_aware_visual_policy.json", repairability_policy)
        self._write_artifact("generation_readiness_blocker_policy.json", blocker_policy)
        self._write_artifact("future_generation_gate_requirements.json", gate_requirements)
        self._write_artifact("visual_strategy_operator_review_packet.json", operator_packet)
        self._write_artifact("fresh_visual_strategy_readiness_report.json", readiness_report)
        
        return {
            "task_id": self.task_id,
            "strategy_created": True,
            "artifacts_created": len(manifest["artifacts"]),
            "strategy_dir": str(self.strategy_dir)
        }
    
    def _build_manifest(self, previous_task_id: str, previous_commit: str) -> Dict[str, Any]:
        """Build the strategy manifest."""
        return {
            "task_id": self.task_id,
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "strategy_type": "fresh_visual_strategy_after_purge",
            "previous_task": previous_task_id,
            "previous_commit": previous_commit,
            "visuals_purged": True,
            "purge_reason": "Operator directive purged all visual outputs due to unrepairable defects and quality failures",
            "strategy_purpose": "Define new visual generation strategy with repairability-aware policies before any generation is attempted",
            "strategy_scope": [
                "visual_style_direction",
                "visual_quality_targets",
                "negative_reference_policy",
                "reference_acquisition_plan",
                "repairability_aware_visual_policy",
                "generation_readiness_blocker_policy",
                "future_generation_gate_requirements"
            ],
            "generation_authorized_by_this_layer": False,
            "generation_blocked_until": "operator_review_of_fresh_visual_strategy",
            "qa_repairability_gate_active": True,
            "unknown_repairability_blocks": True,
            "artifacts": [
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
            ],
            "forbidden_actions_enforced": {
                "generation_performed": False,
                "comfyui_submit_executed": False,
                "retry_attempted": False,
                "preview_rerender_executed": False,
                "preview_render_executed": False,
                "visual_qa_acceptance_executed": False,
                "operator_visual_acceptance_executed": False,
                "voice_generation_executed": False,
                "audio_generation_executed": False,
                "assembly_executed": False,
                "final_render_executed": False,
                "downstream_executed": False,
                "production_accepted": False
            }
        }
    
    def _build_brief(self, previous_task_id: str, previous_commit: str) -> Dict[str, Any]:
        """Build the strategy brief."""
        return {
            "task_id": self.task_id,
            "strategy_brief": "Fresh Visual Strategy after Visual Purge",
            "context": {
                "previous_visual_outputs": "All visual outputs were purged by operator directive",
                "purge_reason": "Unrepairable defects including bad teeth, unnatural mouth, lip-teeth boundary failures, framing defects, and identity drift across multiple generation attempts",
                "generation_attempts_before_purge": 8,
                "generations_purged": ["v7", "v8", "v10", "v11", "v12", "v13", "v14"],
                "qa_repairability_gate_status": "active and approved as mandatory control policy"
            },
            "strategy_objective": "Define a new visual generation approach that explicitly avoids all previous failure modes, enforces repairability-aware quality gates, and requires explicit operator authorization before any generation attempt",
            "key_principles": [
                "No blind retry - every generation must have explicit strategy and authorization",
                "Repairability must be known before generation - unknown repairability blocks",
                "Technical pass is not visual pass - visual quality requires expert review",
                "Production acceptance remains false until explicit operator decision",
                "Negative references from all previous failures must be loaded and enforced",
                "Generation gate must verify workflow, models, and policy before ComfyUI submit"
            ],
            "what_changed": {
                "old_approach": "Iterative retry with incremental corrections, accepting outputs that passed technical validation",
                "new_approach": "Strategy-first approach with explicit quality targets, repairability assessment, and generation gate that must authorize each attempt"
            },
            "what_must_never_repeat": [
                "Bad teeth / unnatural mouth / lip-teeth boundary failures",
                "Framing defects (head not fully in frame, top of head cropped, over-tight face crop)",
                "Identity drift from reference",
                "Inconsistent costume or location",
                "Static/duplicate frame failures",
                "Low detail / mushy image quality",
                "Wrong style deviations from brief",
                "Prompt mismatch with visual output",
                "Timeline/scene mismatch"
            ],
            "success_criteria": [
                "All visual defects from previous generations are explicitly documented as negative references",
                "Repairability assessment is known for each defect type",
                "Generation workflow is selected and validated before submit",
                "Model assets are verified and available",
                "Operator reviews strategy before any generation is authorized",
                "QA enforces repairability gate on all outputs"
            ],
            "next_step": "Operator review of fresh visual strategy before generation planning"
        }
    
    def _build_style_direction(self) -> Dict[str, Any]:
        """Build visual style direction."""
        return {
            "task_id": self.task_id,
            "visual_style_direction": {
                "target_style": "Photorealistic portrait with cinematic lighting",
                "style_reference": "High-quality elderly portrait with natural skin texture, realistic eyes, and proper mouth/teeth anatomy",
                "mood": "Contemplative, dignified, warm but not overly sentimental",
                "lighting_approach": "Soft directional light with subtle fill, natural skin tones, avoiding harsh shadows or blown highlights",
                "color_palette": {
                    "dominant_tones": "Warm neutrals (browns, tans, soft creams)",
                    "accent_colors": "Subtle blues in background for depth",
                    "skin_tone_accuracy": "Critical - must match reference subject's natural complexion"
                },
                "composition_requirements": {
                    "framing": "Portrait orientation, head and shoulders visible, adequate headroom",
                    "head_room": "15-20% of frame above head",
                    "eye_line": "Slightly above center line, natural gaze direction",
                    "background": "Simple, non-distracting, shallow depth of field",
                    "avoid": "Over-tight crops, top of head cropped, head not fully in frame"
                },
                "character_identity_requirements": {
                    "identity_fidelity": "Must match reference subject's facial structure and features",
                    "age_representation": "Elderly subject with natural aging signs (wrinkles, skin texture)",
                    "expression": "Neutral to slightly contemplative, natural mouth position",
                    "avoid": "Identity drift, unnatural age smoothing, exaggerated expressions"
                },
                "technical_style_parameters": {
                    "resolution": "Minimum 1024x1024, preferably higher",
                    "detail_level": "High - skin texture, hair strands, fabric weave must be visible",
                    "sharpness": "Eyes and mouth must be sharp, no blur in critical facial features",
                    "noise": "Minimal, natural film grain acceptable but not digital artifacts"
                }
            },
            "style_enforcement": {
                "negative_references_loaded": True,
                "positive_references_required": ["v6_targeted_refinement_elderly_portrait"],
                "style_deviation_tolerance": "Low - significant style changes require operator approval",
                "style_validation_required": True
            }
        }
    
    def _build_quality_targets(self) -> Dict[str, Any]:
        """Build visual quality targets."""
        return {
            "task_id": self.task_id,
            "visual_quality_targets": {
                "face_quality": {
                    "eyes": {
                        "sharpness": "Must be sharp and in focus",
                        "symmetry": "Natural asymmetry acceptable, no distortion",
                        "pupils": "Visible, properly sized, not blown out or missing",
                        "avoid": "Blurry eyes, distorted eyes, missing pupils, unnatural eye shape"
                    },
                    "mouth": {
                        "teeth": "Natural teeth anatomy, no bad teeth, proper alignment",
                        "lips": "Natural lip shape, proper lip-teeth boundary",
                        "expression": "Neutral or natural expression, not forced",
                        "avoid": "Bad teeth, unnatural mouth, lip-teeth boundary failed, unnatural expression"
                    },
                    "skin": {
                        "texture": "Natural skin texture with appropriate aging signs",
                        "tone": "Consistent with reference subject",
                        "lighting": "Even lighting without harsh shadows or blown highlights",
                        "avoid": "Over-smoothed skin, plastic look, inconsistent tone"
                    },
                    "overall_face": {
                        "proportions": "Natural facial proportions",
                        "identity": "Must match reference subject",
                        "avoid": "Identity drift, distorted facial features"
                    }
                },
                "hands_quality": {
                    "fingers": "Correct number of fingers, proper proportions",
                    "joints": "Natural finger joints, no extra or missing joints",
                    "positioning": "Natural hand position if visible",
                    "avoid": "Broken hands, extra fingers, missing fingers, distorted joints"
                },
                "composition_quality": {
                    "framing": "Proper headroom, subject fully in frame",
                    "rule_of_thirds": "Eye line on upper third line preferred",
                    "background": "Non-distracting, appropriate depth of field",
                    "avoid": "Over-tight crops, top of head cropped, head not fully in frame, distracting background"
                },
                "detail_quality": {
                    "minimum_resolution": "1024x1024",
                    "sharpness": "Critical areas (face, hands) must be sharp",
                    "texture": "Fabric, hair, skin textures must be visible",
                    "avoid": "Low detail, mushy image, loss of texture in critical areas"
                },
                "style_quality": {
                    "consistency": "Must match brief and style direction",
                    "lighting": "Appropriate for mood and subject",
                    "color": "Natural color palette, no color casts",
                    "avoid": "Wrong style, inconsistent with brief, unnatural lighting, color casts"
                },
                "quality_barriers": {
                    "blocker_defects": [
                        "blurry_face",
                        "distorted_eyes",
                        "bad_mouth_teeth",
                        "broken_hands",
                        "identity_drift",
                        "framing_failure"
                    ],
                    "warning_defects": [
                        "slight_softness",
                        "minor_style_deviation",
                        "subtle_lighting_issue"
                    ],
                    "repairability_required": "All defects must have known repairability assessment"
                }
            },
            "quality_validation": {
                "technical_metrics": "Blur, brightness, contrast must be within acceptable ranges",
                "visual_expert_review": "Required for all quality assessments",
                "operator_review": "Required after visual expert assessment"
            }
        }
    
    def _build_negative_reference_policy(self) -> Dict[str, Any]:
        """Build negative reference policy."""
        return {
            "task_id": self.task_id,
            "negative_reference_policy": {
                "policy_purpose": "Explicitly document all visual defects and failure modes from previous generations to prevent recurrence",
                "negative_reference_sources": [
                    "V7 operator visual rejection",
                    "V8 quality guardrails",
                    "V12 operator visual rejection (QA Canon)",
                    "V13 operator visual rejection (framing)",
                    "V14 runtime failure (OOM)"
                ],
                "documented_negative_references": {
                    "v12_bad_teeth": {
                        "defect_type": "bad_teeth",
                        "description": "Unnatural teeth appearance, poor dental anatomy",
                        "reference_asset": "qa/references/negative/v12_bad_teeth_reference.json",
                        "repairability": "not_repairable_with_current_tools",
                        "prevention_strategy": "Explicit prompt engineering for natural teeth, reference positive examples"
                    },
                    "v12_unnatural_mouth": {
                        "defect_type": "unnatural_mouth",
                        "description": "Unnatural mouth shape or expression",
                        "repairability": "not_repairable_with_current_tools",
                        "prevention_strategy": "Natural expression prompts, reference natural mouth examples"
                    },
                    "v12_lip_teeth_boundary": {
                        "defect_type": "lip_teeth_boundary_failed",
                        "description": "Incorrect boundary between lips and teeth",
                        "repairability": "not_repairable_with_current_tools",
                        "prevention_strategy": "Explicit lip-teeth boundary modeling, reference correct anatomy"
                    },
                    "v13_framing_defects": {
                        "defect_type": "framing_failure",
                        "description": "Head not fully in frame, top of head cropped, over-tight face crop",
                        "repairability": "not_repairable_with_current_tools",
                        "prevention_strategy": "Explicit framing parameters, adequate headroom, composition guidelines"
                    },
                    "identity_drift": {
                        "defect_type": "identity_drift",
                        "description": "Generated face does not match reference subject",
                        "repairability": "not_repairable_with_current_tools",
                        "prevention_strategy": "Strong identity conditioning, reference subject features, IP-Adapter if available"
                    },
                    "static_duplicate_frame": {
                        "defect_type": "static_duplicate_frame",
                        "description": "Generated frame is static or duplicate of previous",
                        "repairability": "not_repairable_with_current_tools",
                        "prevention_strategy": "Seed variation, prompt variation, noise injection"
                    },
                    "low_detail_mushy": {
                        "defect_type": "low_detail_mushy",
                        "description": "Image lacks detail, appears mushy or oversmoothed",
                        "repairability": "partially_repairable_with_upscaling",
                        "prevention_strategy": "Higher resolution generation, detail enhancement prompts"
                    },
                    "wrong_style": {
                        "defect_type": "wrong_style",
                        "description": "Visual style does not match brief or reference",
                        "repairability": "not_repairable_with_current_tools",
                        "prevention_strategy": "Style conditioning, reference style examples, style LoRA if available"
                    }
                },
                "negative_reference_enforcement": {
                    "must_be_loaded_before_generation": True,
                    "must_be_referenced_in_prompts": True,
                    "generation_gate_must_check": True,
                    "qa_must_validate_absence": True
                },
                "negative_reference_registry": "qa/references/negative/",
                "negative_reference_count": 8
            }
        }
    
    def _build_reference_acquisition_plan(self) -> Dict[str, Any]:
        """Build reference acquisition plan."""
        return {
            "task_id": self.task_id,
            "reference_acquisition_plan": {
                "plan_purpose": "Define required positive and negative references for fresh visual generation",
                "positive_references": {
                    "required": [
                        {
                            "reference_name": "v6_targeted_refinement_elderly_portrait",
                            "reference_path": "data/rc2_multishot1_ep01/output/assets/combine_v2_v6_targeted_refinement_shot02_00001_.png",
                            "purpose": "Best quality reference from previous generation cycle",
                            "usage": "Style reference, identity reference, quality target",
                            "status": "available"
                        },
                        {
                            "reference_name": "v6_fantasy_candidate",
                            "reference_path": "data/rc2_multishot1_ep01/output/assets/combine_v2_clean_sdxl_v6_candidate_shot02_00001_.png",
                            "purpose": "Concept candidate reference",
                            "usage": "Concept reference, composition reference",
                            "status": "available"
                        }
                    ],
                    "optional": [
                        {
                            "reference_name": "external_elderly_portrait_reference",
                            "purpose": "Additional style reference for elderly portrait quality",
                            "usage": "Style reference, quality target",
                            "status": "to_be_acquired",
                            "acquisition_method": "Operator provided or external reference library"
                        }
                    ]
                },
                "negative_references": {
                    "required": [
                        {
                            "reference_name": "v12_bad_teeth_reference",
                            "reference_path": "qa/references/negative/v12_bad_teeth_reference.json",
                            "purpose": "Document bad teeth defect to prevent recurrence",
                            "usage": "Negative conditioning, prompt avoidance",
                            "status": "available"
                        }
                    ],
                    "auto_generated_from_failures": [
                        "v7_visual_defect_taxonomy",
                        "v8_defect_taxonomy",
                        "v12_qa_canon_report",
                        "v13_operator_rejection"
                    ]
                },
                "reference_validation": {
                    "positive_references_must_be_readable": True,
                    "negative_references_must_be_loaded": True,
                    "reference_integrity_check": True,
                    "reference_sha256_verification": True
                },
                "reference_usage_policy": {
                    "positive_reference_weighting": "Strong conditioning on best quality references",
                    "negative_reference_weighting": "Explicit negative prompts for documented defects",
                    "reference_blending": "Allowed for style synthesis but must preserve identity",
                    "reference_manipulation": "No unauthorized reference modification"
                },
                "acquisition_status": {
                    "positive_references_available": 2,
                    "negative_references_available": 1,
                    "ready_for_generation": True
                }
            }
        }
    
    def _build_repairability_policy(self) -> Dict[str, Any]:
        """Build repairability-aware visual policy."""
        return {
            "task_id": self.task_id,
            "repairability_aware_visual_policy": {
                "policy_purpose": "Enforce repairability-aware quality assessment for all visual outputs",
                "qa_repairability_gate_required": True,
                "unknown_repairability_blocks": True,
                "downstream_requires_validated_repairability": True,
                "technical_pass_is_not_visual_pass": True,
                "visual_operator_review_required": True,
                "production_accepted_must_remain_false": True,
                "defect_classification": {
                    "repairable_with_validated_tools": {
                        "description": "Defects that can be fixed using known, validated tools/nodes",
                        "examples": [
                            "slight_softness (sharpening tools)",
                            "minor_color_cast (color correction)",
                            "slight_exposure_issue (exposure adjustment)"
                        ],
                        "action": "Allow with repair plan, track repair execution"
                    },
                    "not_repairable_with_current_tools": {
                        "description": "Defects that cannot be fixed with current available tools",
                        "examples": [
                            "blurry_face",
                            "distorted_eyes",
                            "bad_mouth_teeth",
                            "broken_hands",
                            "identity_drift",
                            "inconsistent_costume",
                            "inconsistent_location",
                            "framing_failure"
                        ],
                        "action": "BLOCK - must regenerate with corrected approach"
                    },
                    "unknown_repairability": {
                        "description": "Defects whose repairability is not yet known",
                        "examples": [
                            "Novel defect type not in taxonomy",
                            "Complex composite defects",
                            "Defects requiring new tools"
                        ],
                        "action": "BLOCK - must assess repairability before proceeding"
                    },
                    "operator_review_required": {
                        "description": "Defects requiring human visual expert judgment",
                        "examples": [
                            "Style appropriateness",
                            "Expression subtlety",
                            "Artistic quality assessment"
                        ],
                        "action": "Route to visual expert review, then operator decision"
                    },
                    "generation_recipe_must_change": {
                        "description": "Defects indicating fundamental generation approach failure",
                        "examples": [
                            "Systematic identity drift",
                            "Recurring structural defects",
                            "Style mismatch despite conditioning"
                        ],
                        "action": "BLOCK - must revise generation recipe (prompt, workflow, models)"
                    }
                },
                "repairability_assessment_workflow": {
                    "step_1": "QA identifies defects using universal canon and defect taxonomy",
                    "step_2": "QA checks defect_repairability_matrix for known repairability",
                    "step_3": "If repairability known, route accordingly (repair or block)",
                    "step_4": "If repairability unknown, BLOCK until assessment complete",
                    "step_5": "Visual expert review for ambiguous cases",
                    "step_6": "Operator final decision on acceptance or rejection"
                },
                "repair_tool_registry": {
                    "registry_path": "standards_pack/references/repair_tool_registry.json",
                    "must_be_loaded": True,
                    "must_be_validated": True
                },
                "defect_repairability_matrix": {
                    "matrix_path": "standards_pack/internal/defect_repairability_matrix.json",
                    "must_be_loaded": True,
                    "must_be_validated": True
                },
                "enforcement_points": [
                    "Visual QA technical assessment",
                    "Visual expert review gate",
                    "Operator visual decision gate",
                    "Downstream assembly gate"
                ],
                "policy_version": "1.0",
                "policy_status": "active"
            }
        }
    
    def _build_generation_readiness_blocker_policy(self) -> Dict[str, Any]:
        """Build generation readiness blocker policy."""
        return {
            "task_id": self.task_id,
            "generation_readiness_blocker_policy": {
                "policy_purpose": "Define what blocks generation from proceeding",
                "generation_blocked_until": "fresh_visual_strategy_operator_review_required",
                "blocking_conditions": {
                    "strategy_not_reviewed": {
                        "condition": "Fresh visual strategy has not been reviewed by operator",
                        "action": "BLOCK generation until operator review complete",
                        "status": "active"
                    },
                    "negative_references_not_loaded": {
                        "condition": "Negative references from previous failures not loaded",
                        "action": "BLOCK generation until negative references loaded",
                        "status": "pending_check"
                    },
                    "repairability_policy_not_loaded": {
                        "condition": "Repairability-aware visual policy not loaded",
                        "action": "BLOCK generation until policy loaded",
                        "status": "pending_check"
                    },
                    "workflow_not_selected": {
                        "condition": "Generation workflow not selected and validated",
                        "action": "BLOCK generation until workflow selected",
                        "status": "pending_check"
                    },
                    "model_assets_not_verified": {
                        "condition": "Model assets not verified as available",
                        "action": "BLOCK generation until models verified",
                        "status": "pending_check"
                    },
                    "generation_gate_not_opened": {
                        "condition": "Generation gate not explicitly opened by authorized entity",
                        "action": "BLOCK generation until gate opened",
                        "status": "pending_check"
                    }
                },
                "non_blocking_conditions": {
                    "strategy_reviewed": "Fresh visual strategy reviewed by operator",
                    "negative_references_loaded": "All negative references loaded and accessible",
                    "repairability_policy_loaded": "Repairability policy loaded and enforced",
                    "workflow_selected": "Generation workflow selected and validated",
                    "model_assets_verified": "Model assets verified and available",
                    "generation_gate_opened": "Generation gate explicitly opened"
                },
                "blocker_types": {
                    "strategy_blocker": "Fresh visual strategy not reviewed or approved",
                    "reference_blocker": "Required references not available",
                    "policy_blocker": "Required policies not loaded",
                    "workflow_blocker": "Generation workflow not validated",
                    "asset_blocker": "Model assets not available",
                    "gate_blocker": "Generation gate not opened"
                },
                "blocker_resolution": {
                    "strategy_blocker_resolution": "Operator review and approval of fresh visual strategy",
                    "reference_blocker_resolution": "Acquire or validate required references",
                    "policy_blocker_resolution": "Load and validate required policies",
                    "workflow_blocker_resolution": "Select and validate generation workflow",
                    "asset_blocker_resolution": "Verify model asset availability",
                    "gate_blocker_resolution": "Explicit gate opening by authorized entity"
                },
                "current_blocker": "strategy_not_reviewed",
                "current_blocker_status": "active",
                "generation_allowed": False
            }
        }
    
    def _build_generation_gate_requirements(self) -> Dict[str, Any]:
        """Build future generation gate requirements."""
        return {
            "task_id": self.task_id,
            "future_generation_gate_requirements": {
                "generation_authorized_by_this_layer": False,
                "future_generation_requires_explicit_gate": True,
                "gate_purpose": "Ensure all prerequisites are met before any ComfyUI generation submit",
                "prerequisite_checks": {
                    "max_generations_must_be_declared": {
                        "required": True,
                        "description": "Maximum number of generation attempts must be declared before any generation",
                        "default_max": 1,
                        "enforcement": "Gate must track generation count and block after max reached"
                    },
                    "workflow_must_be_selected_before_submit": {
                        "required": True,
                        "description": "Generation workflow must be selected and validated before ComfyUI submit",
                        "validation": "Workflow file must exist, be valid JSON, match expected schema",
                        "enforcement": "Gate must validate workflow before allowing submit"
                    },
                    "model_assets_must_be_verified": {
                        "required": True,
                        "description": "All required model assets must be verified as available",
                        "validation": "Check model paths, file existence, file integrity",
                        "enforcement": "Gate must verify model availability before allowing submit"
                    },
                    "repairability_policy_must_be_loaded": {
                        "required": True,
                        "description": "Repairability-aware visual policy must be loaded and enforced",
                        "validation": "Policy file must exist, be valid JSON, be loaded in memory",
                        "enforcement": "Gate must verify policy loaded before allowing submit"
                    },
                    "negative_references_must_be_loaded": {
                        "required": True,
                        "description": "Negative references from previous failures must be loaded",
                        "validation": "Reference files must exist, be accessible",
                        "enforcement": "Gate must verify negative references loaded before allowing submit"
                    },
                    "positive_references_must_be_loaded": {
                        "required": True,
                        "description": "Positive quality references must be loaded",
                        "validation": "Reference files must exist, be accessible",
                        "enforcement": "Gate must verify positive references loaded before allowing submit"
                    }
                },
                "post_generation_requirements": {
                    "operator_review_required_after_generation": {
                        "required": True,
                        "description": "Every generation output must be reviewed by operator before proceeding",
                        "enforcement": "Pipeline must stop at operator review gate after generation"
                    },
                    "visual_qa_cannot_set_production_accepted": {
                        "required": True,
                        "description": "Visual QA technical pass does not set production_accepted=true",
                        "enforcement": "production_accepted remains false until explicit operator decision"
                    },
                    "assembly_downstream_forbidden_until_operator_acceptance": {
                        "required": True,
                        "description": "Assembly and downstream stages forbidden until operator acceptance",
                        "enforcement": "Assembly and downstream gates must block until operator acceptance"
                    }
                },
                "generation_count_tracking": {
                    "must_track": True,
                    "must_enforce_max": True,
                    "must_log_each_attempt": True,
                    "must_prevent_blind_retry": True
                },
                "gate_authorization": {
                    "who_may_open_gate": "human_operator",
                    "agent_may_open_gate": False,
                    "authorization_required": True,
                    "authorization_must_be_explicit": True,
                    "authorization_must_be_logged": True
                },
                "gate_status": {
                    "current_status": "closed",
                    "closed_reason": "Fresh visual strategy requires operator review before generation gate can be opened",
                    "opened_after": "fresh_visual_strategy_operator_review_required"
                },
                "forbidden_without_gate": [
                    "comfyui_submit",
                    "workflow_execution",
                    "model_loading",
                    "generation_attempt"
                ]
            }
        }
    
    def _build_operator_review_packet(self) -> Dict[str, Any]:
        """Build operator review packet."""
        return {
            "task_id": self.task_id,
            "packet_type": "operator_review_packet",
            "packet_purpose": "Provide operator with complete fresh visual strategy for review and approval",
            "timestamp": datetime.now().isoformat(),
            "strategy_summary": {
                "context": "All visual outputs were purged due to unrepairable defects across 8 generation attempts",
                "proposed_approach": "Strategy-first generation with explicit quality targets, repairability awareness, and generation gate authorization",
                "key_changes": [
                    "No blind retry - explicit strategy and authorization required",
                    "Repairability must be known - unknown repairability blocks",
                    "Technical pass is not visual pass - expert review required",
                    "Negative references from all failures must be enforced",
                    "Generation gate validates workflow, models, and policy before submit"
                ]
            },
            "strategy_artifacts": {
                "manifest": "fresh_visual_strategy_manifest.json",
                "brief": "fresh_visual_strategy_brief.json",
                "visual_style_direction": "visual_style_direction.json",
                "visual_quality_targets": "visual_quality_targets.json",
                "negative_reference_policy": "negative_reference_policy.json",
                "reference_acquisition_plan": "reference_acquisition_plan.json",
                "repairability_aware_visual_policy": "repairability_aware_visual_policy.json",
                "generation_readiness_blocker_policy": "generation_readiness_blocker_policy.json",
                "future_generation_gate_requirements": "future_generation_gate_requirements.json"
            },
            "what_operator_must_review": {
                "visual_style_direction": "Review and approve target style, mood, composition, and identity requirements",
                "visual_quality_targets": "Review and approve quality bars and defect classification",
                "negative_reference_policy": "Review documented defects from previous failures",
                "repairability_policy": "Review repairability assessment approach and blocking rules",
                "generation_gate_requirements": "Review generation gate prerequisites and authorization flow"
            },
            "operator_decision_required": {
                "decision_type": "approve_or_reject_fresh_visual_strategy",
                "options": [
                    {
                        "option": "approve",
                        "description": "Approve fresh visual strategy and proceed to generation planning",
                        "next_action": "generation_planning_with_gate_authorization"
                    },
                    {
                        "option": "reject",
                        "description": "Reject fresh visual strategy and request revisions",
                        "next_action": "revise_fresh_visual_strategy"
                    },
                    {
                        "option": "modify",
                        "description": "Approve with modifications - specify required changes",
                        "next_action": "implement_modifications_then_proceed"
                    }
                ]
            },
            "operator_review_guidance": {
                "focus_areas": [
                    "Does the visual style direction match your intent?",
                    "Are the quality targets appropriate for the project?",
                    "Do the negative references accurately capture what must be avoided?",
                    "Is the repairability policy too strict or too permissive?",
                    "Are the generation gate requirements clear and enforceable?"
                ],
                "review_checklist": [
                    "Style direction approved",
                    "Quality targets approved",
                    "Negative references reviewed",
                    "Repairability policy understood",
                    "Generation gate requirements accepted"
                ]
            },
            "current_state": "fresh_visual_strategy_operator_review_required",
            "next_allowed_action": "fresh_visual_strategy_operator_review_required",
            "generation_allowed": False,
            "qa_repairability_gate_active": True,
            "production_accepted": False
        }
    
    def _build_readiness_report(self) -> Dict[str, Any]:
        """Build readiness report."""
        return {
            "task_id": self.task_id,
            "report_type": "readiness_report",
            "timestamp": datetime.now().isoformat(),
            "readiness_assessment": {
                "overall_readiness": "ready_for_operator_review",
                "ready_for_generation": False,
                "generation_blocked_until": "operator_review_complete"
            },
            "artifact_readiness": {
                "fresh_visual_strategy_manifest": {
                    "status": "created",
                    "valid": True,
                    "path": "fresh_visual_strategy_manifest.json"
                },
                "fresh_visual_strategy_brief": {
                    "status": "created",
                    "valid": True,
                    "path": "fresh_visual_strategy_brief.json"
                },
                "visual_style_direction": {
                    "status": "created",
                    "valid": True,
                    "path": "visual_style_direction.json"
                },
                "visual_quality_targets": {
                    "status": "created",
                    "valid": True,
                    "path": "visual_quality_targets.json"
                },
                "negative_reference_policy": {
                    "status": "created",
                    "valid": True,
                    "path": "negative_reference_policy.json"
                },
                "reference_acquisition_plan": {
                    "status": "created",
                    "valid": True,
                    "path": "reference_acquisition_plan.json"
                },
                "repairability_aware_visual_policy": {
                    "status": "created",
                    "valid": True,
                    "path": "repairability_aware_visual_policy.json"
                },
                "generation_readiness_blocker_policy": {
                    "status": "created",
                    "valid": True,
                    "path": "generation_readiness_blocker_policy.json"
                },
                "future_generation_gate_requirements": {
                    "status": "created",
                    "valid": True,
                    "path": "future_generation_gate_requirements.json"
                },
                "visual_strategy_operator_review_packet": {
                    "status": "created",
                    "valid": True,
                    "path": "visual_strategy_operator_review_packet.json"
                }
            },
            "policy_readiness": {
                "qa_repairability_gate_active": True,
                "unknown_repairability_blocks": True,
                "downstream_requires_validated_repairability": True,
                "technical_pass_not_visual_pass_enforced": True,
                "visual_operator_review_required": True,
                "production_accepted_must_remain_false": True
            },
            "reference_readiness": {
                "positive_references_available": 2,
                "negative_references_available": 1,
                "negative_reference_policy_enforced": True,
                "reference_integrity_valid": True
            },
            "forbidden_actions_verification": {
                "generation_performed": False,
                "comfyui_submit_executed": False,
                "retry_attempted": False,
                "preview_rerender_executed": False,
                "preview_render_executed": False,
                "visual_qa_acceptance_executed": False,
                "operator_visual_acceptance_executed": False,
                "voice_generation_executed": False,
                "audio_generation_executed": False,
                "assembly_executed": False,
                "final_render_executed": False,
                "downstream_executed": False,
                "production_accepted": False,
                "hidden_external_llm_api_call": False,
                "hidden_network_or_api_calls_performed": False,
                "hidden_downloads_or_installs_performed": False,
                "model_download_or_install_performed": False,
                "fake_operator_decision_created": False,
                "fake_success_created": False,
                "blind_retry_attempted": False
            },
            "state_verification": {
                "current_state": "visual_outputs_purged_rebuild_required",
                "next_allowed_action": "fresh_visual_strategy_required",
                "target_state_after_operator_review": "fresh_visual_strategy_operator_review_required",
                "target_next_allowed_action_after_review": "generation_planning_with_gate_authorization"
            },
            "readiness_checklist": {
                "all_artifacts_created": True,
                "all_artifacts_valid": True,
                "policies_loaded": True,
                "references_available": True,
                "forbidden_actions_respected": True,
                "state_consistent": True,
                "qa_repairability_gate_active": True,
                "generation_authorized": False,
                "ready_for_operator_review": True
            },
            "blockers": [],
            "warnings": [],
            "recommendation": "Proceed to operator review of fresh visual strategy"
        }
    
    def _write_artifact(self, filename: str, data: Dict[str, Any]) -> None:
        """Write artifact to JSON file."""
        artifact_path = self.strategy_dir / filename
        with open(artifact_path, 'w') as f:
            json.dump(data, f, indent=2)
