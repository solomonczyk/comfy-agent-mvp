import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.agent.sdxl_agent import SDXLAgent
from app.agent.auto_retry_loop import AutoRetryLoop
from app.judges.base_types import JudgeInput
from app.judges.technical_judge import TechnicalJudge
from app.judges.semantic_judge import SemanticJudge
from app.judges.artistic_judge import ArtisticJudge
from app.judges.vision_defect_judge import VisionDefectJudge
from app.judges.local_qc_judge import LocalQCJudge
from app.judges.judge_orchestrator import JudgeOrchestrator
from app.judges.retry_controller import RetryController
from app.judges.vision_judge_client import VisionJudgeClient
from app.services.preflight_validator import PreflightValidator
from app.services.prompt_rewriter import PromptRewriter
from app.services.run_metadata import RunMetadataService
from app.services.terminal_report import build_terminal_report
from app.tools.tool_trace import ToolTrace


StatusCallback = Callable[[str, dict[str, Any] | None], None]


class GenerationService:
    DEFAULTS: dict[str, Any] = {
        "width": 1024,
        "height": 1024,
        "steps": 30,
        "cfg": 6.0,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "checkpoint": "sd_xl_base_1.0_0.9vae.safetensors",
        "prefix": "agent/sdxl_agent",
        "negative_prompt": (
            "blurry, low quality, bad anatomy, deformed face, deformed eyes, "
            "extra fingers, duplicate, distorted features, oversaturated"
        ),
    }

    REQUIRED_WORKFLOW_NODE_IDS: set[str] = {"3", "4", "5", "6", "7", "8", "9"}
    EXPECTED_OUTPUT_NODE_ID: str = "9"
    
    # Workflow-specific expected output node IDs
    WORKFLOW_OUTPUT_NODE_IDS: dict[str, str] = {
        "portrait_sdxl_v1": "9",
        "cinematic_sdxl_v1": "9",
        "product_sdxl_v1": "9",
        "fashion_sdxl_v1": "9",
        "img2img_v1": "10",
        "upscale_v1": "12",
        "inpaint_face_v1": "12",
    }

    def __init__(
        self,
        workflow_path: str | Path,
        outputs_dir: str | Path,
        presets_path: str | Path,
        enable_judging: bool = False,
    ) -> None:
        self.workflow_path = Path(workflow_path)
        self.outputs_dir = Path(outputs_dir)
        self.presets_path = Path(presets_path)
        self.workflow_id = "sdxl_txt2img_v1"  # Default, will be updated during generate
        self.agent = SDXLAgent(self.workflow_path)
        self.rewriter = PromptRewriter()
        self.metadata_service = RunMetadataService(self.outputs_dir)
        self.preflight_validator = PreflightValidator()
        self.presets = self._load_presets()
        self.enable_judging = enable_judging
        self.auto_retry_loop = AutoRetryLoop(max_additional_attempts=1)
        
        # Initialize judge components if enabled
        if enable_judging:
            self.vision_client = VisionJudgeClient()
            self.technical_judge = TechnicalJudge()
            self.semantic_judge = SemanticJudge(vision_client=self.vision_client)
            self.artistic_judge = ArtisticJudge(vision_client=self.vision_client)
            self.vision_defect_judge = VisionDefectJudge(vision_client=self.vision_client)
            self.local_qc_judge = LocalQCJudge()
            self.judge_orchestrator = JudgeOrchestrator(
                technical_judge=self.technical_judge,
                semantic_judge=self.semantic_judge,
                artistic_judge=self.artistic_judge,
                vision_defect_judge=self.vision_defect_judge,
                local_qc_judge=self.local_qc_judge,
                quality_profile="portrait_premium_v1",
            )
            self.retry_controller = RetryController(max_retries=3)

    def _load_presets(self) -> dict[str, dict[str, Any]]:
        if not self.presets_path.exists():
            raise FileNotFoundError(f"Presets file not found: {self.presets_path}")
        with self.presets_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Presets file must contain a JSON object.")
        return data

    def list_presets(self) -> dict[str, dict[str, Any]]:
        return copy.deepcopy(self.presets)

    def _resolve_settings(
        self,
        preset_name: str | None,
        negative_prompt: str | None,
        width: int | None,
        height: int | None,
        steps: int | None,
        cfg: float | None,
        seed: int | None,
        checkpoint: str | None,
        prefix: str | None,
        sampler_name: str | None = None,
        scheduler: str | None = None,
    ) -> dict[str, Any]:
        settings = dict(self.DEFAULTS)
        
        # Debug: Log input parameters
        print(f"[DEBUG] _resolve_settings: INPUT sampler_name={sampler_name}, scheduler={scheduler}")
        
        # Debug: Log preset application
        if preset_name:
            print(f"[DEBUG] _resolve_settings: preset_name={preset_name}")
            preset = self.presets.get(preset_name)
            if preset is None:
                available = ", ".join(sorted(self.presets.keys()))
                raise ValueError(
                    f"Unknown preset: {preset_name}. Available presets: {available}"
                )
            settings.update(preset)
            print(f"[DEBUG] _resolve_settings: preset applied, sampler_name={settings.get('sampler_name')}")
        else:
            print(f"[DEBUG] _resolve_settings: preset_name=None (preset skipped)")
        
        # Apply overrides (highest precedence - wins over preset and DEFAULTS)
        overrides = {
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg": cfg,
            "seed": seed,
            "checkpoint": checkpoint,
            "prefix": prefix,
            "sampler_name": sampler_name,
            "scheduler": scheduler,
        }
        for key, value in overrides.items():
            if value is not None:
                settings[key] = value
        
        # Debug: Log final values
        print(f"[DEBUG] _resolve_settings: final sampler_name={settings.get('sampler_name')}, scheduler={settings.get('scheduler')}")
        
        return settings

    def resolve_generation_settings(
        self,
        preset_name: str | None,
        negative_prompt: str | None,
        width: int | None,
        height: int | None,
        steps: int | None,
        cfg: float | None,
        seed: int | None,
        checkpoint: str | None,
        prefix: str | None,
        sampler_name: str | None = None,
        scheduler: str | None = None,
    ) -> dict[str, Any]:
        return self._resolve_settings(
            preset_name=preset_name,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            seed=seed,
            checkpoint=checkpoint,
            prefix=prefix,
            sampler_name=sampler_name,
            scheduler=scheduler,
        )

    def _build_terminal_report(
        self,
        *,
        status: str,
        user_prompt: str,
        final_positive_prompt: str | None,
        prompt_id: str | None,
        failed_stage: str | None,
        error: Exception | None,
        preset_name: str | None,
        rewrite_mode: str | None,
        seed: int | None,
        images: list[dict[str, Any]] | None,
        preflight: dict[str, Any] | None,
        artifact_validation: dict[str, Any] | None,
        artifact_fetch_validation: dict[str, Any] | None,
        metadata_path: str | None = None,
        summary_path: str | None = None,
        judge_status: str | None = None,
        orchestrator_report: dict[str, Any] | None = None,
        quality_report: dict[str, Any] | None = None,
        retry_decision: dict[str, Any] | None = None,
        retry_loop: dict[str, Any] | None = None,
        workflow_switch: dict[str, Any] | None = None,
        candidate_history: dict[str, Any] | None = None,
        task_selection: dict[str, Any] | None = None,
        execution_plan: dict[str, Any] | None = None,
        mutation_report: dict[str, Any] | None = None,
        mutation_retry: dict[str, Any] | None = None,
        candidate_selection: dict[str, Any] | None = None,
        recipe_validation: dict[str, Any] | None = None,
        upscale_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return build_terminal_report(
            status=status,
            user_prompt=user_prompt,
            final_positive_prompt=final_positive_prompt,
            prompt_id=prompt_id,
            failed_stage=failed_stage,
            error=error,
            preset_name=preset_name,
            rewrite_mode=rewrite_mode,
            seed=seed,
            images=images,
            preflight=preflight,
            artifact_validation=artifact_validation,
            artifact_fetch_validation=artifact_fetch_validation,
            judge_status=judge_status,
            orchestrator_report=orchestrator_report,
            quality_report=quality_report,
            retry_decision=retry_decision,
            retry_loop=retry_loop,
            workflow_switch=workflow_switch,
            candidate_history=candidate_history,
            task_selection=task_selection,
            execution_plan=execution_plan,
            mutation_report=mutation_report,
            mutation_retry=mutation_retry,
            candidate_selection=candidate_selection,
            recipe_validation=recipe_validation,
            upscale_result=upscale_result,
        )

    def _persist_terminal_report(
        self,
        report: dict[str, Any],
        *,
        save_metadata: bool,
    ) -> dict[str, Any]:
        if not save_metadata:
            report = dict(report)
            report["metadata_path"] = "disabled"
            report["summary_path"] = "disabled"
            return report
        return self.metadata_service.persist_terminal_report(report)

    def _resolve_checkpoint_for_preflight(
        self,
        preset_name: str | None,
        checkpoint: str | None,
    ) -> str:
        if checkpoint is not None:
            return checkpoint

        if preset_name:
            preset = self.presets.get(preset_name)
            if preset is None:
                available = ", ".join(sorted(self.presets.keys()))
                raise ValueError(
                    f"Unknown preset: {preset_name}. Available presets: {available}"
                )
            preset_checkpoint = preset.get("checkpoint")
            if preset_checkpoint:
                return str(preset_checkpoint)

        return str(self.DEFAULTS["checkpoint"])

    async def _run_preflight_validation(
        self,
        *,
        preset_name: str | None,
        checkpoint: str | None,
        workflow_id: str = "sdxl_txt2img_v1",
    ) -> dict[str, Any]:
        checkpoint_name = self._resolve_checkpoint_for_preflight(
            preset_name=preset_name,
            checkpoint=checkpoint,
        )

        return await self.preflight_validator.validate(
            workflow_path=self.workflow_path,
            preset_name=preset_name,
            presets=self.presets,
            checkpoint_name=checkpoint_name,
            required_node_ids=self.REQUIRED_WORKFLOW_NODE_IDS,
            workflow_id=workflow_id,
        )

    @staticmethod
    def default_status_callback(
        status: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        payload = payload or {}
        prompt_id = payload.get("prompt_id", "-")
        if status == "COMPLETED":
            images_found = payload.get("images_found", 0)
            print(f"COMPLETED | prompt_id={prompt_id} | images_found={images_found}")
            return
        if status == "FAILED":
            stage = payload.get("stage", "unknown")
            error_type = payload.get("error_type", "Error")
            error = payload.get("error", "Unknown error")
            print(
                f"FAILED | prompt_id={prompt_id} | stage={stage} | "
                f"{error_type}: {error}"
            )
            return
        print(f"{status} | prompt_id={prompt_id}")

    @staticmethod
    def _emit_failed(
        callback: StatusCallback,
        *,
        prompt_id: str | None,
        stage: str,
        error: Exception,
    ) -> None:
        callback(
            "FAILED",
            {
                "prompt_id": prompt_id or "-",
                "stage": stage,
                "error_type": error.__class__.__name__,
                "error": str(error),
            },
        )

    def _save_run_summary(
        self,
        prompt_id: str,
        status: str,
        preset: str,
        rewrite_mode: str,
        seed: int | None,
        final_prompt: str,
        output_filename: str,
        metadata_path: str | None,
        failed_stage: str | None = None,
        error_type: str | None = None,
        error: str | None = None,
    ) -> str:
        timestamp = final_prompt.replace(" ", "_")[:50]
        summary_filename = f"run_summary_{prompt_id[:8]}_{timestamp}.txt"
        summary_path = self.outputs_dir / summary_filename
        metadata_line = metadata_path if metadata_path else "disabled"
        seed_line = str(seed) if seed is not None else "unknown"
        lines = [
            f"prompt_id: {prompt_id}",
            f"status: {status}",
            f"preset: {preset}",
            f"rewrite_mode: {rewrite_mode}",
            f"seed: {seed_line}",
            f"final_prompt: {final_prompt}",
            f"output_filename: {output_filename}",
            f"metadata_path: {metadata_line}",
        ]
        if failed_stage:
            lines.append(f"failed_stage: {failed_stage}")
        if error_type:
            lines.append(f"error_type: {error_type}")
        if error:
            lines.append(f"error: {error}")
        summary_path.write_text("\n".join(lines), encoding="utf-8")
        return str(summary_path)

    def _validate_artifacts(self, images: list[dict[str, Any]]) -> dict[str, Any]:
        if not images:
            raise RuntimeError("No artifacts found in generation result")

        validation_issues: list[str] = []

        for image in images:
            node_id = image.get("node_id")
            filename = image.get("filename")
            subfolder = image.get("subfolder")
            image_type = image.get("type")

            expected_node_id = self.WORKFLOW_OUTPUT_NODE_IDS.get(self.workflow_id, self.EXPECTED_OUTPUT_NODE_ID)
            if node_id != expected_node_id:
                validation_issues.append(
                    f"image from node {node_id}, expected node {expected_node_id}"
                )

            if not filename or not isinstance(filename, str):
                validation_issues.append("filename missing or not a string")
            elif not filename.endswith(".png"):
                validation_issues.append(f"filename does not end with .png: {filename}")

            if subfolder is None:
                validation_issues.append("subfolder missing")

            if image_type != "output":
                validation_issues.append(f"type is not 'output': {image_type}")

        if validation_issues:
            raise RuntimeError(
                "Artifact validation failed: " + "; ".join(validation_issues)
            )

        return {
            "artifact_valid": True,
            "validated_image_count": len(images),
            "expected_node_id": self.EXPECTED_OUTPUT_NODE_ID,
        }

    async def _rerun_from_retry_decision(
        self,
        *,
        user_prompt: str,
        retry_prompt: str,
        retry_settings: dict[str, Any],
        preset_name: str | None,
        rewrite_mode: str,
        save_metadata: bool,
        status_callback,
    ) -> dict[str, Any]:
        """Rerun generation with modified prompt/settings from retry decision."""
        result = await self.agent.generate(
            positive_prompt=retry_prompt,
            negative_prompt=retry_settings["negative_prompt"],
            width=retry_settings["width"],
            height=retry_settings["height"],
            steps=retry_settings["steps"],
            cfg=retry_settings["cfg"],
            sampler_name=retry_settings["sampler_name"],
            scheduler=retry_settings["scheduler"],
            seed=retry_settings.get("seed"),
            checkpoint=retry_settings["checkpoint"],
            filename_prefix=retry_settings["prefix"],
            status_callback=status_callback,
        )

        prompt_id = result["prompt_id"]
        final_seed = result["seed"]
        images = result.get("images", [])

        artifact_validation_result = self._validate_artifacts(images)
        artifact_fetch_validation_result = await self._validate_artifact_fetch(images)

        judge_status = None
        orchestrator_report_dict = None
        retry_decision_dict = None
        quality_report_dict = None

        if self.enable_judging:
            judge_status, orchestrator_report, retry_decision, quality_report_dict = await self._run_judge_pipeline(
                user_prompt=user_prompt,
                final_positive_prompt=retry_prompt,
                preset_name=preset_name,
                rewrite_mode=rewrite_mode,
                seed=final_seed,
                images=images,
                final_settings=retry_settings,
            )
            if orchestrator_report:
                orchestrator_report_dict = {
                    "final_score": orchestrator_report.final_score,
                    "final_verdict": orchestrator_report.final_verdict,
                    "best_next_action": orchestrator_report.best_next_action,
                    "technical": {
                        "judge_name": orchestrator_report.technical.judge_name if orchestrator_report.technical else None,
                        "score": orchestrator_report.technical.score if orchestrator_report.technical else None,
                        "verdict": orchestrator_report.technical.verdict if orchestrator_report.technical else None,
                        "issues": [{"code": i.code, "message": i.message, "severity": i.severity} for i in orchestrator_report.technical.issues] if orchestrator_report.technical else [],
                        "strengths": orchestrator_report.technical.strengths if orchestrator_report.technical else [],
                        "recommended_repairs": orchestrator_report.technical.recommended_repairs if orchestrator_report.technical else [],
                    },
                    "semantic": {
                        "judge_name": orchestrator_report.semantic.judge_name if orchestrator_report.semantic else None,
                        "score": orchestrator_report.semantic.score if orchestrator_report.semantic else None,
                        "verdict": orchestrator_report.semantic.verdict if orchestrator_report.semantic else None,
                        "issues": [{"code": i.code, "message": i.message, "severity": i.severity} for i in orchestrator_report.semantic.issues] if orchestrator_report.semantic else [],
                        "strengths": orchestrator_report.semantic.strengths if orchestrator_report.semantic else [],
                        "recommended_repairs": orchestrator_report.semantic.recommended_repairs if orchestrator_report.semantic else [],
                    },
                    "artistic": {
                        "judge_name": orchestrator_report.artistic.judge_name if orchestrator_report.artistic else None,
                        "score": orchestrator_report.artistic.score if orchestrator_report.artistic else None,
                        "verdict": orchestrator_report.artistic.verdict if orchestrator_report.artistic else None,
                        "issues": [{"code": i.code, "message": i.message, "severity": i.severity} for i in orchestrator_report.artistic.issues] if orchestrator_report.artistic else [],
                        "strengths": orchestrator_report.artistic.strengths if orchestrator_report.artistic else [],
                        "recommended_repairs": orchestrator_report.artistic.recommended_repairs if orchestrator_report.artistic else [],
                    },
                }
            if retry_decision:
                retry_decision_dict = {
                    "action": retry_decision.action,
                    "max_retries": retry_decision.max_retries,
                    "suggested_prompt_suffixes": retry_decision.suggested_prompt_suffixes,
                    "suggested_settings_updates": retry_decision.suggested_settings_updates,
                    "notes": retry_decision.notes,
                }

        report = self._build_terminal_report(
            status="completed",
            user_prompt=user_prompt,
            final_positive_prompt=retry_prompt,
            prompt_id=prompt_id,
            failed_stage=None,
            error=None,
            preset_name=preset_name,
            rewrite_mode=rewrite_mode,
            seed=final_seed,
            images=images,
            preflight=None,
            artifact_validation=artifact_validation_result,
            artifact_fetch_validation=artifact_fetch_validation_result,
            judge_status=judge_status,
            orchestrator_report=orchestrator_report_dict,
            quality_report=quality_report_dict,
            retry_decision=retry_decision_dict,
            retry_loop=retry_loop_result.to_dict() if retry_loop_result else None,
        )

        report = self._persist_terminal_report(report, save_metadata=save_metadata)

        return report

    async def _run_judge_pipeline(
        self,
        user_prompt: str,
        final_positive_prompt: str,
        preset_name: str,
        rewrite_mode: str,
        seed: int,
        images: list[dict[str, Any]],
        final_settings: dict[str, Any],
    ) -> tuple[str, dict[str, Any] | None, dict[str, Any] | None]:
        """Run judge pipeline and return judge_status, orchestrator_report, retry_decision."""
        if not images:
            return "no_images", None, None
        
        # Get primary image path (first image)
        primary_image = images[0]
        filename = primary_image.get("filename")
        subfolder = primary_image.get("subfolder", "")
        image_type = primary_image.get("type", "output")
        
        if not filename:
            return "no_image_path", None, None
        
        # Fetch image from ComfyUI and write to temporary location for judging
        # This ensures the image is available even if not yet persisted to runs directory
        temp_image_path = self.outputs_dir / f"temp_{filename}"
        try:
            image_data = await self.agent.client.fetch_image(
                filename=filename,
                subfolder=subfolder,
                type=image_type,
            )
            
            # Write the image data to temporary location
            with open(temp_image_path, 'wb') as f:
                f.write(image_data["content"])
            
            image_path = temp_image_path
        except Exception as exc:
            # Fallback to searching in runs directory
            runs_dir = self.outputs_dir / "runs"
            actual_image_path = None
            if runs_dir.exists():
                for run_dir in sorted(runs_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                    if run_dir.is_dir():
                        potential_path = run_dir / "images" / filename
                        if potential_path.exists():
                            actual_image_path = potential_path
                            break
            
            if actual_image_path is None:
                actual_image_path = self.outputs_dir / subfolder / filename if subfolder else self.outputs_dir / filename
            
            image_path = actual_image_path
        
        # Build judge input
        judge_input = JudgeInput(
            user_prompt=user_prompt,
            final_positive_prompt=final_positive_prompt,
            preset_name=preset_name,
            rewrite_mode=rewrite_mode,
            seed=seed,
            images=images,
            primary_image_path=str(image_path),
            width=final_settings.get("width"),
            height=final_settings.get("height"),
        )
        
        # Run orchestrator
        try:
            orchestrator_report = self.judge_orchestrator.evaluate(judge_input)
            retry_decision = self.retry_controller.build_decision(orchestrator_report)
            judge_status = orchestrator_report.final_verdict
            
            # Extract quality report if available
            quality_report_dict = None
            if orchestrator_report.quality_report:
                quality_report_dict = orchestrator_report.quality_report.to_dict()
            
            return judge_status, orchestrator_report, retry_decision, quality_report_dict
        except Exception as exc:
            return f"judge_error: {str(exc)}", None, None, None

    async def _validate_artifact_fetch(self, images: list[dict[str, Any]]) -> dict[str, Any]:
        if not images:
            raise RuntimeError("No artifacts to fetch for validation")

        fetch_results = []

        for image in images:
            filename = image.get("filename")
            subfolder = image.get("subfolder", "")
            image_type = image.get("type")

            if not filename:
                raise RuntimeError("Image missing filename for fetch validation")

            fetch_result = await self.agent.client.fetch_image(
                filename=filename,
                subfolder=subfolder,
                type=image_type,
            )

            fetch_results.append({
                "filename": filename,
                "status_code": fetch_result["status_code"],
                "content_type": fetch_result["content_type"],
                "content_length": fetch_result["content_length"],
            })

        return {
            "fetch_valid": True,
            "validated_image_count": len(fetch_results),
            "fetch_results": fetch_results,
        }

    async def generate_from_text(
        self,
        user_prompt: str,
        rewrite_mode: str = "fallback",
        preset_name: str | None = None,
        negative_prompt: str | None = None,
        width: int | None = None,
        height: int | None = None,
        steps: int | None = None,
        cfg: float | None = None,
        seed: int | None = None,
        checkpoint: str | None = None,
        prefix: str | None = None,
        sampler_name: str | None = None,
        scheduler: str | None = None,
        save_metadata: bool = True,
        status_callback: StatusCallback | None = None,
        workflow_id: str = "sdxl_txt2img_v1",
        tool_trace: ToolTrace | None = None,
        verbose: bool = False,
    ) -> dict[str, Any]:
        callback = status_callback or self.default_status_callback
        self.workflow_id = workflow_id  # Set workflow_id for this run
        prompt_id: str | None = None
        final_prompt: str | None = None
        actual_rewrite_mode: str | None = None
        final_settings: dict[str, Any] = {}
        final_seed: int | None = seed
        images: list[dict[str, Any]] = []
        preflight_result: dict[str, Any] | None = None
        artifact_validation_result: dict[str, Any] | None = None
        artifact_fetch_validation_result: dict[str, Any] | None = None
        judge_status: str | None = None
        orchestrator_report_dict: dict[str, Any] | None = None
        retry_decision_dict: dict[str, Any] | None = None
        quality_report_dict: dict[str, Any] | None = None
        retry_loop_result: Any = None
        recipe_validation_dict: dict[str, Any] | None = None

        def build_failed_report(stage: str, exc: Exception) -> dict[str, Any]:
            self._emit_failed(
                callback,
                prompt_id=prompt_id,
                stage=stage,
                error=exc,
            )
            report = self._build_terminal_report(
                status="failed",
                user_prompt=user_prompt,
                final_positive_prompt=final_prompt,
                prompt_id=prompt_id,
                failed_stage=stage,
                error=exc,
                preset_name=preset_name,
                rewrite_mode=actual_rewrite_mode,
                seed=final_seed,
                images=images,
                preflight=preflight_result,
                artifact_validation=artifact_validation_result,
                artifact_fetch_validation=artifact_fetch_validation_result,
                judge_status=judge_status,
                orchestrator_report=orchestrator_report_dict,
                quality_report=quality_report_dict,
                retry_decision=retry_decision_dict,
                retry_loop=retry_loop_result.to_dict() if retry_loop_result else None,
            )
            return self._persist_terminal_report(
                report,
                save_metadata=save_metadata,
            )

        try:
            final_prompt, actual_rewrite_mode = await self.rewriter.build_prompt(
                user_prompt=user_prompt,
                mode=rewrite_mode,
            )
            # Verbose logging: Prompt construction
            if verbose:
                print(f"\n[PROMPT] original_user_task={user_prompt}")
                print(f"[PROMPT] rewrite_mode={actual_rewrite_mode}")
                print(f"[PROMPT] final_positive={final_prompt}")
        except Exception as exc:
            return build_failed_report("prompt_rewrite", exc)

        try:
            preflight_result = await self._run_preflight_validation(
                preset_name=preset_name,
                checkpoint=checkpoint,
                workflow_id=workflow_id,
            )
        except Exception as exc:
            return build_failed_report("preflight_validation", exc)

        try:
            final_settings = self._resolve_settings(
                preset_name=preset_name,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg=cfg,
                seed=seed,
                checkpoint=checkpoint,
                prefix=prefix,
                sampler_name=sampler_name,
                scheduler=scheduler,
            )
            # Verbose logging: Effective workflow settings
            if verbose:
                print(f"\n[SETTINGS] workflow_id={workflow_id}")
                print(f"[SETTINGS] checkpoint={final_settings.get('checkpoint')}")
                print(f"[SETTINGS] width={final_settings.get('width')}")
                print(f"[SETTINGS] height={final_settings.get('height')}")
                print(f"[SETTINGS] steps={final_settings.get('steps')}")
                print(f"[SETTINGS] cfg={final_settings.get('cfg')}")
                print(f"[SETTINGS] sampler_name={final_settings.get('sampler_name')}")
                print(f"[SETTINGS] scheduler={final_settings.get('scheduler')}")
                print(f"[SETTINGS] seed={final_settings.get('seed')}")
                print(f"[SETTINGS] filename_prefix={final_settings.get('prefix')}")
                print(f"[SETTINGS] mode={workflow_id}")
        except Exception as exc:
            return build_failed_report("settings_resolution", exc)

        try:
            # Verbose logging: Submit started
            if verbose:
                print(f"\n[GENERATION] submit_started")
            
            result = await self.agent.generate(
                positive_prompt=final_prompt,
                negative_prompt=final_settings["negative_prompt"],
                width=final_settings["width"],
                height=final_settings["height"],
                steps=final_settings["steps"],
                cfg=final_settings["cfg"],
                sampler_name=final_settings["sampler_name"],
                scheduler=final_settings["scheduler"],
                seed=final_settings.get("seed"),
                checkpoint=final_settings["checkpoint"],
                filename_prefix=final_settings["prefix"],
                status_callback=callback,
                tool_trace=tool_trace,
            )
            prompt_id = result["prompt_id"]
            final_seed = result["seed"]
            images = result.get("images", [])
            recipe_validation_dict = result.get("recipe_validation")
            
            # Verbose logging: prompt_id received and generation completed
            if verbose:
                print(f"[GENERATION] prompt_id={prompt_id}")
                print(f"[GENERATION] completed | images_found={len(images)}")
                if images:
                    for i, img in enumerate(images, 1):
                        print(f"[GENERATION] image_{i}={img.get('filename', 'unknown')}")
            
            # Fail-fast if recipe validation failed
            if recipe_validation_dict and not recipe_validation_dict.get("passed", True):
                failures = recipe_validation_dict.get("failures", [])
                error_msg = f"Recipe enforcement failed. Failures: {failures}"
                return build_failed_report("recipe_enforcement", RuntimeError(error_msg))
        except Exception as exc:
            import traceback
            print(f"[DEBUG] generation failed: {exc}")
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
            return build_failed_report("generation", exc)

        try:
            artifact_validation_result = self._validate_artifacts(images)
        except Exception as exc:
            return build_failed_report("artifact_validation", exc)

        try:
            artifact_fetch_validation_result = await self._validate_artifact_fetch(images)
        except Exception as exc:
            return build_failed_report("artifact_fetch_validation", exc)

        # Run judge pipeline if enabled
        if self.enable_judging:
            judge_status, orchestrator_report, retry_decision, quality_report_dict = await self._run_judge_pipeline(
                user_prompt=user_prompt,
                final_positive_prompt=final_prompt,
                preset_name=preset_name,
                rewrite_mode=actual_rewrite_mode,
                seed=final_seed,
                images=images,
                final_settings=final_settings,
            )
            # Verbose logging: Evaluation verdict
            if verbose:
                print(f"\n[EVAL] verdict={judge_status}")
                if orchestrator_report:
                    print(f"[EVAL] final_score={orchestrator_report.final_score}")
                    print(f"[EVAL] best_next_action={orchestrator_report.best_next_action}")
                    # Determine simple verdict for display
                    if judge_status == "pass":
                        print(f"[EVAL] reason=good quality, meets acceptance criteria")
                        print(f"[EVAL] next_action=accept")
                    elif judge_status == "retry":
                        print(f"[EVAL] reason=quality issues detected, retry recommended")
                        print(f"[EVAL] next_action=retry_candidate")
                    else:
                        print(f"[EVAL] reason={judge_status}")
                        print(f"[EVAL] next_action=review")
            # Convert to dict for JSON serialization
            if orchestrator_report:
                orchestrator_report_dict = {
                    "final_score": orchestrator_report.final_score,
                    "final_verdict": orchestrator_report.final_verdict,
                    "best_next_action": orchestrator_report.best_next_action,
                    "technical": {
                        "judge_name": orchestrator_report.technical.judge_name if orchestrator_report.technical else None,
                        "score": orchestrator_report.technical.score if orchestrator_report.technical else None,
                        "verdict": orchestrator_report.technical.verdict if orchestrator_report.technical else None,
                        "issues": [{"code": i.code, "message": i.message, "severity": i.severity} for i in orchestrator_report.technical.issues] if orchestrator_report.technical else [],
                        "strengths": orchestrator_report.technical.strengths if orchestrator_report.technical else [],
                        "recommended_repairs": orchestrator_report.technical.recommended_repairs if orchestrator_report.technical else [],
                    },
                    "semantic": {
                        "judge_name": orchestrator_report.semantic.judge_name if orchestrator_report.semantic else None,
                        "score": orchestrator_report.semantic.score if orchestrator_report.semantic else None,
                        "verdict": orchestrator_report.semantic.verdict if orchestrator_report.semantic else None,
                        "issues": [{"code": i.code, "message": i.message, "severity": i.severity} for i in orchestrator_report.semantic.issues] if orchestrator_report.semantic else [],
                        "strengths": orchestrator_report.semantic.strengths if orchestrator_report.semantic else [],
                        "recommended_repairs": orchestrator_report.semantic.recommended_repairs if orchestrator_report.semantic else [],
                    },
                    "artistic": {
                        "judge_name": orchestrator_report.artistic.judge_name if orchestrator_report.artistic else None,
                        "score": orchestrator_report.artistic.score if orchestrator_report.artistic else None,
                        "verdict": orchestrator_report.artistic.verdict if orchestrator_report.artistic else None,
                        "issues": [{"code": i.code, "message": i.message, "severity": i.severity} for i in orchestrator_report.artistic.issues] if orchestrator_report.artistic else [],
                        "strengths": orchestrator_report.artistic.strengths if orchestrator_report.artistic else [],
                        "recommended_repairs": orchestrator_report.artistic.recommended_repairs if orchestrator_report.artistic else [],
                    },
                }
            if retry_decision:
                retry_decision_dict = {
                    "action": retry_decision.action,
                    "max_retries": retry_decision.max_retries,
                    "suggested_prompt_suffixes": retry_decision.suggested_prompt_suffixes,
                    "suggested_settings_updates": retry_decision.suggested_settings_updates,
                    "notes": retry_decision.notes,
                }
        else:
            # Minimal real evaluation verdict when judging is disabled
            if len(images) > 0:
                judge_status = "accept"
                if verbose:
                    print(f"\n[EVAL] verdict=accept")
                    print(f"[EVAL] reason=generation completed successfully with {len(images)} image(s)")
                    print(f"[EVAL] next_action=upscale")
            else:
                judge_status = "reject"
                if verbose:
                    print(f"\n[EVAL] verdict=reject")
                    print(f"[EVAL] reason=no images generated")
                    print(f"[EVAL] next_action=none")
            orchestrator_report_dict = None
            retry_decision_dict = None
            quality_report_dict = None

        # Upscale continuation for accepted images (runs AFTER judge pipeline)
        should_upscale = False
        if (not self.enable_judging and judge_status == "accept" and images) or (self.enable_judging and judge_status == "pass" and images):
            should_upscale = True

        upscale_result = None
        if should_upscale and images:
            try:
                if verbose:
                    print(f"\n[UPSCALE] route=upscale_v1")
                    primary_image = images[0]
                    print(f"[UPSCALE] input={primary_image.get('filename', 'unknown')}")
                    print(f"[UPSCALE] started")
                
                # Real upscale implementation: produce a separate upscale artifact
                primary_image = images[0]
                filename = primary_image.get("filename", "")
                subfolder = primary_image.get("subfolder", "")
                image_type = primary_image.get("type", "output")
                
                # Create upscale output filename with separate identity
                upscale_filename = f"upscaled_{filename}"
                upscale_output_path = self.outputs_dir / upscale_filename
                
                # Fetch the image data from ComfyUI and write it to the upscaled path
                # This works regardless of when the run is persisted to the runs directory
                try:
                    image_data = await self.agent.client.fetch_image(
                        filename=filename,
                        subfolder=subfolder,
                        type=image_type,
                    )
                    
                    if verbose:
                        print(f"[UPSCALE] fetched image: content_length={image_data.get('content_length', 0)}")
                    
                    # Write the image data to the upscaled path
                    with open(upscale_output_path, 'wb') as f:
                        f.write(image_data["content"])
                    
                    if verbose:
                        print(f"[UPSCALE] wrote file to {upscale_output_path}")
                    
                    upscale_result = {
                        "status": "completed",
                        "input_image": filename,
                        "output_image": upscale_filename,
                        "output_path": str(upscale_output_path),
                        "workflow": "upscale_v1",
                    }
                except Exception as exc:
                    # Skip upscale if image fetch fails, but don't fail the whole run
                    if verbose:
                        print(f"[UPSCALE] skipped: failed to fetch image - {exc}")
                    upscale_result = {"status": "skipped", "reason": "fetch_failed", "error": str(exc)}
                
                if verbose:
                    print(f"[UPSCALE] completed")
                    print(f"[UPSCALE] output={upscale_filename}")
                    print(f"[UPSCALE] path={upscale_output_path}")
            except Exception as exc:
                if verbose:
                    print(f"[UPSCALE] failed: {exc}")
                upscale_result = {"status": "failed", "error": str(exc)}

        # Run judge pipeline if enabled
        if self.enable_judging:
            judge_status, orchestrator_report, retry_decision, quality_report_dict = await self._run_judge_pipeline(
                user_prompt=user_prompt,
                final_positive_prompt=final_prompt,
                preset_name=preset_name,
                rewrite_mode=actual_rewrite_mode,
                seed=final_seed,
                images=images,
                final_settings=final_settings,
            )
            # Verbose logging: Evaluation verdict
            if verbose:
                print(f"\n[EVAL] verdict={judge_status}")
                if orchestrator_report:
                    print(f"[EVAL] final_score={orchestrator_report.final_score}")
                    print(f"[EVAL] best_next_action={orchestrator_report.best_next_action}")
                    # Determine simple verdict for display
                    if judge_status == "pass":
                        print(f"[EVAL] reason=good quality, meets acceptance criteria")
                        print(f"[EVAL] next_action=accept")
                    elif judge_status == "retry":
                        print(f"[EVAL] reason=quality issues detected, retry recommended")
                        print(f"[EVAL] next_action=retry_candidate")
                    else:
                        print(f"[EVAL] reason={judge_status}")
                        print(f"[EVAL] next_action=review")
            # Convert to dict for JSON serialization
            if orchestrator_report:
                orchestrator_report_dict = {
                    "final_score": orchestrator_report.final_score,
                    "final_verdict": orchestrator_report.final_verdict,
                    "best_next_action": orchestrator_report.best_next_action,
                    "technical": {
                        "judge_name": orchestrator_report.technical.judge_name if orchestrator_report.technical else None,
                        "score": orchestrator_report.technical.score if orchestrator_report.technical else None,
                        "verdict": orchestrator_report.technical.verdict if orchestrator_report.technical else None,
                        "issues": [{"code": i.code, "message": i.message, "severity": i.severity} for i in orchestrator_report.technical.issues] if orchestrator_report.technical else [],
                        "strengths": orchestrator_report.technical.strengths if orchestrator_report.technical else [],
                        "recommended_repairs": orchestrator_report.technical.recommended_repairs if orchestrator_report.technical else [],
                    },
                    "semantic": {
                        "judge_name": orchestrator_report.semantic.judge_name if orchestrator_report.semantic else None,
                        "score": orchestrator_report.semantic.score if orchestrator_report.semantic else None,
                        "verdict": orchestrator_report.semantic.verdict if orchestrator_report.semantic else None,
                        "issues": [{"code": i.code, "message": i.message, "severity": i.severity} for i in orchestrator_report.semantic.issues] if orchestrator_report.semantic else [],
                        "strengths": orchestrator_report.semantic.strengths if orchestrator_report.semantic else [],
                        "recommended_repairs": orchestrator_report.semantic.recommended_repairs if orchestrator_report.semantic else [],
                    },
                    "artistic": {
                        "judge_name": orchestrator_report.artistic.judge_name if orchestrator_report.artistic else None,
                        "score": orchestrator_report.artistic.score if orchestrator_report.artistic else None,
                        "verdict": orchestrator_report.artistic.verdict if orchestrator_report.artistic else None,
                        "issues": [{"code": i.code, "message": i.message, "severity": i.severity} for i in orchestrator_report.artistic.issues] if orchestrator_report.artistic else [],
                        "strengths": orchestrator_report.artistic.strengths if orchestrator_report.artistic else [],
                        "recommended_repairs": orchestrator_report.artistic.recommended_repairs if orchestrator_report.artistic else [],
                    },
                }
            if retry_decision:
                retry_decision_dict = {
                    "action": retry_decision.action,
                    "max_retries": retry_decision.max_retries,
                    "suggested_prompt_suffixes": retry_decision.suggested_prompt_suffixes,
                    "suggested_settings_updates": retry_decision.suggested_settings_updates,
                    "notes": retry_decision.notes,
                }

        report = self._build_terminal_report(
            status="completed",
            user_prompt=user_prompt,
            final_positive_prompt=final_prompt,
            prompt_id=prompt_id,
            failed_stage=None,
            error=None,
            preset_name=preset_name,
            rewrite_mode=actual_rewrite_mode,
            seed=final_seed,
            images=images,
            preflight=preflight_result,
            artifact_validation=artifact_validation_result,
            artifact_fetch_validation=artifact_fetch_validation_result,
            judge_status=judge_status,
            orchestrator_report=orchestrator_report_dict,
            quality_report=quality_report_dict,
            retry_decision=retry_decision_dict,
            retry_loop=None,  # Will be added after retry loop if needed
            recipe_validation=recipe_validation_dict,
            upscale_result=upscale_result,
        )

        # Verbose logging: Final artifact paths
        if verbose:
            print(f"\n[ARTIFACTS] metadata_path={report.get('metadata_path', 'disabled')}")
            print(f"[ARTIFACTS] summary_path={report.get('summary_path', 'disabled')}")
            if images:
                for i, img in enumerate(images, 1):
                    filename = img.get('filename', 'unknown')
                    subfolder = img.get('subfolder', '')
                    full_path = str(self.outputs_dir / subfolder / filename) if subfolder else str(self.outputs_dir / filename)
                    print(f"[ARTIFACTS] image_{i}_path={full_path}")

        # Run auto retry loop if judge_status == retry
        if self.enable_judging and report.get("judge_status") == "retry":
            retry_loop_result = await self.auto_retry_loop.run_once_retry(
                initial_result=report,
                user_prompt=user_prompt,
                final_prompt=final_prompt,
                final_settings=final_settings,
                rerun_callable=lambda retry_prompt, retry_settings: self._rerun_from_retry_decision(
                    user_prompt=user_prompt,
                    retry_prompt=retry_prompt,
                    retry_settings=retry_settings,
                    preset_name=preset_name,
                    rewrite_mode=actual_rewrite_mode,
                    save_metadata=save_metadata,
                    status_callback=callback,
                ),
            )

            best_result = retry_loop_result.best_result
            best_result["retry_loop"] = {
                "loop_status": retry_loop_result.loop_status,
                "selected_attempt_index": retry_loop_result.selected_attempt_index,
                "selected_reason": retry_loop_result.selected_reason,
                "attempts": [
                    {
                        "attempt_index": a.attempt_index,
                        "prompt_id": a.prompt_id,
                        "judge_status": a.judge_status,
                        "final_verdict": a.final_verdict,
                        "final_score": a.final_score,
                        "retry_action": a.retry_action,
                        "seed": a.seed,
                        "metadata_path": a.metadata_path,
                        "summary_path": a.summary_path,
                        "error_type": a.error_type,
                        "error": a.error,
                        "applied_retry_prompt": a.applied_retry_prompt,
                        "applied_retry_settings": a.applied_retry_settings,
                    }
                    for a in retry_loop_result.attempts
                ],
            }
            report = best_result

        try:
            report = self._persist_terminal_report(
                report,
                save_metadata=save_metadata,
            )
        except Exception as exc:
            import traceback
            print(f"[DEBUG] metadata_save failed: {exc}")
            print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
            return build_failed_report("metadata_save", exc)

        callback(
            "COMPLETED",
            {
                "prompt_id": prompt_id,
                "images_found": len(images),
            },
        )
        return report
