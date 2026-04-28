# RC2 Voice Demo Pack Freeze

## Accepted State

RC2-PACK2B is accepted as the portable real voiceover demo pack.

## Package Root

`F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01`

## Package Zip

`F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01.zip`

## Best Packaged Media

`F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01\output\final\ep01_final_with_voiceover.mp4`

## Validation Result

**13/13 checks passed** - All validation checks passed.

See `proof/RC2_VOICE_DEMO_PACK_VALIDATION.json` for detailed validation report.

## Pytest Result

**24 passed, 8 skipped** - RC2-PACK2B validation tests passed.

## Real Voiceover Details

- **Audio kind:** voiceover (real TTS via edge-tts)
- **TTS engine:** edge-tts
- **Voiceover duration:** 9.336 seconds
- **Final duration:** 9.336 seconds
- **Duration fit passed:** True
- **Duration fit strategy:** extend_video_to_match_voiceover
- **Duration delta:** 0.0 seconds

## Known Limitations

- Single-shot demo (only ep01_shot01)
- Video is extended/looped to match voiceover duration
- Not multi-shot production ready
- Edge-tts dependency for voiceover generation
- This is a demo pack, not a production deliverable

## Do Not Mutate Warning

**CRITICAL:** Do NOT mutate the following:

- Source voiceover root: `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice1_ep01`
- Frozen RC1
- Frozen RC2 demo pack: `F:\ComfyUI\comfy-agent-mvp\data\rc2_demo_pack_ep01`
- This frozen pack: `F:\ComfyUI\comfy-agent-mvp\data\rc2_voice_demo_pack_ep01`

Do NOT:
- Regenerate TTS
- Rerun ffmpeg
- Run ComfyUI
- Run pipeline actions
- Recopy media unless validation proves package is missing files

## Freeze Version

RC2-VOICE-DEMO-PACK-FREEZE1

## Created

2026-04-28T08:07:00Z
RC2-VOICE-DEMO-FREEZE1
