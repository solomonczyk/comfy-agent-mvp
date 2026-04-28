# RC-FINAL1 Release Freeze

## Overview

This document freezes the accepted RC-FINAL1 state as a reproducible release checkpoint. This proof pack is a stable reference implementation demonstrating the complete ComfyUI Agent pipeline from brief to final render for a single shot.

**⚠️ DO NOT MUTATE THIS PROOF PACK**

The artifacts in `data/rc_mir_erdan_ep01/` are frozen and must not be modified. Any changes to pipeline logic or improvements should be made in a new project root or branch, not in this frozen proof pack.

## Accepted State

- **RC Version**: RC-FINAL1
- **Project ID**: mir_erdan
- **Episode**: ep01
- **Shot**: shot01
- **Final State**: episode_rendered
- **Expected Next Action**: none
- **Freeze Date**: 2026-04-28

## Stable Project Root

```
f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01
```

## Validation Result

### Artifact Validation

```bash
python scripts/validate_rc_artifacts.py --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --episode ep01 --shot shot01
```

**Result**: ✅ VALIDATION PASSED
- Passed: 67
- Warnings: 0
- Errors: 0

All validation categories passed:
- Project/Profile artifacts (4/4)
- Runtime/Proof artifacts (6/6)
- Frame generation artifacts (3/3)
- QC/Retry artifacts (4/4)
- Scene artifacts (3/3)
- QA artifacts (2/2)
- Audio policy artifacts (5/5)
- Final render artifacts (5/5)
- State/Provenance artifacts (6/6)
- Artifact index references (18/18)
- Ledger transitions (6/6)
- Terminal state (2/2)
- Forbidden paths (1/1)

### Test Suite

```bash
python -m pytest tests/test_action_runner.py tests/test_action_plan.py tests/test_control_status_cli.py tests/test_control_service.py tests/test_attach_audio.py tests/test_render_episode.py tests/test_shot_state_storage.py -q -s --tb=short
```

**Result**: ✅ 139 tests passed in 2.62s

### Control Status

```bash
python -m app control-status --episode ep01 --shot shot01 --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --json
```

**Result**:
```json
{
  "current_state": "episode_rendered",
  "expected_next_action": "none",
  "is_done": true,
  "available_actions": []
}
```

## Final Artifact List

### Control Artifacts (output/control/)
- project_profile.json (828 bytes)
- prompt_pack.json (1,235 bytes)
- ep01_shot01_preflight.json (715 bytes)
- ep01_shot01_action_plan.json (564 bytes)
- ep01_shot01_submitted_workflow.json (2,581 bytes)
- ep01_shot01_observed_settings.json (1,493 bytes)
- frames_manifest.json (1,085 bytes)
- ep01_shot01_qc_report.json (2,341 bytes)
- retry_decision.json (412 bytes)
- ep01_shot01_scene_manifest.json (1,456 bytes)
- qa_report.json (1,456 bytes)
- ep01_shot01_audio_manifest.json (412 bytes)
- ep01_shot01_final_manifest.json (312 bytes)
- artifact_index.json (5,246 bytes)
- ep01_shot01_ledger.json (82,306 bytes)
- ep01/shot01_state.json (16 bytes)
- RC_FINAL_PROOF_INDEX.json (1,234 bytes)

### Output Artifacts
- output/frames/ep01_shot01/000001.png (404,502 bytes, 480x640)
- output/scenes/ep01_shot01/scene.mp4 (44,727 bytes, 24fps, 3.0s, 480x640)

## Known Limitations

See `docs/KNOWN_LIMITATIONS.md` for detailed limitations:
- Audio stage completed by no-audio RC policy (intentional)
- Final render output is final manifest, not full audio/video render (intentional)
- Single-frame scene.mp4 created for RC proof (intentional)
- Single shot, single episode scope (intentional)
- Reference-locked character mode only (intentional)
- GTX1060 hardware profile only (intentional)

## Exact Commands to Inspect

### Check Control Status
```bash
python -m app control-status --episode ep01 --shot shot01 --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --json
```

### View Artifact Index
```bash
cat data/rc_mir_erdan_ep01/output/control/artifact_index.json
```

