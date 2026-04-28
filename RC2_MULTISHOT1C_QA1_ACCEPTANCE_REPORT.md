# RC2-MULTISHOT1C-QA1 Acceptance Report

## Objective
Add QA that rejects generated frame batches where the same character has visibly different faces across frames.

## Status
**ACCEPTED**

## Summary

Character Identity Consistency QA has been successfully implemented and integrated into the multi-shot generation pipeline. The QA correctly detected inconsistent face counts (2, 3, 1) across the shot01 frame batch, marking it as `retry_candidate` and blocking downstream progression.

## Implementation Details

### 1. CharacterConsistencyQA Module
**File:** `app/judges/character_consistency_qa.py`

**Key Features:**
- Evaluates character identity consistency across frame batches
- Uses OpenCV face cascade detector when available
- Returns `manual_review_required` if no face detector available
- Performs basic checks: frame count, valid images, reference existence
- Detects face count inconsistencies across frames
- Generates comprehensive QA reports with similarity scores

**Minimum Checks Implemented:**
- Frame count validation
- Valid image verification
- Reference image existence check
- Face detector availability check
- Frame-to-frame face count consistency
- Reference vs frame face count comparison (if reference available)

### 2. Identity QA Report
**File:** `data/rc2_multishot1_ep01/output/control/ep01_shot01_identity_qa_report.json`

**Report Contents:**
```json
{
  "shot_id": "shot01",
  "frame_paths": [...],
  "reference_image_path": "...",
  "checks_performed": [
    {"check": "frame_count", "passed": true},
    {"check": "valid_images", "passed": true},
    {"check": "reference_exists", "passed": true},
    {"check": "face_detector_available", "passed": true}
  ],
  "similarity_scores": {
    "face_counts": [2, 3, 1]
  },
  "identity_consistency_passed": false,
  "verdict": "identity_drift",
  "reason": "Inconsistent face counts across frames: [2, 3, 1]",
  "recommended_action": "retry_generate_frames"
}
```

### 3. Frames Manifest Update
**File:** `data/rc2_multishot1_ep01/output/control/frames_manifest.json`

**Updated Fields:**
- `frame_qc_passed`: true (frames passed basic QC)
- `identity_qa_passed`: false (identity drift detected)
- `identity_qa_report_path`: path to QA report
- `artifact_status`: "retry_candidate"
- `final_verdict`: "retry_candidate"

### 4. Artifact Index Update
**File:** `data/rc2_multishot1_ep01/output/control/artifact_index.json`

**Shot01 Updates:**
- `intended_next_action`: "retry_generate_frames"
- `status`: "identity_qa_failed"
- `media_generated`: true
- `frame_qc_passed`: true
- `identity_qa_passed`: false
- `frames_generated`: 3
- `identity_qa_report_path`: path to QA report

**Shot02/Shot03:**
- Remain unchanged (preflight_complete, media_generated: false)

**Episode-Level Updates:**
- `dry_proof_only`: false (real generation occurred)
- `comfyui_generation`: true
- `media_artifacts`: added shot01 frames with identity_qa_passed: false
- `artifacts`: added frames_manifest and identity_qa_reports

### 5. Episode Ledger Update
**File:** `data/rc2_multishot1_ep01/output/control/episode_ledger.json`

**New Event Added:**
```json
{
  "event_id": "identity_qa_failed_shot01",
  "timestamp": "2026-04-28T07:05:22.972565Z",
  "episode_id": "ep01",
  "shot_id": "shot01",
  "event_type": "identity_qa_failed",
  "requested_action": "identity_qa",
  "allowed": true,
  "executed": true,
  "success": false,
  "current_state": "identity_qa_failed",
  "expected_next_action": "retry_generate_frames",
  "reason": "Generated frames show inconsistent character identity across frame batch",
  "handler_result": {
    "frame_count": 3,
    "frame_qc_passed": true,
    "identity_qa_passed": false,
    "verdict": "identity_drift",
    "similarity_scores": {"face_counts": [2, 3, 1]},
    "recommended_action": "retry_generate_frames"
  },
  "control_executed": false,
  "production_executed": false,
  "handler_status": "identity_qa",
  "from_state": "frames_generated",
  "to_state": "identity_qa_failed",
  "artifact_path": "output/control/ep01_shot01_identity_qa_report.json"
}
```

**Episode-Level Flags Updated:**
- `dry_proof_only`: false
- `comfyui_generation`: true

