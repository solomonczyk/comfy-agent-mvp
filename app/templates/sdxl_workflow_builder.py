from copy import deepcopy
from typing import Any


class SDXLWorkflowBuilder:
    POSITIVE_NODE_ID = "6"
    NEGATIVE_NODE_ID = "7"
    SAMPLER_NODE_ID = "3"
    LATENT_NODE_ID = "5"
    CHECKPOINT_NODE_ID = "4"
    SAVE_IMAGE_NODE_ID = "9"

    def __init__(self, template: dict[str, Any]) -> None:
        self.workflow = deepcopy(template)

    def set_checkpoint(self, ckpt_name: str) -> "SDXLWorkflowBuilder":
        self.workflow[self.CHECKPOINT_NODE_ID]["inputs"]["ckpt_name"] = ckpt_name
        return self

    def set_prompts(self, positive: str, negative: str) -> "SDXLWorkflowBuilder":
        self.workflow[self.POSITIVE_NODE_ID]["inputs"]["text"] = positive
        self.workflow[self.NEGATIVE_NODE_ID]["inputs"]["text"] = negative
        return self

    def set_size(self, width: int, height: int, batch_size: int = 1) -> "SDXLWorkflowBuilder":
        self.workflow[self.LATENT_NODE_ID]["inputs"]["width"] = width
        self.workflow[self.LATENT_NODE_ID]["inputs"]["height"] = height
        self.workflow[self.LATENT_NODE_ID]["inputs"]["batch_size"] = batch_size
        return self

    def set_sampling(
        self,
        seed: int,
        steps: int,
        cfg: float,
        sampler_name: str,
        scheduler: str,
        denoise: float = 1.0,
    ) -> "SDXLWorkflowBuilder":
        sampler_inputs = self.workflow[self.SAMPLER_NODE_ID]["inputs"]
        sampler_inputs["seed"] = seed
        sampler_inputs["steps"] = steps
        sampler_inputs["cfg"] = cfg
        sampler_inputs["sampler_name"] = sampler_name
        sampler_inputs["scheduler"] = scheduler
        sampler_inputs["denoise"] = denoise
        return self

    def set_filename_prefix(self, filename_prefix: str) -> "SDXLWorkflowBuilder":
        self.workflow[self.SAVE_IMAGE_NODE_ID]["inputs"]["filename_prefix"] = filename_prefix
        return self

    def build(self) -> dict[str, Any]:
        return self.workflow
