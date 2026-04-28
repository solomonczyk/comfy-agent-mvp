"""Node contracts for workflow mutation.

This module defines the source of truth for mutable nodes in workflow templates.
Contracts specify which nodes can be mutated and which inputs are mutable.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class NodeContract:
    """Contract for a mutable workflow node.
    
    This defines the expected structure and mutable inputs for a node.
    The mutator validates workflow nodes against these contracts before mutation.
    """
    node_id: str
    class_type: str
    mutable_inputs: list[str]
    required_inputs: list[str]
    description: str = ""
    
    def validate_node(self, node_data: dict[str, Any]) -> tuple[bool, str]:
        """Validate that a node matches this contract.
        
        Args:
            node_data: The node data from workflow JSON
            
        Returns:
            (is_valid, error_message)
        """
        # Check class_type
        if node_data.get("class_type") != self.class_type:
            return False, f"Expected class_type '{self.class_type}', got '{node_data.get('class_type')}'"
        
        # Check that required inputs exist
        inputs = node_data.get("inputs", {})
        for required_input in self.required_inputs:
            if required_input not in inputs:
                return False, f"Missing required input '{required_input}'"
        
        # Check that mutable inputs exist (optional but recommended)
        for mutable_input in self.mutable_inputs:
            if mutable_input not in inputs:
                return False, f"Missing mutable input '{mutable_input}'"
        
        return True, ""


# SDXL txt2img template node contracts
# Based on data/workflows/sdxl_txt2img_template.json
SDXL_TXT2IMG_CONTRACTS = {
    "3": NodeContract(
        node_id="3",
        class_type="KSampler",
        mutable_inputs=["seed", "steps", "cfg", "sampler_name", "scheduler"],
        required_inputs=["seed", "steps", "cfg", "sampler_name", "scheduler"],
        description="KSampler node for diffusion sampling"
    ),
    "4": NodeContract(
        node_id="4",
        class_type="CheckpointLoaderSimple",
        mutable_inputs=["ckpt_name"],
        required_inputs=["ckpt_name"],
        description="Checkpoint loader for model weights"
    ),
    "5": NodeContract(
        node_id="5",
        class_type="EmptyLatentImage",
        mutable_inputs=["width", "height"],
        required_inputs=["width", "height"],
        description="Empty latent image generator"
    ),
    "6": NodeContract(
        node_id="6",
        class_type="CLIPTextEncode",
        mutable_inputs=["text"],
        required_inputs=["text"],
        description="CLIP text encoder for positive prompt"
    ),
    "7": NodeContract(
        node_id="7",
        class_type="CLIPTextEncode",
        mutable_inputs=["text"],
        required_inputs=["text"],
        description="CLIP text encoder for negative prompt"
    ),
    "9": NodeContract(
        node_id="9",
        class_type="SaveImage",
        mutable_inputs=["filename_prefix"],
        required_inputs=["filename_prefix"],
        description="Image save node with filename prefix"
    ),
}


# SDXL img2img template node contracts
# Based on data/workflows/sdxl_img2img_template.json
SDXL_IMG2IMG_CONTRACTS = {
    "3": NodeContract(
        node_id="3",
        class_type="KSampler",
        mutable_inputs={"seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"},
        required_inputs={"model", "positive", "negative", "latent_image"},
        description="KSampler node for img2img diffusion sampling"
    ),
    "4": NodeContract(
        node_id="4",
        class_type="CheckpointLoaderSimple",
        mutable_inputs={"ckpt_name"},
        required_inputs=set(),
        description="Checkpoint loader for model weights"
    ),
    "5": NodeContract(
        node_id="5",
        class_type="LoadImage",
        mutable_inputs={"image"},
        required_inputs=set(),
        description="Load input image for img2img"
    ),
    "6": NodeContract(
        node_id="6",
        class_type="CLIPTextEncode",
        mutable_inputs={"text"},
        required_inputs={"clip"},
        description="CLIP text encoder for positive prompt"
    ),
    "7": NodeContract(
        node_id="7",
        class_type="CLIPTextEncode",
        mutable_inputs={"text"},
        required_inputs={"clip"},
        description="CLIP text encoder for negative prompt"
    ),
    "8": NodeContract(
        node_id="8",
        class_type="VAEEncode",
        mutable_inputs=set(),
        required_inputs={"pixels", "vae"},
        description="VAE encoder for latent image"
    ),
    "9": NodeContract(
        node_id="9",
        class_type="VAEDecode",
        mutable_inputs=set(),
        required_inputs={"samples", "vae"},
        description="VAE decoder for latent image"
    ),
    "10": NodeContract(
        node_id="10",
        class_type="SaveImage",
        mutable_inputs={"filename_prefix"},
        required_inputs={"images"},
        description="Image save node with filename prefix"
    ),
}


# SDXL inpaint_face template node contracts
# Based on data/workflows/sdxl_inpaint_face_template.json
SDXL_INPAINT_FACE_CONTRACTS = {
    "3": NodeContract(
        node_id="3",
        class_type="KSampler",
        mutable_inputs=["seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
        required_inputs=["seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
        description="KSampler node for inpaint diffusion sampling"
    ),
    "4": NodeContract(
        node_id="4",
        class_type="CheckpointLoaderSimple",
        mutable_inputs=["ckpt_name"],
        required_inputs=["ckpt_name"],
        description="Checkpoint loader for model weights"
    ),
    "5": NodeContract(
        node_id="5",
        class_type="LoadImage",
        mutable_inputs=["image"],
        required_inputs=["image"],
        description="Load input image for inpainting"
    ),
    "6": NodeContract(
        node_id="6",
        class_type="CLIPTextEncode",
        mutable_inputs=["text"],
        required_inputs=["text"],
        description="CLIP text encoder for positive prompt"
    ),
    "7": NodeContract(
        node_id="7",
        class_type="CLIPTextEncode",
        mutable_inputs=["text"],
        required_inputs=["text"],
        description="CLIP text encoder for negative prompt"
    ),
    "9": NodeContract(
        node_id="9",
        class_type="LoadImageMask",
        mutable_inputs=["mask"],
        required_inputs=["mask"],
        description="Load mask image for inpainting"
    ),
    "12": NodeContract(
        node_id="12",
        class_type="SaveImage",
        mutable_inputs=["filename_prefix"],
        required_inputs=["filename_prefix"],
        description="Image save node with filename prefix"
    ),
}


# Upscale template node contracts
# Based on data/workflows/upscale_template.json
UPSCALE_CONTRACTS = {
    "3": NodeContract(
        node_id="3",
        class_type="KSampler",
        mutable_inputs=["seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
        required_inputs=["seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
        description="KSampler node for upscale diffusion sampling"
    ),
    "4": NodeContract(
        node_id="4",
        class_type="CheckpointLoaderSimple",
        mutable_inputs=["ckpt_name"],
        required_inputs=["ckpt_name"],
        description="Checkpoint loader for model weights"
    ),
    "5": NodeContract(
        node_id="5",
        class_type="LoadImage",
        mutable_inputs=["image"],
        required_inputs=["image"],
        description="Load input image for upscaling"
    ),
    "6": NodeContract(
        node_id="6",
        class_type="CLIPTextEncode",
        mutable_inputs=["text"],
        required_inputs=["text"],
        description="CLIP text encoder for positive prompt"
    ),
    "7": NodeContract(
        node_id="7",
        class_type="CLIPTextEncode",
        mutable_inputs=["text"],
        required_inputs=["text"],
        description="CLIP text encoder for negative prompt"
    ),
    "10": NodeContract(
        node_id="10",
        class_type="LatentUpscale",
        mutable_inputs=["width", "height", "upscale_method"],
        required_inputs=["width", "height"],
        description="Latent upscale node"
    ),
    "12": NodeContract(
        node_id="12",
        class_type="SaveImage",
        mutable_inputs=["filename_prefix"],
        required_inputs=["filename_prefix"],
        description="Image save node with filename prefix"
    ),
}


# Contract registry by workflow ID
WORKFLOW_CONTRACTS = {
    "sdxl_txt2img_v1": SDXL_TXT2IMG_CONTRACTS,
    "portrait_sdxl_v1": SDXL_TXT2IMG_CONTRACTS,
    "cinematic_sdxl_v1": SDXL_TXT2IMG_CONTRACTS,
    "product_sdxl_v1": SDXL_TXT2IMG_CONTRACTS,
    "fashion_sdxl_v1": SDXL_TXT2IMG_CONTRACTS,
    "img2img_v1": SDXL_IMG2IMG_CONTRACTS,
    "inpaint_face_v1": SDXL_INPAINT_FACE_CONTRACTS,
    "upscale_v1": UPSCALE_CONTRACTS,
}


# Legacy SDXL_CONTRACTS for backward compatibility
SDXL_CONTRACTS = SDXL_TXT2IMG_CONTRACTS


def get_contract(node_id: str, workflow_id: str = "sdxl_txt2img_v1") -> NodeContract | None:
    """Get contract for a node ID in a specific workflow."""
    contracts = WORKFLOW_CONTRACTS.get(workflow_id, SDXL_TXT2IMG_CONTRACTS)
    return contracts.get(node_id)


def get_all_contracts(workflow_id: str = "sdxl_txt2img_v1") -> dict[str, NodeContract]:
    """Get all node contracts for a specific workflow."""
    return WORKFLOW_CONTRACTS.get(workflow_id, SDXL_TXT2IMG_CONTRACTS).copy()


def get_mutable_node_ids(workflow_id: str = "sdxl_txt2img_v1") -> list[str]:
    """Get list of all mutable node IDs for a specific workflow."""
    contracts = WORKFLOW_CONTRACTS.get(workflow_id, SDXL_TXT2IMG_CONTRACTS)
    return list(contracts.keys())
