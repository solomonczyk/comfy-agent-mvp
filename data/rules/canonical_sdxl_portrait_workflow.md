# Canonical SDXL Portrait Workflow v1

## Workflow Definition

**Workflow ID**: `sdxl_txt2img_v1`
**Workflow Version**: `1.0`
**Template Path**: `data/workflows/sdxl_txt2img_template.json`
**Purpose**: Canonical SDXL portrait generation workflow for checkpoint comparison

## Canonical Node IDs

| Node ID | Node Type | Purpose | Load-Bearing Fields |
|---------|-----------|---------|---------------------|
| `4` | CheckpointLoaderSimple | Load checkpoint | `ckpt_name` |
| `6` | CLIPTextEncode | Positive prompt encoding | `text` |
| `7` | CLIPTextEncode | Negative prompt encoding | `text` |
| `5` | EmptyLatentImage | Latent image dimensions | `width`, `height`, `batch_size` |
| `3` | KSampler | Sampling parameters | `seed`, `steps`, `cfg`, `sampler_name`, `scheduler`, `denoise` |
| `8` | VAEDecode | VAE decoding | (uses checkpoint's VAE) |
| `9` | SaveImage | Save output image | `filename_prefix` |

**Output Node ID**: `9`

## Load-Bearing Recipe Fields

The following fields MUST be controlled programmatically by the agent:

| Setting | Node ID | Field | Type | Example |
|---------|---------|-------|------|---------|
| checkpoint | `4` | `ckpt_name` | string | `sd_xl_base_1.0_0.9vae.safetensors` |
| positive_prompt | `6` | `text` | string | `realistic female portrait...` |
| negative_prompt | `7` | `text` | string | `blurry, low quality...` |
| width | `5` | `width` | int | `1024` |
| height | `5` | `height` | int | `1024` |
| steps | `3` | `steps` | int | `30` |
| cfg | `3` | `cfg` | float | `6.0` |
| sampler_name | `3` | `sampler_name` | string | `euler` |
| scheduler | `3` | `scheduler` | string | `karras` |
| seed | `3` | `seed` | int | `123456789` |
| denoise | `3` | `denoise` | float | `1.0` |
| filename_prefix | `9` | `filename_prefix` | string | `portrait_comparison/...` |

## Canonical Recipe for Portrait Comparison

```python
{
    "checkpoint": "sd_xl_base_1.0_0.9vae.safetensors",
    "sampler_name": "euler",
    "scheduler": "karras",
    "steps": 30,
    "cfg": 6.0,
    "width": 1024,
    "height": 1024,
    "seed": 123456789,  # Fixed, not randomized
    "denoise": 1.0,
    "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, extra fingers, duplicate, distorted features, oversaturated",
    "filename_prefix": "portrait_comparison/{checkpoint_name}"
}
```

## Mutation Path

1. **Requested Settings**: Python dict passed to `SDXLAgent.generate()`
2. **Workflow Mutator**: `SDXLWorkflowBuilder` applies settings to template
3. **Mutated Workflow**: In-memory workflow dict with all settings applied
4. **Validation**: `validate_recipe_settings()` checks parity before submission
5. **Submitted Payload**: Final workflow dict sent to ComfyUI via `queue_prompt()`

## Fail-Fast Conditions

Generation MUST fail if any load-bearing field mismatch is detected:
- `status = failed`
- `failed_stage = recipe_enforcement`
- Error message includes the specific parameter that failed parity

## Metadata Requirements

Every run must include in `recipe_validation`:
- `requested`: Original requested settings
- `workflow_actual`: Settings as applied in workflow
- `parity`: Per-parameter parity check (requested vs actual)
- `passed`: Boolean indicating overall parity
- `failures`: List of any parameter mismatches
