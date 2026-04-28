"""MK-OBS1.3 — Preflight Validator for ComfyUI generation.

Validates settings before ComfyUI submit to ensure:
- prompt_pack exists and is valid
- reference locks are approved
- checkpoint matches prompt_pack/config
- seed is deterministic
- steps, sampler, scheduler match prompt_pack/config
- resolution matches project safe profile
- batch_size is within safe limits
- prompt sources are from prompt_pack.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.control.node_settings_inspector import NodeSettingsInspector


class PreflightValidator:
    """Validates ComfyUI workflow settings before submission."""

    def __init__(
        self,
        workflow: dict[str, Any],
        prompt_pack: dict[str, Any] | None,
        reference_lock_status: dict[str, Any] | None,
        config: dict[str, Any] | None,
    ) -> None:
        """
        Initialize validator with workflow and context.

        Args:
            workflow: ComfyUI workflow dictionary
            prompt_pack: Prompt pack dictionary or None
            reference_lock_status: Reference lock status dictionary or None
            config: Project config dictionary or None
        """
        self.workflow = workflow
        self.prompt_pack = prompt_pack
        self.reference_lock_status = reference_lock_status
        self.config = config or {}
        self.inspector = NodeSettingsInspector(workflow)
        self.failures: list[dict[str, Any]] = []

    def validate(self) -> dict[str, Any]:
        """
        Run all preflight validation checks.

        Returns:
            Validation report with passed/failed status
        """
        self.failures = []

        # Required checks
        self._check_prompt_pack_exists()
        self._check_reference_lock_approved()
        self._check_checkpoint_match()
        self._check_seed_deterministic()
        self._check_steps_match()
        self._check_sampler_match()
        self._check_scheduler_match()
        self._check_resolution_safe()
        self._check_batch_size_safe()
        self._check_positive_prompt_source()
        self._check_negative_prompt_source()

        passed = len(self.failures) == 0

        return {
            "passed": passed,
            "failures": self.failures,
            "total_checks": 11,
            "failed_checks": len(self.failures),
        }

    def _check_prompt_pack_exists(self) -> None:
        """Check that prompt_pack exists."""
        if self.prompt_pack is None:
            self.failures.append({
                "check": "prompt_pack_exists",
                "status": "failed",
                "reason": "prompt_pack.json not found or does not match episode/shot",
            })

    def _check_reference_lock_approved(self) -> None:
        """Check that reference lock is approved for all required characters."""
        if self.reference_lock_status is None:
            self.failures.append({
                "check": "reference_lock_approved",
                "status": "failed",
                "reason": "reference_lock status not available",
            })
            return

        if not self.reference_lock_status.get("approved", False):
            self.failures.append({
                "check": "reference_lock_approved",
                "status": "failed",
                "reason": self.reference_lock_status.get("reason", "reference lock not approved"),
            })

    def _check_checkpoint_match(self) -> None:
        """Check that checkpoint matches prompt_pack/config."""
        settings = self.inspector.inspect()
        checkpoint_data = settings.get("checkpoint_loader")
        if not checkpoint_data:
            self.failures.append({
                "check": "checkpoint_match",
                "status": "failed",
                "reason": "CheckpointLoaderSimple node not found in workflow",
            })
            return

        workflow_checkpoint = checkpoint_data.get("ckpt_name")
        if not workflow_checkpoint:
            self.failures.append({
                "check": "checkpoint_match",
                "status": "failed",
                "reason": "checkpoint name not set in workflow",
            })
            return

        # Check against prompt_pack first, then config
        expected_checkpoint = None
        if self.prompt_pack:
            expected_checkpoint = self.prompt_pack.get("checkpoint")
        if not expected_checkpoint:
            expected_checkpoint = self.config.get("checkpoint")

        if expected_checkpoint and workflow_checkpoint != expected_checkpoint:
            self.failures.append({
                "check": "checkpoint_match",
                "status": "failed",
                "reason": f"checkpoint mismatch: workflow={workflow_checkpoint}, expected={expected_checkpoint}",
            })

    def _check_seed_deterministic(self) -> None:
        """Check that seed is deterministic (not random/missing)."""
        settings = self.inspector.inspect()
        ksampler = settings.get("ksampler")
        if not ksampler:
            self.failures.append({
                "check": "seed_deterministic",
                "status": "failed",
                "reason": "KSampler node not found in workflow",
            })
            return

        seed = ksampler.get("seed")
        if seed is None or seed == 0:
            self.failures.append({
                "check": "seed_deterministic",
                "status": "failed",
                "reason": f"seed is not deterministic: {seed}",
            })

    def _check_steps_match(self) -> None:
        """Check that steps match prompt_pack/config."""
        settings = self.inspector.inspect()
        ksampler = settings.get("ksampler")
        if not ksampler:
            self.failures.append({
                "check": "steps_match",
                "status": "failed",
                "reason": "KSampler node not found in workflow",
            })
            return

        workflow_steps = ksampler.get("steps")
        if workflow_steps is None:
            self.failures.append({
                "check": "steps_match",
                "status": "failed",
                "reason": "steps not set in workflow",
            })
            return

        # Check against prompt_pack first, then config
        expected_steps = None
        if self.prompt_pack and self.prompt_pack.get("beats"):
            # Use first beat's steps
            first_beat = self.prompt_pack["beats"][0] if self.prompt_pack["beats"] else None
            if first_beat:
                expected_steps = first_beat.get("steps")
        if expected_steps is None:
            expected_steps = self.config.get("steps")

        if expected_steps is not None and workflow_steps != expected_steps:
            self.failures.append({
                "check": "steps_match",
                "status": "failed",
                "reason": f"steps mismatch: workflow={workflow_steps}, expected={expected_steps}",
            })

    def _check_sampler_match(self) -> None:
        """Check that sampler matches prompt_pack/config."""
        settings = self.inspector.inspect()
        ksampler = settings.get("ksampler")
        if not ksampler:
            self.failures.append({
                "check": "sampler_match",
                "status": "failed",
                "reason": "KSampler node not found in workflow",
            })
            return

        workflow_sampler = ksampler.get("sampler_name")
        if not workflow_sampler:
            self.failures.append({
                "check": "sampler_match",
                "status": "failed",
                "reason": "sampler_name not set in workflow",
            })
            return

        # Check against prompt_pack first
        expected_sampler = None
        if self.prompt_pack and self.prompt_pack.get("beats"):
            first_beat = self.prompt_pack["beats"][0] if self.prompt_pack["beats"] else None
            if first_beat:
                expected_sampler = first_beat.get("sampler")

        if expected_sampler and workflow_sampler != expected_sampler:
            self.failures.append({
                "check": "sampler_match",
                "status": "failed",
                "reason": f"sampler mismatch: workflow={workflow_sampler}, expected={expected_sampler}",
            })

    def _check_scheduler_match(self) -> None:
        """Check that scheduler matches prompt_pack/config."""
        settings = self.inspector.inspect()
        ksampler = settings.get("ksampler")
        if not ksampler:
            self.failures.append({
                "check": "scheduler_match",
                "status": "failed",
                "reason": "KSampler node not found in workflow",
            })
            return

        workflow_scheduler = ksampler.get("scheduler")
        if not workflow_scheduler:
            self.failures.append({
                "check": "scheduler_match",
                "status": "failed",
                "reason": "scheduler not set in workflow",
            })
            return

        # Check against prompt_pack first
        expected_scheduler = None
        if self.prompt_pack and self.prompt_pack.get("beats"):
            first_beat = self.prompt_pack["beats"][0] if self.prompt_pack["beats"] else None
            if first_beat:
                expected_scheduler = first_beat.get("scheduler")

        if expected_scheduler and workflow_scheduler != expected_scheduler:
            self.failures.append({
                "check": "scheduler_match",
                "status": "failed",
                "reason": f"scheduler mismatch: workflow={workflow_scheduler}, expected={expected_scheduler}",
            })

    def _check_resolution_safe(self) -> None:
        """Check that resolution matches project safe profile."""
        settings = self.inspector.inspect()
        latent = settings.get("empty_latent")
        if not latent:
            self.failures.append({
                "check": "resolution_safe",
                "status": "failed",
                "reason": "EmptyLatentImage node not found in workflow",
            })
            return

        width = latent.get("width")
        height = latent.get("height")

        if not width or not height:
            self.failures.append({
                "check": "resolution_safe",
                "status": "failed",
                "reason": f"resolution not set: width={width}, height={height}",
            })
            return

        # Safe resolution limits (adjust as needed)
        max_resolution = 2048
        if width > max_resolution or height > max_resolution:
            self.failures.append({
                "check": "resolution_safe",
                "status": "failed",
                "reason": f"resolution exceeds safe limit: {width}x{height} > {max_resolution}",
            })

    def _check_batch_size_safe(self) -> None:
        """Check that batch_size <= configured safe batch."""
        settings = self.inspector.inspect()
        latent = settings.get("empty_latent")
        if not latent:
            self.failures.append({
                "check": "batch_size_safe",
                "status": "failed",
                "reason": "EmptyLatentImage node not found in workflow",
            })
            return

        batch_size = latent.get("batch_size", 1)
        safe_batch = self.config.get("max_frames_per_batch", 3)

        if batch_size > safe_batch:
            self.failures.append({
                "check": "batch_size_safe",
                "status": "failed",
                "reason": f"batch_size exceeds safe limit: {batch_size} > {safe_batch}",
            })

    def _check_positive_prompt_source(self) -> None:
        """Check that positive prompt source is prompt_pack.json."""
        settings = self.inspector.inspect()
        positive = settings.get("positive_prompt")
        if not positive:
            self.failures.append({
                "check": "positive_prompt_source",
                "status": "failed",
                "reason": "positive prompt node not found in workflow",
            })
            return

        source = positive.get("source", "")
        if source != "prompt_pack.json":
            self.failures.append({
                "check": "positive_prompt_source",
                "status": "failed",
                "reason": f"positive prompt source is not prompt_pack.json: {source}",
            })

    def _check_negative_prompt_source(self) -> None:
        """Check that negative prompt source is prompt_pack.json."""
        settings = self.inspector.inspect()
        negative = settings.get("negative_prompt")
        if not negative:
            self.failures.append({
                "check": "negative_prompt_source",
                "status": "failed",
                "reason": "negative prompt node not found in workflow",
            })
            return

        source = negative.get("source", "")
        if source != "prompt_pack.json":
            self.failures.append({
                "check": "negative_prompt_source",
                "status": "failed",
                "reason": f"negative prompt source is not prompt_pack.json: {source}",
            })


def validate_preflight(
    workflow: dict[str, Any],
    prompt_pack: dict[str, Any] | None = None,
    reference_lock_status: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Convenience function to run preflight validation.

    Args:
        workflow: ComfyUI workflow dictionary
        prompt_pack: Prompt pack dictionary or None
        reference_lock_status: Reference lock status dictionary or None
        config: Project config dictionary or None

    Returns:
        Validation report
    """
    validator = PreflightValidator(workflow, prompt_pack, reference_lock_status, config)
    return validator.validate()


if __name__ == "__main__":
    # CLI for testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.control.preflight_validator <workflow.json>")
        sys.exit(1)

    workflow_path = sys.argv[1]
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    result = validate_preflight(workflow)
    print(json.dumps(result, indent=2))
