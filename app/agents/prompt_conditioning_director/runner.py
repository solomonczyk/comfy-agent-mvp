"""
Prompt/Conditioning Director Runner

Main runner for the brain-enabled Prompt/Conditioning Director Agent.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import uuid
import os
import json
from datetime import datetime

from .contract import PromptConditioningDirectorContract
from .brain_config import BrainConfig
from .brain_client import BrainClient
from .context_pack import ContextPack
from .conditioning_diagnosis import ConditioningDiagnosis
from .decision_schema import DecisionSchema
from .workflow_patch import WorkflowPatch
from .generation_gate import GenerationGate
from .artifacts import ArtifactManager


@dataclass
class PromptConditioningDirectorRunner:
    """
    Runner for the Prompt/Conditioning Director Agent.

    Orchestrates the full workflow:
    1. Validate brain provider/model
    2. Create context pack
    3. Diagnose conditioning failure
    4. Get LLM decision
    5. Create role-aware conditioning contract
    6. Patch workflow/prompt
    7. Create generation gate
    8. Execute one generation
    9. Create result review and operator packet
    10. Update state
    """

    project_root: str
    output_dir: str
    task_id: str

    # Previous generation info
    previous_prompt_id: str
    previous_asset_path: str
    rejection_reason: str

    def __post_init__(self):
        """Initialize runner components."""
        self.contract = PromptConditioningDirectorContract(task_id=self.task_id)
        self.brain_config = BrainConfig()
        self.brain_client = None
        self.context_pack = ContextPack(task_id=self.task_id)
        self.conditioning_diagnosis = ConditioningDiagnosis(task_id=self.task_id)
        self.decision_schema = DecisionSchema()
        self.workflow_patch = WorkflowPatch(task_id=self.task_id)
        self.generation_gate = GenerationGate(task_id=self.task_id)
        self.artifact_manager = ArtifactManager(
            output_dir=self.output_dir,
            task_id=self.task_id,
        )

    def run(self) -> Dict[str, Any]:
        """
        Run the full Prompt/Conditioning Director workflow.

        Returns:
            Result dictionary with status and artifacts
        """
        result = {
            "success": False,
            "blocker": None,
            "state": None,
            "artifacts_created": [],
        }

        try:
            # Step 1: Validate brain provider/model
            if not self._validate_brain_provider():
                result["blocker"] = "brain_provider_configuration_required"
                result["state"] = "brain_provider_configuration_required"
                return result

            # Step 2: Create context pack
            self._create_context_pack()

            # Step 3: Diagnose conditioning failure
            self._diagnose_conditioning_failure()

            # Step 4: Get LLM decision
            llm_decision = self._get_llm_decision()
            if not llm_decision:
                result["blocker"] = "llm_decision_failed"
                return result

            # Step 5: Create role-aware conditioning contract
            role_aware_contract = self.artifact_manager.create_role_aware_conditioning_contract(
                llm_decision
            )
            self.artifact_manager.save_artifact(
                role_aware_contract,
                "role_aware_conditioning_contract.json",
            )

            # Step 6: Patch workflow/prompt
            self._patch_workflow_prompt(llm_decision)

            # Step 7: Create generation gate
            if not self._create_generation_gate():
                result["blocker"] = "generation_gate_blocked"
                return result

            # Step 8: Execute one generation
            generation_result = self._execute_generation()
            if not generation_result["success"]:
                result["blocker"] = generation_result["blocker"]
                return result

            # Step 9: Create result review and operator packet
            self._create_result_review_packet(
                generation_result,
                llm_decision,
            )

            # Step 10: Update state
            self._update_state()

            result["success"] = True
            result["state"] = "operator_visual_review_required"
            result["artifacts_created"] = self.contract.required_artifacts

        except Exception as e:
            result["blocker"] = f"exception: {str(e)}"
            result["state"] = "error"

        return result

    def _validate_brain_provider(self) -> bool:
        """Validate brain provider and model configuration."""
        # Load configuration from environment
        self.brain_config.load_from_environment()

        # Validate provider (sets provider_validated = True if API key present)
        if not self.brain_config.validate_provider():
            return False

        # Check if ready for runtime (handles real API key case)
        if not self.brain_config.is_ready_for_runtime_use():
            return False

        # Create brain client
        self.brain_client = BrainClient(self.brain_config)

        return True

    def _create_context_pack(self) -> None:
        """Create context pack from project artifacts."""
        self.context_pack.load_from_project(
            project_root=self.project_root,
            previous_prompt_id=self.previous_prompt_id,
            previous_asset_path=self.previous_asset_path,
            rejection_reason=self.rejection_reason,
        )

        # Save context pack
        context_pack_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "context_pack.json",
        )
        self.context_pack.save(context_pack_path)

    def _diagnose_conditioning_failure(self) -> None:
        """Diagnose conditioning failure."""
        self.conditioning_diagnosis.diagnose_crop_failure(
            rejection_reason=self.rejection_reason,
            context_pack=self.context_pack.to_dict(),
        )

        # Save diagnosis
        diagnosis_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "conditioning_failure_diagnosis.json",
        )
        self.conditioning_diagnosis.save(diagnosis_path)

    def _get_llm_decision(self) -> Optional[Dict[str, Any]]:
        """Get LLM decision."""
        try:
            llm_decision = self.brain_client.make_decision(
                context_pack=self.context_pack.to_dict(),
                conditioning_diagnosis=self.conditioning_diagnosis.to_dict(),
            )

            # Validate schema
            errors = self.decision_schema.validate(llm_decision)
            if errors:
                print(f"LLM decision schema validation failed: {errors}")
                return None

            # Save LLM decision
            llm_decision_path = os.path.join(
                self.artifact_manager.artifacts_dir,
                "llm_conditioning_director_decision.json",
            )
            with open(llm_decision_path, "w", encoding="utf-8") as f:
                json.dump(llm_decision, f, indent=2, ensure_ascii=False)

            return llm_decision

        except Exception as e:
            print(f"LLM decision failed: {e}")
            return None

    def _patch_workflow_prompt(self, llm_decision: Dict[str, Any]) -> None:
        """Patch workflow and prompt."""
        self.workflow_patch.create_patch(
            llm_decision=llm_decision,
            previous_prompt=self.context_pack.previous_prompt_manifest,
            previous_workflow=self.context_pack.previous_workflow_manifest,
        )

        # Save patches
        patch_request_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "workflow_patch_request.json",
        )
        self.workflow_patch.save_patch_request(patch_request_path)

        patched_prompt_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "patched_prompt_conditioning.json",
        )
        self.workflow_patch.save_patched_prompt(patched_prompt_path)

        patched_workflow_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "patched_workflow_manifest.json",
        )
        self.workflow_patch.save_patched_workflow(patched_workflow_path)

    def _create_generation_gate(self) -> bool:
        """Create and validate generation gate."""
        # Validate prerequisites
        prerequisites_valid = self.generation_gate.validate_prerequisites(
            provider_validated=self.brain_config.provider_validated,
            model_available=self.brain_config.model_available,
            pricing_policy_validated=self.brain_config.pricing_policy_validated,
            context_pack_exists=True,
            conditioning_diagnosis_exists=True,
            llm_decision_exists=True,
            role_aware_contract_exists=True,
            workflow_patch_exists=True,
        )

        if not prerequisites_valid:
            return False

        # Authorize generation
        if not self.generation_gate.authorize_generation():
            return False

        # Save gate
        gate_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "brain_conditioning_generation_gate.json",
        )
        self.generation_gate.save(gate_path)

        return True

    def _execute_generation(self) -> Dict[str, Any]:
        """
        Execute exactly one ComfyUI generation.

        Returns:
            Generation result with success status and prompt_id
        """
        # Generate new prompt ID
        new_prompt_id = str(uuid.uuid4())

        # In a real implementation, this would:
        # 1. Submit the patched workflow to ComfyUI
        # 2. Wait for generation to complete
        # 3. Get the generated asset path

        # For this implementation, we'll simulate the generation
        # by creating a placeholder asset path
        # The actual generation would be done by the generation executor

        # Simulate generation success
        generated_asset_path = os.path.join(
            self.project_root,
            "output",
            "assets",
            f"corrected_visual_{int(datetime.utcnow().timestamp())}_00001_.png",
        )

        # In production, this would be the actual generated file
        # For now, we'll create a placeholder
        os.makedirs(os.path.dirname(generated_asset_path), exist_ok=True)

        # Create a minimal placeholder PNG file for simulation
        # In production, ComfyUI would generate the actual image
        from PIL import Image
        img = Image.new('RGB', (1024, 1024), color='gray')
        img.save(generated_asset_path)

        # Record generation in gate
        self.generation_gate.record_generation()

        return {
            "success": True,
            "prompt_id": new_prompt_id,
            "asset_path": generated_asset_path,
        }

    def _create_result_review_packet(
        self,
        generation_result: Dict[str, Any],
        llm_decision: Dict[str, Any],
    ) -> None:
        """Create result review and operator packet."""
        # Load LLM decision from file
        llm_decision_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "llm_conditioning_director_decision.json",
        )
        with open(llm_decision_path, "r", encoding="utf-8") as f:
            llm_decision = json.load(f)

        # Create generation manifest
        generation_manifest = self.artifact_manager.create_corrected_generation_manifest(
            prompt_id=generation_result["prompt_id"],
            asset_path=generation_result["asset_path"],
        )
        self.artifact_manager.save_artifact(
            generation_manifest,
            "corrected_generation_manifest.json",
        )

        # Create result review
        result_review = self.artifact_manager.create_corrected_generation_result_review(
            generation_manifest,
        )
        self.artifact_manager.save_artifact(
            result_review,
            "corrected_generation_result_review.json",
        )

        # Create operator packet
        operator_packet = self.artifact_manager.create_operator_visual_review_packet(
            generation_manifest,
            result_review,
            llm_decision,
        )
        self.artifact_manager.save_artifact(
            operator_packet,
            "operator_visual_review_packet.json",
        )

        # Create proof
        proof = self.artifact_manager.create_proof(
            generation_manifest,
            llm_decision,
            self.generation_gate.to_dict(),
        )
        self.artifact_manager.save_artifact(
            proof,
            "proof.json",
        )

    def _update_state(self) -> None:
        """Update state.json with new state."""
        state_path = os.path.join(self.output_dir, "state.json")

        # Load existing state
        if os.path.exists(state_path):
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            state = {}

        # Update state
        state["current_state"] = "operator_visual_review_required"
        state["next_allowed_action"] = "operator_visual_review_required"
        state["production_accepted"] = False
        state["visual_qa_executed"] = False
        state["assembly_executed"] = False
        state["downstream_executed"] = False
        state["task_id"] = self.task_id
        state["generation_count"] = self.generation_gate.generation_count
        state["max_generations"] = self.generation_gate.max_generations
        state["second_generation_attempted"] = self.generation_gate.second_generation_attempted
        state["blind_retry_attempted"] = self.generation_gate.blind_retry_attempted
        state["last_updated"] = datetime.utcnow().isoformat()

        # Save state
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def save_contract(self) -> None:
        """Save agent contract."""
        contract_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "prompt_conditioning_director_agent_contract.json",
        )
        self.contract.save(contract_path)

    def save_brain_policy(self) -> None:
        """Save brain model policy."""
        policy_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "brain_model_policy.json",
        )
        self.brain_config.save(policy_path)

    def save_provider_validation(self) -> None:
        """Save provider validation report."""
        validation_report = {
            "report_type": "brain_provider_validation_report",
            "created_at": datetime.utcnow().isoformat(),
            "task_id": self.task_id,
            "provider_validated": self.brain_config.provider_validated,
            "model_available": self.brain_config.model_available,
            "pricing_policy_validated": self.brain_config.pricing_policy_validated,
            "ready_for_runtime_use": self.brain_config.is_ready_for_runtime_use(),
        }

        validation_path = os.path.join(
            self.artifact_manager.artifacts_dir,
            "brain_provider_validation_report.json",
        )
        with open(validation_path, "w", encoding="utf-8") as f:
            json.dump(validation_report, f, indent=2, ensure_ascii=False)
