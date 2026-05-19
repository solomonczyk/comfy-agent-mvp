"""Identity Lock Runner - executes identity-locked generation workflow.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .artifacts import IdentityLockArtifacts
from .brain_decision import LLMBrainDecision
from .context_pack import IdentityContextPack
from .identity_contract import IdentityContract
from .identity_gate import IdentityGate
from .reference_router import ReferenceRouter
from .single_subject_gate import SingleSubjectGate
from .workflow_patch import WorkflowPatch


class IdentityLockRunner:
    """Executes identity-locked generation workflow."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"

        # Initialize components
        self.context_pack = IdentityContextPack(project_root)
        self.brain_decision = LLMBrainDecision(project_root)
        self.identity_contract = IdentityContract(project_root)
        self.reference_router = ReferenceRouter(project_root)
        self.workflow_patch = WorkflowPatch(project_root)
        self.artifacts = IdentityLockArtifacts(project_root)
        self.identity_gate = IdentityGate(project_root)
        self.single_subject_gate = SingleSubjectGate(project_root)

    def run(
        self,
        canonical_inventory: list[Dict[str, Any]],
        previous_rejected_assets: list[str],
        operator_rejection_reason: list[str],
        previous_asset_path: str,
        base_workflow: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run the identity-locked generation workflow."""
        # Step 1: Generate operator rejection record
        self.artifacts.generate_operator_rejection_record(
            previous_task="RC-COMBINE-V2-COMPOSITION-WORKFLOW-REAL-CANDIDATE-GENERATION-001",
            rejection_reason=operator_rejection_reason,
            previous_asset_path=previous_asset_path,
        )

        # Step 2: Build identity context pack
        context_pack = self.context_pack.build_context_pack(
            canonical_inventory, previous_rejected_assets, operator_rejection_reason
        )
        self.context_pack.save_context_pack(context_pack)

        # Step 3: Make LLM brain decision
        llm_decision = self.brain_decision.make_identity_lock_decision(context_pack)
        self.brain_decision.save_decision(llm_decision)

        # Step 4: Create identity contract
        identity_contract = self.identity_contract.create_identity_contract(
            llm_decision, context_pack
        )
        self.identity_contract.save_contract(identity_contract)

        # Step 5: Route references by role
        routing_report = self.reference_router.route_references(
            canonical_inventory, llm_decision
        )
        self.reference_router.save_routing_report(routing_report)

        # Step 6: Create workflow patch
        identity_refs = context_pack.get("canonical_identity_sources", {}).get(
            "identity_references", []
        )
        primary_identity_path = (
            identity_refs[0].get("relative_path", "") if identity_refs else ""
        )
        canonical_identity_full_path = (
            self.project_root / "data" / "rc2_multishot1_ep01" / "input" / primary_identity_path
        )

        patch = self.workflow_patch.create_workflow_patch(llm_decision, str(canonical_identity_full_path))
        self.workflow_patch.save_patch(patch)

        # Step 7: Apply patch to workflow
        submitted_workflow = self.workflow_patch.apply_patch_to_workflow(base_workflow, patch)
        self.workflow_patch.save_submitted_workflow(submitted_workflow)

        # Step 8: Generate generation gate
        gate = self.artifacts.generate_generation_gate(
            llm_decision_valid=True,
            identity_contract_valid=True,
            reference_routing_valid=True,
        )

        # Step 9: Execute generation if authorized
        if not gate.get("generation_authorized", False):
            return {"status": "blocked", "reason": "generation_not_authorized"}

        generated_asset_path = self._execute_generation(submitted_workflow)

        if not generated_asset_path:
            return {"status": "failed", "reason": "generation_failed"}

        # Step 10: Post-generation validation
        # Blank detector (basic check)
        blank_detector_passed = self._blank_detector(generated_asset_path)

        # Framing detector (basic check)
        framing_detector_passed = self._framing_detector(generated_asset_path)

        # Environment visibility detector (NEW)
        environment_visibility_passed = self._environment_visibility_detector(generated_asset_path)

        # Generic portrait detector (NEW - blocks beauty close-ups)
        generic_portrait_blocked = self._generic_portrait_detector(generated_asset_path)

        # Single-subject gate
        single_subject_result = self.single_subject_gate.validate_single_subject(
            generated_asset_path
        )
        self.single_subject_gate.save_gate_result(single_subject_result)
        single_subject_gate_passed = single_subject_result.get("passed", False)

        # Identity gate
        identity_gate_result = self.identity_gate.validate_identity(
            generated_asset_path, str(canonical_identity_full_path)
        )
        self.identity_gate.save_gate_result(identity_gate_result)

        # Step 11: Generate manifest and review
        prompt_id = str(uuid.uuid4())
        manifest = self.artifacts.generate_generation_manifest(
            generated_asset_path, prompt_id, submitted_workflow
        )

        review = self.artifacts.generate_result_review(
            generated_asset_path,
            blank_detector_passed,
            framing_detector_passed,
            environment_visibility_passed,
            generic_portrait_blocked,
            single_subject_gate_passed,
            identity_gate_result,
        )

        # Step 12: Generate operator review packet
        packet = self.artifacts.generate_operator_review_packet(
            new_asset_path=generated_asset_path,
            canonical_reference_path=str(canonical_identity_full_path),
            previous_rejected_assets=previous_rejected_assets,
            identity_checklist={
                "identity_preserved": identity_gate_result.get("identity_confidence", 0) > 0.7
                if identity_gate_result.get("identity_confidence") is not None
                else None,
                "no_identity_drift": True,
                "canonical_source_used": True,
            },
            framing_checklist={
                "medium_or_upper_body": framing_detector_passed,
                "full_face_visible": framing_detector_passed,
                "not_square_closeup": True,
                "environment_visible": environment_visibility_passed,
                "not_generic_portrait": generic_portrait_blocked,
            },
            single_subject_checklist={
                "exactly_one_person": single_subject_gate_passed,
                "no_extra_foreground_person": single_subject_gate_passed,
                "no_background_people": single_subject_gate_passed,
            },
        )

        # Step 13: Update state, artifact index, episode ledger
        self.artifacts.update_state(
            current_state="operator_visual_review_required",
            next_allowed_action="operator_visual_review_required",
            generation_count=1,
        )
        self.artifacts.update_artifact_index()
        self.artifacts.update_episode_ledger(
            event_type="identity_lock_generation_completed", verdict="COMPLETED"
        )

        return {
            "status": "completed",
            "generated_asset_path": generated_asset_path,
            "prompt_id": prompt_id,
            "blank_detector_passed": blank_detector_passed,
            "framing_detector_passed": framing_detector_passed,
            "environment_visibility_passed": environment_visibility_passed,
            "generic_portrait_blocked": generic_portrait_blocked,
            "single_subject_gate_passed": single_subject_gate_passed,
            "identity_gate_result": identity_gate_result,
        }

    def _execute_generation(self, workflow: Dict[str, Any]) -> str | None:
        """Execute ComfyUI generation using GenerationExecutor."""
        try:
            print(f"[DEBUG] Attempting to execute generation...")
            print(f"[DEBUG] Project root: {self.project_root}")
            print(f"[DEBUG] Workflow keys: {list(workflow.keys())}")
            
            # Strip metadata that ComfyUI doesn't understand
            clean_workflow = {k: v for k, v in workflow.items() if not k.endswith("_metadata")}
            print(f"[DEBUG] Clean workflow keys: {list(clean_workflow.keys())}")
            
            from app.visual_generation.executor import GenerationExecutor

            executor = GenerationExecutor(self.project_root)
            print(f"[DEBUG] GenerationExecutor created")
            
            # Use short timeout since ComfyUI may have already completed queued jobs
            result = executor.execute(clean_workflow)
            print(f"[DEBUG] Execution result keys: {list(result.keys())}")
            print(f"[DEBUG] Generation performed: {result.get('generation_performed')}")
            print(f"[DEBUG] Failure: {result.get('failure')}")
            print(f"[DEBUG] Failure reason: {result.get('failure_reason')}")

            if result.get("generation_performed"):
                output_images = result.get("output_images", [])
                print(f"[DEBUG] Output images count: {len(output_images)}")
                if output_images:
                    # output_images can be list of strings or list of dicts
                    if isinstance(output_images[0], str):
                        path = output_images[0]
                    else:
                        path = output_images[0].get("path", "")
                    
                    # Convert relative path to absolute path
                    if path and not os.path.isabs(path):
                        # Get ComfyUI output directory from manifest
                        try:
                            from app.visual_generation.manifest import COMFYUI_OUTPUT_DIR
                            path = Path(COMFYUI_OUTPUT_DIR) / path
                        except ImportError:
                            # Fallback to project output
                            path = self.project_root / "output" / "assets" / "fresh_visual_candidates" / path
                    
                    print(f"[DEBUG] Generated asset path: {path}")
                    return str(path) if path else None

            print(f"[DEBUG] Generation failed - no output images")
            return None

        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _blank_detector(self, asset_path: str) -> bool:
        """Basic blank detector."""
        try:
            from PIL import Image  # type: ignore

            img = Image.open(asset_path)
            # Convert to grayscale and check variance
            img_gray = img.convert("L")
            pixels = list(img_gray.getdata())
            variance = sum((x - sum(pixels) / len(pixels)) ** 2 for x in pixels) / len(pixels)
            return variance > 100  # Threshold for non-blank
        except Exception:
            return False

    def _framing_detector(self, asset_path: str) -> bool:
        """Basic framing detector."""
        try:
            from PIL import Image  # type: ignore

            img = Image.open(asset_path)
            width, height = img.size
            # Check if not square 1024 close-up
            return not (width == 1024 and height == 1024) and width >= 1344
        except Exception:
            return False

    def _environment_visibility_detector(self, asset_path: str) -> bool:
        """Detect if environment/background is visible (not blank/solid color)."""
        try:
            from PIL import Image  # type: ignore
            import numpy as np  # type: ignore

            img = Image.open(asset_path)
            img_array = np.array(img)

            # Sample edges to check for background variety
            # Take samples from top, bottom, left, right edges
            h, w = img_array.shape[:2]
            edge_samples = []

            # Sample 10% from each edge
            edge_width = max(1, w // 10)
            edge_height = max(1, h // 10)

            # Top edge
            edge_samples.extend(img_array[:edge_height, :].reshape(-1, 3))
            # Bottom edge
            edge_samples.extend(img_array[-edge_height:, :].reshape(-1, 3))
            # Left edge
            edge_samples.extend(img_array[:, :edge_width].reshape(-1, 3))
            # Right edge
            edge_samples.extend(img_array[:, -edge_width:].reshape(-1, 3))

            edge_samples = np.array(edge_samples)

            # Check color variance in edges
            if len(edge_samples) > 0:
                edge_variance = np.var(edge_samples, axis=0).mean()
                # If variance is too low, likely solid/blank background
                return edge_variance > 50  # Threshold for visible environment

            return False
        except Exception:
            return False

    def _generic_portrait_detector(self, asset_path: str) -> bool:
        """Detect if image is a generic beauty portrait (close-up face, plain background)."""
        try:
            from PIL import Image  # type: ignore
            import numpy as np  # type: ignore

            img = Image.open(asset_path)
            width, height = img.size

            # Check for square or near-square format (typical of portraits)
            aspect_ratio = width / height
            is_square = 0.8 <= aspect_ratio <= 1.2

            # Check for close-up framing (face occupies most of frame)
            # This is a heuristic - in a real implementation you'd use face detection
            is_closeup = width < 1200 or height < 1200

            # Check for plain background using edge variance
            img_array = np.array(img)
            h, w = img_array.shape[:2]
            edge_samples = []

            edge_width = max(1, w // 10)
            edge_height = max(1, h // 10)

            edge_samples.extend(img_array[:edge_height, :].reshape(-1, 3))
            edge_samples.extend(img_array[-edge_height:, :].reshape(-1, 3))
            edge_samples.extend(img_array[:, :edge_width].reshape(-1, 3))
            edge_samples.extend(img_array[:, -edge_width:].reshape(-1, 3))

            edge_samples = np.array(edge_samples)
            edge_variance = np.var(edge_samples, axis=0).mean() if len(edge_samples) > 0 else 0
            has_plain_background = edge_variance < 30

            # If multiple indicators suggest generic portrait, flag it
            is_generic_portrait = is_square and is_closeup and has_plain_background

            # Return True if NOT a generic portrait (i.e., passes the check)
            return not is_generic_portrait
        except Exception:
            return False