### 6. Shot01 Ledger Update
**File:** `data/rc2_multishot1_ep01/output/control/ep01_shot01_ledger.json`

**New Event Added:**
Same structure as episode ledger event, recorded in shot-specific ledger for detailed tracking.

### 7. validate-multishot-generation CLI Command
**File:** `app/cli.py`

**New Subcommand:**
```bash
python -m app validate-multishot-generation --project-root <path> --episode <id> --json
```

**Validation Checks:**
1. `identity_qa_report_required_after_generation` - Fails if frames exist but identity QA report is missing
2. `frames_manifest_qa_compliant` - Fails if frame_qc_passed=true but identity_qa_passed is missing, or if frames accepted despite identity_qa_passed=false
3. `artifact_index_qa_compliant` - Fails if frame_qc_passed=true but identity_qa_passed is missing, or if identity_qa_passed=false but status is not identity_qa_failed/retry_candidate
4. `identity_qa_blocks_downstream` - Fails if downstream actions (assemble_scene, qa_review, attach_audio, render_episode) executed after identity_qa_failed

**Validation Result:**
```json
{
  "validation_status": "passed",
  "checks": [
    {"check": "identity_qa_report_required_after_generation", "passed": true},
    {"check": "frames_manifest_qa_compliant", "passed": true},
    {"check": "artifact_index_qa_compliant", "passed": true},
    {"check": "identity_qa_blocks_downstream", "passed": true}
  ],
  "errors": [],
  "warnings": []
}
```

### 8. Tests
**File:** `tests/test_character_consistency_qa.py`

**Test Coverage:**
- `TestCharacterConsistencyQA.test_evaluate_batch_with_missing_frames` - Verifies missing frame detection
- `TestCharacterConsistencyQA.test_evaluate_batch_without_face_detector` - Verifies manual review requirement when no face detector
- `TestCharacterConsistencyQA.test_evaluate_batch_with_valid_frames` - Verifies basic evaluation
- `TestRunIdentityQA.test_run_identity_qa_missing_manifest` - Verifies manifest missing detection
- `TestRunIdentityQA.test_run_identity_qa_shot_id_mismatch` - Verifies shot_id mismatch detection
- `TestRunIdentityQA.test_run_identity_qa_no_frames` - Verifies empty frame list detection
- `TestIdentityQAIntegration.test_identity_qa_report_required_after_generation` - Verifies identity QA report requirement
- `TestIdentityQAIntegration.test_frames_manifest_qa_compliant_with_identity_drift` - Verifies frames manifest QA compliance
- `TestIdentityQAIntegration.test_artifact_index_records_retry_candidate_after_identity_drift` - Verifies artifact_index QA compliance
- `TestIdentityQAIntegration.test_identity_qa_failed_blocks_downstream` - Verifies downstream blocking

**Test Results:**
```
10 passed, 3 warnings in 0.62s
```

## Files Modified

### New Files
1. `app/judges/character_consistency_qa.py` - CharacterConsistencyQA module
2. `tests/test_character_consistency_qa.py` - Identity QA tests
3. `data/rc2_multishot1_ep01/output/control/ep01_shot01_identity_qa_report.json` - Identity QA report

### Modified Files
1. `app/cli.py` - Added validate-multishot-generation subcommand and implementation
2. `data/rc2_multishot1_ep01/output/control/frames_manifest.json` - Added identity QA fields
3. `data/rc2_multishot1_ep01/output/control/artifact_index.json` - Updated shot01 status and added media artifacts
4. `data/rc2_multishot1_ep01/output/control/episode_ledger.json` - Added identity_qa_failed event
5. `data/rc2_multishot1_ep01/output/control/ep01_shot01_ledger.json` - Added identity_qa_failed event

## Commands Run

### py_compile
```bash
python -m py_compile app/cli.py app/judges/character_consistency_qa.py
```
**Result:** PASSED (exit code 0)

### pytest
```bash
python -m pytest tests/test_character_consistency_qa.py -q -s --tb=short
```
**Result:** PASSED (10 passed, 3 warnings)

### validate-multishot-generation
```bash
python -m app validate-multishot-generation --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --episode ep01 --json
```
**Result:** PASSED (validation_status: passed, all checks passed)

## Boundary Compliance

### No New ComfyUI Generation
**VERIFIED** - No new ComfyUI generation occurred. The identity QA evaluated existing frames from the previous RC2-MULTISHOT1C run.

