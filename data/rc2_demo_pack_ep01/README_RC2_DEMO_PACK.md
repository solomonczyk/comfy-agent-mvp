# RC2 Demo Proof Pack

## What This Pack Is

This is a portable RC2 demo proof pack containing accepted final artifacts for episode `ep01`, shot `shot01`.

## Final Artifact Path

The main demo artifact is:
- `output/final/ep01_final_with_audio.mp4`

This MP4 contains both video and audio streams.

## Audio Disclaimer

**Important:** The audio in this pack is a **technical placeholder**, not a real voiceover.

- **Audio kind:** technical_placeholder
- **Purpose:** Technical placeholder for demo purposes only
- **Not intended as:** Production voiceover or final audio

## Packaging Process

This pack was created by copying existing accepted artifacts. The packaging process:

- **Did NOT run ComfyUI**
- **Did NOT run pipeline actions**
- **Did NOT regenerate audio**
- **Did NOT rerun render-final**
- **Did NOT mutate frozen RC1**
- **Did NOT mutate RC2 render root**
- **Did NOT mutate RC2 audio source root**

The packaging command only copied files from the accepted RC2 audio root to this portable pack root.

## Source Roots

The source roots used to create this pack are documented in `proof/source_roots.json`:
- RC1 frozen root: `F:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01`
- RC2 render root: `F:\ComfyUI\comfy-agent-mvp\data\rc2_render1_ep01`
- RC2 audio root: `F:\ComfyUI\comfy-agent-mvp\data\rc2_audio1_ep01`
- Package root: `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01`

## How to Inspect Media/Artifacts

### Media Files
- `output/final/ep01_final_with_audio.mp4` - Final MP4 with audio (main demo artifact)
- `output/final/ep01_final_no_audio.mp4` - Final MP4 without audio
- `output/audio/ep01_voiceover.wav` - Audio artifact (technical placeholder)

### Control Artifacts
- `output/control/ep01_audio_manifest.json` - Audio manifest
- `output/control/ep01_final_with_audio_manifest.json` - Final manifest with audio
- `output/control/artifact_index.json` - Artifact index
- `output/control/ep01_shot01_ledger.json` - Shot ledger

### Proof Files
- `proof/source_roots.json` - Source root documentation
- `proof/RC2_DEMO_PACK_VALIDATION.json` - Validation report

## Known Limitations

- Audio is a technical placeholder, not a real voiceover
- This is a demo pack, not a production deliverable
- RC1 frozen proof remains separate in the original RC1 root
- This pack does not contain all RC1 artifacts (only RC2 final artifacts)

## Validation

Run the validation report to verify pack integrity:
```bash
cat proof/RC2_DEMO_PACK_VALIDATION.json
```

All checks should show `"passed": true`.

## Created

2026-04-28T05:23:13.073118Z
RC2-PACK1
