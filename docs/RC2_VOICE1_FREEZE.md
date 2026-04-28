# RC2-VOICE1 Freeze Document

## Status
**Accepted** - Real TTS voiceover demo is frozen as the best checkpoint.

## Voiceover Root
`F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01`

## Best Media Artifact
`F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\final\ep01_final_with_voiceover.mp4`

## Voiceover Details
- **Voiceover duration**: 9.336 seconds
- **Final MP4 duration**: 9.336 seconds
- **Duration fit passed**: true (delta = 0.0 seconds)
- **TTS engine**: edge-tts
- **Audio kind**: voiceover (real speech, not technical placeholder)

## Accepted RC2 Layers
- **RC1 frozen root**: `F:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01` (frozen)
- **RC2 demo pack**: `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01` (frozen with technical placeholder audio)
- **RC2 voice root**: `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01` (accepted with real TTS voiceover)

## What Was Fixed from RC2-AUDIO1
RC2-AUDIO1 (technical placeholder audio) → RC2-VOICE1 (real TTS voiceover)
- Replaced technical placeholder audio with real speech using edge-tts
- Fixed duration mismatch by extending video to match voiceover (9.336s)
- Fixed manifest consistency (duration_fit_passed now true across all artifacts)
- No ComfyUI generation, no pipeline reruns, no frozen pack mutation

## Known Limitations
- **Single-shot demo**: Only ep01_shot01 is supported
- **Video extension**: Video is looped/extended to match voiceover duration (3s → 9.336s)
- **Not multi-shot production**: This is a proof-of-concept, not production-ready
- **Edge-tts dependency**: Requires edge-tts to be available for voiceover generation

## Exact Inspect Paths

### Final MP4 with Voiceover
```
F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\final\ep01_final_with_voiceover.mp4
```

### Voiceover Audio
```
F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\audio\ep01_real_voiceover.wav
```

### Voiceover Manifest
```
F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\control\ep01_voiceover_manifest.json
```

### Final Manifest
```
F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\control\ep01_final_with_voiceover_manifest.json
```

### Artifact Index
```
F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\control\artifact_index.json
```

### Ledger
```
F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\control\ep01_shot01_ledger.json
```

### Checksums
```
F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\control\CHECKSUMS_SHA256.txt
```

### Freeze Summary
```
F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\control\RC2_VOICE1_FREEZE_SUMMARY.json
```

## Validation Commands

### Check final MP4 duration and streams
```bash
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_type,width,height,duration:stream=codec_name -of json "F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\final\ep01_final_with_voiceover.mp4"
```

### Verify checksums
```bash
cd F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\control
sha256sum -c CHECKSUMS_SHA256.txt
```

### Verify manifest consistency
```bash
python -c "import json; v=json.load(open('ep01_voiceover_manifest.json')); f=json.load(open('ep01_final_with_voiceover_manifest.json')); print('duration_fit_passed match:', v['duration_fit_passed']==f['duration_fit_passed']); print('duration_delta:', v['duration_delta_seconds'], f['duration_delta_seconds'])"
```

### Run tests
```bash
python -m pytest tests/test_voiceover_final.py tests/test_attach_audio.py tests/test_render_episode.py tests/test_package_rc2_demo.py -q -s --tb=short
```

## DO NOT MUTATE

The following assets are frozen and MUST NOT be modified:
- `F:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01` (RC1 frozen root)
- `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01` (RC2 demo pack with placeholder audio)
- `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\final\ep01_final_with_voiceover.mp4` (best media artifact)
- `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01\output\audio\ep01_real_voiceover.wav` (voiceover audio)
- All manifests, artifact_index.json, and ledger.json in rc2_voice1_ep01

Any modifications to frozen assets invalidates the freeze status and requires a new freeze cycle.

## Freeze Metadata
- **Freeze version**: RC2-VOICE1-FREEZE1
- **Created at**: 2026-04-28T05:44:00Z
- **Freeze reason**: Accepted real TTS voiceover demo as best checkpoint
