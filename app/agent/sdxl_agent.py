import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.comfy.comfy_client import ComfyClient
from app.templates.sdxl_workflow_builder import SDXLWorkflowBuilder
from app.tools import fetch_outputs, submit_to_comfy, watch_progress
from app.tools.tool_trace import ToolTrace


StatusCallback = Callable[[str, dict[str, Any] | None], None]


def validate_recipe_settings(
    requested: dict[str, Any],
    workflow: dict[str, Any],
) -> dict[str, Any]:
    """Validate that requested recipe settings are applied in the workflow.
    
    Returns validation report with requested vs actual values.
    """
    from app.templates.sdxl_workflow_builder import SDXLWorkflowBuilder
    
    validation = {
        "requested": requested,
        "workflow_actual": {},
        "parity": {},
        "passed": True,
        "failures": [],
    }
    
    # Extract actual values from workflow
    checkpoint_node = workflow[SDXLWorkflowBuilder.CHECKPOINT_NODE_ID]["inputs"]
    sampler_node = workflow[SDXLWorkflowBuilder.SAMPLER_NODE_ID]["inputs"]
    latent_node = workflow[SDXLWorkflowBuilder.LATENT_NODE_ID]["inputs"]
    positive_node = workflow[SDXLWorkflowBuilder.POSITIVE_NODE_ID]["inputs"]
    negative_node = workflow[SDXLWorkflowBuilder.NEGATIVE_NODE_ID]["inputs"]
    
    workflow_actual = {
        "checkpoint": checkpoint_node.get("ckpt_name"),
        "sampler_name": sampler_node.get("sampler_name"),
        "scheduler": sampler_node.get("scheduler"),
        "steps": sampler_node.get("steps"),
        "cfg": sampler_node.get("cfg"),
        "seed": sampler_node.get("seed"),
        "width": latent_node.get("width"),
        "height": latent_node.get("height"),
        "positive_prompt": positive_node.get("text"),
        "negative_prompt": negative_node.get("text"),
    }
    
    validation["workflow_actual"] = workflow_actual
    
    # Check parity for each setting
    parity_checks = [
        ("checkpoint", requested["checkpoint"], workflow_actual["checkpoint"]),
        ("sampler_name", requested["sampler_name"], workflow_actual["sampler_name"]),
        ("scheduler", requested["scheduler"], workflow_actual["scheduler"]),
        ("steps", requested["steps"], workflow_actual["steps"]),
        ("cfg", requested["cfg"], workflow_actual["cfg"]),
        ("seed", requested["seed"], workflow_actual["seed"]),
        ("width", requested["width"], workflow_actual["width"]),
        ("height", requested["height"], workflow_actual["height"]),
        ("positive_prompt", requested["positive_prompt"], workflow_actual["positive_prompt"]),
        ("negative_prompt", requested["negative_prompt"], workflow_actual["negative_prompt"]),
    ]
    
    for param_name, requested_val, actual_val in parity_checks:
        passed = requested_val == actual_val
        validation["parity"][param_name] = {
            "requested": requested_val,
            "actual": actual_val,
            "passed": passed,
        }
        
        if not passed:
            validation["passed"] = False
            validation["failures"].append({
                "parameter": param_name,
                "requested": requested_val,
                "actual": actual_val,
            })
    
    return validation


class SDXLAgent:
    def __init__(self, workflow_path: str | Path) -> None:
        self.workflow_path = Path(workflow_path)
        self.client = ComfyClient()

    async def generate(
        self,
        positive_prompt: str,
        negative_prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg: float = 6.0,
        sampler_name: str = "dpmpp_2m",
        scheduler: str = "karras",
        seed: int | None = None,
        checkpoint: str = "sd_xl_base_1.0_0.9vae.safetensors",
        filename_prefix: str = "agent/sdxl_agent",
        status_callback: StatusCallback | None = None,
        tool_trace: ToolTrace | None = None,
    ) -> dict[str, Any]:
        final_seed = seed if seed is not None else random.randint(1, 2**31 - 1)
        
        # Capture requested recipe
        requested_recipe = {
            "checkpoint": checkpoint,
            "sampler_name": sampler_name,
            "scheduler": scheduler,
            "steps": steps,
            "cfg": cfg,
            "seed": final_seed,
            "width": width,
            "height": height,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
        }
        
        template = await self.client.load_workflow(self.workflow_path)
        workflow = (
            SDXLWorkflowBuilder(template)
            .set_checkpoint(checkpoint)
            .set_prompts(positive_prompt, negative_prompt)
            .set_size(width=width, height=height, batch_size=1)
            .set_sampling(
                seed=final_seed,
                steps=steps,
                cfg=cfg,
                sampler_name=sampler_name,
                scheduler=scheduler,
                denoise=1.0,
            )
            .set_filename_prefix(filename_prefix)
            .build()
        )
        
        # Validate recipe settings before submission
        validation = validate_recipe_settings(requested_recipe, workflow)
        
        if not validation["passed"]:
            raise RuntimeError(
                f"Recipe enforcement failed. Settings not applied correctly:\n"
                f"Failures: {validation['failures']}\n"
                f"Requested: {validation['requested']}\n"
                f"Actual: {validation['workflow_actual']}"
            )
        
        prompt_id = await submit_to_comfy.run(tool_trace, client=self.client, workflow=workflow)
        if status_callback:
            status_callback(
                "QUEUED",
                {
                    "prompt_id": prompt_id,
                },
            )
        history_item = await watch_progress.run(
            tool_trace,
            client=self.client,
            prompt_id=prompt_id,
            status_callback=status_callback,
        )
        images = await fetch_outputs.run(tool_trace, client=self.client, history_item=history_item)
        if not images:
            raise RuntimeError(
                f"ComfyUI completed for prompt_id={prompt_id}, but no output images were found."
            )
        return {
            "prompt_id": prompt_id,
            "seed": final_seed,
            "workflow": workflow,
            "history": history_item,
            "images": images,
            "recipe_validation": validation,
        }