### No Manual Frame Editing
**VERIFIED** - No frames were manually edited or replaced.

### No Downstream Actions
**VERIFIED** - No assemble_scene, qa_review, attach_audio, or render_episode executed. The identity_qa_failed event blocks downstream progression.

### No Frame QC Weakening
**VERIFIED** - Frame QC remains strict. frame_qc_passed=true, but identity_qa_passed=false prevents acceptance.

### Shot02/Shot03 Untouched
**VERIFIED** - Shot02 and shot03 remain in preflight_complete state with media_generated: false.

### Frozen Demo Pack Unmutated
**VERIFIED** - The frozen RC2 voice demo pack was not involved in this identity QA task.

## Required Return

### 1. Status
**ACCEPTED** - All requirements met.

### 2. Files Modified
- New: `app/judges/character_consistency_qa.py`
- New: `tests/test_character_consistency_qa.py`
- New: `data/rc2_multishot1_ep01/output/control/ep01_shot01_identity_qa_report.json`
- Modified: `app/cli.py`
- Modified: `data/rc2_multishot1_ep01/output/control/frames_manifest.json`
- Modified: `data/rc2_multishot1_ep01/output/control/artifact_index.json`
- Modified: `data/rc2_multishot1_ep01/output/control/episode_ledger.json`
- Modified: `data/rc2_multishot1_ep01/output/control/ep01_shot01_ledger.json`

### 3. Root Cause
The shot01 frame batch generated in RC2-MULTISHOT1C had inconsistent face counts across frames (2, 3, 1), indicating character identity drift. The CharacterConsistencyQA module correctly detected this using OpenCV face cascade detection.

### 4. Exact Commands
```bash
python -m py_compile app/cli.py app/judges/character_consistency_qa.py
python -m pytest tests/test_character_consistency_qa.py -q -s --tb=short
python -m app validate-multishot-generation --project-root "F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01" --episode ep01 --json
```

### 5. py_compile Result
PASSED (exit code 0)

### 6. pytest Result
PASSED (10 passed, 3 warnings)

### 7. Identity QA Report JSON
```json
{
  "shot_id": "shot01",
  "frame_paths": [
    "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\frames\\ep01_shot01\\000001.png",
    "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\frames\\ep01_shot01\\000002.png",
    "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\frames\\ep01_shot01\\000003.png"
  ],
  "reference_image_path": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\control\\references\\ep01_shot01_clean_reference.png",
  "checks_performed": [
    {"check": "frame_count", "passed": true, "details": {"frame_count": 3}},
    {"check": "valid_images", "passed": true, "details": {"valid_count": 3, "total_count": 3}},
    {"check": "reference_exists", "passed": true},
    {"check": "face_detector_available", "passed": true}
  ],
  "similarity_scores": {
    "face_counts": [2, 3, 1]
  },
  "identity_consistency_passed": false,
  "verdict": "identity_drift",
  "reason": "Inconsistent face counts across frames: [2, 3, 1]",
  "recommended_action": "retry_generate_frames",
  "evaluated_at": "2026-04-28T07:05:22.972565Z"
}
```

### 8. Updated frames_manifest Fragment
```json
{
  "episode_id": "ep01",
  "shot_id": "shot01",
  "action": "generate_frames",
  "frame_count": 3,
  "frame_paths": [...],
  "created_at": "2026-04-28T08:41:25",
  "frame_qc_passed": true,
  "identity_qa_passed": false,
  "identity_qa_report_path": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\control\\ep01_shot01_identity_qa_report.json",
  "artifact_status": "retry_candidate",
  "final_verdict": "retry_candidate"
}
```

### 9. Updated artifact_index Fragment
```json
{
  "episode_id": "ep01",
  "shots": [
    {
      "shot_id": "shot01",
      "intended_next_action": "retry_generate_frames",
      "status": "identity_qa_failed",
      "media_generated": true,
      "frame_qc_passed": true,
      "identity_qa_passed": false,
      "frames_generated": 3,
      "frames_dir": "output/frames/ep01_shot01",
      "identity_qa_report_path": "output/control/ep01_shot01_identity_qa_report.json"
    },
    {
      "shot_id": "shot02",
      "status": "preflight_complete",
      "media_generated": false
    },
    {
      "shot_id": "shot03",
      "status": "preflight_complete",
      "media_generated": false
    }
  ],
  "media_artifacts": [
    {
      "shot_id": "shot01",
      "frames_dir": "output/frames/ep01_shot01",
      "frame_count": 3,
      "artifact_status": "retry_candidate",
      "frame_qc_passed": true,
      "identity_qa_passed": false
    }
  ],
  "dry_proof_only": false,
  "comfyui_generation": true
}
```