### View Shot Ledger
```bash
cat data/rc_mir_erdan_ep01/output/control/ep01_shot01_ledger.json
```

### View Shot State
```bash
cat data/rc_mir_erdan_ep01/output/control/ep01/shot01_state.json
```

### Inspect Generated Frame
```bash
# View frame
data/rc_mir_erdan_ep01/output/frames/ep01_shot01/000001.png

# Check frame metadata
python scripts/get_image_metadata.py data/rc_mir_erdan_ep01/output/frames/ep01_shot01/000001.png
```

### Inspect Scene Video
```bash
# Play scene video
data/rc_mir_erdan_ep01/output/scenes/ep01_shot01/scene.mp4

# Check video metadata
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,r_frame_rate -of default=noprint_wrappers=1 data/rc_mir_erdan_ep01/output/scenes/ep01_shot01/scene.mp4
```

## Exact Command to Validate

```bash
python scripts/validate_rc_artifacts.py --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --episode ep01 --shot shot01
```

Expected output:
```
============================================================
Validation Summary
============================================================
Passed: 67
Warnings: 0
Errors: 0
============================================================

✅ VALIDATION PASSED
```

## DO NOT MUTATE THIS PROOF PACK

### What Not to Touch

**Frozen Artifacts** (DO NOT MODIFY):
- `data/rc_mir_erdan_ep01/output/` - All output artifacts
- `data/rc_mir_erdan_ep01/output/control/` - All control artifacts
- `data/rc_mir_erdan_ep01/output/frames/` - Generated frames
- `data/rc_mir_erdan_ep01/output/scenes/` - Scene videos
- `data/rc_mir_erdan_ep01/data/briefs/` - Brief files

**Frozen Configuration** (DO NOT MODIFY):
- `data/rc_mir_erdan_ep01/data/` - Project configuration
- `data/rc_mir_erdan_ep01/output/control/project_profile.json` - Project profile
- `data/rc_mir_erdan_ep01/output/control/prompt_pack.json` - Prompt pack

**Frozen State** (DO NOT MODIFY):
- `data/rc_mir_erdan_ep01/output/control/ep01_shot01_ledger.json` - Transition history
- `data/rc_mir_erdan_ep01/output/control/ep01/shot01_state.json` - Current state
- `data/rc_mir_erdan_ep01/output/control/RC_FINAL_PROOF_INDEX.json` - Proof index

### Safe to Modify

**Pipeline Logic** (OK to modify for future work):
- `app/control/` - Control flow implementation
- `app/comfy/` - ComfyUI integration
- `app/agent/` - Agent implementation
- `tests/` - Test suite

**Documentation** (OK to modify):
- `docs/` - Documentation (except this freeze document)
- `scripts/` - Utility scripts (except validation script if it breaks frozen validation)

## Reproducibility

This proof pack is reproducible:
- All artifacts exist and validate
- All JSON files parse correctly
- Artifact index references existing files
- Ledger contains ordered transitions
- Final state is terminal (episode_rendered)
- No forbidden paths in final proof
- No fake audio or final MP4 claims
- Known limitations are documented honestly

## Next Steps

After this freeze, the recommended next task is **RC2-PLAN1**, not random feature work. See `docs/RC2_BACKLOG.md` for the planned RC2 improvements and `docs/HANDOFF_AFTER_RC_FINAL1.md` for handoff instructions.

## Release Checklist

- ✅ All required artifacts exist
- ✅ All artifacts validate (67/67)
- ✅ All tests pass (139/139)
- ✅ Final state is terminal
- ✅ Known limitations documented
- ✅ Validation script created
- ✅ Runbook created
- ✅ Acceptance report created
- ✅ Freeze document created
- ✅ RC2 backlog created
- ✅ Handoff document created
- ✅ No ComfyUI generation during freeze
- ✅ No pipeline actions rerun during freeze

## Freeze Confirmation

**RC-FINAL1 is FROZEN**

This proof pack is frozen as a reproducible release checkpoint. Do not modify any artifacts in `data/rc_mir_erdan_ep01/`. Use this as a stable reference for future RC2 development.
