"""MK-E1 — ComfyUI submitter.

Submits a BuiltScene to ComfyUI via HTTP, polls for completion,
and returns the result with frame paths.
"""
from __future__ import annotations

import copy
import time
from pathlib import Path
from typing import Any

from app.observability import ObservedSettingsSnapshotWriter, WorkflowSettingsExtractor
from app.scenes.models import BuiltScene

from .exceptions import ComfySubmitError, ComfyTimeoutError
from .models import SubmitResult
from .workflow_patcher import WorkflowPatcher


class ComfySubmitter:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        output_dir: Path | str | None = None,
        session: Any = None,
        lowvram: bool = True,
        checkpoint: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.output_dir = Path(output_dir) if output_dir else Path("output/frames")
        self.session = session
        self.lowvram = lowvram
        self.checkpoint = checkpoint
        if self.session is None:
            import requests
            self.session = requests.Session()

    def submit(
        self,
        scene: BuiltScene,
        workflow_template: dict,
        timeout_sec: float = 600.0,
        reference_image_path: Path | None = None,
        reference_weight: float = 0.6,
        episode_id: str | None = None,
        shot_id: str | None = None,
        project_root: Path | str | None = None,
        generation_mode: str | None = None,
        denoise: float | None = None,
    ) -> SubmitResult:
        if workflow_template is None:
            raise ValueError("workflow_template cannot be None")
        if not isinstance(workflow_template, dict):
            raise ValueError(f"workflow_template must be a dict, got {type(workflow_template).__name__}")

        workflow = copy.deepcopy(workflow_template)
        
        # RC-COMBINE-V2-571-620: Use fixed "combine_v2" prefix for output path binding
        # This ensures the output collector can find files in ComfyUI native output
        filename_prefix = "combine_v2"
        
        # Inject filename_prefix into SaveImage nodes
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "SaveImage":
                node["inputs"]["filename_prefix"] = filename_prefix
                print(f"[RC-REAL1B-1] Injected filename_prefix '{filename_prefix}' into SaveImage node {node_id}")
        
        self._inject_workflow(workflow, scene, generation_mode)

        # Patch checkpoint if configured
        if self.checkpoint:
            WorkflowPatcher.patch_checkpoint(workflow, self.checkpoint)

        # Patch resolution based on scene aspect ratio
        WorkflowPatcher.patch_resolution(workflow, scene.aspect_ratio)

        # MK-REF1 — Handle reference_locked mode
        original_ref_path = None
        staged_ref_path = None
        character_name = "character"
        cleanliness_metadata = None  # MK-PROFILE1: Initialize for all generation modes
        
        if generation_mode == "reference_locked":
            if reference_image_path is None:
                raise ValueError("reference_image_path is required for reference_locked mode")
            
            # Use default denoise if not provided
            if denoise is None:
                denoise = 0.5  # MK-REAL3R-2: Changed from 0.42 to 0.5 to be within valid range 0.45-0.75
            
            # MK-REAL3R-6 — Patch LoadImage with reference path and set denoise, with staging
            # MK-REF1R-4 — This also rewires KSampler.latent_image to VAEEncode output
            # MK-PROFILE1 — Returns cleanliness metadata from project profile
            workflow, original_ref_path, staged_ref_path, cleanliness_metadata = WorkflowPatcher.patch_reference_image(
                workflow,
                str(reference_image_path),
                project_root=project_root,
                character_name=character_name,
                denoise=denoise,
            )
            
            # MK-REF1R-4 — Disconnect EmptyLatentImage from KSampler in reference_locked mode
            # EmptyLatentImage may exist in template but should not be used as latent source
            for node_id, node in workflow.items():
                if isinstance(node, dict) and node.get("class_type") == "KSampler":
                    latent_image = node["inputs"].get("latent_image")
                    if latent_image and isinstance(latent_image, list):
                        source_id = latent_image[0]
                        source_node = workflow.get(str(source_id))
                        if source_node and source_node.get("class_type") == "EmptyLatentImage":
                            # This should have been rewired by patch_reference_image
                            # Log a warning if it's still connected
                            print(f"[MK-REF1R-4] WARNING: KSampler {node_id} latent_image still connected to EmptyLatentImage {source_id}")
            
            try:
                print(f"[MK-REF1] Reference-locked mode: reference_image={reference_image_path}, denoise={denoise}")
            except UnicodeEncodeError:
                safe_path = str(reference_image_path).encode("ascii", "replace").decode("ascii")
                print(f"[MK-REF1] Reference-locked mode: reference_image={safe_path}, denoise={denoise}")
        
        # RC-REAL2 — Clean reference gate: validate staged reference before real submit
        # Use preflight_service.validate_clean_reference for entropy/stddev QC
        if generation_mode == "reference_locked" and staged_ref_path:
            from app.runtime.preflight_service import PreflightService
            preflight = PreflightService()
            ref_qc = preflight.validate_clean_reference(staged_ref_path)
            if not ref_qc["valid"]:
                error_msg = f"BLOCKED_BY_INVALID_CLEAN_REFERENCE: {'; '.join(ref_qc['blocks'])}"
                print(f"[RC-REAL2 REFERENCE QC] {error_msg}")
                # Write debug artifact before failing
                if episode_id and shot_id and project_root:
                    try:
                        import json
                        control_dir = Path(project_root) / "output" / "control"
                        control_dir.mkdir(parents=True, exist_ok=True)
                        debug_path = control_dir / f"{episode_id}_{shot_id}_reference_qc_error.json"
                        with open(debug_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                "generation_mode": generation_mode,
                                "original_reference_image_path": str(original_ref_path) if original_ref_path else None,
                                "staged_reference_image_path": str(staged_ref_path),
                                "valid": ref_qc["valid"],
                                "blocks": ref_qc["blocks"],
                                "qc_stats": ref_qc["qc_stats"],
                            }, f, indent=2)
                        print(f"[RC-REAL2 REFERENCE QC] Wrote debug artifact: {debug_path}")
                    except Exception as exc:
                        print(f"[RC-REAL2 REFERENCE QC] Failed to write debug artifact: {exc}")
                raise ComfySubmitError(error_msg)
            print(f"[RC-REAL2 REFERENCE QC] Reference validation passed: entropy={ref_qc['qc_stats']['entropy']:.4f}, stddev={ref_qc['qc_stats']['stddev']:.2f}")

        # MK-REAL3R-6 — Prepare clean reference candidate if needed
        # For now, this is a placeholder. In a real implementation, this would:
        # - Detect multi-panel/contact-sheet references
        # - Crop the best single portrait/person panel
        # - Resize/crop to 480x640
        # - Use the clean reference instead of the original multi-panel sheet
        # This will be implemented in a follow-up task.

        # MK-PROMPTLOCK1 — Prompt injection is handled in _inject_workflow via KSampler-connection fallback.
        # For non-reference_locked mode: patch IPAdapter if provided
        if generation_mode != "reference_locked":
            # IPAdapter: patch with reference if provided, otherwise strip nodes entirely
            if reference_image_path is not None:
                WorkflowPatcher.patch_ipadapter(workflow, reference_image_path, weight=reference_weight)
            else:
                WorkflowPatcher.strip_ipadapter(workflow)

        # Patch KSampler nodes to fix common defects (only existing nodes)
        ksampler_node_ids = [node_id for node_id in workflow.keys()
                             if isinstance(workflow.get(node_id), dict)
                             and workflow[node_id].get("class_type") == "KSampler"]
        workflow = WorkflowPatcher.patch_ksampler_nodes(workflow, ksampler_node_ids)

        # MK-REAL3R — Hard pre-submit graph contract gate for reference_locked mode
        # Validate workflow structure before HTTP submit to prevent invalid txt2img fallback
        if generation_mode == "reference_locked":
            contract_errors = self._validate_reference_locked_graph_contract(workflow, reference_image_path)
            if contract_errors:
                error_msg = f"reference_locked workflow graph invalid before submit: {', '.join(contract_errors)}"
                print(f"[GRAPH CONTRACT] {error_msg}")
                # Write debug artifacts before failing
                if episode_id and shot_id and project_root:
                    try:
                        import json
                        control_dir = Path(project_root) / "output" / "control"
                        control_dir.mkdir(parents=True, exist_ok=True)
                        debug_path = control_dir / f"{episode_id}_{shot_id}_graph_contract_error.json"
                        with open(debug_path, 'w', encoding='utf-8') as f:
                            json.dump({
                                "generation_mode": generation_mode,
                                "reference_image_path": str(reference_image_path) if reference_image_path else None,
                                "contract_errors": contract_errors,
                                "workflow": workflow
                            }, f, indent=2)
                        print(f"[GRAPH CONTRACT] Wrote debug artifact: {debug_path}")
                    except Exception as exc:
                        print(f"[GRAPH CONTRACT] Failed to write debug artifact: {exc}")
                raise ComfySubmitError(error_msg)
            print(f"[GRAPH CONTRACT] reference_locked workflow validation passed")

        # MK-OBS2: Persist final observed settings snapshot before submit
        if episode_id and shot_id and project_root:
            try:
                extractor = WorkflowSettingsExtractor()
                # MK-REF1 — Pass generation_mode and reference_image_path for observability
                # MK-REAL3R-6 — Pass staged_reference_image_path if staging was used
                # MK-PROFILE1 — Pass reference_cleanliness metadata from project profile
                observed_settings = extractor.extract(
                    workflow,
                    generation_mode,
                    str(reference_image_path) if reference_image_path else None,
                    str(staged_ref_path) if staged_ref_path else None,
                    cleanliness_metadata,
                )
                writer = ObservedSettingsSnapshotWriter(project_root)
                snapshot_path = writer.write(episode_id, shot_id, observed_settings)
                print(f"[OBSERVABILITY] Wrote observed settings snapshot: {snapshot_path}")
                
                # MK-REAL2R-2: Pre-submit recipe validation
                # Block HTTP submit if observed settings violate recipe
                try:
                    from app.recipes.validator import GenerationRecipeValidator
                    from app.recipes.planned_settings_resolver import PlannedSettingsResolver
                    from app.recipes.registry import RecipeRegistry, HardwareProfileRegistry
                    from app.recipes.advisor import GenerationSettingsAdvisor
                    
                    # Get planned settings
                    resolver = PlannedSettingsResolver(project_root)
                    planned_settings = resolver.resolve_for_shot(episode_id, shot_id)
                    
                    # Get recipe and hardware
                    recipe_registry = RecipeRegistry()
                    hardware_registry = HardwareProfileRegistry()
                    advisor = GenerationSettingsAdvisor(recipe_registry, hardware_registry)
                    
                    # Determine task type from generation_mode or planned settings
                    task_type = "reference_locked_character" if generation_mode == "reference_locked" else "storyboard_keyframes"
                    hardware_profile_id = "gtx_1060_5gb"  # Default hardware profile
                    
                    # Get recommended recipe
                    recipe = advisor.recommend_recipe(
                        task_type=task_type,
                        project_profile={},
                        hardware_profile_id=hardware_profile_id,
                        generation_mode=generation_mode
                    )
                    hardware = hardware_registry.get(hardware_profile_id)
                    
                    # Validate observed settings against recipe
                    validator = GenerationRecipeValidator()
                    validation_result = validator.validate(
                        observed=observed_settings,
                        recipe=recipe,
                        hardware=hardware,
                        task_type=task_type
                    )
                    
                    if validation_result.verdict == "fail":
                        error_msg = f"Pre-submit recipe validation failed"
                        print(f"[RECIPE VALIDATION] {error_msg}")
                        print(f"[RECIPE VALIDATION] Issues: {[issue.code for issue in validation_result.issues if issue.severity == 'error']}")
                        raise ComfySubmitError(f"Pre-submit recipe validation blocked: {error_msg}")
                    else:
                        print(f"[RECIPE VALIDATION] Pre-submit validation passed: verdict={validation_result.verdict}")
                except ImportError as e:
                    # If recipe validation modules not available, log warning but continue
                    print(f"[RECIPE VALIDATION] Recipe validation modules not available, skipping pre-submit check: {e}")
                except ComfySubmitError:
                    # Re-raise validation errors to block submit
                    raise
                    
            except Exception as exc:
                # Log but don't fail submit if snapshot writing fails
                print(f"[OBSERVABILITY] Failed to write observed settings snapshot: {exc}")

        # MK-REAL2R-2: Persist submitted workflow JSON before ComfyUI submit
        if episode_id and shot_id and project_root:
            try:
                import json
                control_dir = Path(project_root) / "output" / "control"
                control_dir.mkdir(parents=True, exist_ok=True)
                submitted_workflow_path = control_dir / f"{episode_id}_{shot_id}_submitted_workflow.json"
                with open(submitted_workflow_path, 'w', encoding='utf-8') as f:
                    json.dump(workflow, f, indent=2)
                print(f"[OBSERVABILITY] Wrote submitted workflow: {submitted_workflow_path}")
            except Exception as exc:
                # Log but don't fail submit if workflow writing fails
                print(f"[OBSERVABILITY] Failed to write submitted workflow: {exc}")

        # Flush CUDA cache before submit (keeps model loaded, frees ~0.5 GB)
        try:
            self.session.post(
                f"http://{self.host}:{self.port}/free",
                json={"unload_models": False, "free_memory": True},
                timeout=5,
            )
        except Exception:
            pass

        url = f"http://{self.host}:{self.port}/prompt"
        # Retry once if ComfyUI crashed and restarted
        for attempt in range(2):
            try:
                response = self.session.post(url, json={"prompt": workflow}, timeout=30)
                break
            except Exception as exc:
                if attempt == 0:
                    print(f"  ComfyUI unreachable ({exc}), waiting up to 120s for restart...")
                    self._wait_for_comfy(wait_sec=120, poll_interval=5)
                else:
                    raise ComfySubmitError(f"ComfyUI still unreachable after restart wait: {exc}")
        if response.status_code != 200:
            raise ComfySubmitError(f"HTTP {response.status_code}: {response.text}")

        prompt_id = response.json().get("prompt_id")
        if not prompt_id:
            raise ComfySubmitError("No prompt_id in response")

        job_start_time = time.time()
        try:
            self._poll_until_complete(prompt_id, timeout_sec)
        except Exception as exc:
            if "ConnectionReset" in str(exc) or "Connection aborted" in str(exc) or "ConnectionError" in type(exc).__name__:
                print(f"  ComfyUI crashed mid-poll, waiting for restart...")
                self._wait_for_comfy(wait_sec=60, poll_interval=5)
                raise ComfySubmitError(f"ComfyUI crashed during execution: {exc}")
            raise
        elapsed = time.time() - job_start_time

        frame_paths = self._collect_frames(prompt_id, scene.scene_id, job_start_time, filename_prefix)

        return SubmitResult(
            prompt_id=prompt_id,
            scene_id=scene.scene_id,
            frame_paths=frame_paths,
            elapsed_sec=elapsed,
            filename_prefix=filename_prefix,
        )

    def _wait_for_comfy(self, wait_sec: float = 60, poll_interval: float = 5) -> None:
        deadline = time.time() + wait_sec
        while time.time() < deadline:
            try:
                r = self.session.get(f"http://{self.host}:{self.port}/system_stats", timeout=3)
                if r.status_code == 200:
                    print("  ComfyUI is back online.")
                    return
            except Exception:
                pass
            time.sleep(poll_interval)
        print("  ComfyUI did not come back within the wait period.")

    def flush_queue(self) -> None:
        try:
            self.session.post(
                f"http://{self.host}:{self.port}/queue",
                json={"clear": True},
                timeout=5,
            )
        except Exception:
            pass

    def _validate_reference_locked_graph_contract(self, workflow: dict, reference_image_path: Path | None) -> list[str]:
        """Validate workflow graph structure for reference_locked mode.

        MK-REAL3R — Hard pre-submit graph contract gate.
        Fails before HTTP submit if workflow structure is invalid for reference_locked mode.

        Args:
            workflow: ComfyUI workflow dict
            reference_image_path: Reference image path

        Returns:
            List of error strings (empty if valid)
        """
        errors = []

        # Check for LoadImage node
        load_image_node_id = None
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "LoadImage":
                load_image_node_id = node_id
                break

        if not load_image_node_id:
            errors.append("no LoadImage node found in workflow")
        else:
            # Check LoadImage has image path
            load_image_node = workflow.get(load_image_node_id, {})
            load_image_path = load_image_node.get("inputs", {}).get("image")
            if not load_image_path or load_image_path == "data/references/character_reference_01.png":
                # Allow default placeholder path, but warn if reference_image_path is missing
                if not reference_image_path:
                    errors.append("reference_image_path is required for reference_locked mode")
                elif not load_image_path:
                    errors.append(f"LoadImage node {load_image_node_id} has no image path set")

        # Check for VAEEncode node
        vae_encode_node_id = None
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "VAEEncode":
                vae_encode_node_id = node_id
                break

        if not vae_encode_node_id:
            errors.append("no VAEEncode node found in workflow")

        # MK-REAL3R-3A — Check for resize node (ImageScale or ImageResize) between LoadImage and VAEEncode
        # This ensures reference image is resized to target resolution
        # Prefer ImageScale (available in this ComfyUI), accept ImageResize for backwards compatibility
        RESIZE_NODE_TYPES = ("ImageScale", "ImageResize")
        resize_node_id = None
        resize_node_class = None
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") in RESIZE_NODE_TYPES:
                resize_node_id = node_id
                resize_node_class = node.get("class_type")
                break

        if not resize_node_id:
            errors.append("no resize node (ImageScale or ImageResize) found in workflow")
        else:
            # Check resize node has correct target resolution (480x640 for vertical)
            resize_node = workflow.get(resize_node_id, {})
            resize_width = resize_node.get("inputs", {}).get("width")
            resize_height = resize_node.get("inputs", {}).get("height")
            if resize_width != 480 or resize_height != 640:
                errors.append(f"{resize_node_class} node {resize_node_id} has resolution {resize_width}x{resize_height}, must be 480x640 for reference_locked mode")

            # Check resize node is connected: LoadImage -> resize -> VAEEncode
            resize_image_input = resize_node.get("inputs", {}).get("image")
            if not resize_image_input or not isinstance(resize_image_input, list):
                errors.append(f"{resize_node_class} node {resize_node_id} has no valid image input")
            else:
                resize_source_id = str(resize_image_input[0])
                if resize_source_id != load_image_node_id:
                    errors.append(f"{resize_node_class} node {resize_node_id} image input not connected to LoadImage {load_image_node_id}")

            # Check VAEEncode pixels input comes from resize node
            if vae_encode_node_id:
                vae_node = workflow.get(vae_encode_node_id, {})
                vae_pixels_input = vae_node.get("inputs", {}).get("pixels")
                if not vae_pixels_input or not isinstance(vae_pixels_input, list):
                    errors.append(f"VAEEncode node {vae_encode_node_id} has no valid pixels input")
                else:
                    vae_source_id = str(vae_pixels_input[0])
                    if vae_source_id != resize_node_id:
                        errors.append(f"VAEEncode node {vae_encode_node_id} pixels input not connected to {resize_node_class} {resize_node_id}")

        # Check KSampler latent_image connection
        ksampler_node_id = None
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "KSampler":
                ksampler_node_id = node_id
                break

        if ksampler_node_id:
            ksampler_node = workflow.get(ksampler_node_id, {})
            latent_image = ksampler_node.get("inputs", {}).get("latent_image")
            if not latent_image:
                errors.append(f"KSampler node {ksampler_node_id} has no latent_image connection")
            elif not isinstance(latent_image, list) or len(latent_image) < 2:
                errors.append(f"KSampler node {ksampler_node_id} latent_image has invalid format")
            else:
                source_id = str(latent_image[0])
                source_node = workflow.get(source_id)
                if not source_node:
                    errors.append(f"KSampler latent_image source node {source_id} not found")
                elif source_node.get("class_type") == "EmptyLatentImage":
                    errors.append(f"KSampler latent_image connected to EmptyLatentImage {source_id} instead of VAEEncode")
                elif vae_encode_node_id and source_id != vae_encode_node_id:
                    errors.append(f"KSampler latent_image connected to {source_node.get('class_type')} {source_id} instead of VAEEncode {vae_encode_node_id}")
            
            # MK-REAL3R-2 — Check KSampler has steps
            steps = ksampler_node.get("inputs", {}).get("steps")
            if not steps:
                errors.append(f"KSampler node {ksampler_node_id} has no steps value")

        # Check batch_size is 1 only if EmptyLatentImage is connected to KSampler
        # In reference_locked mode, EmptyLatentImage may exist but should be disconnected
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage":
                batch_size = node.get("inputs", {}).get("batch_size")
                # Only check batch_size if this EmptyLatentImage is connected to KSampler
                if ksampler_node_id:
                    ksampler_node = workflow.get(ksampler_node_id, {})
                    latent_image = ksampler_node.get("inputs", {}).get("latent_image")
                    if latent_image and isinstance(latent_image, list) and str(latent_image[0]) == node_id:
                        # EmptyLatentImage is connected to KSampler - check batch_size
                        if batch_size and batch_size > 1:
                            errors.append(f"EmptyLatentImage node {node_id} batch_size is {batch_size}, must be 1 for reference_locked mode")

        return errors

    def _inject_workflow(self, workflow: dict, scene: BuiltScene, generation_mode: str | None = None) -> None:
        inject_map = workflow.pop("__inject__", {})
        pos_node = inject_map.get("positive_prompt_node")
        neg_node = inject_map.get("negative_prompt_node")
        frame_node = inject_map.get("frame_count_node")
        lora_node = inject_map.get("lora_stack_node")

        if pos_node and pos_node in workflow:
            workflow[pos_node]["inputs"]["text"] = scene.positive_prompt
        if neg_node and neg_node in workflow:
            workflow[neg_node]["inputs"]["text"] = scene.negative_prompt
        if frame_node and frame_node in workflow:
            workflow[frame_node]["inputs"]["value"] = scene.total_frames
        if lora_node and lora_node in workflow:
            workflow[lora_node]["inputs"]["lora_stack"] = scene.lora_stack

        # MK-PROMPTLOCK1 — Fallback: if __inject__ did not provide pos/neg nodes,
        # follow KSampler.positive / KSampler.negative connections to find CLIPTextEncode nodes
        if not (pos_node and pos_node in workflow) or not (neg_node and neg_node in workflow):
            for node_id, node in workflow.items():
                if not isinstance(node, dict) or node.get("class_type") != "KSampler":
                    continue
                inputs = node.get("inputs", {})
                pos_link = inputs.get("positive")
                neg_link = inputs.get("negative")
                if not pos_node or pos_node not in workflow:
                    if isinstance(pos_link, list) and len(pos_link) >= 1:
                        candidate = str(pos_link[0])
                        candidate_node = workflow.get(candidate)
                        if candidate_node and candidate_node.get("class_type") == "CLIPTextEncode":
                            candidate_node["inputs"]["text"] = scene.positive_prompt
                            print(f"[MK-PROMPTLOCK1] Injected positive_prompt into CLIPTextEncode node {candidate}")
                if not neg_node or neg_node not in workflow:
                    if isinstance(neg_link, list) and len(neg_link) >= 1:
                        candidate = str(neg_link[0])
                        candidate_node = workflow.get(candidate)
                        if candidate_node and candidate_node.get("class_type") == "CLIPTextEncode":
                            candidate_node["inputs"]["text"] = scene.negative_prompt
                            print(f"[MK-PROMPTLOCK1] Injected negative_prompt into CLIPTextEncode node {candidate}")
                break  # Only process first KSampler

        # Inject frame count into EmptyLatentImage batch_size if present
        # MK-REAL2R-2: Use safe smoke limit for batch_size, not total_frames
        # MK-REAL3R: Force batch_size=1 for reference_locked mode
        if generation_mode == "reference_locked":
            safe_batch_size = 1
        else:
            safe_batch_size = min(scene.total_frames, 2)
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "EmptyLatentImage":
                node["inputs"]["batch_size"] = safe_batch_size
                print(f"[INJECT] Node {node_id}: batch_size = {safe_batch_size} (limited from {scene.total_frames})")

        # Randomize seed to prevent ComfyUI from using execution cache
        import random
        for node in workflow.values():
            if isinstance(node, dict) and node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = random.randint(1, 2**32 - 1)

    def _poll_until_complete(self, prompt_id: str, timeout_sec: float) -> None:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            url = f"http://{self.host}:{self.port}/history/{prompt_id}"
            response = self.session.get(url)
            if response.status_code != 200:
                raise ComfySubmitError(f"Poll HTTP {response.status_code}")

            history = response.json()
            if prompt_id in history:
                status = history[prompt_id].get("status", {})
                if status.get("completed", False):
                    return
                status_str = status.get("status_str", "")
                if status_str == "error":
                    # Extract exception message if available
                    msgs = status.get("messages", [])
                    err_msg = next(
                        (m[1].get("exception_message", "unknown")
                         for m in msgs if isinstance(m, list) and m[0] == "execution_error"),
                        "execution_error",
                    )
                    raise ComfySubmitError(f"ComfyUI execution error: {err_msg}")

            time.sleep(1.0)

        raise ComfyTimeoutError(f"Timeout after {timeout_sec}s")

    def _collect_frames(self, prompt_id: str, scene_id: str, job_start_time: float, filename_prefix: str | None = None) -> list[Path]:
        # RC-REAL1B-2: Use filename_prefix for deterministic frame collection
        # Check ComfyUI's output directory (agent subfolder based on filename_prefix)
        # The portable install path is known from the system
        comfy_output = Path("F:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126/ComfyUI_windows_portable/ComfyUI/output")
        
        search_paths = [
            comfy_output,
            comfy_output / "agent",
            self.output_dir / scene_id,
            self.output_dir,
        ]
        
        # If filename_prefix is provided, use it for identification
        if filename_prefix:
            print(f"[RC-REAL1B-2] Collecting frames with filename_prefix: {filename_prefix}")
            for search_dir in search_paths:
                if search_dir.exists():
                    # Look for PNG files matching the filename_prefix
                    matching_pngs = list(search_dir.glob(f"{filename_prefix}_*.png"))
                    if matching_pngs:
                        # Sort by filename to ensure deterministic order
                        matching_pngs.sort()
                        # RC-REAL1B-4: Apply QC gate to reject blank/solid frames
                        valid_frames = []
                        for frame_path in matching_pngs:
                            qc_result = self._qc_check_frame(frame_path, expected_width=None, expected_height=None)
                            if qc_result["accepted"]:
                                valid_frames.append(frame_path)
                                print(f"[RC-REAL1B-4 QC] Frame {frame_path.name} accepted: {qc_result['reason']}")
                            else:
                                print(f"[RC-REAL1B-4 QC] Frame {frame_path.name} REJECTED: {qc_result['reason']}")
                        
                        print(f"[RC-REAL1B-2] Found {len(matching_pngs)} total frames, {len(valid_frames)} passed QC from {search_dir} with prefix {filename_prefix}")
                        return valid_frames
            print(f"[RC-REAL1B-2] No frames found with filename_prefix {filename_prefix}")
            return []
        else:
            # Fallback to timestamp-based filtering (legacy behavior)
            print(f"[WARN] No filename_prefix provided, using legacy timestamp-based collection")
            for search_dir in search_paths:
                if search_dir.exists():
                    # Look for PNG files modified after job started
                    all_pngs = list(search_dir.glob("*.png"))
                    # Filter to files modified after job submission started
                    recent_pngs = [p for p in all_pngs if p.stat().st_mtime >= job_start_time]
                    if recent_pngs:
                        # Sort by modification time (newest first, but ascending for assembly)
                        recent_pngs.sort(key=lambda p: p.stat().st_mtime)
                        # Apply QC gate to legacy collection as well
                        valid_frames = []
                        for frame_path in recent_pngs:
                            qc_result = self._qc_check_frame(frame_path, expected_width=None, expected_height=None)
                            if qc_result["accepted"]:
                                valid_frames.append(frame_path)
                        print(f"[COLLECT] Found {len(recent_pngs)} total frames, {len(valid_frames)} passed QC from {search_dir} (legacy timestamp method)")
                        return valid_frames
            
            print(f"[WARN] No frames found modified after {job_start_time}")
            return []

    def _qc_check_frame(self, frame_path: Path, expected_width: int | None = None, expected_height: int | None = None) -> dict:
        """RC-REAL1B-4: Quality control check for blank/solid frames.
        
        Checks if frame is:
        - readable
        - correct dimensions (expected_width x expected_height, or any if not specified)
        - RGB mode
        - file size above threshold
        - not mostly solid color
        - has sufficient entropy
        
        Args:
            frame_path: Path to frame file
            expected_width: Expected width in pixels (None to skip dimension check)
            expected_height: Expected height in pixels (None to skip dimension check)
        
        Returns:
            dict with 'accepted' (bool) and 'reason' (str)
        """
        try:
            from PIL import Image
            import numpy as np
            
            # Check file exists and has reasonable size
            if not frame_path.exists():
                return {"accepted": False, "reason": "file does not exist"}
            
            file_size = frame_path.stat().st_size
            if file_size < 1000:  # Less than 1KB is suspicious
                return {"accepted": False, "reason": f"file size too small ({file_size} bytes)"}
            
            # Load image
            img = Image.open(frame_path)
            if img.mode != "RGB":
                return {"accepted": False, "reason": f"not RGB mode (got {img.mode})"}
            
            width, height = img.size
            # Only check dimensions if expected dimensions are provided
            if expected_width is not None and expected_height is not None:
                if width != expected_width or height != expected_height:
                    return {"accepted": False, "reason": f"wrong dimensions ({width}x{height}, expected {expected_width}x{expected_height})"}
            
            # Convert to numpy array for analysis
            img_array = np.array(img)
            
            # Check if image is mostly one color (solid/blank)
            # Calculate standard deviation of pixel values
            std_dev = np.std(img_array)
            if std_dev < 10:  # Very low variation indicates solid color
                return {"accepted": False, "reason": f"low variation (std={std_dev:.2f}), likely solid color"}
            
            # Check mean pixel values to detect specific problematic colors
            mean_r = np.mean(img_array[:, :, 0])
            mean_g = np.mean(img_array[:, :, 1])
            mean_b = np.mean(img_array[:, :, 2])
            
            # Check for beige/white/black
            if mean_r > 200 and mean_g > 200 and mean_b > 200:
                return {"accepted": False, "reason": f"too bright/white (R={mean_r:.1f}, G={mean_g:.1f}, B={mean_b:.1f})"}
            if mean_r < 30 and mean_g < 30 and mean_b < 30:
                return {"accepted": False, "reason": f"too dark/black (R={mean_r:.1f}, G={mean_g:.1f}, B={mean_b:.1f})"}
            
            # Calculate entropy (measure of randomness/diversity)
            from scipy.stats import entropy
            hist, _ = np.histogram(img_array.ravel(), bins=256, range=(0, 256))
            hist = hist / np.sum(hist)
            img_entropy = entropy(hist)
            
            if img_entropy < 3.0:  # Low entropy indicates simple/repetitive patterns
                return {"accepted": False, "reason": f"low entropy ({img_entropy:.2f}), likely simple pattern"}
            
            return {"accepted": True, "reason": f"passed QC (std={std_dev:.2f}, entropy={img_entropy:.2f})"}
            
        except ImportError as e:
            # If scipy/PIL not available, accept frame but log warning
            print(f"[RC-REAL1B-4 QC] Warning: QC libraries not available ({e}), accepting frame without full QC")
            return {"accepted": True, "reason": "QC libraries not available, accepted without full check"}
        except Exception as e:
            return {"accepted": False, "reason": f"QC error: {str(e)}"}
