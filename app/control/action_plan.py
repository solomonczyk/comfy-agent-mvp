"""MK-CTRL5 — Deterministic action plan builder.

Builds execution plans for shot actions without running any production systems.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import ActionDefinition, ActionPlan, ShotStateReport
from .visual_qa import load_visual_qa_report
from .reference_lock_gate import ReferenceLockGate
# MK-REF1R-2 — Import ReferenceResolver for existing reference injection
from app.reference.reference_resolver import ReferenceResolver


def _check_prompt_placeholders(prompt_pack: dict) -> dict:
    """MK-PROMPTLOCK1 — Check for placeholder/generic prompts in prompt_pack.
    
    Returns dict with:
    - valid: bool - whether prompts pass the placeholder check
    - reason: str - reason for failure if invalid
    """
    # Check for positive prompt
    positive_prompt = prompt_pack.get("positive_prompt", "")
    if not positive_prompt or not positive_prompt.strip():
        return {"valid": False, "reason": "prompt_pack contains empty positive_prompt"}
    
    # Check for placeholder positive prompts
    placeholder_positive_patterns = [
        "beautiful anime girl",
        "high quality",
        "detailed",
        "masterpiece",
        "best quality"
    ]
    
    positive_lower = positive_prompt.lower().strip()
    for pattern in placeholder_positive_patterns:
        if pattern in positive_lower and len(positive_lower) < 50:
            return {"valid": False, "reason": f"prompt_pack contains placeholder positive prompt: '{pattern}'"}
    
    # Check for negative prompt
    negative_prompt = prompt_pack.get("negative_prompt", "")
    if not negative_prompt or not negative_prompt.strip():
        return {"valid": False, "reason": "prompt_pack contains empty negative_prompt"}
    
    # Check for placeholder negative prompts (e.g., only "blurry")
    negative_lower = negative_prompt.lower().strip()
    if negative_lower == "blurry" or negative_lower in ["blur", "low quality", "worst quality"]:
        return {"valid": False, "reason": "prompt_pack contains placeholder negative prompt"}
    
    # Check for reference_locked mode requirements
    if prompt_pack.get("generation_mode") == "reference_locked":
        reference_image_path = prompt_pack.get("reference_image_path")
        if not reference_image_path or not reference_image_path.strip():
            return {"valid": False, "reason": "reference_locked mode requires reference_image_path"}
    
    # Check for character description
    if "characters" not in prompt_pack and "beats" not in prompt_pack:
        return {"valid": False, "reason": "prompt_pack missing character description"}
    
    return {"valid": True, "reason": ""}


def _inject_reference_locked_fields_from_project_profile(
    prompt_pack: dict,
    control_dir,
    has_reference_locked_character: bool,
) -> dict:
    """RC-CORE1 — Inject character reference from project_profile into prompt_pack.

    This is a generic function that uses project_profile to resolve character
    references, not hardcoded Alya-specific logic.

    Side-effect free except mutating the local prompt_pack dict.
    """
    if not has_reference_locked_character:
        return prompt_pack

    if prompt_pack.get("reference_image_path"):
        prompt_pack.setdefault("generation_mode", "reference_locked")
        prompt_pack.setdefault("reference_role", "character_identity")
        return prompt_pack

    project_profile_path = control_dir / "project_profile.json"

    if not project_profile_path.exists():
        return prompt_pack

    try:
        project_profile = json.loads(project_profile_path.read_text(encoding="utf-8"))
    except Exception:
        return prompt_pack

    # Get first character from prompt_pack characters list
    characters_list = prompt_pack.get("characters", [])
    if not characters_list:
        return prompt_pack

    character_name = characters_list[0] if isinstance(characters_list, list) else characters_list

    # Resolve character from project profile
    characters_dict = project_profile.get("characters", {})
    character_data = None

    # Try to find character by name or alias
    for char_id, char_data in characters_dict.items():
        if char_data.get("character_id") == character_name:
            character_data = char_data
            break
        if character_name in char_data.get("aliases", []):
            character_data = char_data
            break
        if char_data.get("name") == character_name:
            character_data = char_data
            break

    if not character_data:
        return prompt_pack

    reference_image_path = character_data.get("reference_image_path")
    if not reference_image_path:
        return prompt_pack

    # Validate reference exists
    reference_path = Path(reference_image_path)
    if not reference_path.exists():
        return prompt_pack

    prompt_pack["generation_mode"] = "reference_locked"
    prompt_pack["reference_image_path"] = str(reference_path)
    prompt_pack["reference_role"] = character_data.get("reference_role", "character_identity")

    return prompt_pack


class ActionPlanBuilder:
    """Build deterministic execution plans from shot state reports.

    This planner only builds plans; it does NOT execute ComfyUI, ffmpeg, or TTS.
    """

    _DEFINITIONS: dict[str, ActionDefinition] = {
        "create_brief": ActionDefinition(
            action="create_brief",
            handler_key="create_brief",
            required_inputs=["episode_id", "shot_id"],
            expected_outputs=["data/briefs/{episode_id}_{shot_id}_brief.md"],
        ),
        "generate_frames": ActionDefinition(
            action="generate_frames",
            handler_key="generate_frames",
            required_inputs=["brief_path"],
            expected_outputs=["output/{shot_id}/*.png"],
            command_template="python -m app run --brief {brief_path} --output output --scene {shot_id}",
        ),
        "continue_generation": ActionDefinition(
            action="continue_generation",
            handler_key="generate_frames",
            required_inputs=["brief_path"],
            expected_outputs=["output/{shot_id}/*.png"],
            command_template="python -m app run --brief {brief_path} --output output --scene {shot_id}",
        ),
        "assemble_scene": ActionDefinition(
            action="assemble_scene",
            handler_key="assemble_scene",
            required_inputs=["frame_manifest_path"],
            expected_outputs=["output/scenes/{episode_id}_{shot_id}.mp4"],
            command_template="python -m app assemble-scene --frame-manifest {frame_manifest_path} --output output",
        ),
        "qa_review": ActionDefinition(
            action="qa_review",
            handler_key="qa_review",
            required_inputs=["scene_mp4_path"],
            expected_outputs=["output/control/qa_report.json"],
            command_template="python -m app qa-review --scene {scene_mp4_path} --output output",
        ),
        "attach_audio": ActionDefinition(
            action="attach_audio",
            handler_key="attach_audio",
            required_inputs=["scene_mp4_path", "brief_path"],
            expected_outputs=["output/scenes/{episode_id}_{shot_id}_audio.mp4", "output/control/audio_manifest.json"],
            command_template="python -m app attach-audio --scene {scene_mp4_path} --brief {brief_path} --output output",
        ),
        "render_episode": ActionDefinition(
            action="render_episode",
            handler_key="render_episode",
            required_inputs=["scene_mp4_path"],
            expected_outputs=["output/episodes/{episode_id}_{shot_id}_episode.mp4", "output/control/episode_manifest.json"],
            command_template="python -m app render-episode --scene {scene_mp4_path} --output output",
        ),
        "assemble_scene_video": ActionDefinition(
            action="assemble_scene_video",
            handler_key="assemble_scene_video",
            required_inputs=["generated_frames"],
            expected_outputs=["output/scenes/{shot_id}.mp4"],
        ),
        "synthesize_and_mux_audio": ActionDefinition(
            action="synthesize_and_mux_audio",
            handler_key="synthesize_and_mux_audio",
            required_inputs=["scene_mp4", "dialogue present", "voice available"],
            expected_outputs=[
                "output/audio/{shot_id}.wav",
                "output/scenes/{shot_id}_with_audio.mp4",
            ],
        ),
        "assemble_episode": ActionDefinition(
            action="assemble_episode",
            handler_key="assemble_episode",
            required_inputs=["scene result mp4"],
            expected_outputs=["output/episodes/{episode_id}_final.mp4"],
        ),
        "run_qa": ActionDefinition(
            action="run_qa",
            handler_key="run_qa",
            required_inputs=["final_episode_mp4"],
            expected_outputs=[
                "output/{episode_id}_{shot_id}/qa.json",
                "output/control/{episode_id}_{shot_id}_ledger.json",
            ],
        ),
        "none": ActionDefinition(
            action="none",
            handler_key="none",
            required_inputs=[],
            expected_outputs=[],
        ),
    }

    def build(self, report: ShotStateReport, requested_action: str, project_root: Path | str | None = None) -> ActionPlan:
        """Return a deterministic plan for *requested_action* based on *report*."""
        definition = self._DEFINITIONS.get(requested_action)
        expected = report.next_action
        current = report.current_state
        is_blocked = current == "blocked"
        is_done = report.is_done
        artifacts = report.existing_artifacts

        # Determine allowed / reason
        if is_blocked:
            allowed = False
            reason = f"blocked: {report.blocked_reason or 'no reason'}"
        elif requested_action != expected and requested_action != "none":
            allowed = False
            reason = f"expected next action is '{expected}', got '{requested_action}'"
        elif is_done and requested_action != "none":
            allowed = False
            reason = "shot is already done"
        elif requested_action == "none":
            allowed = is_done or is_blocked
            reason = (
                "none is valid for done/blocked state"
                if allowed
                else "'none' is not a valid execution action for this state"
            )
        elif definition is None:
            allowed = False
            reason = "unknown action"
        else:
            allowed = True
            reason = "action matches next expected step"

        # MK-CTRL25 — Visual QA gate for assemble_scene
        # RC-QC1 — Support both legacy (overall_verdict) and new (final_verdict.decision) formats
        if allowed and requested_action == "assemble_scene" and current == "frames_generated":
            # MK-RECIPE7 — Use project_root parameter
            if project_root is not None:
                qa_report = load_visual_qa_report(project_root, report.episode_id, report.shot_id)
                if qa_report is None:
                    allowed = False
                    reason = "visual QA report missing"
                else:
                    # Check both legacy and new format
                    overall_verdict = qa_report.get("overall_verdict")
                    final_verdict = qa_report.get("final_verdict", {}).get("decision")
                    
                    # Legacy format: overall_verdict must be "pass"
                    # New format: final_verdict.decision must be "accept"
                    verdict_passed = (overall_verdict == "pass") or (final_verdict == "accept")
                    
                    if not verdict_passed:
                        allowed = False
                        reason = f"visual QA not passed: overall_verdict={overall_verdict}, final_verdict={final_verdict}"

        # MK-GEN2 — Reference lock gate for generate_frames
        # MK-GEN2R — Prompt-pack mode detection and input contract repair
        prompt_pack_path: str | None = None
        generation_mode: str | None = None  # "brief" or "prompt_pack"
        required_inputs_override: list[str] | None = None  # MK-GEN2R — Override required_inputs for specific modes
        
        if allowed and requested_action == "generate_frames":
            # MK-RECIPE7 — Use project_root parameter instead of getting from report
            if project_root:
                # Try to load prompt_pack.json
                # Check for prompt_pack in control directory
                control_dir = Path(project_root) / "output" / "control"
                if control_dir.exists():
                    prompt_pack_path = control_dir / "prompt_pack.json"
                
                if prompt_pack_path and prompt_pack_path.exists():
                    try:
                        with open(prompt_pack_path, 'r', encoding='utf-8') as f:
                            prompt_pack = json.load(f)
                        print(f"[ACTION_PLAN] Loaded prompt_pack from {prompt_pack_path}")
                        
                        # MK-PROMPTLOCK1 — Prompt placeholder gate
                        placeholder_check = _check_prompt_placeholders(prompt_pack)
                        if not placeholder_check["valid"]:
                            allowed = False
                            reason = placeholder_check["reason"]
                        else:
                            # Check if characters field exists
                            if "characters" not in prompt_pack and "beats" not in prompt_pack:
                                allowed = False
                                reason = "prompt_pack missing characters"
                            elif "characters" not in prompt_pack and not prompt_pack.get("beats"):
                                # beats exists but is empty
                                allowed = False
                                reason = "prompt_pack missing characters"
                            else:
                                # RC-CORE1 — Inject existing reference if prompt_pack has characters but no reference_image_path
                                # Check if prompt_pack contains any character and no reference_image_path
                                has_reference_locked_character = False
                                characters_list = prompt_pack.get("characters", [])
                                if isinstance(characters_list, list) and characters_list:
                                    has_reference_locked_character = True
                                
                                # Also check beats for character references
                                if not has_reference_locked_character and "beats" in prompt_pack:
                                    beats = prompt_pack.get("beats", [])
                                    if isinstance(beats, list):
                                        for beat in beats:
                                            if isinstance(beat, dict):
                                                beat_chars = beat.get("characters", [])
                                                if isinstance(beat_chars, list) and beat_chars:
                                                    has_reference_locked_character = True
                                                    break
                                            if has_reference_locked_character:
                                                break

                                # MK-REF1 — Check for reference_locked generation mode
                                if prompt_pack.get("generation_mode") == "reference_locked":
                                    generation_mode = "reference_locked"
                                    required_inputs_override = ["prompt_pack_path", "reference_image_path"]
                                    
                                    # Validate reference_image_path
                                    reference_image_path = prompt_pack.get("reference_image_path")
                                    if not reference_image_path:
                                        allowed = False
                                        reason = "reference image missing for reference_locked mode"
                                    else:
                                        # Resolve reference image path relative to project root
                                        ref_path = Path(reference_image_path)
                                        if not ref_path.is_absolute():
                                            ref_path = Path(project_root) / ref_path
                                        
                                        if not ref_path.exists():
                                            allowed = False
                                            reason = f"reference image not found: {reference_image_path}"
                                        else:
                                            # Validate file extension
                                            valid_extensions = {".png", ".jpg", ".jpeg", ".webp"}
                                            if ref_path.suffix.lower() not in valid_extensions:
                                                allowed = False
                                                reason = f"invalid reference image extension: {ref_path.suffix}"
                                            else:
                                                # Reference image is valid
                                                # Call reference lock gate for character validation
                                                gate = ReferenceLockGate()
                                                gate_decision = gate.can_generate_prompt_pack(Path(project_root), prompt_pack)
                                                
                                                if not gate_decision.allowed:
                                                    allowed = False
                                                    reason = f"reference lock gate: {gate_decision.reason}"
                                else:
                                    # RC-CORE1 / MK-REF1R-2 / MK-GEN2R — inject reference then set mode
                                    prompt_pack = _inject_reference_locked_fields_from_project_profile(
                                        prompt_pack=prompt_pack,
                                        control_dir=control_dir,
                                        has_reference_locked_character=has_reference_locked_character,
                                    )
                                    if not prompt_pack.get("generation_mode"):
                                        prompt_pack["generation_mode"] = "prompt_pack"
                                    if prompt_pack.get("generation_mode") == "reference_locked":
                                        required_inputs_override = ["prompt_pack_path", "reference_image_path"]
                                    else:
                                        required_inputs_override = ["prompt_pack_path"]
                                    generation_mode = prompt_pack["generation_mode"]
                    except Exception as exc:
                        # If prompt_pack cannot be loaded, deny
                        print(f"[ACTION_PLAN] Failed to load prompt_pack: {exc}")
                        allowed = False
                        reason = "prompt_pack invalid or cannot be loaded"
                        prompt_pack_path = None
                        generation_mode = "prompt_pack"
                        required_inputs_override = ["prompt_pack_path"]
                else:
                    # No prompt_pack.json found - deny (prompt-pack mode is required)
                    allowed = False
                    reason = "prompt_pack missing"
                    prompt_pack_path = None
                    generation_mode = "prompt_pack"  # MK-GEN2R-2
                    required_inputs_override = ["prompt_pack_path"]  # MK-GEN2R-2
            else:
                # No project_root - use brief mode if brief exists (legacy fallback)
                if artifacts.brief_path:
                    generation_mode = "brief"
                    required_inputs_override = ["brief_path"]  # MK-GEN2R — Set required_inputs for brief mode
                else:
                    allowed = False
                    reason = "no project_root and no brief available"

        # If not allowed, return minimal denied plan
        if not allowed:
            # MK-GEN2R-2 — Use required_inputs_override if set, otherwise use definition
            denied_required_inputs = required_inputs_override if required_inputs_override is not None else (definition.required_inputs if definition else [])
            
            # MK-GEN2R-2 — Calculate missing_inputs for denied plan
            denied_missing_inputs: list[str] = []
            if "prompt_pack_path" in denied_required_inputs:
                if not prompt_pack_path or not Path(prompt_pack_path).exists():
                    denied_missing_inputs.append("prompt_pack_path")
            if "brief_path" in denied_required_inputs and not artifacts.brief_path:
                denied_missing_inputs.append("brief_path")
            
            return ActionPlan(
                episode_id=report.episode_id,
                shot_id=report.shot_id,
                action=requested_action,
                allowed=False,
                current_state=current,
                expected_next_action=expected,
                brief_path=report.existing_artifacts.brief_path,
                required_inputs=denied_required_inputs,  # MK-GEN2R-2 — Report required inputs
                missing_inputs=denied_missing_inputs,  # MK-GEN2R-2 — Report missing inputs
                reason=reason,
                executable=False,
                prompt_pack_path=str(prompt_pack_path) if prompt_pack_path else None,  # MK-GEN2R-2
                generation_mode=generation_mode,  # MK-GEN2R-2
            )

        # Build inputs / outputs from definition
        required_inputs = list(definition.required_inputs) if definition else []
        expected_outputs = list(definition.expected_outputs) if definition else []
        handler_key = definition.handler_key if definition else None

        # MK-GEN2R — Use required_inputs_override if set by generation mode logic
        if required_inputs_override is not None:
            required_inputs = required_inputs_override

        # Resolve missing inputs
        missing_inputs: list[str] = []

        # MK-GEN2R — Check missing inputs based on generation mode
        if "prompt_pack_path" in required_inputs:
            if not prompt_pack_path or not Path(prompt_pack_path).exists():
                missing_inputs.append("prompt_pack_path")
        if "brief_path" in required_inputs and not artifacts.brief_path:
            missing_inputs.append("brief_path")
        if "generated_frames" in required_inputs and not artifacts.generated_frames:
            missing_inputs.append("generated_frames")
        if "scene_mp4" in required_inputs and not artifacts.scene_mp4_path:
            missing_inputs.append("scene_mp4")
        if "dialogue present" in required_inputs and not report.audio_required:
            missing_inputs.append("dialogue present")
        if "voice available" in required_inputs:
            # No explicit artifact for voice; assume available if audio_required is True
            if not report.audio_required:
                missing_inputs.append("voice available")
        if "scene result mp4" in required_inputs:
            if not artifacts.scene_mp4_path and not artifacts.scene_mp4_with_audio_path:
                missing_inputs.append("scene result mp4")
        if "final_episode_mp4" in required_inputs and not artifacts.final_episode_mp4_path:
            missing_inputs.append("final_episode_mp4")
        
        # MK-CTRL21 — Check frame_manifest_path for assemble_scene
        frame_manifest_path: str | None = None
        scene_mp4_path: str | None = None  # MK-CTRL22
        
        if requested_action == "assemble_scene":
            # MK-CTRL37R — Use typed frame_manifest_path from state first
            if report.frame_manifest_path:
                frame_manifest_path = report.frame_manifest_path
            # Fallback to legacy artifact_path
            elif report.artifact_path:
                frame_manifest_path = report.artifact_path
            # Otherwise check if frame manifest exists in artifacts
            elif hasattr(artifacts, 'frame_manifest_path') and artifacts.frame_manifest_path:
                frame_manifest_path = artifacts.frame_manifest_path
            
            if not frame_manifest_path:
                missing_inputs.append("frame_manifest_path")
        
        # MK-CTRL22 — Check scene_mp4_path for qa_review
        if requested_action == "qa_review":
            # MK-CTRL37R — Use typed scene_mp4_path from state first
            if report.scene_mp4_path:
                scene_mp4_path = report.scene_mp4_path
            # Fallback to legacy artifact_path
            elif report.artifact_path:
                scene_mp4_path = report.artifact_path
            # Otherwise check if scene MP4 exists in artifacts
            elif artifacts.scene_mp4_path:
                scene_mp4_path = artifacts.scene_mp4_path
            
            if not scene_mp4_path:
                missing_inputs.append("scene_mp4_path")
        
        # MK-CTRL23 — Check scene_mp4_path and brief_path for attach_audio
        brief_path: str | None = None
        if requested_action == "attach_audio":
            # MK-CTRL37R — Use typed scene_mp4_path from state (NOT qa_report_path)
            # This is the critical fix: attach_audio needs scene MP4, not QA report
            if report.scene_mp4_path:
                scene_mp4_path = report.scene_mp4_path
            # Fallback to artifacts.scene_mp4_path (actual scene MP4)
            elif artifacts.scene_mp4_path:
                scene_mp4_path = artifacts.scene_mp4_path
            # Last resort: legacy artifact_path (but this is likely wrong)
            elif report.artifact_path:
                scene_mp4_path = report.artifact_path
            
            # Use brief_path from state or artifacts
            if report.brief_path:
                brief_path = report.brief_path
            elif hasattr(artifacts, 'brief_path') and artifacts.brief_path:
                brief_path = artifacts.brief_path
            
            if not scene_mp4_path:
                missing_inputs.append("scene_mp4_path")
            if not brief_path:
                missing_inputs.append("brief_path")
        
        # MK-CTRL24 — Check scene_mp4_path for render_episode
        if requested_action == "render_episode":
            # MK-CTRL37R — Use typed audio_output_path from state first (audio MP4)
            # This is the critical fix: render_episode needs audio MP4, not audio manifest
            if report.audio_output_path:
                scene_mp4_path = report.audio_output_path
            # Fallback to typed scene_mp4_path (pass-through if no audio)
            elif report.scene_mp4_path:
                scene_mp4_path = report.scene_mp4_path
            # Fallback to artifacts.scene_mp4_with_audio_path
            elif artifacts.scene_mp4_with_audio_path:
                scene_mp4_path = artifacts.scene_mp4_with_audio_path
            # Fallback to artifacts.scene_mp4_path
            elif artifacts.scene_mp4_path:
                scene_mp4_path = artifacts.scene_mp4_path
            # Last resort: legacy artifact_path (but this is likely wrong)
            elif report.artifact_path:
                scene_mp4_path = report.artifact_path
            
            if not scene_mp4_path:
                missing_inputs.append("scene_mp4_path")

        # Build command preview where applicable
        command_preview: str | None = None
        if definition and definition.command_template:
            if requested_action == "assemble_scene":
                # MK-CTRL21 — Use frame_manifest_path in command
                command_preview = definition.command_template.format(
                    frame_manifest_path=frame_manifest_path or "<missing_frame_manifest_path>",
                )
            elif requested_action == "qa_review":
                # MK-CTRL22 — Use scene_mp4_path in command
                command_preview = definition.command_template.format(
                    scene_mp4_path=scene_mp4_path or "<missing_scene_mp4_path>",
                )
            elif requested_action == "attach_audio":
                # MK-CTRL23 — Use scene_mp4_path and brief_path in command
                command_preview = definition.command_template.format(
                    scene_mp4_path=scene_mp4_path or "<missing_scene_mp4_path>",
                    brief_path=brief_path or "<missing_brief_path>",
                )
            elif requested_action == "render_episode":
                # MK-CTRL24 — Use scene_mp4_path in command
                command_preview = definition.command_template.format(
                    scene_mp4_path=scene_mp4_path or "<missing_scene_mp4_path>",
                )
            elif requested_action == "generate_frames":
                # MK-GEN2R — Indicate prompt-pack mode in command preview
                if generation_mode == "prompt_pack":
                    command_preview = f"python -m app run --prompt-pack {prompt_pack_path} --output output --scene {report.shot_id}"
                else:
                    command_preview = definition.command_template.format(
                        episode_id=report.episode_id,
                        shot_id=report.shot_id,
                        brief_path=artifacts.brief_path or "<missing_brief_path>",
                    )
            else:
                command_preview = definition.command_template.format(
                    episode_id=report.episode_id,
                    shot_id=report.shot_id,
                    brief_path=artifacts.brief_path or "<missing_brief_path>",
                )

        # Expand output templates
        expanded_outputs = [
            out.format(episode_id=report.episode_id, shot_id=report.shot_id)
            for out in expected_outputs
        ]

        # executable = true only when allowed and no missing inputs
        executable = allowed and len(missing_inputs) == 0 and requested_action != "none"

        # Refine reason for continuation action
        if allowed and requested_action == "continue_generation":
            reason = "continuation: partial artifact reuse / resume generation"
        elif allowed and requested_action == "generate_frames" and artifacts.generated_frames:
            reason = "current pipeline command renders shot through existing run path"

        # Provide fallback reason when command_preview is None but handler is set
        if allowed and command_preview is None and handler_key and requested_action not in ("create_brief", "none"):
            reason = "stage handler required"

        # MK-RECIPE3 — Recipe validation for generate_frames
        recipe_validation: dict | None = None
        if requested_action == "generate_frames" and allowed:
            # MK-RECIPE7 — Use project_root parameter instead of getting from report
            if project_root is not None:
                try:
                    from app.recipes.settings_resolver import ObservedSettingsResolver
                    from app.recipes.planned_settings_resolver import PlannedSettingsResolver
                    from app.recipes.registry import HardwareProfileRegistry, RecipeRegistry
                    from app.recipes.advisor import GenerationSettingsAdvisor
                    from app.recipes.validator import GenerationRecipeValidator
                    
                    # Try ObservedSettingsResolver first
                    resolver = ObservedSettingsResolver(project_root)
                    observed = resolver.resolve_for_shot(report.episode_id, report.shot_id)
                    settings_source = "observed"
                    
                    # MK-RECIPE5 — Fallback to PlannedSettingsResolver if observed not available
                    if observed is None:
                        planned_resolver = PlannedSettingsResolver(project_root)
                        observed = planned_resolver.resolve_for_shot(report.episode_id, report.shot_id)
                        settings_source = "planned"
                    
                    if observed is not None:
                        # Load recipe and hardware registries
                        recipe_registry = RecipeRegistry()
                        hardware_registry = HardwareProfileRegistry()
                        
                        # Get hardware profile (default to GTX 1060 5GB)
                        hardware_profile_id = "gtx_1060_5gb"
                        try:
                            hardware = hardware_registry.get(hardware_profile_id)
                        except KeyError:
                            hardware = None
                        
                        if hardware is not None:
                            # Use advisor to select recipe
                            advisor = GenerationSettingsAdvisor(recipe_registry, hardware_registry)
                            
                            # Determine task type from project_profile or default
                            task_type = "storyboard_keyframes"
                            project_profile = getattr(report, "project_profile", None) or {}
                            if isinstance(project_profile, dict):
                                task_type = project_profile.get("task_type") or project_profile.get("generation_task") or task_type
                            
                            try:
                                # MK-REF1R-5 — Pass generation_mode to advisor for recipe selection
                                recipe = advisor.recommend_recipe(task_type, project_profile, hardware_profile_id, generation_mode)
                                
                                # Validate settings
                                validator = GenerationRecipeValidator()
                                result = validator.validate(observed, recipe, hardware, task_type)
                                
                                # MK-RECIPE6 — Build human-readable summary
                                from app.recipes.summary import RecipeValidationSummaryBuilder
                                summary_builder = RecipeValidationSummaryBuilder()
                                summary = summary_builder.build(result)
                                
                                recipe_validation = {
                                    "available": True,
                                    "settings_source": settings_source,
                                    "verdict": result.verdict,
                                    "recipe_id": result.recipe_id,
                                    "score": result.score,
                                    "issues": [issue.to_dict() for issue in result.issues],
                                    "recommended_settings": result.recommended_settings,
                                    "summary": summary,
                                }
                                
                                # MK-RECIPE4 — Block generate_frames on fail verdict
                                if result.verdict == "fail":
                                    allowed = False
                                    executable = False
                                    reason = "recipe validation failed"
                                    command_preview = None
                                    handler_key = None
                            except (KeyError, ValueError):
                                # Recipe selection failed
                                recipe_validation = {
                                    "available": False,
                                    "reason": "failed to select recipe",
                                }
                        else:
                            recipe_validation = {
                                "available": False,
                                "reason": "hardware profile not found",
                            }
                    else:
                        recipe_validation = {
                            "available": False,
                            "reason": "observed or planned generation settings not available",
                        }
                except Exception:
                    # Recipe validation failed - don't block generation
                    recipe_validation = {
                        "available": False,
                        "reason": "recipe validation error",
                    }
            else:
                recipe_validation = {
                    "available": False,
                    "reason": "no project_root",
                }

        return ActionPlan(
            episode_id=report.episode_id,
            shot_id=report.shot_id,
            action=requested_action,
            allowed=allowed,
            current_state=report.current_state,
            expected_next_action=report.next_action,
            brief_path=brief_path,  # MK-CTRL23
            required_inputs=required_inputs,  # MK-GEN2R — Use adjusted required_inputs
            missing_inputs=missing_inputs,
            expected_outputs=expanded_outputs,
            command_preview=command_preview,
            handler_key=handler_key,
            reason=reason,
            executable=executable,
            frame_manifest_path=frame_manifest_path,  # MK-CTRL21
            output_dir=getattr(report, "output_dir", None) or "output",  # MK-CTRL21
            scene_mp4_path=scene_mp4_path,  # MK-CTRL22
            prompt_pack_path=str(prompt_pack_path) if prompt_pack_path else None,  # MK-GEN2R
            generation_mode=generation_mode,  # MK-GEN2R
            recipe_validation=recipe_validation,  # MK-RECIPE3
        )