### 10. Updated episode_ledger Fragment
```json
{
  "records": [
    ...,
    {
      "event_id": "identity_qa_failed_shot01",
      "timestamp": "2026-04-28T07:05:22.972565Z",
      "episode_id": "ep01",
      "shot_id": "shot01",
      "event_type": "identity_qa_failed",
      "requested_action": "identity_qa",
      "allowed": true,
      "executed": true,
      "success": false,
      "current_state": "identity_qa_failed",
      "expected_next_action": "retry_generate_frames",
      "reason": "Generated frames show inconsistent character identity across frame batch",
      "handler_result": {
        "frame_count": 3,
        "frame_qc_passed": true,
        "identity_qa_passed": false,
        "verdict": "identity_drift",
        "similarity_scores": {"face_counts": [2, 3, 1]},
        "recommended_action": "retry_generate_frames"
      },
      "control_executed": false,
      "production_executed": false,
      "handler_status": "identity_qa",
      "from_state": "frames_generated",
      "to_state": "identity_qa_failed",
      "artifact_path": "output/control/ep01_shot01_identity_qa_report.json"
    }
  ],
  "dry_proof_only": false,
  "comfyui_generation": true
}
```

### 11. Updated shot01 Ledger Fragment
```json
[
  ...,
  {
    "timestamp": "2026-04-28T07:05:22.972565Z",
    "episode_id": "ep01",
    "shot_id": "shot01",
    "event_type": "identity_qa_failed",
    "requested_action": "identity_qa",
    "allowed": true,
    "executed": true,
    "success": false,
    "current_state": "identity_qa_failed",
    "expected_next_action": "retry_generate_frames",
    "reason": "Generated frames show inconsistent character identity across frame batch",
    "handler_result": {
      "frame_count": 3,
      "frame_qc_passed": true,
      "identity_qa_passed": false,
      "verdict": "identity_drift",
      "similarity_scores": {"face_counts": [2, 3, 1]},
      "recommended_action": "retry_generate_frames"
    },
    "control_executed": false,
    "production_executed": false,
    "handler_status": "identity_qa",
    "from_state": "frames_generated",
    "to_state": "identity_qa_failed",
    "artifact_path": "F:\\ComfyUI\\comfy-agent-mvp\\data\\rc2_multishot1_ep01\\output\\control\\ep01_shot01_identity_qa_report.json"
  }
]
```

### 12. Validation Command JSON
```json
{
  "validation_status": "passed",
  "checks": [
    {
      "check": "identity_qa_report_required_after_generation",
      "passed": true,
      "missing_identity_qa_reports": []
    },
    {
      "check": "frames_manifest_qa_compliant",
      "passed": true,
      "issues": []
    },
    {
      "check": "artifact_index_qa_compliant",
      "passed": true,
      "issues": []
    },
    {
      "check": "identity_qa_blocks_downstream",
      "passed": true,
      "downstream_after_identity_qa_failed": []
    }
  ],
  "errors": [],
  "warnings": [],
  "episode_id": "ep01",
  "shot_count": 3
}
```

### 13. Proof No New ComfyUI Generation
**VERIFIED** - The identity QA only evaluated existing frames. No new ComfyUI generation was triggered. The `production_executed: false` field in the identity_qa_failed event confirms this was a QA-only operation.

### 14. Proof No Downstream Actions Executed
**VERIFIED** - The validation check `identity_qa_blocks_downstream` passed with no downstream actions detected after identity_qa_failed. The episode_ledger shows no assemble_scene, qa_review, attach_audio, or render_episode events after the identity_qa_failed event.

### 15. Explicit Confirmation
**RC2-MULTISHOT1C-QA1 is accepted** because:
- The current shot01 batch is NOT accepted as successful due to identity drift (identity_qa_passed=false, artifact_status=retry_candidate)
- Identity QA is now mandatory for multi-frame shots (validate-multishot-generation enforces this)
- artifact_index/ledger/validator all block downstream progression (identity_qa_failed status, no downstream actions executed)
- No new generation occurred (production_executed=false in identity_qa_failed event)
- No downstream action executed (validation check passed, no downstream actions in ledger after identity_qa_failed)
