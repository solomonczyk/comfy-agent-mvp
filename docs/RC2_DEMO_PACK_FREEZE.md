# RC2 Demo Pack Freeze Document

## Accepted RC2 Layers

- RC2-DIRECTOR1B accepted
- RC2-RENDER1B accepted
- RC2-AUDIO1 accepted
- RC2-PACK1 accepted

## Package Root

`F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01`

## Package Archive

`F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01.zip`

## Best Media Artifact

`F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01\output\final\ep01_final_with_audio.mp4`

## Validation Result

12/12 checks passed

Validation checks:
- final_with_audio_mp4_exists: PASSED
- audio_artifact_exists: PASSED
- audio_stream_exists: PASSED
- video_stream_exists: PASSED
- audio_kind_is_technical_placeholder: PASSED
- no_fake_voiceover_claim: PASSED
- no_comfyui_generation: PASSED
- no_pipeline_action_rerun: PASSED
- frozen_rc1_not_mutated: PASSED
- rc2_render_root_not_mutated: PASSED
- all_package_paths_exist: PASSED
- json_artifacts_parse_correctly: PASSED

## Pytest Result

90 passed, 8 skipped, 11 warnings in 24.48s

Test files:
- tests/test_render_episode.py
- tests/test_attach_audio.py
- tests/test_director_cli.py
- tests/test_director_commands.py
- tests/test_package_rc2_demo.py

## Known Limitations

1. **Technical Placeholder Audio**: The audio in this pack is a technical placeholder, not a real voiceover. It was created for demo purposes only and should not be used as production audio.

2. **Single-Shot / Single-Scene Demo**: This pack contains only a single shot (ep01_shot01) and single scene. It is not representative of a full multi-shot episode.

3. **Final MP4 Derived from Existing scene.mp4**: The final MP4 was created by copying and processing an existing scene.mp4 from RC1, not by generating new frames.

## Exact Commands to Inspect/Validate

### Validate package integrity
```bash
cat F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01\proof\RC2_DEMO_PACK_VALIDATION.json
```

### Verify checksums
```bash
cat F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01\proof\CHECKSUMS_SHA256.txt
```

### Inspect source roots
```bash
cat F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01\proof\source_roots.json
```

### Read package README
```bash
cat F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01\README_RC2_DEMO_PACK.md
```

### Run tests
```bash
python -m pytest tests/test_package_rc2_demo.py tests/test_attach_audio.py tests/test_render_episode.py -q -s --tb=short
```

## Do-Not-Mutate Warning

**CRITICAL**: The following must NOT be mutated:

- Frozen RC1 root: `F:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01`
- RC2 render root: `F:\ComfyUI\comfy-agent-mvp\data\rc2_render1_ep01`
- RC2 audio root: `F:\ComfyUI\comfy-agent-mvp\data\rc2_audio1_ep01`
- Package media artifacts in: `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01\output\`
- Package archive: `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01.zip`

Any changes to these directories or files will invalidate the freeze status and require re-validation.

## Freeze Status

**ACCEPTED** - This RC2 demo pack is frozen as a stable reproducible checkpoint.

## Created

2026-04-28T05:23:13Z
RC2-FREEZE1
