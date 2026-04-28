"""RC-DRY1 — PreflightService integration for dry proof."""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.runtime.checkpoint_resolver import CheckpointResolverLite
from app.runtime.preflight_service import PreflightService
from app.runtime.schema_registry import ComfyNodeSchemaRegistry
from app.runtime.resize_selector import ResizeNodeSelector

# Stable root
STABLE_ROOT = Path("f:/ComfyUI/comfy-agent-mvp/data/rc_mir_erdan_ep01")
OUTPUT_CONTROL = STABLE_ROOT / "output/control"

# Load submitted workflow (shot-specific name)
workflow_path = OUTPUT_CONTROL / "ep01_shot01_submitted_workflow.json"
with open(workflow_path, "r", encoding="utf-8") as f:
    workflow = json.load(f)

# Load prompt pack
prompt_pack_path = OUTPUT_CONTROL / "prompt_pack.json"
with open(prompt_pack_path, "r", encoding="utf-8") as f:
    prompt_pack = json.load(f)

# Setup schema registry with mock object_info
schema_registry = ComfyNodeSchemaRegistry()
schema_registry._object_info = {
    "LoadImage": {},
    "ImageScale": {},
    "ImageResize": {},
    "VAEEncode": {},
    "VAEDecode": {},
    "KSampler": {},
    "CheckpointLoaderSimple": {},
    "CLIPTextEncode": {},
    "SaveImage": {},
}

# Setup checkpoint resolver (lite version - no real ComfyUI calls)
# Use real ComfyUI checkpoint directory for RC-REAL0 runtime readiness
real_checkpoints_dir = Path("F:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126/ComfyUI_windows_portable/ComfyUI/models/checkpoints")
checkpoint_resolver = CheckpointResolverLite(checkpoints_root=real_checkpoints_dir)

# Create PreflightService
service = PreflightService(schema_registry, checkpoint_resolver)

# Validate the dry workflow
checkpoint_name = "realvisxlV50_v50Bakedvae.safetensors"
preflight_result = service.validate_reference_locked_workflow(
    workflow,
    checkpoint_name,
    STABLE_ROOT
)

# Write preflight artifact
preflight_path = service.write_preflight_artifact(
    preflight_result,
    OUTPUT_CONTROL,
    "ep01",
    "shot01"
)

print(f"Preflight result status: {preflight_result['status']}")
print(f"Preflight artifact: {preflight_path}")
print(f"Blocks: {preflight_result['blocks']}")
print(f"Warnings: {preflight_result['warnings']}")
