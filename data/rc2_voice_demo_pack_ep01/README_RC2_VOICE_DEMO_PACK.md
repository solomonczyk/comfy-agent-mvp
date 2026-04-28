# RC2 Voiceover Demo Pack

## What This Pack Is

This is a portable RC2 voiceover demo pack containing accepted final artifacts for episode `ep01`, shot `shot01`.

**This is the real voiceover demo pack.** The voiceover was generated using edge-tts and the video was extended/looped to match the voiceover duration.

## Final Artifact Path

The main demo artifact is:
- `output/final/ep01_final_with_voiceover.mp4`

This MP4 contains both video and audio streams with real voiceover.

## Voiceover Information

- **Audio kind:** voiceover (real TTS via edge-tts)
- **TTS engine:** edge-tts
- **Voiceover duration:** 9.336 seconds
- **Final duration:** 9.336 seconds
- **Duration fit passed:** True
- **Duration fit strategy:** extend_video_to_match_voiceover

## Packaging Process

This pack was created by copying existing accepted artifacts from RC2-VOICE1-FREEZE1. The packaging process:

- **Did NOT run ComfyUI**
- **Did NOT run pipeline actions**
- **Did NOT regenerate TTS**
- **Did NOT rerun ffmpeg**
- **Did NOT generate frames**
- **Did NOT mutate frozen RC1**
- **Did NOT mutate frozen RC2 demo pack**
- **Did NOT mutate rc2_voice1_ep01 media artifacts**

The packaging command only copied files from the accepted RC2 voice root to this portable pack root.

## Source Roots

The source root used to create this pack is documented in `proof/source_roots.json`:
- RC2 voice root: `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01`
- Package root: `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01`

## How to Inspect Media/Artifacts

### Media Files
- `output/final/ep01_final_with_voiceover.mp4` - Final MP4 with real voiceover (main demo artifact)
- `output/audio/ep01_real_voiceover.wav` - Real voiceover audio artifact

### Control Artifacts
- `output/control/ep01_voiceover_script.txt` - Voiceover script text
- `output/control/ep01_voiceover_manifest.json` - Voiceover manifest
- `output/control/ep01_final_with_voiceover_manifest.json` - Final manifest with voiceover
- `output/control/artifact_index.json` - Artifact index
- `output/control/ep01_shot01_ledger.json` - Shot ledger
- `output/control/CHECKSUMS_SHA256.txt` - Source checksums
- `output/control/RC2_VOICE1_FREEZE_SUMMARY.json` - RC2-VOICE1 freeze summary

### Proof Files
- `proof/source_roots.json` - Source root documentation
- `proof/RC2_VOICE_DEMO_PACK_VALIDATION.json` - Validation report
- `proof/CHECKSUMS_SHA256.txt` - Package checksums

## Known Limitations

- Single-shot demo (only ep01_shot01)
- Video is extended/looped to match voiceover duration
- Not multi-shot production ready
- Edge-tts dependency for voiceover generation
- This is a demo pack, not a production deliverable

## Validation

Run the validation report to verify pack integrity:
```bash
cat proof/RC2_VOICE_DEMO_PACK_VALIDATION.json
```

All checks should show `"passed": true`.

## Created

2026-04-28T05:55:31.448263Z
RC2-PACK2
