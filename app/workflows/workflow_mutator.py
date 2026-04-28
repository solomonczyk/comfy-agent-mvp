"""Workflow mutator for task-specific workflow adaptation.

This module provides the WorkflowMutator class that adapts workflow templates
to specific tasks by applying mutations based on execution plans and task-specific overrides.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.agent.execution_plan import ExecutionPlan
from app.workflows.node_contracts import (
    SDXL_CONTRACTS,
    get_all_contracts,
    get_contract,
    get_mutable_node_ids,
)
from app.workflows.workflow_types import TaskType


class MutationError(Exception):
    """Exception raised when workflow mutation fails."""
    
    def __init__(self, message: str, workflow_id: str, node_id: str | None = None):
        self.message = message
        self.workflow_id = workflow_id
        self.node_id = node_id
        super().__init__(self.message)


@dataclass
class MutationResult:
    """Result of workflow mutation."""
    workflow_id: str
    mutated_workflow: dict[str, Any]
    mutated_nodes: list[str]
    applied_changes: dict[str, Any]
    notes: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "workflow_id": self.workflow_id,
            "mutated_nodes": self.mutated_nodes,
            "applied_changes": self.applied_changes,
            "notes": self.notes,
        }


# Task-specific overrides
TASK_OVERRIDES = {
    TaskType.PORTRAIT_TXT2IMG: {
        "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, smooth skin texture, doll-like, anime, cartoon, oversaturated, harsh lighting",
        "width": 1024,
        "height": 1024,
        "steps": 30,
        "cfg": 6.0,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "filename_prefix": "agent/portrait",
    },
    TaskType.CINEMATIC_TXT2IMG: {
        "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, oversaturated, flat lighting, amateur, snapshot",
        "width": 1344,
        "height": 768,
        "steps": 30,
        "cfg": 6.5,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "filename_prefix": "agent/cinematic",
    },
    TaskType.PRODUCT_TXT2IMG: {
        "negative_prompt": "blurry, low quality, bad anatomy, deformed, distorted, oversaturated, harsh shadows, poor lighting, messy background",
        "width": 1024,
        "height": 1024,
        "steps": 25,
        "cfg": 7.0,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "filename_prefix": "agent/product",
    },
    TaskType.FASHION_TXT2IMG: {
        "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, doll-like, anime, cartoon, oversaturated, harsh lighting, poor composition, cluttered",
        "width": 1024,
        "height": 1536,
        "steps": 35,
        "cfg": 6.5,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "filename_prefix": "agent/fashion",
    },
    TaskType.IMG2IMG: {
        "negative_prompt": "blurry, low quality, distorted, oversaturated, artifacts",
        "steps": 30,
        "cfg": 6.0,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "denoise": 0.6,
        "filename_prefix": "agent/img2img",
    },
    TaskType.UPSCALE: {
        "negative_prompt": "blurry, low quality, pixelated, artifacts, noise, oversaturated",
        "steps": 30,
        "cfg": 6.0,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "denoise": 0.35,
        "upscale_width": 2048,
        "upscale_height": 2048,
        "upscale_method": "nearest-exact",
        "filename_prefix": "agent/upscale",
    },
    TaskType.INPAINT_FACE: {
        "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, doll-like",
        "steps": 30,
        "cfg": 6.0,
        "sampler_name": "dpmpp_2m",
        "scheduler": "karras",
        "denoise": 0.75,
        "filename_prefix": "agent/inpaint_face",
    },
}


class WorkflowMutator:
    """Mutator for adapting workflow templates to specific tasks."""
    
    def __init__(self, contracts: dict[str, Any] | None = None, verbose: bool = False):
        """Initialize workflow mutator.
        
        Args:
            contracts: Dictionary of node contracts. Defaults to SDXL_CONTRACTS.
            verbose: Enable node-level mutation logging for debugging.
        """
        self.contracts = contracts or SDXL_CONTRACTS
        self.workflow_contracts = {}  # Cache for workflow-specific contracts
        self.verbose = verbose
    
    def load_template(self, workflow_path: str | Path) -> dict[str, Any]:
        """Load workflow template from JSON file.
        
        Args:
            workflow_path: Path to workflow JSON file
            
        Returns:
            Workflow dictionary
            
        Raises:
            MutationError: If workflow file not found or invalid JSON
        """
        path = Path(workflow_path)
        if not path.exists():
            raise MutationError(
                f"Workflow file not found: {workflow_path}",
                workflow_id=str(path),
            )
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                workflow = json.load(f)
        except json.JSONDecodeError as e:
            raise MutationError(
                f"Invalid JSON in workflow file: {e}",
                workflow_id=str(path),
            ) from e
        
        return workflow
    
    def validate_contracts(self, workflow: dict[str, Any], workflow_id: str) -> list[str]:
        """Validate that workflow nodes match their contracts.
        
        Args:
            workflow: Workflow dictionary
            workflow_id: Workflow identifier for error reporting
            
        Returns:
            List of validated node IDs
            
        Raises:
            MutationError: If any node fails contract validation
        """
        # Get workflow-specific contracts from node_contracts module
        from app.workflows.node_contracts import get_all_contracts
        contracts = get_all_contracts(workflow_id)
        
        validated_nodes = []
        
        for node_id, contract in contracts.items():
            if node_id not in workflow:
                raise MutationError(
                    f"Required mutable node '{node_id}' not found in workflow",
                    workflow_id=workflow_id,
                    node_id=node_id,
                )
            
            node_data = workflow[node_id]
            is_valid, error_msg = contract.validate_node(node_data)
            
            if not is_valid:
                raise MutationError(
                    f"Contract validation failed for node '{node_id}': {error_msg}",
                    workflow_id=workflow_id,
                    node_id=node_id,
                )
            
            validated_nodes.append(node_id)
        
        return validated_nodes
    
    def apply_plan(
        self,
        workflow: dict[str, Any],
        execution_plan: ExecutionPlan,
        overrides: dict[str, Any] | None = None,
    ) -> MutationResult:
        """Apply execution plan and overrides to workflow.
        
        Args:
            workflow: Workflow dictionary
            execution_plan: Execution plan with task and inputs
            overrides: Additional overrides to apply (merged with task-specific)
            
        Returns:
            MutationResult with mutated workflow and changes
            
        Raises:
            MutationError: If mutation fails
        """
        # Validate contracts first
        self.validate_contracts(workflow, execution_plan.workflow_id)
        
        # Get task-specific overrides
        task_overrides = TASK_OVERRIDES.get(execution_plan.task_type, {}).copy()
        
        # Build final overrides with precedence: canonical_recipe > resolved_inputs > overrides > task_overrides
        final_overrides = task_overrides.copy()
        
        # Apply provided overrides
        if overrides:
            final_overrides.update(overrides)
        
        # Apply resolved inputs
        resolved_inputs = execution_plan.resolved_inputs or {}
        for key, value in resolved_inputs.items():
            if value is not None:
                final_overrides[key] = value
        
        # Apply canonical recipe (highest precedence - wins over all defaults)
        canonical_recipe = execution_plan.canonical_recipe or {}
        for key, value in canonical_recipe.items():
            if value is not None:
                final_overrides[key] = value
        
        # Debug: Log canonical recipe application
        if canonical_recipe:
            import sys
            print(f"[DEBUG] Canonical recipe applied to final_overrides:")
            for field in ["sampler_name", "scheduler", "steps", "cfg", "width", "height", "seed"]:
                if field in canonical_recipe:
                    print(f"[DEBUG]   {field}: requested={canonical_recipe[field]}, final={final_overrides.get(field)}")
        
        # Fail-fast validation: check if canonical recipe was applied correctly
        if canonical_recipe:
            load_bearing_fields = [
                "sampler_name", "scheduler", "steps", "cfg", 
                "width", "height", "seed", "negative_prompt", 
                "filename_prefix", "checkpoint"
            ]
            failures = []
            for field in load_bearing_fields:
                if field in canonical_recipe:
                    requested = canonical_recipe[field]
                    actual = final_overrides.get(field)
                    if requested != actual:
                        failures.append({
                            "parameter": field,
                            "requested": requested,
                            "actual": actual
                        })
            
            if failures:
                raise MutationError(
                    f"Recipe enforcement failed. Canonical recipe was not applied correctly. Failures: {failures}",
                    workflow_id=execution_plan.workflow_id,
                )
        
        # Apply mutations
        mutated_nodes = []
        applied_changes = {}
        notes = []
        
        # Positive prompt (node 6)
        if "prompt" in final_overrides or "positive_prompt" in final_overrides:
            prompt_value = final_overrides.get("prompt") or final_overrides.get("positive_prompt")
            if prompt_value:
                self.set_positive_prompt(workflow, prompt_value)
                mutated_nodes.append("6")
                applied_changes["positive_prompt"] = prompt_value
        
        # Negative prompt (node 7)
        if "negative_prompt" in final_overrides:
            self.set_negative_prompt(workflow, final_overrides["negative_prompt"])
            mutated_nodes.append("7")
            applied_changes["negative_prompt"] = final_overrides["negative_prompt"]
        
        # Checkpoint (node 4)
        if "checkpoint" in final_overrides and final_overrides["checkpoint"]:
            self.set_checkpoint(workflow, final_overrides["checkpoint"])
            mutated_nodes.append("4")
            applied_changes["checkpoint"] = final_overrides["checkpoint"]
        
        # Resolution (node 5)
        if "width" in final_overrides or "height" in final_overrides:
            width = final_overrides.get("width")
            height = final_overrides.get("height")
            if width or height:
                self.set_resolution(workflow, width, height)
                mutated_nodes.append("5")
                if width:
                    applied_changes["width"] = width
                if height:
                    applied_changes["height"] = height
        
        # Sampler settings (node 3)
        sampler_settings = {
            k: final_overrides[k]
            for k in ["seed", "steps", "cfg", "sampler_name", "scheduler"]
            if k in final_overrides and final_overrides[k] is not None
        }
        if sampler_settings:
            self.set_sampler_settings(workflow, **sampler_settings)
            mutated_nodes.append("3")
            applied_changes.update(sampler_settings)
        
        # Filename prefix (node 9 for txt2img, 11 for img2img, 12 for upscale/inpaint)
        if "prefix" in final_overrides and final_overrides["prefix"]:
            prefix_node_id = self._get_save_image_node_id(execution_plan.workflow_id)
            self.set_filename_prefix(workflow, final_overrides["prefix"], node_id=prefix_node_id)
            mutated_nodes.append(prefix_node_id)
            applied_changes["filename_prefix"] = final_overrides["prefix"]
        elif "filename_prefix" in final_overrides:
            prefix_node_id = self._get_save_image_node_id(execution_plan.workflow_id)
            self.set_filename_prefix(workflow, final_overrides["filename_prefix"], node_id=prefix_node_id)
            mutated_nodes.append(prefix_node_id)
            applied_changes["filename_prefix"] = final_overrides["filename_prefix"]
        
        # Asset-aware inputs for img2img/inpaint/upscale
        if "input_image" in final_overrides and final_overrides["input_image"]:
            self.set_input_image(workflow, final_overrides["input_image"])
            mutated_nodes.append("5")
            applied_changes["input_image"] = final_overrides["input_image"]
        
        if "mask" in final_overrides and final_overrides["mask"]:
            self.set_mask_image(workflow, final_overrides["mask"])
            mutated_nodes.append("9")
            applied_changes["mask"] = final_overrides["mask"]
        
        if "denoise" in final_overrides and final_overrides["denoise"] is not None:
            self.set_denoise(workflow, final_overrides["denoise"])
            mutated_nodes.append("3")
            applied_changes["denoise"] = final_overrides["denoise"]
        
        if "upscale_width" in final_overrides and "upscale_height" in final_overrides:
            self.set_upscale_settings(
                workflow,
                final_overrides["upscale_width"],
                final_overrides["upscale_height"],
                final_overrides.get("upscale_method", "nearest-exact"),
            )
            mutated_nodes.append("10")
            applied_changes["upscale_width"] = final_overrides["upscale_width"]
            applied_changes["upscale_height"] = final_overrides["upscale_height"]
        
        if task_overrides:
            notes.append(f"Applied task-specific overrides for {execution_plan.task_type.value}")
        
        # Verbose logging: Print pre-submit workflow payload fragment
        if self.verbose:
            print(f"\n[WORKFLOW_PAYLOAD] Pre-submit workflow fragment (load-bearing nodes):")
            # Print key nodes with their final values
            key_nodes = ["3", "4", "5", "6", "7", "9"]  # KSampler, Checkpoint, EmptyLatent, Positive, Negative, SaveImage
            for node_id in key_nodes:
                if node_id in workflow:
                    node = workflow[node_id]
                    node_type = node.get("class_type", "Unknown")
                    node_title = node.get("_meta", {}).get("title", node_type)
                    inputs = node.get("inputs", {})
                    print(f"[WORKFLOW_PAYLOAD] node_id={node_id} | node_type={node_type} | node_title={node_title}")
                    for key, value in inputs.items():
                        if isinstance(value, str) and len(value) > 60:
                            print(f"[WORKFLOW_PAYLOAD]   {key}={value[:60]}...")
                        else:
                            print(f"[WORKFLOW_PAYLOAD]   {key}={value}")
        
        return MutationResult(
            workflow_id=execution_plan.workflow_id,
            mutated_workflow=workflow,
            mutated_nodes=mutated_nodes,
            applied_changes=applied_changes,
            notes=notes,
        )
    
    def set_positive_prompt(self, workflow: dict[str, Any], text: str) -> None:
        """Set positive prompt text in CLIPTextEncode node 6.
        
        Args:
            workflow: Workflow dictionary
            text: Positive prompt text
            
        Raises:
            MutationError: If node 6 not found or invalid
        """
        if "6" not in workflow:
            raise MutationError("Node 6 (positive CLIPTextEncode) not found", workflow_id="unknown", node_id="6")
        
        node = workflow["6"]
        if node.get("class_type") != "CLIPTextEncode":
            raise MutationError("Node 6 is not CLIPTextEncode", workflow_id="unknown", node_id="6")
        
        # Node-level logging: capture old value
        old_value = node.get("inputs", {}).get("text", "None")
        
        if "inputs" not in node:
            node["inputs"] = {}
        node["inputs"]["text"] = text
        
        # Node-level logging: print mutation
        if self.verbose:
            node_title = node.get("_meta", {}).get("title", "CLIPTextEncode")
            print(f"[NODE_MUTATION] node_id=6 | node_type=CLIPTextEncode | node_title={node_title}")
            print(f"[NODE_MUTATION] field=text | old_value={old_value[:50] if old_value and len(old_value) > 50 else old_value}... | new_value={text[:50] if len(text) > 50 else text}...")
    
    def set_negative_prompt(self, workflow: dict[str, Any], text: str) -> None:
        """Set negative prompt text in CLIPTextEncode node 7.
        
        Args:
            workflow: Workflow dictionary
            text: Negative prompt text
            
        Raises:
            MutationError: If node 7 not found or invalid
        """
        if "7" not in workflow:
            raise MutationError("Node 7 (negative CLIPTextEncode) not found", workflow_id="unknown", node_id="7")
        
        node = workflow["7"]
        if node.get("class_type") != "CLIPTextEncode":
            raise MutationError("Node 7 is not CLIPTextEncode", workflow_id="unknown", node_id="7")
        
        # Node-level logging: capture old value
        old_value = node.get("inputs", {}).get("text", "None")
        
        if "inputs" not in node:
            node["inputs"] = {}
        node["inputs"]["text"] = text
        
        # Node-level logging: print mutation
        if self.verbose:
            node_title = node.get("_meta", {}).get("title", "CLIPTextEncode")
            print(f"[NODE_MUTATION] node_id=7 | node_type=CLIPTextEncode | node_title={node_title}")
            print(f"[NODE_MUTATION] field=text | old_value={old_value[:50] if old_value and len(old_value) > 50 else old_value}... | new_value={text[:50] if len(text) > 50 else text}...")
    
    def set_checkpoint(self, workflow: dict[str, Any], ckpt_name: str) -> None:
        """Set checkpoint name in CheckpointLoaderSimple node 4.
        
        Args:
            workflow: Workflow dictionary
            ckpt_name: Checkpoint filename
            
        Raises:
            MutationError: If node 4 not found or invalid
        """
        if "4" not in workflow:
            raise MutationError("Node 4 (CheckpointLoaderSimple) not found", workflow_id="unknown", node_id="4")
        
        node = workflow["4"]
        if node.get("class_type") != "CheckpointLoaderSimple":
            raise MutationError("Node 4 is not CheckpointLoaderSimple", workflow_id="unknown", node_id="4")
        
        # Node-level logging: capture old value
        old_value = node.get("inputs", {}).get("ckpt_name", "None")
        
        if "inputs" not in node:
            node["inputs"] = {}
        node["inputs"]["ckpt_name"] = ckpt_name
        
        # Node-level logging: print mutation
        if self.verbose:
            node_title = node.get("_meta", {}).get("title", "CheckpointLoaderSimple")
            print(f"[NODE_MUTATION] node_id=4 | node_type=CheckpointLoaderSimple | node_title={node_title}")
            print(f"[NODE_MUTATION] field=ckpt_name | old_value={old_value} | new_value={ckpt_name}")
    
    def set_resolution(
        self,
        workflow: dict[str, Any],
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """Set resolution in EmptyLatentImage node 5.
        
        Args:
            workflow: Workflow dictionary
            width: Image width (optional)
            height: Image height (optional)
            
        Raises:
            MutationError: If node 5 not found or invalid
        """
        if "5" not in workflow:
            raise MutationError("Node 5 (EmptyLatentImage) not found", workflow_id="unknown", node_id="5")
        
        node = workflow["5"]
        if node.get("class_type") != "EmptyLatentImage":
            raise MutationError("Node 5 is not EmptyLatentImage", workflow_id="unknown", node_id="5")
        
        # Node-level logging: capture old values
        old_width = node.get("inputs", {}).get("width", "None")
        old_height = node.get("inputs", {}).get("height", "None")
        
        if "inputs" not in node:
            node["inputs"] = {}
        
        if width is not None:
            node["inputs"]["width"] = width
        if height is not None:
            node["inputs"]["height"] = height
        
        # Node-level logging: print mutations
        if self.verbose:
            node_title = node.get("_meta", {}).get("title", "EmptyLatentImage")
            print(f"[NODE_MUTATION] node_id=5 | node_type=EmptyLatentImage | node_title={node_title}")
            if width is not None:
                print(f"[NODE_MUTATION] field=width | old_value={old_width} | new_value={width}")
            if height is not None:
                print(f"[NODE_MUTATION] field=height | old_value={old_height} | new_value={height}")
    
    def set_sampler_settings(
        self,
        workflow: dict[str, Any],
        seed: int | None = None,
        steps: int | None = None,
        cfg: float | None = None,
        sampler_name: str | None = None,
        scheduler: str | None = None,
    ) -> None:
        """Set sampler settings in KSampler node 3.
        
        Args:
            workflow: Workflow dictionary
            seed: Random seed (optional)
            steps: Number of sampling steps (optional)
            cfg: CFG scale (optional)
            sampler_name: Sampler name (optional)
            scheduler: Scheduler name (optional)
            
        Raises:
            MutationError: If node 3 not found or invalid
        """
        if "3" not in workflow:
            raise MutationError("Node 3 (KSampler) not found", workflow_id="unknown", node_id="3")
        
        node = workflow["3"]
        if node.get("class_type") != "KSampler":
            raise MutationError("Node 3 is not KSampler", workflow_id="unknown", node_id="3")
        
        # Node-level logging: capture old values
        old_seed = node.get("inputs", {}).get("seed", "None")
        old_steps = node.get("inputs", {}).get("steps", "None")
        old_cfg = node.get("inputs", {}).get("cfg", "None")
        old_sampler = node.get("inputs", {}).get("sampler_name", "None")
        old_scheduler = node.get("inputs", {}).get("scheduler", "None")
        
        if "inputs" not in node:
            node["inputs"] = {}
        
        if seed is not None:
            node["inputs"]["seed"] = seed
        if steps is not None:
            node["inputs"]["steps"] = steps
        if cfg is not None:
            node["inputs"]["cfg"] = cfg
        if sampler_name is not None:
            node["inputs"]["sampler_name"] = sampler_name
        if scheduler is not None:
            node["inputs"]["scheduler"] = scheduler
        
        # Node-level logging: print mutations
        if self.verbose:
            node_title = node.get("_meta", {}).get("title", "KSampler")
            print(f"[NODE_MUTATION] node_id=3 | node_type=KSampler | node_title={node_title}")
            if seed is not None:
                print(f"[NODE_MUTATION] field=seed | old_value={old_seed} | new_value={seed}")
            if steps is not None:
                print(f"[NODE_MUTATION] field=steps | old_value={old_steps} | new_value={steps}")
            if cfg is not None:
                print(f"[NODE_MUTATION] field=cfg | old_value={old_cfg} | new_value={cfg}")
            if sampler_name is not None:
                print(f"[NODE_MUTATION] field=sampler_name | old_value={old_sampler} | new_value={sampler_name}")
            if scheduler is not None:
                print(f"[NODE_MUTATION] field=scheduler | old_value={old_scheduler} | new_value={scheduler}")
    
    def set_filename_prefix(self, workflow: dict[str, Any], prefix: str, node_id: str = "9") -> None:
        """Set filename prefix in SaveImage node.
        
        Args:
            workflow: Workflow dictionary
            prefix: Filename prefix
            node_id: Node ID for SaveImage (default "9" for txt2img)
            
        Raises:
            MutationError: If node not found or invalid
        """
        if node_id not in workflow:
            raise MutationError(f"Node {node_id} (SaveImage) not found", workflow_id="unknown", node_id=node_id)
        
        node = workflow[node_id]
        if node.get("class_type") != "SaveImage":
            raise MutationError(f"Node {node_id} is not SaveImage", workflow_id="unknown", node_id=node_id)
        
        # Node-level logging: capture old value
        old_value = node.get("inputs", {}).get("filename_prefix", "None")
        
        if "inputs" not in node:
            node["inputs"] = {}
        node["inputs"]["filename_prefix"] = prefix
        
        # Node-level logging: print mutation
        if self.verbose:
            node_title = node.get("_meta", {}).get("title", "SaveImage")
            print(f"[NODE_MUTATION] node_id={node_id} | node_type=SaveImage | node_title={node_title}")
            print(f"[NODE_MUTATION] field=filename_prefix | old_value={old_value} | new_value={prefix}")

    def _get_save_image_node_id(self, workflow_id: str) -> str:
        """Get SaveImage node ID for a given workflow.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Node ID for SaveImage node
        """
        # txt2img workflows use node 9
        if workflow_id in ["portrait_sdxl_v1", "cinematic_sdxl_v1", "product_sdxl_v1", "fashion_sdxl_v1"]:
            return "9"
        # img2img simple template uses node 10
        if workflow_id == "img2img_v1":
            return "10"
        # upscale and inpaint use node 12
        if workflow_id in ["upscale_v1", "inpaint_face_v1"]:
            return "12"
        # Default to node 9
        return "9"
    
    def set_input_image(self, workflow: dict[str, Any], image_path: str, node_id: str = "5") -> None:
        """Set input image path in LoadImage node.
        
        Args:
            workflow: Workflow dictionary
            image_path: Path to input image
            node_id: Node ID for LoadImage (default "5")
            
        Raises:
            MutationError: If node not found or invalid
        """
        if node_id not in workflow:
            raise MutationError(f"Node {node_id} (LoadImage) not found", workflow_id="unknown", node_id=node_id)
        
        node = workflow[node_id]
        if node.get("class_type") != "LoadImage":
            raise MutationError(f"Node {node_id} is not LoadImage", workflow_id="unknown", node_id=node_id)
        
        if "inputs" not in node:
            node["inputs"] = {}
        node["inputs"]["image"] = image_path
    
    def set_mask_image(self, workflow: dict[str, Any], mask_path: str, node_id: str = "9") -> None:
        """Set mask image path in LoadImageMask node for inpainting.
        
        Args:
            workflow: Workflow dictionary
            mask_path: Path to mask image
            node_id: Node ID for LoadImageMask (default "9")
            
        Raises:
            MutationError: If node not found or invalid
        """
        if node_id not in workflow:
            raise MutationError(f"Node {node_id} (LoadImageMask) not found", workflow_id="unknown", node_id=node_id)
        
        node = workflow[node_id]
        if node.get("class_type") != "LoadImageMask":
            raise MutationError(f"Node {node_id} is not LoadImageMask", workflow_id="unknown", node_id=node_id)
        
        if "inputs" not in node:
            node["inputs"] = {}
        node["inputs"]["mask"] = mask_path
    
    def set_denoise(self, workflow: dict[str, Any], denoise: float, node_id: str = "3") -> None:
        """Set denoise/strength value in KSampler node.
        
        Args:
            workflow: Workflow dictionary
            denoise: Denoise strength (0.0-1.0)
            node_id: Node ID for KSampler (default "3")
            
        Raises:
            MutationError: If node not found or invalid
        """
        if node_id not in workflow:
            raise MutationError(f"Node {node_id} (KSampler) not found", workflow_id="unknown", node_id=node_id)
        
        node = workflow[node_id]
        if node.get("class_type") != "KSampler":
            raise MutationError(f"Node {node_id} is not KSampler", workflow_id="unknown", node_id=node_id)
        
        if "inputs" not in node:
            node["inputs"] = {}
        node["inputs"]["denoise"] = denoise
    
    def set_upscale_settings(
        self,
        workflow: dict[str, Any],
        width: int,
        height: int,
        upscale_method: str = "nearest-exact",
        node_id: str = "10",
    ) -> None:
        """Set upscale settings in LatentUpscale node.
        
        Args:
            workflow: Workflow dictionary
            width: Target width
            height: Target height
            upscale_method: Upscale method (default "nearest-exact")
            node_id: Node ID for LatentUpscale (default "10")
            
        Raises:
            MutationError: If node not found or invalid
        """
        if node_id not in workflow:
            raise MutationError(f"Node {node_id} (LatentUpscale) not found", workflow_id="unknown", node_id=node_id)
        
        node = workflow[node_id]
        if node.get("class_type") != "LatentUpscale":
            raise MutationError(f"Node {node_id} is not LatentUpscale", workflow_id="unknown", node_id=node_id)
        
        if "inputs" not in node:
            node["inputs"] = {}
        node["inputs"]["width"] = width
        node["inputs"]["height"] = height
        node["inputs"]["upscale_method"] = upscale_method
