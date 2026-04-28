# ComfyUI Agent RC Proof Pack - Runbook

## Overview

This is a reproducible proof pack for the ComfyUI Agent Reference Implementation (RC). The pack demonstrates a complete end-to-end pipeline execution from brief to final render for a single shot (ep01_shot01) of the Mir Erdan project.

## Project Root

```
f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01
```

## Current State

- **Episode ID**: ep01
- **Shot ID**: shot01
- **Final State**: episode_rendered
- **Expected Next Action**: none (complete)

## Quick Inspection

### Check Control Status

```bash
python -m app control-status --episode ep01 --shot shot01 --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --json
```

Expected output:
```json
{
  "current_state": "episode_rendered",
  "expected_next_action": "none"
}
```

### Validate Artifacts

```bash
python scripts/validate_rc_artifacts.py --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --episode ep01 --shot shot01
```

## Artifact Structure

### Control Artifacts (output/control/)

- `project_profile.json` - Project configuration and character registry
- `prompt_pack.json` - Prompt engineering configuration
- `ep01_shot01_preflight.json` - Preflight validation results
- `ep01_shot01_action_plan.json` - Approved action plan
- `ep01_shot01_submitted_workflow.json` - ComfyUI workflow submitted to queue
- `ep01_shot01_observed_settings.json` - Runtime settings snapshot
- `frames_manifest.json` - Generated frame inventory
- `ep01_shot01_qc_report.json` - Frame quality control report
- `retry_decision.json` - Retry/no-retry decision
- `ep01_shot01_scene_manifest.json` - Scene assembly metadata
- `qa_report.json` - Scene QA report
- `ep01_shot01_audio_manifest.json` - Audio policy manifest (no-audio for RC)
- `ep01_shot01_final_manifest.json` - Final render manifest
- `artifact_index.json` - Complete artifact inventory
- `ep01_shot01_ledger.json` - Shot-level transition ledger
- `shot_ledger.json` - Project-level shot ledger
- `ep01/shot01_state.json` - Current shot state

### Output Artifacts

- `output/frames/ep01_shot01/000001.png` - Generated frame (480x640)
- `output/scenes/ep01_shot01/scene.mp4` - Assembled scene video (single-frame, 24fps, 3.0s)
- `output/control/references/alya_clean_single_portrait_v2_480x640.png` - Character reference

## Pipeline Stages Completed

1. **Brief Creation** - Shot brief created in `data/briefs/ep01_shot01_brief.md`
2. **Preflight Validation** - Gate checks passed
3. **Action Plan** - Approved action plan generated
4. **Frame Generation** - 1 frame generated (reference-locked SDXL)
5. **QC/Retry** - Frame accepted, no retry required
6. **Scene Assembly** - Single-frame scene.mp4 created
7. **QA Review** - Scene passed QA
8. **Audio Attachment** - Skipped per RC no-audio policy
9. **Final Render** - Final manifest created

## Known Limitations

See `docs/KNOWN_LIMITATIONS.md` for detailed limitations:
- Audio stage completed by no-audio RC policy
- Final render output is final manifest, not full audio/video render
- Single-frame scene.mp4 created for RC proof

## Reproduction Without Windsurf

This proof pack can be inspected and reproduced without Windsurf:

1. **Inspect Artifacts**: All artifacts are plain JSON/MD/PNG/MP4 files
2. **Validate**: Run `validate_rc_artifacts.py` to verify integrity
3. **Check State**: Run `control-status` to verify terminal state
4. **Review Ledger**: Examine `ep01_shot01_ledger.json` for transition history
5. **Review Manifests**: Check all manifest files for artifact metadata

## Validation Commands

### Syntax Check

```bash
python -m py_compile app/control/handlers.py app/control/action_runner.py app/control/action_plan.py app/control/shot_controller.py app/control/shot_state_storage.py app/cli.py scripts/validate_rc_artifacts.py
```

### Test Suite

```bash
python -m pytest tests/test_action_runner.py tests/test_action_plan.py tests/test_control_status_cli.py tests/test_control_service.py tests/test_attach_audio.py tests/test_render_episode.py tests/test_shot_state_storage.py -q -s --tb=short
```

### Artifact Validation

```bash
python scripts/validate_rc_artifacts.py --project-root "f:\ComfyUI\comfy-agent-mvp\data\rc_mir_erdan_ep01" --episode ep01 --shot shot01
```

## Key Configuration

- **Recipe**: sdxl_reference_locked_character_gtx1060
- **Hardware Profile**: GTX1060
- **Resolution**: 480x640
- **Character**: Alya (reference-locked)
- **Audio Policy**: no_audio_for_rc

## Acceptance Status

See `docs/ACCEPTANCE_REPORT.md` for detailed acceptance status.
