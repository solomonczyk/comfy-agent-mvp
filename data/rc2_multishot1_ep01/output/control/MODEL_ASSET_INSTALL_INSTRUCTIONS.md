# MODEL ASSET INSTALL INSTRUCTIONS

## Task Code: RC2-PRODCARDS3R
## Episode: ep01 / Shot: shot01
## Created: 2026-04-30T07:46:00.000000Z

---

## IMPORTANT BOUNDARY NOTICE

**This document is a planning and instruction artifact ONLY.**  
No model download, installation, ComfyUI execution, frame generation, retry, QA, assembly, audio, or render actions are performed by this layer.

The retry gate remains **CLOSED**. Production is **NOT accepted**. Downstream actions remain **BLOCKED**.

---

## Missing Assets Summary

| Asset ID | Filename | Type | Status | Blocking |
|---|---|---|---|---|
| asset-001-dynavision | dynavision_v10.safetensors | checkpoint | MISSING | Yes |
| asset-002-ipadapter-faceid | ip-adapter-faceid-plus_sd15.bin | ipadapter_faceid_model | MISSING | Yes |

Both assets must be installed manually by the operator before any retry authorization can be considered.

---

## Asset 1: dynavision_v10.safetensors

### Purpose
Checkpoint replacement for controlled retry of shot01. The current RealVisXL checkpoint produces fundamental incompatibility with the Alya character type (identity drift, visual artifacts, haze, banding, texture collapse).

### Expected Install Path
```
F:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126/ComfyUI_windows_portable/ComfyUI/models/checkpoints/dynavision_v10.safetensors
```

### Source Acquisition
- **Allowed sources**: trusted model source only (CivitAI or HuggingFace)
- **CivitAI**: https://civitai.com/search/models?query=dynavision
- **HuggingFace**: search for dynavision_v10
- Verify uploader reputation and model page before downloading

### Validation Requirements
- **Extension**: must be `.safetensors`
- **Size**: approximately 2.0-7.0 GB (depends on variant: fp16 ~2GB, full ~7GB)
- **Checksum**: SHA-256 or MD5 from source must be recorded post-download
- **Partial download prohibition**: confirm file is fully written (no `.tmp`, `.part`, or `.crdownload` remnants)

### Notes
- This is an **SD1.5-based checkpoint** (not SDXL)
- Baked VAE variant preferred — no separate VAE node required
- Do NOT reuse SDXL checkpoints already present in the checkpoints directory

---

## Asset 2: ip-adapter-faceid-plus_sd15.bin

### Purpose
Facial feature extraction model for dual-lock identity preservation. Complements the ReferenceOnlySimple node at weight 0.85 with IP-Adapter FaceID Plus at weight 0.8.

### Expected Install Path
```
F:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126/ComfyUI_windows_portable/ComfyUI/models/ipadapter/ip-adapter-faceid-plus_sd15.bin
```

### Alternate Acceptable Model
```
F:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126/ComfyUI_windows_portable/ComfyUI/models/ipadapter/ip-adapter-faceid-plusv2_sd15.bin
```
If the v2 variant is available, it is preferred.

### Source Acquisition
- **Allowed sources**: trusted model source only (HuggingFace official repository)
- **HuggingFace**: https://huggingface.co/h94/IP-Adapter-FaceID/tree/main
- Prefer official release files from the h94 organization

### Validation Requirements
- **Extension**: must be `.bin`
- **Size**: approximately 500-800 MB
- **Checksum**: SHA-256 or MD5 from source must be recorded post-download
- **Partial download prohibition**: confirm file is fully written

### Notes
- ComfyUI_IPAdapter_plus custom node is **already installed** — only the model weights file is missing
- The existing `ip-adapter_sdxl.safetensors` at `F:/ComfyUI/models/ipadapter/` is an SDXL variant and is **NOT compatible** with this SD1.5 retry plan
- `insightface buffalo_l` preprocessor is also required; it will auto-download on first ComfyUI IP-Adapter node use if the insightface package is installed

---

## Safe Install Contract

1. **Operator must download assets manually or through an approved, trusted method.**
2. **Assets must be placed exactly in the expected paths listed above.** No subdirectories, no renamed files, no symlinks unless verified.
3. **File existence check must pass.** After placement, confirm `os.path.exists(expected_path)` returns true for both files.
4. **File extension must match expected type.** `.safetensors` for checkpoint; `.bin` for IP-Adapter model.
5. **Checksum or at minimum file size must be recorded.** Record SHA-256 (preferred) or MD5 from the source page, and verify after download. If no source checksum is available, record and verify minimum file size.
6. **Retry gate must remain CLOSED after install until the verification layer passes.** `retry_gate_open` must stay `false`.
7. **NO generation is allowed in this layer.** The contract explicitly prohibits ComfyUI execution, frame generation, `retry_generate_frames`, QA rerun, `assemble_scene`, audio attach, episode render, or any downstream action until `controlled_retry_authorization_required` is reached.

---

## Post-Install Verification Steps (To Be Executed After Manual Install)

After both assets are manually placed, the following verification must be performed before advancing state:

1. **File existence check** — confirm both files exist at expected_install_path.
2. **Record size/hash** — capture `os.path.getsize` and SHA-256 checksum for both files.
3. **Verify extension** — confirm `.safetensors` and `.bin` respectively.
4. **Verify retry implementation plan still targets shot01** — read `controlled_retry_implementation_plan.json` and confirm `target_shot_id == "shot01"`.
5. **Verify retry_gate_open remains false** — read `artifact_index.json` and confirm `retry_gate_open == false`.
6. **Verify no generation was performed during install layer** — confirm `generation_performed == false` and `comfyui_generation == false` in `artifact_index.json`.

Only after all six checks pass may the state transition to:
- `next_allowed_action`: `controlled_retry_authorization_required`
- `retry_prerequisites_available`: `true`

If any check fails, state remains:
- `next_allowed_action`: `model_asset_install_required`

---

## State Summary (Current)

- `retry_gate_open`: **false**
- `production_accepted`: **false**
- `assemble_scene_allowed`: **false**
- `downstream_blocked`: **true**
- `next_allowed_action`: **model_asset_install_required**
- `retry_prerequisites_available`: **false**
- `comfyui_generation`: **false**
- `generation_performed`: **false**
